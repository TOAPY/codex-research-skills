#!/usr/bin/env python3
"""Query the native Codex skills/list API; no thread, model call or experiment."""
import argparse
import json
from pathlib import Path
import queue
import subprocess
import threading

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cwd', action='append', required=True)
parser.add_argument('--output', type=Path)
parser.add_argument('--names-from-repo', type=Path, help='Include every invocation name from this central skills repository')
args = parser.parse_args()
expected = set()
if args.names_from_repo:
    from manage import skills, name_of
    expected = {name_of(p) for p in skills(args.names_from_repo.resolve()).values()}
process = subprocess.Popen(['codex', '--no-daemon', 'app-server', '--stdio'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL, text=True, bufsize=1)
inbox = queue.Queue()
def reader():
    for line in process.stdout:
        try:
            inbox.put(json.loads(line))
        except json.JSONDecodeError:
            pass
threading.Thread(target=reader, daemon=True).start()
def send(obj):
    process.stdin.write(json.dumps(obj)+'\n')
    process.stdin.flush()
def response(id):
    while True:
        try:
            obj = inbox.get(timeout=45)
        except queue.Empty:
            raise RuntimeError('Codex app-server did not respond; verify permissions for its local SQLite state.') from None
        if obj.get('id') == id:
            if 'error' in obj:
                raise RuntimeError(obj['error'])
            return obj['result']
try:
    send({'id': 1, 'method': 'initialize', 'params': {'clientInfo': {'name': 'research-skills-verifier', 'version': '1.0'}}})
    response(1)
    send({'method': 'initialized', 'params': {}})
    send({'id': 2, 'method': 'skills/list', 'params': {'cwds': args.cwd, 'forceReload': True}})
    result = response(2)
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    for entry in result.get('data', []):
        print('cwd:', entry.get('cwd'))
        print('loader errors:', json.dumps(entry.get('errors', []), ensure_ascii=False))
        wanted = [s for s in entry.get('skills', []) if s.get('name', '').startswith('nature-') or
                  s.get('name') in expected | {'academic-research-suite', 'codex-autoresearch', 'researchwrite'}]
        for s in wanted:
            print(s.get('name'), '|', s.get('scope'), '| enabled:', s.get('enabled'), '|', s.get('path'))
        print('Research skills:', len(wanted), '| all skills:', len(entry.get('skills', [])))
finally:
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
