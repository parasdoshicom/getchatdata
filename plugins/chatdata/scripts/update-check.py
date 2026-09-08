#!/usr/bin/env python3
"""Quiet, bounded ChatData release checks for Claude Code."""
import argparse
import json
import math
import os
import re
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


RELEASE_URL = "https://api.github.com/repos/parasdoshicom/getchatdata/releases/latest"
CACHE_SECONDS = 24 * 60 * 60
MAX_RESPONSE_BYTES = 64 * 1024
NETWORK_TIMEOUT_SECONDS = 1.25
HOOK_WORKER_TIMEOUT_SECONDS = 1.6
SEMVER = re.compile(r"^(?:v)?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
WRAPPER_MARKERS = (
    b'#!/usr/bin/env python3\n"""Preserve an existing Claude status line and append ChatData estimates."""',
    b'#!/usr/bin/env python3\n"""Show ChatData estimates and update notices in Claude Code."""',
)


def _home():
    return Path(os.environ.get("CHATDATA_HOME", str(Path.home() / ".chatdata")))


def _cache_path():
    return _home() / "update-check.json"


def _package_root():
    return Path(__file__).resolve().parent


def _installed_version():
    try:
        raw = (_package_root() / "package-info.json").read_text(encoding="utf-8")
        value = json.loads(raw).get("version")
    except (OSError, ValueError, AttributeError):
        return None
    return _normalize_version(value)


def _normalize_version(value):
    if not isinstance(value, str):
        return None
    match = SEMVER.fullmatch(value)
    if not match:
        return None
    parts = match.groups()
    if any(len(part) > 9 for part in parts):
        return None
    return ".".join(str(int(part)) for part in parts)


def _version_tuple(value):
    normalized = _normalize_version(value)
    return tuple(int(part) for part in normalized.split(".")) if normalized else None


def _read_json(path, max_bytes=16 * 1024):
    try:
        if not path.is_file() or path.stat().st_size > max_bytes:
            return None
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _write_cache(value):
    root = _home()
    root.mkdir(parents=True, exist_ok=True)
    try:
        root.chmod(0o700)
    except OSError:
        pass
    handle, temporary = tempfile.mkstemp(prefix=".chatdata-update-", dir=str(root))
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(value, stream, separators=(",", ":"), sort_keys=True)
            stream.write("\n")
        os.chmod(temporary, 0o600)
        os.replace(temporary, _cache_path())
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _valid_cache(value):
    if not isinstance(value, dict) or set(value) != {
            "schema_version", "checked_at_epoch", "installed_version",
            "latest_version", "update_available"}:
        return None
    checked_at = value.get("checked_at_epoch")
    if (value.get("schema_version") != 1 or isinstance(checked_at, bool)
            or not isinstance(checked_at, (int, float)) or not math.isfinite(checked_at)
            or not isinstance(value.get("update_available"), bool)):
        return None
    installed = _normalize_version(value.get("installed_version"))
    latest_raw = value.get("latest_version")
    latest = None if latest_raw is None else _normalize_version(latest_raw)
    if not installed or (latest_raw is not None and not latest):
        return None
    return {
        "schema_version": 1,
        "checked_at_epoch": float(checked_at),
        "installed_version": installed,
        "latest_version": latest,
        "update_available": bool(latest and _version_tuple(latest) > _version_tuple(installed)),
    }


def _fetch_latest():
    request = Request(
        RELEASE_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ChatData-update-check",
        },
    )
    try:
        with urlopen(request, timeout=NETWORK_TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError):
        return None
    if len(raw) > MAX_RESPONSE_BYTES:
        return None
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError):
        return None
    if not isinstance(payload, dict) or payload.get("draft") is not False or payload.get("prerelease") is not False:
        return None
    return _normalize_version(payload.get("tag_name"))


def _settings_path():
    override = os.environ.get("CHATDATA_CLAUDE_SETTINGS")
    if override:
        return Path(override)
    config_root = Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")))
    return config_root / "settings.json"


