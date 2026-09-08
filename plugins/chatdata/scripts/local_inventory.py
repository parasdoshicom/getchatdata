#!/usr/bin/env python3
"""Create a bounded, metadata-only inventory of recent analysis files."""

import argparse
import json
import os
import re
import stat
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_DAYS = 30
MAX_FILES = 5000
MAX_DIRECTORIES = 1000

KINDS = {
    ".sql": "sql",
    ".ipynb": "notebook",
    ".py": "python",
    ".r": "r",
    ".csv": "csv",
    ".parquet": "parquet",
    ".md": "markdown",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
}

EXCLUDED_DIRECTORIES = {
    "chatdata-context",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "venv",
}

SENSITIVE_NAME_PARTS = {
    "auth",
    "authorization",
    "config",
    "credential",
    "credentials",
    "password",
    "secret",
    "secrets",
    "token",
    "tokens",
}


class RootRefused(ValueError):
    """The selected root is too broad or contains protected user state."""


def _iso_utc(timestamp):
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _inside(path, parent):
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _validated_root(raw_root):
    if raw_root is None or not str(raw_root).strip():
        raise RootRefused("Choose an explicit project directory with --root.")
    supplied = Path(raw_root).expanduser()
    try:
        root_lstat = supplied.lstat()
    except OSError as error:
        raise RootRefused("The selected root cannot be inspected: " + str(error)) from None
    if stat.S_ISLNK(root_lstat.st_mode):
        raise RootRefused("The selected root is a symlink. Choose the real project directory instead.")
    if not stat.S_ISDIR(root_lstat.st_mode):
        raise RootRefused("The selected root must be a directory.")

    root = supplied.resolve()
    home = Path.home().resolve()
    filesystem_root = Path(root.anchor).resolve()
    if root == filesystem_root:
        raise RootRefused("Scanning a filesystem root is not allowed. Choose one project directory.")
    if root == home:
        raise RootRefused("Scanning your home directory is not allowed. Choose one project directory.")
    for protected in (home / ".claude", home / ".codex"):
        if _inside(root, protected):
            raise RootRefused("Claude or Codex user state cannot be inventoried. Choose a project directory.")
    return root


def _sensitive_name(name):
    if name.startswith("."):
        return True
    parts = {part for part in re.split(r"[^a-z0-9]+", name.lower()) if part}
    return bool(parts & SENSITIVE_NAME_PARTS)


def _empty_skips():
    return {
        "excluded_directories": 0,
        "symlinks": 0,
        "sensitive_names": 0,
        "unsupported_extensions": 0,
        "older_than_window": 0,
        "non_regular_files": 0,
    }


