#!/usr/bin/env python3
"""Focused authoring acceptance: generated grammar, recovery, standalone reader.

Run only after promoting the eof grammar capability. The parent owns compiler
bootstrap and browser assets; this test does not rebuild or mutate either.
"""
import argparse
import atexit
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', default='out/lang')
    parser.add_argument('--browser-compiler', default='web/compiler.wasm')
    parser.add_argument('--native-only', action='store_true')
    parser.add_argument('--out', default='out/parser-authoring-report.json')
    args = parser.parse_args()
    compiler = (ROOT / args.compiler).resolve()
    env = dict(os.environ, LANG_ROOT=str(ROOT), LANGBE='llvm')
    report = {'status': 'failed', 'native': [], 'commands': []}
    destination = ROOT / args.out
    destination.parent.mkdir(parents=True, exist_ok=True)

    def save_report():
        destination.write_text(json.dumps(report, indent=2) + '\n')

    atexit.register(save_report)
    with tempfile.TemporaryDirectory(prefix='lang-parser-authoring-') as work:
        work = Path(work)
        env['LANG_CACHE'] = str(work / 'cache')
        portable_env = dict(env)
        portable_env.pop('LANG_ROOT', None)

        def run(command, expected=0, cwd=ROOT, changed_env=None):
            command = [str(part) for part in command]
            start = time.monotonic()
            result = subprocess.run(command, cwd=cwd, env=changed_env or env,
                                    capture_output=True, text=True, timeout=90)
            report['commands'].append({'argv': command, 'cwd': str(cwd),
                                       'exit': result.returncode,
                                       'stdout': result.stdout, 'stderr': result.stderr,
                                       'seconds': time.monotonic() - start})
            if expected is not None and result.returncode != expected:
                raise AssertionError(f'{command}: exit {result.returncode}, expected {expected}\n{result.stderr}')
            return result

        for filename in ['test/suite/289_parser_recovery.lang', 'test/parser_eof.lang', 'test/parser_literal.lang', 'test/parser_literal_raw.lang', 'test/parser_macro_boundary.lang', 'test/parser_lisp_quote.lang', 'test/parser_array_length.lang', 'test/parser_block_limit.lang']:
            output = work / Path(filename).stem
            run([compiler, filename, '-o', output.with_suffix('.ll')])
            for optimization in ['-O0', '-O2']:
                binary = Path(str(output) + optimization)
                run(['clang', optimization, output.with_suffix('.ll'), '-o', binary])
                run([binary])
                report['native'].append({'source': filename, 'optimization': optimization, 'value': 0})

        for name, grammar in [
            ('eof-cycle', 'thing = eof thing | number'),
            ('indirect-eof-cycle', 'thing = eof other\n other = thing | number'),
            ('empty-literal', "thing = '' thing | number"),
        ]:
            cycle = work / f'{name}.lang'
            cycle.write_text(f'include "std/parser_reader.lang"\n#parser{{\n {grammar}\n}}\n')
            bad_output = work / f'{name}.ll'
            rejected = run([compiler, cycle, '-o', bad_output], expected=None)
            assert rejected.returncode != 0 and not bad_output.exists()
            expected = 'nonempty literal' if name == 'empty-literal' else 'non-left-recursive rule'
            assert '#parser:' in rejected.stderr and expected in rejected.stderr
            report['native'].append({'source': name, 'diagnostic': rejected.stderr.strip()})

        standalone = work / 'workshopc'
        run([compiler, 'compiler', 'workshop', 'example/workshop/workshop.lang', '-o', standalone])
        alien_dir = work / 'outside-checkout'
        alien_dir.mkdir()
        bad_model = alien_dir / 'bad.workshop'
        bad_model.write_text('add ;\nadd word;\nadd 42;')
        bad_target = alien_dir / 'bad.ll'
        rejected = run([standalone, bad_model, '-o', bad_target], expected=None,
                       cwd=alien_dir, changed_env=portable_env)
        assert rejected.returncode != 0 and not bad_target.exists()
        assert 'workshop:1:5: expected number, found ;' in rejected.stderr
        assert 'workshop:2:5: expected number, found word' in rejected.stderr
        report['native'].append({'source': 'two-independent-errors', 'diagnostic': rejected.stderr.strip()})

        good_model = alien_dir / 'corrected.workshop'
        good_model.write_text('add 20;\nadd 22;')
        target = alien_dir / 'corrected.ll'
        run([standalone, good_model, '-o', target], cwd=alien_dir, changed_env=portable_env)
        run(['clang', '-O2', target, '-o', alien_dir / 'corrected'], cwd=alien_dir)
        run([alien_dir / 'corrected'], expected=42, cwd=alien_dir)
        report['native'].append({'source': 'standalone-corrected-language', 'value': 42})

        if not args.native_only:
            browser = run(['node', 'test/parser_authoring_browser.js', args.browser_compiler])
            report['browser'] = json.loads(browser.stdout)

    report['status'] = 'passed'
    save_report()
    print(f'PASS parser authoring acceptance; report {destination}')


if __name__ == '__main__':
    main()
