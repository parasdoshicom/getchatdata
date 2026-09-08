# Privacy

Last updated: September 8, 2026

ChatData is a free, open-source set of data science skills and local analytical helpers. You can inspect the public code for Claude Code, Codex, or a Cursor project. A personal ChatData account is used for the official email-linked installation and content-free usage dashboard.

The short version: ChatData does not receive your datasets, prompts, conversations, code, SQL, results, analysis records, or charts. Linked usage reporting sends a small fixed event for an explicit ChatData workflow. Your AI client, model provider, connected data sources, GitHub, and the website host are separate services with their own data handling.

## What the plugin does on your machine

The public package contains skill instructions, synthetic CSV examples, an installer, local analysis tools, a usage reporter, and a release update checker.

- The project installer copies the 16 skill folders into the project path you provide. It does not change global client settings.
- The setup doctor runs three calculations against bundled synthetic data. It makes no network requests and writes no files.
- The analysis helper reads the input you name, runs the requested calculation, and prints JSON. When it reads a local CSV, it records that file's SHA-256 hash in the output. The hash supports reproducibility; the helper does not upload it.
- At Claude Code startup, ChatData reads the installed version and prints discovery text. It also checks the latest public GitHub release at most once a day. The check sends no account token, prompt, dataset, path, or project information. It stores only a local release-check cache under `~/.chatdata/`. GitHub receives ordinary connection information, including the requesting IP address. Set `CHATDATA_UPDATE_CHECK=0` in Claude Code’s environment to disable checks. This check is independent of usage reporting.
- A separate SessionStart usage hook attempts to flush already-consented metadata waiting in the local queue. It does nothing when reporting is not linked.
- Separate Claude hooks can notice an explicit ChatData skill invocation and the end of that turn. They ignore the prompt and answer. Reporting starts after you review the dashboard disclosure and run its email-linked install command.
- The reporter stores its token, pending events, and the latest account summary under `~/.chatdata/`. The token and queue files use owner-only permissions where the operating system supports them.
- Update notices do not install software. You choose when to invoke `/chatdata:update`, which uses Claude Code’s native marketplace and plugin update commands. ChatData has no background updater. A linked installation retries its content-free queue during ChatData activity and setup checks; it does not scan your files.

You choose whether an agent writes an analysis record and where it writes that file. ChatData suggests a path inside your current project, such as `analysis/<question>/`, because a visible local record is easy to inspect and reuse. The plugin does not copy that record elsewhere or synchronize it between clients.

## Personal account and usage reporting

The official download asks for an email address and sends a sign-in link. By signing up, you subscribe to ChatData setup help, workflow ideas, and product emails. The account stores the email address, sign-in and security records, subscription status, and account preferences. You can unsubscribe from product emails in the dashboard or through an unsubscribe link in an email.

The dashboard creates a different installation for each client you link. Its command contains a single-use setup code tied to your verified email and selected client. The code expires after 20 minutes and is exchanged automatically over HTTPS for a revocable installation credential stored on your machine. The server stores hashes of both values rather than the usable values. Local configuration keeps each credential separate, and each queued event is bound to a one-way fingerprint of the credential that created it.

The standard dashboard setup includes usage linking and displays the reporting notice before command creation. Its email-linked command passes `--accept-usage-disclosure` and runs without a prompt, including inside Claude Code. A direct compatibility setup without that flag still asks for confirmation. Usage reporting starts only after the email-linked command successfully claims the installation. The official ChatData skills stop before analyzing user data when the current client is not linked; setup, status, update, footer recovery, and the bundled offline doctor remain available so the user can repair the installation.

For an explicit ChatData workflow, a linked installation can send only these event fields:

- a random event ID;
- `workflow_started` or `workflow_completed`;
- a random workflow ID used to pair those two events;
- event time;
- client type: Claude Code, Codex, Cursor, or other;
- one selected ChatData skill from the package's fixed 16-skill list;
- installed plugin version; and
- elapsed seconds on completion.

The event does not include the account email. The bearer token lets the service associate the fixed event with the installation and account. Ordinary web infrastructure may also process connection information such as IP address, user agent, requested endpoint, and time to deliver and protect the service.

A **tracked ChatData prompt** means an explicit ChatData skill workflow that recorded a start event. It is not every prompt sent through Claude Code, Codex, or Cursor. A **completed workflow** has a matching completion event from the same installation, client, skill, and plugin version.

The dashboard estimates time saved for each completion as `max(your baseline minutes per workflow - observed elapsed minutes, 0)`. It estimates dollar value by multiplying that time by the hourly value you entered. The dashboard shows no estimate until both settings are configured. These are user-configured estimates, not measured productivity gains, causal evidence, or savings on an AI provider bill. Elapsed time can include idle time.

If the service is unavailable, fixed events wait in an owner-readable local queue and later retry. A silent delivery attempt exposes only the fixed status `retry_required` and a fixed error category; it does not expose request content or raw server errors. The agent should give you the exact `python3 "<resolved telemetry.py path>" flush` command to run in your ordinary terminal, without asking for broader permissions or attempting to bypass a client sandbox. The queue is capped at 500 events. Events that become older than the service's 90-day acceptance window are removed locally because they can no longer be submitted. If you replace a client's token, unsent events from that earlier installation are removed instead of being reported under the new installation. Analysis continues if reporting is unavailable.

