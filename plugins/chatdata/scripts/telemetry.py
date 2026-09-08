#!/usr/bin/env python3
"""Opt-in, content-free usage tracking for explicit ChatData workflows."""
import argparse
import getpass
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


API_ORIGIN = "https://getchatdata.com"
CONSENT_VERSION = "individual-usage-v1"
MAX_QUEUE = 500
SKILLS = {
    "analysis-review", "causal-inference", "data-quality", "data-science",
    "decision-brief", "experiment-analysis", "experiment-design",
    "exploratory-analysis", "forecasting", "funnel-analysis",
    "metric-definition", "predictive-modeling", "retention", "root-cause",
    "sql-review", "visualization",
}
CLIENTS = {"claude-code", "codex", "cursor", "other"}


class DeliveryError(RuntimeError):
    """A delivery failure with a fixed category safe to show to an agent."""

    def __init__(self, category, message):
        super().__init__(message)
        self.category = category


def home():
    return Path(os.environ.get("CHATDATA_HOME", str(Path.home() / ".chatdata")))


def paths():
    root = home()
    return {
        "root": root,
        "config": root / "individual-telemetry.json",
        "queue": root / "individual-telemetry-queue.jsonl",
        "state": root / "individual-telemetry-state.json",
        "summary": root / "individual-telemetry-summary.json",
        "lock": root / ".individual-telemetry.lock",
        "statusline": root / "claude-statusline.py",
        "statusline_backup": root / "claude-statusline-backup.json",
        "statusline_preference": root / "claude-footer-preference.json",
    }


def _ensure_root():
    root = paths()["root"]
    root.mkdir(parents=True, exist_ok=True)
    try:
        root.chmod(0o700)
    except OSError:
        pass
    return root


def _read_json(path, default):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return default
    return value


def _write_json(path, value):
    _ensure_root()
    fd, name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, separators=(",", ":"), sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, 0o600)
        os.replace(name, path)
    finally:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass


@contextmanager
def _locked(timeout=1.5):
    _ensure_root()
    lock = paths()["lock"]
    deadline = time.monotonic() + timeout
    while True:
        try:
            lock.mkdir(mode=0o700)
            break
        except FileExistsError:
            try:
                if time.time() - lock.stat().st_mtime > 30:
                    lock.rmdir()
                    continue
            except (FileNotFoundError, OSError):
                continue
            if time.monotonic() >= deadline:
                raise RuntimeError("ChatData telemetry state is busy; retry once.")
            time.sleep(0.025)
    try:
        yield
    finally:
        try:
            lock.rmdir()
        except FileNotFoundError:
            pass


def _config():
    value = _read_json(paths()["config"], {})
    if not isinstance(value, dict) or value.get("consent_version") != CONSENT_VERSION:
        return None
    installations = value.get("installations")
    if not isinstance(installations, dict) or not installations:
        return None
    for client, item in installations.items():
        if client not in CLIENTS or not isinstance(item, dict):
            return None
        token = item.get("token")
        if not isinstance(token, str) or not re.fullmatch(r"cdi_[A-Za-z0-9_-]{43}", token):
            return None
    return value


def _installation_config(client):
    config = _config()
    if not config:
        return None
    item = config["installations"].get(client)
    return item if isinstance(item, dict) else None


def _installation_key(token):
    return hashlib.sha256(("chatdata-installation:" + token).encode()).hexdigest()


def _utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _version():
    return json.loads((Path(__file__).resolve().parent / "package-info.json").read_text())["version"]


