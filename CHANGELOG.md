# Changes

## 1.6.4 — September 8, 2026

- Refresh the local dashboard summary whenever ChatData syncs, even when no usage events are waiting. Claude Code can now replace a stale “set your time baseline” footer after the account already has an estimate.
- Keep the sync content-free: the refresh reads only the same aggregate workflow totals and estimate settings already shown in the dashboard.

## 1.6.3 — September 8, 2026

- Made the link check name the exact JSON field for Claude Code, Codex, and Cursor, including the bracket syntax required for Claude Code's hyphenated key.
- Removed legacy interactive linking examples from the public README. The supported path is now the single email-linked install command from the dashboard.
- Corrected Claude Code's startup guidance so it stops before analysis when the current installation is not linked.

## 1.6.2 — September 8, 2026

- Made the required-link preflight read the client-specific `local_link` field from the offline status report, so every skill has an exact, machine-readable linked or unlinked decision before analysis starts.

## 1.6.1 — September 8, 2026

- Replaced the dashboard's manual installation-token prompt with one email-linked command. Its single-use setup code expires after 20 minutes and is exchanged automatically for a revocable local credential.
- Made linking work noninteractively inside Claude Code, Codex, and Cursor. Claude Code no longer fails because its shell has no controlling TTY.
- Made a linked installation required for the official ChatData analytical workflow. When the current client is unlinked, the skills stop before reading user data or producing an analysis and point to the email-linked dashboard command.
- Kept usage events content-free: they still exclude prompts, files, paths, project identity, queries, results, model details, token counts, and provider costs.
- Kept the previous manual token flow as a compatibility fallback for older setup routes.

## 1.5.0 — September 7, 2026

- Added a read-only local status report with link state, cached usage, pending events, and a useful next step. Use `status.py --check` to include the synthetic setup checks.
- The Claude footer distinguishes unlinked reporting, a missing time baseline, and cached estimates. It labels pending events and old summaries instead of treating them as live totals.
- Added `/chatdata:help` for quick command discovery and re-established local record review guidance after compaction. Interrupted Claude workflows no longer count as completed.
- Added `/chatdata:savings` for cached usage and `/chatdata:resume <analysis folder>` for continuing a specific local analysis after checking its evidence and freshness.
- Updated first-run guidance for standard dashboard linking and the editable $125/hour default. All 16 data-science skills remain free.
- No conversation-history scanning, new telemetry fields, remote analysis storage, or background uploads were added.

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
