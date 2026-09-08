---
name: experiment-analysis
description: Analyze an A/B test or vet a claimed winner using assignment checks, uncertainty, and practical effect.
---

# Check whether a winner can be called

Read [the working agreement](../../references/working-agreement.md) when using this skill. It defines source, privacy, execution, and evidence boundaries.

Read the design before outcomes: population, assignment unit, allocation, primary metric, horizon, exclusions, and smallest meaningful effect. Check counts at assignment and exposure separately. Sample-ratio mismatch (SRM) means the observed assignment differs unexpectedly from the plan; investigate it before trusting an outcome comparison.

Use the bundled experiment helper for two independent groups with binary outcomes and aggregate counts only. Supply planned allocation and the prespecified minimum effect. It reports SRM, absolute and relative lift, Newcombe/Wilson confidence bounds, and a descriptive result. For repeated users, clusters, paired observations, heavy-tailed revenue, or continuous outcomes, select an appropriate estimator instead. Do not convert event counts into independent users.

Inspect observation maturity, missingness, attrition, invariant metrics, treatment leakage, delayed outcomes, and guardrails. An outcome denominator after treatment can bias the result. Compare assignment-based and exposure-based populations without treating them as equivalent.

Distinguish evidence of benefit from enough benefit to act. An interval crossing zero is inconclusive, not proof of no effect. A large p-value is not equivalence. Guardrail noninferiority requires a prespecified margin and adequate power. Exploratory segments need multiplicity handling and later validation.

Return the estimand, counts, exclusions, effect and uncertainty, SRM, guardrails, decision, and next evidence needed. A script's candidate result is never an automatic ship decision. If the design or a guardrail is missing, label the recommendation conditional. Save exact inputs and commands.

For helper commands and input formats, see [the runnable tools](../../references/tools.md) when needed. Resolve script paths relative to this skill: `../../scripts/analyze.py`.

Read the [worked failure case](../../references/worked-failures.md#experiment-analysis) when checking a plausible but unsupported answer.
