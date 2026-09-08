#!/usr/bin/env python3
"""Install, inspect, or restore ChatData's Claude Code status line."""
import argparse
from contextlib import contextmanager
import json
import os
import stat
import sys
import tempfile
import time
from pathlib import Path


MAX_JSON_BYTES = 64 * 1024
STATE_SCHEMA = 1


def _home():
    return Path(os.environ.get("CHATDATA_HOME", str(Path.home() / ".chatdata")))


def _settings_path():
    override = os.environ.get("CHATDATA_CLAUDE_SETTINGS")
    if override:
        return Path(override)
    config_root = Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")))
    return config_root / "settings.json"


def _paths():
    root = _home()
    return {
        "root": root,
        "wrapper": root / "claude-statusline.py",
        "backup": root / "claude-statusline-backup.json",
        "preference": root / "claude-footer-preference.json",
        "lock": root / ".claude-footer.lock",
    }


def _read_object(path, missing=None):
    try:
        if not path.is_file() or path.stat().st_size > MAX_JSON_BYTES:
            return missing
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    return value if isinstance(value, dict) else None


def _ensure_private_root():
    root = _paths()["root"]
    root.mkdir(parents=True, exist_ok=True)
    try:
        root.chmod(0o700)
    except OSError:
        pass
    return root


@contextmanager
def _mutation_lock(timeout=0.4):
    _ensure_private_root()
    lock = _paths()["lock"]
    deadline = time.monotonic() + timeout
    while True:
        try:
            lock.mkdir(mode=0o700)
            break
        except FileExistsError:
            try:
                metadata = lock.lstat()
                if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                    raise RuntimeError("ChatData's Claude footer lock is not a directory.")
                if time.time() - metadata.st_mtime > 10:
                    lock.rmdir()
                    continue
            except FileNotFoundError:
                pass
            except OSError:
                pass
            if time.monotonic() >= deadline:
                raise RuntimeError("ChatData's Claude footer is busy; retry once.")
            time.sleep(0.02)
    try:
        yield
    finally:
        try:
            lock.rmdir()
        except FileNotFoundError:
            pass


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix="." + path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(value, stream, separators=(",", ":"), sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _copy_wrapper():
    paths = _paths()
    source = Path(__file__).resolve().parent / "claude-statusline.py"
    if not source.is_file() or source.is_symlink():
        raise RuntimeError("ChatData's Claude status-line helper is unavailable.")
    replacement = source.read_bytes()
    _ensure_private_root()
    handle, temporary = tempfile.mkstemp(prefix=".claude-statusline.", dir=str(paths["root"]))
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(replacement)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o700)
        os.replace(temporary, paths["wrapper"])
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _wrapper_value():
    wrapper = _paths()["wrapper"]
    command = '"' + sys.executable.replace('"', '\\"') + '" "' + str(wrapper).replace('"', '\\"') + '"'
    return {"type": "command", "command": command}


def _preference():
    value = _read_object(_paths()["preference"])
    if (not value or value.get("schema_version") != STATE_SCHEMA
            or value.get("state") not in {"managed", "restored", "user_selected"}):
        return None
    return value


def _backup():
    value = _read_object(_paths()["backup"])
    if not value or not isinstance(value.get("had_status_line"), bool):
        return None
    installed = value.get("installed_value")
    if not isinstance(installed, dict) or not isinstance(value.get("wrapper_command"), str):
        return None
    return value


def _record_preference(state, installed_value=None):
    value = {"schema_version": STATE_SCHEMA, "state": state}
    if isinstance(installed_value, dict):
        value["installed_value"] = installed_value
    _write_json(_paths()["preference"], value)


def _settings_snapshot(path):
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return "missing", None
    except OSError:
        return "invalid", None
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        return "invalid", None
    if metadata.st_size > MAX_JSON_BYTES:
        return "invalid", None
    try:
        raw = path.read_bytes()
    except OSError:
        return "invalid", None
    if len(raw) > MAX_JSON_BYTES:
        return "invalid", None
    return "present", raw


def _safe_settings():
    path = _settings_path()
    state, raw = _settings_snapshot(path)
    if state == "missing":
        return path, {}, (state, raw)
    if state != "present":
        return path, None, (state, raw)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError, TypeError):
        value = None
    return path, value if isinstance(value, dict) else None, (state, raw)


def _write_settings_if_unchanged(path, value, snapshot):
    if _settings_snapshot(path) != snapshot:
        return False
    _write_json(path, value)
    return True


