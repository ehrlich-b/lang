#!/usr/bin/env python3
"""Build and validate a closed, source-bound comparison draft entirely offline."""
import argparse
import ast
import gzip
import hashlib
import io
import json
import pathlib
import re
import subprocess
import tarfile
from html.parser import HTMLParser
from urllib.parse import urlsplit

ROOT = pathlib.Path(__file__).resolve().parents[1]
INPUT_HEAD = '209e4ca1e12a643102e37b58b6e43fe7ce4c5eaf'
BASE = 'e148de1e1a3bb1a229f3a8369e41e4b0241783e3'
MANIFEST_HASH = '0be69a0effd5dab92a1122471a382d0e32fe49b495ee298e36c3e370bef9702e'
SDK = 'lang-0.1.0+e148de1e1a3b-x86_64-linux'
ARMS = ('lang', 'bison', 'antlr')
CASES = ('claims-to-evidence', 'lang-losses', 'native-scope', 'sdk-identity',
         'links', 'release-dry-run')
SOURCES = {'lang': ['harbor.lang'],
           'bison': ['harbor.l', 'harbor.y', 'harbor.c', 'harbor.h'],
           'antlr': ['Harbor.g4', 'main.cpp']}
OBSTACLES = (
    ('generated-names', 'lang/FRICTION.md', 'new generated-rule name collision',
     'Lang needed grammar-rule prefixes to avoid bundled function names; ANTLR reported no compiler errors or warnings.'),
    ('string-validation', 'lang/FRICTION.md', 'arbitrary escapes',
     'Lang needed language-owned string validation and newline preservation; its SDK scanner accepts strings outside this brief.'),
    ('link-warning', 'lang/FRICTION.md', 'target-triple warning',
     'Lang retained a native target-triple warning; ANTLR reported no compiler errors or warnings.'),
    ('isolation-setup', 'lang/FRICTION.md', 'Permission denied',
     'Lang also encountered isolation setup failures and a false Clang prerequisite diagnosis; these are setup friction, not grammar errors.'),
    ('prior-exposure', 'lang/QUALIFIERS.md', 'not a blinded study',
     'Lang had prior exposure to the earlier friction record; this weakens independence.'),
)
UNMEASURED = [
    'Comparable Lang time to first working sample and a common timing boundary.',
    'Human usability, independent blinded replication, and a general error/dead-end ranking.',
    'Runtime throughput, build-time performance, memory, binary size, and optimization quality.',
    'Other platforms, other grammars, scale, ecosystem breadth, and universal interoperability.',
    'Public SDK availability, deployed website identity, and served-byte equality.',
    'The final matched comparison head and any additional losses it measures.',
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text())


def write_json(path, value):
    path.write_bytes(json_bytes(value))


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def measurements(data):
    return {'version': 1, 'input_manifest_sha256': MANIFEST_HASH,
            'metrics': data['metrics'], 'diagnostics': data['diagnostics']}


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()


def safe(root, name):
    path = root / name
    require(not path.is_symlink() and path.resolve().is_relative_to(root.resolve()),
            'escaping path: ' + name)
    return path


def frozen(root):
    require(digest((root / 'MANIFEST.json').read_bytes()) == MANIFEST_HASH,
            'changed frozen manifest')
    rows = load(root / 'MANIFEST.json')
    for row in rows:
        require(digest(safe(root, row['path']).read_bytes()) == row['sha256'],
                'changed frozen input: ' + row['path'])
    return rows


def results(inputs, arm):
    value = load(inputs / arm / 'trial-results.json')
    return value if isinstance(value, list) else value['results' if arm == 'bison' else 'cases']


def source(inputs, name):
    return {'path': 'frozen/' + name, 'sha256': digest((inputs / name).read_bytes())}


def metric(inputs, arm, key, value, derivation, names):
    return {'id': arm + '.' + key, 'value': value, 'derivation': derivation,
            'sources': [source(inputs, arm + '/' + name) for name in names]}


