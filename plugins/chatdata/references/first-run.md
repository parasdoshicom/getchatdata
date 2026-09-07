# Your first useful analysis

Start a new agent session after installation. First select the installed skill: `/chatdata:data-science` in Claude Code, ChatData’s **data-science** skill in Codex, or `/chatdata-data-science` in Cursor. Then ask:

> Use ChatData to check setup, then analyze its bundled mix-shift example. Run the calculation, explain what changed, and save a reusable analysis record in analysis/chatdata-first-run/. Use only the synthetic example; do not connect to my data.

In Claude Code, `/chatdata:status` also runs the setup check. Selecting the skill explicitly avoids confusing it with an older ChatData installation. If a skill is missing, confirm the project and restart the chat before changing any settings.

## What should happen

The agent reads the installed skill, locates `scripts/doctor.py` in the native plugin or project skill folder, and runs it with Python 3.9+. The doctor uses bundled synthetic data and makes no network requests or file writes. It checks:

- Mix: conversion falls from 17% to 8%, with the full 9 percentage-point drop explained by customer mix.
- Funnel: 3 visits, 2 signups, 1 purchase after handling ordering, duplicates and the observation window.
- Experiment: a 10% versus 20% result cannot be called a winner because observed assignment counts disagree with the planned allocation.

The agent then uses root-cause for the requested mix analysis, runs the helper, explains that arithmetic contribution does not establish what caused the mix to change, and writes the definition, command, result, checks and caveats into the agreed folder. Label the example synthetic and the record proposed until the user actually reviews it. Never invent a reviewer or review date.

Show the user the output path and the result. Three passing helper checks do not prove live data access, that every skill was loaded, or that future model answers will be correct.

## Pick up the work next time

> Read analysis/chatdata-first-run/ before continuing. Explain the saved definition and result, check whether the inputs or assumptions changed, then tell me what is safe to reuse.

The user chooses what to keep. The plugin does not automatically synchronize records between clients or send them to ChatData. Keep private records out of public repositories.

## Then use your own question

Bring one CSV, one SQL query, or one experiment readout. Tell the agent what decision you need to make. It should inspect what you supplied and ask only for missing information that changes the answer. Read-only access is the default for connected sources; launching experiments, uploads and production changes require specific authorization.

For updates and setup errors, use the [public installation guide](https://github.com/parasdoshicom/getchatdata#install).