def scan(root, days=DEFAULT_DAYS, now=None, max_files=MAX_FILES, max_directories=MAX_DIRECTORIES):
    """Return recent regular-file metadata without reading file contents or writing state."""
    if isinstance(days, bool) or not isinstance(days, int) or days < 1:
        raise ValueError("days must be a positive integer")
    if isinstance(max_files, bool) or not isinstance(max_files, int) or max_files < 1:
        raise ValueError("max_files must be a positive integer")
    if isinstance(max_directories, bool) or not isinstance(max_directories, int) or max_directories < 1:
        raise ValueError("max_directories must be a positive integer")

    selected_root = _validated_root(root)
    scan_time = time.time() if now is None else float(now)
    cutoff = scan_time - (days * 24 * 60 * 60)
    inventory = []
    skipped = _empty_skips()
    errors = []
    truncated_reasons = []
    directories_scanned = 0
    regular_files_seen = 0
    pending = [selected_root]

    while pending:
        if directories_scanned >= max_directories:
            truncated_reasons.append("directory_limit")
            break
        directory = pending.pop()
        directories_scanned += 1
        try:
            directory_metadata = directory.lstat()
            if stat.S_ISLNK(directory_metadata.st_mode):
                skipped["symlinks"] += 1
                continue
            if not stat.S_ISDIR(directory_metadata.st_mode):
                skipped["non_regular_files"] += 1
                continue
            with os.scandir(directory) as iterator:
                entries = list(iterator)
        except OSError as error:
            errors.append({
                "path": os.path.relpath(str(directory), str(selected_root)),
                "error": type(error).__name__,
            })
            continue

        # Reversed insertion keeps traversal and output stable without relying on filesystem order.
        for entry in sorted(entries, key=lambda item: item.name.casefold(), reverse=True):
            try:
                if entry.is_symlink():
                    skipped["symlinks"] += 1
                    continue
                if entry.is_dir(follow_symlinks=False):
                    if entry.name.startswith(".") or entry.name in EXCLUDED_DIRECTORIES:
                        skipped["excluded_directories"] += 1
                    else:
                        pending.append(Path(entry.path))
                    continue
                if not entry.is_file(follow_symlinks=False):
                    skipped["non_regular_files"] += 1
                    continue

                regular_files_seen += 1
                if regular_files_seen > max_files:
                    truncated_reasons.append("file_limit")
                    pending.clear()
                    break
                if _sensitive_name(entry.name):
                    skipped["sensitive_names"] += 1
                    continue
                suffix = Path(entry.name).suffix.lower()
                if suffix not in KINDS:
                    skipped["unsupported_extensions"] += 1
                    continue
                metadata = entry.stat(follow_symlinks=False)
                if not stat.S_ISREG(metadata.st_mode):
                    skipped["non_regular_files"] += 1
                    continue
                if metadata.st_mtime < cutoff:
                    skipped["older_than_window"] += 1
                    continue
                inventory.append({
                    "path": os.path.relpath(entry.path, str(selected_root)),
                    "kind": KINDS[suffix],
                    "size_bytes": metadata.st_size,
                    "modified_at": _iso_utc(metadata.st_mtime),
                })
            except OSError as error:
                errors.append({
                    "path": os.path.relpath(entry.path, str(selected_root)),
                    "error": type(error).__name__,
                })

    inventory.sort(key=lambda item: (-datetime.fromisoformat(item["modified_at"].replace("Z", "+00:00")).timestamp(), item["path"]))
    complete = not errors and not truncated_reasons
    return {
        "status": "complete" if complete else "incomplete",
        "root": str(selected_root),
        "window": {
            "days": days,
            "field": "filesystem_modified_time",
            "meaning": "Files modified during this window; this is not proof they were used or analyzed.",
            "scanned_at": _iso_utc(scan_time),
            "modified_since": _iso_utc(cutoff),
        },
        "inventory": inventory,
        "coverage": {
            "complete": complete,
            "directories_scanned": directories_scanned,
            "regular_files_seen": regular_files_seen,
            "selected_files": len(inventory),
            "limits": {"files": max_files, "directories": max_directories},
            "skipped": skipped,
            "errors": errors,
            "truncated": bool(truncated_reasons),
            "truncated_reasons": sorted(set(truncated_reasons)),
        },
        "interpretation": "Metadata inventory only. No file was read, and no metric definition or analysis was approved.",
        "privacy": "Local output only. This command makes no network requests and sends no telemetry.",
    }


def main():
    parser = argparse.ArgumentParser(description="Inventory recently modified analysis files using local metadata only.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan_parser = subparsers.add_parser("scan")
    scan_parser.add_argument("--root", required=True, help="Explicit project directory to inspect")
    scan_parser.add_argument("--days", type=int, default=DEFAULT_DAYS)
    args = parser.parse_args()
    try:
        result = scan(args.root, days=args.days)
        print(json.dumps(result, indent=2))
        return 0 if result["coverage"]["complete"] else 3
    except (RootRefused, ValueError) as error:
        print(json.dumps({
            "status": "refused",
            "error": str(error),
            "next_step": "Choose one explicit project directory. No files were scanned.",
        }), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
