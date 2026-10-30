#!/usr/bin/env python3
"""Compile whole official Lua test files and report each target's outcome."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / 'conformance/lua/lua-5.4.8-tests.tar.gz'
SHA256 = '9581d5a7c39ffbf29b8ccde2709083c380f7bbddbd968dcb15712d2f2e33f4e5'
READER = ROOT / 'example/lua/lua.lang'


def run(args, env, cwd=ROOT):
    try:
        p = subprocess.run([str(a) for a in args], cwd=cwd, env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        return p.returncode, (p.stderr + p.stdout).decode('utf-8', 'replace')[-1000:]
    except subprocess.TimeoutExpired:
        return 124, 'timed out after 30 seconds'


def compile_and_run(compiler, source, temp, target):
    env = dict(os.environ, LANG_CACHE=str(temp / 'cache'), LANGBE='llvm', LANGOS='linux')
    ast = temp / 'program.ast'
    status, detail = run([compiler, 'read', READER, source, '-o', ast], env)
    if status:
        return {'passed': False, 'stage': 'reader', 'detail': detail.strip()}
    env.update(LANGBE=target, LANGOS='wasm' if target == 'wasm' else 'linux')
    output = temp / ('program.wasm' if target == 'wasm' else 'program.ll')
    status, detail = run([compiler, '--from-ast', ast, '--ast-source', source, '-o', output], env)
    if status:
        return {'passed': False, 'stage': 'compile', 'detail': detail.strip()}
    if target == 'llvm':
        binary = temp / 'program'
        status, detail = run(['clang', '-O0', output, '-o', binary], env)
        if status:
            return {'passed': False, 'stage': 'link', 'detail': detail.strip()}
        command = [binary]
    else:
        command = ['node', ROOT / 'test/wasm_host.js', output]
    status, detail = run(command, env)
    return {'passed': status == 0, 'stage': 'run', 'exit': status, 'detail': detail.strip()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--compiler', default='out/lang')
    parser.add_argument('--report', required=True)
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    compiler = (ROOT / args.compiler).resolve()
    scratch = ROOT.parent / 'scratch'
    scratch.mkdir(exist_ok=True)
    if hashlib.sha256(ARCHIVE.read_bytes()).hexdigest() != SHA256:
        raise SystemExit('official archive checksum mismatch')
    with tempfile.TemporaryDirectory(dir=scratch, prefix='lua-score-') as directory:
        temp = Path(directory)
        cases = []
        if args.smoke:
            for name in ['arithmetic.lua', 'false.lua', 'unsupported.lua', 'long-comment.lua']:
                cases.append((name, (ROOT / 'test/lua' / name).read_bytes()))
            endings = json.loads((ROOT / 'test/lua/comment-newlines.json').read_text())
            cases.extend((name, source.encode('utf-8')) for name, source in endings.items())
        else:
            with tarfile.open(ARCHIVE, 'r:gz') as tar:
                for member in sorted(tar.getmembers(), key=lambda m: m.name):
                    if member.isfile() and member.name.endswith('.lua'):
                        cases.append((member.name, tar.extractfile(member).read()))
        rows = []
        for index, (name, data) in enumerate(cases):
            source = temp / 'source.lua'
            source.write_bytes(data)
            results = {target: compile_and_run(compiler, source, temp, target)
                       for target in ('llvm', 'wasm')}
            rows.append({'file': name, **results})
            print(name, *(f"{target}={'PASS' if results[target]['passed'] else 'FAIL'}({results[target]['stage']})" for target in results), flush=True)
        report = {'suite': 'Lua 5.4.8 official files' if not args.smoke else 'reader smoke',
                  'archive_sha256': SHA256, 'reader_lines': len(READER.read_text().splitlines()),
                  'results': rows,
                  'totals': {target: {'passed': sum(r[target]['passed'] for r in rows),
                                      'failed': sum(not r[target]['passed'] for r in rows)}
                             for target in ('llvm', 'wasm')}}
        Path(args.report).write_text(json.dumps(report, indent=2) + '\n')
        if args.smoke:
            expected = [True, False, False, False, False, False, False]
            if any([r[t]['passed'] for r in rows] != expected for t in ('llvm', 'wasm')):
                raise SystemExit('smoke outcomes did not match expectations')
            if any(rows[1][t].get('exit') != 1 for t in ('llvm', 'wasm')):
                raise SystemExit('false assertion did not execute and fail')
            if any(rows[i][t].get('exit') != 1 for i in (4, 5, 6) for t in ('llvm', 'wasm')):
                raise SystemExit('assertion after comment did not execute and fail')


if __name__ == '__main__':
    main()
