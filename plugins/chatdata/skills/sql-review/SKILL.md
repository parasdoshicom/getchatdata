---
name: sql-review
description: Review or write analytical SQL with grain, joins, time boundaries, and metric reconciliation.
---

# Make the query match the question

Read [the working agreement](../../references/working-agreement.md) when using this skill. It defines source, privacy, execution, and evidence boundaries.

State dialect, source tables, row grain, expected result grain, key relationships, timezone, and metric definition. Read schema metadata and existing verified queries before inventing columns. Keep source access read-only unless the user authorizes writes.

Review join cardinality and preaggregate many-side tables before joining. Check NULL behavior, COUNT(*) versus COUNT(column), DISTINCT masking duplicate joins, WHERE filters that turn LEFT JOINs into INNER JOINs, integer division, divide-by-zero, and sum-of-ratios mistakes. Separate deduplication from legitimate repeated events.

Use half-open time ranges and an explicit timezone. Distinguish partition pruning columns from business event time. For windows, state partition keys, ordering and deterministic tie breakers, and frame bounds. Do not use future information in a historical feature or cohort assignment.

Inspect query plans or use dry-run estimates when the connector supports them. Bound scan cost and returned rows. A LIMIT may bound output while still scanning the whole table. Do not claim a query was run when it was only reviewed.

Validate against small hand-computed fixtures including duplicates, NULLs, boundary timestamps, empty groups, and a one-to-many join. Reconcile one independent total. Deliver the query, changed assumptions, actual execution status, cost if observed, and checks with expected versus actual values.

For helper commands and input formats, see [the runnable tools](../../references/tools.md) when needed. Resolve script paths relative to this skill: `../../scripts/analyze.py`.

Before accepting an equality join, run the local join audit on available CSV extracts, with the intended relationship stated explicitly. A repeated key can multiply rows and totals even when the SQL looks correct.

```sh
python3 ../../scripts/join_audit.py --left orders.csv --right customers.csv \
  --left-keys customer_id region --right-keys customer_id region \
  --relationship many-to-one --left-measure amount
```

Resolve the script path from this skill's directory. Use `one-to-one`, `one-to-many`, `many-to-one`, or `many-to-many` according to the source grain, before looking at the results. The audit reports duplicate and NULL key counts, matched and unmatched input rows, and exact INNER JOIN and LEFT JOIN output row counts for the supplied extracts. Keys use exact text equality; empty key fields never match, including within composite keys. Add `--null-value NULL` for an additional exact NULL token. Normalize data deliberately before auditing if the source uses different casts, collation, or whitespace rules.

Exit code 1 blocks a violated uniqueness expectation, an observed many-to-many match, or repetition of a supplied left measure. Declaring `many-to-many` does not waive observed many-to-many multiplication. Preaggregate to the intended grain or correct the keys, then rerun before accepting totals. A valid one-to-many join can pass without a measure; adding a left measure blocks duplicated contributions even if positive and negative values cancel. Measure totals and differences are decimal strings; every measure value must be finite and numeric. For INNER JOIN, compare the output total with the matched input total so lost rows and duplicated contributions stay distinguishable.

Exit code 2 means invalid or unreadable input. JSON includes aggregate counts and totals, never raw keys or row values. A passing audit applies only to the provided extracts and equality semantics. It does not prove full-source cardinality, arbitrary SQL predicates, or metric correctness. When extracts cannot be obtained, mark join execution unverified and supply the equivalent grouped-key counts and reconciliation SQL for review.

For an existing local DuckDB database, the optional `../../scripts/duckdb_query.py` adapter runs one `SELECT` or `WITH` statement from a SQL file in read-only mode and limits returned rows. It disables external file, URL, extension, and attached-database access for the query. A result limit does not limit scanned bytes, so inspect the plan and filters before running a costly query. The adapter requires the local `duckdb` Python package and does not install it automatically.

Read the [worked failure case](../../references/worked-failures.md#sql-review) when checking a plausible but unsupported answer.
