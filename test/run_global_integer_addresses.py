#!/usr/bin/env python3
"""Exercise global i64/u8 addresses with independent runtime controls."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / 'test'
INPUTS = [FIXTURES / 'global_integer_addresses.lang',
          FIXTURES / 'global_integer_addresses.ast',
          FIXTURES / 'global_integer_addresses.expected.json',
          FIXTURES / 'global_integer_addresses_handler_shadow.lang',
          ROOT / 'src/codegen_llvm.lang', ROOT / 'test/wasm_host.js']


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--compiler', type=Path, required=True)
    ap.add_argument('--evidence', type=Path, required=True)
    args = ap.parse_args()
    require(platform.system() == 'Linux' and platform.machine() == 'x86_64',
            'requires native Linux x86-64')
    for path in INPUTS:
        require(path.is_file(), f'missing required input: {path}')
    evidence = args.evidence.resolve()
    require(ROOT not in evidence.parents and evidence != ROOT,
            'evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix='global-integer-addresses-', dir=evidence))
    compiler = args.compiler.resolve()
    require(compiler.is_file(), f'missing compiler: {compiler}')
    receipt_path = ROOT / 'out/verify-input.json'
    finished_path = ROOT / 'out/verify-receipt.json'
    require(receipt_path.is_file() and finished_path.is_file(),
            'missing source-bound make verify receipts')
    receipt = json.loads(receipt_path.read_text())
    finished = json.loads(finished_path.read_text())
    require(receipt.get('source', {}).get('revision') == subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'compiler source receipt revision mismatch')
    require(receipt.get('source', {}).get('inputs', {}).get('src/codegen_llvm.lang') ==
            sha(ROOT / 'src/codegen_llvm.lang'), 'source/compiler receipt mismatch')
    require(compiler == (ROOT / 'out/bootstrap_verify/kernel2').resolve(),
            'compiler does not match source-bound verify output')
    require(finished.get('compiler', {}).get('sha256') == sha(compiler),
            'compiler binary receipt mismatch')

    expected = json.loads((FIXTURES / 'global_integer_addresses.expected.json').read_text())
    log = []

    def run(argv, *, target, expected_exit=None, stdin=None):
        argv = [str(x) for x in argv]
        env = dict(os.environ, LANGBE='llvm', LANGOS=target,
                   LANG_CACHE=str(run_dir / 'cache' / target))
        env.pop('LANG_ROOT', None)
        result = subprocess.run(argv, cwd=ROOT, env=env, input=stdin,
                                capture_output=True, timeout=180)
        index = len(log)
        stdout, stderr = run_dir / f'{index}.stdout', run_dir / f'{index}.stderr'
        stdout.write_bytes(result.stdout)
        stderr.write_bytes(result.stderr)
        log.append(dict(argv=argv, cwd=str(ROOT), target=target, exit=result.returncode,
                        expected_exit=expected_exit, stdout=str(stdout), stderr=str(stderr),
                        stdout_sha256=sha(stdout), stderr_sha256=sha(stderr)))
        if expected_exit is not None:
            require(result.returncode == expected_exit,
                    f'{argv} exited {result.returncode}, expected {expected_exit}; {stderr}')
        return result

    report = dict(head=receipt['source']['revision'], compiler_sha256=sha(compiler),
                  source_receipt=sha(receipt_path), build_receipt=sha(finished_path), inputs={str(p.relative_to(ROOT)): sha(p)
                  for p in INPUTS}, runs=log, targets=['native Linux x86-64', 'LLVM-to-Wasm/Node'])

    modules = {}
    for fixture, result_code in expected.items():
        source = FIXTURES / fixture
        suffix = '.ast' if fixture.endswith('.ast') else '.lang'
        require(source.suffix == suffix and result_code == 0, f'invalid frozen fixture row: {fixture}')
        for target in ('linux', 'wasm'):
            module = run_dir / f'{target}-{fixture}.ll'
            cmd = [compiler, source]
            if suffix == '.ast':
                cmd.append('--from-ast')
            cmd += ['-o', module]
            run(cmd, target=target, expected_exit=0)
            modules[(fixture, target)] = module
            for opt in ('-O0', '-O2'):
                wasm = target == 'wasm'
                out = run_dir / f'{target}-{fixture}-{opt}.wasm' if wasm else run_dir / f'{target}-{fixture}-{opt}'
                clang = ['clang', opt, '--target=wasm32-unknown-unknown', '-nostdlib',
                         '-Wl,--no-entry', '-Wl,--export-all', '-Wl,--allow-undefined',
                         '-Wl,-z,stack-size=8388608', module, '-o', out] if wasm else \
                        ['clang', opt, '--target=x86_64-unknown-linux-gnu', module, '-o', out]
                run(clang, target=target, expected_exit=0)
                execute = ['node', ROOT / 'test/wasm_host.js', out] if wasm else [out]
                run(execute, target=target, expected_exit=result_code)

    # Handler payload bindings are let-stack entries even when they shadow a
    # global. Keep this regression on native O0, the supported effects mode,
    # and assert its runtime result rather than only checking emitted IR.
    handler_source = FIXTURES / 'global_integer_addresses_handler_shadow.lang'
    handler_module = run_dir / 'handler-shadow.ll'
    run([compiler, handler_source, '-o', handler_module], target='linux', expected_exit=0)
    handler_exe = run_dir / 'handler-shadow'
    run(['clang', '-O0', handler_module, '-o', handler_exe], target='linux', expected_exit=0)
    run([handler_exe], target='linux', expected_exit=0)

    # Mutations use actual emitted LLVM and execution: symbol corruption must
    # fail clang, a wrong global must fail runtime checks, and a wrong frozen
    # readback must fail runtime checks.
    baseline = modules[('global_integer_addresses.lang', 'linux')].read_text()
    bad_local = baseline.replace('ptrtoint i64* @global_i to i64',
                                 'ptrtoint i64* %global_i to i64', 1)
    require(bad_local != baseline, 'could not locate global i64 address IR')
    bad_local_ir = run_dir / 'mutation-at-to-local.ll'
    bad_local_ir.write_text(bad_local)
    bad_local_asm = run_dir / 'mutation-at-to-local.o'
    run(['clang', '-c', bad_local_ir, '-o', bad_local_asm], target='linux', expected_exit=1)

    wrong_global = baseline.replace('ptrtoint i64* @global_i to i64',
                                    'ptrtoint i64* @after_i to i64', 1)
    require(wrong_global != baseline, 'could not create wrong-global mutation')
    wrong_global_ir = run_dir / 'mutation-wrong-global.ll'
    wrong_global_ir.write_text(wrong_global)
    wrong_global_exe = run_dir / 'mutation-wrong-global'
    run(['clang', '-O0', wrong_global_ir, '-o', wrong_global_exe], target='linux', expected_exit=0)
    run([wrong_global_exe], target='linux', expected_exit=1)

    source_text = (FIXTURES / 'global_integer_addresses.lang').read_text()
    wrong_expectation = source_text.replace('global_i != -7654321', 'global_i != -7654320', 1)
    require(wrong_expectation != source_text, 'could not create wrong-readback mutation')
    wrong_source = run_dir / 'mutation-wrong-readback.lang'
    wrong_source.write_text(wrong_expectation)
    wrong_ir = run_dir / 'mutation-wrong-readback.ll'
    run([compiler, wrong_source, '-o', wrong_ir], target='linux', expected_exit=0)
    wrong_exe = run_dir / 'mutation-wrong-readback'
    run(['clang', '-O0', wrong_ir, '-o', wrong_exe], target='linux', expected_exit=0)
    run([wrong_exe], target='linux', expected_exit=1)

    report['mutations'] = ['at-to-local rejected by clang',
                           'wrong global symbol rejected by execution',
                           'wrong readback expectation rejected by execution']
    report['artifacts'] = {p.name: sha(p) for p in sorted(run_dir.iterdir()) if p.is_file()}
    (run_dir / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'PASS global integer addresses: {len(log)} commands; evidence={run_dir}')


if __name__ == '__main__':
    main()
