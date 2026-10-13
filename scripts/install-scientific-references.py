#!/usr/bin/env python3
"""Fetch reference-only skills directly from upstream after rights are obtained."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

central = Path(__file__).resolve().parents[1]
source = json.loads((central / 'upstream-references/scientific-agent-skills.json').read_text())
names = {item['name']: item for item in source['skills']}
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--permission-obtained', action='store_true', help='Confirm applicable copying/use rights have been obtained; does not grant rights')
parser.add_argument('--skill', choices=sorted(names), action='append')
parser.add_argument('--destination', type=Path, default=Path.home()/'.agents/skills')
parser.add_argument('--gh', help='Path to GitHub CLI v2.90+ if it is not on PATH')
args = parser.parse_args()
if not args.permission_obtained:
    parser.error('No download performed. Review the individual licenses and obtain applicable rights before using --permission-obtained.')
selected = sorted(set(args.skill or names))
dest = args.destination.expanduser().absolute()
if dest.is_relative_to(central.resolve()):
    parser.error('Reference-only content must remain outside the distributed central repository.')
if dest.is_symlink() or dest.parent.is_symlink():
    parser.error('Linked installation roots are refused.')
for name in selected:
    if (dest/name).exists() or (dest/name).is_symlink():
        parser.error('Existing skill will not be overwritten: '+name)
gh = args.gh or shutil.which('gh')
if not gh:
    parser.error('GitHub CLI v2.90+ is required; use --gh for its executable path.')
dest.parent.mkdir(parents=True, exist_ok=True)
activated = []
with tempfile.TemporaryDirectory(prefix='.scientific-reference-review-', dir=dest.parent) as temporary:
    stage = Path(temporary)/'skills'
    for name in selected:
        subprocess.run([gh, 'skill', 'install', 'K-Dense-AI/scientific-agent-skills', names[name]['path'],
                        '--pin', source['commit'], '--agent', 'codex', '--dir', str(stage)], check=True, timeout=180)
    for name in selected:
        path = stage/name
        if not (path/'SKILL.md').is_file() or any(p.is_symlink() for p in path.rglob('*')):
            raise RuntimeError('Invalid upstream skill directory: '+name)
        (path/'UPSTREAM.json').write_text(json.dumps({'url': source['repository'], 'commit': source['commit'],
            'license': names[name]['declared_license'], 'reference_only': True}, indent=2)+'\n')
    dest.mkdir(exist_ok=True)
    try:
        for name in selected:
            if (dest/name).exists() or (dest/name).is_symlink():
                raise RuntimeError('Destination appeared during download: '+name)
            (stage/name).rename(dest/name)
            activated.append(name)
    except BaseException:
        for name in reversed(activated):
            (dest/name).rename(stage/name)
        raise
print('Installed directly from pinned upstream:', ', '.join(selected))
print('No research code executed. These directories are not part of central Git synchronization; do not redistribute without rights.')
