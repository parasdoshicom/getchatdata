# Your first useful analysis

Start a new agent session after installation. First select the installed skill: `/chatdata:data-science` in Claude Code, ChatData’s **data-science** skill in Codex, or `/chatdata-data-science` in Cursor. Then ask:

> Use ChatData to check setup, then analyze its bundled mix-shift example. Run the calculation, explain what changed, and save a reusable analysis record in analysis/chatdata-first-run/. Use only the synthetic example; do not connect to my data.

The agent must confirm that the current client is linked to the user's verified ChatData dashboard email before beginning the analysis. If it is not linked, it stops and points to the dashboard install command. Linking is part of the official ChatData workflow, not an optional follow-up.

In Claude Code, `/chatdata:status` also runs the setup check. Selecting the skill explicitly avoids confusing it with an older ChatData installation. If a skill is missing, confirm the project and restart the chat before changing any settings.

## What should happen

The agent reads the installed skill, resolves `scripts/doctor.py` in that installation, and runs `python3 "<resolved absolute path>/scripts/doctor.py"` with Python 3.9+. Invoke Python explicitly; the .py file is not an executable command. The doctor uses bundled synthetic data and makes no network requests or file writes. It checks:

- Mix: conversion falls from 17% to 8%, with the full 9 percentage-point drop explained by customer mix.
- Funnel: 3 visits, 2 signups, 1 purchase after handling ordering, duplicates and the observation window.
- Experiment: a 10% versus 20% result cannot be called a winner because observed assignment counts disagree with the planned allocation.

The agent then uses root-cause for the requested mix analysis, runs the helper, explains that arithmetic contribution does not establish what caused the mix to change, and writes the definition, command, result, checks and caveats into the agreed folder. Label the example synthetic and the record proposed until the user actually reviews it. Never invent a reviewer or review date.

Save only the requested analysis record for this synthetic run; do not create client memory or write outside the agreed project. Show the user the output path and the result. Three passing helper checks do not prove live data access, that every skill was loaded, or that future model answers will be correct.

## Pick up the work next time

> Read analysis/chatdata-first-run/ before continuing. Explain the saved definition and result, check whether the inputs or assumptions changed, then tell me what is safe to reuse.

The user chooses what to keep. The plugin does not automatically synchronize records between clients or send them to ChatData. Keep private records out of public repositories.

## Then use your own question

Bring one CSV, one SQL query, or one experiment readout. Tell the agent what decision you need to make. It should inspect what you supplied and ask only for missing information that changes the answer. Read-only access is the default for connected sources; launching experiments, uploads and production changes require specific authorization.

For a project with existing analysis work, use `/chatdata:onboard <project directory>`. It creates a private `chatdata-context/` folder and inventories supported files modified in that one directory during the last 30 days. The inventory uses filenames and filesystem metadata, not file contents or client conversation history. It does not move originals or make a network request. “Recently modified” is not proof that a file was used. If the folder already exists, refresh only the inventory reports and preserve the semantic model and trust records. Read [the local context guide](local-context.md) before turning any inventory item into reusable metric context.

The first inventory is a map, not a completed semantic layer. The user must review the proposed metric definition, sources, checks, and caveats. Before answering a named metric as canonical, run the local context check for its exact name. A blocked check means stop that canonical answer, explain what is missing, stale, changed, or conflicting, and give the next action. Clearly labeled exploratory work and the bundled synthetic example remain available.

For updates and setup errors, use the [public installation guide](https://github.com/parasdoshicom/getchatdata#install).

## Quick checks without losing your place

In Claude Code, use `/chatdata:savings` for your cached workflow totals, `/chatdata:onboard <project directory>` to build local context, and `/chatdata:resume <analysis folder>` to pick up a saved record. In Codex or Cursor, ask the installed ChatData skill to onboard the explicit project, show local status, or resume the specific folder. The shared helper `python3 "<resolved plugin root>/scripts/status.py"` reports link state, pending events, and the next useful step without reading your conversations or sending a request. `--check` also runs the synthetic checks.

The footer distinguishes an unlinked Claude installation, a linked account needing a time baseline, and cached savings. Pending events and old snapshots are labeled. A credential saved locally is not proof that the server still accepts it; refresh via the dashboard or explicitly sync usage to check.
