#!/usr/bin/env python3
"""Bind a compiler and its generated artifacts to the exact build inputs."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()


def inputs():
    # Generated browser outputs and receipts deliberately are not source inputs.
    paths = git('ls-files', 'src', 'std', 'example', 'test/reader_locations',
                'Makefile', 'scripts/build_receipt.py', 'scripts/lang_package.py',
                'scripts/package_kit.py', 'web/build.sh',
                'web/build_compiler.sh', 'web/build_stdlib.js').splitlines()
    return {p: digest(p) for p in paths}


def hashes(root):
    return {str(p): digest(p) for p in sorted(Path(root).rglob('*')) if p.is_file()}


def artifact(path):
    return {'path': str(path), 'sha256': digest(path), 'bytes': Path(path).stat().st_size}


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_artifact(value):
    require(isinstance(value, dict), 'malformed artifact')
    require(isinstance(value.get('path'), str) and bool(value['path']), 'missing artifact path')
    require(isinstance(value.get('sha256'), str) and
            re.fullmatch(r'[0-9a-f]{64}', value['sha256']), 'malformed artifact hash')
    require(type(value.get('bytes')) is int and value['bytes'] >= 0, 'malformed artifact size')


def validate_inputs(value):
    require(isinstance(value, dict) and bool(value), 'malformed input hashes')
    for path, sha in value.items():
        require(isinstance(path, str) and bool(path) and isinstance(sha, str) and
                re.fullmatch(r'[0-9a-f]{64}', sha), 'malformed input hash')


def validate(receipt, finished=False):
    require(isinstance(receipt, dict), 'malformed receipt')
    require(type(receipt.get('schema')) is int and receipt['schema'] == 1, 'unsupported receipt schema')
    require(receipt.get('mode') in ('build', 'verify', 'promotion'), 'malformed build mode')
    source = receipt.get('source')
    require(isinstance(source, dict), 'malformed source identity')
    require(isinstance(source.get('revision'), str) and
            re.fullmatch(r'[0-9a-f]{40}', source['revision']), 'malformed source revision')
    require(type(source.get('dirty')) is bool, 'malformed source status')
    validate_inputs(source.get('inputs'))
    bootstrap = receipt.get('bootstrap')
    require(isinstance(bootstrap, dict) and isinstance(bootstrap.get('identity'), str) and
            bool(bootstrap['identity']), 'malformed bootstrap identity')
    validate_inputs(bootstrap.get('inputs'))
    validate_artifact(receipt.get('builder'))
    if finished:
        compiler = receipt.get('compiler')
        validate_artifact(compiler)
        require(isinstance(compiler.get('version'), str) and bool(compiler['version']),
                'malformed compiler version')
        require(isinstance(receipt.get('artifacts'), dict), 'malformed artifact inventory')
        for item in receipt['artifacts'].values():
            validate_artifact(item)


def check(receipt, compiler):
    validate(receipt, finished=True)
    require(receipt['source']['revision'] == git('rev-parse', 'HEAD'), 'stale source revision')
    require(receipt['compiler']['sha256'] == digest(compiler), 'compiler hash mismatch')
    require(receipt['compiler']['bytes'] == Path(compiler).stat().st_size, 'compiler size mismatch')
    require(receipt['source']['inputs'] == inputs(), 'source inputs changed; rebuild the compiler')
    require(receipt['compiler']['version'] == subprocess.check_output(
        [str(Path(compiler).resolve()), 'version'], text=True), 'compiler version mismatch')

    for path, expected in receipt['artifacts'].items():
        require(expected['sha256'] == digest(path), 'artifact hash mismatch: ' + path)
        require(expected['bytes'] == Path(path).stat().st_size, 'artifact size mismatch: ' + path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['start', 'finish', 'check', 'web-version', 'web'])
    parser.add_argument('--input')
    parser.add_argument('--output')
    parser.add_argument('--compiler')
    parser.add_argument('--mode', choices=['build', 'verify', 'promotion'])
    parser.add_argument('--artifact', action='append', default=[])
    args = parser.parse_args()
    if args.action == 'start':
        paths = inputs()
        value = {'schema': 1, 'mode': args.mode,
                 'source': {'revision': git('rev-parse', 'HEAD'), 'inputs': paths,
                            'dirty': bool(git('status', '--porcelain', '--', *paths))},
                 'bootstrap': {'identity': Path('bootstrap/current/COMMIT').read_text().strip(),
                               'inputs': hashes('bootstrap/current')},
                 'builder': artifact(args.compiler)}
        write(args.output, value)
        return
    value = json.loads(Path(args.input).read_text())
    if args.action == 'finish':
        validate(value)
        require(value['source']['inputs'] == inputs(), 'source changed during build')
        value['compiler'] = artifact(args.compiler)
        value['compiler']['version'] = subprocess.check_output([str(Path(args.compiler).resolve()), 'version'], text=True)
        value['artifacts'] = {p: artifact(p) for p in args.artifact}
        write(args.output, value)
    elif args.action == 'check':
        check(value, args.compiler)
        print(json.dumps({'source': value['source']['revision'], 'compiler': artifact(args.compiler)}))
    elif args.action == 'web-version':
        check(value, args.compiler)
        # Browser identity describes the wasm target, never the native builder.
        commit = value['source']['revision'][:7] + ('-dirty' if value['source']['dirty'] else '')
        constants = dict(LANG_VERSION='0.1.0', LANG_COMMIT=commit, LANG_BUILD_BACKEND='llvm',
                         LANG_BUILD_OS='wasm', LANG_BUILD_ARCH='wasm32', LANG_BUILD_LIBC='system',
                         LANG_BOOTSTRAP_FROM=value['bootstrap']['identity'])
        Path(args.output).write_text(''.join(f'var {k} *u8 = {json.dumps(v)};\n' for k, v in constants.items()))
    else:
        check(value, args.compiler)
        write(args.output, {'schema': 1, 'source': value['source'], 'bootstrap': value['bootstrap'],
                            'builder': value['compiler'],
                            'version': Path('out/web_version_info.lang').read_text(),
                            'artifacts': {p: artifact(p) for p in args.artifact}})


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as error:
        print(f'receipt validation failed: {error}', file=sys.stderr)
        sys.exit(1)
