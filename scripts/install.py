#!/usr/bin/env python3
"""Install ChatData skills into one project, without changing global client settings."""
import argparse
import json
import shutil
import tempfile
from pathlib import Path


def install(client, project):
    project=Path(project).resolve()
    if not project.is_dir():
        raise ValueError('Project must be an existing directory')
    source=Path(__file__).resolve().parents[1]/'plugins/chatdata'
    target=project/('.cursor/skills' if client=='cursor' else '.agents/skills')
    names=sorted(p.name for p in (source/'skills').iterdir() if (p/'SKILL.md').is_file())
    destinations=[target/('chatdata-'+name) for name in names]
    conflicts=[str(p) for p in destinations if p.exists() or p.is_symlink()]
    if conflicts:
        raise ValueError('Existing skill folders preserved. Remove or move only the ChatData folders you intend to replace: '+', '.join(conflicts))
    # Stage the entire bundle before changing any destination.
    with tempfile.TemporaryDirectory(prefix='chatdata-install-') as temporary:
        staging=Path(temporary)
        for name in names:
            dest=staging/('chatdata-'+name)
            shutil.copytree(source/'skills'/name,dest)
            text=(dest/'SKILL.md').read_text().replace('../../references/','references/').replace('../../scripts/','scripts/')
            text=text.replace('name: '+name+'\n','name: chatdata-'+name+'\n',1)
            (dest/'SKILL.md').write_text(text)
            shutil.copytree(source/'references',dest/'references')
            shutil.copytree(source/'scripts',dest/'scripts',ignore=shutil.ignore_patterns('__pycache__'))
            shutil.copytree(source/'examples',dest/'examples')
        target.mkdir(parents=True,exist_ok=True)
        written=[]
        try:
            for dest in destinations:
                # copytree refuses a concurrent destination; never overwrite another install.
                shutil.copytree(staging/dest.name,dest)
                written.append(dest)
        except Exception:
            for dest in written:
                shutil.rmtree(dest)
            raise
    return {'client':client,'skills':len(names),'path':str(target),'restart':'Start a new agent session to refresh skill discovery.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client',choices=['cursor','codex'],required=True)
    parser.add_argument('--project',required=True)
    args=parser.parse_args()
    try:
        print(json.dumps(install(args.client,args.project),indent=2))
    except (ValueError,OSError) as error:
        parser.exit(2,str(error)+'\n')
