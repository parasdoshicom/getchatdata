---
description: Organize recent local analysis context for one project and prepare a metric for review.
disable-model-invocation: true
argument-hint: "<project directory> [metric name]"
---

Before inventorying a folder, run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/telemetry.py" status`. If Claude Code is not `linked_locally`, stop before reading the requested folder. Tell the user to open `https://getchatdata.com/dashboard`, create and run the email-linked Claude Code command, then retry `/chatdata:onboard`. Do not describe linking as optional.

Use the explicit project directory in $ARGUMENTS or the current request. If none is supplied, ask for one. Never replace it with the home directory, a filesystem root, Claude or Codex user state, another repository, or a search across chat history.

Read `${CLAUDE_PLUGIN_ROOT}/references/local-context.md`, then confirm `${CLAUDE_PLUGIN_ROOT}/scripts/local_context.py` exists. Run setup with Python 3.9+ and the selected directory quoted as one argument:

```sh
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/local_context.py" init --root "<selected project directory>" --days 30
```

Claude substitutes the plugin root in this command content. Do not rely on the current working directory or a shell environment variable. Setup may create only `<selected project directory>/chatdata-context/`. It must preserve every original file. It reads file metadata only, makes no network request, and does not inspect Claude conversation history. If context already exists, do not overwrite it. Run `local_context.py refresh --root "<selected project directory>" --days 30` only when the user wants the inventory updated; it replaces only the inventory JSON and local HTML view while preserving the semantic model, trust records, and README. Then continue by reviewing the existing context.

Describe the inventory as files modified in the last 30 days, never as files the user actually used. Show the number found, skipped-file counts, permission failures, and any truncation reported by `inventory.json`. Incomplete coverage means you cannot claim missing context does not exist.

If the user provided a metric, inspect only the relevant project files needed to draft its Ossie entry and trust record. If no metric was provided, show a short list of likely analysis candidates from the inventory and ask which recurring metric or decision should become reusable. Do not move, rename, rewrite, or delete the originals.

Draft `semantic-model.json` and the exact-name `trust.json` entry from evidence. Map each local source to an exact dataset name in the metric's Ossie model. Fingerprint each selected source and check artifact with the helper, then use `local_context.py semantic-hash --root "<selected project directory>"` for `semantic_sha256`. Keep review status false or absent until the user actually reviews the definition, source mapping, checks, and caveats. Show the user those items and ask them to correct or approve them; never manufacture approval.

After real review, record it and run:

```sh
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/local_context.py" check --root "<selected project directory>" --metric "<exact metric name>"
```

If it returns `blocked`, show every gap and the exact next action. Do not answer that metric as canonical until the check returns `ready_for_analysis`. Exploratory analysis remains allowed when the user asks for it and it is clearly labeled exploratory. Synthetic examples remain allowed when clearly labeled synthetic.

Close by showing the local `chatdata-context/` path, what was created or updated, what the user reviewed, the check result, and what still needs attention. Do not upload the folder, commit it, or send any file to ChatData.
