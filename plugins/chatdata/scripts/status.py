#!/usr/bin/env python3
"""Show a safe, offline ChatData status report."""
import argparse
from datetime import datetime
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
import uuid


CLIENTS = ("claude-code", "codex", "cursor")
CLIENT_LABELS = {
    "claude-code": "Claude Code",
    "codex": "Codex",
    "cursor": "Cursor",
}
CONSENT_VERSION = "individual-usage-v1"
DEFAULT_HOURLY_VALUE_USD = 125
MAX_JSON_BYTES = 64 * 1024
MAX_QUEUE_BYTES = 512 * 1024
MAX_QUEUE_EVENTS = 500
SKILLS = {
    "analysis-review", "causal-inference", "data-quality", "data-science",
    "decision-brief", "experiment-analysis", "experiment-design",
    "exploratory-analysis", "forecasting", "funnel-analysis",
    "metric-definition", "predictive-modeling", "retention", "root-cause",
    "sql-review", "visualization",
}
TOKEN_PATTERN = re.compile(r"cdi_[A-Za-z0-9_-]{43}")
KEY_PATTERN = re.compile(r"[a-f0-9]{64}")
VERSION_PATTERN = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")


def _data_root():
    return Path(os.environ.get("CHATDATA_HOME", str(Path.home() / ".chatdata")))


def _paths():
    root = _data_root()
    return {
        "config": root / "individual-telemetry.json",
        "queue": root / "individual-telemetry-queue.jsonl",
        "summary": root / "individual-telemetry-summary.json",
    }


def _read_small_file(path, limit):
    """Read a regular file without following symlinks or exceeding limit."""
    try:
        if path.is_symlink():
            return "unsafe", None
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        descriptor = os.open(str(path), flags)
    except FileNotFoundError:
        return "missing", None
    except OSError:
        return "unreadable", None
    try:
        details = os.fstat(descriptor)
        if not stat.S_ISREG(details.st_mode) or details.st_size > limit:
            return "unsafe", None
        chunks = []
        remaining = limit + 1
        while remaining:
            chunk = os.read(descriptor, remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        if len(data) > limit:
            return "unsafe", None
        return "ok", data
    except OSError:
        return "unreadable", None
    finally:
        os.close(descriptor)


def _read_small_object(path):
    state, raw = _read_small_file(path, MAX_JSON_BYTES)
    if state != "ok":
        return state, None
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError):
        return "malformed", None
    if not isinstance(value, dict):
        return "malformed", None
    return "ok", value


def _version():
    path = Path(__file__).resolve().parent / "package-info.json"
    state, raw = _read_small_file(path, MAX_JSON_BYTES)
    if state != "ok":
        return "unknown"
    try:
        value = json.loads(raw.decode("utf-8"))
        version = value.get("version") if isinstance(value, dict) else None
    except (UnicodeError, ValueError):
        version = None
    return version if isinstance(version, str) and VERSION_PATTERN.fullmatch(version) else "unknown"


def _client_links(path):
    state, value = _read_small_object(path)
    if state == "missing":
        return state, {client: "not_linked" for client in CLIENTS}
    if state != "ok" or value.get("consent_version") != CONSENT_VERSION:
        return state if state != "ok" else "malformed", {client: "unknown" for client in CLIENTS}
    installations = value.get("installations")
    if not isinstance(installations, dict):
        return "malformed", {client: "unknown" for client in CLIENTS}

    links = {}
    config_state = "ok"
    for client in CLIENTS:
        item = installations.get(client)
        if item is None:
            links[client] = "not_linked"
        elif isinstance(item, dict) and isinstance(item.get("token"), str) \
                and TOKEN_PATTERN.fullmatch(item["token"]):
            links[client] = "linked_locally"
        else:
            links[client] = "unknown"
            config_state = "malformed"
    return config_state, links


def _iso_timestamp(value):
    if not isinstance(value, str) or len(value) > 40:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return value


def _finite_number(value, minimum=0, maximum=1000000):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number) or not minimum <= number <= maximum:
        return None
    return value


def _nonnegative_integer(value, maximum=1000000000):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
        return None
    return value


