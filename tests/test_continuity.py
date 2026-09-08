import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'plugins/chatdata'

class ContinuityTests(unittest.TestCase):
    def test_session_context_reestablishes_record_scope_without_echoing_input(self):
        for source in ('startup', 'compact', 'resume'):
            result = subprocess.run(['node', str(ROOT / 'scripts/session-start.js')],
                input=json.dumps({'source': source, 'transcript_path': 'PRIVATE_PATH', 'prompt': 'PRIVATE_PROMPT'}),
                text=True, capture_output=True, check=True)
            output = json.loads(result.stdout)
            context = output['hookSpecificOutput']['additionalContext']
            self.assertIn('If the path was lost, ask for it', context)
            self.assertIn('/chatdata:help', context)
            self.assertNotIn('PRIVATE_', result.stdout)

    def test_compaction_inherits_context_and_failure_uses_separate_hook(self):
        hooks = json.loads((ROOT / 'hooks/hooks.json').read_text())['hooks']
        self.assertTrue(any('matcher' not in group for group in hooks['SessionStart']))
        failure = hooks['StopFailure'][0]['hooks'][0]
        self.assertIn('claude-hook', failure['args'])
        self.assertNotIn('PreCompact', hooks)
