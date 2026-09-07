---
name: data-science
description: Set up ChatData, verify its local examples, or choose and carry out a data science workflow for a question, dataset, or decision.
---

# Start with the decision

Use the installation that supplied this skill. In Claude Code its native root is `${CLAUDE_PLUGIN_ROOT}`: read references and run scripts under that resolved absolute path. In Codex, resolve `../../` from the absolute path of this loaded SKILL.md; in a project install use this skill folder itself. Never search the home directory, choose a different ChatData installation, or substitute hosted MCP setup. If this installation cannot be resolved, report the missing path and stop.

Read [the working agreement](../../references/working-agreement.md) when using this skill. It defines source, privacy, execution, and evidence boundaries.

For installation, setup checks, or a first run without customer data, read [the first-run guide](../../references/first-run.md). When asked to verify setup, invoke Python explicitly; do not execute the .py file directly. In Claude Code run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py"`. In Codex or a project install, first resolve the script from this loaded SKILL.md as described above, then run `python3 "<resolved absolute path>/scripts/doctor.py"`. It runs three synthetic checks without network access or file writes. Explain its scope honestly: local helpers passed, while client discovery and live data are separate checks. If asked to try an analysis, continue through the example and save a usable record; a diagnostic printout alone is not the first analysis.

Identify the decision, the available data, and the cost of a wrong answer. If the user is unsure, offer one concrete starting question and explain what its answer would change. Ask only for missing details that change the method; inspect provided files first.

Route by the question:
- Is this experiment trustworthy? Use experiment-analysis. Before launch, use experiment-design.
- Where do people drop off? Use funnel-analysis. Why did the total move? Use root-cause.
- Do people come back? Use retention. Are the inputs usable? Use data-quality.
- What is in this file? Use exploratory-analysis. What should this metric mean? Use metric-definition.
- Is this query correct? Use sql-review. What happens next? Use forecasting.
- Can we predict an outcome? Use predictive-modeling. Did an intervention cause it? Use causal-inference.
- How should we show it? Use visualization. What should we decide? Use decision-brief.
- Can this analysis survive scrutiny? Use analysis-review.

Read the selected sibling SKILL.md, then execute it. In a project skills install, folder and skill names have a chatdata- prefix; locate the matching installed skill. Do not load all skills. Continue through calculation, relevant checks, and a usable result within the user's authorized scope. Planning alone does not complete an analysis.

For a first run without data, use the bundled synthetic examples. Explain that example outputs are not evidence about the user's business. For a new recurring question, create a small local definition and rerun record after the user has reviewed its assumptions.

For helper commands and input formats, see [the runnable tools](../../references/tools.md) when needed. Resolve script paths relative to this skill: `../../scripts/analyze.py`.
