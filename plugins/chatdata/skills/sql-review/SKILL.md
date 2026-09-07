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
