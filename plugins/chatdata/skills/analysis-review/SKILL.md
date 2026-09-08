---
name: analysis-review
description: Independently scrutinize an analysis for arithmetic, methodology, evidence, and unsupported claims.
---

# Try to make the conclusion fail

Read [the working agreement](../../references/working-agreement.md) when using this skill. It defines source, privacy, execution, and evidence boundaries.

Read the actual inputs, code, output, and definition. A confident narrative or another agent's summary is not proof. Recompute at least one decision-critical result from raw or independently aggregated data when access allows.

Review grain, denominator, cohort maturity, freshness, join multiplication, missingness, selection, multiplicity, statistical assumptions, leakage, and causal language as relevant to the method. Test a boundary case that would produce a plausible but wrong answer.

Compare the conclusion with the stated evidence. Check whether an interval answers the decision, whether a sensitivity analysis can reverse it, and whether the strongest alternative explanation was tested. Separate calculation correctness from source correctness and interpretation.

For reusable work, inspect the analysis record: source version or hash, code/command, parameters, expected checks, caveats, and expiration trigger. Missing reproducibility should block a claim of verified reuse, not force a fabricated source path.

Deliver findings in order of decision impact, each with evidence, correction, and retest. Return supported, supported with limitations, or not supported for the stated conclusion. Record checks not run. Apply straightforward local fixes within scope and rerun relevant checks; do not merely list repairable defects.

For helper commands and input formats, see [the runnable tools](../../references/tools.md) when needed. Resolve script paths relative to this skill: `../../scripts/analyze.py`.

Read the [worked failure case](../../references/worked-failures.md#analysis-review) when checking a plausible but unsupported answer.
