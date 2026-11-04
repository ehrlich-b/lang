#!/usr/bin/env python3
"""Reuse a development compiler only when its complete content identity matches."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess

from build_inputs import write_version
from build_receipt import git, inputs
from write_if_changed import write_if_changed

# Includes and requires are checkout-relative, just as in the compiler. Skip
# comments and literal strings so examples in diagnostics do not become inputs.
DIRECTIVE = re.compile(r'//[^\n]*|/\*.*?\*/|\b(include|require)(?:\s|//[^\n]*(?:\n|$)|/\*.*?\*/)*"([^"\n]+)"|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', re.S)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dependencies(sources, previous=None):
    # A graph cannot gain an edge without changing one of its files. Hash every
    # old node first; unchanged bytes let us skip lexing the compiler again.
    if isinstance(previous, dict) and all(p in previous for p in sources):
        try:
            current = {p: digest(p) for p in previous}
            if current == previous:
                return current
        except (OSError, TypeError):
            pass
    pending = list(sources)
    hashes = {}
    while pending:
        path = pending.pop()
        if path in hashes:
            continue
        content = Path(path).read_bytes()
        hashes[path] = hashlib.sha256(content).hexdigest()
        for match in DIRECTIVE.finditer(content.decode()):
            if match[1]:
                pending.append(match[2] + ('.lang' if match[1] == 'require' else ''))
    return hashes


def tool(command):
    executable = shutil.which(command[0])
    if executable is None:
        raise FileNotFoundError(command[0])
    return {'path': str(Path(executable).resolve()), 'sha256': digest(executable),
            'version': subprocess.check_output([*command, '--version'], text=True)}


def run(argv, **kwargs):
    print(shlex.join(argv), flush=True)
    subprocess.run(argv, check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', required=True)
    parser.add_argument('--cc', required=True)
    parser.add_argument('--cflags', required=True)
    parser.add_argument('--langflags', required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--platform', required=True)
    parser.add_argument('--arch', required=True)
    parser.add_argument('--bootstrap', required=True)
    parser.add_argument('--os-layer', required=True)
    parser.add_argument('sources', nargs='+')
    args = parser.parse_args()
    cc = shlex.split(args.cc)
    cflags = shlex.split(args.cflags)
    langflags = shlex.split(args.langflags)
    Path('out').mkdir(exist_ok=True)
    # Serialize compiler invocations; failed builds never install a valid identity.
    with Path('out/dev-build.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        write_if_changed('std/os.lang', f'include "{args.os_layer}"\n'.encode())
        libc = 'system' if args.platform == 'macos' or 'libc' in args.os_layer else 'none'
        write_version(args.version, 'llvm', args.platform, args.arch, libc, args.bootstrap)
        if not Path(args.seed).exists() and not Path(args.seed).is_symlink():
            run(['make', '-j1', 'init'])
        state = Path('out/dev-build.json')
        try:
            previous = json.loads(state.read_text())
            old_identity = previous['identity']
        except (OSError, ValueError, KeyError, TypeError):
            previous, old_identity = {}, {}
        old_sources = (old_identity.get('sources') if isinstance(old_identity, dict)
                       and old_identity.get('source_order') == args.sources else None)
        identity = {
            'schema': 1, 'sources': dependencies(args.sources, old_sources),
            # Keep the existing broader receipt fresh even when an unrelated
            # source changes twice while the checkout is already dirty.
            'receipt': {'revision': git('rev-parse', 'HEAD'), 'inputs': inputs()},
            'recipe': {p: digest(p) for p in ['Makefile', 'scripts/dev_build.py',
                       'scripts/write_if_changed.py', 'scripts/build_inputs.py',
                       'scripts/build_receipt.py']},
            'seed': {'path': str(Path(args.seed).resolve()), 'sha256': digest(args.seed)},
            'toolchain': tool(cc), 'cc': cc, 'cflags': cflags, 'langflags': langflags,
            'source_order': args.sources, 'version': args.version, 'platform': args.platform,
            'environment': {k: v for k, v in os.environ.items()
                            if k.startswith(('LC_', 'CCC_', 'CLANG_')) or k in
                            ('LANG', 'LANGBE', 'LANGOS', 'LANGLIBC', 'LANG_ROOT', 'PATH', 'CPATH', 'C_INCLUDE_PATH', 'LIBRARY_PATH',
                             'SDKROOT', 'MACOSX_DEPLOYMENT_TARGET', 'LD_LIBRARY_PATH')},
        }
        binary = f'out/lang_dev_{args.version}'
        ir = binary + '.ll'
        artifacts = [binary, ir, 'out/build-input.json', 'out/build-receipt.json']
        try:
            if (previous['identity'] == identity and
                    Path('out/lang_next').resolve() == Path(binary).resolve() and
                    previous['artifacts'] == {p: digest(p) for p in artifacts}):
                print('Development compiler is up to date.')
                return
        except (OSError, ValueError, KeyError):
            pass
        run(['python3', 'scripts/build_receipt.py', 'start', '--mode', 'build',
             '--compiler', args.seed, '--output', 'out/build-input.json'])
        env = dict(os.environ, LANGBE='llvm', LANGOS=args.platform)
        run([args.seed, *args.sources, *langflags, '-o', ir], env=env)
        run([*cc, *cflags, ir, '-o', binary])
        # Keep the established versioned output names and provenance receipts.
        subprocess.run(['ln', '-sf', Path(binary).name, 'out/lang_next'], check=True)
        run(['python3', 'scripts/build_receipt.py', 'finish', '--input',
             'out/build-input.json', '--compiler', 'out/lang_next', '--output',
             'out/build-receipt.json', '--artifact', ir])
        if (identity['sources'] != dependencies(args.sources) or
                identity['seed']['sha256'] != digest(args.seed)):
            raise RuntimeError('Build inputs changed during compilation; retry the build')
        write_if_changed(state, (json.dumps({'identity': identity, 'artifacts':
                         {p: digest(p) for p in artifacts}}, sort_keys=True, indent=2) + '\n').encode())
        print('Created: out/lang_next -> ' + Path(binary).name)


if __name__ == '__main__':
    main()
