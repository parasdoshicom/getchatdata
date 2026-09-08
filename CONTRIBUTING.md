# Contributing

Start with an issue describing the analytical failure and why it matters. Use synthetic or openly licensed data. Do not include customer records, tokens, private prompts, or paid course materials.

A change should include the relevant method, an example that would fail without it, and a repeatable check. Run `python3 -m unittest discover -s tests -v` and `python3 scripts/validate.py`. New skills need a narrow trigger and specific guidance that improves a decision. Avoid broad claims of superiority without a reproducible comparative evaluation.

Keep the shared skills usable on Claude Code, Codex, and Cursor. Keep the release MIT licensed and free of license checks and paid-feature dependencies. Usage reporting must stay opt-in and content-free: never collect prompts, files, paths, queries, results, model details, project identity, or session IDs. Human review is required before merging contributed code.
