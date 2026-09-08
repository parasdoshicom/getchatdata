# Worked failures

These are synthetic teaching cases, not customer results or claims about ChatData's performance. Read the case linked from the skill you are using. Each shows an answer that sounds reasonable, the evidence that breaks it, and what to return instead. Numerical examples are hand-checkable; they do not imply that a bundled helper implements every method described here.

## data-science

- **Tempting answer:** “Setup passed, so your project's activation rate is ready to report.”
- **Planted defect:** The local doctor passed its synthetic checks, but the requested project's activation definition has no user review and its source evidence is missing. No customer analysis ran.
- **Required check or stop:** Resolve this installation and the explicit project directory. Run the exact local metric context check. Stop the canonical activation answer when that check blocks it; never copy a synthetic rate into the business answer.
- **Corrected output:** Report the local helper checks separately from project readiness. List the missing review and source evidence with next actions. If the user requested an example, deliver a clearly labeled synthetic analysis and rerun record.

## metric-definition

- **Tempting answer:** “Weekly activation is 50%,” averaging mobile's 1/10 (10%) and desktop's 81/90 (90%).
- **Planted defect:** Segment rates received equal weight even though their eligible populations differ ninefold. The draft also leaves “activated” undefined.
- **Required check or stop:** Resolve the activation event, eligible population, week, and timezone from reviewed context. Stop a canonical answer if that definition is missing. For an explicitly exploratory comparison using these counts, aggregate numerators and denominators before division.
- **Corrected output:** With those counts, the pooled rate is 82/100 = 82%, alongside the two segment rates and denominators. Mark the contract proposed until the user reviews it; include the rules for duplicate activation events and returning users.

## data-quality

- **Tempting answer:** “The order table is complete and safe for an average-order-value report because it has no NULLs.”
- **Planted defect:** The file contains order A for $100 twice and order B for $50 once. Every field has a value, but the repeated order A has the same source record ID.
- **Required check or stop:** Test the declared order key and inspect duplicate provenance. Reconcile raw rows and amounts before creating a derivative. Confirm that the extra row is a duplicate ingest, rather than a legitimate revision or line item.
- **Corrected output:** Report three raw rows, two distinct orders, and $250 before correction. If the source confirms duplicate ingestion, the derivative contains $150 across two orders, for $75 average order value. Preserve the raw file and record the one rejected row and rule; if provenance remains unresolved, block the definitive average.

## exploratory-analysis

- **Tempting answer:** “This acquisition channel creates unusually loyal customers; prioritize it.”
- **Planted defect:** Of 40 inspected slices, the best has two returning users out of two eligible users. The analyst chose the slice after seeing the results, and people selected their own channels.
- **Required check or stop:** Record all comparisons tried, show the slice denominator, and check cohort maturity and acquisition mix. Treat the result as exploratory. Do not use the best-looking slice as a confirmed effect or causal explanation.
- **Corrected output:** “Two of two observed users returned; the sample is too small to support prioritizing the channel.” Include the broader distribution, mark the selected slice as exploratory, and propose a prespecified comparison on new mature data.

## experiment-design

- **Tempting answer:** “Randomize each session and stop as soon as conversion has p < 0.05.”
- **Planted defect:** People have multiple sessions and can receive both variants. The team inspects the proposed fixed-horizon test daily with no stopping rule or adjustment.
- **Required check or stop:** Define whether treatment acts on a person, account, or session. For a persistent user experience, assign consistently by person and power the test using independent people, not sessions. Choose a fixed horizon or a justified sequential design before launch.
- **Corrected output:** Deliver a launch plan with assignment unit, eligibility, primary outcome, minimum useful effect, allocation, maturity window, guardrails, and stopping rule. If baseline rate or unique eligible traffic is missing, mark sample size and launch readiness unresolved rather than guessing a duration.

## experiment-analysis

