---
name: funnel-analysis
description: Measure ordered conversion steps, drop-off, and time to convert from event data.
---

# Count people in the right order

Read [the working agreement](../../references/working-agreement.md) when using this skill. It defines source, privacy, execution, and evidence boundaries.

Define the identity, entry event, ordered steps, attribution window, timezone, conversion horizon, and entry cohort. Inspect anonymous-to-known identity stitching and consent coverage. Count eligible users or accounts, not raw events. Clarify whether the funnel is open or closed and whether steps must be consecutive.

Use scripts/analyze.py funnel for a closed, ordered, user-level funnel on CSV columns user_id,event,timestamp. The helper uses the earliest entry per user, strict increasing timestamps, and a fixed horizon from entry. Equal timestamps are ambiguous and cannot establish order. It excludes entry cohorts whose whole conversion window has not elapsed by --as-of.

For a different re-entry, session, or equal-time rule, change the definition and implementation explicitly. Inspect duplicate events, late arrival, broken step names, multiple devices, bots, and missing identities. Do not silently drop bad records. Build a deduplicated user-step spine before joining acquisition or revenue tables.

Show entry-to-step and adjacent-step conversion, counts, losses, and time to convert when available. Compare mature cohorts with the same follow-up. Segment on attributes measured at entry; decompose mix changes before blaming a step. Rank opportunities by recoverable volume with assumptions, not just the largest percent drop.

Deliver the funnel definition, excluded/unmatured counts, a step table, the highest-value diagnostic next query, and a rerunnable query or script. Mark causal explanations as hypotheses.

For helper commands and input formats, see [the runnable tools](../../references/tools.md) when needed. Resolve script paths relative to this skill: `../../scripts/analyze.py`.

Read the [worked failure case](../../references/worked-failures.md#funnel-analysis) when checking a plausible but unsupported answer.
