# What ChatData can do

ChatData is built for one person doing serious data work with an AI coding client. It gives that client 16 data science skills, a shared working agreement, seven runnable analytical checks, six synthetic example files, and a reusable analysis-record format.

The aim is practical: help one data scientist move from a question to a checked, rerunnable answer without needing another specialist beside them. ChatData does not claim that installing a prompt file creates expertise or produces a measured 10× gain. It makes the methods, checks, deliverables, and stopping conditions explicit so the person using the model can demand better work.

Each skill below explains when to use it, what to provide, what the agent should check, what you should receive, and where the method stops. You can copy the prompts as written and replace the bracketed parts.

## How the skills work together

You do not need to choose all 16 skills for one question. Start with **data-science** when you are unsure. It inspects the question and routes the work to the narrowest useful method. A typical analysis may use three skills:

1. **metric-definition** makes the population, denominator, window, and source explicit.
2. A method skill such as **experiment-analysis**, **funnel-analysis**, **root-cause**, or **retention** performs the analysis and its checks.
3. **analysis-review** tries to break the conclusion before you act on it.

Use **visualization** when the result needs a chart and **decision-brief** when another person needs to make a decision from it. The agent should read only the relevant skills and use the tools already available in your environment. It should complete the calculation rather than return a generic plan.

For analysis worth keeping, ask the agent to save a local [analysis record](../plugins/chatdata/references/analysis-record.md). The record captures the definition, source and cutoff, exact command or query, assumptions, result, checks, caveats, and the conditions that would make reuse unsafe.

## 1. Data science workflow

[Read the skill](../plugins/chatdata/skills/data-science/SKILL.md)

Use this when you have a business question, dataset, query, or decision but are not sure which method belongs. It is also the setup and first-run skill.

**Give it:** the decision you need to make, the data or files already available, the time period, and what a wrong answer would cost. The skill should inspect supplied files before asking you to repeat information already present.

**It should:** choose one relevant specialist skill, run the calculation, perform the checks that matter for the decision, and return a usable result. It should not load every skill, stop at a project plan, or treat a synthetic example as evidence about your business.

**Ask:**

> Use ChatData’s data-science skill. I need to decide [decision]. Inspect [files/query/results] first. Choose the right workflow, run the analysis and relevant checks, and save a proposed analysis record in [local path]. Tell me which assumptions could change the decision.

**Expect:** a clear question, the selected method and reason, inspected sources, calculations or code, checked outputs, a result tied to the decision, and an analysis record when requested.

**Limit:** the routing skill does not create access to a database or make an unsupported question measurable. Its setup doctor verifies five bundled calculations. That does not prove client skill discovery, live-source access, or the correctness of every later model response.

## 2. Metric definition

[Read the skill](../plugins/chatdata/skills/metric-definition/SKILL.md)

Use this before calculating a KPI whose meaning is still fuzzy. Many wrong answers start with an unstated denominator, mixed populations, incompatible time windows, or a source chosen because it gives the more convenient number.

**Give it:** the decision, existing definitions and approved queries, available schema, data delay, and the awkward cases that might belong in or out.

**It should define:** unit, numerator, denominator, eligibility, exclusions, timezone, observation window, aggregation rule, source, and expected delay. For ratios, it should aggregate numerator and denominator before division. It should test concrete boundary cases such as a refund, returning user, duplicate event, late record, automated visit, or account with several users.

**Ask:**

> Define [metric] for the decision [decision]. Inspect the existing query and schema. Specify the unit, numerator, denominator, population, exclusions, timezone, window, source, and delay. Test [two boundary cases]. If two reasonable definitions disagree, show both and ask me to choose before calling either one canonical.

**Expect:** a complete metric contract, source-to-field mapping, boundary-case table, calculation feasibility, and unresolved decisions. The definition remains proposed until the actual owner approves it.

**Limit:** ChatData cannot make a definition canonical by assertion. If the supplied data cannot represent the denominator or exclusion rule, the skill should say the metric cannot yet be computed.

## 3. Experiment design

[Read the skill](../plugins/chatdata/skills/experiment-design/SKILL.md)

Use this before launching an A/B test. It starts from the decision and the smallest effect worth acting on, then works backward to the design.

**Give it:** hypothesis, action if successful, smallest useful effect, primary metric, baseline, eligible traffic, randomization unit, eligibility, exposure rule, analysis population, expected outcome delay, and guardrails.