- **Tempting answer:** “Ship treatment: conversion increased from 20% to 25%.”
- **Planted defect:** A planned 50/50 assignment produced 6,000 control users and 4,000 treatment users, with 1,200 and 1,000 conversions. No evidence explains the assignment imbalance.
- **Required check or stop:** Check sample-ratio mismatch using assignment counts, then compare assignment and exposure logs. Investigate missing assignments, eligibility filters, and selective logging before interpreting outcomes. A favorable conversion interval cannot repair a broken comparison.
- **Corrected output:** Show the descriptive +5 percentage-point difference and the assignment mismatch, with a decision to withhold the winner claim. Name the logging or allocation evidence needed, and rerun the estimate only after the evidence justifies the comparison.

## funnel-analysis

- **Tempting answer:** “Two of two entrants purchased, so entry-to-purchase conversion is 100%.”
- **Planted defect:** User A purchased on January 1 and entered on January 2. User B entered on January 2 and purchased on January 3. Both have the two event names, but only B completed them in order.
- **Required check or stop:** For a closed funnel, use ordered events within a declared horizon. With a seven-day horizon and an as-of date of January 10, both entries are mature. Count each eligible person once. Inspect timestamps instead of intersecting sets of event names.
- **Corrected output:** Report two entrants and one ordered purchaser: 1/2 = 50%. Explain why A's earlier purchase does not qualify, and record the entry, timezone, horizon, as-of cutoff, and equal-timestamp policy.

## retention

- **Tempting answer:** “The January 20 cohort's week-one retention is 0%, much worse than the January 6 cohort.”
- **Planted defect:** The extract ends January 25. For a definition where week one is days 7 through 13 after entry, no January 20 entrant has completed that window. All timestamps use UTC.
- **Required check or stop:** Compare each person's entry time and full return window with the extract cutoff. Keep the original cohort denominator, including people who later churn. Mask unobserved cells instead of filling them with zero.
- **Corrected output:** Show week-one retention as unobserved for January 20, with the cohort count and maturity cutoff. Compare only cohorts with complete follow-up at the same age. State the exact return event and day-window convention.

## root-cause

- **Tempting answer:** “Conversion fell from 18% to 12% because traffic mix changed, so rolling back the new checkout would do nothing.”
- **Planted defect:** In period one, channel A converts 16/80 and B converts 2/20. In period two, A converts 4/20 and B converts 8/80. Within-channel rates remain 20% and 10%; traffic shifted toward B.
- **Required check or stop:** Reconcile totals and decompose the rate using exhaustive, disjoint channel groups. Check comparable periods and measurement before attributing the movement. Investigate why channel mix changed separately from checkout behavior.
- **Corrected output:** Show 18/100 versus 12/100, a -6 percentage-point mix contribution, and zero within-channel contribution. The arithmetic explains where the decline came from. It neither supports nor rules out rollback. The checkout's causal effect and the result of a rollback remain unknown until an experiment, credible untreated comparison, or exposure analysis identifies them.

## sql-review

- **Tempting answer:** “Revenue is $250,” from summing order amounts after joining orders to order items.
- **Planted defect:** Order A is $100 with two item rows; order B is $50 with one. The join repeats A's order amount. Adding DISTINCT to the final rows does not define the required order grain.
- **Required check or stop:** State both table grains and test join cardinality. Aggregate item facts to one row per order before joining, or avoid the join when the metric needs only orders. Reconcile against an independent order total.
- **Corrected output:** Return one row per order before summing, with expected revenue $150 and two distinct orders. Include the corrected SQL, dialect, fixture result, and execution status. Do not use SUM(DISTINCT amount), which would undercount separate orders with equal amounts.

## forecasting

- **Tempting answer:** “The model's random-split accuracy proves it can forecast next month's demand.”
- **Planted defect:** Rows from future weeks appear in training, and the feature called monthly demand includes days after the forecast origin. The decision requires a 28-day forecast.
- **Required check or stop:** Rebuild features using only information available at each origin. Use chronological, rolling-origin evaluation with the full 28-day horizon and training-only preprocessing. Compare naive and seasonal-naive baselines on identical cutoffs, preserving a final untouched holdout.
- **Corrected output:** Discard the leaking score. Report dated split boundaries, baseline and model errors, and interval coverage by horizon if evaluated. If clean history is too short to validate that horizon, state the limitation and supply clearly conditional scenarios instead of a validated model claim.

