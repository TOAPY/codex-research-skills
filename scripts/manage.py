#!/usr/bin/env python3
"""Cross-platform skill copies with drift checks. No third-party packages required."""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

REPO_DEFAULT = Path(__file__).resolve().parents[1]
SKIP = {'.git', '__pycache__', '.pytest_cache', '.DS_Store', '.venv', 'node_modules'}
STATE_NAME = 'research-skills-state.json'
# OpenAI prefixes must start a token, not the last letters of a BIDS "task-" filename.
SECRET = re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,}|(?<![A-Za-z0-9])sk-(?:proj-)?[A-Za-z0-9_-]{40,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')

def fail(message):
    raise RuntimeError(message)

def git(repo, *args, check=True):
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True)
    if check and result.returncode:
        fail(result.stderr.strip() or 'Git failed: ' + ' '.join(args))
    return result.stdout.strip()

def ignored(path):
    return any(p in SKIP for p in path.parts) or path.suffix in {'.pyc', '.pyo'}

def name_of(skill):
    raw = (skill / 'SKILL.md').read_text(encoding='utf-8')
    if not raw.startswith('---\n') and not raw.startswith('---\r\n'):
        fail(f'Missing YAML frontmatter: {skill}')
    header = raw.split('---', 2)[1]
    match = re.search(r'^name:\s*[\'"]?([a-z0-9-]+)[\'"]?\s*$', header, re.M)
    if not match or not re.search(r'^description:\s*\S', header, re.M):
        fail(f'Invalid name/description: {skill}')
    return match.group(1)

