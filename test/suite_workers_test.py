#!/usr/bin/env python3
"""Bounded worker policy regression, including actual LLVM worker descendants."""
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parent.parent
helper = root / 'test/suite_workers.sh'

def run(code, **overrides):
    env = {k: v for k, v in os.environ.items() if k not in
           ('JOBS', 'SUITE_CPU_BUDGET', 'LANG_SUITE_WORKER', 'SEQUENTIAL')}
    env.update(overrides)
    return subprocess.run(['bash', '-c', code], env=env, text=True, capture_output=True)

for requested, expected in [(None, 2), ('1', 1), ('2', 2), ('4', 4), ('16', 4), ('999999999999999999999999', 4)]:
    env = {} if requested is None else {'JOBS': requested}
    result = run(f'source "{helper}"; echo "$JOBS"', **env)
    assert result.returncode == 0 and result.stdout.strip() == str(expected), result
    print(f'PASS JOBS={requested}: {expected}')
for invalid in ['0', '-1', 'no', '1.5', '01', '1+2']:
    assert run(f'source "{helper}"', JOBS=invalid).returncode == 2
for env, expected in [({'JOBS': '16', 'SUITE_CPU_BUDGET': '16'}, '16'),
                      ({'JOBS': '4', 'SEQUENTIAL': '1'}, '1'),
                      ({'JOBS': '4', 'LANG_SUITE_WORKER': '1'}, '1')]:
    result = run(f'source "{helper}"; echo "$JOBS"', **env)
    assert result.returncode == 0 and result.stdout.strip() == expected

# Exercise the unchanged real worker function without starting the full suite.
source = (root / 'test/run_llvm_suite.sh').read_text()
worker = source[source.index('run_one_test() {'):source.index('export -f run_one_test')]
with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as directory:
    tmp = Path(directory)
    fixture = tmp / 'probe.lang'
    fixture.write_text('// 0\nfunc main() i64 { return 0; }\n')
    compiler = tmp / 'compiler'
    compiler.write_text('#!/bin/bash\nsource "' + str(helper) + '"\n[ "$JOBS" = 1 ] || exit 99\nexit "${FAKE_COMPILE_EXIT:-0}"\n')
    compiler.chmod(0o755)
    lli = tmp / 'lli'
    lli.write_text('#!/bin/bash\nexit "${FAKE_RUN_EXIT:-0}"\n')
    lli.chmod(0o755)
    # Eight concurrent parents each try to create a nested pool with JOBS=4.
    probe = f"""source "{helper}"
{worker}
export -f run_one_test
export COMPILER="{compiler}" LANGOS=linux
 do_timeout() {{ shift; "$@"; }}
export -f do_timeout
printf '%s\\n' "{fixture}" "{fixture}" "{fixture}" "{fixture}" "{fixture}" "{fixture}" "{fixture}" "{fixture}" | xargs -P"$JOBS" -I{{}} bash -c 'run_one_test "$1"' _ {{}}
"""
    for requested in [None, '1', '2', '4', '16']:
        env = dict(PATH=str(tmp) + ':' + os.environ['PATH'])
        if requested is not None: env['JOBS'] = requested
        result = run(probe, **env)
        assert result.returncode == 0 and result.stdout.count('PASS probe') == 8, result
    for env in [{'FAKE_COMPILE_EXIT': '7'}, {'FAKE_RUN_EXIT': '124'}]:
        result = run(probe, PATH=str(tmp) + ':' + os.environ['PATH'], **env)
        assert result.returncode != 0 and 'FAIL probe' in result.stdout, result
print('PASS nested workers, explicit integration budget, failure and timeout propagation')
