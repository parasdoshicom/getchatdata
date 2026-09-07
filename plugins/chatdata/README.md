# ChatData plugin

16 free, open-source data science skills for Claude Code, Codex, and Cursor. See the [repository README](../../README.md) for installation and the [tools guide](references/tools.md) for runnable examples.

The `.claude-plugin` and `.codex-plugin` manifests load the same skill source. Cursor uses the project installer at `../../scripts/install.py`. The Claude startup hook supplies branding and discovery context only; it does not access data or modify settings.
