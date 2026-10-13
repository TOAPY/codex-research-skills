#!/usr/bin/env python3
"""Package reviewed upstream checkouts into a NEW staging directory."""
import argparse
import json
from pathlib import Path
import shutil

UPSTREAMS = {
    'academic': {'url': 'https://github.com/Imbad0202/academic-research-skills-codex', 'commit': '52228e8280dd1770e18ecfc3b1fdf16b13b58104', 'license': 'CC-BY-NC-4.0', 'version': '3.23.0'},
    'nature': {'url': 'https://github.com/Yuan1z0825/nature-skills', 'commit': '473e8d7b1b918fe37208d3a5e143a3ac9af4c91b', 'license': 'Apache-2.0; nested MIT exceptions retained'},
    'autoresearch': {'url': 'https://github.com/leo-lilinxiao/codex-autoresearch', 'commit': '0f54c571707487f59486ba7c50d405edfc746c19', 'license': 'MIT'},
}

def copy(src, dst):
    def ignore(directory, names):
        return [n for n in names if n in {'.git', '__pycache__', '.DS_Store', '.pytest_cache', 'node_modules'} or n.endswith(('.pyc', '.pyo'))]
    shutil.copytree(src, dst, ignore=ignore)

def package(academic, nature, autoresearch, output, pins=None):
    if output.exists():
        raise RuntimeError('Output must be a new directory; existing files are never overwritten.')
    root = output / '.agents' / 'skills'
    root.mkdir(parents=True)
    copy(academic / 'skills' / 'academic-research-suite', root / 'academic-research-suite')
    shutil.copy2(academic / 'LICENSE', root / 'academic-research-suite' / 'LICENSE')
    for p in sorted((nature / 'skills').iterdir()):
        if not p.is_dir():
            continue
        if not (p / 'SKILL.md').exists():
            raise RuntimeError('Unexpected skill directory without SKILL.md: ' + str(p))
        copy(p, root / p.name)
        shutil.copy2(nature / 'LICENSE', root / p.name / 'LICENSE.nature-skills')
    copy(autoresearch, root / 'codex-autoresearch')
    restricted = root / 'nature-figure' / 'assets' / 'figures4papers'
    notice = (restricted / 'THIRD_PARTY_NOTICES.md').read_bytes()
    # Only our freshly created staging directory is removed here.
    shutil.rmtree(restricted)
    restricted.mkdir()
    (restricted / 'THIRD_PARTY_NOTICES.md').write_bytes(notice)
    (restricted / 'UPSTREAM-REFERENCE.md').write_text(
        '# Unvendored reference assets\n\n'
        'Source: https://github.com/ChenLiu-1996/figures4papers\n\n'
        'The source had no explicit distribution license at packaging time. '
        'Third-party scripts, figures and previews are intentionally excluded. '
        'Nature core plotting tools and original templates are retained. '
        'After obtaining rights, use scripts/fetch-restricted-reference.py in the central repository '
        'to fetch a pinned upstream checkout into a separate local reference folder. '
        'Never copy it into this skills repository.\n', encoding='utf-8')
    demos = root / 'nature-figure' / 'references' / 'demos.md'
    demos.write_text('<!-- Modified 2026-10-13: replace unlicensed local assets with upstream references. -->\n'
        '# figures4papers Reference Index\n\n'
        'Local third-party previews and scripts are not distributed. Read '
        '`../assets/figures4papers/THIRD_PARTY_NOTICES.md` and '
        '`../assets/figures4papers/UPSTREAM-REFERENCE.md`. '
        'Browse the original project at https://github.com/ChenLiu-1996/figures4papers '
        'only when needed. Obtain appropriate rights before copying, adapting or distributing. '
        'For the installed plotting tools, use `template-catalog.md` and `asset-adaptation.md`.\n', encoding='utf-8')
    for p in root.glob('nature-*'):
        skill = p / 'SKILL.md'
        raw = skill.read_text(encoding='utf-8')
        head, body = raw.split('---', 2)[1:]
        body = body.replace('python skills/nature-figure/scripts/audit_figure_collisions.py', 'python "<SKILL_ROOT>/scripts/audit_figure_collisions.py"')
        if p.name == 'nature-downloader':
            body = body.replace('$env:USERPROFILE\\.claude\\skills\\nature-downloader', '$env:USERPROFILE\\.agents\\skills\\nature-downloader')
        block = '\n<!-- Modified 2026-10-13: Codex path portability guidance; upstream workflow retained. -->\n' + (
            '\n## Codex installation paths\n\n'
            'Resolve `SKILL_ROOT` to the directory containing this SKILL.md. '
            'Resolve this skill\'s scripts/, references/, assets/, static/ and templates/ from SKILL_ROOT, '
            'regardless of the current project working directory. '
            'Examples beginning skills/' + p.name + '/ mean SKILL_ROOT/, not a path in the research project. '
            'Keep ../nature-shared/ as a sibling-relative path. On native Windows use the installed '
            'Python interpreter (python or py -3) and PowerShell; no Bash installation is required. '
            'Use available Codex browser/tools for browser steps. Optional external browser skills, MCP servers, '
            'provider credentials and scientific packages are not installed by this package; report missing '
            'capabilities before using their features. Read PORTABILITY.md.\n')
        skill.write_text('---'+head+'---'+block+body, encoding='utf-8')
        (p / 'PORTABILITY.md').write_text(
            '# Codex portability overlay\n\n'
            'Modified 2026-10-13. The entire upstream skill directory is retained except the '
            'unlicensed figures4papers assets in nature-figure. All sibling nature-shared files are included. '
            'SKILL.md has an installation-path note; the Nature Figure audit example and Nature Downloader '
            'own Windows path are corrected. Original Claude/web-access-main instructions are optional references; '
            'that external skill is not supplied. Use available Codex browser tools where appropriate. '
            'Requirements files and MCP implementations are preserved, but their dependencies and credentials '
            'are configured only for a requested task. See the central README.\n', encoding='utf-8')
    # Replace README's now-broken embedded third-party preview with a source link.
    for filename in ('README.md', 'README_EN.md'):
        path = root / 'nature-figure' / filename
        lines = path.read_text(encoding='utf-8').splitlines()
        lines = [line if 'comparison_radar.png' not in line else
                 '| figures4papers reference | [Upstream reference](https://github.com/ChenLiu-1996/figures4papers) | Not distributed: permission required |' for line in lines]
        path.write_text('<!-- Modified 2026-10-13: unlicensed local preview replaced with upstream link. -->\n'+'\n'.join(lines)+'\n', encoding='utf-8')
    records = pins or UPSTREAMS
    for p in root.iterdir():
        key = 'academic' if p.name == 'academic-research-suite' else ('autoresearch' if p.name == 'codex-autoresearch' else 'nature')
        (p / 'UPSTREAM.json').write_text(json.dumps(records[key], indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    (output / 'UPSTREAMS.json').write_text(json.dumps(records, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print('Prepared', len(list(root.iterdir())), 'skill directories at', root)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--academic-root', required=True, type=Path)
    parser.add_argument('--nature-root', required=True, type=Path)
    parser.add_argument('--autoresearch-root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    package(args.academic_root, args.nature_root, args.autoresearch_root, args.output)
