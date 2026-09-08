import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/chatdata"


def load_status():
    spec = importlib.util.spec_from_file_location("chatdata_status", PLUGIN / "scripts/status.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


S = load_status()
TOKEN = "cdi_" + "a" * 43


class StatusReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="chatdata-status-")
        self.data = Path(self.tmp.name) / "data"
        self.data.mkdir()
        self.environment = patch.dict(os.environ, {"CHATDATA_HOME": str(self.data)})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.tmp.cleanup()

    def write_json(self, name, value):
        (self.data / name).write_text(json.dumps(value), encoding="utf-8")

    def link(self, client="claude-code"):
        self.write_json("individual-telemetry.json", {
            "consent_version": "individual-usage-v1",
            "installations": {client: {"token": TOKEN, "connected_at": "2026-09-07T20:00:00Z"}},
        })

    def queue_event(self, client="claude-code"):
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "workflow_started",
            "workflow_id": str(uuid.uuid4()),
            "occurred_at": "2026-09-07T20:00:00Z",
            "client": client,
            "skill_id": "root-cause",
            "plugin_version": "1.4.1",
        }
        record = {"installation_key": "b" * 64, "event": event}
        (self.data / "individual-telemetry-queue.jsonl").write_text(
            json.dumps(record) + "\n", encoding="utf-8")

    def test_unlinked_report_is_clear_and_uses_default_hourly_value(self):
        report = S.build_report()
        expected_version = json.loads(
            (PLUGIN / "scripts/package-info.json").read_text(encoding="utf-8"))["version"]
        self.assertEqual(report["version"], expected_version)
        self.assertTrue(all(item["local_link"] == "not_linked"
                            for item in report["clients"].values()))
        self.assertEqual(report["usage"]["pending_events"], 0)
        self.assertEqual(report["cached_dashboard_summary"]["hourly_value_usd"], 125)
        self.assertEqual([item["code"] for item in report["next_steps"]],
                         ["link", "set_baseline"])
        human = S.render(report)
        self.assertIn("Linked locally means this computer has", human)
        self.assertIn("$125/hour default", human)
        self.assertIn("not a live server check", human)

    def test_link_queue_and_cached_settings_are_reported_without_token(self):
        self.link()
        self.queue_event()
        self.write_json("individual-telemetry-summary.json", {
            "tracked_prompts": 2,
            "completed_workflows": 1,
            "observed_elapsed_seconds": 30,
            "estimates_configured": True,
            "baseline_minutes_per_workflow": 60,
            "hourly_value_usd": 175,
            "estimated_hours_saved": 0.5,
            "estimated_value_usd": 87.5,
            "updated_at": "2026-09-07T21:00:00Z",
        })
        report = S.build_report()
        serialized = json.dumps(report)
        self.assertNotIn(TOKEN, serialized)
        self.assertEqual(report["clients"]["claude-code"]["local_link"], "linked_locally")
        self.assertEqual(report["clients"]["codex"]["local_link"], "not_linked")
        self.assertEqual(report["usage"]["pending_events"], 1)
        self.assertEqual(report["cached_dashboard_summary"]["updated_at"],
                         "2026-09-07T21:00:00Z")
        self.assertEqual(report["cached_dashboard_summary"]["tracked_prompts"], 2)
        self.assertEqual(report["cached_dashboard_summary"]["completed_workflows"], 1)
        self.assertEqual(report["cached_dashboard_summary"]["estimated_hours_saved"], 0.5)
        self.assertEqual(report["cached_dashboard_summary"]["estimated_value_usd"], 87.5)
        self.assertEqual(report["cached_dashboard_summary"]["hourly_value_usd"], 175)
        self.assertEqual(report["cached_dashboard_summary"]["hourly_value_source"],
                         "dashboard_setting")
        self.assertEqual([item["code"] for item in report["next_steps"]], ["flush"])
        human = S.render(report)
        self.assertIn("Workflows started   2", human)
        self.assertIn("Completed workflows 1", human)
        self.assertIn("0.5 hours · $88 (cached)", human)
        self.assertIn("combine linked clients", human)

    def test_cached_counts_are_kept_when_estimates_are_not_configured(self):
        self.link("codex")
        self.write_json("individual-telemetry-summary.json", {
            "tracked_prompts": 0,
            "completed_workflows": 4,
            "observed_elapsed_seconds": 125,
            "estimates_configured": False,
            "estimated_hours_saved": 999,
            "estimated_value_usd": 999999,
            "updated_at": "2026-09-07T21:00:00Z",
        })
        report = S.build_report()
        summary = report["cached_dashboard_summary"]
        self.assertEqual(summary["tracked_prompts"], 0)
        self.assertEqual(summary["completed_workflows"], 4)
        self.assertEqual(summary["observed_elapsed_seconds"], 125)
        self.assertIsNone(summary["estimated_hours_saved"])
        self.assertIsNone(summary["estimated_value_usd"])
        human = S.render(report)
        self.assertIn("Workflows started   0", human)
        self.assertNotIn("999", human)

    def test_bool_nonfinite_and_malformed_totals_are_never_shown_as_savings(self):
        self.link("cursor")
        self.write_json("individual-telemetry-summary.json", {
            "tracked_prompts": True,
            "completed_workflows": -1,
            "observed_elapsed_seconds": "private elapsed value",
            "estimates_configured": True,
            "baseline_minutes_per_workflow": 60,
            "hourly_value_usd": 125,
            "estimated_hours_saved": float("nan"),
            "estimated_value_usd": True,
            "updated_at": "2026-09-07T21:00:00Z",
        })
        report = S.build_report()
        summary = report["cached_dashboard_summary"]
        self.assertIsNone(summary["tracked_prompts"])
        self.assertIsNone(summary["completed_workflows"])
        self.assertIsNone(summary["observed_elapsed_seconds"])
        self.assertIsNone(summary["estimated_hours_saved"])
        self.assertIsNone(summary["estimated_value_usd"])
        self.assertIn("Estimated saved     unavailable", S.render(report))

    def test_malformed_private_files_never_leak_or_become_claimed_status(self):
        secret = "PRIVATE_CUSTOMER_PROMPT_NEVER_PRINT"
        (self.data / "individual-telemetry.json").write_text(
            json.dumps({"token": TOKEN, "prompt": secret}), encoding="utf-8")
        (self.data / "individual-telemetry-queue.jsonl").write_text(
            json.dumps({"prompt": secret}) + "\n", encoding="utf-8")
        self.write_json("individual-telemetry-summary.json", {
            "estimates_configured": True,
            "estimated_value_usd": 900,
            "prompt": secret,
            "updated_at": secret,
        })
        before = {path.name: path.read_bytes() for path in self.data.iterdir()}
        report = S.build_report()
        human = S.render(report)
        after = {path.name: path.read_bytes() for path in self.data.iterdir()}
        serialized = json.dumps(report) + human
        self.assertNotIn(secret, serialized)
        self.assertNotIn(TOKEN, serialized)
        self.assertTrue(all(item["local_link"] == "unknown"
                            for item in report["clients"].values()))
        self.assertIsNone(report["usage"]["pending_events"])
        self.assertFalse(report["cached_dashboard_summary"]["estimates_configured"])
        self.assertEqual(before, after)

    def test_symlink_and_oversized_files_are_not_read(self):
        private = Path(self.tmp.name) / "private.json"
        private.write_text(json.dumps({"prompt": "SYMLINK_SECRET"}), encoding="utf-8")
        (self.data / "individual-telemetry.json").symlink_to(private)
        (self.data / "individual-telemetry-summary.json").write_text(
            "x" * (S.MAX_JSON_BYTES + 1), encoding="utf-8")
        report = S.build_report()
        self.assertEqual(report["local_files"]["link_state"], "unsafe")
        self.assertEqual(report["local_files"]["summary_state"], "unsafe")
        self.assertNotIn("SYMLINK_SECRET", json.dumps(report))

    @unittest.skipUnless(hasattr(os, "mkfifo"), "named pipes are not available")
    def test_named_pipe_cannot_block_status(self):
        os.mkfifo(self.data / "individual-telemetry.json")
        completed = subprocess.run(
            [sys.executable, str(PLUGIN / "scripts/status.py"), "--json"],
            text=True, capture_output=True, check=True,
            env={**os.environ, "CHATDATA_HOME": str(self.data)}, timeout=3,
        )
        report = json.loads(completed.stdout)
        self.assertEqual(report["local_files"]["link_state"], "unsafe")
        self.assertTrue(all(item["local_link"] == "unknown"
                            for item in report["clients"].values()))

    def test_json_check_runs_bundled_doctor_without_network(self):
        completed = subprocess.run(
            [sys.executable, str(PLUGIN / "scripts/status.py"), "--json", "--check"],
            text=True, capture_output=True, check=True,
            env={**os.environ, "CHATDATA_HOME": str(self.data)}, timeout=60,
        )
        report = json.loads(completed.stdout)
        self.assertTrue(report["offline_check"])
        self.assertFalse(report["server_authorization_checked"])
        self.assertEqual(report["local_checks"]["status"], "passed")
        self.assertEqual(len(report["local_checks"]["checks"]), 3)

    def test_status_command_uses_report_with_bundled_checks(self):
        command = (PLUGIN / "commands/status.md").read_text(encoding="utf-8")
        self.assertIn('scripts/status.py" --check', command)
        self.assertNotIn('scripts/telemetry.py" status', command)


if __name__ == "__main__":
    unittest.main()
