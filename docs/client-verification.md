# Client verification

Checked September 7, 2026. These are reproducible setup and representative workflow checks, not a guarantee that every model answer is correct. No private customer data was used.

## Package checks

The suite contains 40 tests covering analytical calculations, invalid inputs, setup checks from installed paths, update backups, rollback after a failed update, and preservation of unrelated skills. CI runs on Python 3.9, 3.12 and 3.13. The package validator checks 16 skills, manifests, internal links and licensing.

The setup helper runs three synthetic cases: a rate falling from 17% to 8% entirely because of mix; a mature ordered funnel of 3 → 2 → 1; and an experiment whose assignment imbalance blocks a winner decision.

## Live client checks

A process exiting successfully is insufficient: it may still have used the wrong installation or skipped the requested calculation.

### Claude Code

Claude Code 2.1.261, using Sonnet and the native `--plugin-dir` option, loaded all 16 skills and ran the explicit `/chatdata:data-science` first-run flow against version 1.1.2. The final run had no failed tool calls or permission denials. It invoked the installed doctor with `python3`, used the bundled mix-shift file, reproduced 17% → 8% with −9 percentage points from mix, zero within-segment contribution and zero residual, and saved a proposed analysis record plus raw output only inside the requested disposable project. It did not search another installation or create client-memory files.

This tested the unpacked plugin in a real Claude session. Marketplace download/install was not exercised because the test preserved the existing global Claude configuration. Claude’s strict marketplace and plugin validators reported no errors or warnings. The separate `/chatdata:status` setup flow also passed after its plugin-root repair.

### Codex

Codex CLI 0.153.4 installed ChatData from the public GitHub marketplace. A fresh GPT-5.6 Sol session with high reasoning loaded the native data-science and root-cause skills in version 1.1.1, invoked both helpers with `python3`, passed all three setup checks, reproduced the mix result, and saved one proposed synthetic analysis record. The record included the installed version, exact commands, source hash, checks, caveats and conditions for rerunning it. It did not invent a reviewer.

The native GitHub update commands were exercised successfully. Final version 1.1.2 was installed and enabled; all 32 published plugin files matched the installed cache byte for byte, and its exact installed doctor passed all three checks. The version 1.1.2 change made Python invocation explicit; the preceding model run had already used that invocation correctly. A separate Codex project-skills runtime also passed on version 1.0.0. During the final native run, harmless checks for absent project metadata and Git state returned errors in the disposable directory; the analytical workflow completed.

## Cursor: authentication still required

The official Cursor CLI, version 2026.09.02-c22c1a3, was installed for testing. It reports “Not logged in,” so a live model run could not be completed. The project installer and installed setup helper passed; actual skill discovery, instruction following and record creation in Cursor remain unverified.

Use the [installation and first-run guide](../README.md#install) after signing in to your chosen client. Select the skill explicitly and inspect the output. Do not treat an installed folder or a passing Python check as proof of AI behavior.

## Failures found and repaired

Claude initially searched an older hosted ChatData installation when given only a natural-language setup request. Onboarding now asks the user to select the free skill explicitly, and Claude instructions pin file access to that plugin’s root. A later run tried to execute the setup Python file directly; the instructions now use `python3` explicitly.

For native Codex, a preexisting unrelated marketplace on the test machine pointed to a folder without a supported manifest. Broad marketplace listing failed, while installation, targeted listing and actual use of `chatdata-free` succeeded. No unrelated marketplace or plugin was removed to hide that condition.

## Scope

These checks do not establish live warehouse connectivity, unattended production operation, all-skill model accuracy, automatic cross-client memory, or superiority over another analytics product. Saved analysis records are local, inspectable files; the next session must be pointed at them and must recheck changed inputs and assumptions.
