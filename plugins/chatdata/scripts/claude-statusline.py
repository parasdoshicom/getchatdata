#!/usr/bin/env python3
"""Show ChatData estimates and update notices in Claude Code."""
import json
import math
import os
import re
import sys
from pathlib import Path


root = Path(os.environ.get("CHATDATA_HOME", str(Path.home() / ".chatdata")))
raw = sys.stdin.read()
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
