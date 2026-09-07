---
name: exploratory-analysis
description: Explore an unfamiliar dataset and identify useful, testable questions without overstating patterns.
---

# Learn what is worth testing

Read [the working agreement](../../references/working-agreement.md) when using this skill. It defines source, privacy, execution, and evidence boundaries.

Start with the unit, collection process, coverage, and intended decision. Run the relevant data-quality checks. Separate identifiers from measurements and ordinal from nominal categories. Use bounded inspection before loading large files fully.

Inspect univariate distributions, quantiles, missingness, outliers, and segment counts before pairwise relationships. Prefer robust summaries for skewed data. An outlier may be a valid high-value case; retain the original and show sensitivity to a stated handling rule.

Distinguish exploration from confirmation. Track the comparisons tried. Avoid p-value fishing and explaining the best-looking slice as if it had been prespecified. Show denominators and uncertainty where the sampling model supports it.

For associations, check time trends, confounding, selection, Simpson's paradox, and nonlinearity. Treat clustering and embeddings as exploratory structure, not discovered ground truth. Prevent target leakage when exploration feeds modeling.

Deliver a concise data map, a few decision-relevant findings with supporting calculations, unresolved data problems, and ranked questions worth testing next. Include rerunnable code and a record of transformations; do not dump every chart.

For helper commands and input formats, see [the runnable tools](../../references/tools.md) when needed. Resolve script paths relative to this skill: `../../scripts/analyze.py`.
