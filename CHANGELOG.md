# Changes

## 1.1.0 — September 7, 2026

- Added a first-run workflow that checks three bundled examples, carries out an analysis, and saves a reusable record.
- Added an offline doctor with explicit expected results and clear limits on what it verifies.
- Pinned Claude’s status command to its own installed plugin root so an older hosted ChatData installation cannot be mistaken for this package.
- Added backed-up project skill updates and rollback on a failed replacement; unrelated skills and local backups are preserved.
- Unified hook, manifest, doctor and calculation provenance versions.
- Documented GitHub-backed Codex installation and explicit updates, client-specific first prompts, reuse, and troubleshooting.

## 1.0.0 — September 7, 2026

Initial MIT-licensed release: 16 data science skills, five offline analytical helpers, Claude Code/Codex packaging, and a Cursor/project skills installer.
