---
name: forecasting
description: Forecast time series with backtesting, simple baselines, uncertainty, and leakage checks.
---

# Beat a baseline before adding complexity

Read [the working agreement](../../references/working-agreement.md) when using this skill. It defines source, privacy, execution, and evidence boundaries.

Define the target, horizon, decision cadence, aggregation, known future inputs, and cost of over- versus under-prediction. Inspect gaps, seasonality, structural breaks, changing exposure, and whether zeros are real. Keep an untouched temporal holdout.

Start with naive and seasonal-naive baselines. Use rolling-origin evaluation with training-only preprocessing; random splits leak time. Match validation horizon to the decision horizon, including gaps for delayed labels. Compare MAE or an appropriate scale-free metric; MAPE is unstable with zero or near-zero actuals.

Fit a more complex model only if it improves a relevant held-out criterion. Exogenous features must be available as of prediction time. Explain whether forecasts condition on a scenario (price, promotion, staffing) or predict those drivers too.

Evaluate interval coverage and width by horizon. Use a method consistent with residual dependence and nonstationarity; do not generate confidence from an arbitrary percentage around the line. Sparse series and regime shifts may justify scenario bounds instead of a precise model forecast.

Deliver baseline versus model backtests, a forecast with dated horizon and uncertainty, known failure modes, and a refresh trigger. Save split dates, data version, code, and environment. Never call in-sample fit a forecast validation.

For helper commands and input formats, see [the runnable tools](../../references/tools.md) when needed. Resolve script paths relative to this skill: `../../scripts/analyze.py`.

Read the [worked failure case](../../references/worked-failures.md#forecasting) when checking a plausible but unsupported answer.
