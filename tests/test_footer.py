import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from test_analysis import P, load


F = load("chatdata_footer", P / "scripts/footer.py")


class FooterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="chatdata-footer-")
        self.base = Path(self.tmp.name)
        self.home = self.base / "chatdata"
        self.settings = self.base / "claude" / "settings.json"
        self.env = patch.dict(os.environ, {
            "CHATDATA_HOME": str(self.home),
            "CHATDATA_CLAUDE_SETTINGS": str(self.settings),
        })
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def _write_settings(self, value):
        self.settings.parent.mkdir(parents=True, exist_ok=True)
        self.settings.write_text(json.dumps(value), encoding="utf-8")

    def test_first_session_replaces_woz_without_telemetry_and_restores_exactly(self):
        prior = {"type": "command", "command": "printf WOZ_SENTINEL", "padding": 2}
        original = {"statusLine": prior, "theme": "dark", "env": {"A": "B"}}
        self._write_settings(original)

        result = F.session_start()
        current = json.loads(self.settings.read_text())
        backup = json.loads((self.home / "claude-statusline-backup.json").read_text())
        self.assertEqual(result["statusline"], "enabled")
        self.assertEqual(current["theme"], "dark")
        self.assertEqual(current["env"], {"A": "B"})
        self.assertNotIn("WOZ", current["statusLine"]["command"])
        self.assertEqual(backup["value"], prior)
        self.assertFalse((self.home / "individual-telemetry.json").exists())

        output = subprocess.run(
            [sys.executable, str(self.home / "claude-statusline.py")],
            input="{}", text=True, capture_output=True, check=True,
            env={**os.environ, "CHATDATA_HOME": str(self.home)},
        ).stdout
        self.assertIn("ChatData", output)
        self.assertNotIn("WOZ", output)

        restored = F.restore()
        self.assertTrue(restored["restored"])
        self.assertEqual(json.loads(self.settings.read_text()), original)
        self.assertEqual(F.session_start()["statusline"], "restored")
        self.assertEqual(json.loads(self.settings.read_text()), original)

    def test_later_user_footer_is_never_overwritten(self):
        self._write_settings({"theme": "light"})
        F.session_start()
        selected = {"type": "command", "command": "printf USER_CHOICE"}
        self._write_settings({"theme": "light", "statusLine": selected})
        self.assertEqual(F.session_start()["statusline"], "user_selected")
        self.assertEqual(F.session_start()["statusline"], "user_selected")
        self.assertEqual(json.loads(self.settings.read_text())["statusLine"], selected)

    def test_explicit_enable_after_restore_saves_new_current_footer(self):
        old = {"type": "command", "command": "printf old"}
        self._write_settings({"statusLine": old})
        F.session_start()
        F.restore()
        newer = {"type": "command", "command": "printf newer"}
        self._write_settings({"statusLine": newer})
        self.assertEqual(F.enable()["statusline"], "enabled")
        self.assertEqual(F.restore()["statusline"], "restored")
        self.assertEqual(json.loads(self.settings.read_text())["statusLine"], newer)

    def test_malformed_oversize_and_symlink_settings_fail_closed(self):
        self.settings.parent.mkdir(parents=True)
        for raw in ("[not-an-object]", "{" + "x" * (F.MAX_JSON_BYTES + 1)):
            self.settings.unlink(missing_ok=True)
            self.settings.write_text(raw)
            before = self.settings.read_bytes()
            self.assertEqual(F.session_start()["statusline"], "settings_unreadable")
            self.assertEqual(self.settings.read_bytes(), before)
        target = self.base / "target.json"
        target.write_text(json.dumps({"statusLine": {"command": "keep"}}))
        self.settings.unlink()
        self.settings.symlink_to(target)
        self.assertEqual(F.session_start()["statusline"], "settings_unreadable")
        self.assertEqual(json.loads(target.read_text())["statusLine"]["command"], "keep")

    def test_settings_drift_preserves_unrelated_external_change(self):
        self._write_settings({"theme": "old"})
        real_check = F._write_settings_if_unchanged

        def drift_then_check(path, value, snapshot):
            self._write_settings({"theme": "changed-elsewhere", "custom": True})
            return real_check(path, value, snapshot)

        with patch.object(F, "_write_settings_if_unchanged", side_effect=drift_then_check):
            with self.assertRaisesRegex(RuntimeError, "changed while"):
                F.enable()
        self.assertEqual(json.loads(self.settings.read_text()),
                         {"theme": "changed-elsewhere", "custom": True})

    def test_two_concurrent_session_starts_converge(self):
        self._write_settings({"theme": "dark"})
        env = {**os.environ, "CHATDATA_HOME": str(self.home),
               "CHATDATA_CLAUDE_SETTINGS": str(self.settings)}
        command = [sys.executable, str(P / "scripts/footer.py"), "session-start"]
        first = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 text=True, env=env)
        second = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  text=True, env=env)
        outputs = [first.communicate(timeout=4), second.communicate(timeout=4)]
        self.assertEqual([first.returncode, second.returncode], [0, 0])
        self.assertEqual([item[0].strip() for item in outputs], ["{}", "{}"])
        settings = json.loads(self.settings.read_text())
        backup = json.loads((self.home / "claude-statusline-backup.json").read_text())
        self.assertEqual(settings["theme"], "dark")
        self.assertEqual(settings["statusLine"], backup["installed_value"])
        self.assertFalse((self.home / ".claude-footer.lock").exists())

    def test_invalid_lock_shape_fails_closed_without_spinning(self):
        self.home.mkdir(parents=True)
        lock = self.home / ".claude-footer.lock"
        lock.write_text("not a lock directory")
        started = time.monotonic()
        with self.assertRaisesRegex(RuntimeError, "not a directory"):
            F.enable()
        self.assertLess(time.monotonic() - started, 0.2)
        lock.unlink()
        target = self.base / "lock-target"
        target.mkdir()
        lock.symlink_to(target)
        with self.assertRaisesRegex(RuntimeError, "not a directory"):
            F.enable()

    def test_honors_claude_config_dir(self):
        isolated = self.base / "isolated"
        with patch.dict(os.environ, {"CHATDATA_CLAUDE_SETTINGS": "",
                                     "CLAUDE_CONFIG_DIR": str(isolated)}):
            self.assertEqual(F._settings_path(), isolated / "settings.json")

    def test_footer_command_is_explicit_and_telemetry_independent(self):
        command = (P / "commands/footer.md").read_text()
        self.assertIn("disable-model-invocation: true", command)
        self.assertIn("<enable|restore|status>", command)
        self.assertIn('footer.py" $ARGUMENTS', command)
        self.assertIn("None of these actions enables or changes usage reporting", command)


if __name__ == "__main__":
    unittest.main()
