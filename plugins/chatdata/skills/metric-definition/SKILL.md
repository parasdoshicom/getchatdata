---
name: metric-definition
description: Define a KPI, denominator, cohort, or source of truth before calculating a business metric.
---

# Make the question measurable

Read [the working agreement](../../references/working-agreement.md) when using this skill. It defines source, privacy, execution, and evidence boundaries.

Inspect existing definitions, source schemas, and approved queries before drafting a new definition. For an existing project, read [the local context guide](../../references/local-context.md) and use its visible `chatdata-context/` folder when present. Do not scan the home directory or global client history. Its recent-file inventory is based on filesystem modification time, not proof of use, and setup does not read or move source files or make a network request.

Before calculating or stating a named metric as canonical, run the local context check for the explicit project and exact metric name. If it reports `blocked`, stop the canonical answer and show each missing, stale, changed, or conflicting item with its next action. Do not invent a definition, choose silently between conflicts, mark checks passed without local evidence, or claim the user reviewed a draft. Explicit exploratory work remains allowed when clearly labeled exploratory; bundled examples remain allowed when clearly labeled synthetic.

The bundled Apache Ossie `0.2.0.dev0` snapshot provides the draft JSON shape for local semantic models. ChatData's validator covers only the schema features in that pinned file. Structural validity is not official full Ossie validation, evidence that a metric is correct, or user approval. A person must actually review the matching trust entry before `reviewed_by_user` can be true.

Specify the unit (person, account, event, subscription), numerator, denominator, eligibility, exclusions, timezone, observation window, aggregation rule, source, and data delay. Name the decision and who can settle an ambiguity. For ratios, aggregate numerator and denominator before division; do not average subgroup rates without the right weights.

Use a worked boundary case: a returning person, a refund, a duplicate event, a late-arriving record, or an account with several users. Show whether it belongs and why. Separate stocks from flows, booked from collected revenue, event time from ingestion time, and active users from automated traffic.

If two definitions give different answers, calculate both only if safe and affordable and explicitly requested as an exploratory comparison. Label them and ask which matches the decision. Do not silently pick the larger number or call either canonical while the conflict remains. Save the proposed contract using the analysis-record template, marked proposed until the user approves it.

Deliver the definition, a source mapping, testable boundary cases, and remaining decisions. State when the requested metric cannot be computed from the supplied data.

For helper commands and input formats, see [the runnable tools](../../references/tools.md) when needed. Resolve script paths relative to this skill: `../../scripts/analyze.py`.
