#!/usr/bin/env python3
"""Accept optimized effects only when behavior matches O0 or the build rejects it."""
import csv
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parent.parent
os.chdir(root)
compiler = str(Path(os.environ.get('COMPILER', './out/lang')).resolve())
evidence = Path((os.environ.get('EFFECTS_EVIDENCE_DIR') or tempfile.mkdtemp(prefix='effects-safety-'))).resolve()
evidence.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, LANGBE='llvm')
programs = sorted(p for p in Path('test/suite').glob('*.lang')
                  if re.search(r'^\s*effect\s|\bperform\s|\bhandle\s*\{', p.read_text(), re.M))
programs += [Path('test/effects/two_performs.lang'), Path('test/effects/two_handlers.lang'),
             Path('test/effects_o2_twice.lang')]
expected_output = {'two_performs': b'500491\n', 'two_handlers': b'2268\n',
                   'effects_o2_twice': b'62\n2\n'}
rows = []
failed = False

def run(command, prefix, run_env=env):
    result = subprocess.run(command, env=run_env, capture_output=True, timeout=60)
    prefix.with_suffix('.stdout').write_bytes(result.stdout)
    prefix.with_suffix('.stderr').write_bytes(result.stderr)
    prefix.with_suffix('.exit').write_text(str(result.returncode) + '\n')
    return result

for source in programs:
    name = source.stem
    directory = evidence / name
    directory.mkdir(parents=True, exist_ok=True)
    case_env = dict(env, LANG_CACHE=str(directory / 'cache'))
    try:
        ir = directory / 'program.ll'
        compiled = run([compiler, str(source), '-o', str(ir)], directory / 'compiler', case_env)
        if compiled.returncode:
            raise RuntimeError('LLVM emission failed: ' + compiled.stderr.decode(errors='replace'))
        reference = None
        for level in range(3):
            binary = directory / f'O{level}'
            build = run([os.environ.get('CLANG', 'clang'), f'-O{level}', str(ir), '-o', str(binary)],
                        directory / f'build-O{level}')
            if build.returncode:
                if level == 0 or not build.stderr.strip():
                    raise RuntimeError(f'O{level} build failed without an acceptable baseline/diagnostic')
                rows.append([name, f'-O{level}', 'LOUD BUILD FAILURE', '', '', build.returncode])
                continue
            result = run([str(binary)], directory / f'run-O{level}', case_env)
            behavior = (result.returncode, result.stdout, result.stderr)
            if level == 0:
                match = re.search(r'expect:\s*(\d+)', source.read_text().splitlines()[0])
                expected_exit = int(match.group(1)) if match else 0
                if result.returncode != expected_exit:
                    raise RuntimeError(f'O0 exit {result.returncode}, expected {expected_exit}')
                if name in expected_output and result.stdout != expected_output[name]:
                    raise RuntimeError(f'O0 output {result.stdout!r}, expected {expected_output[name]!r}')
                reference = behavior
            verdict = 'PASS' if behavior == reference else 'WRONG BEHAVIOR'
            failed |= verdict != 'PASS'
            rows.append([name, f'-O{level}', verdict, result.stdout.decode(errors='replace'),
                         result.stderr.decode(errors='replace'), result.returncode])
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        rows.append([name, '', 'FAIL', str(error), '', ''])
        failed = True

with (evidence / 'matrix.tsv').open('w') as output:
    writer = csv.writer(output, delimiter='\t')
    writer.writerow(['program', 'optimization', 'verdict', 'stdout', 'stderr', 'exit'])
    writer.writerows(rows)
(evidence / 'matrix.json').write_text(json.dumps(rows, indent=2) + '\n')
for row in rows:
    print(f'{row[0]} {row[1]}: {row[2]}; stdout={row[3]!r}; exit={row[5]}')
print(f"Effects safety: {'FAIL' if failed else 'PASS'} ({len(programs)} programs, O0/O1/O2)")
sys.exit(1 if failed else 0)
