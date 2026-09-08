import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_analysis import P, load


T = load("telemetry_interrupted_workflow", P / "scripts/telemetry.py")
TOKEN = "cdi_" + "a" * 43


class InterruptedWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="chatdata-interrupted-")
        self.root = Path(self.tmp.name)
        self.env = patch.dict(os.environ, {"CHATDATA_HOME": str(self.root / "data")})
        self.env.start()
        T._write_json(T.paths()["config"], {
            "consent_version": T.CONSENT_VERSION,
            "installations": {
                "claude-code": {
                    "token": TOKEN,
                    "connected_at": "2026-09-07T20:00:00Z",
                }
            },
        })

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def run_hook(self, payload):
        with patch.object(sys, "stdin", io.StringIO(json.dumps(payload))):
            T.claude_hook()

    def test_failed_turn_is_not_completed_and_next_invocation_starts_fresh(self):
        session = "private-session-value"
        self.run_hook({
            "hook_event_name": "PreToolUse",
            "session_id": session,
            "tool_input": {"skill": "chatdata:root-cause"},
        })
        first_workflow_id = T._queue_events()[0]["workflow_id"]

        self.run_hook({
            "hook_event_name": "StopFailure",
            "session_id": session,
            "error": "private failure detail",
            "prompt": "private business question",
        })
        with patch.object(T, "flush", return_value={}) as flush:
            self.run_hook({
                "hook_event_name": "Stop",
                "session_id": session,
                "last_assistant_message": "private partial answer",
            })
        flush.assert_called_once_with(silent=True)

        events_after_failure = T._queue_events()
        self.assertEqual([event["event_type"] for event in events_after_failure],
                         ["workflow_started"])
        self.assertEqual(T._read_json(T.paths()["state"], {})["active"], {})

        self.run_hook({
            "hook_event_name": "PreToolUse",
            "session_id": session,
            "tool_input": {"skill": "chatdata:root-cause"},
        })
        events = T._queue_events()
        self.assertEqual([event["event_type"] for event in events],
                         ["workflow_started", "workflow_started"])
        self.assertNotEqual(events[1]["workflow_id"], first_workflow_id)
        self.assertFalse(any(event["event_type"] == "workflow_completed" for event in events))

        serialized = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (T.paths()["queue"], T.paths()["state"])
        )
        for private_value in (
            session,
            "private failure detail",
            "private business question",
            "private partial answer",
        ):
            self.assertNotIn(private_value, serialized)


if __name__ == "__main__":
    unittest.main()
