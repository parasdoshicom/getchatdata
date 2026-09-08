---
description: Show what is installed, what is linked locally, and the next useful setup step.
---

This command belongs to the free ChatData plugin at `${CLAUDE_PLUGIN_ROOT}`. Use only this resolved installation. Confirm that `${CLAUDE_PLUGIN_ROOT}/scripts/status.py` exists. Do not search for another installation or inspect any installation token.

Check Python 3.9+ availability, then run exactly:

```sh
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/status.py" --check
```

Claude substitutes the plugin root in this command content. Do not rely on the current working directory or a shell environment variable. If the root is unresolved or the file is absent, stop and report that exact setup failure. Do not install dependencies, change settings, connect an account, flush events, or make a network request while checking status.

Relay the report in plain language, including its suggested next step. "Linked locally" only means this computer has an installation credential. The offline report does not confirm that the server still accepts it. A cached dashboard timestamp comes from the last successful response and is not a live connection check. The three optional helper checks use bundled synthetic data; they do not prove client skill discovery, connected data, or answer quality.

All 16 skills remain free and work without usage reporting; AI client fees can apply. If the report says the time baseline is missing, explain that the user sets their usual minutes per workflow and that ChatData starts at $125/hour unless they change it. If there are queued events, show the exact flush command from the report but do not run it without a separate request. If no data was supplied, offer the bundled mix-shift example as the first task. Show the installed version instead of inventing the latest release.