def _request(method, path, token, payload=None, timeout=3):
    data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
    origin = os.environ.get("CHATDATA_API_ORIGIN", API_ORIGIN).rstrip("/")
    parsed_origin = urlparse(origin)
    production = origin == API_ORIGIN
    loopback_test = parsed_origin.scheme == "http" and parsed_origin.hostname in {"127.0.0.1", "localhost"}
    if not production and not loopback_test:
        raise RuntimeError("ChatData usage reporting only connects to getchatdata.com or a loopback test server.")
    request = Request(origin + path, data=data, method=method,
                      headers={"Authorization": "Bearer " + token,
                               "Content-Type": "application/json",
                               "User-Agent": "ChatData-individual/" + _version()})
    try:
        with urlopen(request, timeout=timeout) as response:
            raw_response = response.read().decode("utf-8")
    except HTTPError as error:
        categories = {
            400: "invalid_event",
            401: "authorization_failed",
            403: "authorization_failed",
            429: "rate_limited",
        }
        category = categories.get(error.code, "service_error")
        raise DeliveryError(category, "ChatData usage service returned HTTP " + str(error.code)) from None
    except (URLError, TimeoutError, OSError, UnicodeError):
        raise DeliveryError(
            "network_unavailable",
            "ChatData usage service is unavailable; usage remains queued locally.",
        ) from None
    try:
        parsed = json.loads(raw_response)
    except ValueError:
        raise DeliveryError("invalid_response", "ChatData usage service returned an invalid response.") from None
    if not isinstance(parsed, dict) or parsed.get("ok") is not True:
        raise DeliveryError("invalid_response", "ChatData usage service returned an invalid response.")
    return parsed


def _summary_from_response(response):
    summary = response.get("account_summary")
    if not isinstance(summary, dict):
        return
    allowed = {key: summary.get(key) for key in (
        "tracked_prompts", "completed_workflows", "observed_elapsed_seconds",
        "estimated_hours_saved", "estimated_value_usd", "estimates_configured",
        "baseline_minutes_per_workflow", "hourly_value_usd", "updated_at")}
    _write_json(paths()["summary"], allowed)


