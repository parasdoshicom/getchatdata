#!/usr/bin/env python3
"""Check public-package manifests, skill links, and release consistency offline."""
import json
from pathlib import Path
import re

root=Path(__file__).resolve().parents[1]; plugin=root/'plugins/chatdata'
claude=json.loads((plugin/'.claude-plugin/plugin.json').read_text())
codex=json.loads((plugin/'.codex-plugin/plugin.json').read_text())
marketplace=json.loads((root/'.claude-plugin/marketplace.json').read_text())
assert claude['name']==codex['name']=='chatdata'
assert claude['version']==codex['version']==json.loads((plugin/'scripts/package-info.json').read_text())['version']
assert marketplace['plugins'][0]['version']==claude['version']
assert claude['license']==codex['license']=='MIT'
for file in root.rglob('*.json'):
    if '.git' not in file.parts: json.loads(file.read_text())
skills=list((plugin/'skills').glob('*/SKILL.md'))
assert len(skills)==16
for skill in skills:
    text=skill.read_text()
    assert text.startswith('---\nname: '+skill.parent.name+'\n')
    assert '\ndescription: ' in text
    for link in re.findall(r'\]\(([^)]+)\)',text):
        if not link.startswith(('https://','http://','#')):
            assert (skill.parent/link.split('#')[0]).is_file(),f'Broken link: {skill}: {link}'
for file in root.rglob('*.md'):
    if '.git' in file.parts: continue
    for link in re.findall(r'\]\(([^)]+)\)',file.read_text()):
        if not link.startswith(('https://','http://','mailto:','#')):
            assert (file.parent/link.split('#')[0]).exists(),f'Broken documentation link: {file}: {link}'
assert (root/'LICENSE').read_text()==(plugin/'LICENSE').read_text()
assert not (plugin/'.mcp.json').exists(),'Free core must not require hosted MCP'
assert (plugin/'scripts/telemetry.py').is_file() and (plugin/'scripts/claude-statusline.py').is_file()
for script in ('retention.py', 'join_audit.py', 'duckdb_query.py'):
    assert (plugin/'scripts'/script).is_file(),f'Missing analytical helper: {script}'
for skill in skills:
    assert 'worked-failures.md#' in skill.read_text(),f'Missing worked failure link: {skill}'
enforcement_path=root/'evals/results'/f'enforcement-v{claude["version"]}.json'
assert enforcement_path.is_file(),f'Missing enforcement evidence: {enforcement_path.name}'
enforcement=json.loads(enforcement_path.read_text())
assert enforcement['plugin_version']==claude['version']
assert enforcement['passed']==enforcement['total']==5
assert len(enforcement['cases'])==5 and all(case['passed'] is True for case in enforcement['cases'])
print(f'Validated {len(skills)} skills, local links, manifests, MIT license, analytical helpers and enforcement evidence.')
