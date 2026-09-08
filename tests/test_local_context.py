import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_analysis import P, load


C = load("local_context", P / "scripts/local_context.py")


class LocalContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="chatdata-context-")
        self.root = Path(self.tmp.name) / "project"
        self.root.mkdir()
        self.source = self.root / "data" / "orders.csv"
        self.source.parent.mkdir()
        self.source.write_text("order_id,status\n1,complete\n")
        self.evidence = self.root / "checks" / "orders-quality.json"
        self.evidence.parent.mkdir()
        self.evidence.write_text('{"duplicates":0}\n')
        C.initialize(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def write_json(self, relative, value):
        (self.root / relative).write_text(json.dumps(value, indent=2) + "\n")

    def model(self, expression="COUNT(DISTINCT order_id)"):
        return {
            "version": "0.2.0.dev0",
            "semantic_model": [{
                "name": "local_model",
                "datasets": [{"name": "orders", "source": "local.orders"}],
                "metrics": [{
                    "name": "orders_count",
                    "description": "Completed orders",
                    "datatype": "Integer",
                    "expression": {"dialects": [{"dialect": "ANSI_SQL", "expression": expression}]},
                }],
            }],
        }

    def trust_record(self, model=None):
        model = model or self.model()
        return {
            "schema_version": 1,
            "metrics": {
                "orders_count": {
                    "definition": "Distinct completed orders",
                    "unit": "orders",
                    "population": "production orders",
                    "timezone": "UTC",
                    "window": "calendar day",
                    "exclusions": "test and refunded orders",
                    "null_policy": "exclude missing order IDs",
                    "grain": "one row per order",
                    "reviewed_by_user": True,
                    "reviewed_at": "2026-01-01T00:00:00Z",
                    "semantic_sha256": C._canonical_sha256(model),
                    "sources": [{
                        "dataset": "orders",
                        "path": "data/orders.csv",
                        "sha256": C.fingerprint(self.root, "data/orders.csv")["sha256"],
                        "checked_at": "2026-01-01T00:00:00Z",
                        "valid_until": "2027-01-01T00:00:00Z",
                    }],
                    "checks": [{
                        "name": "duplicate order IDs",
                        "status": "passed",
                        "evidence_path": "checks/orders-quality.json",
                        "evidence_sha256": C.fingerprint(self.root, "checks/orders-quality.json")["sha256"],
                    }],
                    "unresolved_conflicts": [],
                    "caveats": ["Late arriving orders can revise recent days."],
                }
            },
        }

    def make_ready(self):
        model = self.model()
        self.write_json("chatdata-context/semantic-model.json", model)
        self.write_json("chatdata-context/trust.json", self.trust_record(model))
        return model

    def check(self):
        return C.check(self.root, "orders_count", now=datetime(2026, 6, 1, tzinfo=timezone.utc))

    def test_init_is_private_metadata_only_and_refuses_existing_destination(self):
        context = self.root / "chatdata-context"
        self.assertEqual((context / ".gitignore").read_text(), "*\n")
        self.assertEqual(json.loads((context / "semantic-model.json").read_text()), {"version": "0.2.0.dev0", "semantic_model": []})
        inventory = json.loads((context / "inventory.json").read_text())
        self.assertIn("data/orders.csv", [item["path"] for item in inventory["inventory"]])
        self.assertIn("did not read, move, upload", (context / "README.md").read_text())
        original = (context / "trust.json").read_text()
        with self.assertRaisesRegex(C.ContextRefused, "already exists"):
            C.initialize(self.root)
        self.assertEqual((context / "trust.json").read_text(), original)

    def test_init_escapes_local_file_labels_in_html(self):
        other = Path(self.tmp.name) / "html-project"
        other.mkdir()
        (other / "a<script>.sql").write_text("do not read me")
        C.initialize(other)
        rendered = (other / "chatdata-context/index.html").read_text()
        self.assertIn("a&lt;script&gt;.sql", rendered)
        self.assertNotIn("a<script>", rendered)
        self.assertNotIn("http://", rendered)
        self.assertNotIn("https://", rendered)

    def test_incomplete_inventory_is_visible_and_blocks(self):
        other = Path(self.tmp.name) / "partial-project"
        other.mkdir()
        report = {
            "status": "incomplete", "root": str(other),
            "window": {"days": 30}, "inventory": [],
            "coverage": {"complete": False, "selected_files": 0, "errors": [{"path": "locked", "error": "PermissionError"}]},
        }
        fake_inventory = type("Inventory", (), {"_validated_root": lambda _, raw: Path(raw).resolve(), "scan": lambda *args, **kwargs: report})()
        with patch.object(C, "_load_sibling", return_value=fake_inventory):
            result = C.initialize(other)
        self.assertEqual(result["status"], "initialized_with_inventory_gap")
        self.assertIn("incomplete", (other / "chatdata-context/README.md").read_text().lower())

    def test_refresh_updates_reports_and_preserves_user_records(self):
        context = self.root / "chatdata-context"
        model_before = (context / "semantic-model.json").read_bytes()
        trust_before = (context / "trust.json").read_bytes()
        readme_before = (context / "README.md").read_bytes()
        (self.root / "new-analysis.sql").write_text("select 1")
        result = C.refresh(self.root)
        self.assertEqual(result["status"], "refreshed")
        inventory = json.loads((context / "inventory.json").read_text())
        self.assertIn("new-analysis.sql", [item["path"] for item in inventory["inventory"]])
        self.assertNotIn("chatdata-context/inventory.json", [item["path"] for item in inventory["inventory"]])
        self.assertEqual((context / "semantic-model.json").read_bytes(), model_before)
        self.assertEqual((context / "trust.json").read_bytes(), trust_before)
        self.assertEqual((context / "README.md").read_bytes(), readme_before)

    def test_missing_metric_blocks_with_exact_gap(self):
        result = self.check()
        self.assertEqual(result["status"], "blocked")
        self.assertIn("metric_not_uniquely_modeled", [gap["code"] for gap in result["gaps"]])
        self.assertIn("missing_trust_record", [gap["code"] for gap in result["gaps"]])

    def test_ready_requires_all_local_proof(self):
        model = self.make_ready()
        result = self.check()
        self.assertEqual(result["status"], "ready_for_analysis")
        self.assertEqual(result["semantic_sha256"], C._canonical_sha256(model))
        self.assertIn("does not prove", result["meaning"])

    def test_changed_source_and_changed_semantic_model_block(self):
        model = self.make_ready()
        self.source.write_text("order_id,status\n2,complete\n")
        result = self.check()
        self.assertIn("source_changed", [gap["code"] for gap in result["gaps"]])
        self.source.write_text("order_id,status\n1,complete\n")
        model["semantic_model"][0]["metrics"][0]["description"] = "Revised definition"
        self.write_json("chatdata-context/semantic-model.json", model)
        result = self.check()
        self.assertIn("semantic_model_changed", [gap["code"] for gap in result["gaps"]])

    def test_unreviewed_stale_and_conflicted_records_block(self):
        model = self.model()
        trust = self.trust_record(model)
        record = trust["metrics"]["orders_count"]
        record["reviewed_by_user"] = False
        record["sources"][0]["valid_until"] = "2026-05-01T00:00:00Z"
        record["unresolved_conflicts"] = ["dashboard disagrees"]
        self.write_json("chatdata-context/semantic-model.json", model)
        self.write_json("chatdata-context/trust.json", trust)
        codes = [gap["code"] for gap in self.check()["gaps"]]
        self.assertIn("not_reviewed", codes)
        self.assertIn("stale_source", codes)
        self.assertIn("unresolved_conflicts", codes)

    def test_traversal_symlink_remote_and_wrong_dataset_are_local_proof_gaps(self):
        model = self.model()
        trust = self.trust_record(model)
        source = trust["metrics"]["orders_count"]["sources"][0]
        for unsafe in ("../orders.csv", "https://example.com/orders.csv"):
            source["path"] = unsafe
            source["dataset"] = "missing_dataset"
            self.write_json("chatdata-context/semantic-model.json", model)
            self.write_json("chatdata-context/trust.json", trust)
            codes = [gap["code"] for gap in self.check()["gaps"]]
            self.assertIn("missing_local_proof", codes)
            self.assertIn("unmapped_local_source", codes)
        link = self.root / "linked.csv"
        link.symlink_to(self.source)
        source.update(path="linked.csv", dataset="orders")
        self.write_json("chatdata-context/trust.json", trust)
        self.assertIn("missing_local_proof", [gap["code"] for gap in self.check()["gaps"]])

    def test_placeholder_expression_and_raced_file_block(self):
        model = self.model(expression="")
        trust = self.trust_record(model)
        self.write_json("chatdata-context/semantic-model.json", model)
        self.write_json("chatdata-context/trust.json", trust)
        self.assertIn("placeholder_metric_expression", [gap["code"] for gap in self.check()["gaps"]])
        self.make_ready()
        original = C.os.fstat
        calls = {"count": 0}

        def changing_fstat(fd):
            value = original(fd)
            calls["count"] += 1
            if calls["count"] == 2:
                altered = list(value)
                altered[8] = value.st_mtime + 1
                return os.stat_result(altered)
            return value

        with patch.object(C.os, "fstat", side_effect=changing_fstat):
            result = self.check()
        self.assertEqual(result["status"], "blocked")

    def test_malformed_json_values_and_unhashable_dataset_block_without_traceback(self):
        model = self.model()
        trust = self.trust_record(model)
        trust["metrics"]["orders_count"]["sources"][0]["dataset"] = ["orders"]
        self.write_json("chatdata-context/semantic-model.json", model)
        self.write_json("chatdata-context/trust.json", trust)
        result = self.check()
        self.assertEqual(result["status"], "blocked")
        self.assertIn("unmapped_local_source", [gap["code"] for gap in result["gaps"]])

        (self.root / "chatdata-context/trust.json").write_text('{"schema_version":1,"schema_version":1,"metrics":{}}')
        result = self.check()
        self.assertEqual(result["status"], "blocked")
        self.assertIn("duplicate key", result["gaps"][0]["detail"])

        (self.root / "chatdata-context/trust.json").write_text('{"schema_version":NaN,"metrics":{}}')
        result = self.check()
        self.assertEqual(result["status"], "blocked")
        self.assertIn("non-finite", result["gaps"][0]["detail"])

    def test_invalid_semantic_shapes_and_relationship_integrity_block(self):
        for mutate in (
            lambda model: model["semantic_model"][0]["metrics"][0].update(expression={"dialects": None}),
            lambda model: model["semantic_model"][0].update(relationships=[{
                "name": "bad", "from": ["orders"], "to": "orders",
                "from_columns": ["id"], "to_columns": ["id"],
            }]),
        ):
            model = self.model()
            mutate(model)
            self.write_json("chatdata-context/semantic-model.json", model)
            result = self.check()
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["gaps"][0]["code"], "invalid_semantic_model")

        model = self.model()
        namespace = model["semantic_model"][0]
        namespace["datasets"][0]["fields"] = [{
            "name": "order_id", "datatype": "Integer",
            "expression": {"dialects": [{"dialect": "ANSI_SQL", "expression": ""}]},
        }]
        namespace["relationships"] = [{
            "name": "self", "from": "orders", "to": "orders",
            "from_columns": [""], "to_columns": ["order_id"],
        }]
        trust = self.trust_record(model)
        self.write_json("chatdata-context/semantic-model.json", model)
        self.write_json("chatdata-context/trust.json", trust)
        codes = [gap["code"] for gap in self.check()["gaps"]]
        self.assertIn("placeholder_field_expression", codes)
        self.assertIn("placeholder_relationship_column", codes)

    def test_cli_blocked_exit_two_and_fingerprint_helpers(self):
        script = P / "scripts/local_context.py"
        blocked = subprocess.run(
            [sys.executable, str(script), "check", "--root", str(self.root), "--metric", "orders_count"],
            text=True, capture_output=True,
        )
        self.assertEqual(blocked.returncode, 2)
        self.assertEqual(json.loads(blocked.stdout)["status"], "blocked")
        hashed = C.fingerprint(self.root, "data/orders.csv")
        self.assertEqual(len(hashed["sha256"]), 64)
        semantic = C.semantic_hash(self.root)
        self.assertEqual(semantic["semantic_sha256"], C._canonical_sha256(json.loads((self.root / semantic["path"]).read_text())))


if __name__ == "__main__":
    unittest.main()
