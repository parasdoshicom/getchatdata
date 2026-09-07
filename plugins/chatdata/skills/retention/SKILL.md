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

For helper commands and input formats, see [the runnable tools](../../references/tools.md) when needed. Resolve script paths relative to this skill: `../../scripts/analyze.py`.
