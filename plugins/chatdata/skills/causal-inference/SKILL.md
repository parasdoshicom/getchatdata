---
name: causal-inference
description: Assess causal claims or design observational estimates with explicit assumptions and falsification checks.
---

# Separate an association from an intervention effect

Read [the working agreement](../../references/working-agreement.md) when using this skill. It defines source, privacy, execution, and evidence boundaries.

Define the treatment, outcome, target population, assignment mechanism, time zero, follow-up, and estimand. Draw the assumed causal structure or write it explicitly. Name confounders, mediators, colliders, and post-treatment variables before choosing adjustments.

Prefer randomized evidence when available and valid. For observational data, explain why a method is identified: conditional exchangeability and overlap for weighting/matching; parallel trends and no anticipation for difference-in-differences; continuity/no manipulation for regression discontinuity; exclusion, relevance, and independence for instruments.

Check overlap and covariate balance for propensity methods. For panel interventions, inspect pretrends and composition changes; use an estimator appropriate for staggered timing and heterogeneous effects instead of blindly using two-way fixed effects. Cluster standard errors at the treatment assignment level when justified.

Use negative controls, placebo dates/outcomes, sensitivity analysis, and alternative reasonable specifications. A failed diagnostic can invalidate an estimate; a passed diagnostic does not prove untestable assumptions. Do not adjust away the treatment's effect through mediators when estimating a total effect.

Deliver the estimand, identification assumptions, diagnostics, effect with justified uncertainty, threats, and what additional evidence would change the conclusion. When the design cannot support causation, provide a descriptive result and a feasible identification plan.

For helper commands and input formats, see [the runnable tools](../../references/tools.md) when needed. Resolve script paths relative to this skill: `../../scripts/analyze.py`.
