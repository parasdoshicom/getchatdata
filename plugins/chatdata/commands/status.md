---
description: Verify ChatData setup, local helper checks, and personal usage-reporting status.
---

This command belongs to the free ChatData plugin at `${CLAUDE_PLUGIN_ROOT}`. Use only this resolved installation. Read `${CLAUDE_PLUGIN_ROOT}/scripts/package-info.json` and list `${CLAUDE_PLUGIN_ROOT}/skills/`.

Check Python 3.9+ availability, then run exactly:

```sh
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py"
```

Then inspect the local usage-reporting state:

```sh
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/telemetry.py" status
```

Claude substitutes the plugin root in this command content. Do not rely on the current working directory or a shell environment variable. If the root is unresolved or the file is absent, stop and report that exact setup failure. Never search the home directory or another ChatData installation, fall back to hosted MCP instructions, invent a fixture, or replace the doctor with an ad hoc calculation. Do not install dependencies or change client settings.

Report the observed version, the three check results, whether this installation is linked, the locally queued event count, and whether the cached account summary has configured estimates. Do not print or search for an installation token. A passing helper check proves local calculations only; confirm the selected ChatData skill is available in this session separately. Do not claim connected data works or that all model answers are correct. If a step fails, state the exact failure and a targeted repair.

Explain that all 16 skills remain free and work without hosted MCP or linked reporting; AI client fees can apply. The official download uses a personal account, and linking this installation to the usage dashboard is a separate consent step. If no data was supplied, offer the mix-shift example as the first task. When the user asks to run the example, read `${CLAUDE_PLUGIN_ROOT}/skills/root-cause/SKILL.md` and `${CLAUDE_PLUGIN_ROOT}/examples/mix-shift.csv`. Run `${CLAUDE_PLUGIN_ROOT}/scripts/analyze.py` on that exact CSV, explain why the rate changed, and save an analysis record in their chosen folder. If an earlier setup step failed, do not manufacture a successful example or record. On the next session, point the agent at that record and recheck freshness before reuse. Show the installed version instead of inventing the latest release.