def snapshot(directory):
    if not directory.is_dir() or directory.is_symlink():
        fail(f'Expected an ordinary directory, refusing links: {directory}')
    result = {}
    for path in sorted(directory.rglob('*')):
        rel = path.relative_to(directory)
        if ignored(rel):
            continue
        if path.is_symlink():
            fail(f'Refusing symlink: {path}')
        if path.is_file():
            result[rel.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result

def copy_skill(source, dest):
    def ignore(directory, names):
        return [n for n in names if ignored(Path(n))]
    snapshot(source)  # Validate links and types before copying.
    shutil.copytree(source, dest, ignore=ignore)
    if snapshot(source) != snapshot(dest):
        fail(f'Copy verification failed: {source}')

def skills(repo):
    root = repo / '.agents' / 'skills'
    if not root.is_dir():
        fail(f'No repository skills: {root}')
    found = {p.name: p for p in sorted(root.iterdir()) if p.is_dir() and not p.name.startswith('.')}
    pin_file = repo / 'UPSTREAMS.json'
    if pin_file.is_file():
        pins = json.loads(pin_file.read_text(encoding='utf-8'))
        reference_only = {n for pin in pins.values() for n in pin.get('reference_only', [])}
        blocked = set(found) & reference_only
        if blocked:
            fail('Reference-only licensed content must not be redistributed: ' + ', '.join(sorted(blocked)))
    if not found:
        fail('Repository contains no skills.')
    names = {}
    for dirname, path in found.items():
        if not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', dirname):
            fail(f'Unsafe directory name: {dirname}')
        key = name_of(path)
        if key in names:
            fail(f'Duplicate skill frontmatter name: {key}')
        names[key] = dirname
        snapshot(path)
    return found

def state_path(dest):
    return dest.parent / STATE_NAME

def read_state(dest):
    path = state_path(dest)
    if path.is_symlink():
        fail(f'Refusing linked state file: {path}')
    return json.loads(path.read_text()) if path.exists() else {'format': 1, 'skills': {}}

def save_state(dest, state):
    path = state_path(dest)
    tmp = path.with_suffix('.tmp')
    with tmp.open('x', encoding='utf-8') as handle:
        json.dump(state, handle, indent=2, ensure_ascii=False)
        handle.write('\n')
    os.replace(tmp, path)

@contextlib.contextmanager
def lock(dest):
    if dest.is_symlink() or dest.parent.is_symlink():
        fail('Refusing linked skills directory or parent.')
    dest.parent.mkdir(parents=True, exist_ok=True)
    lockdir = dest.parent / '.research-skills-sync.lock'
    try:
        lockdir.mkdir()
    except FileExistsError:
        fail(f'Another sync is running (or stale lock): {lockdir}. Verify before removing it.')
    try:
        yield
    finally:
        lockdir.rmdir()

def preflight(repo, dest, source):
    state = read_state(dest)
    if state.get('repository') and state['repository'] != str(repo.resolve()):
        fail('This destination is managed by a different checkout; use its sync script.')
    for dirname, baseline in state['skills'].items():
        if not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', dirname):
            fail('Unsafe state entry.')
        target = dest / dirname
        if not target.exists() or snapshot(target) != baseline:
            fail(f'Installed skill changed or was removed: {dirname}. Capture/review it before sync.')
    wanted_names = {name_of(p): d for d, p in source.items()}
    if dest.exists():
        for path in dest.iterdir():
            if path.is_dir() and (path / 'SKILL.md').is_file():
                key = name_of(path)
                if key in wanted_names and path.name != wanted_names[key]:
                    fail(f'Existing skill name conflict: {key} at {path}')
    for dirname, path in source.items():
        target = dest / dirname
        if (target.exists() or target.is_symlink()) and dirname not in state['skills']:
            fail(f'Unmanaged existing skill would be overwritten: {target}. No files changed.')
    return state

def deploy(repo, dest, source, state):
    # Stage outside skills/, so Codex cannot discover temporary duplicate entries.
    dest.mkdir(parents=True, exist_ok=True)
    changed = {n: p for n, p in source.items() if state['skills'].get(n) != snapshot(p)}
    with tempfile.TemporaryDirectory(prefix='.research-skills-stage-', dir=dest.parent) as temp:
        stage = Path(temp)
        for n, p in changed.items():
            copy_skill(p, stage / n)
        activated = []
        saved = []
        try:
            for n in changed:
                target = dest / n
                if target.exists():
                    target.rename(stage / (n + '.backup'))
                    saved.append(n)
                (stage / n).rename(target)
                activated.append(n)
            updated = dict(state['skills'])  # Preserve retired skills; never guess what to delete.
            updated.update({n: snapshot(dest / n) for n in source})
            save_state(dest, {'format': 1, 'repository': str(repo.resolve()), 'skills': updated})
        except BaseException:
            for n in reversed(activated):
                shutil.rmtree(dest / n)
            for n in saved:
                (stage / (n + '.backup')).rename(dest / n)
            raise
    print(f'Installed/updated {len(changed)} of {len(source)} skills into {dest}; copies verified.')

def clean(repo):
    if git(repo, 'status', '--porcelain', '--untracked-files=all'):
        fail('Repository has uncommitted changes. Review and commit them before sync; no automatic stash/reset.')
    branch = git(repo, 'symbolic-ref', '--quiet', '--short', 'HEAD')
    if not branch:
        fail('Detached HEAD is not supported for device sync.')
    return branch

def scan_secrets(repo):
    tracked = git(repo, 'ls-files', '-z').split('\0')
    for rel in filter(None, tracked):
        path = Path(rel)
        if any(p in {'private-data', 'research-data', 'autoresearch-results', '.venv', 'node_modules'} for p in path.parts):
            fail(f'Private/runtime data path is tracked: {rel}')
        if path.name in {'.env', 'credentials.json', 'auth.json', 'hosts.yml'} or path.suffix in {'.key', '.pem'}:
            fail(f'Sensitive file is tracked: {rel}')
        full = repo / path
        if full.is_file() and SECRET.search(full.read_bytes()):
            fail(f'Possible credential in {rel}; inspect locally. Value intentionally not printed.')
    print('Tracked-file credential scan passed (review research content separately).')

def sync(args):
    if args.push and args.offline:
        fail('--push cannot be combined with --offline.')
    repo = args.repo.resolve()
    dest = args.dest.expanduser().absolute()
    with lock(dest):
        branch = clean(repo)
        source = skills(repo)
        state = preflight(repo, dest, source)
        if not args.offline:
            remote = git(repo, 'remote', 'get-url', 'origin')
            if args.remote_url and remote != args.remote_url:
                fail(f'Origin differs from requested URL: {remote}')
            subprocess.run(['git', '-C', str(repo), 'fetch', '--prune', 'origin'], check=True)
            remote_ref = f'refs/remotes/origin/{branch}'
            git(repo, 'rev-parse', '--verify', remote_ref)
            counts = git(repo, 'rev-list', '--left-right', '--count', 'HEAD...' + remote_ref).split()
            if int(counts[0]) and int(counts[1]):
                fail('Local and remote commits diverged. Resolve manually; no automatic merge/rebase.')
            subprocess.run(['git', '-C', str(repo), 'merge', '--ff-only', remote_ref], check=True)
            source = skills(repo)
            state = preflight(repo, dest, source)
        deploy(repo, dest, source, state)
        if args.push:
            scan_secrets(repo)
            subprocess.run(['git', '-C', str(repo), 'push', 'origin', f'HEAD:refs/heads/{branch}'], check=True)

def capture(args):
    repo, dest = args.repo.resolve(), args.dest.expanduser().absolute()
    dirname = args.skill
    if not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', dirname):
        fail('Unsafe skill directory name.')
    with lock(dest):
        state = read_state(dest)
        if state.get('repository') and state['repository'] != str(repo):
            fail('Destination belongs to a different checkout.')
        installed = dest / dirname
        key = name_of(installed)
        baseline = state['skills'].get(dirname)
        target = repo / '.agents' / 'skills' / dirname
        if target.exists():
            if baseline is None or snapshot(target) != baseline:
                fail('Repository copy also changed or is unmanaged; resolve manually.')
        for n, p in skills(repo).items():
            if n != dirname and name_of(p) == key:
                fail(f'Duplicate invocation name: {key}')
        with tempfile.TemporaryDirectory(dir=target.parent.parent, prefix='.research-capture-') as temp:
            stage = Path(temp) / dirname
            copy_skill(installed, stage)
            backup = Path(temp) / 'backup'
            if target.exists():
                target.rename(backup)
            try:
                stage.rename(target)
                state['repository'] = str(repo)
                state['skills'][dirname] = snapshot(installed)
                save_state(dest, state)
            except BaseException:
                if target.exists():
                    shutil.rmtree(target)
                if backup.exists():
                    backup.rename(target)
                raise
    print(f'Captured {dirname}. Review git diff, commit only intended skill files, then sync --push.')

def vendor(args):
    repo = args.repo.resolve()
    project = args.project.resolve()
    if project == repo:
        fail('Choose another project checkout.')
    if git(project, 'status', '--porcelain', '--untracked-files=all'):
        fail('Target project is dirty; commit its changes before vendoring.')
    dest = project / '.agents' / 'skills'
    with lock(dest):
        source = skills(repo)
        state = preflight(repo, dest, source)
        deploy(repo, dest, source, state)
    # Record a public-safe source pointer, no absolute paths or credentials.
    pointer = project / '.agents' / 'research-skills-source.json'
    if pointer.exists() and pointer.is_symlink():
        fail('Refusing linked provenance file.')
    pointer.write_text(json.dumps({'repository': 'https://github.com/TOAPY/codex-research-skills', 'commit': git(repo, 'rev-parse', 'HEAD')}, indent=2)+'\n')
    print('Review and commit .agents/skills and .agents/research-skills-source.json in the target project.')
    print('Keep .agents/research-skills-state.json local; add that exact path to the target .gitignore.')

def validate(args):
    source = skills(args.repo.resolve())
    required = {
        'academic-research-suite': ['manifest.json', 'ars/NOTICE.md', 'ars/deep-research/WORKFLOW.md', 'codex/scripts/ars_codex_full_runtime.py'],
        'codex-autoresearch': ['scripts/autoresearch.py', 'scripts/autoresearch_core.py', 'references/workflow.md', 'agents/openai.yaml'],
        'nature-shared': ['core/terminology-ledger.md', 'journal-formats/nature.md'],
    }
    for n, paths in required.items():
        if n not in source:
            fail(f'Missing required skill: {n}')
        for rel in paths:
            if not (source[n] / rel).is_file():
                fail(f'Missing dependency: {n}/{rel}')
    for n, p in source.items():
        for rel in re.findall(r'`(\.\./nature-shared/[^`\s]+)`', (p / 'SKILL.md').read_text()):
            if not (p / rel).is_file():
                fail(f'Missing sibling dependency: {n}/{rel}')
        print(f'{n}: ${name_of(p)} ({len(snapshot(p))} files)')
    restricted = source['nature-figure'] / 'assets' / 'figures4papers'
    forbidden = [p for p in restricted.rglob('*') if p.is_file() and p.name not in {'THIRD_PARTY_NOTICES.md', 'UPSTREAM-REFERENCE.md'}]
    if forbidden:
        fail('Unlicensed third-party figures4papers assets must not be vendored.')
    print(f'Validation passed: {len(source)} complete skill directories; no duplicate names.')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['sync', 'capture', 'vendor-project', 'validate', 'scan-secrets'])
    parser.add_argument('--repo', type=Path, default=REPO_DEFAULT)
    parser.add_argument('--dest', type=Path, default=Path.home()/'.agents'/'skills')
    parser.add_argument('--offline', action='store_true', help='Install reviewed local checkout without network')
    parser.add_argument('--push', action='store_true', help='Push already reviewed and committed changes')
    parser.add_argument('--remote-url')
    parser.add_argument('--skill')
    parser.add_argument('--project', type=Path)
    args = parser.parse_args()
    if args.command == 'capture' and not args.skill:
        parser.error('capture requires --skill DIRECTORY')
    if args.command == 'vendor-project' and not args.project:
        parser.error('vendor-project requires --project PATH')
    try:
        {'sync': sync, 'capture': capture, 'vendor-project': vendor, 'validate': validate,
         'scan-secrets': lambda a: scan_secrets(a.repo.resolve())}[args.command](args)
    except (RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        print('STOP:', str(exc), file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
