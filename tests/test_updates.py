import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_analysis import P, load


U = load("update_check", P / "scripts/update-check.py")
T = load("telemetry_update_paths", P / "scripts/telemetry.py")


class FakeResponse:
    def __init__(self, body):
        self.body = body
        self.read_size = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, size):
        self.read_size = size
        return self.body


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="chatdata-update-")
        self.root = Path(self.tmp.name) / "chatdata"
        self.settings = Path(self.tmp.name) / "claude" / "settings.json"
        self.env = patch.dict(os.environ, {
            "CHATDATA_HOME": str(self.root),
            "CHATDATA_CLAUDE_SETTINGS": str(self.settings),
        }, clear=False)
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_newer_release_returns_user_visible_notice(self):
        with patch.object(U, "_installed_version", return_value="1.3.0"), \
             patch.object(U, "_fetch_latest", return_value="1.4.0"):
            result = U.check_for_update(now=1000)
            output = U._hook_output()
        self.assertTrue(result["update_available"])
        self.assertEqual(result["latest_version"], "1.4.0")
        self.assertIn("ChatData 1.4.0 is available", output["systemMessage"])
        self.assertIn("/chatdata:update", output["systemMessage"])
        self.assertEqual(U._cache_path().stat().st_mode & 0o777, 0o600)

    def test_current_and_older_release_are_quiet(self):
        for latest in ("1.3.0", "1.2.9"):
            with self.subTest(latest=latest):
                U._cache_path().unlink(missing_ok=True)
                with patch.object(U, "_installed_version", return_value="1.3.0"), \
                     patch.object(U, "_fetch_latest", return_value=latest):
                    result = U.check_for_update(now=1000)
                self.assertFalse(result["update_available"])
                with patch.object(U, "check_for_update", return_value=result):
                    self.assertEqual(U._hook_output(), {})

    def test_strict_stable_semver(self):
        accepted = {"1.2.3": "1.2.3", "v10.20.30": "10.20.30", "0.0.0": "0.0.0"}
        for raw, normalized in accepted.items():
            self.assertEqual(U._normalize_version(raw), normalized)
        for raw in ("1.2", "1.2.3-beta", "1.2.3+build", "01.2.3", "v1.2.3.4",
                    "999999999999999999999.2.3", "latest", 123):
            self.assertIsNone(U._normalize_version(raw))

    def test_invalid_oversize_and_offline_responses_are_quiet(self):
        cases = (
            FakeResponse(b"not json"),
            FakeResponse(json.dumps({"draft": False, "prerelease": False,
                                     "tag_name": "1.4.0-beta"}).encode()),
            FakeResponse(b"x" * (U.MAX_RESPONSE_BYTES + 1)),
        )
        for response in cases:
            with self.subTest(size=len(response.body)), patch.object(U, "urlopen", return_value=response):
                self.assertIsNone(U._fetch_latest())
                self.assertEqual(response.read_size, U.MAX_RESPONSE_BYTES + 1)
        with patch.object(U, "urlopen", side_effect=U.URLError("private network detail")):
            self.assertIsNone(U._fetch_latest())

    def test_cache_limits_network_to_once_per_day_including_failure(self):
        with patch.object(U, "_installed_version", return_value="1.3.0"), \
             patch.object(U, "_fetch_latest", return_value=None) as fetch:
            first = U.check_for_update(now=1000)
            second = U.check_for_update(now=2000)
            third = U.check_for_update(now=1000 + U.CACHE_SECONDS + 1)
        self.assertEqual(fetch.call_count, 2)
        self.assertIsNone(first["latest_version"])
        self.assertEqual(second["checked_at_epoch"], 1000)
        self.assertEqual(third["checked_at_epoch"], 1000 + U.CACHE_SECONDS + 1)

    def test_disabled_check_makes_no_network_request_or_cache(self):
        with patch.dict(os.environ, {"CHATDATA_UPDATE_CHECK": "0"}), \
             patch.object(U, "refresh_owned_statusline", return_value=False), \
             patch.object(U, "_fetch_latest") as fetch:
            self.assertIsNone(U.check_for_update(now=1000))
        fetch.assert_not_called()
        self.assertFalse(U._cache_path().exists())

    def test_hook_is_quiet_for_cache_write_error_and_worker_timeout(self):
        with patch.object(U, "_installed_version", return_value="1.3.0"), \
             patch.object(U, "_write_cache", side_effect=OSError("private path detail")), \
             patch.object(U, "_fetch_latest") as fetch:
            self.assertEqual(U._hook_output(), {})
        fetch.assert_not_called()
        with patch.object(U.subprocess, "run", side_effect=U.subprocess.TimeoutExpired("worker", 1.6)):
            self.assertEqual(U._run_hook_worker(), {})

    def test_timed_out_attempt_is_cached_before_network_and_backs_off(self):
        with patch.object(U, "_installed_version", return_value="1.3.0"), \
             patch.object(U, "_fetch_latest", side_effect=TimeoutError("slow response")):
            first = U.check_for_update(now=1000)
        self.assertEqual(first["checked_at_epoch"], 1000)
        self.assertIsNone(first["latest_version"])
        with patch.object(U, "_installed_version", return_value="1.3.0"), \
             patch.object(U, "_fetch_latest") as fetch:
            second = U.check_for_update(now=2000)
        fetch.assert_not_called()
        self.assertEqual(second["checked_at_epoch"], 1000)

    def test_malformed_cache_is_ignored_without_a_traceback(self):
        self.root.mkdir(parents=True)
        U._cache_path().write_text("[not a cache object]")
        with patch.object(U, "_installed_version", return_value="1.3.0"), \
             patch.object(U, "_fetch_latest", return_value=None):
            self.assertEqual(U._hook_output(), {})

    def _install_old_owned_wrapper(self):
        self.root.mkdir(parents=True)
        destination = self.root / "claude-statusline.py"
        old = U.WRAPPER_MARKERS[0] + b"\n# prior ChatData wrapper\n"
        destination.write_bytes(old)
        command = f'"{sys.executable}" "{destination}"'
        installed_value = {"type": "command", "command": command}
        (self.root / "claude-statusline-backup.json").write_text(json.dumps({
            "wrapper_command": command,
            "installed_value": installed_value,
        }))
        self.settings.parent.mkdir(parents=True)
        self.settings.write_text(json.dumps({"statusLine": installed_value}))
        return destination, old

    def test_refreshes_only_the_statusline_wrapper_chatdata_still_owns(self):
        destination, old = self._install_old_owned_wrapper()
        self.assertTrue(U.refresh_owned_statusline())
        self.assertEqual(destination.read_bytes(), (P / "scripts/claude-statusline.py").read_bytes())

        destination.write_bytes(old)
        self.settings.write_text(json.dumps({
            "statusLine": {"type": "command", "command": "printf 'user changed this'"}
        }))
        self.assertFalse(U.refresh_owned_statusline())
        self.assertEqual(destination.read_bytes(), old)

    def test_statusline_refresh_honors_isolated_claude_config_dir(self):
        with patch.dict(os.environ, {"CHATDATA_CLAUDE_SETTINGS": ""}), \
             patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(Path(self.tmp.name) / "isolated")}), \
             patch("pathlib.Path.home", return_value=Path(self.tmp.name) / "global-home"):
            self.assertEqual(U._settings_path(), Path(self.tmp.name) / "isolated" / "settings.json")

    def test_telemetry_statusline_install_honors_isolated_claude_config_dir(self):
        isolated = Path(self.tmp.name) / "isolated"
        with patch.dict(os.environ, {
                "CHATDATA_CLAUDE_SETTINGS": "", "CLAUDE_CONFIG_DIR": str(isolated)}):
            self.assertEqual(T._claude_settings_path(), isolated / "settings.json")

    def test_statusline_appends_cached_notice(self):
        self.root.mkdir(parents=True)
        (self.root / "update-check.json").write_text(json.dumps({
            "schema_version": 1,
            "checked_at_epoch": 1000,
            "installed_version": "1.3.0",
            "latest_version": "1.4.0",
            "update_available": True,
        }))
        completed = subprocess.run(
            [sys.executable, str(P / "scripts/claude-statusline.py")],
            input="{}", text=True, capture_output=True, check=True,
            env={**os.environ, "CHATDATA_HOME": str(self.root)},
        )
        self.assertIn("update 1.4.0 available · /chatdata:update", completed.stdout)

        (self.root / "update-check.json").write_text("[]")
        malformed = subprocess.run(
            [sys.executable, str(P / "scripts/claude-statusline.py")],
            input="{}", text=True, capture_output=True, check=True,
            env={**os.environ, "CHATDATA_HOME": str(self.root)},
        )
        self.assertNotIn("update", malformed.stdout)

        (self.root / "update-check.json").write_text(json.dumps({
            "schema_version": 1, "checked_at_epoch": 1000,
            "installed_version": "1.3.0", "latest_version": "1.4.0",
            "update_available": True,
        }))
        disabled = subprocess.run(
            [sys.executable, str(P / "scripts/claude-statusline.py")],
            input="{}", text=True, capture_output=True, check=True,
            env={**os.environ, "CHATDATA_HOME": str(self.root), "CHATDATA_UPDATE_CHECK": "0"},
        )
        self.assertNotIn("update", disabled.stdout)

        (self.root / "individual-telemetry-summary.json").write_text(json.dumps({
            "estimates_configured": True,
            "estimated_hours_saved": "bad",
            "estimated_value_usd": "also bad",
        }))
        malformed_summary = subprocess.run(
            [sys.executable, str(P / "scripts/claude-statusline.py")],
            input="{}", text=True, capture_output=True, check=True,
            env={**os.environ, "CHATDATA_HOME": str(self.root)},
        )
        self.assertIn("usage estimates unavailable", malformed_summary.stdout)

        (self.root / "individual-telemetry-summary.json").write_text(json.dumps({
            "estimates_configured": True,
            "estimated_hours_saved": 999,
            "estimated_value_usd": 999,
            "padding": "x" * (17 * 1024),
        }))
        oversized_summary = subprocess.run(
            [sys.executable, str(P / "scripts/claude-statusline.py")],
            input="{}", text=True, capture_output=True, check=True,
            env={**os.environ, "CHATDATA_HOME": str(self.root)},
        )
        self.assertNotIn("999", oversized_summary.stdout)
        self.assertIn("set your baseline", oversized_summary.stdout)

    def test_prior_statusline_is_never_executed_or_displayed(self):
        self.root.mkdir(parents=True)
        side_effect = Path(self.tmp.name) / "prior-ran"
        prior_command = f'touch "{side_effect}"; printf WOZ_SENTINEL'
        (self.root / "claude-statusline-backup.json").write_text(json.dumps({
            "value": {"type": "command", "command": prior_command}
        }))
        completed = subprocess.run(
            [sys.executable, str(P / "scripts/claude-statusline.py")],
            input="{}", text=True, capture_output=True, check=True, timeout=5,
            env={**os.environ, "CHATDATA_HOME": str(self.root)},
        )
        self.assertIn("ChatData", completed.stdout)
        self.assertNotIn("WOZ_SENTINEL", completed.stdout)
        self.assertFalse(side_effect.exists())

    def test_hook_and_manual_update_command_are_bounded(self):
        hooks = json.loads((P / "hooks/hooks.json").read_text())["hooks"]["SessionStart"][0]["hooks"]
        self.assertEqual(hooks[2]["args"][-2:], ["flush", "--silent"])
        update_hook = hooks[3]
        self.assertTrue(update_hook["args"][-2].endswith("/scripts/update-check.py"))
        self.assertEqual(update_hook["args"][-1], "hook")
        self.assertLessEqual(update_hook["timeout"], 2)
        self.assertNotIn("async", update_hook)

        command = (P / "commands/update.md").read_text()
        self.assertIn("disable-model-invocation: true", command)
        self.assertIn("Claude Code only", command)
        self.assertIn("claude plugin marketplace list --json", command)
        self.assertIn("`source` is `github`", command)
        self.assertIn("`repo` is exactly `parasdoshicom/getchatdata`", command)
        self.assertIn('git -C "<verified absolute installLocation>" remote get-url origin', command)
        self.assertIn("If any matching entry has `managed` or another unrecognized scope, stop", command)
        self.assertIn("claude plugin marketplace update chatdata-free", command)
        self.assertIn("claude plugin update chatdata@chatdata-free --scope <scope>", command)
        self.assertIn("Require exactly one `chatdata@chatdata-free` entry for every retained scope", command)
        self.assertIn("Do not download or execute code with `curl`", command)
        self.assertIn("do not add `--yes`", command)


if __name__ == "__main__":
    unittest.main()
