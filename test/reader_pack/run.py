#!/usr/bin/env python3
"""Offline reader authoring smoke replay; all receipts live outside the checkout."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from interpreter import interpret
from wrong_interpreters import wrong

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / 'test/reader_pack'
os.chdir(ROOT)
SOURCES = ['std/core.lang', 'src/lexer.lang', 'src/parser.lang', 'src/codegen.lang',
           'src/codegen_llvm.lang', 'src/codegen_wasm.lang', 'src/ast_emit.lang', 'src/sexpr_reader.lang']
READ = '''    var text *u8 = alloc(65536);
    var length i64 = 0;
    var count i64 = file_read(0, text, 65535);
    while count > 0 {
        length = length + count;
        if length >= 65535 { count = 0; }
        else { count = file_read(0, text + length, 65535 - length); }
    }
    if count < 0 { return nil; }
    *(text + length) = 0;
    return threshold(text);
'''


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def check_contract():
    frozen = json.loads((PACK / 'freeze.json').read_text())
    for name, expected in frozen.items():
        assert sha(ROOT / name) == expected, f'changed frozen input: {name}'
    protocol = json.loads((PACK / 'protocol.json').read_text())
    assert protocol['orders'] == [['interpreter-only', 'native-plus-wasm'], ['native-plus-wasm', 'interpreter-only']]
    assert all(value is False for key, value in protocol['policy'].items() if key != 'network')
    assert protocol['future_runs']['status'] == 'disabled'
    # Signatures are checked against current source, not remembered API names.
    for file, signatures in json.loads((PACK / 'helpers.json').read_text()).items():
        source = (ROOT / file).read_text()
        for signature in signatures:
            assert signature in source, f'stale helper signature: {signature}'
    doc = (ROOT / 'docs/reader-pack/README.md').read_text()
    blocks = [b.split('\n', 1) for b in doc.split('```')[1::2]]
    assert blocks and all(language == 'bash' for language, _ in blocks)
    assert all('test/reader_pack/run.py' in body for _, body in blocks)
    print('PASS frozen tasks, independent fixtures, helper signatures, counterbalance and budget policy')
    return protocol


class Replay:
    def __init__(self, evidence):
        self.evidence = evidence
        self.log_index = 0
        self.env = dict(os.environ, LANGBE='llvm', LANGOS='linux', LANG_CACHE=str(evidence / 'cache'),
                        TMPDIR=str(evidence / 'tmp'), JOBS='2')
        (evidence / 'tmp').mkdir()
        self.rows = []

    def run(self, command, name, data=None, env=None, ok=True):
        self.log_index += 1
        prefix = self.evidence / f'{self.log_index:03d}-{name}'
        start = time.perf_counter()
        result = subprocess.run([str(x) for x in command], input=data, capture_output=True,
                                env=env or self.env, timeout=300)
        elapsed = (time.perf_counter() - start) * 1000
        prefix.with_suffix('.stdout').write_bytes(result.stdout)
        prefix.with_suffix('.stderr').write_bytes(result.stderr)
        dump(prefix.with_suffix('.json'), {'command': [str(x) for x in command], 'exit': result.returncode,
                                         'elapsed_ms': elapsed})
        if ok and result.returncode:
            raise RuntimeError(f'{name}: exit {result.returncode}; see {prefix}.stderr')
        return result, elapsed

    def build(self):
        b = self.evidence / 'build'
        b.mkdir()
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
        assert not subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all'], text=True).strip(), 'commit the source before pinning a build'
        paths = sorted(set([*ROOT.glob('src/*.lang'), *ROOT.glob('std/**/*.lang'),
                            ROOT / 'bootstrap/current/compiler_linux.ll',
                            ROOT / 'web/compiler_host.js', ROOT / 'web/program_host.js']))
        before = {str(p.relative_to(ROOT)): sha(p) for p in paths}
        # Ignored OS dispatch and version input are generated, never trusted from old binaries.
        (ROOT / 'std/os.lang').write_text('include "std/os/libc.lang"\n')
        version = b / 'version_info.lang'
        version.write_text('\n'.join(f'var {key} *u8 = "{value}";' for key, value in {
            'LANG_VERSION': '0.1.0', 'LANG_COMMIT': head, 'LANG_BUILD_BACKEND': 'llvm',
            'LANG_BUILD_OS': 'linux', 'LANG_BUILD_ARCH': 'x86_64', 'LANG_BUILD_LIBC': 'system',
            'LANG_BOOTSTRAP_FROM': (ROOT / 'bootstrap/current/COMMIT').read_text().strip(),
        }.items()) + '\n')
        self.run(['clang', '-O2', 'bootstrap/current/compiler_linux.ll', '-o', b / 'seed'], 'seed')
        inputs = [SOURCES[0], str(version), *SOURCES[1:]]
        self.compiler = b / 'lang'
        self.run([b / 'seed', *inputs, 'src/compiler_readers_none.lang', 'src/main.lang', '-o', b / 'compiler.ll'], 'current-source')
        self.run(['clang', '-O2', b / 'compiler.ll', '-o', self.compiler], 'native-compiler')
        self.run([self.compiler, *inputs, 'src/compiler_readers_web.lang', 'src/main.lang', '-o', b / 'compiler-wasm.ll'],
                 'wasm-source', env=dict(self.env, LANGOS='wasm'))
        self.wasm = b / 'compiler.wasm'
        self.run(['clang', '-O2', '--target=wasm32-unknown-unknown', '-nostdlib',
                  '-Wl,--no-entry', '-Wl,--export-all', '-Wl,--allow-undefined', '-Wl,-z,stack-size=8388608',
                  b / 'compiler-wasm.ll', '-o', self.wasm], 'wasm-compiler')
        # Source hashes and source commit are an authoritative, replayable build identity.
        after = {str(p.relative_to(ROOT)): sha(p) for p in paths}
        before.pop('std/os.lang', None)
        after.pop('std/os.lang', None)
        assert before == after, 'compiler input changed during build'
        dump(b / 'identity.json', {'source_commit': head, 'source_sha256': after,
                                 'version_input_sha256': sha(version),
                                 'native_sha256': sha(self.compiler), 'wasm_sha256': sha(self.wasm)})
        for tool in ['clang', 'node', 'python3']:
            self.run([tool, '--version'], 'version-' + tool)

    def native_task(self, name, cases, compile_failure=False, candidate=None, group="native"):
        directory = self.evidence / group / name
        directory.mkdir(parents=True)
        wrapper = directory / 'wrapper.lang'
        reader_path = str(candidate) if candidate else f'test/reader_pack/{name}.lang'
        wrapper.write_text(f'include "{reader_path}"\nfunc pack_read() *u8 {{\n{READ}}}\n' + '''
func main() i64 {
    var ast *u8 = pack_read();
    if ast == nil { return 1; }
    println(ast);
    return 0;
}
''')
        built, build_ms = self.run([self.compiler, wrapper, '-o', directory / 'reader.ll'], 'native-reader-' + name, ok=not compile_failure)
        if compile_failure:
            return [{'fixture': name, 'compileFailure': built.returncode != 0 and not (directory / 'reader.ll').exists(),
                     'diagnostic': built.stderr.decode(), 'build_ms': build_ms}]
        _, link_ms = self.run(['clang', '-O0', directory / 'reader.ll', '-o', directory / 'reader'], 'link-reader-' + name)
        build_ms += link_ms
        rows = []
        for c in cases:
            read, elapsed = self.run([directory / 'reader'], 'read-' + name + '-' + c['id'], data=c['source'].encode(), ok=False)
            row = {key: c[key] for key in ['id', 'stage', 'split']}
            row.update(fixture=name, backend='native', build_ms=build_ms, read_ms=elapsed,
                       reader_exit=read.returncode, diagnostic=read.stderr.decode(), stdout='')
            if read.returncode:
                row['rejected'] = True
                assert not read.stdout, 'failed reader emitted AST'
            else:
                ast = directory / (c['id'] + '.ast')
                ast.write_bytes(read.stdout)
                row['ast'] = read.stdout.decode()
                ir = directory / (c['id'] + '.ll')
                program = directory / c['id']
                _, emit_ms = self.run([self.compiler, '--from-ast', ast, '-o', ir], 'emit-' + c['id'])
                _, link_ms = self.run(['clang', '-O0', ir, '-o', program], 'link-' + c['id'])
                ran, run_ms = self.run([program], 'run-' + c['id'], ok=False)
                assert ran.returncode >= 0, 'program crashed'
                row.update(value=ran.returncode, stdout=ran.stdout.decode(), program_build_ms=emit_ms + link_ms, run_ms=run_ms)
            rows.append(row)
        return rows

    def browser_tasks(self, tasks, order):
        directory = self.evidence / ('browser-' + str(order))
        directory.mkdir()
        # Load current source dependencies directly, bypassing checked-in web bundles.
        files = {str(p.relative_to(ROOT)): p.read_text() for p in ROOT.glob('std/**/*.lang')}
        files['src/limits.lang'] = (ROOT / 'src/limits.lang').read_text()
        files.update({str(p.relative_to(ROOT)): p.read_text() for p in PACK.glob('*.lang')})
        payload = {'compiler': list(self.wasm.read_bytes()), 'files': files, 'tasks': tasks}
        dump(directory / 'input.json', payload)
        self.run(['node', 'test/reader_pack/browser.mjs', directory / 'input.json', directory / 'results.json'], 'real-browser')
        return json.loads((directory / 'results.json').read_text())['rows']


def passed(row, case):
    if 'expected' in case:
        return not row.get('rejected') and row.get('value') == case['expected']
    return row.get('rejected', False) and case['diagnostic'] in row.get('diagnostic', '')


def smoke(evidence):
    protocol = check_contract()
    replay = Replay(evidence)
    replay.build()
    cases = []
    for split in ['training', 'heldout']:
        cases.extend(dict(c, split=split) for c in json.loads((PACK / (split + '.json')).read_text()))
    for order_index, order in enumerate(protocol['orders']):
        for track in order:
            if track == 'interpreter-only':
                for c in cases:
                    start = time.perf_counter()
                    observed = interpret(c['source'], c['stage'])
                    row = dict(c, backend='interpreter', order=order_index, read_ms=(time.perf_counter() - start) * 1000,
                               rejected='diagnostic' in observed, **observed)
                    # Keep expected diagnostics separate from observed diagnostics.
                    assert passed(row, c), row
                    replay.rows.append(row)
            else:
                tasks = []
                for stage, fixture in [('create', 'create'), ('evolve', 'threshold')]:
                    subset = [c for c in cases if c['stage'] == stage]
                    rows = replay.native_task(fixture, subset, group='native-' + str(order_index))
                    for row in rows:
                        row['order'] = order_index
                        assert passed(row, next(c for c in subset if c['id'] == row['id'])), row
                    replay.rows.extend(rows)
                    tasks.append({'name': fixture, 'cases': subset,
                                  'wrapper': f'include "test/reader_pack/{fixture}.lang"\nfunc main() *u8 {{\n{READ}}}\n'})
                browser_rows = replay.browser_tasks(tasks, order_index)
                for row in browser_rows:
                    row['order'] = order_index
                    assert passed(row, next(c for c in cases if c['id'] == row['id'])), row
                replay.rows.extend(browser_rows)
    # Negative controls: known defects must fail exactly the same oracle.
    repairs = []
    tasks = []
    for defect in protocol['repairs']:
        name = Path(defect['fixture']).stem
        compile_failure = defect['case'] == 'compile'
        subset = [] if compile_failure else [next(c for c in cases if c['id'] == defect['case'])]
        native = replay.native_task(name, subset, compile_failure)
        if compile_failure:
            assert native[0]['compileFailure'] and "takes 2 arguments, called with 1" in native[0]['diagnostic'], native
        else:
            assert not passed(native[0], subset[0]), f'oracle accepted defect {name}'
        repair_start = time.perf_counter()
        if compile_failure:
            try:
                wrong('threshold 73 value 73', 'evolve', name)
            except TypeError as error:
                interpreter_bad = {'compileFailure': True, 'diagnostic': str(error)}
            else:
                raise AssertionError('interpreter oracle accepted wrong arity')
        else:
            interpreter_bad = wrong(subset[0]['source'], 'evolve', name)
            interpreter_bad['rejected'] = 'diagnostic' in interpreter_bad
            assert not passed(interpreter_bad, subset[0]), f'interpreter accepted {name}'
        after_rows = [r for r in replay.rows if r.get('fixture') == 'threshold' or r['backend'] == 'interpreter' and r['stage'] == 'evolve']
        assert after_rows and all(passed(r, next(c for c in cases if c['id'] == r['id'])) for r in after_rows)
        repairs.append({'fixture': name, 'before_native': native, 'before_interpreter': interpreter_bad,
                        'after_reference': 'threshold', 'after_verified_observations': len(after_rows),
                        'interpreter_control_ms': (time.perf_counter() - repair_start) * 1000,
                        'model_attempts': 0, 'repair_mode': 'supplied reference replay'})
        tasks.append({'name': name, 'cases': subset, 'compileFailure': compile_failure,
                      'wrapper': f'include "test/reader_pack/{name}.lang"\nfunc main() *u8 {{\n{READ}}}\n'})
    browser_bad = replay.browser_tasks(tasks, 'repairs')
    assert len(browser_bad) == len(protocol['repairs']), 'missing browser controls'
    for defect, row in zip(protocol['repairs'], browser_bad):
        if defect['case'] == 'compile':
            assert row['compileFailure'] and 'takes 2 arguments, called with 1' in row['diagnostic'], row
        else:
            assert not passed(row, next(c for c in cases if c['id'] == defect['case'])), f'browser accepted {defect}'
        next(r for r in repairs if r['fixture'] == row['fixture'])['before_browser'] = row
    dump(evidence / 'repairs.json', repairs)
    dump(evidence / 'observations.json', replay.rows)
    groups = {}
    for row in replay.rows:
        key = '/'.join([row['backend'], row['stage'], row['split']])
        group = groups.setdefault(key, {'total': 0, 'passed': 0, 'read_ms': 0, 'program_build_ms': 0, 'run_ms': 0})
        group['total'] += 1
        group['passed'] += int(passed(row, next(c for c in cases if c['id'] == row['id'])))
        for metric in ['read_ms', 'program_build_ms', 'run_ms']:
            group[metric] += row.get(metric, 0)
    summary = {'label': protocol['label'], 'by_backend_stage_split': groups, 'orders': protocol['orders'], 'observations': len(replay.rows),
               'correct': len(replay.rows), 'negative_controls_rejected': len(repairs) * 3,
               'model_calls': 0, 'model_attempts': 0, 'paid_calls': 0,
               'metrics': protocol['metrics'], 'build_identity': 'build/identity.json'}
    dump(evidence / 'summary.json', summary)
    print(json.dumps(summary, indent=2))



def evaluate(evidence, track, candidate, stage):
    check_contract()
    cases = [dict(c, split=split) for split in ['training', 'heldout']
             for c in json.loads((PACK / (split + '.json')).read_text()) if c['stage'] == stage]
    if track == 'interpreter-only':
        spec = importlib.util.spec_from_file_location('submitted_interpreter', candidate)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        rows = []
        for c in cases:
            start = time.perf_counter()
            try:
                observed = module.interpret(c['source'], stage)
                row = dict(observed, rejected='diagnostic' in observed)
            except Exception as error:
                row = {'error': str(error)}
            row.update(id=c['id'], backend='interpreter', elapsed_ms=(time.perf_counter() - start) * 1000)
            row['passed'] = passed(row, c)
            rows.append(row)
    else:
        replay = Replay(evidence)
        replay.build()
        source = candidate.read_text()
        rows = replay.native_task('submitted', cases, candidate=candidate)
        # Includes in submitted readers resolve from the repo source dependencies;
        # the submitted top-level source is supplied as a virtual file.
        virtual = 'test/reader_pack/submitted.lang'
        directory = evidence / 'browser-submission'
        directory.mkdir()
        files = {str(p.relative_to(ROOT)): p.read_text() for p in ROOT.glob('std/**/*.lang')}
        files.update({str(p.relative_to(ROOT)): p.read_text() for p in PACK.glob('*.lang')})
        files['src/limits.lang'] = (ROOT / 'src/limits.lang').read_text()
        files[virtual] = source
        payload = {'compiler': list(replay.wasm.read_bytes()), 'files': files, 'tasks': [{
            'name': 'submitted', 'cases': cases,
            'wrapper': f'include "{virtual}"\nfunc main() *u8 {{\n{READ}}}\n'}]}
        dump(directory / 'input.json', payload)
        replay.run(['node', 'test/reader_pack/browser.mjs', directory / 'input.json', directory / 'results.json'], 'candidate-browser')
        rows += json.loads((directory / 'results.json').read_text())['rows']
        for row in rows:
            row['passed'] = passed(row, next(c for c in cases if c['id'] == row['id']))
    dump(evidence / 'evaluation.json', {'candidate': str(candidate), 'sha256': sha(candidate), 'rows': rows})
    correct = sum(r['passed'] for r in rows)
    print(f'{correct}/{len(rows)} oracle observations passed; {evidence / "evaluation.json"}')
    return 0 if correct == len(rows) else 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['contract', 'smoke', 'evaluate'])
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--track', choices=['interpreter-only', 'native-plus-wasm'])
    parser.add_argument('--candidate', type=Path)
    parser.add_argument('--stage', choices=['create', 'evolve'])
    args = parser.parse_args()
    if args.mode == 'contract':
        check_contract()
    else:
        if not args.evidence:
            parser.error('--evidence is required')
        evidence = args.evidence.resolve()
        if evidence == ROOT or ROOT in evidence.parents:
            parser.error('evidence must be outside the checkout')
        evidence.mkdir(parents=True, exist_ok=False)
        if args.mode == 'smoke':
            smoke(evidence)
        else:
            if not all([args.track, args.candidate, args.stage]):
                parser.error('evaluate requires --track, --candidate and --stage')
            sys.exit(evaluate(evidence, args.track, args.candidate.resolve(), args.stage))
