# Frozen regression contract; execute from the repository root.
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

NAME = 'arli_py_param_shape'
READER = 'minipy'
CASES = [{'label': 'missing_separator', 'body': 'def f(a b):\n    return a+b\n', 'expected': None, 'diagnostic': 'parameter separator', 'prelude': ''}, {'label': 'duplicate', 'body': 'def f(a, a):\n    return a\n', 'expected': None, 'diagnostic': 'duplicate parameter', 'prelude': ''}, {'label': 'reserved_true', 'body': 'def f(True):\n    return True\n', 'expected': None, 'diagnostic': 'reserved parameter', 'prelude': ''}, {'label': 'reserved_false', 'body': 'def f(False):\n    return False\n', 'expected': None, 'diagnostic': 'reserved parameter', 'prelude': ''}, {'label': 'reserved_none', 'body': 'def f(None):\n    return None\n', 'expected': None, 'diagnostic': 'reserved parameter', 'prelude': ''}, {'label': 'valid_trailing', 'body': 'def f(a, b,):\n    return a+b\ndef g():\n    return f(20,22)\n', 'expected': 42, 'diagnostic': None, 'prelude': ''}, {'label': 'valid_empty', 'body': 'def g():\n    return 42\n', 'expected': 42, 'diagnostic': None, 'prelude': ''}]

def arli_py_param_shape_source(case):
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

def arli_py_param_shape_run():
    compiler = os.environ['ARLI_COMPILER']
    failures = []
    with tempfile.TemporaryDirectory(prefix=NAME + '-', dir=os.environ['ARLI_EVIDENCE']) as temp:
        directory = Path(temp)
        for index, case in enumerate(CASES):
            source = directory / (str(index) + '.lang')
            source.write_text(arli_py_param_shape_source(case))
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
    sys.exit(arli_py_param_shape_run())