def claims(inputs):
    metrics = []
    diagnostics = {}
    for arm in ARMS:
        rows = results(inputs, arm)
        expected = {'sample.conf', 'fixtures/valid-edge.conf'} | {
            'fixtures/' + p.name for p in (inputs / 'trial1/fixtures').iterdir()}
        require(len(rows) == len(expected) and {r['file'] for r in rows} == expected,
                'missing/duplicate trial cases: ' + arm)
        valid = [r for r in rows if r['file'] in ('sample.conf', 'fixtures/valid-edge.conf')]
        invalid = [r for r in rows if r not in valid]
        require(all(r['valid'] is True and r['exit'] == 0 and r['stdout'] and not r['stderr'] for r in valid),
                'false valid success: ' + arm)
        require(all(r['valid'] is False and r['exit'] != 0 and not r['stdout'] for r in invalid),
                'false invalid success: ' + arm)
        fields = sum(bool(re.search(re.escape(pathlib.Path(r['file']).name) +
                                   r':\d+:\d+:', r['stderr'])) and 'expected' in r['stderr']
                     for r in invalid)
        carets = sum(bool(re.search(r'^\s*\^', r['stderr'], re.M)) for r in invalid)
        for key, value, derivation in (
                ('valid', len(valid), 'count valid inputs with exit zero, output and no diagnostic'),
                ('invalid', len(invalid), 'count invalid inputs with nonzero exit and no output'),
                ('diagnostic-fields', fields, 'count invalid diagnostics with file:line:column and expected'),
                ('carets', carets, 'count invalid diagnostics with a caret line')):
            metrics.append(metric(inputs, arm, key, value, derivation, ['trial-results.json']))
        metrics.append(metric(inputs, arm, 'source-lines',
                              sum(len((inputs / arm / f).read_text().splitlines()) for f in SOURCES[arm]),
                              'physical language-source lines, blanks/comments included; helpers/generated files excluded',
                              SOURCES[arm]))
        diagnostics[arm] = [{k: r[k] for k in ('file', 'exit', 'stdout', 'stderr')} for r in invalid]
    for arm, key in (('bison', 'timing'), ('antlr', 'wall_seconds')):
        raw = load(inputs / arm / 'trial-results.json')
        value = raw[key]['seconds_to_first_passing_sample'] if arm == 'bison' else raw[key]
        metrics.append(metric(inputs, arm, 'first-sample-seconds', value,
                              '/timing/seconds_to_first_passing_sample' if arm == 'bison' else '/wall_seconds',
                              ['trial-results.json']))
    obstacles = []
    for name, path, anchor, text in OBSTACLES:
        require(anchor in (inputs / path).read_text(), 'missing obstacle anchor: ' + name)
        obstacles.append({'id': name, 'text': text, 'anchor': anchor, 'source': source(inputs, path)})
    data = {'version': 1, 'status': 'draft-validated', 'comparison_head': None,
            'public_available': False, 'superiority': False, 'metrics': metrics,
            'diagnostics': diagnostics, 'lang_losses_and_friction': obstacles,
            'unmeasured': UNMEASURED,
            'native_scope': 'These host validators only; all three arms are native.',
            'native_evidence': [source(inputs, p) for p in
                                ('lang/commands.json', 'lang/harbor.lang',
                                 'bison/trial-results.json', 'bison/build.sh',
                                 'antlr/trial-results.json', 'antlr/build.sh')],
            'sdk': {'version': '0.1.0+e148de1e1a3b', 'commit': BASE,
                    'target': 'x86_64-linux',
                    'receipt': source(inputs, 'lang/' + SDK + '.receipt.json'),
                    'archive': source(inputs, 'lang/' + SDK + '.tar.xz')}}
    data['measurement_result'] = {'path': 'measurements.json',
                                  'sha256': digest(json_bytes(measurements(data)))}
    return data


def story(data):
    values = {m['id']: m['value'] for m in data['metrics']}
    table = ['| Recorded dimension | Lang | flex/Bison | ANTLR |',
             '| --- | ---: | ---: | ---: |']
    for label, key in [('Valid accepts', 'valid'), ('Invalid rejections', 'invalid'),
                       ('File/line/column/expected coverage', 'diagnostic-fields'),
                       ('Caret diagnostics', 'carets'), ('Language-source lines', 'source-lines')]:
        table.append('| ' + label + ' | ' + ' | '.join(str(values[a + '.' + key]) for a in ARMS) + ' |')
    table.append('| Recorded first-sample seconds (unmatched clocks) | unmeasured | ' +
                 str(values['bison.first-sample-seconds']) + ' | ' +
                 str(values['antlr.first-sample-seconds']) + ' |')
    replacement = {
        'metrics': '\n'.join(table),
        'losses': 'Lang losses, limitations and friction recorded so far:\n\n' +
                  '\n'.join('- ' + row['text'] for row in data['lang_losses_and_friction']),
        'unmeasured': 'Unmeasured or pending dimensions:\n\n' + '\n'.join('- ' + x for x in data['unmeasured']),
        'identity': ('Frozen SDK: `' + data['sdk']['version'] + '`, target `' +
                     data['sdk']['target'] + '`, source `' + BASE + '`.\n'
                     'Archive SHA-256: `' + data['sdk']['archive']['sha256'] + '`.'),
        'links': '\n'.join('[Frozen ' + p + '](frozen/' + p + ')' for p in
                           ('trial1/brief.md', 'lang/trial-results.json', 'bison/trial-results.json',
                            'antlr/trial-results.json', 'lang/FRICTION.md', 'lang/QUALIFIERS.md',
                            'bison/FRICTION.md', 'antlr/FRICTION.md')),
    }
    text = (ROOT / 'docs/comparison-release-story.md.in').read_text()
    for key, value in replacement.items():
        text = text.replace('{{' + key + '}}', value)
    require('{{' not in text, 'unrendered story')
    return text


