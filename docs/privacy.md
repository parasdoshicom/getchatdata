# Privacy

Last updated: September 7, 2026

ChatData is a free, open-source set of data science skills and local analytical helpers. You install the code into Claude Code, Codex, or a Cursor project. There is no ChatData account, license key, usage meter, or ChatData data service behind the plugin.

The short version: the ChatData installer and bundled Python helpers do not send your datasets, prompts, analysis records, or helper results to ChatData. Your AI client, model provider, connected data sources, GitHub, and the website host are separate services with their own data handling.

## What the plugin does on your machine

The public package contains text instructions, two synthetic CSV examples, a Python installer, a setup doctor, and a small standard-library analysis helper.

- The project installer copies the 16 skill folders into the project path you provide. It does not change global client settings.
- The setup doctor runs three calculations against bundled synthetic data. It makes no network requests and writes no files.
- The analysis helper reads the input you name, runs the requested calculation, and prints JSON. When it reads a local CSV, it records that file's SHA-256 hash in the output. The hash supports reproducibility; it is not uploaded by the helper.
- The Claude Code startup hook reads the local package version and prints discovery text. It does not inspect your project, read your data, change permissions, or call a network service.
- ChatData does not include telemetry, analytics beacons, crash reporting, background synchronization, or an automatic updater.

You choose whether an agent writes an analysis record and where it writes that file. ChatData suggests a path inside your current project, such as `analysis/<question>/`, because a visible local record is easy to inspect and reuse. The plugin does not copy that record elsewhere or synchronize it between clients.

## What “local” does and does not mean

The ChatData code above runs from files installed on your machine. That does not mean every AI interaction stays on your device.

Claude Code, Codex, Cursor, or another model client may send your prompt, selected files, tool results, and conversation context to its model provider. Connected warehouses, notebook services, observability tools, and other data systems may also process queries or results. Their behavior depends on the products, accounts, settings, and connections you choose.

Before using private, personal, regulated, or customer data:

1. Check the privacy and retention terms for your AI client and model provider.
2. Check which files and folders you allowed the client to read.
3. Review every connected data tool and its permissions.
4. Keep source access read-only unless you need and authorize a write.
5. Save analysis records only in a location appropriate for the data they describe.
6. Keep private records, generated extracts, credentials, and secrets out of public repositories.

If your policy requires on-device inference, use an AI client and model configuration that actually provides it. Installing ChatData by itself does not turn a cloud model into a local model.

## Network activity outside the plugin

Some ordinary actions around the plugin use third-party services:

- **Installation and updates.** Cloning, downloading, or updating the public repository contacts GitHub. GitHub receives the request under its own privacy policy and may record standard connection information such as IP address, user agent, requested resource, and time.
- **AI use.** Your chosen client and model provider process the content that client sends to them. ChatData does not control that transmission or the provider's retention settings.
- **Connected data tools.** A warehouse, database, notebook, chart service, or other tool you authorize may receive queries and return data under its own terms.
- **Website visits.** Cloudflare serves `getchatdata.com`. It may process ordinary request, performance, and security information needed to deliver and protect the site. The website can also send application error events and the technical context configured for those events to PostHog. The plugin does not receive those website logs or error events.
- **Support.** If you email `support@getchatdata.com`, ChatData receives the address, message, and attachments you choose to send so the message can be read and answered. Do not email datasets, credentials, or other sensitive records.
- **Public contributions.** GitHub issues, discussions, pull requests, and commits are public. Remove private data, secrets, internal URLs, and customer details before posting.

## What ChatData does not collect through the plugin

The plugin has no ChatData-operated endpoint to receive:

- your prompts or conversations;
- your source files, schemas, query text, or query results;
- your analysis records or charts;
- the names of your projects or clients;
- model usage, skill usage, errors, or command history;
- account, payment, or license information.

This statement applies to the ChatData code in this repository. Other software may collect information under its own terms. That includes the AI client, model provider, operating system, source system, GitHub, Cloudflare, and PostHog on the website.

## Practical privacy choices

You can inspect every file before installation because the package is public and MIT licensed. You can run `python3 plugins/chatdata/scripts/doctor.py` from a source checkout to verify the synthetic helper checks without involving an AI client. You can also run the analysis helper directly and review its JSON output before sharing that output with a model.

For sensitive work, give the agent the smallest useful input. Aggregated counts may be enough for an experiment readout or rate decomposition. A schema and query may be enough for SQL review. When row-level data is necessary, use the least sensitive fields and an environment approved for that data.

The plugin's working agreement tells the agent to treat source text and CSV cells as data rather than instructions. It also prefers authorized read-only access, rejects invented results, and requires specific authorization for uploads or external messages. Those instructions reduce common mistakes. They cannot override your AI client's permissions or guarantee that a model will follow every instruction.

## Changes to this notice

We will make material changes in this public file so you can review them in Git history. The version you installed remains inspectable on your machine until you choose to update it.

Questions about this notice can be sent to `support@getchatdata.com`. Please describe the product behavior or policy question without attaching private data.
