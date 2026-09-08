---
name: predictive-modeling
description: Build or evaluate a predictive model with leakage-safe splits, baselines, calibration, and error analysis.
---

# Match validation to the real prediction

Read [the working agreement](../../references/working-agreement.md) when using this skill. It defines source, privacy, execution, and evidence boundaries.

Define the prediction moment, label, label delay, unit, action, and error costs. List which features exist at that moment. Use time or group splits when production repeats entities or predicts the future; fit preprocessing only on training data.

Establish a simple baseline. For classification inspect prevalence, precision/recall at actionable thresholds, confusion counts, calibration, and subgroup performance. Accuracy alone can hide useless rare-event predictions. For regression inspect residuals, asymmetric losses, and error by scale and segment.

Keep test data out of feature selection, hyperparameter tuning, and threshold selection. Use cross-validation within the training portion when appropriate. Evaluate against leakage traps: post-outcome fields, future aggregates, duplicated entities, and target-encoded categories fit before splitting.

Choose complexity only when held-out improvement justifies cost. Inspect stability, missing-feature behavior, distribution shift, and intended-use limits. Feature importance and SHAP explanations describe a model, not the causal effect of changing a feature.

Deliver a model card with data and split provenance, baseline comparison, threshold rationale, error analysis, training/inference commands, and monitoring signals. Local training can proceed inside agreed resource limits. Deployment, automated decisions about people, or production writes need explicit authorization and appropriate domain review.

For helper commands and input formats, see [the runnable tools](../../references/tools.md) when needed. Resolve script paths relative to this skill: `../../scripts/analyze.py`.

Read the [worked failure case](../../references/worked-failures.md#predictive-modeling) when checking a plausible but unsupported answer.
