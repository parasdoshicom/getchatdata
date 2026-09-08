import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_analysis import P, load


L = load("local_inventory", P / "scripts/local_inventory.py")


class LocalInventoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="chatdata-inventory-")
        self.root = (Path(self.tmp.name) / "project").resolve()
        self.root.mkdir()
        self.now = 2_000_000_000

    def tearDown(self):
        self.tmp.cleanup()

    def touch(self, relative, content="data", age_days=0):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        modified = self.now - age_days * 86400
        os.utime(path, (modified, modified))
        return path

    def test_scans_only_supported_recent_metadata_and_labels_mtime(self):
        self.touch("queries/funnel.sql", "select private_customer_data")
        self.touch("analysis/model.ipynb", "not valid json")
        self.touch("notes.md", age_days=31)
        self.touch("image.png")
        result = L.scan(self.root, now=self.now)
        self.assertEqual(result["status"], "complete")
        self.assertEqual([(item["path"], item["kind"]) for item in result["inventory"]], [
            ("analysis/model.ipynb", "notebook"),
            ("queries/funnel.sql", "sql"),
        ])
        self.assertEqual(result["window"]["field"], "filesystem_modified_time")
        self.assertIn("not proof", result["window"]["meaning"])
        self.assertIn("No file was read", result["interpretation"])
        self.assertIn("no network", result["privacy"])

    def test_excludes_sensitive_names_dotdirs_and_dependency_trees(self):
        self.touch("credentials.json")
        self.touch("warehouse-token.yaml")
        self.touch("analysis-config.json")
        self.touch(".env")
        self.touch(".git/history.sql")
        self.touch("chatdata-context/inventory.json")
        self.touch("node_modules/package/report.sql")
        self.touch("safe/configuration-study.py")
        result = L.scan(self.root, now=self.now)
        self.assertEqual([item["path"] for item in result["inventory"]], ["safe/configuration-study.py"])
        self.assertEqual(result["coverage"]["skipped"]["sensitive_names"], 4)
        self.assertEqual(result["coverage"]["skipped"]["excluded_directories"], 3)

    def test_never_follows_file_directory_or_root_symlinks(self):
        outside = Path(self.tmp.name) / "outside"
        outside.mkdir()
        secret = outside / "secret.sql"
        secret.write_text("select secret")
        (self.root / "linked-file.sql").symlink_to(secret)
        (self.root / "linked-dir").symlink_to(outside, target_is_directory=True)
        result = L.scan(self.root, now=self.now)
        self.assertEqual(result["inventory"], [])
        self.assertEqual(result["coverage"]["skipped"]["symlinks"], 2)
        root_link = Path(self.tmp.name) / "project-link"
        root_link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(L.RootRefused, "root is a symlink"):
            L.scan(root_link, now=self.now)

    def test_file_and_directory_limits_make_coverage_incomplete(self):
        for name in ("a.sql", "b.sql", "c.sql"):
            self.touch(name)
        result = L.scan(self.root, now=self.now, max_files=2)
        self.assertEqual(result["status"], "incomplete")
        self.assertFalse(result["coverage"]["complete"])
        self.assertEqual(result["coverage"]["truncated_reasons"], ["file_limit"])
        self.assertLessEqual(len(result["inventory"]), 2)

        for directory in ("one", "two"):
            self.touch(directory + "/query.sql")
        result = L.scan(self.root, now=self.now, max_directories=1)
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["coverage"]["truncated_reasons"], ["directory_limit"])

    def test_permission_errors_are_explicit_and_not_success(self):
        denied = self.root / "denied"
        denied.mkdir()
        original = L.os.scandir

        def selective_scandir(path):
            if Path(path) == denied:
                raise PermissionError("denied")
            return original(path)

        with patch.object(L.os, "scandir", side_effect=selective_scandir):
            result = L.scan(self.root, now=self.now)
        self.assertEqual(result["status"], "incomplete")
        self.assertFalse(result["coverage"]["complete"])
        self.assertEqual(result["coverage"]["errors"], [{"path": "denied", "error": "PermissionError"}])

    def test_refuses_home_filesystem_root_and_user_state(self):
        with patch.object(L.Path, "home", return_value=self.root):
            with self.assertRaisesRegex(L.RootRefused, "home directory"):
                L.scan(self.root, now=self.now)
        with self.assertRaisesRegex(L.RootRefused, "filesystem root"):
            L.scan(Path(self.root.anchor), now=self.now)

        fake_home = Path(self.tmp.name) / "home"
        user_state = fake_home / ".codex" / "tasks"
        user_state.mkdir(parents=True)
        with patch.object(L.Path, "home", return_value=fake_home):
            with self.assertRaisesRegex(L.RootRefused, "user state"):
                L.scan(user_state, now=self.now)

    def test_cli_requires_explicit_root_and_emits_json(self):
        script = P / "scripts/local_inventory.py"
        missing = subprocess.run([sys.executable, str(script), "scan"], capture_output=True, text=True)
        self.assertNotEqual(missing.returncode, 0)
        complete = subprocess.run(
            [sys.executable, str(script), "scan", "--root", str(self.root), "--days", "30"],
            capture_output=True,
            text=True,
            check=True,
        )
        result = json.loads(complete.stdout)
        self.assertTrue(result["coverage"]["complete"])
        self.assertEqual(result["window"]["days"], 30)


if __name__ == "__main__":
    unittest.main()
