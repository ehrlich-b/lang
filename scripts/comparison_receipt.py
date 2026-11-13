#!/usr/bin/env python3
"""Create and check comparison receipts against a pinned, retained trial archive.

This validates historical captures; it does not execute historical commands or
attest to their original capture environment. The caller supplies the trusted
archive revision, rather than trusting an identity asserted by the receipt.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ARMS = ('lang', 'bison', 'antlr')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])


def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate JSON field: ' + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(), object_pairs_hook=unique)


def inside(root, name):
    require(isinstance(name, str) and name and not Path(name).is_absolute(),
            'expected relative evidence path')
    path = (root / name).resolve()
    require(path.is_relative_to(root.resolve()) and path != root.resolve(),
            'evidence path escapes root')
    return path


def archive(inputs, revision):
    require(git(inputs, 'rev-parse', 'HEAD').decode().strip() == revision,
            'wrong trial archive revision')
    manifest = inputs / 'MANIFEST.json'
    require(manifest.read_bytes() == git(inputs, 'show', revision + ':MANIFEST.json'),
            'changed archive manifest')
    hashes = {}
    for item in load(manifest):
        name = item['path']
        data = inside(inputs, name).read_bytes()
        require(digest(data) == item['sha256'], 'changed trial input: ' + name)
        hashes[name] = digest(data)
    require(len(hashes) == len(load(manifest)), 'duplicate manifest path')
    return hashes


def termination(code):
    require(type(code) is int, 'return code must be an integer')
    # Negative Python subprocess codes mean a signal. A positive shell 128+N
    # remains an exit status: there is no evidence that it was a signal.
    return {'kind': 'signal' if code < 0 else 'exit',
            'value': -code if code < 0 else code}


def command(row):
    if 'argv' in row:
        argv = row['argv']
        require(isinstance(argv, list) and bool(argv) and
                all(isinstance(x, str) and x for x in argv), 'missing command argv')
        return {'argv': argv}
    require(isinstance(row.get('command'), str) and row['command'].strip(),
            'missing command text')
    return {'shell': row['command']}


def records(inputs):
    """Adapt the three frozen formats without flattening failures into passes."""
    result = []
    for arm in ARMS:
        raw = load(inputs / arm / 'trial-results.json')
        cases = raw if isinstance(raw, list) else raw.get('cases', raw.get('results'))
        commands = (load(inputs / arm / 'commands.json') if arm == 'lang'
                    else raw['commands'])
        require(isinstance(cases, list) and len(cases) == 10, 'expected ten trial cases')
        expected = {'sample.conf'} | {
            'fixtures/' + p.name for p in (inputs / arm / 'fixtures').iterdir()}
        require({c['file'] for c in cases} == expected, 'trial fixture inventory mismatch')
        for scope, rows in [('command', commands), ('case', cases)]:
            for index, row in enumerate(rows):
                cmd = row
                if scope == 'case' and 'argv' not in row:
                    # These formats retain case commands in their command history.
                    matches = [r for r in commands if
                               all(r.get(k) == row[k] for k in ('exit', 'stdout', 'stderr'))
                               and row['file'] in json.dumps(command(r))]
                    require(bool(matches), 'case has no captured command: ' + row['file'])
                    cmd = matches[0]
                require(all(isinstance(row.get(k), str) for k in ('stdout', 'stderr')),
                        'missing captured stream')
                value = {'id': f'{arm}/{scope}/{index}', 'arm': arm, 'scope': scope,
                         'command': command(cmd), 'returncode': row['exit'],
                         'termination': termination(row['exit']),
                         'succeeded': row['exit'] == 0,
                         'stdout': row['stdout'], 'stderr': row['stderr']}
                if scope == 'case':
                    require(type(row['valid']) is bool, 'missing fixture expectation')
                    value.update(fixture=row['file'], expected_valid=row['valid'])
                result.append(value)
    return result


def identity(repo, inputs, revision):
    hashes = archive(inputs, revision)
    brief = hashes['trial1/brief.md']
    require(all(hashes[arm + '/brief.md'] == brief for arm in ARMS),
            'comparison briefs differ')
    return {'head': git(repo, 'rev-parse', 'HEAD').decode().strip(),
            'archive_revision': revision,
            'manifest_sha256': digest((inputs / 'MANIFEST.json').read_bytes()),
            'inputs': hashes, 'brief_sha256': brief}


def create(repo, inputs, revision, output):
    source = identity(repo, inputs, revision)
    rows = records(inputs)
    root = output.parent.resolve()
    for row in rows:
        for stream in ('stdout', 'stderr'):
            data = row[stream].encode()
            # Content addressed, shared between mutants; empty streams are files.
            sha = digest(data)
            name = 'streams/' + sha
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            row[stream] = {'path': name, 'sha256': sha}
    receipt = {'schema': 1, 'source': source,
               'arms': {arm: {'head': source['head'],
                              'brief_sha256': source['brief_sha256']} for arm in ARMS},
               'records': rows}
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')


def check(repo, inputs, revision, receipt, evidence):
    value = load(receipt)
    require(isinstance(value, dict) and set(value) == {'schema', 'source', 'arms', 'records'},
            'malformed comparison receipt fields')
    require(type(value.get('schema')) is int and value['schema'] == 1,
            'unsupported comparison receipt schema')
    expected_source = identity(repo, inputs, revision)
    require(value.get('source') == expected_source, 'stale comparison source or changed brief')
    require(value.get('arms') == {
        arm: {'head': expected_source['head'],
              'brief_sha256': expected_source['brief_sha256']} for arm in ARMS},
        'stale arm head or changed arm brief')
    expected = records(inputs)
    actual = value.get('records')
    require(isinstance(actual, list) and len(actual) == len(expected),
            'missing comparison records')
    for got, want in zip(actual, expected):
        require(isinstance(got, dict), 'malformed comparison record')
        normalized = dict(got)
        for stream in ('stdout', 'stderr'):
            ref = got.get(stream)
            require(isinstance(ref, dict) and set(ref) == {'path', 'sha256'},
                    'missing ' + stream + ' evidence')
            data = inside(evidence, ref['path']).read_bytes()
            require(digest(data) == ref['sha256'], stream + ' evidence hash mismatch')
            require(data == want[stream].encode(), stream + ' differs from retained capture')
            normalized[stream] = data.decode()
        # Compare types as well as values (JSON true must not stand for exit 1).
        require(json.dumps(normalized, sort_keys=True) == json.dumps(want, sort_keys=True),
                'forged result or missing command: ' + want['id'])
    print(f'PASS: {len(expected)} comparison records bound to current HEAD and frozen inputs')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['create', 'check'])
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--inputs', type=Path, required=True)
    p.add_argument('--inputs-revision', required=True)
    p.add_argument('--receipt', type=Path, required=True)
    p.add_argument('--evidence', type=Path)
    a = p.parse_args()
    if a.action == 'create':
        create(a.repo, a.inputs, a.inputs_revision, a.receipt)
    else:
        check(a.repo, a.inputs, a.inputs_revision, a.receipt,
              a.evidence or a.receipt.parent)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as error:
        print(f'comparison receipt rejected: {error}', file=sys.stderr)
        sys.exit(1)
