#!/usr/bin/env python3
"""Reproduce the current compiler baseline on this native host, without publishing."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='new directory for logs and receipt.json')
    args = parser.parse_args()
    os.chdir(ROOT)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    # Avoid inherited cross-target/compiler selections silently changing the proof.
    env = dict(os.environ)
    for key in ('LANGBE', 'LANGOS', 'COMPILER', 'LANGLIBC', 'LANG_ROOT', 'LANG_CACHE', 'LANG_LAYOUT_PROFILE'):
        env.pop(key, None)
    env.update(JOBS='2', PUBLISH_BOOTSTRAP='0', COMPILER=str(ROOT / 'out/bootstrap_verify/kernel2'), TMPDIR=str(output / 'tmp'),
               EFFECTS_EVIDENCE_DIR=str(output / 'effects'))
    (output / 'tmp').mkdir()
    receipt = {'schema': 1, 'started': datetime.now(timezone.utc).isoformat(),
               'host': {'system': platform.system(), 'machine': platform.machine()},
               'gates': [], 'tools': {}, 'complete': False}

    def git(*args):
        return subprocess.check_output(['git', *args], text=True).strip()

    def hashes():
        return {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(Path('bootstrap/current').rglob('*')) if p.is_file()}

    receipt.update(head=git('rev-parse', 'HEAD'), branch=git('branch', '--show-current'),
                   status_before=git('status', '--porcelain'), bootstrap_before=hashes())

    def save():
        (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')

    def gate(name, command, *, tokens=(), skips=None):
        log = output / (name + '.txt')
        gate_env = dict(env, EFFECTS_EVIDENCE_DIR=str(output / (name + '-effects')))
        with log.open('w') as stream:
            result = subprocess.run(command, env=gate_env, stdout=stream, stderr=subprocess.STDOUT)
        text = log.read_text(errors='replace')
        row = {'name': name, 'command': command, 'exit': result.returncode,
               'log': log.name, 'pass': result.returncode == 0 and all(token in text for token in tokens)}
        if name == 'verify' and row['pass']:
            artifacts = ['kernel2.ll', 'kernel3.ll', 'reader_ast1.ast', 'reader_ast2.ast']
            # Verification prints both fixed-point pairs and never promotes.
            receipt['fixed_points'] = {}
            for artifact in artifacts:
                match = re.search(r'^([0-9a-f]{64})\s+[^\n]*/' + re.escape(artifact) + r'$', text, re.M)
                if match is None:
                    raise RuntimeError(f'bootstrap did not record fixed-point hash: {artifact}')
                receipt['fixed_points'][artifact] = match.group(1)
            points = receipt['fixed_points']
            row['pass'] &= points['kernel2.ll'] == points['kernel3.ll'] and points['reader_ast1.ast'] == points['reader_ast2.ast']
        if skips is not None:
            actual = sorted(re.findall(r'^SKIP .+$', text, re.M))
            expected = json.loads(Path('test/baseline_skips.json').read_text())[skips]
            row.update(skips=actual, expected_skips=expected)
            row['pass'] &= actual == expected
        receipt['gates'].append(row)
        save()
        print(f'{"PASS" if row["pass"] else "FAIL"} {name}: {log}', flush=True)
        return row['pass']

    try:
        if (platform.system(), platform.machine()) not in [('Linux', 'x86_64'), ('Darwin', 'arm64')]:
            raise RuntimeError('supported native baseline hosts: Linux x86_64 and macOS arm64')
        tools = {'clang': ['--version'], 'lli': ['--version'], 'wasm-ld': ['--version'],
                 'node': ['--version'], 'make': ['--version'], 'python3': ['--version']}
        if platform.system() == 'Linux':
            tools['ld.lld'] = ['--version']
        for tool, flags in tools.items():
            path = shutil.which(tool)
            if path is None:
                raise RuntimeError(f'required baseline tool missing: {tool}')
            version = subprocess.run([path, *flags], capture_output=True, text=True, check=True)
            receipt['tools'][tool] = {'path': path, 'version': version.stdout + version.stderr}
        save()
        native_skips = 'llvm-macos' if platform.system() == 'Darwin' else 'llvm-linux'
        commands = [
            ('verify', ['make', 'verify'],
             ('LLVM FIXED POINT VERIFIED', 'AST FIXED POINT VERIFIED'), native_skips),
            ('llvm', ['test/run_llvm_suite.sh'], ('Passed:',), native_skips),
            ('effects', [sys.executable, 'test/run_effects_safety.py'], ('Effects safety: PASS',), None),
            ('wasm', ['test/run_wasm_suite.sh'], ('wasm suite:',), 'llvm-wasm32'),
            ('direct-wasm', ['make', 'test-direct-wasm'], ('direct wasm: passed',), None),
            ('compiler-wasm', ['make', 'test-compiler-wasm'], ('PASS compiler_wasm_e2e',), None),
            ('profiles', [sys.executable, 'test/run_profile_checks.py', '--output', str(output / 'profiles')], (), None),
        ]
        for name, command, tokens, skips in commands:
            if not gate(name, command, tokens=tokens, skips=skips):
                return 1
        if hashes() != receipt['bootstrap_before']:
            raise RuntimeError('non-promoting baseline changed the preserved seed')
        receipt['complete'] = True
        return 0
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        receipt['error'] = str(error)
        print(f'FAIL baseline: {error}', file=sys.stderr)
        return 1
    finally:
        receipt.update(finished=datetime.now(timezone.utc).isoformat(),
                       bootstrap_after=hashes(), status_after=git('status', '--porcelain'))
        save()


if __name__ == '__main__':
    raise SystemExit(main())
