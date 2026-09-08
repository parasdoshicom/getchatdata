#!/usr/bin/env python3
"""Run a bounded, read-only query against a local DuckDB database."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import time

_FORBIDDEN = re.compile(
    r"\b(attach|call|copy|create|delete|detach|drop|export|import|insert|install|load|pragma|set|update|alter|vacuum)\b",
    re.IGNORECASE,
)
_ALLOWED_START = re.compile(r"^\s*(select|with)\b", re.IGNORECASE)


def _safe_query(sql):
    if not isinstance(sql, str) or not sql.strip():
        raise ValueError("SQL file is empty")
    stripped = sql.strip()
    if stripped.endswith(";"):
        stripped = stripped[:-1].rstrip()
    if ";" in stripped:
        raise ValueError("Only one SQL statement is allowed")
    if not _ALLOWED_START.match(stripped):
        raise ValueError("Only read-only SELECT or WITH statements are allowed")
    match = _FORBIDDEN.search(stripped)
    if match:
        raise ValueError("Read-only query rejected because it contains: " + match.group(1).lower())
    return stripped


def query_database(database, sql_file, max_rows=1000):
    database = Path(database).expanduser().resolve()
    sql_file = Path(sql_file).expanduser().resolve()
    if not database.is_file():
        raise ValueError("DuckDB database must be an existing local file")
    if not sql_file.is_file():
        raise ValueError("SQL file must be an existing local file")
    if sql_file.stat().st_size > 1_000_000:
        raise ValueError("SQL file must be no larger than 1 MB")
    if isinstance(max_rows, bool) or not isinstance(max_rows, int) or not 1 <= max_rows <= 10000:
        raise ValueError("max_rows must be an integer from 1 to 10000")
    sql = _safe_query(sql_file.read_text())
    try:
        import duckdb
    except ImportError as error:
        raise ValueError("DuckDB adapter requires the optional local package: python3 -m pip install duckdb") from error

    database_stat = database.stat()
    started = time.monotonic()
    try:
        connection = duckdb.connect(str(database), read_only=True)
        try:
            connection.execute("SET enable_external_access = false")
            connection.execute("SET autoinstall_known_extensions = false")
            connection.execute("SET autoload_known_extensions = false")
            # The wrapper bounds materialized output. The database remains read-only.
            cursor = connection.execute("SELECT * FROM (" + sql + ") AS chatdata_query LIMIT ?", [max_rows + 1])
            columns = [item[0] for item in cursor.description]
            result_rows = cursor.fetchall()
        finally:
            connection.close()
    except duckdb.Error as error:
        raise ValueError("DuckDB could not execute the bounded read-only query") from error
    truncated = len(result_rows) > max_rows
    result_rows = result_rows[:max_rows]
    return {
        "result": "completed_read_only",
        "database_fingerprint": {
            "size_bytes": database_stat.st_size,
            "modified_time_ns": database_stat.st_mtime_ns,
        },
        "sql_sha256": hashlib.sha256(sql_file.read_bytes()).hexdigest(),
        "columns": columns,
        "rows": result_rows,
        "row_count_returned": len(result_rows),
        "truncated": truncated,
        "max_rows": max_rows,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "limits": [
            "The row limit bounds returned results; it does not guarantee a bounded scan.",
            "External file, URL, extension installation, and attach access are disabled for this query.",
            "Read-only execution does not establish metric correctness, freshness, or safe join grain.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", help="Existing local DuckDB database file")
    parser.add_argument("--sql-file", required=True, help="File containing one read-only query")
    parser.add_argument("--max-rows", type=int, default=1000)
    args = parser.parse_args()
    try:
        print(json.dumps(query_database(args.database, args.sql_file, args.max_rows), indent=2, default=str))
    except (ValueError, OSError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