def refresh_owned_statusline():
    """Refresh only the wrapper ChatData previously installed and still owns."""
    root = _home()
    destination = root / "claude-statusline.py"
    backup = _read_json(root / "claude-statusline-backup.json")
    settings = _read_json(_settings_path())
    source = _package_root() / "claude-statusline.py"
    if not backup or not settings or not source.is_file() or not destination.is_file():
        return False
    try:
        if destination.is_symlink() or not stat.S_ISREG(destination.stat().st_mode):
            return False
        current = settings.get("statusLine")
        installed_value = backup.get("installed_value")
        wrapper_command = backup.get("wrapper_command")
        if current != installed_value or not isinstance(current, dict):
            return False
        if current.get("command") != wrapper_command or not isinstance(wrapper_command, str):
            return False
        if str(destination) not in wrapper_command:
            return False
        old = destination.read_bytes()
        replacement = source.read_bytes()
        if not any(old.startswith(marker) for marker in WRAPPER_MARKERS) or old == replacement:
            return False
        handle, temporary = tempfile.mkstemp(prefix=".chatdata-statusline-", dir=str(root))
        with os.fdopen(handle, "wb") as stream:
            stream.write(replacement)
        os.chmod(temporary, 0o700)
        os.replace(temporary, destination)
        return True
    except OSError:
        return False
    finally:
        try:
            os.unlink(temporary)
        except (NameError, FileNotFoundError):
            pass


def check_for_update(now=None):
    refresh_owned_statusline()
    installed = _installed_version()
    if not installed or os.environ.get("CHATDATA_UPDATE_CHECK", "1").strip().lower() in {
            "0", "false", "off", "no"}:
        return None
    current_time = time.time() if now is None else float(now)
    cached = _valid_cache(_read_json(_cache_path()))
    fresh = cached and 0 <= current_time - cached["checked_at_epoch"] < CACHE_SECONDS
    if fresh:
        latest = cached["latest_version"]
    else:
        previous_latest = cached["latest_version"] if cached else None
        attempt = {
            "schema_version": 1,
            "checked_at_epoch": current_time,
            "installed_version": installed,
            "latest_version": previous_latest,
            "update_available": bool(
                previous_latest and _version_tuple(previous_latest) > _version_tuple(installed)),
        }
        try:
            _write_cache(attempt)
        except OSError:
            return None
        try:
            fetched = _fetch_latest()
        except Exception:
            return attempt
        latest = fetched if fetched is not None else previous_latest
        cached = dict(attempt)
        cached["latest_version"] = latest
        cached["update_available"] = bool(
            latest and _version_tuple(latest) > _version_tuple(installed))
        try:
            _write_cache(cached)
        except OSError:
            return attempt
    available = bool(latest and _version_tuple(latest) > _version_tuple(installed))
    if not cached or cached["installed_version"] != installed or cached["update_available"] != available:
        cached = {
            "schema_version": 1,
            "checked_at_epoch": cached["checked_at_epoch"] if cached else current_time,
            "installed_version": installed,
            "latest_version": latest,
            "update_available": available,
        }
        _write_cache(cached)
    return cached


def _hook_output():
    try:
        result = check_for_update()
    except Exception:
        return {}
    if not result or not result["update_available"]:
        return {}
    return {
        "systemMessage": (
            f"ChatData {result['latest_version']} is available "
            f"(installed: {result['installed_version']}). Run /chatdata:update to update, "
            "then run /reload-plugins."
        )
    }


def _run_hook_worker():
    if os.environ.get("CHATDATA_UPDATE_CHECK", "1").strip().lower() in {"0", "false", "off", "no"}:
        return {}
    try:
        completed = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "hook-worker"],
            capture_output=True,
            text=True,
            timeout=HOOK_WORKER_TIMEOUT_SECONDS,
            check=False,
        )
        if completed.returncode != 0 or len(completed.stdout) > 2048:
            return {}
        parsed = json.loads(completed.stdout)
        if parsed == {}:
            return {}
        message = parsed.get("systemMessage") if isinstance(parsed, dict) else None
        if not isinstance(message, str) or len(message) > 512:
            return {}
        return {"systemMessage": message}
    except (OSError, subprocess.SubprocessError, ValueError, TypeError):
        return {}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("hook", "hook-worker", "clear"), nargs="?", default="hook")
    args = parser.parse_args()
    if args.command == "clear":
        try:
            _cache_path().unlink()
        except FileNotFoundError:
            pass
        return 0
    output = _hook_output() if args.command == "hook-worker" else _run_hook_worker()
    print(json.dumps(output, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
