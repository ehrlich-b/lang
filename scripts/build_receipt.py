#!/usr/bin/env python3
"""Bind a compiler and its generated artifacts to the exact build inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()


def inputs():
    # Generated browser outputs and receipts deliberately are not source inputs.
    paths = git('ls-files', 'src', 'std', 'example', 'test/reader_locations',
                'Makefile', 'scripts/build_receipt.py', 'web/build.sh',
                'web/build_compiler.sh', 'web/build_stdlib.js').splitlines()
    return {p: digest(p) for p in paths}


def hashes(root):
    return {str(p): digest(p) for p in sorted(Path(root).rglob('*')) if p.is_file()}


def artifact(path):
    return {'path': str(path), 'sha256': digest(path), 'bytes': Path(path).stat().st_size}


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def check(receipt, compiler):
    assert receipt['compiler']['sha256'] == digest(compiler), 'compiler hash mismatch'
    assert receipt['source']['inputs'] == inputs(), 'source inputs changed; rebuild the compiler'
    assert receipt['compiler']['version'] == subprocess.check_output([str(Path(compiler).resolve()), 'version'], text=True), 'compiler version mismatch'


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
        assert value['source']['inputs'] == inputs(), 'source changed during build'
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
    main()