**It should check:** power, allocation, minimum duration, relevant business cycles, missingness, multiple variants or metrics, interference, contamination, carryover, novelty, seasonality, instrumentation, sample-ratio mismatch plans, and whether outcomes can mature before the decision. It should predeclare alpha, power, exclusions, ramp, guardrails, and a stopping rule. It should not invent a sequential method after someone has already peeked at results.

**Ask:**

> Design an experiment for [change]. The decision is [decision], baseline is [rate], eligible traffic is [count per week], and the smallest absolute effect worth acting on is [effect]. Define randomization, exposure, population, primary metric, guardrails, duration, power, exclusions, ramp, stopping rule, and launch checks. Flag every input you had to assume.

**Expect:** a testable hypothesis, power calculation or justified simulation, analysis population, instrumentation checks, decision rule, and launch-readiness verdict with exact missing inputs.

**Limit:** the bundled power helper covers equal-allocation, independent binary outcomes using a normal approximation. Continuous revenue, repeated events, or clustered assignment require an appropriate variance model or simulation. The skill can design and vet a test; it does not launch one without authorization.

## 4. Experiment analysis

[Read the skill](../plugins/chatdata/skills/experiment-analysis/SKILL.md)

Use this to analyze an A/B result or challenge a claim that one variant won. The skill checks whether assignment and measurement are trustworthy before interpreting lift.

**Give it:** the experiment design, planned allocation, assignment and exposure counts, outcome counts or observations, primary metric, smallest meaningful effect, horizon, exclusions, invariant metrics, and guardrails.

**It should check:** sample-ratio mismatch, absolute and relative lift, uncertainty, observation maturity, attrition, missingness, delayed outcomes, treatment leakage, denominator changes after treatment, invariant metrics, and guardrails. It should distinguish evidence of some benefit from evidence of enough benefit to justify action. A wide interval or large p-value must not be described as proof of no effect.

**Ask:**

> Vet this experiment before calling a winner. Planned allocation was [allocation]. The primary metric and minimum useful effect were [definition/effect]. Use the assignment counts, exposure counts, outcomes, exclusions, horizon, and guardrails in [file]. Check sample-ratio mismatch, maturity, effect size, uncertainty, and practical significance. Return a conditional decision when design evidence is missing.

**Expect:** estimand, counts and exclusions, assignment check, absolute and relative effect, confidence bounds, guardrail status, decision, and the next evidence needed.

