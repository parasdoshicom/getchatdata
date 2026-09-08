# Runnable analysis checks

Python 3.9+; standard library only. No package install, network access, account, or credential is needed. Commands below run from the public repository root. Within an installed skill, locate `scripts/analyze.py` relative to its SKILL.md (or `../../scripts/analyze.py` inside the native plugin). Commands emit JSON to stdout; redirect it to the user's chosen output directory to retain it.

## Experiment readout

```sh
python3 plugins/chatdata/scripts/analyze.py experiment --control-n 1000 --control-success 100 --treatment-n 1000 --treatment-success 140 --min-effect 0.01
```

Counts must represent independent randomized units with binary outcomes. `--allocation` is the planned treatment fraction (default .5), `--alpha` is two-sided (default .05), and `--min-effect` is an absolute rate difference, not percent. This example is synthetic. It gives 10% versus 14%, a 4 percentage-point difference, with uncertainty. The helper does not inspect assignment logs, stopping rules, outcome maturity, or guardrails. Read experiment-analysis before making a decision.

The confidence interval uses Newcombe's unpaired difference of Wilson score intervals. The reported p-value is a separate pooled normal approximation and can differ near a decision boundary; use the prespecified inferential method. Sparse outcomes are marked for review and have no asymptotic p-value. SRM uses a chi-square goodness-of-fit test with one degree of freedom at .001; fewer than five expected assignments in either arm prevents that check.

## Approximate sample size

```sh
python3 plugins/chatdata/scripts/analyze.py power --baseline 0.1 --absolute-effect 0.02 --power 0.8
```

Equal allocation, fixed horizon, independent binary outcomes, normal approximation. About 3,841 units per arm for this example. No cluster or multiplicity correction is included. A baseline of .1 and effect of .02 means 10% to 12%, not 10% to 10.02%.

## Ordered, mature funnel

```sh
python3 plugins/chatdata/scripts/analyze.py funnel plugins/chatdata/examples/funnel.csv --steps visit signup purchase --as-of 2026-01-05T00:00:00Z --window-hours 48
```

Required columns: `user_id,event,timestamp`. ISO-8601 timestamps must include a timezone. Uses the first entry, strict ordering and a horizon from entry; counts only users with a fully observed horizon. The example yields 3 → 2 → 1. One recent user is excluded, one duplicate is removed, and an out-of-order purchase is not credited. Equal timestamps do not prove ordering. Empty denominators yield null rates.

## Rate decomposition

```sh
python3 plugins/chatdata/scripts/analyze.py decompose plugins/chatdata/examples/mix-shift.csv
```

Columns: `segment,n_before,converted_before,n_after,converted_after`. Supply an exhaustive partition with each segment present in both periods and positive denominators. The example falls from 17% to 8% with unchanged segment conversion rates: all −9 percentage points are mix. The symmetric decomposition splits the interaction equally between mix and within-segment performance and checks the reconciliation residual. This explains arithmetic contribution, not causal effects.

## CSV quality profile

```sh
python3 plugins/chatdata/scripts/analyze.py profile plugins/chatdata/examples/funnel.csv --keys user_id event timestamp
```

Checks missing values, duplicate rows and duplicate keys without printing raw cell values. These small-file helpers load CSV rows into memory. For large sources, adapt the method to a bounded warehouse query or chunked processing. Profiling alone cannot establish freshness, business validity, or suitability.

## Exact-period retention

Export one complete cohort file and one file containing only qualifying return activity, then run:

```sh
python3 plugins/chatdata/scripts/retention.py \
  --cohorts cohorts.csv --activity activity.csv \
  --as-of 2026-01-04T00:00:00Z --timezone UTC \
  --frequency day --periods 4
```

The default columns are `entity_id,cohort_at` and `entity_id,activity_at`. All timestamps and the exclusive `--as-of` cutoff need explicit UTC offsets; the IANA timezone defines calendar boundaries. The helper fixes cohort membership, keeps every eligible entrant in the denominator, deduplicates qualifying activity by entity and calendar period, and emits null for unfinished periods. It stops on conflicting cohort entries, unknown entities, activity before entry, malformed timestamps, or incomplete required fields. Output contains aggregates without identities or input paths. See the [full retention contract](csv-retention.md) before interpreting the result.

## Join cardinality and measure audit

```sh
python3 plugins/chatdata/scripts/join_audit.py \
  --left orders.csv --right items.csv \
  --left-keys order_id --right-keys order_id \
  --relationship one-to-many --left-measure revenue
```

State `one-to-one`, `one-to-many`, `many-to-one`, or `many-to-many` from the intended source grain. Composite keys are accepted after each key flag. The helper reports duplicate and NULL keys, matched and unmatched input rows, and exact INNER and LEFT JOIN output counts using exact text equality. With `--left-measure`, it reconciles decimal totals before and after the join. Exit code 1 blocks violated uniqueness, observed many-to-many fanout, or a repeated left-side measure. Exit code 2 means the extract or arguments were invalid. Results contain only aggregate counts and totals, not keys or rows. A pass applies only to the supplied extracts and equality semantics.

## Optional local DuckDB query

The core plugin remains dependency-free. If your project already uses DuckDB, or you install it in your own environment, ChatData can query an existing local database file without opening it for writes:

```sh
python3 -m pip install duckdb
python3 plugins/chatdata/scripts/duckdb_query.py warehouse.duckdb \
  --sql-file analysis/query.sql --max-rows 1000
```

The SQL file must contain one `SELECT` or `WITH` statement and be no larger than 1 MB. The adapter rejects additional statements and common write, extension, attach, export, and configuration commands. It opens the existing database read-only, disables external file and URL access plus extension auto-loading, and bounds returned rows from 1 to 10,000. That limit does not bound scanned bytes or query cost. Output includes the result rows, column names, a SQL hash, database size and modification-time fingerprint, elapsed time, and truncation status. The adapter never sends data itself, but your AI client may include command output in a model request under that client's policy. Read-only execution does not prove that the query uses the right grain, definition, or source.

## Methods

- [Newcombe, 1998: interval estimation for independent proportions](https://pubmed.ncbi.nlm.nih.gov/9595617/)
- [NIST: confidence limits for a binomial proportion](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)
- [Microsoft Research: diagnosing sample ratio mismatch](https://www.microsoft.com/en-us/research/publication/diagnosing-sample-ratio-mismatch-in-online-controlled-experiments-a-taxonomy-and-rules-of-thumb-for-practitioners/)

These checks have deterministic fixtures. They do not constitute evidence that an AI model will follow every skill correctly.
