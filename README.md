# ChatData

**Good AI answers don’t reset. Free forever.**

Your open-source data science workspace, ready to install. ChatData brings together 16 analysis skills, runnable Python checks, synthetic examples, and reusable record templates for Claude Code, Codex, and Cursor. It helps one person frame a question, run the analysis, challenge the conclusion, and save the evidence locally for the next session.

It is MIT licensed and open source, with no trial, license key, or paid feature tier. The official download starts with a free personal account. After installation, you can link content-free usage reporting to see how many explicit ChatData workflows ran and what they may have saved based on your own baseline and hourly value. Your AI client, model usage, warehouse, and other tools may still cost money.

[Install](#install) · [Try it on synthetic data](#first-run-get-one-useful-answer) · [Explore all 16 capabilities](docs/capabilities.md) · [Privacy](docs/privacy.md) · [Source](https://github.com/parasdoshicom/getchatdata)

## How good answers carry forward

You could assemble this yourself: write Markdown skill files, package them for each client, wire up Claude Code hooks, add calculation scripts, and design a record format for later sessions. ChatData brings those pieces together for one person.

The skills ask your agent to save the question, metric definition, source, code, checked outputs, caveats, and conditions that would invalidate the answer in a local folder you choose. Keep that folder and point the next session at it. The agent can inspect the record, rerun the calculation, and recheck changed inputs before continuing.

The files carry the context. Reuse depends on saving the record and following the workflow; installation alone does not make every chat remember everything. Claude Code hooks handle startup discovery, update notices, and optional usage reporting. Codex and Cursor use their own skill setup. [Inspect the record template](plugins/chatdata/references/analysis-record.md) or [see the installed components](plugins/chatdata).

## What changes when ChatData is installed

A general-purpose AI client can write code, query tables, and draw charts. It can also produce a polished answer from the wrong grain or a shifting denominator. Other common failures include an immature cohort, a multiplied join, a leaky model split, and a causal claim the data does not support.

ChatData gives the client a more demanding way to work:

- Start from the decision and inspect the data already supplied.
- Define the unit, population, denominator, timezone, window, exclusions, and source before calculating a metric.
- Match the method to the data rather than forcing every question into the same template.
- Run checks that can withhold a conclusion: assignment imbalance, incomplete follow-up, join multiplication, leakage, failed reconciliation, or missing causal assumptions.
- Report counts, effect sizes, uncertainty, contrary evidence, and checks that did not run.
- Save the definition, source version, code, output, caveats, and invalidation conditions in a local analysis record.
- Point the next session at that record and recheck what changed before reusing the answer.

The goal is to make one data scientist more capable and harder to fool. We do not claim a measured 10× productivity result or guaranteed model accuracy. The value is inspectable in the methods, runnable checks, and artifacts the agent leaves behind.

## Install

### Claude Code

Run in your terminal:

```sh
claude plugin marketplace add parasdoshicom/getchatdata
claude plugin install chatdata@chatdata-free
```

Restart Claude Code, then run `/chatdata:status` or `/chatdata:data-science`.

Try a focused skill directly:

```text
/chatdata:experiment-analysis Check whether this A/B result is trustworthy.
```

The plugin uses the ChatData name, command namespace, and startup hooks. The discovery hook reports the installed version and how to start. If you link usage reporting, separate hooks count explicit ChatData skill invocations and when that turn finishes. They do not send the prompt or answer.

If another installed ChatData package uses the same `/chatdata:` namespace, enable one version for a session so the client does not select the wrong skill root.

### Codex

Run in your terminal:

```sh
codex plugin marketplace add parasdoshicom/getchatdata --ref main
codex plugin add chatdata@chatdata-free
```

Start a new task, select ChatData’s **data-science** skill, and use the first-run prompt below. Native plugins work in Codex desktop and CLI. For a project-scoped install, use the installer below with `--client codex`; it writes the skills into `.agents/skills/`.

If your Codex version does not offer plugin commands, the project-scoped installer provides the same skill content and local helpers.

### Cursor

From the folder where you want to keep the public source:

```sh
git clone https://github.com/parasdoshicom/getchatdata.git
python3 getchatdata/scripts/install.py --client cursor --project /absolute/path/to/your-project
```

Replace the project path with your existing data project. Start a new Cursor agent chat in that project, select `/chatdata-data-science`, and use the first-run prompt below. The installer puts the skills and helpers in `.cursor/skills/chatdata-*`.

Check the installed local helpers without asking the AI:

```sh
python3 "/absolute/path/to/your-project/.cursor/skills/chatdata-data-science/scripts/doctor.py"
```

It should report three passing synthetic checks. That proves the local helper installation works. Skill discovery and a real agent response are separate checks; the first-run workflow covers those.

### Project-scoped Codex install

Clone the public repository, then run:

```sh
python3 getchatdata/scripts/install.py --client codex --project /absolute/path/to/your-project
```

The installer writes the skills into `.agents/skills/chatdata-*`. It preserves unrelated skills and refuses to overwrite existing ChatData folders unless you pass `--update`.

On update, the installer moves the old ChatData folders, including local edits, into the printed `chatdata-backups/` directory before installing the new copy. Review and reapply any customization you want to keep. If installation fails after the backup begins, the installer restores the prior folders.

## Link your personal usage dashboard

Dashboard linking is part of the standard setup in your [ChatData dashboard](https://getchatdata.com/dashboard). The setup page explains usage reporting, creates one installation token per client, and provides a combined install-and-link command. The token appears once. Enter it through the hidden prompt so it does not become part of your shell history.

From the cloned repository root, link Claude Code to your dashboard:

```sh
python3 plugins/chatdata/scripts/telemetry.py connect --client claude-code --enable-statusline
```

Link Codex or Cursor with the same script:

```sh
python3 plugins/chatdata/scripts/telemetry.py connect --client codex
python3 plugins/chatdata/scripts/telemetry.py connect --client cursor
```

The dashboard setup notice lists usage fields before you create a token. Its generated command includes `--accept-usage-disclosure` to avoid asking the same question again in the terminal; the token is still entered privately and verified. A direct `connect` command without that flag shows the consent prompt. A linked installation reports one start for an explicit ChatData workflow and one completion when that workflow finishes. It sends random event and workflow IDs, event time, client, selected skill, plugin version, and elapsed seconds. It does not send email addresses in events, prompts, files, paths, project or repository names, session IDs, SQL or other queries, results, model details, token counts, or provider costs.

The dashboard calls these **tracked ChatData prompts** and **completed workflows**. Estimated time saved is `max(your baseline minutes − observed elapsed minutes, 0)` for each completed workflow. Estimated value multiplies that time by the hourly value you entered. These are user-configured estimates. They are not measured productivity gains or reductions in an AI provider bill. Elapsed time can include idle time.

Claude Code can show both estimates in its status line:

```text
ChatData · 1.2h estimated saved · $187.50 estimated value
```

On the first Claude Code session after installation, ChatData replaces the configured footer with its own branding. It keeps a local backup of your previous footer, including Woz or a custom command, but does not run or display it. Usage reporting still requires the separate consent prompt above. Local disconnect restores the previous setting if it has not changed in the meantime. If you choose another footer later, ChatData respects that choice. To restore your previous Claude footer without disconnecting usage, run `/chatdata:footer restore` in Claude Code. Use `/chatdata:footer enable` to choose ChatData again, or `/chatdata:footer status` to inspect it. You can also restore from the cloned repository root:

```sh
python3 plugins/chatdata/scripts/footer.py restore
```

To choose ChatData again later, run `python3 plugins/chatdata/scripts/footer.py enable`. Use `footer.py status` to check which setting is active. Run restore before uninstalling ChatData if you want the previous footer back.

Codex and Cursor do not have a ChatData footer; use the personal dashboard or check the cached summary locally:

```sh
python3 plugins/chatdata/scripts/telemetry.py status
```

If the service is temporarily unavailable, metadata waits in a local queue and retries later. Analysis continues. A silent client-side delivery attempt returns the fixed status `retry_required` and a fixed error category; it does not return request content or server error text. The agent should give you the exact `python3 "<resolved telemetry.py path>" flush` command to run in your ordinary terminal. It should not ask for broader client permissions or try to bypass a client sandbox. Each client's queue stays bound to the token that created it. If you replace a client's token, ChatData discards any unsent events for that earlier installation rather than attributing them to the new one. To disconnect this machine, run `python3 plugins/chatdata/scripts/telemetry.py disconnect`. Then revoke that installation token in the dashboard. Revoking one client token does not disconnect your other clients.

## First run: get one useful answer

Start a fresh agent session after installation. Select `/chatdata:data-science` in Claude Code, ChatData’s **data-science** skill in Codex, or `/chatdata-data-science` in Cursor. Paste this prompt:

> Use ChatData to check setup, then analyze its bundled mix-shift example. Run the calculation, explain what changed, and save a reusable analysis record in analysis/chatdata-first-run/. Use only the synthetic example; do not connect to my data.

You should get four concrete results:

1. The setup doctor reports the installed ChatData version.
2. Three synthetic checks pass:
   - conversion falls from 17% to 8%, with the full 9 percentage-point decline explained by customer mix;
   - an ordered funnel contains 3 visits, 2 signups, and 1 purchase after an immature user and duplicate event are handled;
   - an apparent experiment lift from 10% to 20% is withheld because assignment counts conflict with the planned allocation.
3. The agent explains the mix result without calling arithmetic attribution a causal explanation.
4. A proposed local record contains the question, definition, exact command, source hash, result, checks, and caveats.

The package labels these examples as synthetic. Their results make no claim about your business.

In the next session, paste:

> Read analysis/chatdata-first-run/ before continuing. Explain the saved definition and result, check whether the inputs or assumptions changed, then tell me what is safe to reuse.

The [full first-run guide](plugins/chatdata/references/first-run.md) explains the expected output and common failure cases. The record stays in the folder you chose. ChatData does not synchronize it between clients or silently upload it.

Run the doctor directly from a source checkout at any time:

```sh
python3 plugins/chatdata/scripts/doctor.py
```

The doctor uses Python 3.9+ standard-library code, makes no network requests, and writes no files. It does not verify the AI client's skill discovery or a live data connection. The native Claude Code startup hook also uses Node.js.

## Sixteen skills for the analysis work you already do

| Skill | Use it when | What it asks the agent to check |
| --- | --- | --- |
| [data-science](plugins/chatdata/skills/data-science/SKILL.md) | You have a question or dataset and need the right workflow | Decision, available evidence, cost of error, method choice, completed calculation, reusable record |
| [metric-definition](plugins/chatdata/skills/metric-definition/SKILL.md) | A KPI, cohort, denominator, or source of truth is ambiguous | Unit, numerator, denominator, population, exclusions, timezone, window, source, boundary cases |
| [experiment-design](plugins/chatdata/skills/experiment-design/SKILL.md) | You are planning or vetting an A/B test | Smallest useful effect, power, randomization, exposure, guardrails, maturity, stopping rule |
| [experiment-analysis](plugins/chatdata/skills/experiment-analysis/SKILL.md) | Someone wants to call an experiment winner | Assignment balance, exposure, effect size, uncertainty, maturity, attrition, leakage, guardrails |
| [funnel-analysis](plugins/chatdata/skills/funnel-analysis/SKILL.md) | You need ordered conversion and drop-off | Identity, event order, duplicates, mature windows, adjacent and end-to-end conversion |
| [root-cause](plugins/chatdata/skills/root-cause/SKILL.md) | A metric changed and you need to locate the movement | Measurement breaks, comparable periods, mix versus within-segment change, reconciliation, contrary evidence |
| [retention](plugins/chatdata/skills/retention/SKILL.md) | You need cohort retention, churn, repeat purchase, or survival | Cohort age, at-risk denominator, incomplete follow-up, resurrection, censoring, coverage changes |
| [data-quality](plugins/chatdata/skills/data-quality/SKILL.md) | You need to know whether data is usable for one decision | Grain, keys, missingness, ranges, drift, referential integrity, join multiplication, impact of each issue |
| [sql-review](plugins/chatdata/skills/sql-review/SKILL.md) | You are writing or reviewing analytical SQL | Grain, joins, NULLs, deduplication, ratio math, time boundaries, windows, cost, fixture reconciliation |
| [exploratory-analysis](plugins/chatdata/skills/exploratory-analysis/SKILL.md) | A dataset is unfamiliar and you need useful questions | Collection, coverage, distributions, outliers, comparisons tried, confounding, leakage, follow-up tests |
| [forecasting](plugins/chatdata/skills/forecasting/SKILL.md) | You need a dated forecast for a decision | Temporal holdout, naive baselines, rolling backtests, future-feature availability, interval coverage |
| [predictive-modeling](plugins/chatdata/skills/predictive-modeling/SKILL.md) | You need to predict an outcome at a defined moment | Leakage-safe split, baseline, threshold, calibration, subgroup errors, shift, intended use |
| [causal-inference](plugins/chatdata/skills/causal-inference/SKILL.md) | Someone asks whether an intervention caused an outcome | Estimand, causal structure, identification assumptions, diagnostics, placebos, sensitivity |
| [visualization](plugins/chatdata/skills/visualization/SKILL.md) | A checked result needs a chart or dashboard | Decision-focused encoding, denominators, uncertainty, source, value verification, rendered output |
| [decision-brief](plugins/chatdata/skills/decision-brief/SKILL.md) | Analysis needs to become a decision | Recommendation, evidence, contrary case, alternatives, uncertainty, next result that changes the action |
| [analysis-review](plugins/chatdata/skills/analysis-review/SKILL.md) | An analysis needs an independent challenge | Recalculation, grain, joins, assumptions, sensitivity, leakage, unsupported claims, fix and retest |

The [capabilities guide](docs/capabilities.md) goes much deeper. It gives every skill a copyable prompt, required inputs, expected output, checks, runnable helper where available, and method limits.

## Things to try next

Bring one CSV, one query, or one experiment readout. Tell the agent what decision the answer should change. These prompts are intentionally specific enough to produce inspectable work.

### Challenge an experiment result

> Use ChatData’s experiment-analysis skill. Planned allocation was 50/50 and the smallest useful absolute effect was 1 percentage point. Inspect the assignment counts, exposure counts, outcomes, exclusions, horizon, and guardrails in results.csv. Check sample-ratio mismatch, maturity, effect size, uncertainty, and practical significance. Do not call a winner if the design evidence is missing.

### Find a funnel drop-off without counting events out of order

> Use ChatData’s funnel-analysis skill. Build a closed user-level funnel from visit to signup to purchase with a 7-day window in UTC. Check duplicate events, strict ordering, identity gaps, late data, and immature entry cohorts. Show counts, adjacent-step conversion, end-to-end conversion, and the next diagnostic query.

### Explain a metric change before guessing at causes

> Use ChatData’s root-cause skill. Reproduce conversion for the before and after periods from the same definition and source. Rule out partial periods, delayed data, event changes, and duplicate joins. Decompose the change by acquisition channel into mix and within-channel performance. Reconcile it to the headline change and give me the strongest evidence against the leading explanation.

### Review SQL that looks plausible

> Use ChatData’s sql-review skill. State the source and result grain, then review this query for join multiplication, NULL behavior, ratio math, time boundaries, timezone, window frames, and future leakage. Test duplicates, NULLs, boundary timestamps, empty groups, and one-to-many joins. Reconcile one independent total and say whether the query was actually run.

### Try to break an analysis before acting

> Use ChatData’s analysis-review skill. Read the actual inputs, code, output, definition, and saved record. Recompute one decision-critical result. Check grain, denominator, maturity, freshness, joins, missingness, selection, multiplicity, assumptions, leakage, and causal language. Test one plausible boundary case and one sensitivity that could reverse the decision. Fix and retest local defects, then return supported, supported with limitations, or not supported.

There are copyable prompts for all 16 skills in [docs/capabilities.md](docs/capabilities.md).

## Built-in runnable checks

ChatData includes five deterministic calculations. They are small enough to inspect and use only the Python standard library.

| Helper | What it does | What it refuses to hide |
| --- | --- | --- |
| Binary experiment | Rates, absolute and relative lift, uncertainty, assignment-balance check | An apparent winner with sample-ratio mismatch |
| Approximate power | Per-arm sample size for a binary outcome | Baseline, absolute effect, alpha, power, and equal-allocation assumptions |
| Ordered funnel | Closed user-level conversion from timestamped events | Duplicates, out-of-order steps, future events, and immature windows |
| Rate decomposition | Mix and within-segment contributions to a rate change | Non-reconciling totals, duplicate segments, and undefined segment rates |
| CSV profile | Rows, columns, missing values, duplicate rows, and duplicate keys | The difference between structural checks and business validity |

See [the exact commands, inputs, outputs, formulas, and method sources](plugins/chatdata/references/tools.md).

Other skills guide the client in using the Python, SQL, notebook, visualization, and authorized data tools already available in your environment. ChatData does not include a database connector, managed compute service, automatic experiment launcher, or model host.

## Keep useful work for the next session

For a result worth reusing, ask the agent to save a local [analysis record](plugins/chatdata/references/analysis-record.md). A good record includes:

- the question and decision;
- the metric definition and boundary rules;
- source and observation cutoff;
- local input hash or source version;
- exact query, command, parameters, dependencies, and seed;
- result, units, effect size, and uncertainty;
- expected and actual checks, including failures and checks not run;
- evidence against the conclusion;
- limitations and unresolved questions;
- what would change the decision;
- freshness and definition conditions to recheck next time.

A record starts as **proposed**. It becomes **reviewed by user** only when a person actually reviews it. A later session should never reuse the answer blindly; it should recheck the source, cutoff, definition, and assumptions first.

## Privacy

The project installer, setup doctor, analytical helper, and unlinked skills do not send usage events. The doctor makes no network requests or file writes. The helper reads only the path supplied to it and prints its result locally.

Usage reporting starts only after you create an installation token in the dashboard, run `connect`, and accept the local consent prompt. It reports fixed workflow metadata and excludes the content of the work. Events never contain prompts, conversations, files, paths, project or repository names, session IDs, SQL or other queries, results, model details, token counts, or provider costs. Your account email is stored with your personal account, but it is not placed in usage events.

Your AI client may still send prompts, selected files, and tool output to its model provider. Connected warehouses and other tools have their own policies. Installing or updating from this repository contacts GitHub. Visiting the website and using the personal dashboard contacts ChatData's website services. “The helper runs locally” does not mean a cloud AI model keeps everything on-device.

Read [the privacy notice](docs/privacy.md) before using private, personal, regulated, or customer data. Keep credentials, raw private data, and analysis records out of public issues and commits.

## Updates

The native Codex installation tracks this repository's `main` branch. Updating remains an explicit action:

```sh
codex plugin marketplace upgrade chatdata-free
codex plugin add chatdata@chatdata-free
```

Start a new task and rerun the setup prompt to confirm the installed version. ChatData does not run a background updater or promise that your client polls GitHub automatically.

### Claude Code update notices

At session startup, ChatData checks its latest published GitHub release at most once a day. When a newer version is available, it shows:

```text
ChatData 1.4.0 is available (installed: 1.3.0). Run /chatdata:update to update, then run /reload-plugins.
```

The version above is an illustration. The real notice uses the published version. The same notice appears in the ChatData footer beside your estimates. You do not need to link usage reporting to receive the startup notice.

Run `/chatdata:update` when you want to update. The command refreshes the `chatdata-free` marketplace and updates only the ChatData plugin in its existing installation scope. It reports the result and asks you to run `/reload-plugins` or restart Claude Code. It does not install an update automatically or enable a background updater.

The terminal equivalent for a user-scoped installation is:

```sh
claude plugin marketplace update chatdata-free
claude plugin update chatdata@chatdata-free --scope user
```

Restart Claude Code and run `/chatdata:status`. A project or local installation uses its corresponding `--scope` value. Managed installations need their administrator’s update route.

Up-to-date installs stay quiet. A network failure does not interrupt your work; a previously cached update notice may remain. The check fetches only public release metadata, without an account token, prompt, dataset, or project information. GitHub still receives normal connection information. Set `CHATDATA_UPDATE_CHECK=0` in the environment that launches Claude Code to turn these checks off. The analysis helpers remain usable without them.

Existing versions need one manual update to get this feature; future sessions can then show newer-release notices.

For Cursor or a project-scoped Codex install, run these commands from a clean source checkout:

```sh
git pull --ff-only
python3 scripts/install.py --client cursor --project /absolute/path/to/your-project --update
```

Use `--client codex` for `.agents/skills/`. If Git reports local changes or a conflict, inspect them before updating. Do not discard your edits. Start a new chat after the update.

## If setup stops

| What you see | Next step |
| --- | --- |
| `codex`, `claude`, `git`, or `python3` is not found | Install or open the required client or tool. ChatData does not bundle it. |
| Plugin commands are unavailable in Codex | Update the client, or use `scripts/install.py --client codex` for a project-scoped install. |
| Skills do not appear | Start a new session in the project you installed into. Select the ChatData skill explicitly and check that the package is enabled. |
| Existing ChatData folders | Use `--update` to back them up and replace them. Unrelated skills remain in place. |
| The agent asks to run a local command | Review the exact command and grant only the permission it needs. Do not disable the client's safeguards. |
| The doctor fails | Keep the error, check Python 3.9+ and the installed version, refresh the package, then retry. A failed doctor is not a successful setup. |
| Another marketplace source is broken | Try the exact `chatdata@chatdata-free` install command first. Do not remove unrelated plugins to fix ChatData. |
| The AI client requires a login or subscription | Use that client's sign-in. Your free ChatData personal account is separate and provides the download steps and usage dashboard. |

## Evidence and limits

The release has package validation, unit tests for the helper calculations, installer rollback tests, local link checks, synthetic first-run cases, and recorded client verification. The [evaluation guide](docs/evaluation.md) separates deterministic software checks from the harder question of model behavior.

These skills and checks improve the process an agent follows. They do not guarantee that a model will never make a mistake. They do not prove live data access, unattended operation, automatic memory, or superiority over another product. Inspect the evidence, run a relevant check, preserve the limits, and make the result reproducible.

For tested client versions, actual workflow results, and remaining limits, see [client verification](docs/client-verification.md).

## Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md). Bring a reproducible analytical failure, a synthetic fixture, or a better method with a source. Keep the release free of license checks and paid-feature dependencies, and keep usage events within the documented content-free schema. [MIT license](LICENSE).
