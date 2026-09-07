---
name: visualization
description: Create analytical charts or dashboards that show the decision, denominators, uncertainty, and sources.
---

# Show the comparison the reader needs

Read [the working agreement](../../references/working-agreement.md) when using this skill. It defines source, privacy, execution, and evidence boundaries.

Identify the reader's decision and choose an encoding for it: position for comparisons, lines for time, scatter for relationships, and small multiples for consistent segment comparisons. Use tables when precise lookup is the task. Avoid charts that merely decorate a statistic.

Use a zero baseline for bars unless a different encoding makes the nonzero baseline explicit. Label units, dates, population, source, and sample size. Show uncertainty and missing periods. Do not interpolate through unobserved data as though it were measured. Use direct labels, legible type, and colors distinguishable without color alone.

Compare like periods, scales, and denominators. A dual axis can manufacture a visual correlation. Aggregated series may hide a mix shift; show the partition when it changes the decision. Annotate known events without asserting that they caused a movement.

Build the artifact with the user's available tools. Verify plotted values against the calculation, inspect the rendered result at its intended size, and fix clipping, unreadable legends, misleading axes, and inaccessible contrast. For dashboards, test filter effects on numerator and denominator together.

Deliver the chart or file, a short interpretation, source and refresh date, and any material limitation. Keep notebook rendering, export, or publication status explicit. Do not publish or upload private data without authorization.

For helper commands and input formats, see [the runnable tools](../../references/tools.md) when needed. Resolve script paths relative to this skill: `../../scripts/analyze.py`.
