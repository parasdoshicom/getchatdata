import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from test_analysis import I, P, load

D = load('doctor', P / 'scripts/doctor.py')


class OnboardingTests(unittest.TestCase):
    def test_doctor_checks_bundled_examples(self):
        result = D.check_bundle()
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(len(result['checks']), 5)
        self.assertIn('not verified', result['scope'])

    def test_installed_doctor_works_from_an_unrelated_directory(self):
        for client, folder in [('codex', '.agents'), ('cursor', '.cursor')]:
            with self.subTest(client=client), tempfile.TemporaryDirectory(prefix='data project ') as tmp:
                I.install(client, tmp)
                script = Path(tmp)/folder/'skills/chatdata-data-science/scripts/doctor.py'
                result = subprocess.run([sys.executable, str(script)], cwd=tmp,
                                        capture_output=True, text=True, check=True)
                self.assertEqual(json.loads(result.stdout)['status'], 'passed')

    def test_update_backs_up_customizations_and_preserves_unrelated_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            I.install('cursor', tmp)
            base = Path(tmp)/'.cursor/skills'
            custom = base/'chatdata-root-cause/my-notes.md'
            custom.write_text('local work')
            other = base/'other-skill'; other.mkdir(); (other/'keep').write_text('keep')
            result = I.install('cursor', tmp, update=True)
            self.assertEqual((Path(result['backup'])/'chatdata-root-cause/my-notes.md').read_text(), 'local work')
            self.assertFalse(custom.exists())
            self.assertEqual((other/'keep').read_text(), 'keep')

    def test_failed_update_restores_original_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            I.install('codex', tmp)
            original = Path(tmp)/'.agents/skills/chatdata-root-cause/custom.md'
            original.write_text('keep my edits')
            copy = I.shutil.copytree
            def broken_copy(source, dest, *args, **kwargs):
                if Path(dest).parent == Path(tmp).resolve()/'.agents/skills':
                    (Path(dest)/'partial').write_text('incomplete')
                    raise OSError('simulated write failure')
                return copy(source, dest, *args, **kwargs)
            with patch.object(I.shutil, 'copytree', side_effect=broken_copy):
                with self.assertRaises(OSError):
                    I.install('codex', tmp, update=True)
            self.assertEqual(original.read_text(), 'keep my edits')
            self.assertEqual(len(list(original.parents[1].glob('chatdata-*/SKILL.md'))), 16)
            self.assertFalse((Path(tmp)/'.agents/.chatdata-install.lock').exists())

    def test_symlink_destination_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as external:
            project = Path(tmp); (project/'.cursor').mkdir()
            (project/'.cursor/skills').symlink_to(external, target_is_directory=True)
            with self.assertRaises(ValueError): I.install('cursor', project, update=True)
            self.assertEqual(list(Path(external).iterdir()), [])

    def test_corrupt_example_fails_instead_of_claiming_setup_passed(self):
        with tempfile.TemporaryDirectory() as tmp:
            I.install('cursor', tmp)
            bundle=Path(tmp)/'.cursor/skills/chatdata-data-science'
            (bundle/'examples/mix-shift.csv').write_text('wrong,columns\n1,2\n')
            with self.assertRaises(ValueError): D.check_bundle(bundle)
