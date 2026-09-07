---
name: metric-definition
description: Define a KPI, denominator, cohort, or source of truth before calculating a business metric.
---

# Make the question measurable

Read [the working agreement](../../references/working-agreement.md) when using this skill. It defines source, privacy, execution, and evidence boundaries.

Inspect existing definitions, source schemas, and approved queries before drafting a new definition. When ChatData MCP is connected, resolve its approved context first. It is optional for this free plugin; local definitions work too.

Specify the unit (person, account, event, subscription), numerator, denominator, eligibility, exclusions, timezone, observation window, aggregation rule, source, and data delay. Name the decision and who can settle an ambiguity. For ratios, aggregate numerator and denominator before division; do not average subgroup rates without the right weights.

Use a worked boundary case: a returning person, a refund, a duplicate event, a late-arriving record, or an account with several users. Show whether it belongs and why. Separate stocks from flows, booked from collected revenue, event time from ingestion time, and active users from automated traffic.

If two definitions give different answers, calculate both only if safe and affordable, label them, and ask which matches the decision. Do not silently pick the larger number. Save the proposed contract using the analysis-record template, marked proposed until the user approves it.

Deliver the definition, a source mapping, testable boundary cases, and remaining decisions. State when the requested metric cannot be computed from the supplied data.

For helper commands and input formats, see [the runnable tools](../../references/tools.md) when needed. Resolve script paths relative to this skill: `../../scripts/analyze.py`.
