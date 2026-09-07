# ChatData

**Good answers don’t reset. Free forever.**

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
codex plugin marketplace add parasdoshicom/getchatdata --ref main
codex plugin add chatdata@chatdata-free
```

Start a new task, select ChatData’s **data-science** skill, and use the first-run prompt below. Native plugins work in Codex desktop and CLI; the IDE extension should use the project skills installer. If your Codex version does not offer plugin commands, use the project skills installer below with `--client codex`; it installs into `.agents/skills/`.

### Cursor

From the folder where you want to keep the public source:

```sh
git clone https://github.com/parasdoshicom/getchatdata.git
python3 getchatdata/scripts/install.py --client cursor --project /absolute/path/to/your-project
```

Replace the project path with your existing data project. Start a new Cursor agent chat in that project, select `/chatdata-data-science`, and use the first-run prompt below. The installer puts the same skills and helpers in `.cursor/skills/chatdata-*`. Cursor loads these as native skills; this does not claim a listing in Cursor's marketplace.

To check the installed helpers without asking the AI, run:

```sh
python3 "/absolute/path/to/your-project/.cursor/skills/chatdata-data-science/scripts/doctor.py"
```

This should report three passing synthetic checks. Skill discovery and a real agent response are separate checks; follow the first-run guide to verify those.

The installer preserves existing files and refuses to overwrite an installed ChatData skill unless you request `--update`. Updates move the old ChatData folders, including local edits, into the printed `chatdata-backups/` directory before installing the new copy. Review and reapply any customizations you want to keep. Unrelated skills are preserved. If an update fails, the installer restores the prior folders. To uninstall, remove only the `chatdata-*` folders it created; keep backups until you no longer need them. For native plugins, use the client's plugin manager.

## First run: get one useful answer

After installation, start a fresh agent session. Select `/chatdata:data-science` in Claude Code, ChatData’s **data-science** skill in Codex, or `/chatdata-data-science` in Cursor. Then paste:

> Use ChatData to check setup, then analyze its bundled mix-shift example. Run the calculation, explain what changed, and save a reusable analysis record in analysis/chatdata-first-run/. Use only the synthetic example; do not connect to my data.

You should see the installed version and three local checks: a 17% → 8% rate change explained by mix, an ordered 3 → 2 → 1 funnel, and an experiment winner withheld because assignment is imbalanced. The agent should then explain the mix result and give you a saved record with the command, evidence and caveats. These are synthetic examples, not your business results.

In the next session, ask:

> Read analysis/chatdata-first-run/ before continuing. Check whether the inputs or assumptions changed, then tell me what is safe to reuse.

The [first-run guide](plugins/chatdata/references/first-run.md) explains the expected behavior. Records stay where you choose to save them; this is not automatic cross-client memory.

To check the helpers directly from a source checkout:

```sh
python3 plugins/chatdata/scripts/doctor.py
```

The doctor makes no network requests or file writes. It does not verify AI client discovery or a warehouse connection. Python 3.9+ is required. Native Claude's startup hook also uses Node.js.

## Updates

The Codex installation above tracks this GitHub repository's `main` branch, rather than a development folder on your machine. To fetch the current release and reinstall it:

```sh
codex plugin marketplace upgrade chatdata-free
codex plugin add chatdata@chatdata-free
```

Start a new task and rerun the setup prompt to confirm the installed version. This is an explicit update workflow; ChatData does not add a background updater or promise that your client automatically polls GitHub.

For Claude Code:

```sh
claude plugin marketplace update chatdata-free
claude plugin update chatdata@chatdata-free
```

Restart Claude Code and run `/chatdata:status`.

For Cursor or a Codex project skills install, run these from your clean source checkout:

```sh
git pull --ff-only
python3 scripts/install.py --client cursor --project /absolute/path/to/your-project --update
```

Use `--client codex` for `.agents/skills/`. If Git reports local changes or a conflict, inspect them before updating; do not discard your edits. Start a new chat after the update.

## If setup stops

| What you see | Next step |
| --- | --- |
| `codex`, `claude`, `git`, or `python3` is not found | Install or open the required client/tool first. ChatData does not bundle the AI client. |
| Plugin commands are unavailable in Codex | Update the client, or use `scripts/install.py --client codex` for your project. |
| Skills do not appear | Start a new session in the project you installed into, then select the ChatData skill explicitly. Check that the plugin is enabled in your client's plugin manager. |
| Existing ChatData folders | Use `--update` to back them up and replace them. The installer leaves unrelated skills alone. |
| The agent asks to run a local command | Review the exact command and grant only the permission needed for that command. Do not disable your client's safeguards. |
| The doctor fails | Keep the error, check Python 3.9+ and the installed version, refresh the package, then retry. Do not treat a failed check as a successful setup. |
| Another marketplace is broken | A broad marketplace listing may fail for an unrelated source. Try the exact `chatdata@chatdata-free` install command first; do not remove other plugins to fix ChatData. |
| The AI client requires a login or subscription | Use that client's sign-in. There is no separate ChatData account. |

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

The individual plugin stays free. If you want help applying these methods across your team, [contact Paras about ChatData advisory](mailto:support@getchatdata.com?subject=ChatData%20team%20advisory). Advisory is a separate service for shared AI infrastructure: definitions, reusable context, workflow design, and evaluating whether agents use that context correctly. You do not need to buy advisory to use any skill.

## Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md). Bring a reproducible analytical failure, a synthetic fixture, or a better method with a source. Keep client-specific packaging separate from shared analytical behavior. [MIT license](LICENSE).

For the tested client versions, actual workflow results and remaining limits, see [client verification](docs/client-verification.md).