def inventory():
    # Read the registered inventory without importing its command-line program.
    tree = ast.parse((ROOT / 'web/verify_archive.py').read_text())
    assignment = next(n for n in tree.body if isinstance(n, ast.Assign) and
                      any(isinstance(t, ast.Name) and t.id == 'SITE_FILES' for t in n.targets))
    return sorted(ast.literal_eval(assignment.value.args[0].func.value).split())


def site_links():
    """Audit existing local links without fetching remote resources."""
    rows = []

    class Links(HTMLParser):
        def handle_starttag(self, tag, attributes):
            for key, value in attributes:
                if key not in ('href', 'src') or not value:
                    continue
                target = urlsplit(value)
                if target.scheme or target.netloc or not target.path:
                    continue
                name = target.path
                if name.endswith('/'):
                    name += 'index.html'
                resolved = safe(ROOT / 'web', name)
                rows.append({'page': str(page.relative_to(ROOT)), 'link': value,
                             'exists': resolved.is_file(),
                             'in_site_manifest': str(resolved.relative_to(ROOT / 'web')).removeprefix('./') in inventory()})

    for page in sorted((ROOT / 'web').glob('*.html')):
        Links().feed(page.read_text())
    return rows


def plan(inputs, data):
    files = {name: {'sha256': digest((ROOT / 'web' / name).read_bytes()),
                    'bytes': (ROOT / 'web' / name).stat().st_size} for name in inventory()}
    receipt = load(ROOT / 'web/receipt.json')
    return {'version': 1, 'mode': 'offline-dry-run', 'publish': False,
            'final_validation': 'pending-matched-comparison', 'comparison_head': None,
            'source_tree': git('rev-parse', 'HEAD^{tree}'),
            'input_head': INPUT_HEAD, 'input_manifest_sha256': MANIFEST_HASH,
            'sdk': data['sdk'], 'site_recorded_source': receipt['source']['revision'],
            'site_matches_sdk': receipt['source']['revision'] == BASE,
            'story_in_site_archive': False, 'site_files': files,
            'existing_site_links': site_links(),
            'story_sha256': digest(story(data).encode()),
            'measurement_result': data['measurement_result'],
            'claims_sha256': digest((json.dumps(data, indent=2, sort_keys=True) + '\n').encode()),
            'blocked_until': ['matched comparison passes at a committed head',
                              'all measured losses and unmeasured dimensions reconciled',
                              'site and SDK identities rebuilt and verified together',
                              'existing site release download link resolved into a verified artifact inventory',
                              'story integrated and a separate publication authorized'],
            'future_served_check': 'web/verify_live.py against the final verified archive; never run by this draft'}


def sdk_identity(inputs):
    receipt = load(inputs / 'lang' / (SDK + '.receipt.json'))
    archive = inputs / 'lang' / (SDK + '.tar.xz')
    require(receipt['commit'] == BASE and receipt['sdk_version'] == '0.1.0+e148de1e1a3b'
            and receipt['target'] == 'x86_64-linux', 'SDK identity mismatch')
    require(receipt['archive']['sha256'] == digest(archive.read_bytes()) and
            receipt['archive']['bytes'] == archive.stat().st_size, 'SDK archive mismatch')
    with tarfile.open(archive, 'r:xz') as tar:
        members = [m for m in tar.getmembers() if m.isfile()]
        actual = {}
        for m in members:
            path = pathlib.PurePosixPath(m.name)
            require(path.parts[0] == SDK and '..' not in path.parts, 'SDK archive path')
            key = str(pathlib.PurePosixPath(*path.parts[1:]))
            require(key not in actual, 'duplicate SDK entry')
            actual[key] = {'bytes': m.size, 'mode': oct(m.mode),
                           'sha256': digest(tar.extractfile(m).read())}
        # sdk.json cannot hash itself; the archive hash binds this metadata file.
        embedded = json.load(tar.extractfile(SDK + '/sdk.json'))
        require(embedded == {k: v for k, v in receipt.items() if k != 'archive'},
                'embedded SDK identity differs from receipt')
        require(set(actual) == set(receipt['files']) | {'sdk.json'} and
                {k: v for k, v in actual.items() if k != 'sdk.json'} == receipt['files'],
                'SDK contents differ from receipt')


