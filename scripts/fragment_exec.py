#!/usr/bin/env python3
"""Opt-in native execution for trusted, explicitly qualified local LLVM fragments.

Cold runs never compile. Qualification compares one bounded, argument-free local
fragment against lli; it is not a semantic or integration-suite certification.
The cache is private executable build output, not an untrusted artifact store.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tempfile

ORACLE = 'fragment-exit-streams-v1'
FLAGS = ['-O0']
LLI_FLAGS = ['--jit-kind=orc']


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tool(name):
    path = Path(shutil.which(name) or name).resolve(strict=True)
    return {'path': str(path), 'sha256': digest(path),
            'version': subprocess.check_output([str(path), '--version']).decode()}


def identity(ir):
    clang, lli = tool('clang'), tool('lli')
    linker_name = subprocess.check_output([clang['path'], '-print-prog-name=ld']).decode().strip()
    linker = tool(linker_name)
    return dict(ir=digest(ir), clang=clang, lli=lli, linker=linker, flags=FLAGS,
                lli_flags=LLI_FLAGS, oracle=ORACLE,
                runner=digest(__file__), system=platform.system(),
                machine=platform.machine(),
                target=subprocess.check_output([clang['path'], '-dumpmachine']).decode().strip())


def key_for(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def eligible(ir):
    # Effects and opaque assembly keep their existing native execution rules.
    try:
        text = ir.read_text()
    except UnicodeDecodeError:
        return False
    return re.search(r'\basm\b|@llvm\.stack(?:save|restore)|\bblockaddress\s*\(', text) is None


def lookup(cache, value):
    try:
        receipt = json.loads((cache / (key_for(value) + '.json')).read_text())
        binary = cache / receipt['binary']
        if binary.parent != cache or receipt['identity'] != value:
            return None
        if receipt['sha256'] != digest(binary) or not os.access(binary, os.X_OK):
            return None
        return binary
    except (OSError, ValueError, KeyError, TypeError):
        return None


def observe(argv, timeout):
    try:
        r = subprocess.run(argv, capture_output=True, timeout=timeout, stdin=subprocess.DEVNULL)
        return dict(exit=r.returncode, stdout=r.stdout.hex(), stderr=r.stderr.hex(), timeout=False)
    except subprocess.TimeoutExpired as e:
        return dict(exit=None, stdout=(e.stdout or b'').hex(), stderr=(e.stderr or b'').hex(), timeout=True)


def qualify(ir, cache, timeout):
    if not eligible(ir):
        raise ValueError('assembly and stack-control fragments require their existing execution path')
    value = identity(ir)
    cache.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Never publish incomplete binaries or receipts. Concurrent readers see only
    # complete immutable executables, with an atomically installed qualification.
    with tempfile.TemporaryDirectory(dir=cache) as tmp:
        binary = Path(tmp) / 'native'
        subprocess.run([value['clang']['path'], *FLAGS, '-fuse-ld=' + value['linker']['path'], str(ir), '-o', str(binary)],
                       check=True, timeout=timeout, capture_output=True)
        reference = observe([value['lli']['path'], *LLI_FLAGS, str(ir)], timeout)
        native = observe([str(binary)], timeout)
        if reference != native or native['timeout'] or native['exit'] < 0:
            raise ValueError('qualification failed: ' + json.dumps(dict(lli=reference, native=native)))
        if identity(ir) != value:
            raise ValueError('inputs changed during qualification')
        name = Path(tmp).name + '.native'
        published = cache / name
        os.replace(binary, published)
        receipt = dict(identity=value, binary=name, sha256=digest(published), observation=reference)
        pending = Path(tmp) / 'receipt.json'
        pending.write_text(json.dumps(receipt, sort_keys=True) + '\n')
        os.replace(pending, cache / (key_for(value) + '.json'))
    return published


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['run', 'qualify', 'resolve'])
    p.add_argument('ir', type=Path)
    p.add_argument('--cache', type=Path, required=True)
    p.add_argument('--timeout', type=float, default=2)
    a = p.parse_args()
    ir, cache = a.ir.resolve(strict=True), a.cache.resolve()
    if a.mode == 'qualify':
        print(qualify(ir, cache, a.timeout))
        return
    binary = None
    if cache.is_dir() and eligible(ir):
        try:
            binary = lookup(cache, identity(ir))
        except (OSError, subprocess.SubprocessError, UnicodeDecodeError):
            # An unavailable native toolchain invalidates hits, not lli runs.
            pass
    command = [str(binary)] if binary else ['lli', *LLI_FLAGS, str(ir)]
    if a.mode == 'resolve':
        # Resolve once outside a bounded timing loop; no implicit qualification.
        print(json.dumps(command))
    else:
        # Inherit streams, stdin, signals and exit status, as direct lli does.
        if binary:
            os.execv(str(binary), command)
        os.execvp('lli', command)


if __name__ == '__main__':
    main()
