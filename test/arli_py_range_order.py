# Frozen regression contract; execute from the repository root.
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

NAME = 'arli_py_range_order'
READER = 'minipy'
CASES = [{'label': 'bound_order', 'body': 'def g():\n    total = 0\n    for i in range(arli_start(), arli_stop()):\n        total += i\n    return total + arli_trace\n', 'expected': 15, 'diagnostic': None, 'prelude': 'var arli_trace i64 = 0; func arli_start() i64 { arli_trace=arli_trace*10+1; return 1; } func arli_stop() i64 { arli_trace=arli_trace*10+2; return 3; }'}, {'label': 'last_value', 'body': 'def g():\n    i = 99\n    for i in range(1, 4):\n        pass\n    return i\n', 'expected': 3, 'diagnostic': None, 'prelude': ''}, {'label': 'empty_preserves', 'body': 'def g():\n    i = 42\n    for i in range(3, 1):\n        i = 0\n    return i\n', 'expected': 42, 'diagnostic': None, 'prelude': ''}, {'label': 'negative_continue', 'body': 'def g():\n    total = 0\n    for i in range(5, 0, -2):\n        if i == 3:\n            continue\n        total += i\n    return total * 10 + i\n', 'expected': 61, 'diagnostic': None, 'prelude': ''}, {'label': 'body_assignment', 'body': 'def g():\n    total = 0\n    for i in range(3):\n        i = 40\n        total += 1\n    return total + i\n', 'expected': 43, 'diagnostic': None, 'prelude': ''}, {'label': 'break_keeps_value', 'body': 'def g():\n    for i in range(1, 9):\n        if i == 4:\n            break\n    return i\n', 'expected': 4, 'diagnostic': None, 'prelude': ''}]

def arli_py_range_order_source(case):
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

def arli_py_range_order_run():
    compiler = os.environ['ARLI_COMPILER']
    failures = []
    with tempfile.TemporaryDirectory(prefix=NAME + '-', dir=os.environ['ARLI_EVIDENCE']) as temp:
        directory = Path(temp)
        for index, case in enumerate(CASES):
            source = directory / (str(index) + '.lang')
            source.write_text(arli_py_range_order_source(case))
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
    sys.exit(arli_py_range_order_run())
