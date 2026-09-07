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

## Fresh-session reuse checks on version 1.1.2

Later on September 7, independent checks exercised first-run and fresh-session reuse against the unchanged 1.1.2 package.

Claude Code 2.1.261 with Sonnet loaded all 16 skills through `--plugin-dir`. It ran the doctor and decomposition, saved a proposed local record and raw output, then a separate session read that record, rechecked the source hash and version, and reproduced byte-identical decomposition output. It reported the synthetic and causal limits correctly. Both sessions had no failed tool calls or permission denials. This still does not test marketplace download/install.

Codex CLI 0.153.4 confirmed 1.1.2 installed and enabled from the public GitHub marketplace. A fresh GPT-5.6 Sol session loaded the exact native skills, passed the three setup checks, reproduced 17% to 8%, and saved a proposed record with proof files. A separate read-only session matched the source, helper and version hashes, matched fresh output, and independently recomputed the result with exact fractions. The saved record remained byte-identical. It limited reuse to the synthetic example and method, rather than treating the result as evidence about another dataset.

The Codex analytical flow completed, but the first session was not entirely error-free. The model attempted a Git check in a disposable non-Git folder, repaired one failed patch-context match, and made a malformed search call. None changed the calculation or final record. Unrelated configured integrations also produced startup or shutdown warnings. These checks do not establish an error-free client environment.

The installed Python doctor passed all three checks with operating-system network access denied. Source inspection found no network client code in the local Python helpers. This verifies the local helper behavior; the AI sessions themselves used cloud models and only synthetic input.

## Cursor: authentication still required

The official Cursor CLI, version 2026.09.02-c22c1a3, was installed for testing. It reports “Not logged in,” so a live model run could not be completed. The project installer and installed setup helper passed; actual skill discovery, instruction following and record creation in Cursor remain unverified.

Use the [installation and first-run guide](../README.md#install) after signing in to your chosen client. Select the skill explicitly and inspect the output. Do not treat an installed folder or a passing Python check as proof of AI behavior.

## Failures found and repaired

Claude initially searched an older hosted ChatData installation when given only a natural-language setup request. Onboarding now asks the user to select the free skill explicitly, and Claude instructions pin file access to that plugin’s root. A later run tried to execute the setup Python file directly; the instructions now use `python3` explicitly.

For native Codex, a preexisting unrelated marketplace on the test machine pointed to a folder without a supported manifest. Broad marketplace listing failed, while installation, targeted listing and actual use of `chatdata-free` succeeded. No unrelated marketplace or plugin was removed to hide that condition.

## Scope

These checks do not establish live warehouse connectivity, unattended production operation, all-skill model accuracy, automatic cross-client memory, or superiority over another analytics product. Saved analysis records are local, inspectable files; the next session must be pointed at them and must recheck changed inputs and assumptions.
