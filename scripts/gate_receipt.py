#!/usr/bin/env python3
"""Reuse complete local verification, never promotion, in a trusted local cache.

LANG_VERIFY_CACHE can share receipts between disposable checkouts. The default
is shared by local checkouts. Integration can force a fresh run with
LANG_VERIFY_FRESH=1; promotion never goes through this module.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import subprocess
import sys

SCHEMA = 1
GENERATED = {'std/os.lang'}
OUTPUTS = ['out/verify-input.json', 'out/verify-receipt.json',
           'out/version_info.lang', 'std/os.lang']


class UnsupportedInputClosure(ValueError):
    """An input tree cannot be safely represented by the local inventory."""


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])


def environment_value(key, value, root):
    if key in ('MAKEFLAGS', 'MFLAGS'):
        # Transport endpoints differ per invocation; scheduling width and every
        # semantic option remain in the identity. Support GNU make FIFO and fd forms.
        value = re.sub(r'--jobserver-(?:auth|fds)=\S+', '--jobserver', value)
    return value.replace(str(root), '<checkout>')


def make_policy(command):
    """Fail closed for non-verifying modes and unknown make input closures."""
    flags = []
    for name in ('MAKEFLAGS', 'MFLAGS', 'GNUMAKEFLAGS'):
        flags.extend(shlex.split(os.environ.get(name, '')))
    flags.extend(command[1:])
    unsupported = bool(os.environ.get('MAKEOVERRIDES', '').strip())
    for token in flags:
        if token.startswith('--'):
            option = token.split('=', 1)[0]
            if option in ('--ignore-errors', '--just-print', '--dry-run',
                          '--recon', '--question', '--touch'):
                raise ValueError('make mode cannot certify verification: ' + token)
            if option in ('--eval', '--file', '--makefile', '--include-dir',
                          '--environment-overrides'):
                unsupported = True
        elif '=' in token:
            # Even unchanged override text can select mutable external files.
            unsupported = True
        elif token.startswith('-') or token.isalpha() and token != '_verify-complete':
            short = token.lstrip('-')
            if any(letter in short for letter in 'inqt'):
                raise ValueError('make mode cannot certify verification: ' + token)
            if any(letter in short for letter in 'efI'):
                unsupported = True
    return not unsupported


def identity(root, command):
    # All versioned inputs, including every suite and launcher, plus new files.
    # Include ignored source fixtures too; only known generated files are omitted.
    names = set(os.fsdecode(p) for p in git(
        root, 'ls-files', '-z', '--cached', '--others', '--exclude-standard').split(b'\0') if p)
    for directory in ('src', 'std', 'test', 'scripts', 'example', 'bootstrap/current'):
        for p in (root / directory).rglob('*'):
            if p.is_symlink() and not p.is_file():
                raise UnsupportedInputClosure('non-file symlink: ' + str(p.relative_to(root)))
            if p.is_file() and '__pycache__' not in p.parts:
                names.add(str(p.relative_to(root)))
    inputs = {}
    for name in sorted(names - GENERATED):
        p = root / name
        if p.is_symlink() and not p.is_file():
            raise UnsupportedInputClosure('non-file symlink: ' + name)
        inputs[name] = ({'sha256': digest(p), 'mode': p.stat().st_mode & 0o777,
                         'link': os.readlink(p) if p.is_symlink() else None}
                        if p.is_file() else None)
    # Compiler overrides may be wrappers with arbitrary external dependencies.
    # Their closure is unknown, so run verification without a reusable receipt.
    if os.environ.get('CLANG'):
        raise UnsupportedInputClosure('CLANG override has an unsupported tool closure')
    tools = {}
    for name in ('clang', 'lli', 'node', 'python3', 'make', 'bash', 'sh',
                 'ld', 'as', 'timeout', 'diff', 'shasum'):
        found = shutil.which(name)
        if found:
            path = Path(found).resolve()
            row = {'path': str(path), 'sha256': digest(path)}
            # Dynamic tool dependencies are part of toolchain identity as well.
            if platform.system() == 'Linux':
                libraries = subprocess.run(['ldd', str(path)], capture_output=True, text=True)
                deps = {}
                for token in libraries.stdout.split():
                    if token.startswith('/') and Path(token).is_file():
                        deps[token] = digest(token)
                row['libraries'] = deps
            if name == 'clang':
                dependencies = {}
                for filename in ('crt1.o', 'Scrt1.o', 'crti.o', 'crtn.o',
                                 'crtbeginS.o', 'crtendS.o', 'libgcc.a', 'libc.so'):
                    result = subprocess.check_output([str(path), '-print-file-name=' + filename], text=True).strip()
                    if Path(result).is_file():
                        dependencies[result] = digest(result)
                resource_dir = Path(subprocess.check_output(
                    [str(path), '-print-resource-dir'], text=True).strip())
                for resource in resource_dir.rglob('*'):
                    if resource.is_file():
                        dependencies[str(resource)] = digest(resource)
                row['resources'] = dependencies
            tools[name] = row
        else:
            tools[name] = None
    # Conservative: differing ambient options miss rather than silently reuse.
    environment = {k: hashlib.sha256(environment_value(k, v, root).encode()).hexdigest()
                   for k, v in os.environ.items()
                   if k not in ('PWD', 'OLDPWD', 'SHLVL', '_', 'LANG_VERIFY_CACHE',
                                'LANG_VERIFY_FRESH', 'MAKELEVEL')}
    return {'schema': SCHEMA, 'candidate': git(root, 'rev-parse', 'HEAD').decode().strip(),
            'candidate_short': git(root, 'rev-parse', '--short', 'HEAD').decode().strip(),
            'inputs': inputs, 'tools': tools, 'environment': environment,
            'makefiles': {name: digest(root / name) if (root / name).is_file() else None
                          for name in os.environ.get('MAKEFILES', '').split()},
            'host': [platform.system(), platform.machine(), platform.release()],
            'command': command}


def save(path, value):
    # Called under the cache lock; an interrupted write is an invalid receipt.
    path.write_bytes(encoded(value) + b'\n')


def consume(root, cache, get_identity, executor, outputs, *, fresh=False):
    """Execute once under a per-identity lock and publish success last.

    executor(log) returns an exit code. Tests use the same protocol with a tiny
    executor; they cannot publish a receipt for the production command identity.
    """
    cache.mkdir(parents=True, exist_ok=True)
    before = get_identity()
    key = hashlib.sha256(encoded(before)).hexdigest()
    entry = cache / key
    entry.mkdir(exist_ok=True)
    with (entry / 'lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        record = entry / 'receipt.json'
        try:
            receipt = json.loads(record.read_text())
            if (not isinstance(receipt, dict) or
                    not isinstance(receipt.get('outputs'), dict) or
                    not isinstance(receipt.get('root'), str)):
                raise ValueError('incomplete receipt')
            for row in receipt['outputs'].values():
                if (not isinstance(row, dict) or type(row.get('mode')) is not int or
                        not 0 <= row['mode'] <= 0o777):
                    raise ValueError('malformed output')
            valid = (not fresh and receipt['schema'] == SCHEMA and
                     receipt['status'] == 'complete' and receipt['identity'] == before and
                     receipt['exit'] == 0 and receipt['outputs'] and
                     set(outputs) == set(receipt['outputs']) and
                     receipt['log_sha256'] == digest(entry / 'execution.log'))
            for name, row in receipt['outputs'].items():
                path = Path(name)
                if path.is_absolute() or '..' in path.parts:
                    valid = False
                    break
                valid &= digest(entry / 'files' / name) == row['sha256']
            if valid and get_identity() == before:
                for name, row in receipt['outputs'].items():
                    target = root / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    data = (entry / 'files' / name).read_bytes()
                    if name in ('out/verify-input.json', 'out/verify-receipt.json'):
                        # Existing build receipts name absolute artifact paths.
                        data = data.replace(receipt['root'].encode(), str(root).encode())
                    target.write_bytes(data)
                    target.chmod(row['mode'])
                print((entry / 'execution.log').read_text(errors='replace').replace(receipt['root'], str(root)), end='')
                print(f'Completed verification receipt reused: {key}', flush=True)
                return 0
        except (OSError, ValueError, KeyError, TypeError):
            pass
        save(record, {'schema': SCHEMA, 'status': 'incomplete', 'identity': before})
        start = os.times()
        with (entry / 'execution.log').open('wb') as log:
            status = executor(log)
        finish = os.times()
        value = {'schema': SCHEMA, 'status': 'failed', 'identity': before,
                 'root': str(root), 'exit': status,
                 'cpu_seconds': sum(finish[:4]) - sum(start[:4])}
        if status == 0 and get_identity() == before:
            inventory = {}
            for name in outputs:
                source = root / name
                target = entry / 'files' / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                inventory[name] = {'sha256': digest(target), 'mode': source.stat().st_mode & 0o777}
            value.update(status='complete', outputs=inventory,
                         log_sha256=digest(entry / 'execution.log'))
        elif status == 0:
            status = 1
            value['exit'] = status
            print('Verification inputs changed during execution; no success receipt', file=sys.stderr)
        save(record, value)
        print((entry / 'execution.log').read_text(errors='replace'), end='')
        return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('missing complete verification command')
    # The launcher's MAKE assignment is fixed, not an input override. Inherited
    # overrides remain visible in MAKEFLAGS/MAKEOVERRIDES and disable reuse.
    try:
        reusable = make_policy([arg for arg in command if arg != 'MAKE=make'])
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2
    root = Path.cwd().resolve()
    default_cache = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')) / 'lang/verification'
    cache = Path(os.environ.get('LANG_VERIFY_CACHE', default_cache)).resolve()
    (root / 'out').mkdir(exist_ok=True)
    # Different input identities must not race on this checkout's generated files.
    with (root / 'out/verification.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        def execute(log):
            return subprocess.run(command, stdout=log, stderr=subprocess.STDOUT).returncode
        outputs = OUTPUTS + ['out/bootstrap_verify/' + name for name in (
            'ctrusted', 'kernel1', 'kernel1.ll', 'kernel2', 'kernel2.ll',
            'kernel3.ll', 'reader_ast1.ast', 'reader_ast2.ast')]
        if os.environ.get('MAKEFILES', '').strip() or not reusable:
            # Extra makefiles can include arbitrary external prerequisites and
            # recipes. Their transitive closure is not our repository closure.
            # Run normally without consuming or publishing any cached success.
            print('Unsupported make inputs supplied; verification receipt reuse disabled', flush=True)
            return subprocess.run(command).returncode
        try:
            return consume(root, cache, lambda: identity(root, command), execute, outputs,
                           fresh=os.environ.get('LANG_VERIFY_FRESH') == '1')
        except UnsupportedInputClosure as error:
            print(f'Unsupported input closure; verification receipt reuse disabled: {error}', flush=True)
            return subprocess.run(command).returncode


if __name__ == '__main__':
    sys.exit(main())
