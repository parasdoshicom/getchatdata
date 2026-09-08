import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_analysis import P, load


T = load("telemetry", P / "scripts/telemetry.py")
TOKEN = "cdi_" + "a" * 43
TOKEN_2 = "cdi_" + "b" * 43
LINK_CODE = "cdl_" + "c" * 43
SUMMARY = {
    "tracked_prompts": 3,
    "completed_workflows": 2,
    "observed_elapsed_seconds": 120,
    "estimated_hours_saved": 1.25,
    "estimated_value_usd": 187.5,
    "estimates_configured": True,
    "baseline_minutes_per_workflow": 45,
    "hourly_value_usd": 150,
    "updated_at": "2026-09-07T20:00:00Z",
}


class TelemetryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="chatdata-telemetry-")
        self.root = Path(self.tmp.name)
        self.settings = self.root / "claude" / "settings.json"
        self.env = patch.dict(os.environ, {
            "CHATDATA_HOME": str(self.root / "data"),
            "CHATDATA_CLAUDE_SETTINGS": str(self.settings),
        })
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def link(self, client="codex", token=TOKEN):
        T._write_json(T.paths()["config"], {
            "consent_version": T.CONSENT_VERSION,
            "installations": {client: {"token": token, "connected_at": "2026-09-07T20:00:00Z"}},
        })

    def test_unlinked_install_stays_offline(self):
        with patch.object(T, "_request") as request:
            result = T.start("codex", "root-cause")
        self.assertEqual(result, {"telemetry": "not_linked"})
        request.assert_not_called()
        self.assertFalse(T.paths()["queue"].exists())

    def test_claude_stop_hook_waits_for_completion_delivery(self):
        hooks = json.loads((P / "hooks/hooks.json").read_text())["hooks"]
        stop = hooks["Stop"][0]["hooks"][0]
        self.assertNotIn("async", stop)
        self.assertEqual(stop["args"][-1], "claude-hook")
        footer = hooks["SessionStart"][0]["hooks"][1]
        self.assertTrue(footer["args"][-2].endswith("/scripts/footer.py"))
        self.assertEqual(footer["args"][-1], "session-start")
        self.assertLessEqual(footer["timeout"], 2)
        startup_flush = hooks["SessionStart"][0]["hooks"][2]
        self.assertEqual(startup_flush["args"][-2:], ["flush", "--silent"])

    def test_connect_requires_consent_and_hides_token(self):
        remote = {"ok": True, "client": "codex", "consent_version": T.CONSENT_VERSION,
                  "account_summary": SUMMARY}
        with patch("builtins.input", return_value="yes"), \
             patch.object(T.getpass, "getpass", return_value=TOKEN), \
             patch.object(T, "_request", return_value=remote) as request:
            result = T.connect("codex")
        self.assertNotIn(TOKEN, json.dumps(result))
        self.assertEqual(T._installation_config("codex")["token"], TOKEN)
        self.assertEqual(T.paths()["config"].stat().st_mode & 0o777, 0o600)
        request.assert_called_once_with("GET", "/api/individual/config", TOKEN)

    def test_declined_consent_writes_nothing(self):
        with patch("builtins.input", return_value="no"), patch.object(T, "_request") as request:
            result = T.connect("cursor")
        self.assertFalse(result["consent"])
        self.assertFalse(T.paths()["config"].exists())
        request.assert_not_called()

    def test_disclosed_dashboard_connect_skips_yes_no_but_keeps_hidden_token_verification(self):
        remote = {"ok": True, "client": "claude-code",
                  "consent_version": T.CONSENT_VERSION,
                  "account_summary": SUMMARY}
        with patch("builtins.input", side_effect=AssertionError("yes/no prompt must be skipped")), \
             patch.object(T.getpass, "getpass", return_value=TOKEN) as hidden_prompt, \
             patch.object(T, "_request", return_value=remote) as request:
            result = T.connect("claude-code", accept_usage_disclosure=True)
        hidden_prompt.assert_called_once()
        request.assert_called_once_with("GET", "/api/individual/config", TOKEN)
        self.assertEqual(result["telemetry"], "linked")
        self.assertNotIn(TOKEN, json.dumps(result))
        self.assertEqual(T._installation_config("claude-code")["token"], TOKEN)

    def test_email_linked_connect_is_non_interactive_and_exchanges_one_time_code(self):
        remote = {"ok": True, "token": TOKEN, "client": "claude-code",
                  "consent_version": T.CONSENT_VERSION,
                  "account_summary": SUMMARY}
        with patch("builtins.input", side_effect=AssertionError("must not prompt")), \
             patch.object(T.getpass, "getpass", side_effect=AssertionError("must not require a TTY")), \
             patch.object(T, "_request", return_value=remote) as request:
            result = T.connect("claude-code", accept_usage_disclosure=True,
                               email="HELLO@getchatdata.com", link_code=LINK_CODE)
        request.assert_called_once_with(
            "POST", "/api/individual/installations/claim", None,
            {"email": "hello@getchatdata.com", "client": "claude-code",
             "consent_version": T.CONSENT_VERSION, "link_code": LINK_CODE},
            timeout=10,
        )
        self.assertEqual(result["telemetry"], "linked")
        self.assertEqual(T._installation_config("claude-code")["token"], TOKEN)
        self.assertNotIn(LINK_CODE, json.dumps(T._config()))

    def test_email_link_requires_email_and_one_time_code_together(self):
        with patch.object(T, "_request") as request:
            with self.assertRaisesRegex(ValueError, "both --email and --link-code"):
                T.connect("codex", accept_usage_disclosure=True,
                          email="hello@getchatdata.com")
        request.assert_not_called()

    def test_disclosed_dashboard_connect_still_rejects_invalid_or_wrong_client_token(self):
        with patch("builtins.input", side_effect=AssertionError("yes/no prompt must be skipped")), \
             patch.object(T.getpass, "getpass", return_value="not-a-token"), \
             patch.object(T, "_request") as request:
            with self.assertRaisesRegex(ValueError, "not valid"):
                T.connect("codex", accept_usage_disclosure=True)
        request.assert_not_called()

        remote = {"ok": True, "client": "cursor",
                  "consent_version": T.CONSENT_VERSION,
                  "account_summary": SUMMARY}
        with patch("builtins.input", side_effect=AssertionError("yes/no prompt must be skipped")), \
             patch.object(T.getpass, "getpass", return_value=TOKEN), \
             patch.object(T, "_request", return_value=remote):
            with self.assertRaisesRegex(ValueError, "different client"):
                T.connect("codex", accept_usage_disclosure=True)
        self.assertIsNone(T._config())

    def test_cli_disclosure_flag_is_explicit_and_defaults_off(self):
        with patch.object(sys, "argv", ["telemetry.py", "connect", "--client", "cursor"]), \
             patch.object(T, "connect", return_value={}) as connect:
            self.assertEqual(T.main(), 0)
        connect.assert_called_once_with("cursor", False, False, None, None)

        with patch.object(sys, "argv", ["telemetry.py", "connect", "--client", "cursor",
                                             "--accept-usage-disclosure"]), \
             patch.object(T, "connect", return_value={}) as connect:
            self.assertEqual(T.main(), 0)
        connect.assert_called_once_with("cursor", False, True, None, None)

        with patch.object(sys, "argv", ["telemetry.py", "connect", "--client", "claude-code",
                                             "--email", "hello@getchatdata.com",
                                             "--link-code", LINK_CODE,
                                             "--accept-usage-disclosure"]), \
             patch.object(T, "connect", return_value={}) as connect:
            self.assertEqual(T.main(), 0)
        connect.assert_called_once_with(
            "claude-code", False, True, "hello@getchatdata.com", LINK_CODE)

    def test_connect_rejects_token_for_a_different_client(self):
        remote = {"ok": True, "client": "cursor", "consent_version": T.CONSENT_VERSION,
                  "account_summary": SUMMARY}
        with patch("builtins.input", return_value="yes"), \
             patch.object(T.getpass, "getpass", return_value=TOKEN), \
             patch.object(T, "_request", return_value=remote):
            with self.assertRaisesRegex(ValueError, "different client"):
                T.connect("codex")
        self.assertIsNone(T._config())

    def test_multiple_clients_keep_separate_tokens_and_batches(self):
        responses = {
            TOKEN: {"ok": True, "client": "claude-code", "consent_version": T.CONSENT_VERSION,
                    "account_summary": SUMMARY},
            TOKEN_2: {"ok": True, "client": "codex", "consent_version": T.CONSENT_VERSION,
                      "account_summary": SUMMARY},
        }
        def remote(method, path, token, payload=None, timeout=3):
            if method == "GET":
                return responses[token]
            ids = [event["event_id"] for event in payload["events"]]
            return {"ok": True, "accepted_event_ids": ids, "duplicate_event_ids": [],
                    "account_summary": SUMMARY}
        with patch("builtins.input", return_value="yes"), \
             patch.object(T.getpass, "getpass", side_effect=[TOKEN, TOKEN_2]), \
             patch.object(T, "_request", side_effect=remote):
            T.connect("claude-code")
            T.connect("codex")
            T.start("claude-code", "root-cause", no_flush=True)
            T.start("codex", "sql-review", no_flush=True)
            result = T.flush()
        self.assertEqual(result["sent"], 2)
        self.assertEqual(T._installation_config("claude-code")["token"], TOKEN)
        self.assertEqual(T._installation_config("codex")["token"], TOKEN_2)
        self.assertEqual(T._queue_events(), [])

    def test_reconnecting_client_discards_only_that_old_installation_queue(self):
        self.link("codex", TOKEN)
        T.start("codex", "root-cause", no_flush=True)
        old_event = T._queue_events()[0]
        remote = {"ok": True, "client": "codex", "consent_version": T.CONSENT_VERSION,
                  "account_summary": SUMMARY}
        with patch("builtins.input", return_value="yes"), \
             patch.object(T.getpass, "getpass", return_value=TOKEN_2), \
             patch.object(T, "_request", return_value=remote):
            result = T.connect("codex")
        self.assertEqual(result["discarded_previous_installation_events"], 1)
        self.assertNotIn(old_event, T._queue_events())
        self.assertEqual(T._installation_config("codex")["token"], TOKEN_2)

    def test_events_use_only_content_free_allowlist(self):
        self.link()
        started = T.start("codex", "root-cause", no_flush=True)
        T.complete(started["workflow_id"], "codex", "root-cause", 90, no_flush=True)
        events = T._queue_events()
        self.assertEqual([event["event_type"] for event in events],
                         ["workflow_started", "workflow_completed"])
        forbidden = {"prompt", "file", "path", "project", "repo", "session_id",
                     "model", "query", "result", "email", "cost"}
        for event in events:
            self.assertFalse(forbidden.intersection(event))
            self.assertEqual(event["workflow_id"], started["workflow_id"])
        self.assertEqual(events[1]["elapsed_seconds"], 90)

    def test_complete_measures_from_local_start_and_preserves_other_state(self):
        self.link("cursor")
        T._write_json(T.paths()["state"], {"active": {"claude-session": {"skill_id": "root-cause"}}})
        with patch.object(T.time, "time", side_effect=[1000.0, 1012.8]):
            started = T.start("cursor", "funnel-analysis", no_flush=True)
            result = T.complete(started["workflow_id"], "cursor", "funnel-analysis", no_flush=True)
        self.assertTrue(result["completed"])
        self.assertEqual(T._queue_events()[1]["elapsed_seconds"], 12)
        state = T._read_json(T.paths()["state"], {})
        self.assertEqual(state["active"], {"claude-session": {"skill_id": "root-cause"}})
        self.assertNotIn(started["workflow_id"], state["manual"])

    def test_complete_rejects_mismatched_client_or_skill(self):
        self.link()
        started = T.start("codex", "sql-review", no_flush=True)
        with self.assertRaisesRegex(ValueError, "must match"):
            T.complete(started["workflow_id"], "codex", "root-cause", no_flush=True)
        self.assertEqual(len(T._queue_events()), 1)

    def test_invalid_queue_record_is_never_sent(self):
        self.link()
        T._ensure_root()
        T.paths()["queue"].write_text(json.dumps({"prompt": "private"}) + "\n")
        with patch.object(T, "_request") as request:
            with self.assertRaisesRegex(RuntimeError, "left unchanged"):
                T.flush()
        request.assert_not_called()

    def test_expired_events_are_removed_before_delivery(self):
        self.link()
        event = T._event("workflow_started", str(T.uuid.uuid4()), "codex", "root-cause")
        event["occurred_at"] = "2025-01-01T00:00:00Z"
        T._write_queue([{"installation_key": T._installation_key(TOKEN), "event": event}])
        with patch.object(T, "_request") as request:
            result = T.flush()
        self.assertEqual(result["queued"], 0)
        self.assertEqual(T._queue_events(), [])
        request.assert_not_called()

    def test_flush_acknowledges_and_caches_server_summary(self):
        self.link("cursor")
        T.start("cursor", "funnel-analysis", no_flush=True)
        queued = T._queue_events()
        response = {"ok": True, "accepted_event_ids": [queued[0]["event_id"]],
                    "duplicate_event_ids": [], "account_summary": SUMMARY}
        with patch.object(T, "_request", return_value=response) as request:
            result = T.flush()
        payload = request.call_args.args[3]
        self.assertEqual(set(payload), {"schema_version", "events"})
        self.assertEqual(result["sent"], 1)
        self.assertEqual(result["delivery_status"], "delivered")
        self.assertEqual(T._queue_events(), [])
        self.assertEqual(T._read_json(T.paths()["summary"], {})["estimated_value_usd"], 187.5)

    def test_failed_delivery_keeps_queue(self):
        self.link()
        T.start("codex", "sql-review", no_flush=True)
        private_error = "private upstream detail must not be returned"
        with patch.dict(os.environ, {"CHATDATA_API_ORIGIN": "http://127.0.0.1:4185"}), \
             patch.object(T, "urlopen", side_effect=T.URLError(private_error)):
            result = T.flush(silent=True)
        self.assertEqual(result["sent"], 0)
        self.assertEqual(result["delivery_status"], "retry_required")
        self.assertEqual(result["error_category"], "network_unavailable")
        self.assertNotIn(private_error, json.dumps(result))
        self.assertEqual(len(T._queue_events()), 1)

    def test_working_agreement_gives_actionable_flush_without_permission_bypass(self):
        agreement = (P / "references/working-agreement.md").read_text()
        self.assertIn('python3 "<resolved telemetry.py path>" flush', agreement)
        self.assertIn("Do not request broader client permissions", agreement)
        self.assertIn("or retry automatically", agreement)

    def test_api_origin_refuses_non_chatdata_remote_host(self):
        with patch.dict(os.environ, {"CHATDATA_API_ORIGIN": "https://example.com"}):
            with self.assertRaisesRegex(RuntimeError, "only connects"):
                T._request("GET", "/api/individual/config", TOKEN)

    def test_claude_hooks_count_one_explicit_workflow_without_prompt_content(self):
        self.link("claude-code")
        session = "private-session-value"
        direct = {"hook_event_name": "UserPromptExpansion", "session_id": session,
                  "command_name": "chatdata:root-cause", "prompt": "secret business question"}
        with patch.object(sys, "stdin", io.StringIO(json.dumps(direct))):
            T.claude_hook()
        nested = {"hook_event_name": "PreToolUse", "session_id": session,
                  "tool_input": {"skill": "chatdata:root-cause", "other": "secret"}}
        with patch.object(sys, "stdin", io.StringIO(json.dumps(nested))):
            T.claude_hook()
        stop = {"hook_event_name": "Stop", "session_id": session,
                "last_assistant_message": "secret answer"}
        with patch.object(T, "flush", return_value={}), \
             patch.object(sys, "stdin", io.StringIO(json.dumps(stop))):
            T.claude_hook()
        events = T._queue_events()
        self.assertEqual(len(events), 2)
        self.assertEqual([event["event_type"] for event in events],
                         ["workflow_started", "workflow_completed"])
        serialized = json.dumps(events)
        self.assertNotIn("secret", serialized)
        self.assertNotIn(session, serialized)
        self.assertNotIn(T._session_key(session), serialized)

    def test_unrelated_claude_skill_is_not_counted(self):
        self.link("claude-code")
        payload = {"hook_event_name": "PreToolUse", "session_id": "s1",
                   "tool_input": {"skill": "some-other-plugin:review"}}
        with patch.object(sys, "stdin", io.StringIO(json.dumps(payload))):
            T.claude_hook()
        self.assertEqual(T._queue_events(), [])

    def test_unlinked_claude_skill_is_denied_with_dashboard_recovery(self):
        payload = {"hook_event_name": "PreToolUse", "session_id": "s1",
                   "tool_input": {"skill": "chatdata:root-cause"}}
        output = io.StringIO()
        with patch.object(sys, "stdin", io.StringIO(json.dumps(payload))), \
             patch.object(sys, "stdout", output):
            T.claude_hook()
        response = json.loads(output.getvalue())
        self.assertEqual(response["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("verified dashboard email", response["systemMessage"])
        self.assertIn("getchatdata.com/dashboard", response["systemMessage"])
        self.assertFalse(T.paths()["queue"].exists())

    def test_unlinked_direct_command_instructs_claude_to_stop(self):
        payload = {"hook_event_name": "UserPromptExpansion", "session_id": "s1",
                   "command_name": "chatdata:sql-review"}
        output = io.StringIO()
        with patch.object(sys, "stdin", io.StringIO(json.dumps(payload))), \
             patch.object(sys, "stdout", output):
            T.claude_hook()
        response = json.loads(output.getvalue())
        self.assertIn("Stop before reading user data", response["systemMessage"])
        self.assertNotIn("hookSpecificOutput", response)

    def test_statusline_replaces_existing_command_and_explicit_restore_is_exact(self):
        original = {"type": "command", "command": "printf 'WOZ saved'", "padding": 2}
        self.settings.parent.mkdir(parents=True)
        self.settings.write_text(json.dumps({"statusLine": original, "theme": "dark"}))
        enabled = T.install_statusline()
        current = json.loads(self.settings.read_text())
        self.assertTrue(enabled["preserved_existing"])
        self.assertNotEqual(current["statusLine"]["command"], original["command"])
        self.link("claude-code")
        T._write_json(T.paths()["summary"], SUMMARY)
        completed = subprocess.run([sys.executable, str(T.paths()["statusline"])], input="{}",
                                   text=True, capture_output=True, check=True,
                                   env={**os.environ, "CHATDATA_HOME": str(T.paths()["root"])})
        self.assertNotIn("WOZ saved", completed.stdout)
        self.assertIn("1.2h est. saved", completed.stdout)
        self.assertIn("$187.50 est. value", completed.stdout)
        result = T.restore_statusline()
        restored = json.loads(self.settings.read_text())
        self.assertTrue(result["restored"])
        self.assertEqual(restored, {"statusLine": original, "theme": "dark"})

    def test_disconnect_preserves_summary_and_requires_dashboard_revoke(self):
        self.link()
        T._write_json(T.paths()["summary"], SUMMARY)
        result = T.disconnect()
        self.assertTrue(result["dashboard_revoke_required"])
        self.assertFalse(result["server_token_revoked"])
        self.assertTrue(T.paths()["summary"].exists())
        self.assertIsNone(T._config())

    def test_disconnect_does_not_change_independent_statusline(self):
        self.settings.parent.mkdir(parents=True)
        self.settings.write_text(json.dumps({"statusLine": {"type": "command", "command": "old"}}))
        T.install_statusline()
        changed = {"type": "command", "command": "new-user-command"}
        self.settings.write_text(json.dumps({"statusLine": changed}))
        result = T.disconnect()
        self.assertEqual(json.loads(self.settings.read_text())["statusLine"], changed)
        self.assertEqual(result["claude_statusline"]["statusline"], "independent")
        self.assertTrue(T.paths()["statusline_backup"].exists())


if __name__ == "__main__":
    unittest.main()
