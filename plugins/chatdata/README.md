# ChatData plugin

16 free, open-source data science skills for Claude Code, Codex, and Cursor. See the [repository README](../../README.md) for installation and the [tools guide](references/tools.md) for runnable examples.

The `.claude-plugin` and `.codex-plugin` manifests load the same skill source. Cursor uses the project installer at `../../scripts/install.py`.

The official download starts from a personal ChatData account. Linking usage reporting is a separate consent step. Once linked, ChatData counts explicit ChatData workflows using fixed metadata only. It does not send prompts, files, paths, project names, queries, results, model details, or session IDs. Unlinked installations keep working locally.

Claude's plugin hooks can count direct or agent-selected ChatData skills and the end of that turn. On the first session after installation, ChatData sets up its own footer for estimated hours, value, and update notices. It backs up the prior footer without running or displaying it. Usage reporting still requires explicit consent, and later user footer choices are respected. Codex and Cursor use the same `scripts/telemetry.py` counter through the selected skill; their totals appear in the personal dashboard and the local `status` command.