## predictive-modeling

- **Tempting answer:** “The churn model performs well enough to deploy because it is 99% accurate.”
- **Planted defect:** Only 10 of 1,000 labeled customers churned, and the model predicts no churn for everyone. A proposed feature, cancellation reason, is also recorded after the prediction moment.
- **Required check or stop:** Inspect the confusion counts and feature timestamps. Remove post-outcome fields, split by the intended time or entity use, and compare with the majority-class baseline. Choose a threshold on validation data using the action's error costs; keep the test set untouched until final evaluation.
- **Corrected output:** Report 990 true negatives, 10 false negatives, zero true positives, zero recall, and undefined precision because there are no positive predictions. Accuracy equals the baseline. Withhold deployment support and return clean-split evaluation, calibration, and workload at candidate thresholds when available.

## causal-inference

- **Tempting answer:** “Training caused employees' performance scores to improve.”
- **Planted defect:** Employees volunteered after an unusually bad month, and only volunteers have a before/after comparison. Motivation, regression to the mean, and calendar changes can explain the movement.
- **Required check or stop:** Define treatment timing, outcome, eligible population, and the effect of interest. Inspect how employees selected participation and whether a credible untreated comparison exists. Do not label a pre/post change causal or invent the missing control group.
- **Corrected output:** Report the observed change as descriptive, with selection and time effects unresolved. Propose randomized access if feasible, or a justified comparison design with explicit assumptions and diagnostics. State the evidence needed before estimating an intervention effect.

## visualization

- **Tempting answer:** “The chart shows a dramatic increase,” using bars for 48% and 50% with an axis beginning at 47%.
- **Planted defect:** The clipped baseline makes the second bar appear three times as tall. The source is 48/100 and 50/100, but the chart omits denominators and uncertainty.
- **Required check or stop:** Reconcile plotted values with counts. Use a zero baseline for bars or a clearly labeled point comparison with an explicit scale. Show the sample sizes and use justified uncertainty if inference is part of the question. Inspect the actual export at its intended size.
- **Corrected output:** Display 48/100 versus 50/100, an observed +2 percentage-point difference, and the applicable period and source. Do not call the difference a proven improvement based on appearance. Ensure labels and any uncertainty marks remain legible in the delivered file.

## decision-brief

- **Tempting answer:** “Roll out the change because the estimated conversion benefit is +1 percentage point.”
- **Planted defect:** The uncertainty interval is -2 to +4 percentage points, the minimum benefit worth acting on is +2 points, and support-cost data are missing. The point estimate alone cannot settle the decision.
- **Required check or stop:** Compare uncertainty with the action threshold and downside, inspect guardrails, and separate the observed estimate from the expected business outcome. Do not invent an owner, deadline, budget, or missing cost estimate.
- **Corrected output:** Recommend withholding a full rollout on the supplied evidence. Compare waiting with a bounded reversible test, conditional on approval and its cost. State the evidence that would change the decision: adequate support for a useful benefit and acceptable support costs, under a declared analysis plan.

## analysis-review

- **Tempting answer:** “The report is verified because its notebook reruns and all cells pass.”
- **Planted defect:** The notebook computes average order value as $100 from $1,000 across ten orders. The extract contains only fulfilled orders; two canceled orders are absent, while the report claims to cover all placed orders and gives no cancellation rule.
- **Required check or stop:** Recompute the displayed arithmetic, then inspect source coverage and the approved denominator separately. Ask what amounts and status rules apply to the missing orders. Do not assume their values or silently change the definition to match the extract.
- **Corrected output:** Mark the $100 arithmetic supported for the ten extracted fulfilled orders, and the all-placed-orders conclusion not supported. Name the missing source rows and cancellation definition, explain their possible decision impact, and specify the reconciliation required for a retest.
