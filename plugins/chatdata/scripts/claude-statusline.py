#!/usr/bin/env python3
"""Preserve an existing Claude status line and append ChatData estimates."""
import json
import math
import os
import re
import signal
import subprocess
import sys
from pathlib import Path


root = Path(os.environ.get("CHATDATA_HOME", str(Path.home() / ".chatdata")))
raw = sys.stdin.read()
backup_path = root / "claude-statusline-backup.json"
summary_path = root / "individual-telemetry-summary.json"
update_path = root / "update-check.json"
semver = re.compile(r"^(0|[1-9][0-9]{0,8})\.(0|[1-9][0-9]{0,8})\.(0|[1-9][0-9]{0,8})$")


def read_small_object(path):
    try:
        if not path.is_file() or path.stat().st_size > 16 * 1024:
            return {}
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    return value if isinstance(value, dict) else {}


backup = read_small_object(backup_path)

prior = backup.get("value")
if isinstance(prior, dict) and isinstance(prior.get("command"), str):
    process = None
    try:
        popen_options = {"start_new_session": True} if os.name == "posix" else {
            "creationflags": subprocess.CREATE_NEW_PROCESS_GROUP
        }
        process = subprocess.Popen(
            prior["command"], text=True, shell=True, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, **popen_options)
        stdout, _stderr = process.communicate(raw, timeout=2)
        if process.returncode == 0 and stdout.strip():
            print(stdout.rstrip())
    except subprocess.TimeoutExpired:
        try:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGKILL)
            else:
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    capture_output=True, timeout=1, check=False)
        except (OSError, subprocess.SubprocessError):
            if process is not None:
                process.kill()
        if process is not None:
            try:
                process.communicate(timeout=1)
            except (OSError, subprocess.SubprocessError):
                process.kill()
    except (OSError, subprocess.SubprocessError):
        if process is not None:
            process.kill()

summary = read_small_object(summary_path)
update = read_small_object(update_path)

latest = update.get("latest_version")
installed = update.get("installed_version")
latest_match = semver.fullmatch(latest) if isinstance(latest, str) else None
installed_match = semver.fullmatch(installed) if isinstance(installed, str) else None
if (os.environ.get("CHATDATA_UPDATE_CHECK", "1").strip().lower() in {"0", "false", "off", "no"}
        or update.get("schema_version") != 1 or update.get("update_available") is not True
        or not latest_match or not installed_match
        or tuple(map(int, latest_match.groups())) <= tuple(map(int, installed_match.groups()))):
    latest = None
update_notice = f" · update {latest} available · /chatdata:update" if latest else ""

if summary.get("estimates_configured"):
    try:
        hours = float(summary.get("estimated_hours_saved") or 0)
        value = float(summary.get("estimated_value_usd") or 0)
        if not math.isfinite(hours) or not math.isfinite(value) or hours < 0 or value < 0:
            raise ValueError("invalid estimates")
        estimate_text = f"{hours:.1f}h estimated saved · ${value:,.2f} estimated value"
    except (TypeError, ValueError, OverflowError):
        estimate_text = "usage estimates unavailable"
    print(f"ChatData · {estimate_text}{update_notice}")
else:
    print(f"ChatData · set your baseline + hourly value in the dashboard{update_notice}")
