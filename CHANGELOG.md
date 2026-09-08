# Changes

## 1.2.0 — September 7, 2026

- Added personal account linking with a token entered through a hidden prompt instead of a command-line argument.
- Added opt-in usage reporting for explicit ChatData workflows. Events contain random IDs, event time, client, selected skill, plugin version, and elapsed seconds. They do not contain prompts, files, paths, project identity, queries, results, model details, or session IDs.
- Added an offline queue, idempotent delivery, a local status command, and a disconnect command. Existing unlinked installations keep working without telemetry.
- Added a Claude Code status line that shows estimated hours and dollar value from the user's own baseline and hourly value. It wraps and restores an existing status line instead of silently replacing it.
- Added Claude hooks for direct and agent-selected ChatData skill invocations. Codex and Cursor use the same counter through their installed skill instructions.

## 1.1.0 — September 7, 2026

- Added a first-run workflow that checks three bundled examples, carries out an analysis, and saves a reusable record.
- Added an offline doctor with explicit expected results and clear limits on what it verifies.
- Pinned Claude’s status command to its own installed plugin root so an older hosted ChatData installation cannot be mistaken for this package.
- Added backed-up project skill updates and rollback on a failed replacement; unrelated skills and local backups are preserved.
- Unified hook, manifest, doctor and calculation provenance versions.
- Documented GitHub-backed Codex installation and explicit updates, client-specific first prompts, reuse, and troubleshooting.

## 1.0.0 — September 7, 2026

Initial MIT-licensed release: 16 data science skills, five offline analytical helpers, Claude Code/Codex packaging, and a Cursor/project skills installer.
