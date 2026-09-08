import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from test_analysis import P


SCRIPT = P / "scripts/claude-statusline.py"
TOKEN = "cdi_" + "a" * 43


class StatuslineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="chatdata-statusline-")
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, value):
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / name).write_text(json.dumps(value))

    def fresh_time(self):
        return (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()

    def link_claude(self):
        self.write("individual-telemetry.json", {
            "consent_version": "individual-usage-v1",
            "installations": {"claude-code": {"token": TOKEN}},
        })

    def run_statusline(self, stdin="{}"):
        return subprocess.run(
            [sys.executable, str(SCRIPT)], input=stdin, text=True,
            capture_output=True, check=True, timeout=5,
            env={**os.environ, "CHATDATA_HOME": str(self.root)},
        ).stdout.strip()

    def test_unlinked_state_ignores_preserved_summary_and_never_exposes_secrets(self):
        secret = "private-prompt-and-token"
        self.write("individual-telemetry-summary.json", {
            "tracked_prompts": 9,
            "estimates_configured": True,
            "estimated_hours_saved": 8.5,
            "estimated_value_usd": 1062.5,
            "prompt": secret,
        })
        output = self.run_statusline(secret)
        self.assertEqual(output, "ChatData · usage not linked · connect in your dashboard")
        self.assertNotIn(secret, output)
        self.assertNotIn("1,062", output)

    def test_linked_state_shows_workflows_and_only_requests_time_baseline(self):
        self.link_claude()
        self.write("individual-telemetry-summary.json", {
            "tracked_prompts": 3,
            "completed_workflows": 2,
            "estimates_configured": False,
            "hourly_value_usd": 125,
            "updated_at": self.fresh_time(),
        })
        self.assertEqual(
            self.run_statusline(),
            "ChatData · 2 completed workflows · set your time baseline in the dashboard",
        )

    def test_other_client_link_does_not_make_claude_look_linked(self):
        self.write("individual-telemetry.json", {
            "consent_version": "individual-usage-v1",
            "installations": {"codex": {"token": TOKEN}},
        })
        self.write("individual-telemetry-summary.json", {
            "tracked_prompts": 20,
            "estimates_configured": True,
            "estimated_hours_saved": 10,
            "estimated_value_usd": 1250,
        })
        self.assertEqual(
            self.run_statusline(),
            "ChatData · usage not linked · connect in your dashboard",
        )

    def test_linked_state_shows_valid_estimates_without_calling_workflows_prompts(self):
        self.link_claude()
        self.write("individual-telemetry-summary.json", {
            "tracked_prompts": 1,
            "completed_workflows": 1,
            "estimates_configured": True,
            "estimated_hours_saved": 1.25,
            "estimated_value_usd": 156.25,
            "updated_at": self.fresh_time(),
        })
        output = self.run_statusline()
        self.assertEqual(
            output,
            "ChatData · 1 completed workflow · 1.2h est. saved · $156 est. value",
        )
        self.assertNotIn("prompt", output.lower())

    def test_pending_content_free_events_mark_server_totals_before_sync(self):
        self.link_claude()
        self.write("individual-telemetry-summary.json", {
            "tracked_prompts": 3,
            "completed_workflows": 2,
            "estimates_configured": True,
            "estimated_hours_saved": 1.0,
            "estimated_value_usd": 125.0,
            "updated_at": self.fresh_time(),
        })
        event = {
            "event_id": "12345678-1234-4123-8123-123456789abc",
            "event_type": "workflow_started",
            "workflow_id": "abcdefab-1234-4123-8123-123456789abc",
            "occurred_at": "2026-09-08T01:00:00Z",
            "client": "claude-code",
            "skill_id": "root-cause",
            "plugin_version": "1.4.1",
        }
        installation_key = hashlib.sha256(
            ("chatdata-installation:" + TOKEN).encode()
        ).hexdigest()
        record = {"installation_key": installation_key, "event": event}
        (self.root / "individual-telemetry-queue.jsonl").write_text(json.dumps(record) + "\n")
        output = self.run_statusline()
        self.assertIn("1 event pending sync (totals may lag)", output)

    def test_queue_ignores_valid_events_for_other_clients_and_installations(self):
        self.link_claude()
        self.write("individual-telemetry-summary.json", {
            "tracked_prompts": 1,
            "completed_workflows": 0,
            "estimates_configured": False,
            "updated_at": self.fresh_time(),
        })
        base_event = {
            "event_id": "12345678-1234-4123-8123-123456789abc",
            "event_type": "workflow_started",
            "workflow_id": "abcdefab-1234-4123-8123-123456789abc",
            "occurred_at": "2026-09-08T01:00:00Z",
            "skill_id": "root-cause",
            "plugin_version": "1.4.1",
        }
        other_client = {**base_event, "client": "cursor"}
        other_install = {**base_event, "client": "claude-code",
                         "event_id": "87654321-4321-4321-8321-cba987654321"}
        records = [
            {"installation_key": "c" * 64, "event": other_client},
            {"installation_key": "d" * 64, "event": other_install},
        ]
        (self.root / "individual-telemetry-queue.jsonl").write_text(
            "".join(json.dumps(record) + "\n" for record in records)
        )
        output = self.run_statusline()
        self.assertNotIn("pending sync", output)
        self.assertNotIn("totals may lag", output)

    def test_malformed_queue_or_numeric_types_never_produce_false_claims(self):
        self.link_claude()
        secret = "secret prompt"
        self.write("individual-telemetry-summary.json", {
            "tracked_prompts": "500",
            "completed_workflows": True,
            "estimates_configured": True,
            "estimated_hours_saved": "9.5",
            "estimated_value_usd": float("inf"),
            "updated_at": self.fresh_time(),
        })
        (self.root / "individual-telemetry-queue.jsonl").write_text(
            json.dumps({"event": {"event_type": "workflow_started", "prompt": secret}}) + "\n"
        )
        output = self.run_statusline()
        self.assertEqual(output, "ChatData · estimates unavailable")
        self.assertNotIn("500", output)
        self.assertNotIn(secret, output)
        self.assertNotIn("pending", output)

    def test_summary_marks_old_invalid_and_future_cache_ages_without_echoing_values(self):
        self.link_claude()
        base = {
            "tracked_prompts": 1,
            "completed_workflows": 1,
            "estimates_configured": False,
        }
        old = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        self.write("individual-telemetry-summary.json", {**base, "updated_at": old})
        self.assertIn("cached >24h", self.run_statusline())

        future = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        self.write("individual-telemetry-summary.json", {**base, "updated_at": future})
        future_output = self.run_statusline()
        self.assertIn("cache age unknown", future_output)
        self.assertNotIn(future, future_output)

        invalid = "private-invalid-timestamp"
        self.write("individual-telemetry-summary.json", {**base, "updated_at": invalid})
        invalid_output = self.run_statusline()
        self.assertIn("cache age unknown", invalid_output)
        self.assertNotIn(invalid, invalid_output)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO test needs os.mkfifo")
    def test_fifo_state_file_cannot_block_the_footer(self):
        os.mkfifo(self.root / "individual-telemetry.json")
        self.assertEqual(
            self.run_statusline(),
            "ChatData · usage not linked · connect in your dashboard",
        )

    def test_symlinked_or_oversized_state_is_not_read(self):
        outside = Path(self.tmp.name).parent / (self.root.name + "-private.json")
        try:
            outside.write_text(json.dumps({
                "consent_version": "individual-usage-v1",
                "installations": {"claude-code": {"token": TOKEN}},
            }))
            (self.root / "individual-telemetry.json").symlink_to(outside)
            self.write("individual-telemetry-summary.json", {
                "padding": "x" * (17 * 1024),
                "tracked_prompts": 999,
            })
            output = self.run_statusline("private stdin" * 4096)
            self.assertEqual(output, "ChatData · usage not linked · connect in your dashboard")
            self.assertNotIn("999", output)
        finally:
            outside.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
