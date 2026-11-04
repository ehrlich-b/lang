#!/usr/bin/env python3
"""Compare complete token records with the pre-dispatch lexer on a small corpus."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import subprocess

BASE = '4b93dcaa32c177ed827fb7597b02d8431ace2dec'
p = argparse.ArgumentParser()
p.add_argument('--evidence', type=Path, required=True)
a = p.parse_args()
out = a.evidence.resolve()
out.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, LANGBE='llvm', LANGOS='linux')

def run(cmd):
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    result = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    tool = Path(shutil.which(str(cmd[0])))
    print(json.dumps({'argv': list(map(str, cmd)), 'exit': result.returncode,
                     'cpu_seconds': after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime,
                     'tool_sha256': hashlib.sha256(tool.read_bytes()).hexdigest()}), flush=True)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors='replace'))
    return result.stdout

parent = run(['git', 'show', BASE + ':src/lexer.lang']).decode()
(out / 'parent-lexer.lang').write_text(parent)
words = re.findall(r'if lexeme_eq\("(\w+)"\)', parent)
cases = []
for word in words:
    cases.extend([word, '_' + word, word + '_', 'x' + word, word + 'x'])
    cases.extend(word[:i] for i in range(1, len(word)))
    cases.extend(word[:i] + 'z' + word[i+1:] for i in range(len(word)))
cases += [' '.join(words), '\r\n'.join(words), 'α if β\r\nfunc', '"λ"\r\nif', 'syscall syscallx', '', 'a', 'very_long_identifier']
cases = list(dict.fromkeys(cases))

def quote(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('\r', '\\r').replace('\n', '\\n') + '"'

harness = '''func dump(source *u8) void {
    lexer_init(source);
    var done i64 = 0;
    while done == 0 {
        var tok *u8 = scan_token();
        print_int(tok_type(tok)); print(" ");
        print_int(tok_line(tok)); print(" ");
        print_int(tok_col(tok)); print(" ");
        print_int(tok_lexeme_len(tok)); print(" ");
        var i i64 = 0;
        while i < tok_lexeme_len(tok) {
            print_int(*(tok_lexeme(tok) + i)); print(" ");
            i = i + 1;
        }
        println("");
        if tok_type(tok) == TOKEN_EOF { done = 1; }
    }
}
func main() i64 {
'''
for case in cases:
    harness += '    dump(' + quote(case) + ');\n'
harness += '    return 0;\n}\n'
(out / 'corpus.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2) + '\n')
(out / 'tokens.lang').write_text(harness)
records = []
for label, lexer in [('parent', out / 'parent-lexer.lang'), ('candidate', Path('src/lexer.lang'))]:
    ir = out / (label + '.ll')
    exe = out / label
    run(['out/lang_next', 'std/core.lang', str(lexer), str(out / 'tokens.lang'), '-o', str(ir)])
    run(['clang', '-O0', str(ir), '-o', str(exe)])
    data = run([str(exe)])
    (out / (label + '-tokens.txt')).write_bytes(data)
    records.append(data)
assert records[0] == records[1], 'token kinds/text/spans changed'
# Check keyword kinds independently of the candidate dispatch.
constants = dict(re.findall(r'var (TOKEN_\w+) i64 = (\d+);', parent))
expected = dict(re.findall(r'if lexeme_eq\("(\w+)"\) \{ return (TOKEN_\w+);', parent))
rows = iter(records[1].decode().splitlines())
for case in cases:
    first = next(rows)
    if case in expected:
        assert int(first.split()[0]) == int(constants[expected[case]])
    if int(first.split()[0]) != 0:
        while int(next(rows).split()[0]) != 0:
            pass
# The existing comprehensive fragment must also compile and run.
run(['out/lang_next', 'std/core.lang', 'src/lexer.lang', 'test/lexer_full_test.lang', '-o', str(out / 'lexer_full_test.ll')])
run(['clang', '-O0', str(out / 'lexer_full_test.ll'), '-o', str(out / 'lexer_full_test')])
(out / 'lexer_full_test.txt').write_bytes(run([str(out / 'lexer_full_test')]))
print(json.dumps({'cases': len(cases), 'token_rows': len(records[0].splitlines()), 'sha256': hashlib.sha256(records[0]).hexdigest(), 'result': 'PASS'}))
