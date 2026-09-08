---
description: Show your tracked ChatData workflows and saved time and value estimates.
disable-model-invocation: true
---

Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/status.py"` from this resolved installation. Do not search other installations, expose credentials, or inspect conversation history. Report only the observed cached totals and when they were refreshed. Explain whether the Claude client is linked, whether events are queued, and the one useful next action.

The dollar figure is estimated time value, not reduced AI spend. A missing baseline means savings are not yet estimated. The dashboard defaults to $125/hour unless changed; do not invent a baseline or recalculate past events. Use https://getchatdata.com/dashboard for settings. If the user asks to sync, run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/telemetry.py" flush`, then rerun status. A cached summary does not prove the connection is currently valid.
