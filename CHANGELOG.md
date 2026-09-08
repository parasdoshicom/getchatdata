# Changes

## 1.4.1 — September 7, 2026

- Made dashboard linking part of the standard website setup, with a visible usage notice and a combined install-and-link command.
- Added an explicit setup flag to avoid repeating the dashboard disclosure question in the terminal. Tokens remain private, verified, and revocable.

## 1.4.0 — September 7, 2026

- Made ChatData the Claude Code footer on the first session after installation, with ChatData branding, savings estimates, and release notices.
- Backed up the previous footer for restoration without running or displaying it. Later user footer choices are respected.
- Kept footer setup separate from usage-reporting consent.

## 1.3.0 — September 7, 2026

- Added a Claude Code startup notice for newer published releases, with `/chatdata:update` to update when requested. An existing ChatData status line also shows the cached notice.
- Added bounded public GitHub release checks, cached for a day and quiet when current or unavailable. `CHATDATA_UPDATE_CHECK=0` disables them.
- Kept existing Woz/custom status lines intact and kept update checks separate from usage reporting.
- Documented the public metadata request and local cache in the privacy notice.

## 1.2.1 — September 7, 2026

- Kept consented usage events queued when a client sandbox or temporary network failure blocks delivery, and exposed only the fixed `retry_required` status and a fixed error category to the agent.
- Added an exact ordinary-terminal flush instruction for queued events without asking for broader client permissions or attempting to bypass the client sandbox.

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