**Runnable check:** the bundled helper analyzes two independent groups with binary outcomes. It reports sample-ratio mismatch, Wilson/Newcombe uncertainty, absolute percentage-point difference, relative lift, and a descriptive result. See [the exact command and assumptions](../plugins/chatdata/references/tools.md#experiment-readout).

**Limit:** repeated users, clusters, paired observations, continuous outcomes, and heavy-tailed revenue need another estimator. The helper's candidate result is not an automatic ship decision.

## 5. Funnel analysis

[Read the skill](../plugins/chatdata/skills/funnel-analysis/SKILL.md)

Use this to measure an ordered journey, locate drop-off, or compare conversion across mature cohorts. It avoids the common mistake of counting events that occurred out of order or people who have not had enough time to convert.

**Give it:** entity identifier, entry event, ordered steps, timestamp and timezone, entry cohort, conversion horizon, identity rules, and whether the funnel is open or closed.

**It should check:** entity counts rather than event counts, strict ordering, duplicates, late arrivals, broken event names, anonymous-to-known stitching, multiple devices, bots, missing identities, and cohort maturity. It should show entry-to-step and adjacent-step conversion, counts, losses, and time to convert when available. Segments should use attributes known at entry.

**Ask:**

> Build a [closed/open] funnel for [population] from [entry] through [ordered steps]. Use a [duration] conversion window in [timezone]. Check duplicate and out-of-order events, identity gaps, late data, and immature entry cohorts. Show counts, entry-to-step rates, adjacent-step rates, losses, and the highest-value next diagnostic query.

**Expect:** funnel definition, excluded and immature counts, step table, conversion timing, segmentation assumptions, one diagnostic next query, and rerunnable SQL or code.

**Runnable check:** the CSV helper uses earliest entry, strict increasing timestamps, and a fixed horizon. Its synthetic fixture returns 3 visits, 2 signups, and 1 purchase while excluding one immature user, removing one duplicate, and refusing to credit an out-of-order purchase.

**Limit:** re-entry, sessions, equal timestamps, consecutive-step rules, or open funnels need an explicit alternative definition and implementation. The skill should label explanations for drop-off as hypotheses unless causal evidence supports them.

## 6. Root-cause analysis

[Read the skill](../plugins/chatdata/skills/root-cause/SKILL.md)

Use this when a metric moved and you need to know where the movement occurred before speculating about why.

**Give it:** baseline and current periods, metric definition, source, observation cutoff, timezone, comparable calendar periods, and grounded segments such as channel, platform, geography, tenure, or product.

**It should first rule out:** partial periods, data delay, renamed events, source changes, duplicate joins, and incompatible definitions. For rates, it should separate a change in population mix from a change inside segments and reconcile every contribution to the total. It should build a small hypothesis table with mechanism, predicted evidence, evidence for, evidence against, and next test. It should try to disprove the leading explanation.

**Ask:**

> Investigate why [metric] changed from [before] to [after]. Reproduce both values from the same source, definition, cutoff, and timezone. Rule out measurement problems first. Decompose the change across [grounded partition], reconcile to the total, and separate mix from within-segment performance. Give me ranked hypotheses, contrary evidence, and the next test for each.

**Expect:** reproduced headline values, measurement checks, arithmetic bridge, reconciliation residual, ranked hypotheses, ruled-out explanations, and a next action tied to evidence.

**Runnable check:** the rate-decomposition helper uses a symmetric Shapley allocation. The bundled example falls from 17% to 8%; unchanged segment rates mean all −9 percentage points come from customer mix.

**Limit:** arithmetic attribution says where a change occurred. It does not establish what caused the population or behavior to change. Segments must be unique, disjoint, and exhaustive; zero-denominator cells need explicit treatment.

## 7. Retention and churn

[Read the skill](../plugins/chatdata/skills/retention/SKILL.md)

Use this for cohort retention, repeat purchase, churn, resurrection, or time-to-event analysis. The skill keeps cohort age separate from calendar time and refuses to turn incomplete follow-up into zeros.

**Give it:** cohort entry event, entity, return event, interval, timezone, eligibility, data coverage, and the chosen definition: exact-period, rolling, bracket, repeat purchase, gross revenue, net revenue, or survival.

**It should check:** fixed cohort membership, period-zero consistency, at-risk denominators, cohort maturity, data coverage changes, delayed activation, migration, cancellation timing, reactivation, survivor bias, censoring, and competing risks. It should show counts with rates and compare cohorts at equal ages.

**Ask:**

> Build [retention/churn/repeat-purchase] cohorts from [entry] and [return/outcome] for [entity]. Define eligibility, timezone, interval, and denominator. Mask cells without enough follow-up. Show counts and rates at equal cohort ages, inspect resurrection and coverage changes, and explain which lifecycle moment deserves the next investigation.

**Expect:** definition, entity-period spine, cohort table with immature cells masked, retention curve, denominator checks, and a decision-relevant interpretation.

**Limit:** a few early retention points do not support a confident lifetime-value estimate. Survival work requires explicit event and censoring definitions; competing risks may need a different estimator.

## 8. Data quality

[Read the skill](../plugins/chatdata/skills/data-quality/SKILL.md)

Use this to decide whether data is fit for a specific analysis. It reports the impact of each issue instead of collapsing everything into a generic quality score.

**Give it:** dataset or schema, intended analysis, row grain, expected keys, event and ingestion times, expected coverage, source relationships, and how much error the decision can tolerate.

**It should check:** uniqueness, missingness, types, ranges, category drift, referential integrity, impossible sequences, timestamp bounds, distribution changes, and source reconciliation. Before a join, it should record each table's grain, key cardinality, and expected row multiplier. Afterward, it should reconcile rows, entities, amounts, and unmatched keys. Missingness should be checked by outcome, treatment, and important segments when relevant.

**Ask:**

> Decide whether [dataset] is fit for [analysis/decision]. Identify row grain and keys, then test missingness, duplicates, types, ranges, time coverage, impossible values, category drift, and join cardinality. Quantify each issue, its likely effect on the answer, and a fix or sensitivity bound. Return usable, usable with limitations, or blocked for this question.

**Expect:** source map, checks with affected counts and shares, before-and-after join reconciliation, issue impact, cleaned-output location when authorized, and a suitability verdict.

**Runnable check:** the CSV profiler counts rows, columns, missing values, duplicate rows, and duplicate keys without printing raw cell values.

**Limit:** structural profiling cannot prove freshness, representativeness, business validity, or fitness for every future question. The small-file helper loads CSV rows into memory; large sources need bounded queries or chunking.

## 9. SQL review

[Read the skill](../plugins/chatdata/skills/sql-review/SKILL.md)

Use this to write or review analytical SQL where a plausible result could still be wrong because of grain, joins, filters, time boundaries, or ratios.

**Give it:** SQL dialect, query, schemas, source grain, expected result grain, key relationships, timezone, metric definition, and any verified reference totals.

**It should check:** join cardinality, preaggregation, NULL behavior, `COUNT(*)` versus `COUNT(column)`, `DISTINCT` hiding multiplication, filters that turn a `LEFT JOIN` into an `INNER JOIN`, integer division, divide-by-zero, sum-of-ratios mistakes, and future information leakage. It should use half-open time ranges and explicit timezone. Window functions need declared partition keys, ordering, tie breakers, and frame bounds.

**Ask:**

> Review this [dialect] query for [metric/decision]. State source and output grain. Inspect schemas before assuming columns. Check joins, NULLs, deduplication, ratio math, time boundaries, timezone, window frames, and leakage. Validate duplicates, NULLs, boundary timestamps, empty groups, and a one-to-many join. Reconcile one independent total and say whether the query was actually run.

**Expect:** corrected query, changed assumptions, execution status, observed cost when available, fixture checks with expected and actual results, and an independent reconciliation.

**Limit:** reading a query does not prove it ran. A `LIMIT` may reduce returned rows while still scanning the full source. The skill should report cost only when the source exposes it.

## 10. Exploratory analysis

[Read the skill](../plugins/chatdata/skills/exploratory-analysis/SKILL.md)

Use this when a dataset is unfamiliar and you need to learn which questions are worth testing. The skill separates discovery from confirmation so the most surprising slice does not become an invented conclusion.

**Give it:** the dataset, collection process, coverage, intended decision, known identifiers, and any constraints on loading or query cost.

**It should check:** grain and quality first, then distributions, quantiles, missingness, outliers, segment counts, time trends, confounding, selection, Simpson's paradox, nonlinearity, and target leakage. It should use robust summaries for skewed data and keep valid high-value outliers visible through sensitivity analysis. It should track comparisons tried.

**Ask:**

> Explore [dataset] to find questions worth testing for [decision]. Start with unit, collection process, coverage, quality, distributions, missingness, and outliers. Track the comparisons you try. Check time trends, selection, confounding, Simpson’s paradox, nonlinearity, and leakage. Return a concise data map, a few supported findings, unresolved problems, and ranked follow-up questions with rerunnable code.

**Expect:** data map, quality issues, compact set of calculations and charts, transformations, a few findings with denominators, and ranked confirmatory questions.

**Limit:** clusters, embeddings, correlations, and the best-looking slice are exploratory structure. They are not automatically stable, prespecified, causal, or ready for a decision.

## 11. Forecasting

[Read the skill](../plugins/chatdata/skills/forecasting/SKILL.md)

Use this to forecast a time series when the result will drive staffing, inventory, budget, capacity, or another dated decision.

**Give it:** target, dated history, forecast horizon, decision cadence, aggregation, known future inputs, delayed labels, and the costs of over- and under-prediction.

**It should check:** gaps, false versus real zeros, changing exposure, seasonality, structural breaks, an untouched temporal holdout, naive and seasonal-naive baselines, rolling-origin evaluation, leakage-safe preprocessing, horizon-matched error, and interval coverage by horizon. Future features must be known at prediction time or identified as scenario assumptions.

**Ask:**

> Forecast [target] from [history] for [dated horizon] to support [decision]. Keep a temporal holdout and use rolling-origin evaluation. Compare naive and seasonal-naive baselines before adding complexity. Check gaps, zeros, seasonality, structural breaks, future-feature availability, and interval coverage. Save split dates, code, data version, assumptions, and a refresh trigger.

**Expect:** baseline table, backtest design, held-out error, chosen model and reason, dated forecast with uncertainty, scenario assumptions, known failure modes, and refresh trigger.

**Limit:** in-sample fit is not forecast validation. Near-zero actuals can make MAPE unstable. Sparse history or a regime shift may justify scenario ranges instead of a precise forecast.

## 12. Predictive modeling

[Read the skill](../plugins/chatdata/skills/predictive-modeling/SKILL.md)

Use this to build or evaluate a model that predicts an outcome for a defined action. The skill makes the prediction moment explicit so future information does not leak into training.

**Give it:** prediction moment, label and delay, entity, intended action, error costs, feature availability at that moment, historical data, and operational constraints.

**It should check:** time or group splits, training-only preprocessing, a simple baseline, target prevalence, actionable thresholds, precision and recall, confusion counts, calibration, subgroup performance, residuals, asymmetric loss, feature stability, missing-feature behavior, distribution shift, and leakage. Test data should stay out of feature selection, tuning, and threshold choice.

**Ask:**

> Build or evaluate a model that predicts [label] at [prediction moment] for [action]. List only features available at that moment. Use a time or group split that matches production, fit preprocessing on training data, compare a simple baseline, and inspect calibration, actionable thresholds, subgroup errors, residuals, shift, and leakage. Return a model card with training and inference commands.

**Expect:** data and split provenance, baseline comparison, held-out metrics, threshold rationale, error and subgroup analysis, leakage checks, training and inference commands, intended-use limits, and monitoring signals.

**Limit:** feature importance and SHAP values describe model behavior; they do not show the causal effect of changing a feature. Deployment and automated decisions about people need separate authorization and appropriate domain review.

## 13. Causal inference

[Read the skill](../plugins/chatdata/skills/causal-inference/SKILL.md)

Use this when someone claims an intervention caused a result or when a randomized experiment is unavailable and you need an observational design.

**Give it:** treatment, outcome, target population, assignment mechanism, time zero, follow-up, desired estimand, available covariates, and an explicit causal diagram or written structure.

**It should check:** confounders, mediators, colliders, post-treatment controls, identification assumptions, overlap and balance, pretrends and composition, manipulation near cutoffs, instrument relevance and exclusion, assignment-level clustering, negative controls, placebo outcomes or dates, sensitivity, and alternate specifications. The chosen diagnostics depend on the design.

**Ask:**

> Assess whether [intervention] caused [outcome] for [population]. Define treatment, outcome, time zero, follow-up, and estimand. Write the assumed causal structure and name confounders, mediators, colliders, and post-treatment variables. Explain the identification assumptions for [proposed design], run its diagnostics and falsification checks, and return a descriptive answer when causation is not supported.

**Expect:** estimand, causal structure, identification argument, estimator, diagnostics, effect with uncertainty, sensitivity results, threats, and the evidence that would change the conclusion.

**Limit:** observed diagnostics cannot prove untestable assumptions. When the design does not identify an intervention effect, the useful answer is a descriptive result plus a feasible evidence plan.

## 14. Visualization

[Read the skill](../plugins/chatdata/skills/visualization/SKILL.md)

Use this to turn a checked result into a chart or dashboard that supports a particular comparison or decision.

**Give it:** the reader and decision, checked calculation, source and refresh date, intended display size, output format, and charting tools available in your environment.

**It should check:** encoding choice, denominators, comparable scales and periods, uncertainty, missing periods, source, sample size, bar baselines, dual-axis risks, mix shifts, direct labeling, color independence, filter behavior, and exact plotted values. It should inspect the rendered output and fix clipping, unreadable legends, misleading axes, and low contrast.

**Ask:**

> Create a [chart/dashboard] for [reader] deciding [decision] from the checked calculation in [path]. Choose the simplest encoding for the comparison. Label units, dates, population, source, sample size, uncertainty, and missing periods. Verify plotted values against the calculation and inspect the rendered result at [size] for clipping, axes, legends, and accessible contrast.

**Expect:** chart file, verified value mapping, a short interpretation, source and refresh date, material limitation, and explicit status for rendering or export.

**Limit:** the skill uses the charting tools already available in your client or project. It does not publish or upload a private chart without authorization.

## 15. Decision brief

[Read the skill](../plugins/chatdata/skills/decision-brief/SKILL.md)

Use this after analysis when a decision-maker needs the result, the case against it, and the evidence that changes the recommendation.

**Give it:** decision, checked analysis, alternatives, costs, reversibility, timing, source record, and an owner or deadline only when those are known.

**It should:** lead with the recommendation and confidence, separate observations from estimates and assumptions, include denominators and periods, show effect size and uncertainty, present the strongest contrary evidence, compare meaningful alternatives, and convert uncertainty into a bounded next action.

**Ask:**

> Turn [analysis path] into a decision brief for [decision]. Lead with the recommendation and confidence. Keep facts, estimates, assumptions, and hypotheses separate. Include denominators and periods for every important number, the strongest evidence against the recommendation, alternatives, and the result that would change the decision. Do not invent an owner, deadline, urgency, benchmark, or savings estimate.

**Expect:** decision, evidence, uncertainty, limitations, alternatives, next action, and links to the local calculation and source record.

**Limit:** the skill does not invent missing organizational details or publish the brief. Sending it to someone is a separate action that requires authorization.

## 16. Analysis review

[Read the skill](../plugins/chatdata/skills/analysis-review/SKILL.md)

Use this before relying on an important analysis, including work produced with ChatData. It starts from the actual inputs, code, output, and definition rather than trusting a polished summary.

**Give it:** raw or independently aggregated inputs, calculation code or query, outputs, metric definition, source cutoff, and the analysis record.

**It should check:** arithmetic, grain, denominator, cohort maturity, freshness, join multiplication, missingness, selection, multiplicity, statistical assumptions, target leakage, causal language, sensitivity, contrary evidence, and reproducibility. When access allows, it should recompute one decision-critical result and test a boundary case that could create a plausible wrong answer. Straightforward local defects should be fixed and retested.

**Ask:**

> Try to make the conclusion in [analysis path] fail. Read the actual inputs, code, output, definition, and record. Recompute one decision-critical result if possible. Check grain, denominator, maturity, freshness, joins, missingness, selection, multiplicity, assumptions, leakage, and causal language. Test a plausible boundary case and a sensitivity that could reverse the decision. Fix local defects you can verify, rerun the relevant checks, and return supported, supported with limitations, or not supported.

**Expect:** findings ordered by decision impact, evidence for each finding, corrections, retest results, unrun checks, contrary evidence, and a final support verdict for the stated conclusion.

**Limit:** review can verify only what it can inspect. Missing inputs or reproducibility block a claim that the result was independently verified; they do not justify invented evidence.

## The seven bundled analytical checks

The skills can use the Python, SQL, notebook, visualization, and data tools already available in your environment. ChatData also ships small Python helpers for seven common checks. They use only the Python 3.9+ standard library.

| Command | What it calculates | Main guardrail |
| --- | --- | --- |
| `experiment` | Two-group binary rates, absolute and relative lift, uncertainty, sample-ratio mismatch | Withholds a clean winner when assignment counts conflict with the planned allocation |
| `power` | Approximate per-arm sample size for an independent binary outcome | Makes baseline, absolute effect, alpha, power, and equal allocation explicit |
| `funnel` | Closed, ordered, user-level funnel from a CSV | Enforces strict order and fully mature conversion windows |
| `decompose` | Before/after rate change split into mix and within-segment contributions | Requires an exhaustive partition and reconciles contributions to the total |
| `profile` | CSV rows, columns, missingness, duplicate rows, and duplicate keys | Does not print raw cell values or claim that structure proves business validity |
| `retention.py` | Exact daily, weekly, or monthly cohort retention from separate cohort and activity CSVs | Masks incomplete periods, fixes denominators, and rejects ambiguous membership or pre-entry activity |
| `join_audit.py` | Equality-join cardinality, output rows, and optional measure reconciliation for two CSV extracts | Blocks violated uniqueness, many-to-many fanout, and duplicated measures |

Every helper emits JSON. The original file-based commands include an input SHA-256 hash; the retention and join helpers instead return aggregates without input paths, row values, or keys. The detailed commands, formats, formulas, and method sources are in [Runnable analysis checks](../plugins/chatdata/references/tools.md).

## What a reusable answer contains

“Good answers don’t reset” depends on a visible record, not hidden memory. Ask ChatData to save:

- the question and decision;
- the complete definition, including unit, denominator, population, timezone, window, and exclusions;
- source and observation cutoff;
- local file hash or source version when available;
- exact query, command, parameters, dependencies, and random seed;
- result, units, effect size, and justified uncertainty;
- expected and actual checks, including failures and checks not run;
- evidence against the conclusion;
- limitations and unresolved questions;
- the action and evidence that would change it;
- freshness and definition conditions to recheck next time.

The record starts as **proposed**. It becomes **reviewed by user** only after a person actually reviews it. On the next run, point the agent at the local record and ask it to recheck source freshness, definitions, and expected invariants before reuse.

## What ChatData does not provide

ChatData includes an optional, read-only adapter for an existing local DuckDB file. It does not include a managed warehouse connection, managed data service, automatic experiment launcher, or model host. It does not provide automatic cross-client memory or guarantee that a model will follow every instruction. The local helper checks are deliberately small and inspectable. The 16 skills guide the model in using the authorized tools already present in your client and project.

The public [evaluation guide](evaluation.md) includes the measured planted-defect enforcement check and explains how to compare fresh model sessions without revealing conditions to the reviewer.
