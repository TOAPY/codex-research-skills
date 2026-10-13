#!/usr/bin/env python3
"""Download pinned upstream versions to a new review stage; never activate or push."""
import argparse
import copy
import io
import json
from pathlib import Path
import re
import tempfile
import urllib.request
import zipfile
from package_upstreams import package

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', required=True, type=Path)
parser.add_argument('--academic-commit')
parser.add_argument('--nature-commit')
parser.add_argument('--autoresearch-commit')
parser.add_argument('--scientific-commit')
args = parser.parse_args()
central = Path(__file__).resolve().parents[1]
pins = copy.deepcopy(json.loads((central / 'UPSTREAMS.json').read_text()))
for key in pins:
    override = getattr(args, key + '_commit')
    if override:
        if not re.fullmatch(r'[0-9a-f]{40}', override):
            parser.error('Commit overrides must be 40-character SHA values.')
        pins[key]['commit'] = override
        pins[key].pop('version', None)
if args.output.exists():
    parser.error('Choose a new output directory; no overwrite is allowed.')
with tempfile.TemporaryDirectory(prefix='research-upstream-review-') as temp:
    roots = {}
    for key, pin in pins.items():
        owner_repo = pin['url'].removeprefix('https://github.com/')
        url = f"https://codeload.github.com/{owner_repo}/zip/{pin['commit']}"
        request = urllib.request.Request(url, headers={'User-Agent': 'codex-research-skills-installer'})
        with urllib.request.urlopen(request, timeout=120) as response:
            data = response.read()
        destination = Path(temp) / key
        destination.mkdir()
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for info in archive.infolist():
                path = Path(info.filename)
                if path.is_absolute() or '..' in path.parts or '\\' in info.filename:
                    raise RuntimeError('Unsafe archive member')
                if (info.external_attr >> 16) & 0o170000 == 0o120000:
                    raise RuntimeError('Symlink in archive')
            archive.extractall(destination)
        roots[key] = next(destination.iterdir())
    package(roots['academic'], roots['nature'], roots['autoresearch'], args.output, pins, scientific=roots.get('scientific'))
print('Review licenses, scripts, dependency and path changes before replacing managed repository copies.')
