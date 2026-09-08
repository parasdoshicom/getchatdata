#!/usr/bin/env python3
"""Offline validation for ChatData's pinned Apache Ossie JSON profile.

This module intentionally implements only the JSON Schema vocabulary used by
the bundled Ossie schema. It fails closed if a future schema introduces a
keyword or reference form that this small validator does not understand.
"""

from functools import lru_cache
import json
import os
from pathlib import Path
import stat
import sys


MAX_DOCUMENT_BYTES = 2 * 1024 * 1024
MAX_DEPTH = 64
MAX_NODES = 100_000
MAX_ERRORS = 200

_SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "references"
    / "ossie"
    / "ossie-schema.json"
)
_SUPPORTED_SCHEMA_KEYS = {
    "$schema",
    "$id",
    "$defs",
    "$ref",
    "title",
    "description",
    "examples",
    "type",
    "properties",
    "required",
    "additionalProperties",
    "items",
    "minItems",
    "enum",
    "const",
    "oneOf",
}
_JSON_TYPES = {"object", "array", "string", "number", "integer", "boolean", "null"}


class DuplicateKeyError(ValueError):
    """Raised when authored JSON contains the same object key twice."""


class UnsupportedSchemaError(ValueError):
    """Raised when the bundled schema exceeds this validator's vocabulary."""


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_nonfinite_number(value):
    raise ValueError(f"non-finite JSON number {value!r} is not allowed")


def _read_regular_file(path: Path, limit: int) -> bytes:
    try:
        if path.is_symlink():
            raise ValueError(f"refusing symlink: {path}")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        descriptor = os.open(str(path), flags)
    except FileNotFoundError as error:
        raise ValueError(f"file not found: {path}") from error
    except OSError as error:
        raise ValueError(f"cannot read file: {path}") from error

    try:
        details = os.fstat(descriptor)
        if not stat.S_ISREG(details.st_mode):
            raise ValueError(f"not a regular file: {path}")
        if details.st_size > limit:
            raise ValueError(f"file exceeds {limit} bytes: {path}")
        chunks = []
        remaining = limit + 1
        while remaining:
            chunk = os.read(descriptor, remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        if len(raw) > limit:
            raise ValueError(f"file exceeds {limit} bytes: {path}")
        return raw
    except OSError as error:
        raise ValueError(f"cannot read file: {path}") from error
    finally:
        os.close(descriptor)


def load_json(path, *, max_bytes=MAX_DOCUMENT_BYTES):
    """Load a bounded regular JSON file and reject duplicate object keys."""
    raw = _read_regular_file(Path(path), max_bytes)
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonfinite_number,
        )
    except UnicodeError as error:
        raise ValueError(f"file is not UTF-8 JSON: {path}") from error
    except json.JSONDecodeError as error:
        raise ValueError(
            f"invalid JSON at line {error.lineno}, column {error.colno}: {error.msg}"
        ) from error


def _schema_error(path, message):
    raise UnsupportedSchemaError(f"{path}: {message}")


def _audit_schema(node, path="$", depth=0, nodes=None):
    if nodes is None:
        nodes = [0]
    nodes[0] += 1
    if nodes[0] > MAX_NODES:
        _schema_error(path, f"schema exceeds {MAX_NODES} nodes")
    if depth > MAX_DEPTH:
        _schema_error(path, f"schema exceeds depth {MAX_DEPTH}")
    if not isinstance(node, dict):
        _schema_error(path, "schema node must be an object")

    unknown = sorted(set(node) - _SUPPORTED_SCHEMA_KEYS)
    if unknown:
        _schema_error(path, f"unsupported schema keyword {unknown[0]!r}")

    schema_type = node.get("type")
    if schema_type is not None and schema_type not in _JSON_TYPES:
        _schema_error(path, f"unsupported type {schema_type!r}")
    reference = node.get("$ref")
    if reference is not None and (
        not isinstance(reference, str) or not reference.startswith("#/$defs/")
    ):
        _schema_error(path, f"unsupported reference {reference!r}")
    properties = node.get("properties")
    if properties is not None:
        if not isinstance(properties, dict) or not all(isinstance(key, str) for key in properties):
            _schema_error(path, "properties must be an object with string keys")
        for key, child in properties.items():
            _audit_schema(child, f"{path}.properties[{key!r}]", depth + 1, nodes)
    definitions = node.get("$defs")
    if definitions is not None:
        if not isinstance(definitions, dict) or not all(isinstance(key, str) for key in definitions):
            _schema_error(path, "$defs must be an object with string keys")
        for key, child in definitions.items():
            _audit_schema(child, f"{path}.$defs[{key!r}]", depth + 1, nodes)
    items = node.get("items")
    if items is not None:
        _audit_schema(items, f"{path}.items", depth + 1, nodes)
    branches = node.get("oneOf")
    if branches is not None:
        if not isinstance(branches, list) or not branches:
            _schema_error(path, "oneOf must be a non-empty array")
        for index, child in enumerate(branches):
            _audit_schema(child, f"{path}.oneOf[{index}]", depth + 1, nodes)

    required = node.get("required")
    if required is not None and (
        not isinstance(required, list)
        or not all(isinstance(key, str) for key in required)
        or len(required) != len(set(required))
    ):
        _schema_error(path, "required must contain unique string keys")
    additional = node.get("additionalProperties")
    if additional is not None and not isinstance(additional, bool):
        _schema_error(path, "only boolean additionalProperties is supported")
    minimum = node.get("minItems")
    if minimum is not None and (
        isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 0
    ):
        _schema_error(path, "minItems must be a non-negative integer")
    if "enum" in node and not isinstance(node["enum"], list):
        _schema_error(path, "enum must be an array")


