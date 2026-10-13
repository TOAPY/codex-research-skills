#!/usr/bin/env python3
"""Package reviewed upstream checkouts into a NEW staging directory."""
import argparse
import json
from pathlib import Path
import shutil
import re

UPSTREAMS = {
    'academic': {'url': 'https://github.com/Imbad0202/academic-research-skills-codex', 'commit': '52228e8280dd1770e18ecfc3b1fdf16b13b58104', 'license': 'CC-BY-NC-4.0', 'version': '3.23.0'},
    'nature': {'url': 'https://github.com/Yuan1z0825/nature-skills', 'commit': '473e8d7b1b918fe37208d3a5e143a3ac9af4c91b', 'license': 'Apache-2.0; nested MIT exceptions retained'},
    'autoresearch': {'url': 'https://github.com/leo-lilinxiao/codex-autoresearch', 'commit': '0f54c571707487f59486ba7c50d405edfc746c19', 'license': 'MIT'},
    'scientific': {'url': 'https://github.com/K-Dense-AI/scientific-agent-skills', 'commit': 'a1043ef544e3a100c28e70a736b6cf32554d0677', 'license': 'MIT collection; individual SKILL.md licenses retained; venue Elsevier assets LPPL-1.3-or-later', 'version': '2.72.0', 'reference_only': ['glycoengineering', 'phylogenetics', 'primekg', 'rowan']},
}

def copy(src, dst):
    def ignore(directory, names):
        return [n for n in names if n in {'.git', '__pycache__', '.DS_Store', '.pytest_cache', 'node_modules'} or n.endswith(('.pyc', '.pyo'))]
    shutil.copytree(src, dst, ignore=ignore)

def package_scientific(scientific, root, record):
    """Retain whole independent skill directories and the upstream MIT notice."""
    count = 0
    for p in sorted((scientific / 'skills').iterdir()):
        if not p.is_dir():
            continue
        if not (p / 'SKILL.md').is_file():
            raise RuntimeError('Unexpected scientific directory without SKILL.md: ' + str(p))
        if p.name in record.get('reference_only', []):
            continue
        header = (p / 'SKILL.md').read_text(encoding='utf-8').split('---', 2)[1]
        license_match = re.search(r'^license:\s*(.*)$', header, re.M)
        declared = license_match.group(1).lower() if license_match else ''
        if 'unknown' in declared or 'proprietary' in declared:
            raise RuntimeError('New unclear individual license needs review: ' + p.name)
        if (root / p.name).exists():
            raise RuntimeError('Scientific skill directory conflicts: ' + p.name)
        copy(p, root / p.name)
        shutil.copy2(scientific / 'LICENSE.md', root / p.name / 'LICENSE.scientific-agent-skills.md')
        (root / p.name / 'UPSTREAM.json').write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
        count += 1
    scientific_support(scientific, root.parent.parent, record)
    return count

def scientific_support(scientific, output, record):
    """Preserve upstream setup declarations, references and full license texts."""
    support = output / 'upstream-support' / 'scientific-agent-skills'
    support.mkdir(parents=True, exist_ok=True)
    for name in ('README.md', 'LICENSE.md', 'CITATION.cff', 'pyproject.toml', 'plugin.json'):
        shutil.copy2(scientific / name, support / name)
    shutil.copy2(scientific / 'tests' / 'skill-requirements.toml', support / 'skill-requirements.toml')
    texts = Path(__file__).resolve().parents[1] / 'upstream-support' / 'scientific-agent-skills' / 'licenses'
    if texts.resolve() != (support / 'licenses').resolve():
        copy(texts, support / 'licenses')
    for p in (output / '.agents' / 'skills').iterdir():
        if not (p / 'LICENSE.scientific-agent-skills.md').exists():
            continue
        raw = (p / 'SKILL.md').read_text(encoding='utf-8').split('---', 2)[1]
        match = re.search(r'^license:\s*(.*)$', raw, re.M)
        declaration = match.group(1).lower() if match else ''
        key = None
        if 'apache' in declaration:
            key = 'Apache-2.0'
        elif 'bsd-2-clause' in declaration:
            key = 'BSD-2-Clause'
        elif any(n in declaration for n in ('bsd-3-clause', '3 clause bsd', '3-clause bsd')):
            key = 'BSD-3-Clause'
        elif 'gpl-3.0-or-later' in declaration:
            key = 'GPL-3.0-or-later'
        elif 'gplv3' in declaration:
            key = 'GPL-3.0-only'
        elif 'gpl-2.0' in declaration:
            key = 'GPL-2.0-only'
        elif 'noncommercial' in declaration:
            key = 'PolyForm-Noncommercial-1.0.0'
        elif 'nc-sa' in declaration:
            key = 'CC-BY-NC-SA-4.0'
        elif 'cc-by-4.0' in declaration or 'creativecommons.org/licenses/by/4.0' in declaration:
            key = 'CC-BY-4.0'
        elif 'biopython' in declaration:
            key = 'Biopython'
        if key:
            shutil.copy2(texts / (key + '.txt'), p / 'LICENSE.individual.txt')
        if p.name == 'venue-templates':
            shutil.copy2(texts / 'LPPL-1.3c.txt', p / 'assets' / 'journals' / 'LICENSE.LPPL.txt')
            (p / 'assets' / 'journals' / 'THIRD_PARTY-NOTICE.md').write_text(
                'The unmodified elsarticle-*.tex and elsarticle-*.bst files are an excerpt of the Elsevier Elsarticle Bundle. '
                'Copyright 2007-2026 Elsevier Ltd. Their original LPPL 1.3-or-later notices are retained. '
                'Obtain the complete bundle and manifest at https://ctan.org/pkg/elsarticle or '
                'https://mirrors.ctan.org/macros/latex/contrib/elsarticle.zip . '
                'Other templates keep their original contents and licensing declarations.\n', encoding='utf-8')
    references = output / 'upstream-references'
    references.mkdir(exist_ok=True)
    items = []
    for name in record.get('reference_only', []):
        raw = (scientific / 'skills' / name / 'SKILL.md').read_text(encoding='utf-8')
        declared = re.search(r'^license:\s*(.*)$', raw, re.M).group(1)
        items.append({'name': name, 'declared_license': declared,
                      'url': record['url'] + '/tree/' + record['commit'] + '/skills/' + name, 'path': 'skills/' + name})
    (references / 'scientific-agent-skills.json').write_text(json.dumps({
        'repository': record['url'], 'commit': record['commit'],
        'reason': 'Individual skill licenses are unclear or proprietary. No skill content is redistributed.',
        'skills': items}, indent=2) + '\n', encoding='utf-8')

def package(academic, nature, autoresearch, output, pins=None, scientific=None):
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
    if scientific is not None:
        package_scientific(scientific, root, records['scientific'])
    elif 'scientific' in records:
        records = {key: value for key, value in records.items() if key != 'scientific'}
    (output / 'UPSTREAMS.json').write_text(json.dumps(records, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print('Prepared', len(list(root.iterdir())), 'skill directories at', root)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--academic-root', required=True, type=Path)
    parser.add_argument('--nature-root', required=True, type=Path)
    parser.add_argument('--autoresearch-root', required=True, type=Path)
    parser.add_argument('--scientific-root', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    package(args.academic_root, args.nature_root, args.autoresearch_root, args.output, scientific=args.scientific_root)
