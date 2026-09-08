#!/usr/bin/env python3
"""Run planted-defect checks against ChatData's deterministic helpers."""
import importlib.util
import json
import math
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/chatdata"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


A = _load("chatdata_analyze_eval", PLUGIN / "scripts/analyze.py")
R = _load("chatdata_retention_eval", PLUGIN / "scripts/retention.py")
J = _load("chatdata_join_eval", PLUGIN / "scripts/join_audit.py")


def run():
    cases = []
    experiment = A.experiment(1000, 100, 1500, 300)
    cases.append({"id": "uneven-assignment", "passed": experiment["result"] == "blocked_srm",
                  "observed": experiment["result"]})

    _, funnel_rows = A.rows(PLUGIN / "examples/funnel.csv")
    funnel = A.funnel(funnel_rows, ["visit", "signup", "purchase"], "2026-01-05T00:00:00Z", 48)
    observed_funnel = [step["users"] for step in funnel["steps"]]
    funnel_pass = observed_funnel == [3, 2, 1] and funnel["excluded_immature_users"] == 1 and funnel["duplicate_events_removed"] == 1
    cases.append({"id": "funnel-order-and-maturity", "passed": funnel_pass,
                  "observed": {"users": observed_funnel, "excluded_immature": funnel["excluded_immature_users"], "duplicates_removed": funnel["duplicate_events_removed"]}})

    _, mix_rows = A.rows(PLUGIN / "examples/mix-shift.csv")
    mix = A.decompose(mix_rows)
    mix_pass = all(math.isclose(mix[key], expected, abs_tol=1e-12) for key, expected in {
        "change_pp": -9, "mix_pp": -9, "within_pp": 0, "reconciliation_residual_pp": 0,
    }.items())
    cases.append({"id": "composition-before-causation", "passed": mix_pass,
                  "observed": {key: round(mix[key], 6) for key in ("change_pp", "mix_pp", "within_pp", "reconciliation_residual_pp")}})

    with tempfile.TemporaryDirectory() as temporary:
        temporary = Path(temporary)
        cohorts = temporary / "cohorts.csv"
        activity = temporary / "activity.csv"
        cohorts.write_text("entity_id,cohort_at\na,2026-01-20T00:00:00Z\n")
        activity.write_text("entity_id,activity_at\n")
        retention = R.retention(cohorts, activity, as_of="2026-01-25T00:00:00Z", timezone_name="UTC", frequency="week", periods=2)
        cell = retention["cohorts"][0]["cells"][1]
        cases.append({"id": "immature-retention", "passed": cell["status"] == "unobserved" and cell["rate"] is None,
                      "observed": {"status": cell["status"], "rate": cell["rate"]}})

        left = temporary / "orders.csv"
        right = temporary / "items.csv"
        left.write_text("order_id,revenue\nA,10\nB,20\n")
        right.write_text("order_id,item_id\nA,1\nA,2\nA,3\nB,4\nB,5\n")
        join = J.audit(left, right, ["order_id"], ["order_id"], "one-to-many", "revenue")
        reconciliation = join["left_measure_reconciliation"]
        join_pass = join["status"] == "blocked" and reconciliation["input_total"] == "30" and reconciliation["left_output_total"] == "70"
        cases.append({"id": "join-measure-inflation", "passed": join_pass,
                      "observed": {"status": join["status"], "input_total": reconciliation["input_total"], "left_output_total": reconciliation["left_output_total"]}})

    passed = sum(case["passed"] for case in cases)
    return {
        "suite": "ChatData planted-defect enforcement",
        "plugin_version": json.loads((PLUGIN / "scripts/package-info.json").read_text())["version"],
        "passed": passed,
        "total": len(cases),
        "cases": cases,
        "claim_limit": "This tests deterministic helpers on known synthetic defects. It does not measure AI reasoning, real-world accuracy, or productivity lift.",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
