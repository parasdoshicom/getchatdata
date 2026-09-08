---
name: experiment-design
description: Design or vet an A/B test, including power, randomization, guardrails, and stopping rules.
---

# Write a test that can answer the decision

Read [the working agreement](../../references/working-agreement.md) when using this skill. It defines source, privacy, execution, and evidence boundaries.

Set the hypothesis, action if successful, smallest effect worth acting on, primary metric, randomization unit, eligibility, exposure rule, and analysis population. Default to intention-to-treat when assignment is the intervention; do not condition on post-treatment engagement. Distinguish relative lift from absolute percentage points.

Estimate baseline rate and eligible traffic from supplied evidence. Use scripts/analyze.py power for an approximate two-sided binary-outcome design with equal allocation; disclose its independence and normal-approximation assumptions. Inflate for cluster randomization using a justified design effect. Do not apply a binary formula to continuous revenue or repeated events. For those, choose a validated variance model or simulation and show the input assumptions.

Predeclare alpha, power, allocation, guardrails, minimum duration covering relevant cycles, ramp, exclusions, missingness handling, and decision rule. Account for multiple variants and primary metrics. Fixed-horizon inference needs a fixed horizon; choose and implement a valid sequential method before peeking, not afterward.

Check interference, contamination, carryover, novelty, seasonality, instrumentation, SRM, and whether the outcome can mature before the decision. Recommend an A/A or logging check when exposure reliability is unknown.

Deliver an experiment plan and a launch-readiness verdict with specific missing inputs. Running power calculations or offline simulations is allowed within the task. Launching an experiment, changing product traffic, spending money, or messaging participants requires the user's authorization.

For helper commands and input formats, see [the runnable tools](../../references/tools.md) when needed. Resolve script paths relative to this skill: `../../scripts/analyze.py`.

Read the [worked failure case](../../references/worked-failures.md#experiment-design) when checking a plausible but unsupported answer.
