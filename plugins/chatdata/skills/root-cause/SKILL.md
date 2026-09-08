---
name: root-cause
description: Investigate why a metric changed and separate measurement, composition, and within-segment effects.
---

# Explain the movement before its cause

Read [the working agreement](../../references/working-agreement.md) when using this skill. It defines source, privacy, execution, and evidence boundaries.

Reproduce the baseline and current value from the same definition, cutoff, source, and timezone. Rule out partial periods, late data, renamed events, duplicate joins, and source changes before diagnosing product behavior. Compare comparable weekdays and full periods.

Build a small hypothesis table with mechanism, predicted observation, evidence for, evidence against, and next test. Start from grounded segments such as entry channel, platform, geography, tenure, or product. Do not search hundreds of slices until one looks significant.

For a rate, use scripts/analyze.py decompose on exhaustive, disjoint segment counts for both periods. Read references with the client's Read tool. Run the helper as one standalone Bash command that begins with `python3` and contains no `cd`, `cat`, `ls`, pipe, or second command. If that call is denied or fails, retry the exact standalone helper command once; if it still fails, stop instead of substituting hand arithmetic as a verified result. The helper uses symmetric (Shapley) attribution: mix contribution = change in weight times average rate; within contribution = change in rate times average weight. Contributions reconcile exactly to the overall percentage-point change. Missing/new segments with no measurable rate need explicit treatment; the helper refuses zero-denominator cells rather than inventing counterfactual rates.

For totals, distinguish volume, conversion, price, refunds, and recognition timing. Use additive bridges or a stated interaction-allocation method and reconcile the residual. Avoid double-counting overlapping dimensions; diagnose one partition at a time. Reconcile absolute counts before describing a segment's larger share or count as growth, a gain, or a loss; a share change does not establish that the total outcome grew. Remove abandoned calculations and self-corrections from the final answer.

Try to disprove the leading explanation with a negative control, unchanged segment, independent source, or timing check. Observational contribution is not causation. Deliver the arithmetic bridge, ranked hypotheses, ruled-out explanations, uncertainty, and an action tied to the next test. If evidence only supports where the change occurred, say that.

A decomposition cannot identify what an intervention caused or predict what reversing it would do. Unless the evidence includes a design that identifies the intervention's effect, state that both the intervention effect and the rollback effect are unknown. Do not claim that a release helped, harmed, had no effect, or that rollback would or would not reverse the movement. Do not use the direction of an observed within-segment change to argue for or against the intervention; report it only as an association. When asked for an action, say that this arithmetic alone neither supports nor rules out rollback. Do not speculate that rollback could remove a gain, restore a rate, prevent harm, or have any other directional outcome, even conditionally. Keep mechanism hypotheses separate from the action and name the comparison or exposure evidence needed to test them.

For helper commands and input formats, see [the runnable tools](../../references/tools.md) when needed. Resolve script paths relative to this skill: `../../scripts/analyze.py`.

Read the [worked failure case](../../references/worked-failures.md#root-cause) when checking a plausible but unsupported answer.
