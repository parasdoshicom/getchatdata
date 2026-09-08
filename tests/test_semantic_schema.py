import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "chatdata"


def load_module():
    path = PLUGIN / "scripts" / "semantic_schema.py"
    spec = importlib.util.spec_from_file_location("chatdata_semantic_schema", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


S = load_module()


def useful_model():
    return {
        "version": "0.2.0.dev0",
        "semantic_model": [
            {
                "name": "local_model",
                "description": "Definitions observed in this project.",
                "datasets": [
                    {
                        "name": "orders",
                        "source": "warehouse.analytics.orders",
                        "primary_key": ["order_id"],
                        "fields": [
                            {
                                "name": "order_id",
                                "datatype": "String",
                                "expression": {
                                    "dialects": [
                                        {"dialect": "ANSI_SQL", "expression": "order_id"}
                                    ]
                                },
                            }
                        ],
                    }
                ],
                "metrics": [
                    {
                        "name": "orders_count",
                        "description": "Distinct completed orders.",
                        "datatype": "Integer",
                        "expression": {
                            "dialects": [
                                {
                                    "dialect": "ANSI_SQL",
                                    "expression": "COUNT(DISTINCT order_id)",
                                }
                            ]
                        },
                        "ai_context": {
                            "instructions": "Exclude test orders and use UTC.",
                            "examples": ["How many orders completed yesterday?"],
                        },
                    }
                ],
            }
        ],
    }


class SemanticSchemaTests(unittest.TestCase):
    def test_bundled_schema_is_exact_pinned_snapshot(self):
        schema_path = PLUGIN / "references" / "ossie" / "ossie-schema.json"
        digest = hashlib.sha256(schema_path.read_bytes()).hexdigest()
        self.assertEqual(
            digest,
            "ce3f3e4a7098f53beb92136cc4cf2f107dde799815497e02a76af4bdf29d2716",
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["properties"]["version"]["const"], "0.2.0.dev0")

    def test_upstream_minimum_is_structurally_valid_but_not_evidence(self):
        self.assertEqual(S.validate({"version": "0.2.0.dev0", "semantic_model": []}), [])

    def test_realistic_dataset_field_and_metric_are_valid(self):
        self.assertEqual(S.validate(useful_model()), [])

    def test_rejects_extra_properties(self):
        model = useful_model()
        model["team_workspace"] = "not part of Ossie"
        errors = S.validate(model)
        self.assertIn("$.team_workspace: additional property is not allowed", errors)

    def test_rejects_wrong_types_and_missing_required_values(self):
        model = useful_model()
        model["semantic_model"][0]["datasets"] = "orders"
        del model["semantic_model"][0]["name"]
        errors = S.validate(model)
        self.assertTrue(any("missing required property 'name'" in error for error in errors))
        self.assertTrue(any("$.semantic_model[0].datasets: must be array" in error for error in errors))

    def test_rejects_invalid_dialect(self):
        model = useful_model()
        model["semantic_model"][0]["metrics"][0]["expression"]["dialects"][0][
            "dialect"
        ] = "POSTGRES"
        errors = S.validate(model)
        self.assertTrue(any("$.semantic_model[0].metrics[0].expression.dialects[0].dialect" in error for error in errors))
        self.assertTrue(any("must be one of" in error for error in errors))

    def test_rejects_empty_required_arrays(self):
        model = useful_model()
        model["semantic_model"][0]["datasets"] = []
        errors = S.validate(model)
        self.assertIn("$.semantic_model[0].datasets: must contain at least 1 item(s)", errors)

    def test_ai_context_must_match_string_or_object(self):
        model = useful_model()
        model["semantic_model"][0]["metrics"][0]["ai_context"] = ["not valid"]
        errors = S.validate(model)
        self.assertTrue(any("must match exactly one allowed shape" in error for error in errors))

    def test_schema_audit_fails_closed_for_unknown_keyword_and_external_ref(self):
        with self.assertRaises(S.UnsupportedSchemaError):
            S._audit_schema({"type": "string", "pattern": "x"})
        with self.assertRaises(S.UnsupportedSchemaError):
            S._audit_schema({"$ref": "https://example.com/schema.json"})
        with self.assertRaises(S.UnsupportedSchemaError):
            S._audit_references({"$ref": "#/$defs/Missing"}, {"$defs": {}})

    def test_json_loader_rejects_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "semantic-model.json"
            path.write_text(
                '{"version":"0.2.0.dev0","version":"0.1.0","semantic_model":[]}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate JSON key 'version'"):
                S.load_json(path)

    def test_json_loader_rejects_oversize_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "semantic-model.json"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exceeds 1 bytes"):
                S.load_json(path, max_bytes=1)

    def test_json_loader_rejects_nonfinite_json_numbers(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "semantic-model.json"
            path.write_text(
                '{"version":"0.2.0.dev0","semantic_model":[],"x":NaN}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "non-finite JSON number"):
                S.load_json(path)

    def test_cli_reports_exact_paths_and_exit_status(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "semantic-model.json"
            path.write_text(json.dumps(useful_model()), encoding="utf-8")
            valid = subprocess.run(
                [sys.executable, str(PLUGIN / "scripts" / "semantic_schema.py"), str(path)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(valid.returncode, 0, valid.stderr)
            self.assertTrue(json.loads(valid.stdout)["valid"])

            path.write_text('{"version":"wrong","semantic_model":[]}', encoding="utf-8")
            invalid = subprocess.run(
                [sys.executable, str(PLUGIN / "scripts" / "semantic_schema.py"), str(path)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(invalid.returncode, 1)
            result = json.loads(invalid.stdout)
            self.assertFalse(result["valid"])
            self.assertIn("$.version: must equal '0.2.0.dev0'", result["errors"])


if __name__ == "__main__":
    unittest.main()