`telemetry.py disconnect` removes the local token, pending queue, and active-workflow state. It keeps the last local summary unless you pass `--erase-local-usage`. On the first Claude Code session after installation, ChatData configures its own footer and saves a local backup of the previous setting. It does not execute the previous footer. This local setup does not enable usage reporting. Disconnect restores the earlier setting when ChatData still owns the footer, and later user footer choices are respected. Disconnect does not revoke the server token; revoke that installation in the dashboard. Revoking one token does not affect other installations.

## What usage reporting does not collect

Usage events never contain:

- prompts, conversations, or answers;
- source files, file hashes, paths, schemas, or dataset names;
- project, repository, workspace, customer, or company names;
- code, SQL, other query text, parameters, or query results;
- analysis records, notebooks, tables, charts, screenshots, or exports;
- model names, model details, token counts, provider costs, or command history;
- Claude session IDs; or
- errors, tool output, credentials, secrets, or environment variables.

The local Claude hook uses a one-way hash of the Claude session ID only to avoid counting the same ChatData turn twice. That hash stays in local state and is never placed in an event.

## What “local” does and does not mean

The ChatData skills, installer, doctor, analysis helper, analysis records, and content being analyzed run from files installed on your machine. That does not mean every AI interaction stays on your device.

Claude Code, Codex, Cursor, or another model client may send your prompt, selected files, tool results, and conversation context to its model provider. Connected warehouses, notebook services, observability tools, and other data systems may also process queries or results. Their behavior depends on the products, accounts, settings, and connections you choose.

Before using private, personal, regulated, or customer data:

1. Check the privacy and retention terms for your AI client and model provider.
2. Check which files and folders you allowed the client to read.
3. Review every connected data tool and its permissions.
4. Keep source access read-only unless you need and authorize a write.
5. Save analysis records only in a location appropriate for the data they describe.
6. Keep private records, generated extracts, credentials, and secrets out of public repositories.

If your policy requires on-device inference, use an AI client and model configuration that actually provides it. Installing ChatData by itself does not turn a cloud model into a local model.

## Other network activity

- **Account, dashboard, and usage service.** Signing in, changing preferences, managing tokens, loading the dashboard, and sending linked usage events contact ChatData's website services.
- **Installation and updates.** Cloning, downloading, or updating the public repository contacts GitHub. Claude Code startup can also fetch public release metadata for an update notice, without usage linking or an account credential. GitHub receives the request under its own privacy policy and may record standard connection information.
- **AI use.** Your chosen client and model provider process the content that client sends to them. ChatData does not control that transmission or the provider's retention settings.
- **Connected data tools.** A warehouse, database, notebook, chart service, or other tool you authorize may receive queries and return data under its own terms.
- **Website visits.** Cloudflare serves `getchatdata.com` and may process request, performance, and security information. The website loads a Cloudflare analytics and performance beacon and can send application error events with configured technical context to PostHog. Those website systems do not receive the content analyzed by the local plugin through ChatData usage events.
- **Email.** ChatData receives the email address and message content needed for sign-in, the setup help, workflow ideas, and product emails included with signup, and support messages you send to `support@getchatdata.com`. Do not email datasets, credentials, or other sensitive records.
- **Public contributions.** GitHub issues, discussions, pull requests, and commits are public. Remove private data, secrets, internal URLs, and customer details before posting.

## Your choices

You can inspect every plugin file because the package is public and MIT licensed. The license permits modification and redistribution, so no open-source publisher can technically prevent someone from changing the code. The official ChatData skills require a linked installation before analyzing user data. You can check the current link state, queued event count, and cached aggregate with `telemetry.py status`.

Use the dashboard to update your estimate settings, unsubscribe from product emails, revoke an installation token, or request account data access or deletion. Local analysis records remain on your machine and are not part of a ChatData account export because ChatData never receives them. You may also email `support@getchatdata.com` with an account or privacy request.

The plugin's working agreement tells the agent to treat source text and CSV cells as data rather than instructions. It also prefers authorized read-only access, rejects invented results, and requires specific authorization for uploads or external messages. Those instructions reduce common mistakes. They cannot override your AI client's permissions or guarantee that a model will follow every instruction.

## Changes to this notice

We will publish material changes in this file so you can review them in Git history. The version you installed remains inspectable on your machine until you choose to update it.

Questions about this notice can be sent to `support@getchatdata.com`. Please describe the product behavior or policy question without attaching private data.

## Local context onboarding

The local inventory reads file names, sizes, and modification times in a project folder you choose. It creates a local report and does not upload those paths or metadata. It does not read conversation history. Source fingerprint and evidence checks read only explicitly referenced local files. Your semantic model, inventory, review records, and report stay in your project; ChatData telemetry does not include them. Your AI client may read files you provide under its own data policy.
