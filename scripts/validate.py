#!/usr/bin/env python3
"""Check public-package manifests, skill links, and release consistency offline."""
import json
from pathlib import Path
import re

root=Path(__file__).resolve().parents[1]; plugin=root/'plugins/chatdata'
claude=json.loads((plugin/'.claude-plugin/plugin.json').read_text())
codex=json.loads((plugin/'.codex-plugin/plugin.json').read_text())
assert claude['name']==codex['name']=='chatdata'
assert claude['version']==codex['version']==json.loads((plugin/'scripts/package-info.json').read_text())['version']
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
            assert (skill.parent/link).is_file(),f'Broken link: {skill}: {link}'
for file in root.rglob('*.md'):
    if '.git' in file.parts: continue
    for link in re.findall(r'\]\(([^)]+)\)',file.read_text()):
        if not link.startswith(('https://','http://','mailto:','#')):
            assert (file.parent/link.split('#')[0]).exists(),f'Broken documentation link: {file}: {link}'
assert (root/'LICENSE').read_text()==(plugin/'LICENSE').read_text()
assert not (plugin/'.mcp.json').exists(),'Free core must not require hosted MCP'
print(f'Validated {len(skills)} skills, local links, manifests, MIT license and offline core.')
