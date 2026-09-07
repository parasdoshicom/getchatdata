---
name: root-cause
description: Investigate why a metric changed and separate measurement, composition, and within-segment effects.
---

# Explain the movement before its cause

Read [the working agreement](../../references/working-agreement.md) when using this skill. It defines source, privacy, execution, and evidence boundaries.

Reproduce the baseline and current value from the same definition, cutoff, source, and timezone. Rule out partial periods, late data, renamed events, duplicate joins, and source changes before diagnosing product behavior. Compare comparable weekdays and full periods.

Build a small hypothesis table with mechanism, predicted observation, evidence for, evidence against, and next test. Start from grounded segments such as entry channel, platform, geography, tenure, or product. Do not search hundreds of slices until one looks significant.

For a rate, use scripts/analyze.py decompose on exhaustive, disjoint segment counts for both periods. It uses symmetric (Shapley) attribution: mix contribution = change in weight times average rate; within contribution = change in rate times average weight. Contributions reconcile exactly to the overall percentage-point change. Missing/new segments with no measurable rate need explicit treatment; the helper refuses zero-denominator cells rather than inventing counterfactual rates.

For totals, distinguish volume, conversion, price, refunds, and recognition timing. Use additive bridges or a stated interaction-allocation method and reconcile the residual. Avoid double-counting overlapping dimensions; diagnose one partition at a time.

Try to disprove the leading explanation with a negative control, unchanged segment, independent source, or timing check. Observational contribution is not causation. Deliver the arithmetic bridge, ranked hypotheses, ruled-out explanations, uncertainty, and an action tied to the next test. If evidence only supports where the change occurred, say that.

For helper commands and input formats, see [the runnable tools](../../references/tools.md) when needed. Resolve script paths relative to this skill: `../../scripts/analyze.py`.
