#!/usr/bin/env python3
"""Install ChatData skills into one project, without changing global client settings."""
import argparse
import json
import shutil
import tempfile
from pathlib import Path


def install(client, project, update=False):
    project=Path(project).resolve()
    if not project.is_dir():
        raise ValueError('Project must be an existing directory')
    source=Path(__file__).resolve().parents[1]/'plugins/chatdata'
    target=project/('.cursor/skills' if client=='cursor' else '.agents/skills')
    names=sorted(p.name for p in (source/'skills').iterdir() if (p/'SKILL.md').is_file())
    destinations=[target/('chatdata-'+name) for name in names]
    conflicts=[str(p) for p in destinations if p.exists() or p.is_symlink()]
    if any(p.is_symlink() for p in [target.parent, target] + destinations):
        raise ValueError('Symlinked install destinations are preserved; choose a project with local skill folders.')
    if conflicts and not update:
        raise ValueError('Existing skill folders preserved. Rerun with --update to back them up and replace them: '+', '.join(conflicts))
    backup = None
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
        lock = target.parent / '.chatdata-install.lock'
        try:
            lock.mkdir()
        except FileExistsError:
            raise ValueError('Another ChatData install is in progress. If it stopped, inspect and remove only '+str(lock)) from None
        written=[]
        moved=[]
        try:
            # Recheck after locking; never replace an install that raced the first check.
            current=[p for p in destinations if p.exists() or p.is_symlink()]
            if any(p.is_symlink() for p in current):
                raise ValueError('Symlinked skill folders are preserved.')
            if current and not update:
                raise ValueError('Existing skill folders preserved. Use --update to back them up and replace them.')
            if current:
                backup_parent=target.parent/'chatdata-backups'
                if backup_parent.is_symlink():
                    raise ValueError('Symlinked backup folder is preserved.')
                backup_parent.mkdir(exist_ok=True)
                backup=Path(tempfile.mkdtemp(prefix='before-update-',dir=backup_parent))
                for dest in current:
                    dest.rename(backup/dest.name)
                    moved.append(dest)
            for dest in destinations:
                dest.mkdir()  # Refuse a competing destination before recording ownership.
                written.append(dest)
                shutil.copytree(staging/dest.name,dest,dirs_exist_ok=True)
        except Exception:
            # Remove only folders created by this install, then restore the originals.
            for dest in written:
                shutil.rmtree(dest)
            for dest in moved:
                if not dest.exists():
                    (backup/dest.name).rename(dest)
            raise
        finally:
            lock.rmdir()
    return {'client':client,'skills':len(names),'path':str(target),'backup':str(backup) if backup else None,'version':json.loads((source/'scripts/package-info.json').read_text())['version'],'first_prompt':'Use ChatData to check setup and run its synthetic examples.','restart':'Start a new agent session to refresh skill discovery.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client',choices=['cursor','codex'],required=True)
    parser.add_argument('--project',required=True)
    parser.add_argument('--update',action='store_true',help='Back up existing ChatData skill folders before replacing them; preserves unrelated skills.')
    args=parser.parse_args()
    try:
        print(json.dumps(install(args.client,args.project,args.update),indent=2))
    except (ValueError,OSError) as error:
        parser.exit(2,str(error)+'\n')
