---
name: retention
description: Build mature cohort retention, churn, repeat-purchase, or survival analyses.
---

# Keep cohort age separate from calendar time

Read [the working agreement](../../references/working-agreement.md) when using this skill. It defines source, privacy, execution, and evidence boundaries.

Define the cohort entry event, entity, return event, frequency, timezone, and eligibility. Distinguish exact-period retention, rolling retention, bracket retention, resurrection, and repeat purchase. For revenue, distinguish gross from net retention and customer from dollar denominators.

Construct an entity-period spine before counting returns. Ensure period zero is defined consistently and cohort membership is fixed. Mark cells without enough follow-up as unobserved, not zero. Cohort age and calendar period are different axes. Compare cohorts at equal age and show counts along with rates.

Inspect survivor bias, delayed activation, migration, cancellations followed by reactivation, and data coverage changes. Do not drop churned users from the denominator. Subscription churn needs at-risk exposure and a defined cancellation/effective-end rule.

For time-to-churn with right censoring, use survival analysis with explicit event and censoring definitions. Check whether censoring is plausibly independent; competing risks may need a different estimator. Never infer lifetime value from a few early retention points without a stated horizon and sensitivity range.

Deliver a cohort table with immature cells masked, a retention curve, denominator checks, and a decision about which cohort or lifecycle moment deserves investigation. Keep acquisition mix separate from within-cohort behavior.

For exact calendar-period retention from CSV, run `../../scripts/retention.py` with separate complete cohort and qualifying activity files, an explicit `--as-of`, and `--timezone`. Follow [the retention helper contract](../../references/csv-retention.md). The helper rejects conflicting cohort entries, unknown entities, and activity before entry; deduplicates entity-period returns; preserves full cohort denominators; and masks unfinished periods. Do not replace these checks with an activity-only denominator or fill null cells with zero.

The helper covers exact daily, Monday-weekly, and monthly retention. It does not validate source completeness or compute churn, rolling retention, survival, or revenue retention. Use a separately justified method for those questions. For other helper commands, see [the runnable tools](../../references/tools.md).

Read the [worked failure case](../../references/worked-failures.md#retention) when checking a plausible but unsupported answer.
