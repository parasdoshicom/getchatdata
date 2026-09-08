# Privacy

Last updated: September 7, 2026

ChatData is a free, open-source set of data science skills and local analytical helpers. You can inspect and install the public code in Claude Code, Codex, or a Cursor project. A personal ChatData account is used for the official download and, if you choose to link an installation, a content-free usage dashboard.

The short version: ChatData does not receive your datasets, prompts, conversations, code, SQL, results, analysis records, or charts. Linked usage reporting sends a small fixed event for an explicit ChatData workflow. Your AI client, model provider, connected data sources, GitHub, and the website host are separate services with their own data handling.

## What the plugin does on your machine

The public package contains text instructions, two synthetic CSV examples, a Python installer, a setup doctor, a small standard-library analysis helper, and an optional usage reporter.

- The project installer copies the 16 skill folders into the project path you provide. It does not change global client settings.
- The setup doctor runs three calculations against bundled synthetic data. It makes no network requests and writes no files.
- The analysis helper reads the input you name, runs the requested calculation, and prints JSON. When it reads a local CSV, it records that file's SHA-256 hash in the output. The hash supports reproducibility; the helper does not upload it.
- The Claude discovery script, `session-start.js`, reads the local package version and prints discovery text. It does not inspect your project, read your data, change permissions, or call a network service.
- A separate SessionStart usage hook attempts to flush already-consented metadata waiting in the local queue. It does nothing when reporting is not linked.
- Separate Claude hooks can notice an explicit ChatData skill invocation and the end of that turn. They ignore the prompt and answer. Reporting stays off until you link an installation and accept the local consent prompt.
- The optional reporter stores its token, pending events, and the latest account summary under `~/.chatdata/`. The token and queue files use owner-only permissions where the operating system supports them.
- ChatData has no background updater. A linked installation retries its content-free queue during ChatData activity and setup checks; it does not scan your files.

You choose whether an agent writes an analysis record and where it writes that file. ChatData suggests a path inside your current project, such as `analysis/<question>/`, because a visible local record is easy to inspect and reuse. The plugin does not copy that record elsewhere or synchronize it between clients.

## Personal account and usage reporting

The official download asks for an email address and sends a sign-in link. By signing up, you subscribe to ChatData setup help, workflow ideas, and product emails. The account stores the email address, sign-in and security records, subscription status, and account preferences. You can unsubscribe from product emails in the dashboard or through an unsubscribe link in an email.

The dashboard creates a different installation token for each client you link. The token is shown once. ChatData stores a hash of it on the server rather than the token itself. Enter the token through the reporter's hidden prompt so it does not become part of shell history. Local configuration keeps each token separate, and each queued event is bound to a one-way fingerprint of the token that created it.

Nothing is reported until all three things happen: you create a token in the dashboard, run `telemetry.py connect`, and answer yes to the local consent question. An existing unlinked installation remains local and fully usable.

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

If the service is unavailable, fixed events wait in an owner-readable local queue and later retry. The queue is capped at 500 events. Events that become older than the service's 90-day acceptance window are removed locally because they can no longer be submitted. If you replace a client's token, unsent events from that earlier installation are removed instead of being reported under the new installation. Analysis continues if reporting is unavailable.

`telemetry.py disconnect` removes the local token, pending queue, and active-workflow state. It keeps the last local summary unless you pass `--erase-local-usage`. If ChatData installed a Claude status-line wrapper, disconnect restores the exact earlier setting when that setting has not been changed since installation. Disconnect does not revoke the server token; revoke that installation in the dashboard. Revoking one token does not affect other installations.

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
- **Installation and updates.** Cloning, downloading, or updating the public repository contacts GitHub. GitHub receives the request under its own privacy policy and may record standard connection information.
- **AI use.** Your chosen client and model provider process the content that client sends to them. ChatData does not control that transmission or the provider's retention settings.
- **Connected data tools.** A warehouse, database, notebook, chart service, or other tool you authorize may receive queries and return data under its own terms.
- **Website visits.** Cloudflare serves `getchatdata.com` and may process request, performance, and security information. The website loads a Cloudflare analytics and performance beacon and can send application error events with configured technical context to PostHog. Those website systems do not receive the content analyzed by the local plugin through ChatData usage events.
- **Email.** ChatData receives the email address and message content needed for sign-in, the setup help, workflow ideas, and product emails included with signup, and support messages you send to `support@getchatdata.com`. Do not email datasets, credentials, or other sensitive records.
- **Public contributions.** GitHub issues, discussions, pull requests, and commits are public. Remove private data, secrets, internal URLs, and customer details before posting.

## Your choices

You can inspect every plugin file because the package is public and MIT licensed. You can use the skills and local analytical helpers without linking usage reporting. You can check the current link state, queued event count, and cached aggregate with `telemetry.py status`.

Use the dashboard to update your estimate settings, unsubscribe from product emails, revoke an installation token, or request account data access or deletion. Local analysis records remain on your machine and are not part of a ChatData account export because ChatData never receives them. You may also email `support@getchatdata.com` with an account or privacy request.

The plugin's working agreement tells the agent to treat source text and CSV cells as data rather than instructions. It also prefers authorized read-only access, rejects invented results, and requires specific authorization for uploads or external messages. Those instructions reduce common mistakes. They cannot override your AI client's permissions or guarantee that a model will follow every instruction.

## Changes to this notice

We will publish material changes in this file so you can review them in Git history. The version you installed remains inspectable on your machine until you choose to update it.

Questions about this notice can be sent to `support@getchatdata.com`. Please describe the product behavior or policy question without attaching private data.
