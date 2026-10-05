#!/usr/bin/env python3
"""Mint a compiler, build changed models outside the checkout, verify science.

python3 test/hamiltonian_e2e.py [COMPILER] [--output out/hamiltonian]
Only stdlib Python, the existing compiler, and clang are required.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
import hamiltonian_reference as reference


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('compiler', nargs='?', default='./out/lang')
    parser.add_argument('--output')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    compiler = Path(args.compiler).resolve()
    receipts = []
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix='lang-hamiltonian-') as directory:
        outside = Path(directory)
        output = Path(args.output).resolve() if args.output else outside / 'evidence'
        output.mkdir(parents=True, exist_ok=True)

        def run(command, cwd=outside, expected=0, standalone=False):
            begin = time.perf_counter()
            environment = {**os.environ, 'LANGBE': 'llvm',
                           'LANG_CACHE': str(outside / 'cache')}
            if standalone:
                # The minted compiler must carry its runtime and reader, not
                # accidentally resolve includes through the source checkout.
                environment['LANG_ROOT'] = str(outside / 'missing-source-root')
            result = subprocess.run([str(v) for v in command], cwd=cwd,
                                    env=environment,
                                    capture_output=True, text=True, timeout=90)
            receipts.append({'command': [str(v) for v in command], 'cwd': str(cwd),
                             'standalone_missing_source_root': standalone,
                             'exit': result.returncode,
                             'seconds': time.perf_counter()-begin,
                             'stderr': result.stderr})
            # Preserve the actual failed command too, rather than losing all
            # evidence if a later assertion fails.
            (output / 'commands.json').write_text(json.dumps(receipts, indent=2)+'\n')
            assert result.returncode == expected, (command, result.returncode, result.stderr)
            return result

        # First gate the exact reader/AST decimal boundary and typed f64 ABI.
        probe_source = outside / 'fractional.probe'; probe_source.write_text('probe\n')
        probe_ast = output / 'fractional.ast'
        run([compiler, 'read', 'test/hamiltonian_float_reader.lang', probe_source,
             '-o', probe_ast], cwd=root)
        probe_ir = output / 'fractional.ll'
        run([compiler, '--from-ast', probe_ast, '--runtime', 'std/core.lang',
             '-o', probe_ir], cwd=root)
        assert 'define double @affine(double' in probe_ir.read_text()
        for opt in ('O0', 'O2'):
            binary = outside / f'fractional-{opt}'
            run(['clang', '-w', f'-{opt}', probe_ir, '-o', binary])
            result = run([binary])
            assert result.stdout == '0.34375\n', result.stdout
            (output / f'fractional-{opt}.txt').write_text(result.stdout)

        # This compiler contains both reader and fully expanded runtime AST.
        minted = output / 'hamc'
        run([compiler, 'compiler', 'ham', 'example/hamiltonian/hamiltonian.lang',
             '--runtime', 'example/hamiltonian/runtime.lang', '-o', minted], cwd=root)
        isolated_compiler = outside / 'hamc'
        shutil.copy2(minted, isolated_compiler)
        quartic = (root / 'example/hamiltonian/quartic.ham').read_text()
        double_well = (root / 'example/hamiltonian/double_well.ham').read_text()

        def build(name, source):
            file = outside / f'{name}.ham'
            file.write_text(source)
            ir = outside / f'{name}.ll'
            run([isolated_compiler, file.name, '-o', ir.name], standalone=True)
            assert ir.exists()
            shutil.copy2(file, output / file.name)
            shutil.copy2(ir, output / ir.name)
            binaries = {}
            for opt in ('O0', 'O2'):
                binary = outside / f'{name}-{opt}'
                run(['clang', '-w', f'-{opt}', ir.name, '-o', binary.name])
                binaries[opt] = binary
            return binaries

        def trajectory(name, binaries, mode=None):
            paths = []
            for opt, binary in binaries.items():
                result = run([binary] + ([mode] if mode else []))
                path = output / f'{name}-{opt}.csv'
                path.write_text(result.stdout)
                paths.append(str(path))
            return paths

        def settings(source, h, count):
            return re.sub(r'run step .*?;', f'run step {h} steps {count} sample 1;', source)

        harmonic = quartic.replace('param a = 0.6;', 'param a = 0.0;').replace('param b = 0.4;', 'param b = 0.0;')
        manifest = {'harmonic': [], 'long_harmonic': [], 'optimization_pairs': []}
        harmonic_binaries = None
        for h, count in ((0.04, 92), (0.02, 184), (0.01, 368)):
            binaries = build(f'harmonic-{h}', settings(harmonic, h, count))
            paths = trajectory(f'harmonic-{h}', binaries)
            manifest['harmonic'].append(paths[1])
            manifest['optimization_pairs'].append(paths)
            harmonic_binaries = binaries
        # Gate harmonic convergence BEFORE attempting the nonlinear experiments.
        assert reference.analyze_harmonic(manifest['harmonic'])['passed']
        for h, count in ((0.04, 25000), (0.02, 50000)):
            paths = trajectory(f'long-harmonic-{h}', build(f'long-harmonic-{h}', settings(harmonic, h, count)))
            manifest['long_harmonic'].append(paths[1])
            manifest['optimization_pairs'].append(paths)
        nonlinear = {}
        models = (('quartic', quartic), ('double_well', double_well),
                  ('quartic_changed', quartic.replace('param b = 0.4;', 'param b = 0.9;')))
        for name, source in models:
            nonlinear[name] = build(name, source)
            paths = trajectory(name, nonlinear[name])
            manifest[name] = paths[1]
            manifest['optimization_pairs'].append(paths)

        json_exports = []

        def reject_json_constant(text):
            raise ValueError(f'nonfinite JSON constant: {text}')

        def same_float(actual, expected):
            # Equality alone misses loss of a negative-zero sign in JSON.
            return actual == expected and math.copysign(1, actual) == math.copysign(1, expected)

        def json_trajectory(name, source, binaries, coordinates, masses, expected_paths):
            match = re.search(r'run step (\S+) steps (\d+) sample (\d+);', source)
            assert match
            h, steps, stride = float(match[1]), int(match[2]), int(match[3])
            for opt, csv_path in zip(('O0', 'O2'), expected_paths):
                result = run([binaries[opt], '--json'])
                path = output / f'{name}-{opt}.json'; path.write_text(result.stdout)
                document = json.loads(result.stdout, parse_constant=reject_json_constant)
                assert document['schema'] == 'lang.hamiltonian.trajectory.v1'
                assert document['nondimensional'] is True
                assert document['method'] == 'velocity-verlet'
                assert document['coordinates'] == coordinates
                assert document['masses'] == masses
                assert document['step_size'] == h
                assert document['steps'] == steps and document['sample_stride'] == stride
                csv_rows = list(csv.DictReader(Path(csv_path).read_text().splitlines()))
                samples = document['samples']
                assert len(samples) == len(csv_rows)
                assert [s['step'] for s in samples] == [0, *range(stride, steps+1, stride), *([] if steps % stride == 0 else [steps])]
                for sample, row in zip(samples, csv_rows):
                    assert type(sample['step']) is int
                    assert sample['step'] == int(row['step'])
                    assert same_float(sample['time'], float(row['time']))
                    assert len(sample['q']) == len(coordinates) and len(sample['p']) == len(coordinates)
                    assert all(same_float(v, float(row[f'q_{q}'])) for v, q in zip(sample['q'], coordinates))
                    assert all(same_float(v, float(row[f'p_{q}'])) for v, q in zip(sample['p'], coordinates))
                    assert same_float(sample['energy'], float(row['energy']))
                json_exports.append(str(path))

        for name, source in models:
            paths = next(p for p in manifest['optimization_pairs'] if Path(p[0]).name == f'{name}-O0.csv')
            json_trajectory(name, source, nonlinear[name], ['x', 'y'], [1.3, 1.3], paths)

        # Save inspectable forces and independently exercise serialized ASTs.
        for name, source in models:
            file = outside / f'{name}.ham'
            ast = output / f'{name}.ast'
            run([compiler, 'read', 'example/hamiltonian/hamiltonian.lang', file,
                 '-o', ast], cwd=root)
            text = ast.read_text()
            for function in ('ham_potential', 'ham_force_x', 'ham_force_y', 'ham_step'):
                assert re.search(r'\(func\s+' + function + r'\s', text), function
            assert '(span ' in text
            ir = output / f'{name}-roundtrip.ll'
            run([compiler, '--from-ast', ast, '--runtime', 'example/hamiltonian/runtime.lang',
                 '-o', ir], cwd=root)
            for opt in ('O0', 'O2'):
                binary = outside / f'{name}-roundtrip-{opt}'
                run(['clang', '-w', f'-{opt}', ir, '-o', binary])
                result = run([binary])
                path = output / f'{name}-roundtrip-{opt}.csv'; path.write_text(result.stdout)
                manifest['optimization_pairs'].append([str(output / f'{name}-{opt}.csv'), str(path)])
        manifest['json_trajectories'] = json_exports

        reverse = trajectory('reversal', nonlinear['quartic'], '--reverse')
        manifest['reversal'] = reverse[1]
        manifest['optimization_pairs'].append(reverse)

        gradients = {opt: [] for opt in ('O0', 'O2')}
        for model, binaries in [('harmonic', harmonic_binaries), *nonlinear.items()]:
            for opt, binary in binaries.items():
                for x, y in reference.GRADIENT_POINTS:
                    result = run([binary, '--forces', str(x), str(y)])
                    rows = list(csv.DictReader(io.StringIO(result.stdout)))
                    assert len(rows) == 1
                    row = rows[0]
                    gradients[opt].append({'model': model, 'x': x, 'y': y,
                                          'force_x': row['force_x'], 'force_y': row['force_y'],
                                          'potential': row['potential']})
        manifest['gradients'] = []
        for opt, rows in gradients.items():
            path = output / f'gradients-{opt}.csv'
            with path.open('w', newline='') as handle:
                writer = csv.DictWriter(handle, fieldnames=['model', 'x', 'y', 'force_x', 'force_y', 'potential'])
                writer.writeheader(); writer.writerows(rows)
            manifest['gradients'].append(str(path))

        # Generic lowering: four unequal masses, free motion, x^0 and x^8.
        free = '''model free { nondimensional;
pair u mass 1 position -0.1 momentum 0.2;
pair v mass 2 position 0.3 momentum -0.4;
pair w mass 3 position -0.5 momentum 0.6;
pair z mass 4 position 0.7 momentum -0.8;
potential = u^0 - 1; run step 0.01 steps 10 sample 1; }'''
        free_binaries = build('free-four', free)
        free_paths = trajectory('free-four', free_binaries)
        for path in free_paths:
            row = list(csv.DictReader(io.StringIO(Path(path).read_text())))[-1]
            for coordinate, expected in zip(('u', 'v', 'w', 'z'), (-0.08, 0.28, -0.48, 0.68)):
                assert abs(float(row[f'q_{coordinate}']) - expected) < 1e-14
        json_trajectory('free-four', free, free_binaries, ['u', 'v', 'w', 'z'], [1, 2, 3, 4], free_paths)
        sparse = settings(quartic, 0.01, 10).replace('sample 1;', 'sample 3;')
        sparse_binaries = build('sparse', sparse)
        sparse_paths = trajectory('sparse', sparse_binaries)
        json_trajectory('sparse', sparse, sparse_binaries, ['x', 'y'], [1.3, 1.3], sparse_paths)
        signed_zero = 'model zero { nondimensional; pair z mass 1 position -0.0 momentum -0.0; potential = 0; run step 0.01 steps 2 sample 2; }'
        zero_binaries = build('signed-zero', signed_zero)
        zero_paths = trajectory('signed-zero', zero_binaries)
        json_trajectory('signed-zero', signed_zero, zero_binaries, ['z'], [1], zero_paths)
        for opt in ('O0', 'O2'):
            initial = json.loads((output / f'signed-zero-{opt}.json').read_text())['samples'][0]
            assert math.copysign(1, initial['q'][0]) == -1
            assert math.copysign(1, initial['p'][0]) == -1
        power = 'model power { nondimensional; pair x mass 1 position -0.5 momentum 0; potential = x^8; run step 0.01 steps 1 sample 1; }'
        for binary in build('power-eight', power).values():
            row = list(csv.DictReader(io.StringIO(run([binary, '--forces', '-0.5']).stdout)))[0]
            assert abs(float(row['force_x']) - 0.0625) < 1e-14
        cancellation = power.replace('x^8', '(0.3-0.30000000000000002)*x')
        for binary in build('decimal-cancellation', cancellation).values():
            row = list(csv.DictReader(io.StringIO(run([binary, '--forces', '1']).stdout)))[0]
            assert float(row['force_x']) == -(0.3-0.30000000000000002), row

        failures = [
            ('zero-mass', 'mass m position', 'mass 0 position', 'mass must be'),
            ('negative-mass', 'mass m position', 'mass -1 position', 'mass must be'),
            ('unknown', 'k*(x^2+y^2)', 'missing*(x^2+y^2)', 'unknown symbol'),
            ('state-division', '/2 + a', '/x + a', 'state-independent'),
            ('zero-division', '/2 + a', '/(1-1) + a', 'nonzero'),
            ('rounded-zero-division', '/2 + a', '/(0.2+0.1-0.30000000000000003) + a', 'nonzero'),
            ('fractional-power', 'x^4', 'x^0.5', 'integer'),
            ('large-power', 'x^4', 'x^9', 'bound'),
            ('negative-power', 'x^4', 'x^-1', 'expected'),
            ('chained-power', 'x^4', 'x^2^2', 'chained powers'),
            ('function', 'x^4', 'sin(x)', 'expected'),
            ('momentum-potential', 'x^4', 'p_x^2', 'unknown symbol'),
            ('zero-step', 'step 0.01', 'step 0', 'step must be'),
            ('negative-step', 'step 0.01', 'step -0.01', 'step must be'),
            ('zero-steps', 'steps 368', 'steps 0', 'bound'),
            ('fractional-steps', 'steps 368', 'steps 1.5', 'integer'),
            ('large-steps', 'steps 368', 'steps 1000001', 'bound'),
            ('zero-sample', 'sample 1', 'sample 0', 'bound'),
            ('large-sample', 'sample 1', 'sample 369', 'sample stride'),
            ('duplicate', 'param b =', 'param a =', 'duplicate'),
            ('kinetics', 'potential =', 'kinetic = x^2; potential =', 'expected'),
            ('nonfinite', 'param a = 0.6;', 'param a = NaN;', 'unknown constant'),
            ('not-nondimensional', 'nondimensional;', '', 'expected'),
            ('expansion', 'x^4', '((((((x^8)^8)^8)^8)^8)^8)', '65536 AST'),
            ('unary-depth', 'param a = 0.6;', 'param a = ' + '- '*33 + '0.6;', 'unary minuses exceed 32'),
            ('paren-depth', 'x^4', '('*33 + 'x' + ')'*33, 'nesting exceeds 32'),
            ('source-bound', 'nondimensional;', 'nondimensional; //' + 'a'*65536 + '\n', '65536 source bytes'),
            ('token-bound', 'x^4', '+'.join(['x']*2200), '4096 tokens'),
            ('decimal-bound', 'param a = 0.6;', 'param a = ' + '1'*129 + ';', 'at most 128 bytes'),
            ('pair-bound', 'potential =', ''.join(f'pair extra{i} mass 1 position 0 momentum 0; ' for i in range(3)) + 'potential =', 'four canonical pairs'),
            ('param-bound', 'param a = 0.6;', ''.join(f'param extra{i} = 1; ' for i in range(32)) + 'param a = 0.6;', '32 parameters'),
        ]
        for name, old, new, message in failures:
            source = outside / f'bad-{name}.ham'; source.write_text(quartic.replace(old, new))
            ir = outside / f'bad-{name}.ll'
            result = run([isolated_compiler, source.name, '-o', ir.name], expected=1, standalone=True)
            assert not ir.exists()
            assert re.search(r'hamiltonian:\d+:\d+:', result.stderr), result.stderr
            assert message in result.stderr, result.stderr
            assert 'reader lowering error' not in result.stderr, result.stderr
        for invalid in ('NaN', 'inf', '', '-', '1.', '1.2.3'):
            run([nonlinear['quartic']['O2'], '--forces', invalid, '0'], expected=2)
        runaway = quartic.replace('step 0.01 steps 368', 'step 100 steps 100')
        for binary in build('runaway', runaway).values():
            result = run([binary], expected=3)
            assert 'nonfinite trajectory' in result.stderr
            result = run([binary, '--json'], expected=3)
            assert 'nonfinite trajectory' in result.stderr
            try:
                json.loads(result.stdout)
                raise AssertionError('failed trajectory must not look like complete JSON')
            except json.JSONDecodeError:
                pass

        manifest_path = output / 'manifest.json'
        manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
        report = reference.verify(manifest)
        (output / 'numerical-report.json').write_text(json.dumps(report, indent=2)+'\n')
        assert report['passed'], json.dumps(report, indent=2)
        (output / 'commands.json').write_text(json.dumps(receipts, indent=2)+'\n')
        paths = [p for p in output.iterdir() if p.is_file() and p.name != 'evidence.json' and p.suffix != '.log']
        def sha256(path):
            return hashlib.sha256(path.read_bytes()).hexdigest()
        evidence = {'source_commit': run(['git', 'rev-parse', 'HEAD'], cwd=root).stdout.strip(),
                    'source_dirty': bool(run(['git', 'status', '--porcelain'], cwd=root).stdout.strip()),
                    'compiler_root': (root / 'bootstrap/current/COMMIT').read_text().strip(),
                    'compiler_sha256': sha256(compiler),
                    'platform': platform.platform(),
                    'clang': run(['clang', '--version']).stdout.splitlines()[0],
                    'seconds': time.perf_counter()-started,
                    'artifacts': {p.name: {'bytes': p.stat().st_size, 'sha256': sha256(p)} for p in paths},
                    'source_sha256': {str(p.relative_to(root)): sha256(p) for p in [
                        *sorted((root / 'example/hamiltonian').glob('*.lang')),
                        root / 'test/hamiltonian_e2e.py', root / 'test/hamiltonian_reference.py',
                        root / 'test/hamiltonian_float_reader.lang']}}
        (output / 'evidence.json').write_text(json.dumps(evidence, indent=2)+'\n')
        print(f'PASS hamiltonian_e2e (standalone compiler, O0/O2, AST roundtrip, CSV/JSON, analytic/RK4 oracles, {len(failures)} rejections; {time.perf_counter()-started:.2f}s)')


if __name__ == '__main__':
    main()
