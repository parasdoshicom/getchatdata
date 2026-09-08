import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "evals/model-comparison/compare.py"
spec = importlib.util.spec_from_file_location("comparison", SCRIPT)
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)


class ComparisonTests(unittest.TestCase):
    def test_prepare_blinds_and_summary_reveals_only_after_scoring(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            cases = tmp / "cases.json"
            cases.write_text(json.dumps([
                {"id": "a", "pass": "find a", "fail": "miss a"},
                {"id": "b", "pass": "find b", "fail": "miss b"},
            ]))
            guided = tmp / "guided"; guided.mkdir()
            unguided = tmp / "unguided"; unguided.mkdir()
            for case in ("a", "b"):
                (guided / (case + ".md")).write_text("guided " + case)
                (unguided / (case + ".md")).write_text("plain " + case)
            output = tmp / "review-set"
            result = C.prepare(cases, guided, unguided, output, 9)
            self.assertEqual(result["responses"], 4)
            packets = list((output / "review").glob("*.md"))
            self.assertEqual(len(packets), 4)
            scores = json.loads((output / "scores.json").read_text())
            key = json.loads((output / "key.json").read_text())
            condition = {item["blind_id"]: item["condition"] for item in key}
            for score in scores:
                score["passed"] = condition[score["blind_id"]] == "chatdata"
                score["condition_guess"] = "unknown"
                score["blinding_compromised"] = False
            (output / "scores.json").write_text(json.dumps(scores))
            report = C.summarize(output / "key.json", output / "scores.json")
            self.assertEqual(report["conditions"]["chatdata"]["pass_rate"], 1)
            self.assertEqual(report["conditions"]["unguided"]["pass_rate"], 0)
            self.assertEqual(report["chatdata_only_passes"], 2)

    def test_incomplete_scoring_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            key = Path(tmp) / "key.json"; scores = Path(tmp) / "scores.json"
            key.write_text(json.dumps([{"blind_id": "x", "condition": "chatdata", "case_id": "a"}]))
            scores.write_text(json.dumps([{"blind_id": "x", "case_id": "a", "passed": None,
                                           "condition_guess": "unknown", "blinding_compromised": False}]))
            with self.assertRaisesRegex(ValueError, "true or false"):
                C.summarize(key, scores)

    def test_explicit_condition_names_are_masked_but_original_is_preserved(self):
        masked, replacements = C._mask_condition_markers("ChatData result; unguided comparison")
        self.assertEqual(replacements, 2)
        self.assertNotIn("ChatData", masked)
        self.assertNotIn("unguided", masked)


if __name__ == "__main__":
    unittest.main()