def _enable_locked():
    settings_path, settings, snapshot = _safe_settings()
    if settings is None:
        raise RuntimeError("Claude settings must be a JSON object smaller than 64 KiB.")
    paths = _paths()
    _ensure_private_root()
    _copy_wrapper()
    installed = _wrapper_value()
    current = settings.get("statusLine")
    backup = _backup()
    preference = _preference()
    if current == installed and backup:
        _record_preference("managed", installed)
        return {"statusline": "already_enabled", "path": str(settings_path)}
    # Explicit enable means the current user-selected footer becomes the restore target.
    new_backup = {
        "had_status_line": "statusLine" in settings,
        "value": current,
        "wrapper_command": installed["command"],
        "installed_value": installed,
    }
    settings["statusLine"] = installed
    _write_json(paths["backup"], new_backup)
    if not _write_settings_if_unchanged(settings_path, settings, snapshot):
        raise RuntimeError("Claude settings changed while ChatData was enabling the footer; retry once.")
    _record_preference("managed", installed)
    return {"statusline": "enabled", "path": str(settings_path),
            "preserved_existing": current is not None,
            "previous_preference": preference.get("state") if preference else None}


def enable():
    """Explicitly install ChatData and save the current footer for restoration."""
    with _mutation_lock():
        return _enable_locked()


def session_start():
    """Install once, refresh owned wrappers, and preserve later user choices."""
    try:
        with _mutation_lock():
            return _session_start_locked()
    except (OSError, RuntimeError):
        return {"statusline": "unchanged"}


def _session_start_locked():
    settings_path, settings, snapshot = _safe_settings()
    if settings is None:
        return {"statusline": "settings_unreadable"}
    paths = _paths()
    preference = _preference()
    backup = _backup()
    current = settings.get("statusLine")

    if preference and preference["state"] in {"restored", "user_selected"}:
        return {"statusline": preference["state"]}

    # A pre-marker ChatData install is still owned when settings exactly match its backup.
    if backup and current == backup.get("installed_value"):
        try:
            _copy_wrapper()
            installed = _wrapper_value()
            if installed != current:
                settings["statusLine"] = installed
                backup["installed_value"] = installed
                backup["wrapper_command"] = installed["command"]
                if not _write_settings_if_unchanged(settings_path, settings, snapshot):
                    return {"statusline": "unchanged"}
                _write_json(paths["backup"], backup)
            _record_preference("managed", installed)
            return {"statusline": "refreshed"}
        except OSError:
            return {"statusline": "unchanged"}

    if preference and preference["state"] == "managed":
        expected = preference.get("installed_value")
        if current != expected:
            try:
                _record_preference("user_selected")
            except OSError:
                pass
            return {"statusline": "user_selected"}
        # Corrupt/missing backup means ownership cannot be proven; do not overwrite.
        if not backup:
            return {"statusline": "ownership_unverified"}

    # A saved backup with a different live value proves that the user changed it.
    if backup and current != backup.get("installed_value"):
        try:
            _record_preference("user_selected")
        except OSError:
            pass
        return {"statusline": "user_selected"}

    try:
        return _enable_locked()
    except (OSError, RuntimeError):
        return {"statusline": "unchanged"}


def restore():
    """Restore the exact footer saved before ChatData took ownership."""
    with _mutation_lock():
        return _restore_locked()


def _restore_locked():
    settings_path, settings, snapshot = _safe_settings()
    if settings is None:
        raise RuntimeError("Claude settings must be a JSON object smaller than 64 KiB.")
    backup = _backup()
    if not backup:
        _ensure_private_root()
        _record_preference("restored")
        return {"statusline": "not_managed", "restored": False}
    if settings.get("statusLine") != backup.get("installed_value"):
        _record_preference("user_selected")
        return {"statusline": "user_selected", "restored": False}
    if backup["had_status_line"]:
        settings["statusLine"] = backup.get("value")
    else:
        settings.pop("statusLine", None)
    if not _write_settings_if_unchanged(settings_path, settings, snapshot):
        raise RuntimeError("Claude settings changed while ChatData was restoring the footer; retry once.")
    _record_preference("restored")
    return {"statusline": "restored", "restored": True, "path": str(settings_path)}


def status():
    settings_path, settings, _snapshot = _safe_settings()
    preference = _preference()
    backup = _backup()
    return {
        "statusline": preference.get("state") if preference else "not_configured",
        "path": str(settings_path),
        "settings_readable": settings is not None,
        "restore_available": bool(backup),
        "chatdata_active": bool(settings is not None and backup
                                and settings.get("statusLine") == backup.get("installed_value")),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("session-start", "enable", "restore", "status"))
    args = parser.parse_args()
    try:
        result = {"session-start": session_start, "enable": enable,
                  "restore": restore, "status": status}[args.command]()
        if args.command == "session-start":
            print("{}")
        else:
            print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, RuntimeError, ValueError) as error:
        if args.command == "session-start":
            print("{}")
            return 0
        print(json.dumps({"ok": False, "error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
