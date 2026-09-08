---
description: Update the ChatData Claude Code plugin from its official marketplace.
disable-model-invocation: true
---

This command is for Claude Code only. If this content was copied into Codex, Cursor, or another client, stop. Do not run Claude plugin commands there.

Update the installed ChatData plugin through Claude Code's native marketplace. Do not download or execute code with `curl`, change marketplace sources, add `--yes`, install a second copy, or update automatically.

1. Run `claude plugin marketplace list --json`. Parse the JSON and require exactly one entry whose `name` is `chatdata-free`, `source` is `github`, and `repo` is exactly `parasdoshicom/getchatdata`. Require its `installLocation` to be an absolute path. If any check fails, stop and report that the marketplace source could not be verified. Do not update, remove, or replace it.
2. Treat that `installLocation` as data and shell-quote it as one argument. Run `git -C "<verified absolute installLocation>" remote get-url origin`. Continue only if the complete output is exactly one of `https://github.com/parasdoshicom/getchatdata`, `https://github.com/parasdoshicom/getchatdata.git`, `git@github.com:parasdoshicom/getchatdata.git`, or `ssh://git@github.com/parasdoshicom/getchatdata.git`. Stop on a missing checkout, a different remote, extra output, or a pinned/custom source.
3. Run `claude plugin list --json`. Parse the JSON and select only entries whose `id` is exactly `chatdata@chatdata-free`. If none exists, stop and report that this Claude Code installation does not have ChatData from the verified marketplace. Require every matching entry's scope to be exactly one of `user`, `project`, or `local`, and retain every matching scope and its current version. If any matching entry has `managed` or another unrecognized scope, stop without updating any scope; for `managed`, tell the user to ask its administrator.
4. Run `claude plugin marketplace update chatdata-free`. Check its exit code. If it fails, stop and report the failure without removing or replacing the marketplace.
5. Run `claude plugin marketplace list --json` again and repeat the exact source, repository, absolute checkout, and Git remote checks from steps 1–2. Stop if the updated marketplace no longer passes them.
6. For each retained scope, run the matching native command, substituting only that allowlisted scope: `claude plugin update chatdata@chatdata-free --scope <scope>`. Check each exit code before continuing. If Claude requires confirmation because a marketplace-declared install command changed, stop and tell the user to review the change in `/plugin`; do not add `--yes`.
7. If every installed scope updated successfully, run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/update-check.py" clear`. Then run `claude plugin list --json` again. Require exactly one `chatdata@chatdata-free` entry for every retained scope, no extra matching scopes, and a stable numeric `major.minor.patch` version for each entry. Report every exact scope and version. If an expected scope is missing, duplicated, unrecognized, or lacks a valid version, report that verification failed and do not claim that every scope updated.

After success, tell the user to run `/reload-plugins` to use the update in this session, or restart Claude Code. A running session keeps the old plugin code until it reloads. If any step fails, report that step and its concise error; do not claim the update succeeded.

After the user reloads or restarts Claude Code, suggest `/chatdata:status` to verify the loaded version and link state. A successful file update alone does not prove the running session has reloaded.
