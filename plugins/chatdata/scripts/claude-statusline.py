#!/usr/bin/env python3
"""Preserve an existing Claude status line and append ChatData estimates."""
import json
import os
import subprocess
import sys
from pathlib import Path


root = Path(os.environ.get("CHATDATA_HOME", str(Path.home() / ".chatdata")))
raw = sys.stdin.read()
backup_path = root / "claude-statusline-backup.json"
summary_path = root / "individual-telemetry-summary.json"

try:
    backup = json.loads(backup_path.read_text(encoding="utf-8"))
except (OSError, ValueError, TypeError):
    backup = {}

prior = backup.get("value")
if isinstance(prior, dict) and isinstance(prior.get("command"), str):
    try:
        completed = subprocess.run(prior["command"], input=raw, text=True, shell=True,
                                   capture_output=True, timeout=2)
        if completed.returncode == 0 and completed.stdout.strip():
            print(completed.stdout.rstrip())
    except (OSError, subprocess.SubprocessError):
        pass

try:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
except (OSError, ValueError, TypeError):
    summary = {}

if summary.get("estimates_configured"):
    hours = float(summary.get("estimated_hours_saved") or 0)
    value = float(summary.get("estimated_value_usd") or 0)
    print(f"ChatData · {hours:.1f}h estimated saved · ${value:,.2f} estimated value")
else:
    print("ChatData · set your baseline + hourly value in the dashboard")
