# Exact-period CSV retention

The failure to prevent: counting only returners in the denominator or treating unfinished follow-up as zero can make cohort comparisons misleading.

Use two local CSVs. The cohort file must include every eligible entrant, including people who never return. Fix eligibility and the entry event before exporting. The activity file must contain only the qualifying return event; filter event types in the source query. Neither file is written or sent over the network.

`cohorts.csv`:

```csv
entity_id,cohort_at
a,2026-01-01T00:00:00Z
b,2026-01-01T12:00:00Z
```

`activity.csv`:

```csv
entity_id,activity_at
a,2026-01-02T01:00:00Z
a,2026-01-02T23:00:00Z
```

From this skill directory, run:

```sh
python3 ../../scripts/retention.py --cohorts cohorts.csv --activity activity.csv \
  --as-of 2026-01-04T00:00:00Z --timezone UTC --frequency day --periods 4
```

Both inputs and `--as-of` require timestamps with explicit UTC offsets. `--timezone` selects the IANA timezone used for calendar boundaries. Weeks begin Monday; months follow the calendar; daylight-saving transitions retain local date boundaries. `--periods` includes age zero and accepts 1 through 1000. Rename columns with `--entity-column`, `--cohort-column`, and `--activity-column`.

`--as-of` is an exclusive cutoff through which the caller has verified complete data. Events and entrants at or after it are excluded and counted in diagnostics. A cell becomes observed only when its entire calendar period has ended by that instant. The example produces counts `[0, 1, 0, null]`, rates `[0, 0.5, 0, null]`, and a denominator of two in every cell. Duplicate activity in one entity-period counts once. Age zero measures qualifying activity in the entry calendar period; entry alone does not imply a return.

Repeated cohort rows are allowed only when they resolve to the same timestamp. Conflicting membership, missing required values, unknown activity entities, and activity before entry stop analysis. Resolve these issues in the source; do not silently remove them to improve retention. Empty activity with valid headers is allowed; an empty cohort is rejected.

Output is aggregate JSON with cohort dates, counts, rates, maturity status, diagnostics, and limitations. It contains no entity IDs, row samples, or input paths. Aggregates can still be sensitive for small cohorts; follow the working agreement before sharing. A failed CLI check exits with code 2 and a JSON error on stderr.

Before interpreting results, verify cohort and event coverage through the cutoff, late-arriving events, migration effects, and whether the calendar-period definition fits the decision. This helper cannot prove those assumptions. Compare cohorts at the same mature age. Do not describe this output as rolling retention, elapsed-time retention, subscription churn, survival, revenue retention, or a causal result.
