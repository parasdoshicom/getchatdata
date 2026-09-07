# ChatData

**Better data work, in the AI tools you already use. Free forever.**

ChatData gives Claude Code, Codex, and Cursor 16 data science skills: how to frame a question, choose a method, run an analysis, check what could make it wrong, and leave evidence you can rerun.

For individual data scientists, analysts, and people doing the data work without a specialist beside them. MIT licensed. No ChatData account, trial, license key, hosted service, or paid feature tier. Your AI client, model usage, warehouse, and other tools may still cost money.

[Website](https://getchatdata.com) · [Skills](#what-you-can-do) · [Runnable examples](plugins/chatdata/references/tools.md) · [Quality checks](docs/evaluation.md)

## Install

### Claude Code

Run in your terminal:

```sh
claude plugin marketplace add parasdoshicom/getchatdata
claude plugin install chatdata@chatdata-free
```

Restart Claude Code, then run `/chatdata:status` or `/chatdata:data-science`. Ask, for example: `/chatdata:experiment-analysis Check whether this A/B result is trustworthy.`

The plugin uses the ChatData name, command namespace, and a startup context hook. It does not replace your status line, change permissions, or overwrite other plugins. If you already have the older hosted ChatData plugin, use one version in a session to avoid the shared `/chatdata:` namespace. Disable the old plugin in that project's settings if you choose the free one; no hosted account is needed for this package.

### Codex

Run in your terminal:

```sh
codex plugin marketplace add parasdoshicom/getchatdata
codex plugin add chatdata@chatdata-free
```

Start a new task and ask: “Use ChatData to investigate why conversion changed.” You can select the relevant skill explicitly in Codex. If your Codex version does not offer plugin commands, use the project skills installer below with `--client codex`; it installs into `.agents/skills/`.

### Cursor

From the folder where you want to keep the public source:

```sh
git clone https://github.com/parasdoshicom/getchatdata.git
python3 getchatdata/scripts/install.py --client cursor --project /absolute/path/to/your-project
```

Replace the project path with your existing data project. Start a new Cursor agent chat and ask: “Use ChatData to analyze this funnel.” The installer puts the same skills and helpers in `.cursor/skills/chatdata-*`. Cursor loads these as native skills; this does not claim a listing in Cursor's marketplace.

The installer preserves existing files and refuses to overwrite an installed ChatData skill. For an update, inspect the diff, move the prior `chatdata-*` folders to a backup, and run it again. To uninstall a project skills install, remove only the `chatdata-*` folders it created. For native plugins, use the client's plugin manager.

## Try it without connecting any data

```sh
git clone https://github.com/parasdoshicom/getchatdata.git
cd getchatdata
python3 plugins/chatdata/scripts/analyze.py decompose plugins/chatdata/examples/mix-shift.csv
python3 plugins/chatdata/scripts/analyze.py funnel plugins/chatdata/examples/funnel.csv --steps visit signup purchase --as-of 2026-01-05T00:00:00Z --window-hours 48
python3 -m unittest discover -s tests -v
```

These synthetic examples show two easy mistakes: blaming performance when the mix changed, and counting a purchase that happened before signup. Expected results and experiment examples are in [the tools guide](plugins/chatdata/references/tools.md).

## What you can do

| Skill | Use it to |
| --- | --- |
| [data-science](plugins/chatdata/skills/data-science/SKILL.md) | Choose and carry out a data science workflow for a question, dataset, or decision. |
| [metric-definition](plugins/chatdata/skills/metric-definition/SKILL.md) | Define a KPI, denominator, cohort, or source of truth before calculating a business metric. |
| [experiment-design](plugins/chatdata/skills/experiment-design/SKILL.md) | Design or vet an A/B test, including power, randomization, guardrails, and stopping rules. |
| [experiment-analysis](plugins/chatdata/skills/experiment-analysis/SKILL.md) | Analyze an A/B test or vet a claimed winner using assignment checks, uncertainty, and practical effect. |
| [funnel-analysis](plugins/chatdata/skills/funnel-analysis/SKILL.md) | Measure ordered conversion steps, drop-off, and time to convert from event data. |
| [root-cause](plugins/chatdata/skills/root-cause/SKILL.md) | Investigate why a metric changed and separate measurement, composition, and within-segment effects. |
| [retention](plugins/chatdata/skills/retention/SKILL.md) | Build mature cohort retention, churn, repeat-purchase, or survival analyses. |
| [data-quality](plugins/chatdata/skills/data-quality/SKILL.md) | Assess whether a dataset is fit for a named analysis, including grain, missingness, joins, and freshness. |
| [sql-review](plugins/chatdata/skills/sql-review/SKILL.md) | Review or write analytical SQL with grain, joins, time boundaries, and metric reconciliation. |
| [exploratory-analysis](plugins/chatdata/skills/exploratory-analysis/SKILL.md) | Explore an unfamiliar dataset and identify useful, testable questions without overstating patterns. |
| [forecasting](plugins/chatdata/skills/forecasting/SKILL.md) | Forecast time series with backtesting, simple baselines, uncertainty, and leakage checks. |
| [predictive-modeling](plugins/chatdata/skills/predictive-modeling/SKILL.md) | Build or evaluate a predictive model with leakage-safe splits, baselines, calibration, and error analysis. |
| [causal-inference](plugins/chatdata/skills/causal-inference/SKILL.md) | Assess causal claims or design observational estimates with explicit assumptions and falsification checks. |
| [visualization](plugins/chatdata/skills/visualization/SKILL.md) | Create analytical charts or dashboards that show the decision, denominators, uncertainty, and sources. |
| [decision-brief](plugins/chatdata/skills/decision-brief/SKILL.md) | Turn analysis into a concise decision brief with evidence, tradeoffs, and a measurable next step. |
| [analysis-review](plugins/chatdata/skills/analysis-review/SKILL.md) | Independently scrutinize an analysis for arithmetic, methodology, evidence, and unsupported claims. |

## What this adds to a general-purpose AI client

Your client can already write code, query data, and make charts. ChatData supplies a consistent method for the decisions around that work: which denominator belongs in the question, when an experiment is not ready to call, whether cohort age explains a drop, and what would disprove the leading explanation.

The release includes five runnable checks for binary experiments, sample size, ordered funnels, rate decomposition, and CSV quality. Other skills guide the client in using the Python, SQL, charting libraries, and authorized data tools available in your environment. There is no bundled warehouse connector or automatic experiment-launch service.

For work worth reusing, keep the definition, inputs, exact calculation, checks, and caveats in a local [analysis record](plugins/chatdata/references/analysis-record.md). Recheck them when data or assumptions change. These are instructions and tools, not a guarantee that an AI model will never make a mistake.

We do not claim a measured 10× improvement or superiority over another tool. [The evaluation page](docs/evaluation.md) separates executable checks from model-quality evaluation and publishes the failure cases we expect a reviewer to test.

## Privacy

The bundled installer and analytical helpers make no network requests and have no ChatData telemetry. Plugin installation fetches this public repository. Skills operate through your chosen AI client and the tools you authorize; those providers' data policies and charges still apply. Do not put credentials, customer data, or private analysis records in a public issue or commit.

## For your whole team

The individual plugin stays free. If you want help applying these methods across your team, [contact Paras about ChatData advisory](mailto:support@getchatdata.com?subject=ChatData%20team%20advisory). Advisory is a separate service for metric definitions, workflow design, evaluation, and adoption. You do not need to buy advisory to use any skill.

## Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md). Bring a reproducible analytical failure, a synthetic fixture, or a better method with a source. Keep client-specific packaging separate from shared analytical behavior. [MIT license](LICENSE).
