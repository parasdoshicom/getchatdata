import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/chatdata/scripts/duckdb_query.py"
spec = importlib.util.spec_from_file_location("duckdb_query", SCRIPT)
D = importlib.util.module_from_spec(spec)
spec.loader.exec_module(D)


class QueryValidationTests(unittest.TestCase):
    def test_accepts_one_read_only_statement(self):
        self.assertEqual(D._safe_query("SELECT 1;"), "SELECT 1")
        self.assertTrue(D._safe_query("WITH x AS (SELECT 1) SELECT * FROM x").startswith("WITH"))

    def test_rejects_writes_extensions_and_multiple_statements(self):
        rejected = [
            "DELETE FROM x", "SELECT 1; DROP TABLE x", "INSTALL httpfs",
            "LOAD httpfs", "ATTACH 'other.db'", "COPY x TO 'out.csv'",
        ]
        for sql in rejected:
            with self.subTest(sql=sql), self.assertRaises(ValueError):
                D._safe_query(sql)

    def test_missing_database_fails_before_optional_dependency(self):
        with tempfile.TemporaryDirectory() as tmp:
            query = Path(tmp) / "query.sql"
            query.write_text("SELECT 1")
            with self.assertRaisesRegex(ValueError, "existing local file"):
                D.query_database(Path(tmp) / "missing.duckdb", query)


try:
    import duckdb
except ImportError:
    duckdb = None


@unittest.skipIf(duckdb is None, "optional duckdb package is not installed")
class DuckDBExecutionTests(unittest.TestCase):
    def test_read_only_query_is_bounded_and_fingerprinted(self):
        with tempfile.TemporaryDirectory() as tmp:
            database = Path(tmp) / "test.duckdb"
            con = duckdb.connect(str(database))
            con.execute("CREATE TABLE values_table AS SELECT range AS value FROM range(5)")
            con.close()
            sql_file = Path(tmp) / "query.sql"
            sql_file.write_text("SELECT value FROM values_table ORDER BY value")
            result = D.query_database(database, sql_file, 3)
            self.assertEqual(result["result"], "completed_read_only")
            self.assertEqual(result["rows"], [(0,), (1,), (2,)])
            self.assertTrue(result["truncated"])
            self.assertGreater(result["database_fingerprint"]["size_bytes"], 0)
            self.assertEqual(len(result["sql_sha256"]), 64)

    def test_external_file_access_is_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            database = Path(tmp) / "test.duckdb"
            con = duckdb.connect(str(database))
            con.execute("CREATE TABLE safe(value INTEGER)")
            con.close()
            private_file = Path(tmp) / "private.csv"
            private_file.write_text("secret\nvalue\n")
            sql_file = Path(tmp) / "query.sql"
            sql_file.write_text("SELECT * FROM read_csv_auto('" + str(private_file).replace("'", "''") + "')")
            with self.assertRaisesRegex(ValueError, "could not execute"):
                D.query_database(database, sql_file)


if __name__ == "__main__":
    unittest.main()
