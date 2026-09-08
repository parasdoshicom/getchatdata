# ChatData plugin

16 free, open-source data science skills for Claude Code, Codex, and Cursor. Seven analytical checks run with the Python standard library; an optional local DuckDB adapter supports bounded read-only queries against an existing database file. See the [repository README](../../README.md) for installation and the [tools guide](references/tools.md) for runnable examples.

The `.claude-plugin` and `.codex-plugin` manifests load the same skill source. Cursor uses the project installer at `../../scripts/install.py`.

The official download starts from a personal ChatData account. The dashboard shows the usage disclosure and creates one noninteractive install command linked to the verified email. Once linked, ChatData counts explicit ChatData workflows using fixed metadata only. It does not send prompts, files, paths, project names, queries, results, model details, or session IDs. The source is public and inspectable; the official ChatData skills require a linked installation before they analyze user data.

Claude's plugin hooks can count direct or agent-selected ChatData skills and the end of that turn. On the first session after installation, ChatData sets up its own footer for estimated hours, value, and update notices. It backs up the prior footer without running or displaying it. The linked install follows the dashboard disclosure, and later user footer choices are respected. Codex and Cursor use the same `scripts/telemetry.py` counter through the selected skill; their totals appear in the personal dashboard and the local `status` command.