def _valid_event(event):
    if not isinstance(event, dict):
        return False
    expected = {"event_id", "event_type", "workflow_id", "occurred_at", "client", "skill_id", "plugin_version"}
    event_type = event.get("event_type")
    if event_type == "workflow_completed":
        expected.add("elapsed_seconds")
    elif event_type != "workflow_started":
        return False
    if set(event) != expected or event.get("client") not in CLIENTS or event.get("skill_id") not in SKILLS:
        return False
    try:
        uuid.UUID(event["event_id"])
        uuid.UUID(event["workflow_id"])
    except (ValueError, AttributeError, TypeError):
        return False
    if _event_time(event) is None:
        return False
    version = event.get("plugin_version")
    if not isinstance(version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        return False
    if event_type == "workflow_completed":
        elapsed = event.get("elapsed_seconds")
        if isinstance(elapsed, bool) or not isinstance(elapsed, int) or not 0 <= elapsed <= 604800:
            return False
    return True


def _queue_records():
    path = paths()["queue"]
    if not path.exists():
        return []
    records = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            value = json.loads(line)
            if (not isinstance(value, dict) or set(value) != {"installation_key", "event"}
                    or not isinstance(value["installation_key"], str)
                    or not re.fullmatch(r"[a-f0-9]{64}", value["installation_key"])
                    or not _valid_event(value["event"])):
                raise ValueError
            records.append(value)
    except (OSError, ValueError):
        raise RuntimeError("ChatData's local usage queue is unreadable; it was left unchanged.") from None
    return records


def _queue_events():
    return [record["event"] for record in _queue_records()]


def _write_queue(records):
    path = paths()["queue"]
    if not records:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        return
    _ensure_root()
    if len(records) > MAX_QUEUE:
        raise RuntimeError("ChatData's local usage queue is full; no new workflow was counted.")
    text = "".join(json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n" for record in records)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, 0o600)
        os.replace(name, path)
    finally:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass


def _enqueue(event):
    if not _valid_event(event):
        raise ValueError("Telemetry event fields do not match the content-free schema.")
    installation = _installation_config(event["client"])
    if not installation:
        raise RuntimeError("This client is not linked to ChatData usage reporting.")
    key = _installation_key(installation["token"])
    with _locked():
        queued = _queue_records()
        if any(item["event"].get("event_id") == event["event_id"] for item in queued):
            return
        if len(queued) >= MAX_QUEUE:
            raise RuntimeError("ChatData's local usage queue is full; no new workflow was counted.")
        queued.append({"installation_key": key, "event": event})
        _write_queue(queued)


def _event_time(event):
    try:
        value = str(event["occurred_at"]).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(timezone.utc)
    except (KeyError, TypeError, ValueError):
        return None


def _prune_expired(records):
    """Discard unsendable local events after the server's 90-day window."""
    cutoff = datetime.now(timezone.utc).timestamp() - (90 * 24 * 60 * 60)
    return [record for record in records
            if _event_time(record["event"]) is not None
            and _event_time(record["event"]).timestamp() >= cutoff]


def flush(silent=False):
    config = _config()
    if not config:
        return {"telemetry": "not_linked", "queued": 0}
    with _locked():
        queued = _queue_records()
        current = _prune_expired(queued)
        if current != queued:
            _write_queue(current)
        queued = current
    if not queued:
        return {"telemetry": "linked", "queued": 0, "sent": 0,
                "delivery_status": "nothing_queued"}
    sent = 0
    failures = []
    for client, installation in config["installations"].items():
        key = _installation_key(installation["token"])
        batch_records = [record for record in queued
                         if record["installation_key"] == key and record["event"]["client"] == client][:50]
        if not batch_records:
            continue
        batch = [record["event"] for record in batch_records]
        try:
            response = _request("POST", "/api/individual/usage", installation["token"],
                                {"schema_version": 1, "events": batch})
            handled = set(response.get("accepted_event_ids", [])) | set(response.get("duplicate_event_ids", []))
            if not handled.issuperset(event["event_id"] for event in batch):
                raise DeliveryError(
                    "invalid_response",
                    "ChatData usage service did not acknowledge the full batch; it remains queued.",
                )
            with _locked():
                current = _queue_records()
                _write_queue([record for record in current
                              if record["event"].get("event_id") not in handled])
            _summary_from_response(response)
            sent += len(batch)
        except DeliveryError as error:
            failures.append((error.category, str(error)))
        except RuntimeError as error:
            failures.append(("service_error", str(error)))
    remaining = len(_queue_records())
    if failures and not silent:
        raise DeliveryError(failures[0][0], failures[0][1])
    result = {
        "telemetry": "linked",
        "queued": remaining,
        "sent": sent,
        "delivery_status": "retry_required" if failures else "delivered",
    }
    if failures:
        result["error_category"] = failures[0][0]
    return result


def _event(event_type, workflow_id, client, skill_id, elapsed_seconds=None):
    if client not in CLIENTS:
        raise ValueError("Unknown client.")
    if skill_id not in SKILLS:
        raise ValueError("Unknown ChatData skill.")
    event = {
        "event_id": str(uuid.uuid4()), "event_type": event_type,
        "workflow_id": workflow_id, "occurred_at": _utc_now(), "client": client,
        "skill_id": skill_id, "plugin_version": _version(),
    }
    if elapsed_seconds is not None:
        event["elapsed_seconds"] = max(0, min(int(elapsed_seconds), 604800))
    return event


def start(client, skill_id, no_flush=False):
    if not _installation_config(client):
        return {"telemetry": "not_linked"}
    workflow_id = str(uuid.uuid4())
    _enqueue(_event("workflow_started", workflow_id, client, skill_id))
    started_at = _utc_now()
    with _locked():
        state = _read_json(paths()["state"], {})
        if not isinstance(state, dict):
            state = {}
        manual = state.get("manual", {})
        if not isinstance(manual, dict):
            manual = {}
        manual[workflow_id] = {"client": client, "skill_id": skill_id,
                               "started_epoch": time.time(), "started_at": started_at}
        state["manual"] = manual
        _write_json(paths()["state"], state)
    result = {"telemetry": "linked", "workflow_id": workflow_id, "started_at": started_at}
    if not no_flush:
        result["delivery"] = flush(silent=True)
    return result


def complete(workflow_id, client, skill_id, elapsed_seconds=None, no_flush=False):
    try:
        uuid.UUID(workflow_id)
    except (ValueError, AttributeError):
        raise ValueError("workflow_id must be the UUID returned by start.") from None
    if not _installation_config(client):
        return {"telemetry": "not_linked"}
    with _locked():
        state = _read_json(paths()["state"], {})
        if not isinstance(state, dict):
            state = {}
        manual = state.get("manual", {})
        if not isinstance(manual, dict):
            manual = {}
        item = manual.get(workflow_id)
        if not isinstance(item, dict):
            raise ValueError("workflow_id is not an active local ChatData workflow.")
        if item.get("client") != client or item.get("skill_id") != skill_id:
            raise ValueError("client and skill_id must match the values used by start.")
        if elapsed_seconds is None:
            try:
                elapsed_seconds = max(0, int(time.time() - float(item["started_epoch"])))
            except (KeyError, TypeError, ValueError):
                raise ValueError("The local start time is unavailable; start a new workflow.") from None
    _enqueue(_event("workflow_completed", workflow_id, client, skill_id, elapsed_seconds))
    with _locked():
        state = _read_json(paths()["state"], {})
        if isinstance(state, dict):
            manual = state.get("manual", {})
            if isinstance(manual, dict):
                manual.pop(workflow_id, None)
                state["manual"] = manual
            _write_json(paths()["state"], state)
    result = {"telemetry": "linked", "workflow_id": workflow_id, "completed": True}
    if not no_flush:
        result["delivery"] = flush(silent=True)
    return result


def _session_key(session_id):
    return hashlib.sha256(("chatdata-local-session:" + session_id).encode()).hexdigest()


def _skill_slug(value):
    if not isinstance(value, str):
        return None
    value = value.strip().lower()
    for prefix in ("chatdata:", "chatdata-", "chatdata/"):
        if value.startswith(prefix):
            value = value[len(prefix):]
            break
    return value if value in SKILLS else None


def claude_hook():
    try:
        payload = json.load(sys.stdin)
    except (ValueError, TypeError):
        return
    if not _installation_config("claude-code") or not isinstance(payload, dict):
        return
    session_id = payload.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        return
    key = _session_key(session_id)
    event_name = payload.get("hook_event_name")
    state_path = paths()["state"]
    with _locked():
        state = _read_json(state_path, {})
        active = state.get("active", {}) if isinstance(state, dict) else {}
        if not isinstance(active, dict):
            active = {}
        if event_name in ("UserPromptExpansion", "PreToolUse"):
            if event_name == "UserPromptExpansion":
                skill_id = _skill_slug(payload.get("command_name"))
            else:
                tool = payload.get("tool_input", {})
                skill_id = None
                if isinstance(tool, dict):
                    for field in ("skill", "name", "skill_name", "command"):
                        skill_id = _skill_slug(tool.get(field))
                        if skill_id:
                            break
            if skill_id and key not in active:
                workflow_id = str(uuid.uuid4())
                queued = _queue_records()
                if len(queued) < MAX_QUEUE:
                    active[key] = {"workflow_id": workflow_id, "skill_id": skill_id,
                                   "started_epoch": time.time(), "started_at": _utc_now()}
                    event = _event("workflow_started", workflow_id, "claude-code", skill_id)
                    installation = _installation_config("claude-code")
                    _write_queue(queued + [{"installation_key": _installation_key(installation["token"]),
                                             "event": event}])
        elif event_name == "Stop":
            item = active.pop(key, None)
            if isinstance(item, dict) and item.get("skill_id") in SKILLS:
                elapsed = max(0, int(time.time() - float(item.get("started_epoch", time.time()))))
                queued = _queue_records()
                if len(queued) < MAX_QUEUE:
                    event = _event("workflow_completed", item["workflow_id"],
                                   "claude-code", item["skill_id"], elapsed)
                    installation = _installation_config("claude-code")
                    _write_queue(queued + [{"installation_key": _installation_key(installation["token"]),
                                             "event": event}])
        state["active"] = active
        _write_json(state_path, state)
    if event_name == "Stop":
        flush(silent=True)


def _claude_settings_path():
    override = os.environ.get("CHATDATA_CLAUDE_SETTINGS")
    if override:
        return Path(override)
    config_root = Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")))
    return config_root / "settings.json"


def _footer_module():
    path = Path(__file__).resolve().parent / "footer.py"
    spec = importlib.util.spec_from_file_location("chatdata_footer", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("ChatData's Claude footer helper is unavailable.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def install_statusline():
    return _footer_module().enable()


def restore_statusline():
    return _footer_module().restore()


def connect(client, enable_statusline=False):
    print("ChatData usage tracking sends only workflow IDs, event times, client, skill, plugin version, and elapsed seconds.")
    print("It never sends prompts, files, paths, project names, queries, results, model details, or session IDs.")
    answer = input("Link this installation and send that metadata? [y/N] ").strip().lower()
    if answer not in ("y", "yes"):
        return {"telemetry": "not_linked", "consent": False}
    token = getpass.getpass("Paste the installation token from your ChatData dashboard: ").strip()
    if not re.fullmatch(r"cdi_[A-Za-z0-9_-]{43}", token):
        raise ValueError("The installation token is not valid.")
    remote = _request("GET", "/api/individual/config", token)
    if remote.get("client") != client or remote.get("consent_version") != CONSENT_VERSION:
        raise ValueError("That installation token belongs to a different client or consent version.")
    config = _config() or {"consent_version": CONSENT_VERSION, "installations": {}}
    installations = dict(config["installations"])
    previous = installations.get(client)
    discarded = 0
    if isinstance(previous, dict) and previous.get("token") != token:
        old_key = _installation_key(previous["token"])
        with _locked():
            records = _queue_records()
            kept = [record for record in records if record["installation_key"] != old_key]
            discarded = len(records) - len(kept)
            _write_queue(kept)
    installations[client] = {"token": token, "connected_at": _utc_now()}
    config = {"consent_version": CONSENT_VERSION, "installations": installations}
    _write_json(paths()["config"], config)
    _summary_from_response(remote)
    result = {"telemetry": "linked", "consent_version": CONSENT_VERSION,
              "client": client, "content_collected": False}
    if discarded:
        result["discarded_previous_installation_events"] = discarded
    if client == "claude-code" and enable_statusline:
        result["claude_statusline"] = install_statusline()
    return result


def disconnect(erase_local_usage=False):
    p = paths()
    for key in ("config", "queue", "state"):
        p[key].unlink(missing_ok=True)
    if erase_local_usage:
        p["summary"].unlink(missing_ok=True)
    return {"telemetry": "disconnected", "server_token_revoked": False,
            "dashboard_revoke_required": True, "local_summary_preserved": not erase_local_usage,
            "claude_statusline": {"statusline": "independent"}}


def status():
    config = _config()
    queued = _queue_records() if paths()["queue"].exists() else []
    queued_by_client = {client: 0 for client in sorted(config["installations"])} if config else {}
    for record in queued:
        client = record["event"]["client"]
        queued_by_client[client] = queued_by_client.get(client, 0) + 1
    summary = _read_json(paths()["summary"], {})
    return {"telemetry": "linked" if config else "not_linked",
            "consent_version": config.get("consent_version") if config else None,
            "clients": sorted(config["installations"]) if config else [],
            "queued_events": len(queued), "queued_by_client": queued_by_client,
            "account_summary": summary if isinstance(summary, dict) else {}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    link = commands.add_parser("connect")
    link.add_argument("--client", choices=sorted(CLIENTS), required=True)
    link.add_argument("--enable-statusline", action="store_true")
    begin = commands.add_parser("start")
    begin.add_argument("--client", choices=sorted(CLIENTS), required=True)
    begin.add_argument("--skill-id", choices=sorted(SKILLS), required=True)
    begin.add_argument("--no-flush", action="store_true")
    end = commands.add_parser("complete")
    end.add_argument("workflow_id")
    end.add_argument("--client", choices=sorted(CLIENTS), required=True)
    end.add_argument("--skill-id", choices=sorted(SKILLS), required=True)
    end.add_argument("--elapsed-seconds", type=int)
    end.add_argument("--no-flush", action="store_true")
    flush_command = commands.add_parser("flush")
    flush_command.add_argument("--silent", action="store_true")
    commands.add_parser("status")
    hook = commands.add_parser("claude-hook")
    unlink = commands.add_parser("disconnect")
    unlink.add_argument("--erase-local-usage", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "connect":
            result = connect(args.client, args.enable_statusline)
        elif args.command == "start":
            result = start(args.client, args.skill_id, args.no_flush)
        elif args.command == "complete":
            result = complete(args.workflow_id, args.client, args.skill_id,
                              args.elapsed_seconds, args.no_flush)
        elif args.command == "flush":
            result = flush(args.silent)
        elif args.command == "status":
            result = status()
        elif args.command == "disconnect":
            result = disconnect(args.erase_local_usage)
        else:
            claude_hook()
            return 0
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