def site_archive(packet, release):
    with tarfile.open(packet / 'site-snapshot.tar.gz', 'r:gz') as tar:
        members = tar.getmembers()
        names = [m.name for m in members]
        require(len(names) == len(set(names)) and all(m.isfile() for m in members),
                'duplicate/non-file site entry')
        require(set(names) == set(release['site_files']) | {'MANIFEST'}, 'site inventory mismatch')
        expected = ''.join(row['sha256'] + '  ' + name + '\n'
                           for name, row in sorted(release['site_files'].items()))
        require(tar.extractfile('MANIFEST').read().decode() == expected, 'dry-run manifest mismatch')
        for name, row in release['site_files'].items():
            data = tar.extractfile(name).read()
            require(digest(data) == row['sha256'] and len(data) == row['bytes'],
                    'dry-run file mismatch: ' + name)


def validate(inputs, packet, case=None, final=False):
    require(not final, 'Final validation blocked: matched comparison head and reconciled site/SDK artifacts are pending')
    frozen(inputs)
    frozen(packet / 'frozen')
    expected = claims(inputs)
    require(load(packet / 'measurements.json') == measurements(expected) and
            digest((packet / 'measurements.json').read_bytes()) == expected['measurement_result']['sha256'],
            'quantitative result differs from hashed source-derived measurements')
    actual = load(packet / 'claims.json')
    require(actual == expected, 'unsupported/changed/missing claims, loss or dimension')
    require((packet / 'STORY.md').read_text() == story(expected),
            'unsupported story prose, quantity, superiority or availability claim')
    release = plan(inputs, expected)
    require(load(packet / 'release-plan.json') == release, 'release identity or manifest mismatch')
    if case in (None, 'sdk-identity'):
        sdk_identity(inputs)
    if case in (None, 'native-scope'):
        commands = load(inputs / 'lang/commands.json')
        require(any(c['argv'][0] == 'clang' and c['exit'] == 0 for c in commands), 'no native Lang link')
        require(load(inputs / 'antlr/trial-results.json')['native'] is True, 'no native ANTLR result')
        require('clang' in load(inputs / 'bison/trial-results.json')['implementation'], 'no native Bison result')
    if case in (None, 'links'):
        links = re.findall(r'\]\(([^)]+)\)', (packet / 'STORY.md').read_text())
        require(bool(links), 'missing local links')
        for link in links:
            require(':' not in link and safe(packet, link).is_file(), 'broken/nonlocal link: ' + link)
        for link in re.findall(r'\]\(([^)]+)\)', (ROOT / 'docs/comparison-release.md').read_text()):
            require(safe(ROOT / 'docs', link).is_file(), 'broken documentation link: ' + link)
    if case in (None, 'release-dry-run'):
        site_archive(packet, release)
    return {'case': case or 'all', 'status': 'draft-validated', 'final_validation': 'pending',
            'head': git('rev-parse', 'HEAD'), 'manifest_sha256': MANIFEST_HASH,
            'story_sha256': release['story_sha256']}


def prepare(inputs, packet):
    require(not packet.resolve().is_relative_to(ROOT), 'packet must be outside the checkout')
    frozen(inputs)
    packet.mkdir(parents=True, exist_ok=True)
    for row in [{'path': 'MANIFEST.json'}] + load(inputs / 'MANIFEST.json'):
        dst = safe(packet, 'frozen/' + row['path'])
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes((inputs / row['path']).read_bytes())
    data = claims(inputs)
    write_json(packet / 'measurements.json', measurements(data))
    write_json(packet / 'claims.json', data)
    (packet / 'STORY.md').write_text(story(data))
    release = plan(inputs, data)
    write_json(packet / 'release-plan.json', release)
    with (packet / 'site-snapshot.tar.gz').open('wb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', mtime=0, filename='') as compressed:
            with tarfile.open(fileobj=compressed, mode='w') as tar:
                entries = {name: (ROOT / 'web' / name).read_bytes() for name in release['site_files']}
                entries['MANIFEST'] = ''.join(row['sha256'] + '  ' + name + '\n' for name, row in
                                             sorted(release['site_files'].items())).encode()
                for name, content in sorted(entries.items()):
                    info = tarfile.TarInfo(name)
                    info.size, info.mode, info.mtime = len(content), 0o644, 0
                    tar.addfile(info, io.BytesIO(content))
    validate(inputs, packet)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'validate'])
    parser.add_argument('--inputs', type=pathlib.Path, required=True)
    parser.add_argument('--packet', type=pathlib.Path, required=True)
    parser.add_argument('--case', choices=CASES)
    parser.add_argument('--final', action='store_true')
    args = parser.parse_args()
    try:
        if args.action == 'prepare':
            require(not args.final and args.case is None, 'prepare is draft-only')
            prepare(args.inputs.resolve(), args.packet.resolve())
        print(json.dumps(validate(args.inputs.resolve(), args.packet.resolve(), args.case, args.final), sort_keys=True))
    except (ValueError, KeyError, OSError, tarfile.TarError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