def _summary(path):
    state, value = _read_small_object(path)
    empty = {
        "available": False,
        "updated_at": None,
        "estimates_configured": False,
        "baseline_minutes_per_workflow": None,
        "hourly_value_usd": DEFAULT_HOURLY_VALUE_USD,
        "hourly_value_source": "dashboard_default",
        "tracked_prompts": None,
        "completed_workflows": None,
        "observed_elapsed_seconds": None,
        "estimated_hours_saved": None,
        "estimated_value_usd": None,
    }
    if state != "ok":
        return state, empty

    updated_at = _iso_timestamp(value.get("updated_at"))
    totals = {
        "tracked_prompts": _nonnegative_integer(value.get("tracked_prompts")),
        "completed_workflows": _nonnegative_integer(value.get("completed_workflows")),
        "observed_elapsed_seconds": _nonnegative_integer(
            value.get("observed_elapsed_seconds"), maximum=100000000000),
    }
    estimates_configured = value.get("estimates_configured") is True
    baseline = _finite_number(value.get("baseline_minutes_per_workflow"), 0, 10080)
    hourly = _finite_number(value.get("hourly_value_usd"), 0, 100000)
    if not estimates_configured or baseline is None or hourly is None:
        return "ok", {**empty, **totals, "available": True, "updated_at": updated_at,
                      "hourly_value_usd": hourly if hourly is not None else DEFAULT_HOURLY_VALUE_USD,
                      "hourly_value_source": "dashboard_setting" if hourly is not None else "dashboard_default"}
    estimated_hours = _finite_number(value.get("estimated_hours_saved"), 0, 1000000000)
    estimated_value = _finite_number(value.get("estimated_value_usd"), 0, 100000000000)
    return "ok", {
        **totals,
        "available": True,
        "updated_at": updated_at,
        "estimates_configured": True,
        "baseline_minutes_per_workflow": baseline,
        "hourly_value_usd": hourly,
        "hourly_value_source": "dashboard_setting",
        "estimated_hours_saved": estimated_hours,
        "estimated_value_usd": estimated_value,
    }


def _valid_queue_event(value):
    if not isinstance(value, dict) or set(value) != {"installation_key", "event"}:
        return False
    if not isinstance(value.get("installation_key"), str) \
            or not KEY_PATTERN.fullmatch(value["installation_key"]):
        return False
    event = value.get("event")
    if not isinstance(event, dict):
        return False
    event_type = event.get("event_type")
    expected = {"event_id", "event_type", "workflow_id", "occurred_at", "client", "skill_id", "plugin_version"}
    if event_type == "workflow_completed":
        expected.add("elapsed_seconds")
        elapsed = event.get("elapsed_seconds")
        if isinstance(elapsed, bool) or not isinstance(elapsed, int) or not 0 <= elapsed <= 604800:
            return False
    elif event_type != "workflow_started":
        return False
    if set(event) != expected or event.get("client") not in CLIENTS + ("other",):
        return False
    if event.get("skill_id") not in SKILLS:
        return False
    if not isinstance(event.get("plugin_version"), str) \
            or not VERSION_PATTERN.fullmatch(event["plugin_version"]):
        return False
    if _iso_timestamp(event.get("occurred_at")) is None:
        return False
    try:
        uuid.UUID(event["event_id"])
        uuid.UUID(event["workflow_id"])
    except (ValueError, AttributeError, TypeError):
        return False
    return True


def _queue(path):
    state, raw = _read_small_file(path, MAX_QUEUE_BYTES)
    if state == "missing":
        return state, 0
    if state != "ok":
        return state, None
    try:
        lines = [line for line in raw.decode("utf-8").splitlines() if line.strip()]
        if len(lines) > MAX_QUEUE_EVENTS:
            return "unsafe", None
        records = [json.loads(line) for line in lines]
    except (UnicodeError, ValueError):
        return "malformed", None
    if not all(_valid_queue_event(record) for record in records):
        return "malformed", None
    return "ok", len(records)


