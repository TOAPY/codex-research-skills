#!/usr/bin/env python3
"""Optional local-only fetch, after the caller has obtained copying permission."""
import argparse
from pathlib import Path
import re
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--permission-obtained', action='store_true', required=True)
parser.add_argument('--commit', required=True)
parser.add_argument('--destination', type=Path, required=True)
args = parser.parse_args()
if not re.fullmatch(r'[0-9a-f]{40}', args.commit):
    parser.error('Use an exact upstream commit SHA.')
dest = args.destination.expanduser().absolute()
central = Path(__file__).resolve().parents[1]
if central == dest or central in dest.parents or '.agents' in dest.parts or dest.exists():
    parser.error('Choose a new local reference folder outside skill directories and the central repository.')
subprocess.run(['git', 'clone', '--no-checkout', 'https://github.com/ChenLiu-1996/figures4papers.git', str(dest)], check=True)
subprocess.run(['git', '-C', str(dest), 'checkout', '--detach', args.commit], check=True)
print('Fetched for local use only. No files were executed or copied into Skills.')
