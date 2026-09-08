import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "evals/run_enforcement_eval.py"
spec = importlib.util.spec_from_file_location("enforcement_eval", SCRIPT)
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)


class EnforcementEvaluationTests(unittest.TestCase):
    def test_all_planted_defects_are_caught(self):
        report = E.run()
        self.assertEqual(report["passed"], report["total"])
        self.assertEqual(report["total"], 5)
        self.assertIn("does not measure AI reasoning", report["claim_limit"])


if __name__ == "__main__":
    unittest.main()
