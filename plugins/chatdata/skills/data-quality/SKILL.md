---
name: data-quality
description: Assess whether a dataset is fit for a named analysis, including grain, missingness, joins, and freshness.
---

# Test the data against the decision

Read [the working agreement](../../references/working-agreement.md) when using this skill. It defines source, privacy, execution, and evidence boundaries.

Identify what one row means, expected keys, event time versus ingestion time, coverage, and the decision's tolerance for error. Inspect schema and a bounded sample, then run appropriate full-data checks within cost limits. Use scripts/analyze.py profile for CSV row counts, missing values, duplicate rows, and duplicate keys; it does not prove validity or freshness.

Test uniqueness, nullability, types, ranges, category drift, referential integrity, timestamp bounds, and impossible sequences. Compare distributions over time and across sources. Report missingness by outcome, treatment, and important segments; missing-not-at-random data can bias an otherwise correct calculation.

Before a join, record each table's grain, key cardinality, and expected row multiplier. Afterward reconcile rows, distinct entities, amounts, and unmatched keys. A plausible total does not rule out compensating errors.

For each issue, record affected count and share, likely impact on the requested result, whether the analysis can proceed, and a concrete fix or sensitivity bound. Avoid one generic quality score that hides a critical defect.

Deliver a suitability verdict: usable, usable with named limitations, or blocked for this question. Keep raw data untouched. Put cleaned derivatives and rejected-row reports in the agreed output folder; record transformations.

For helper commands and input formats, see [the runnable tools](../../references/tools.md) when needed. Resolve script paths relative to this skill: `../../scripts/analyze.py`.
