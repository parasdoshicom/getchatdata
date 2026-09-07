#!/usr/bin/env python3
"""Verify the local ChatData bundle with synthetic calculations; no network or writes."""
import json
from pathlib import Path
import subprocess
import sys


def check_bundle(root=None):
    root = Path(root) if root else Path(__file__).resolve().parents[1]
    info = json.loads((root / 'scripts/package-info.json').read_text())
    checks = []

    def run(name, args, verify, expected):
        result = subprocess.run([sys.executable, str(root / 'scripts/analyze.py')] + args,
                                capture_output=True, text=True, timeout=15)
        if result.returncode:
            raise ValueError(name + ': ' + (result.stderr.strip() or 'helper failed'))
        output = json.loads(result.stdout)
        if not verify(output):
            raise ValueError(name + ': calculated result does not match the bundled fixture')
        checks.append({'name': name, 'status': 'passed', 'expected': expected, 'result': output})

    run('Customer mix', ['decompose', str(root / 'examples/mix-shift.csv')],
        lambda x: abs(x['change_pp'] + 9) < 1e-9 and abs(x['mix_pp'] + 9) < 1e-9
        and abs(x['within_pp']) < 1e-9, '17% to 8%; all -9 percentage points from mix')
    run('Ordered funnel', ['funnel', str(root / 'examples/funnel.csv'), '--steps', 'visit',
        'signup', 'purchase', '--as-of', '2026-01-05T00:00:00Z', '--window-hours', '48'],
        lambda x: [s['users'] for s in x['steps']] == [3, 2, 1]
        and x['excluded_immature_users'] == 1 and x['duplicate_events_removed'] == 1,
        '3 visits, 2 signups, 1 purchase; one immature user excluded and one duplicate removed')
    run('Invalid experiment assignment', ['experiment', '--control-n', '1000',
        '--control-success', '100', '--treatment-n', '1500', '--treatment-success', '300'],
        lambda x: x['result'] == 'blocked_srm', 'Withhold winner despite apparent 10% to 20% lift')
    return {'status': 'passed', 'name': info['name'], 'version': info['version'],
            'python': sys.version.split()[0], 'synthetic': True, 'checks': checks,
            'scope': 'Local bundled helpers only. Client skill discovery and connected data are not verified by this check.',
            'next_prompt': 'Use ChatData to analyze the bundled mix-shift example. Run the calculation, explain what changed, and save an analysis record in analysis/chatdata-first-run/.',
            'reuse_prompt': 'Read analysis/chatdata-first-run/ before continuing. Recheck source freshness and definitions before reusing the answer.'}


def main():
    try:
        print(json.dumps(check_bundle(), indent=2))
        return 0
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
        print(json.dumps({'status': 'failed', 'error': str(error),
                          'next_step': 'Refresh the ChatData package and rerun. Do not call setup complete.'}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
