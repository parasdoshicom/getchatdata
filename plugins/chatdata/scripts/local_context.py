#!/usr/bin/env python3
"""Build and verify a private, local semantic context for one project."""

import argparse
import hashlib
import html
import importlib.util
import json
import os
import stat
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


MAX_READ_BYTES = 20 * 1024 * 1024
CONTEXT_DIR = "chatdata-context"
SEMANTIC_VERSION = "0.2.0.dev0"
TRUST_FIELDS = ("definition", "unit", "population", "timezone", "window", "exclusions", "null_policy", "grain")


class ContextRefused(ValueError):
    """A requested local operation was unsafe or would overwrite state."""


def _load_sibling(name):
    path = Path(__file__).with_name(name + ".py")
    spec = importlib.util.spec_from_file_location("chatdata_" + name, path)
    if not spec or not spec.loader:
        raise ContextRefused("ChatData is missing " + name + ".py. Reinstall the plugin.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _root(raw):
    inventory = _load_sibling("local_inventory")
    try:
        return inventory._validated_root(raw)
    except (inventory.RootRefused, ValueError) as error:
        raise ContextRefused(str(error)) from None


def _canonical_sha256(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _has_expression(item):
    expression = item.get("expression") if isinstance(item, dict) else None
    dialects = expression.get("dialects") if isinstance(expression, dict) else None
    return isinstance(dialects, list) and any(
        isinstance(value, dict) and isinstance(value.get("expression"), str) and value["expression"].strip()
        for value in dialects
    )


def _relative_path(raw, label):
    if not isinstance(raw, str) or not raw.strip():
        raise ContextRefused(label + " must be a nonempty project-relative path.")
    path = Path(raw)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ContextRefused(label + " must stay inside the selected project and cannot use '.' or '..'.")
    if "://" in raw:
        raise ContextRefused(label + " must be a local file. Remote sources are not accepted as local proof.")
    return path


def _safe_file(root, raw_path, label):
    relative = _relative_path(raw_path, label)
    candidate = root / relative
    current = root
    for part in relative.parts:
        current = current / part
        try:
            info = current.lstat()
        except OSError as error:
            raise ContextRefused(label + " is unavailable: " + raw_path + " (" + type(error).__name__ + ")") from None
        if stat.S_ISLNK(info.st_mode):
            raise ContextRefused(label + " cannot be a symlink or pass through one: " + raw_path)
    if not stat.S_ISREG(info.st_mode):
        raise ContextRefused(label + " must be a regular file: " + raw_path)
    if info.st_size > MAX_READ_BYTES:
        raise ContextRefused(label + " exceeds the 20 MB verification limit: " + raw_path)
    return candidate, info


def _read_bytes(root, raw_path, label):
    path, before = _safe_file(root, raw_path, label)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise ContextRefused(label + " stopped being a regular file: " + raw_path)
        signature = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)
        if signature(opened) != signature(before):
            raise ContextRefused(label + " changed while it was being opened: " + raw_path)
        chunks, total = [], 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, MAX_READ_BYTES + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_READ_BYTES:
                raise ContextRefused(label + " exceeds the 20 MB verification limit: " + raw_path)
            chunks.append(chunk)
        after = os.fstat(descriptor)
        if signature(after) != signature(opened):
            raise ContextRefused(label + " changed while it was being verified: " + raw_path)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _read_json(root, relative):
    def unique_object(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ContextRefused(relative + " contains duplicate key " + repr(key) + ".")
            value[key] = item
        return value

    def reject_constant(value):
        raise ContextRefused(relative + " contains non-finite number " + value + ".")

    try:
        return json.loads(
            _read_bytes(root, relative, relative).decode("utf-8"),
            object_pairs_hook=unique_object,
            parse_constant=reject_constant,
        )
    except UnicodeDecodeError:
        raise ContextRefused(relative + " must be UTF-8 JSON.") from None
    except json.JSONDecodeError as error:
        raise ContextRefused(relative + " is not valid JSON: " + error.msg) from None
    except RecursionError:
        raise ContextRefused(relative + " is nested too deeply to verify safely.") from None


def _write_new(path, content):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        os.write(descriptor, content.encode("utf-8"))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _json_text(value):
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def _readme(report):
    selected = report["coverage"]["selected_files"]
    complete = report["coverage"]["complete"]
    gap = "No inventory coverage gaps were reported." if complete else (
        "Inventory coverage is incomplete. Do not treat missing files as absent; review inventory.json coverage errors and limits."
    )
    return f"""# ChatData local context

This private folder indexes analysis work already on this machine. ChatData did not read, move, upload, or approve any inventoried source file.

## Inventory

- Window: {report['window']['days']} days by filesystem modified time
- Candidate files: {selected}
- Coverage complete: {str(complete).lower()}
- Gap: {gap}

## Exact next steps

1. Describe datasets and metrics in `semantic-model.json` using the bundled Apache Ossie {SEMANTIC_VERSION} schema.
2. Add the chosen metric to `trust.json`. Record its definition, unit, population, timezone, window, exclusions, null policy, grain, local source hashes, and passed check evidence.
3. Set `reviewed_by_user` only after you reviewed those records. Use `local_context.py semantic-hash --root <project>` for `semantic_sha256` and `local_context.py fingerprint --root <project> --path <relative-file>` for source and evidence hashes.
4. Run `local_context.py check --root <project> --metric <exact-name>`. ChatData must report `ready_for_analysis` before presenting a trusted metric answer. Exploratory or synthetic work should still be labeled as such.

`ready_for_analysis` only means the recorded local prerequisites still match. It does not prove the metric is correct or the resulting analysis is true.
"""


def _index(report):
    rows = "".join(
        "<tr><td>" + html.escape(item["path"]) + "</td><td>" + html.escape(item["kind"]) +
        "</td><td>" + html.escape(item["modified_at"]) + "</td></tr>"
        for item in report["inventory"]
    ) or '<tr><td colspan="3">No recent supported analysis files found.</td></tr>'
    coverage = "Complete metadata scan" if report["coverage"]["complete"] else "INCOMPLETE — inspect inventory.json before relying on absence"
    skipped = sum(value for value in report["coverage"].get("skipped", {}).values() if isinstance(value, int))
    errors = len(report["coverage"].get("errors", []))
    return """<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ChatData local context</title>
<style>*{box-sizing:border-box}body{font:16px/1.55 system-ui;max-width:960px;margin:0 auto;padding:clamp(1rem,5vw,3.5rem);color:#482f41;background:#fcfaf7}h1{font-size:clamp(2rem,8vw,4.5rem);line-height:1;margin:.2em 0}.card{border:1px solid #d8cec8;border-radius:18px;padding:clamp(1rem,3vw,2rem);background:#fff}.accent{color:#84956c}.table{overflow-x:auto}.scroll{display:none;color:#6d5a68;font-size:.85rem}table{border-collapse:collapse;width:100%;min-width:620px}th,td{text-align:left;padding:.65rem;border-bottom:1px solid #ded7d2;overflow-wrap:anywhere}code{background:#f0ede8;padding:.15rem .3rem}@media(max-width:620px){.scroll{display:block}}</style>
<main><p class="accent">LOCAL · PRIVATE · YOUR CONTEXT</p><h1>Know what your AI can trust.</h1><div class="card"><p>This is a """ + html.escape(str(report["window"]["days"])) + """-day filesystem modification inventory, not a usage history. No source contents were read or uploaded.</p>
<p><strong>Coverage:</strong> """ + html.escape(coverage) + "</p><p><strong>Skipped entries:</strong> " + str(skipped) + " · <strong>scan errors:</strong> " + str(errors) + """</p><p>This report does not certify metric readiness. Define and review a metric, then run the exact metric check. Missing local proof stops a trusted metric answer.</p>
<p class="scroll">Scroll to see file details →</p><div class="table"><table><thead><tr><th>Local path</th><th>Kind</th><th>Modified</th></tr></thead><tbody>""" + rows + "</tbody></table></div></div></main>"


def initialize(raw_root, days=30):
    root = _root(raw_root)
    destination = root / CONTEXT_DIR
    try:
        destination.lstat()
    except FileNotFoundError:
        pass
    else:
        raise ContextRefused(CONTEXT_DIR + " already exists. Existing context was preserved; choose check or edit it directly.")
    inventory = _load_sibling("local_inventory").scan(root, days=days)
    semantic = {"version": SEMANTIC_VERSION, "semantic_model": []}
    trust = {"schema_version": 1, "metrics": {}}
    temporary = Path(tempfile.mkdtemp(prefix=".chatdata-context-", dir=root))
    files = {
        ".gitignore": "*\n",
        "inventory.json": _json_text(inventory),
        "semantic-model.json": _json_text(semantic),
        "trust.json": _json_text(trust),
        "README.md": _readme(inventory),
        "index.html": _index(inventory),
    }
    try:
        for name, content in files.items():
            _write_new(temporary / name, content)
        try:
            destination.lstat()
        except FileNotFoundError:
            os.rename(temporary, destination)
        else:
            raise ContextRefused(CONTEXT_DIR + " appeared during setup. Nothing was overwritten.")
    except Exception:
        for name in files:
            try:
                (temporary / name).unlink()
            except FileNotFoundError:
                pass
        try:
            temporary.rmdir()
        except FileNotFoundError:
            pass
        raise
    return {
        "status": "initialized" if inventory["coverage"]["complete"] else "initialized_with_inventory_gap",
        "context": str(destination),
        "inventory_files": inventory["coverage"]["selected_files"],
        "coverage_complete": inventory["coverage"]["complete"],
        "next_step": "Complete semantic-model.json and trust.json, then run check for one exact metric.",
    }


def _replace_generated(root, relative, content):
    path, before = _safe_file(root, relative, relative)
    temporary = path.parent / ("." + path.name + ".new-" + str(os.getpid()))
    try:
        _write_new(temporary, content)
        current = path.lstat()
        signature = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)
        if stat.S_ISLNK(current.st_mode) or not stat.S_ISREG(current.st_mode) or signature(current) != signature(before):
            raise ContextRefused(relative + " changed during refresh. Nothing was replaced.")
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def refresh(raw_root, days=30):
    root = _root(raw_root)
    context = root / CONTEXT_DIR
    try:
        info = context.lstat()
    except OSError as error:
        raise ContextRefused("Run init first; " + CONTEXT_DIR + " is unavailable (" + type(error).__name__ + ").") from None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise ContextRefused(CONTEXT_DIR + " must be the real local directory created by ChatData.")
    # Validate both user-owned records before changing generated reports.
    _safe_file(root, CONTEXT_DIR + "/semantic-model.json", "semantic model")
    _safe_file(root, CONTEXT_DIR + "/trust.json", "trust record")
    inventory = _load_sibling("local_inventory").scan(root, days=days)
    _replace_generated(root, CONTEXT_DIR + "/inventory.json", _json_text(inventory))
    _replace_generated(root, CONTEXT_DIR + "/index.html", _index(inventory))
    return {
        "status": "refreshed" if inventory["coverage"]["complete"] else "refreshed_with_inventory_gap",
        "context": str(context),
        "inventory_files": inventory["coverage"]["selected_files"],
        "coverage_complete": inventory["coverage"]["complete"],
        "preserved": ["semantic-model.json", "trust.json", "README.md"],
        "next_step": "Run check again for the exact metric before presenting a trusted metric answer.",
    }


def _iso(raw, field, gaps):
    try:
        if not isinstance(raw, str) or len(raw) > 100:
            raise ValueError
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if value.tzinfo is None:
            raise ValueError
        return value.astimezone(timezone.utc)
    except (AttributeError, ValueError):
        gaps.append({"code": "invalid_time", "detail": field + " must be an ISO-8601 timestamp with a timezone."})
        return None


def _hash_file(root, item, path_field, hash_field, label, gaps):
    if not isinstance(item, dict):
        gaps.append({"code": "invalid_" + label, "detail": label + " entries must be objects."})
        return
    try:
        content = _read_bytes(root, item.get(path_field), label)
    except ContextRefused as error:
        code = "missing_local_proof" if label in ("source", "evidence") else "unsafe_path"
        gaps.append({"code": code, "detail": str(error)})
        return
    actual = hashlib.sha256(content).hexdigest()
    if not content:
        gaps.append({"code": "empty_" + label, "detail": item.get(path_field, "<missing>") + " is empty and cannot establish local proof."})
    if item.get(hash_field) != actual:
        gaps.append({"code": label + "_changed", "detail": item.get(path_field, "<missing>") + " does not match its recorded SHA-256."})


def check(raw_root, metric, now=None):
    root = _root(raw_root)
    gaps = []
    if not isinstance(metric, str) or not metric.strip():
        return _blocked(metric, [{"code": "invalid_metric", "detail": "--metric must be a nonempty exact metric name."}])
    try:
        model = _read_json(root, CONTEXT_DIR + "/semantic-model.json")
        trust = _read_json(root, CONTEXT_DIR + "/trust.json")
        inventory = _read_json(root, CONTEXT_DIR + "/inventory.json")
    except ContextRefused as error:
        return _blocked(metric, [{"code": "missing_local_context", "detail": str(error)}])
    validator = _load_sibling("semantic_schema")
    semantic_errors = validator.validate(model)
    if semantic_errors:
        return _blocked(metric, [{"code": "invalid_semantic_model", "detail": error} for error in semantic_errors])
    if not isinstance(inventory, dict) or not isinstance(inventory.get("coverage"), dict):
        gaps.append({"code": "invalid_inventory", "detail": "inventory.json is missing its coverage record."})
    elif inventory["coverage"].get("complete") is not True:
        gaps.append({"code": "incomplete_inventory", "detail": "The local inventory was incomplete. Resolve its reported errors or limits before analysis."})
    matches = []
    if isinstance(model, dict) and isinstance(model.get("semantic_model"), list):
        for namespace in model["semantic_model"]:
            if isinstance(namespace, dict) and isinstance(namespace.get("metrics"), list):
                for item in namespace["metrics"]:
                    if isinstance(item, dict) and item.get("name") == metric:
                        matches.append((namespace, item))
    if len(matches) != 1:
        gaps.append({"code": "metric_not_uniquely_modeled", "detail": f"Expected exactly one Ossie metric named {metric!r}; found {len(matches)}."})
        dataset_names = set()
    else:
        namespace, modeled_metric = matches[0]
        if not isinstance(namespace.get("name"), str) or not namespace["name"].strip():
            gaps.append({"code": "placeholder_semantic_model", "detail": "The containing Ossie semantic model needs a nonempty name."})
        if not _has_expression(modeled_metric):
            gaps.append({"code": "placeholder_metric_expression", "detail": "The modeled metric needs at least one nonempty dialect expression."})
        datasets = namespace.get("datasets") if isinstance(namespace.get("datasets"), list) else []
        dataset_names = set()
        for index, item in enumerate(datasets):
            name = item.get("name") if isinstance(item, dict) else None
            source = item.get("source") if isinstance(item, dict) else None
            if not isinstance(name, str) or not name.strip() or not isinstance(source, str) or not source.strip():
                gaps.append({"code": "placeholder_dataset", "detail": f"datasets[{index}] needs nonempty name and source strings."})
            elif name in dataset_names:
                gaps.append({"code": "duplicate_dataset", "detail": "Dataset names must be unique inside the metric's semantic model: " + name})
            else:
                dataset_names.add(name)
            fields = item.get("fields", []) if isinstance(item, dict) else []
            seen_fields = set()
            if isinstance(fields, list):
                for field_index, field in enumerate(fields):
                    field_name = field.get("name") if isinstance(field, dict) else None
                    if not isinstance(field_name, str) or not field_name.strip():
                        gaps.append({"code": "placeholder_field", "detail": f"datasets[{index}].fields[{field_index}] needs a nonempty name."})
                    elif field_name in seen_fields:
                        gaps.append({"code": "duplicate_field", "detail": f"Dataset {name!r} has duplicate field {field_name!r}."})
                    else:
                        seen_fields.add(field_name)
                    if isinstance(field, dict) and not _has_expression(field):
                        gaps.append({"code": "placeholder_field_expression", "detail": f"datasets[{index}].fields[{field_index}] needs a nonempty dialect expression."})
        metric_names = set()
        for item in namespace.get("metrics", []):
            name = item.get("name") if isinstance(item, dict) else None
            if isinstance(name, str) and name in metric_names:
                gaps.append({"code": "duplicate_metric", "detail": "Metric names must be unique inside a semantic model: " + name})
            elif isinstance(name, str):
                metric_names.add(name)
        relationship_names = set()
        relationships = namespace.get("relationships", [])
        if isinstance(relationships, list):
            for index, relationship in enumerate(relationships):
                name = relationship.get("name") if isinstance(relationship, dict) else None
                if not isinstance(name, str) or not name.strip():
                    gaps.append({"code": "placeholder_relationship", "detail": f"relationships[{index}] needs a nonempty name."})
                elif name in relationship_names:
                    gaps.append({"code": "duplicate_relationship", "detail": "Relationship names must be unique: " + name})
                else:
                    relationship_names.add(name)
                if isinstance(relationship, dict):
                    if relationship.get("from") not in dataset_names or relationship.get("to") not in dataset_names:
                        gaps.append({"code": "unknown_relationship_dataset", "detail": f"relationships[{index}] must reference known from/to datasets."})
                    from_columns, to_columns = relationship.get("from_columns"), relationship.get("to_columns")
                    if isinstance(from_columns, list) and isinstance(to_columns, list) and len(from_columns) != len(to_columns):
                        gaps.append({"code": "relationship_column_mismatch", "detail": f"relationships[{index}] must pair equal numbers of from_columns and to_columns."})
                    if isinstance(from_columns, list) and isinstance(to_columns, list) and not all(
                        isinstance(column, str) and column.strip() for column in from_columns + to_columns
                    ):
                        gaps.append({"code": "placeholder_relationship_column", "detail": f"relationships[{index}] columns must be nonempty strings."})
    semantic_hash = _canonical_sha256(model)
    if not isinstance(trust, dict) or type(trust.get("schema_version")) is not int or trust.get("schema_version") != 1:
        gaps.append({"code": "invalid_trust_schema", "detail": "trust.json schema_version must be 1."})
    metrics = trust.get("metrics") if isinstance(trust, dict) else None
    record = metrics.get(metric) if isinstance(metrics, dict) else None
    if not isinstance(record, dict):
        gaps.append({"code": "missing_trust_record", "detail": "Add this exact metric under trust.json metrics."})
        return _blocked(metric, gaps)
    for field in TRUST_FIELDS:
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            gaps.append({"code": "missing_" + field, "detail": "trust.json needs a nonempty " + field + "."})
    if record.get("reviewed_by_user") is not True:
        gaps.append({"code": "not_reviewed", "detail": "reviewed_by_user must be true after a person reviews this metric."})
    instant = datetime.now(timezone.utc) if now is None else now.astimezone(timezone.utc)
    reviewed = _iso(record.get("reviewed_at"), "reviewed_at", gaps)
    if reviewed and reviewed >= instant:
        gaps.append({"code": "future_review", "detail": "reviewed_at must be in the past."})
    if record.get("semantic_sha256") != semantic_hash:
        gaps.append({"code": "semantic_model_changed", "detail": "semantic_sha256 does not match the current canonical semantic model."})
    sources = record.get("sources")
    if not isinstance(sources, list) or not sources:
        gaps.append({"code": "missing_local_proof", "detail": "At least one hashed local source is required."})
    else:
        for index, source in enumerate(sources):
            _hash_file(root, source, "path", "sha256", "source", gaps)
            if isinstance(source, dict):
                source_dataset = source.get("dataset")
                if not isinstance(source_dataset, str) or source_dataset not in dataset_names:
                    gaps.append({"code": "unmapped_local_source", "detail": f"sources[{index}].dataset must name a dataset in the metric's Ossie semantic model."})
                checked = _iso(source.get("checked_at"), f"sources[{index}].checked_at", gaps)
                valid = _iso(source.get("valid_until"), f"sources[{index}].valid_until", gaps)
                if checked and checked >= instant:
                    gaps.append({"code": "future_source_check", "detail": f"sources[{index}].checked_at must be in the past."})
                if valid and valid <= instant:
                    gaps.append({"code": "stale_source", "detail": f"sources[{index}] is no longer valid."})
    checks = record.get("checks")
    if not isinstance(checks, list) or not checks:
        gaps.append({"code": "missing_local_proof", "detail": "At least one passed check with hashed local evidence is required."})
    else:
        for index, item in enumerate(checks):
            if not isinstance(item, dict) or item.get("status") != "passed":
                gaps.append({"code": "check_not_passed", "detail": f"checks[{index}] must have status 'passed'."})
            _hash_file(root, item, "evidence_path", "evidence_sha256", "evidence", gaps)
    if record.get("unresolved_conflicts") != []:
        gaps.append({"code": "unresolved_conflicts", "detail": "unresolved_conflicts must be an empty list."})
    if not isinstance(record.get("caveats"), list):
        gaps.append({"code": "missing_caveats", "detail": "caveats must be a list, even when empty."})
    if gaps:
        return _blocked(metric, gaps)
    return {
        "status": "ready_for_analysis",
        "metric": metric,
        "semantic_sha256": semantic_hash,
        "meaning": "Recorded local prerequisites matched. This does not prove mathematical truth or enforce behavior outside ChatData.",
    }


def _blocked(metric, gaps):
    return {
        "status": "blocked",
        "metric": metric,
        "gaps": gaps,
        "next_step": "Resolve every listed local gap and run this exact check again. Do not analyze or invent missing context.",
    }


def fingerprint(raw_root, path):
    root = _root(raw_root)
    content = _read_bytes(root, path, "file")
    return {"status": "fingerprinted", "path": path, "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}


def semantic_hash(raw_root):
    root = _root(raw_root)
    model = _read_json(root, CONTEXT_DIR + "/semantic-model.json")
    return {"status": "fingerprinted", "path": CONTEXT_DIR + "/semantic-model.json", "semantic_sha256": _canonical_sha256(model), "method": "canonical JSON: sorted keys, compact separators, UTF-8"}


def main():
    parser = argparse.ArgumentParser(description="Initialize and verify private ChatData context on one local project.")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--root", required=True)
    init.add_argument("--days", type=int, default=30)
    init.add_argument("--days30", action="store_const", const=30, dest="days")
    refresh_parser = commands.add_parser("refresh")
    refresh_parser.add_argument("--root", required=True)
    refresh_parser.add_argument("--days", type=int, default=30)
    refresh_parser.add_argument("--days30", action="store_const", const=30, dest="days")
    verify = commands.add_parser("check")
    verify.add_argument("--root", required=True)
    verify.add_argument("--metric", required=True)
    hash_parser = commands.add_parser("fingerprint")
    hash_parser.add_argument("--root", required=True)
    hash_parser.add_argument("--path", required=True)
    semantic_parser = commands.add_parser("semantic-hash")
    semantic_parser.add_argument("--root", required=True)
    args = parser.parse_args()
    try:
        if args.command == "init":
            result = initialize(args.root, args.days)
        elif args.command == "refresh":
            result = refresh(args.root, args.days)
        elif args.command == "check":
            result = check(args.root, args.metric)
        elif args.command == "fingerprint":
            result = fingerprint(args.root, args.path)
        else:
            result = semantic_hash(args.root)
        print(json.dumps(result, indent=2))
        return 2 if result["status"] == "blocked" else (3 if result["status"] in ("initialized_with_inventory_gap", "refreshed_with_inventory_gap") else 0)
    except (ContextRefused, ValueError, OSError) as error:
        print(json.dumps({"status": "refused", "error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
