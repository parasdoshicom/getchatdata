#!/usr/bin/env python3
"""Show local ChatData usage state, estimates, and update notices in Claude Code."""
import hashlib
import json
import math
import os
import re
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path


MAX_INPUT_BYTES = 16 * 1024
MAX_OBJECT_BYTES = 16 * 1024
MAX_QUEUE_BYTES = 512 * 1024
MAX_QUEUE_EVENTS = 500
CONSENT_VERSION = "individual-usage-v1"
CLIENT = "claude-code"
CLIENTS = {"claude-code", "codex", "cursor", "other"}
SKILLS = {
    "analysis-review", "causal-inference", "data-quality", "data-science",
    "decision-brief", "experiment-analysis", "experiment-design",
    "exploratory-analysis", "forecasting", "funnel-analysis",
    "metric-definition", "predictive-modeling", "retention", "root-cause",
    "sql-review", "visualization",
}

root = Path(os.environ.get("CHATDATA_HOME", str(Path.home() / ".chatdata")))
summary_path = root / "individual-telemetry-summary.json"
config_path = root / "individual-telemetry.json"
queue_path = root / "individual-telemetry-queue.jsonl"
update_path = root / "update-check.json"
semver = re.compile(r"^(0|[1-9][0-9]{0,8})\.(0|[1-9][0-9]{0,8})\.(0|[1-9][0-9]{0,8})$")
token = re.compile(r"^cdi_[A-Za-z0-9_-]{43}$")
sha256 = re.compile(r"^[a-f0-9]{64}$")
uuid = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-"
    r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)


def read_bounded(path, limit):
    """Read a regular local file without following symlinks or exceeding limit."""
    if path.is_symlink():
        return None
    flags = (os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
             | getattr(os, "O_NONBLOCK", 0))
    try:
        descriptor = os.open(path, flags)
    except OSError:
        return None
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            return None
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            raw_value = stream.read(limit + 1)
    except OSError:
        return None
    finally:
        os.close(descriptor)
    return raw_value if len(raw_value) <= limit else None


def read_small_object(path):
    raw_value = read_bounded(path, MAX_OBJECT_BYTES)
    if raw_value is None:
        return {}
    try:
        value = json.loads(raw_value.decode("utf-8"))
    except (UnicodeError, ValueError, TypeError):
        return {}
    return value if isinstance(value, dict) else {}


def valid_number(value):
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value) and value >= 0)


def valid_count(value):
    return not isinstance(value, bool) and isinstance(value, int) and value >= 0


def summary_age_text(summary):
    if not summary:
        return None
    updated_at = summary.get("updated_at")
    if not isinstance(updated_at, str) or len(updated_at) > 64:
        return "cache age unknown"
    try:
        parsed = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
    except ValueError:
        return "cache age unknown"
    if parsed.tzinfo is None:
        return "cache age unknown"
    age_seconds = (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds()
    if age_seconds < 0:
        return "cache age unknown"
    return "cached >24h" if age_seconds > 24 * 60 * 60 else None


def claude_token(config):
    if config.get("consent_version") != CONSENT_VERSION:
        return None
    installations = config.get("installations")
    if not isinstance(installations, dict):
        return None
    installation = installations.get(CLIENT)
    if (not isinstance(installation, dict)
            or not isinstance(installation.get("token"), str)
            or token.fullmatch(installation["token"]) is None):
        return None
    return installation["token"]


def valid_queue_event(event):
    if not isinstance(event, dict):
        return False
    event_type = event.get("event_type")
    expected = {
        "event_id", "event_type", "workflow_id", "occurred_at", "client",
        "skill_id", "plugin_version",
    }
    if event_type == "workflow_completed":
        expected.add("elapsed_seconds")
    elif event_type != "workflow_started":
        return False
    if (set(event) != expected or event.get("client") not in CLIENTS
            or event.get("skill_id") not in SKILLS):
        return False
    if not all(isinstance(event.get(key), str) for key in (
            "event_id", "workflow_id", "occurred_at", "skill_id", "plugin_version")):
        return False
    if not uuid.fullmatch(event["event_id"]) or not uuid.fullmatch(event["workflow_id"]):
        return False
    if len(event["occurred_at"]) > 64 or len(event["skill_id"]) > 100:
        return False
    try:
        occurred_at = datetime.fromisoformat(event["occurred_at"].replace("Z", "+00:00"))
    except ValueError:
        return False
    if occurred_at.tzinfo is None:
        return False
    if semver.fullmatch(event["plugin_version"]) is None:
        return False
    if event_type == "workflow_completed":
        elapsed = event.get("elapsed_seconds")
        if (isinstance(elapsed, bool) or not isinstance(elapsed, int)
                or not 0 <= elapsed <= 604800):
            return False
    return True


def queued_event_count(path, installation_key):
    raw_value = read_bounded(path, MAX_QUEUE_BYTES)
    if raw_value is None:
        return 0 if not path.exists() else None
    try:
        lines = raw_value.decode("utf-8").splitlines()
    except UnicodeError:
        return None
    if len(lines) > MAX_QUEUE_EVENTS:
        return None
    count = 0
    for line in lines:
        try:
            record = json.loads(line)
        except (ValueError, TypeError):
            return None
        if (not isinstance(record, dict)
                or set(record) != {"installation_key", "event"}
                or not isinstance(record.get("installation_key"), str)
                or sha256.fullmatch(record["installation_key"]) is None
                or not valid_queue_event(record.get("event"))):
            return None
        if (record["installation_key"] == installation_key
                and record["event"]["client"] == CLIENT):
            count += 1
    return count


# Claude sends session context on stdin. The footer does not need it, so consume only
# a small fixed amount and never inspect or display it.
try:
    sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
except (AttributeError, OSError):
    pass

summary = read_small_object(summary_path)
config = read_small_object(config_path)
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

linked_token = claude_token(config)
if linked_token is None:
    status_text = "usage not linked · connect in your dashboard"
else:
    pieces = []
    started = summary.get("tracked_prompts")
    completed = summary.get("completed_workflows")
    if valid_count(started) and valid_count(completed) and completed <= started:
        pieces.append(f"{completed:,} completed workflow{'s' if completed != 1 else ''}")
    elif valid_count(started):
        pieces.append(f"{started:,} workflow{'s' if started != 1 else ''} started")

    estimates_configured = summary.get("estimates_configured")
    if estimates_configured is True:
        hours = summary.get("estimated_hours_saved")
        value = summary.get("estimated_value_usd")
        if valid_number(hours) and valid_number(value):
            pieces.extend((f"{hours:.1f}h est. saved", f"${value:,.2f} est. value"))
        else:
            pieces.append("estimates unavailable")
    elif estimates_configured is False or estimates_configured is None:
        pieces.append("set your time baseline in the dashboard")
    else:
        pieces.append("estimates unavailable")

    age_text = summary_age_text(summary)
    if age_text:
        pieces.append(age_text)

    installation_key = hashlib.sha256(
        ("chatdata-installation:" + linked_token).encode("utf-8")
    ).hexdigest()
    pending = queued_event_count(queue_path, installation_key)
    if pending:
        pieces.append(
            f"{pending:,} event{'s' if pending != 1 else ''} pending sync (totals may lag)"
        )
    status_text = " · ".join(pieces)

print(f"ChatData · {status_text}{update_notice}")
