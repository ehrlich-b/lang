# Frozen regression contract; execute from the repository root.
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

NAME = 'arli_py_floor_mod'
READER = 'minipy'
CASES = [{'label': 'floor_negative_left', 'body': 'def g():\n    return (-7 // 3) + 50\n', 'expected': 47, 'diagnostic': None, 'prelude': ''}, {'label': 'floor_negative_right', 'body': 'def g():\n    return (7 // -3) + 50\n', 'expected': 47, 'diagnostic': None, 'prelude': ''}, {'label': 'mod_negative_left', 'body': 'def g():\n    return (-7 % 3) + 40\n', 'expected': 42, 'diagnostic': None, 'prelude': ''}, {'label': 'mod_negative_right', 'body': 'def g():\n    return (7 % -3) + 44\n', 'expected': 42, 'diagnostic': None, 'prelude': ''}, {'label': 'exact_and_positive', 'body': 'def g():\n    return (-6 // 3) + (-7 // -3) + (8 // 2) + 38\n', 'expected': 42, 'diagnostic': None, 'prelude': ''}, {'label': 'precedence', 'body': 'def g():\n    return 40 + 8 // 3 * 2 - 2\n', 'expected': 42, 'diagnostic': None, 'prelude': ''}, {'label': 'single_evaluation', 'body': 'def g():\n    return (arli_left() // arli_right()) + arli_trace\n', 'expected': 9, 'diagnostic': None, 'prelude': 'var arli_trace i64=0; func arli_left() i64 { arli_trace=arli_trace*10+1; return -7; } func arli_right() i64 { arli_trace=arli_trace*10+2; return 3; }'}, {'label': 'ordinary_slash', 'body': 'def g():\n    return (-7 / 3) + 44\n', 'expected': 42, 'diagnostic': None, 'prelude': ''}]

def arli_py_floor_mod_source(case):
    runtime = 'include "example/minilisp/lisp_runtime.lang"\n' if READER == 'minilisp' else ''
    source = 'include "std/core.lang"\n' + runtime + case['prelude'] + '\n'
    source += 'include "example/' + READER + '/' + READER + '.lang"\n'
    if READER == 'minilisp' and not case['body'].startswith('(defun'):
        source += 'func main() i64 { var result i64 = #minilisp{ ' + case['body'] + ' };\n'
        if case['expected'] is not None:
            if case['expected'] == 0 and case['label'] == 'and_skips':
                source += 'if !lisp_is_nil(result) { return 90; }\n'
            else:
                source += 'if lisp_to_int(result) != ' + str(case['expected']) + ' { return 90; }\n'
        source += case.get('postcheck', '') + '\nreturn 0; }\n'
        return source
    source += '#' + READER + '{\n' + case['body'] + '\n}\n'
    invoke = case.get('invoke', 'g()')
    if case['expected'] is not None:
        source += 'func main() i64 { if ' + invoke + ' != ' + str(case['expected']) + ' { return 90; } return 0; }\n'
    else:
        source += 'func main() i64 { return 0; }\n'
    return source

def arli_py_floor_mod_run():
    compiler = os.environ['ARLI_COMPILER']
    failures = []
    with tempfile.TemporaryDirectory(prefix=NAME + '-', dir=os.environ['ARLI_EVIDENCE']) as temp:
        directory = Path(temp)
        for index, case in enumerate(CASES):
            source = directory / (str(index) + '.lang')
            source.write_text(arli_py_floor_mod_source(case))
            output = directory / (str(index) + '.ll')
            env = dict(os.environ, LANGBE='llvm', LANGOS='linux', LANG_CACHE=str(directory / 'cache'))
            result = subprocess.run([compiler, str(source), '-o', str(output)], env=env, capture_output=True, timeout=60)
            diagnostic = result.stderr.decode(errors='replace') + result.stdout.decode(errors='replace')
            if case['diagnostic'] is not None:
                if result.returncode == 0:
                    failures.append('accepted invalid case ' + case['label'])
                elif case['diagnostic'] not in diagnostic or not re.search(READER.replace('minilisp', 'minilisp') + r':\d+:\d+:', diagnostic):
                    failures.append('wrong diagnostic/location in ' + case['label'] + ': ' + diagnostic[-1500:])
                elif output.exists() and output.stat().st_size:
                    failures.append('usable output after rejection in ' + case['label'])
                else:
                    print('PASS', NAME, case['label'], 'rejected with located diagnostic')
            else:
                if result.returncode:
                    failures.append('positive compile failed in ' + case['label'] + ': ' + diagnostic[-1500:])
                    continue
                for opt in ['0', '2']:
                    binary = directory / (str(index) + '-O' + opt)
                    linked = subprocess.run(['clang', '-O' + opt, str(output), '-o', str(binary)], capture_output=True, timeout=30)
                    if linked.returncode:
                        failures.append('invalid LLVM in ' + case['label'] + ': ' + linked.stderr.decode(errors='replace')[-1500:])
                        continue
                    ran = subprocess.run([str(binary)], capture_output=True, timeout=5)
                    if case.get('runtime_error'):
                        if ran.returncode == 0 or case['runtime_error'] not in ran.stderr.decode(errors='replace'):
                            failures.append('missing loud runtime rejection ' + case['label'] + ' at O' + opt)
                        else:
                            print('PASS', NAME, case['label'], 'runtime rejection O' + opt)
                    elif ran.returncode:
                        failures.append('runtime assertion ' + case['label'] + ' at O' + opt + ' (exit ' + str(ran.returncode) + ')')
                    else:
                        print('PASS', NAME, case['label'], 'O' + opt)
    for failure in failures:
        print('FAIL ' + NAME + ': ' + failure)
    return bool(failures)

if __name__ == '__main__':
    sys.exit(arli_py_floor_mod_run())