def _audit_references(node, root):
    reference = node.get("$ref")
    if reference is not None:
        _resolve_reference(root, reference)
    for child in node.get("properties", {}).values():
        _audit_references(child, root)
    for child in node.get("$defs", {}).values():
        _audit_references(child, root)
    if "items" in node:
        _audit_references(node["items"], root)
    for child in node.get("oneOf", []):
        _audit_references(child, root)


@lru_cache(maxsize=1)
def _bundled_schema():
    schema = load_json(_SCHEMA_PATH, max_bytes=MAX_DOCUMENT_BYTES)
    _audit_schema(schema)
    _audit_references(schema, schema)
    return schema


def _resolve_reference(root, reference):
    if not reference.startswith("#/$defs/"):
        raise UnsupportedSchemaError(f"unsupported reference {reference!r}")
    current = root
    for raw_part in reference[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or part not in current:
            raise UnsupportedSchemaError(f"unresolved reference {reference!r}")
        current = current[part]
    if not isinstance(current, dict):
        raise UnsupportedSchemaError(f"reference {reference!r} is not a schema object")
    return current


def _is_type(value, expected):
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "null":
        return value is None
    raise UnsupportedSchemaError(f"unsupported type {expected!r}")


def _same_json_value(left, right):
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    return left == right


def _append_error(errors, path, message):
    if len(errors) < MAX_ERRORS:
        errors.append(f"{path}: {message}")


def _validate_instance(value, schema, root, path, depth, state, errors):
    state["nodes"] += 1
    if state["nodes"] > MAX_NODES:
        _append_error(errors, path, f"document exceeds {MAX_NODES} nodes")
        return
    if depth > MAX_DEPTH:
        _append_error(errors, path, f"document exceeds depth {MAX_DEPTH}")
        return

    reference = schema.get("$ref")
    if reference is not None:
        target = _resolve_reference(root, reference)
        _validate_instance(value, target, root, path, depth + 1, state, errors)
        # Draft 2020-12 allows validation siblings next to $ref. The pinned
        # schema currently has none, but retaining them here prevents a future
        # supported-key change from being silently ignored.
        schema = {key: item for key, item in schema.items() if key != "$ref"}

    branches = schema.get("oneOf")
    if branches is not None:
        matched = 0
        for branch in branches:
            branch_errors = []
            branch_state = {"nodes": state["nodes"]}
            _validate_instance(value, branch, root, path, depth + 1, branch_state, branch_errors)
            state["nodes"] = max(state["nodes"], branch_state["nodes"])
            if not branch_errors:
                matched += 1
        if matched != 1:
            _append_error(errors, path, f"must match exactly one allowed shape; matched {matched}")
        return

    expected = schema.get("type")
    if expected is not None and not _is_type(value, expected):
        _append_error(errors, path, f"must be {expected}, got {type(value).__name__}")
        return
    if "const" in schema and not _same_json_value(value, schema["const"]):
        _append_error(errors, path, f"must equal {schema['const']!r}")
    if "enum" in schema and not any(_same_json_value(value, item) for item in schema["enum"]):
        _append_error(errors, path, f"must be one of {schema['enum']!r}")

    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                _append_error(errors, path, f"missing required property {key!r}")
        if schema.get("additionalProperties") is False:
            for key in sorted(set(value) - set(properties)):
                _append_error(errors, f"{path}.{key}", "additional property is not allowed")
        for key, child in properties.items():
            if key in value:
                _validate_instance(
                    value[key], child, root, f"{path}.{key}", depth + 1, state, errors
                )
    elif isinstance(value, list):
        minimum = schema.get("minItems")
        if minimum is not None and len(value) < minimum:
            _append_error(errors, path, f"must contain at least {minimum} item(s)")
        child = schema.get("items")
        if child is not None:
            for index, item in enumerate(value):
                _validate_instance(
                    item, child, root, f"{path}[{index}]", depth + 1, state, errors
                )


def validate(model):
    """Return structural errors for an Ossie JSON value; an empty list means valid.

    Structural validity is not evidence that a model contains an approved metric.
    In particular, the upstream schema permits an empty ``semantic_model`` array.
    """
    try:
        schema = _bundled_schema()
        errors = []
        _validate_instance(model, schema, schema, "$", 0, {"nodes": 0}, errors)
        if len(errors) >= MAX_ERRORS:
            errors.append(f"$: validation stopped after {MAX_ERRORS} errors")
        return errors
    except (UnsupportedSchemaError, ValueError) as error:
        return [f"$: bundled Ossie schema cannot be safely validated: {error}"]


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 1:
        print("Usage: semantic_schema.py <semantic-model.json>", file=sys.stderr)
        return 2
    try:
        model = load_json(arguments[0])
    except ValueError as error:
        print(json.dumps({"valid": False, "errors": [str(error)]}, indent=2))
        return 1
    errors = validate(model)
    print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