def _run_checks():
    try:
        path = Path(__file__).resolve().parent / "doctor.py"
        spec = importlib.util.spec_from_file_location("chatdata_local_doctor", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.check_bundle()
    except Exception:  # The report stays useful even when local checks fail.
        return {"status": "failed", "checks": [],
                "next_step": "Refresh the ChatData package, then rerun status."}
    checks = []
    for item in result.get("checks", []):
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            checks.append({"name": item["name"][:80],
                           "status": "passed" if item.get("status") == "passed" else "failed"})
    return {"status": "passed" if result.get("status") == "passed" else "failed",
            "checks": checks,
            "scope": "Bundled synthetic calculations only; client skill discovery and connected data were not checked."}


def build_report(check=False):
    paths = _paths()
    config_state, links = _client_links(paths["config"])
    queue_state, pending = _queue(paths["queue"])
    summary_state, summary = _summary(paths["summary"])

    next_steps = []
    if config_state not in {"ok", "missing"}:
        next_steps.append({
            "code": "relink",
            "message": "The local link file cannot be trusted. Create a fresh installation link from the dashboard.",
            "action": "https://getchatdata.com/dashboard",
        })
    elif not any(value == "linked_locally" for value in links.values()):
        next_steps.append({
            "code": "link",
            "message": "Link the AI client you use so its ChatData workflows can appear in your dashboard.",
            "action": "https://getchatdata.com/dashboard",
        })

    if queue_state not in {"ok", "missing"}:
        next_steps.append({
            "code": "queue_unreadable",
            "message": "The local usage queue is unreadable and was left unchanged.",
            "action": "Update ChatData, then run status again. Contact support@getchatdata.com if it remains unreadable.",
        })
    elif pending:
        telemetry_path = Path(__file__).resolve().parent / "telemetry.py"
        next_steps.append({
            "code": "flush",
            "message": "%d usage event%s %s waiting to reach your dashboard." %
                       (pending, "" if pending == 1 else "s", "is" if pending == 1 else "are"),
            "action": 'python3 "%s" flush' % telemetry_path,
        })

    if not summary["estimates_configured"]:
        next_steps.append({
            "code": "set_baseline",
            "message": "Set your usual minutes per workflow. ChatData uses $125/hour by default, and you can change it.",
            "action": "https://getchatdata.com/dashboard",
        })
    if not next_steps:
        next_steps.append({"code": "none", "message": "No local action is needed.", "action": None})

    report = {
        "status": "ok",
        "product": "ChatData",
        "version": _version(),
        "offline_check": True,
        "server_authorization_checked": False,
        "clients": {client: {"label": CLIENT_LABELS[client], "local_link": links[client]}
                    for client in CLIENTS},
        "usage": {"pending_events": pending, "queue_state": queue_state},
        "cached_dashboard_summary": summary,
        "local_files": {
            "link_state": config_state,
            "summary_state": summary_state,
        },
        "next_steps": next_steps,
        "link_explanation": (
            "Linked locally means this computer has a ChatData installation credential. "
            "This offline report cannot confirm that the credential is still valid on the server."
        ),
        "summary_explanation": (
            "These account totals are a local cache from the last successful ChatData response. "
            "They combine linked clients and are not a live server check."
        ),
    }
    if check:
        report["local_checks"] = _run_checks()
    return report


def render(report):
    lines = ["ChatData %s" % report["version"], "", "Local setup"]
    labels = {"linked_locally": "linked locally", "not_linked": "not linked", "unknown": "unknown"}
    for client in CLIENTS:
        item = report["clients"][client]
        lines.append("  %-12s %s" % (item["label"], labels[item["local_link"]]))
    lines.extend(["", report["link_explanation"], "", "Usage dashboard"])
    pending = report["usage"]["pending_events"]
    if pending is None:
        lines.append("  Pending events      unknown (local queue unreadable)")
    else:
        lines.append("  Pending events      %d" % pending)
    summary = report["cached_dashboard_summary"]
    lines.append("  Cached summary      %s" % (summary["updated_at"] or "none"))
    lines.append("  Workflows started   %s" %
                 (summary["tracked_prompts"] if summary["tracked_prompts"] is not None else "unavailable"))
    lines.append("  Completed workflows %s" %
                 (summary["completed_workflows"]
                  if summary["completed_workflows"] is not None else "unavailable"))
    if summary["estimates_configured"]:
        lines.append("  Time baseline       %s minutes per workflow" % summary["baseline_minutes_per_workflow"])
        lines.append("  Hourly value        $%s/hour (dashboard setting)" % summary["hourly_value_usd"])
        if summary["estimated_hours_saved"] is not None \
                and summary["estimated_value_usd"] is not None:
            lines.append("  Estimated saved     %.1f hours · $%.0f (cached)" %
                         (summary["estimated_hours_saved"], summary["estimated_value_usd"]))
        else:
            lines.append("  Estimated saved     unavailable")
    else:
        lines.append("  Time baseline       not set")
        lines.append("  Hourly value        $125/hour default (change it in the dashboard)")
    lines.extend(["", report["summary_explanation"]])

    checks = report.get("local_checks")
    if checks:
        lines.extend(["", "Local helper checks"])
        if checks["checks"]:
            for item in checks["checks"]:
                lines.append("  %-30s %s" % (item["name"], item["status"]))
        else:
            lines.append("  failed")
        lines.append("  %s" % checks.get("scope", checks.get("next_step", "")))

    lines.extend(["", "Next"])
    for item in report["next_steps"]:
        lines.append("  %s" % item["message"])
        if item["action"]:
            lines.append("  %s" % item["action"])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable diagnostics.")
    parser.add_argument("--check", action="store_true",
                        help="Also run the three bundled synthetic calculation checks.")
    args = parser.parse_args()
    report = build_report(check=args.check)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render(report), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
