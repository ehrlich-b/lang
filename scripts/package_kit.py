#!/usr/bin/env python3
"""Verify and use an extracted local compiler kit (Python 3 standard library)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def member(root, name):
    require(isinstance(name, str) and name and not Path(name).is_absolute()
            and '..' not in Path(name).parts, 'unsafe artifact path')
    path = root / name
    require(not any(p.is_symlink() for p in [path, *path.parents] if p != root.parent),
            'symlink artifact: ' + name)
    require(path.is_file() and root in path.resolve().parents, 'missing artifact: ' + name)
    return path


def verify(root):
    receipt = json.loads((root / 'receipt.json').read_text())
    require(receipt['schema'] == 1, 'unsupported receipt schema')
    artifacts = receipt['artifacts']
    require(isinstance(artifacts, dict) and artifacts, 'missing artifact inventory')
    for name, expected in artifacts.items():
        require(re.fullmatch('[0-9a-f]{64}', expected) is not None, 'invalid artifact hash')
        require(digest(member(root, name)) == expected, 'artifact hash mismatch: ' + name)
    require(set(artifacts) == {str(p.relative_to(root)) for p in root.rglob('*')
                             if p.is_file() and p != root / 'receipt.json'}, 'artifact inventory mismatch')
    for name in ('bin/compiler', 'kit.py', 'README.md', receipt['example'], receipt['metadata']):
        require(name in artifacts, 'untracked required artifact: ' + name)
    metadata = json.loads(member(root, receipt['metadata']).read_text())
    require(metadata['schema'] == 1 and isinstance(metadata['runtime_contract'], str)
            and metadata['runtime_contract'].strip(), 'missing runtime metadata')
    require(isinstance(metadata['runtime_sources'], list), 'missing runtime selection')
    for name in metadata['runtime_sources']:
        require(name in artifacts, 'untracked runtime: ' + name)
    require(isinstance(metadata['licenses'], list) and metadata['licenses'], 'missing license metadata')
    require({n['component'] for n in metadata['licenses']} >= {'compiler', 'reader', 'runtime'},
            'missing license component metadata')
    for notice in metadata['licenses']:
        require(isinstance(notice['component'], str) and notice['component'].strip(), 'missing license component')
        require(notice['file'] in artifacts and member(root, notice['file']).read_text().strip(),
                'missing license notice')
    require(receipt['host']['os'] == 'Linux' and receipt['host']['architecture'] == 'x86_64',
            'unsupported kit profile')
    require(receipt['dependencies']['linkage'] == 'dynamic'
            and receipt['dependencies']['shared_libraries'], 'missing dynamic dependency metadata')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['verify', 'llvm', 'native'])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--clang', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    try:
        receipt = verify(root)
        if args.action == 'verify':
            print('Verified compiler kit')
            return 0
        require(args.output is not None, '--output is required')
        output = args.output.absolute()
        require(root != output and root not in output.parents, 'output must be outside the kit')
        env = dict(os.environ, LANGBE='llvm', LANGOS='linux')
        env.pop('LANG_ROOT', None)
        env.pop('LANG_CLANG', None)
        if args.action == 'native':
            require(args.clang is not None and args.clang.is_absolute() and args.clang.is_file(),
                    'native requires --clang with an explicit absolute executable path')
            env['LANG_CLANG'] = str(args.clang)
        command = [str(root / 'bin/compiler'), str(root / receipt['example']),
                   '--emit=' + ('llvm' if args.action == 'llvm' else 'native'), '-o', str(output)]
        return subprocess.run(command, env=env, check=False).returncode
    except (ValueError, OSError, KeyError, TypeError) as error:
        print('kit: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
