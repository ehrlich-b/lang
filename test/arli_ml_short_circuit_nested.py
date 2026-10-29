# Nested short-circuit and closure regressions; run from the repository root.
import os
from pathlib import Path
import subprocess
import tempfile

compiler = Path(os.environ.get('ARLI_COMPILER', 'out/lang_next')).resolve()
root = Path.cwd()
prefix = '''include "std/core.lang"
include "example/minilisp/lisp_runtime.lang"
var arli_calls i64 = 0;
func arli_marker() i64 { arli_calls = arli_calls + 1; return lisp_int(42); }
include "example/minilisp/minilisp.lang"
'''
cases = {
    'capture': '(let ((x 42)) (funcall (lambda () (or nil x))))',
    'capture_both': '(let ((x 42)) (funcall (lambda () (and x x))))',
    'nested_capture': '(let ((x 42)) (funcall (lambda () (or nil (and x (or nil x))))))',
    'if_capture': '(let ((x 42)) (funcall (lambda () (or nil (if 1 x 0)))))',
    'skipped': '(let ((x 42)) (funcall (lambda () (or x (arli_marker)))))',
}
for n in (8, 9, 10):
    expr = '(lambda () 42)'
    for _ in range(n):
        expr = '(or nil ' + expr + ')'
    cases['depth' + str(n)] = '(funcall ' + expr + ')'

env = dict(os.environ, LANGBE='llvm', LANGOS='linux')
with tempfile.TemporaryDirectory(prefix='nested-', dir=os.environ.get('ARLI_EVIDENCE', str(root.parent / 'evidence'))) as tmp:
    d = Path(tmp)
    env['LANG_CACHE'] = str(d / 'cache')
    for name, expr in cases.items():
        source = d / (name + '.lang')
        source.write_text(prefix + 'func main() i64 { if lisp_to_int(#minilisp{ ' + expr + ' }) != 42 { return 90; } if arli_calls != 0 { return 91; } return 0; }\n')
        ir = d / (name + '.ll')
        subprocess.run([compiler, source, '-o', ir], env=env, check=True, timeout=90)
        for opt in ('0', '2'):
            binary = d / (name + '-O' + opt)
            subprocess.run(['clang', '-O' + opt, ir, '-o', binary], check=True, timeout=60)
            subprocess.run([binary], check=True, timeout=10)
        print('PASS', name, 'O0 O2', flush=True)
    # Each lowered expression emits the unique deepest operand call exactly once.
    for n in (1, 4, 8, 10):
        expr = '(arli_marker)'
        for _ in range(n):
            expr = '(or nil ' + expr + ')'
        source = d / ('growth' + str(n) + '.lang')
        source.write_text(prefix + 'func main() i64 { var x i64 = #minilisp{ ' + expr + ' }; return 0; }\n')
        ir = d / ('growth' + str(n) + '.ll')
        subprocess.run([compiler, source, '-o', ir], env=env, check=True, timeout=90)
        calls = ir.read_text().count('call i64 @arli_marker()')
        assert calls == 1, (n, calls)
        print('PASS growth', n, 'one operand call', flush=True)
    # A block-local x must shadow the surrounding function's x in a lambda.
    source = d / 'shadow.lang'
    source.write_text('''include "std/core.lang"
include "std/ast.lang"
reader shadowprobe(text *u8) *u8 {
    var inner *u8 = ast_vec();
    ast_push(inner, ast_var("x", ast_type_i64(), ast_int(42)));
    var lam *u8 = ast_lambda(ast_vec(), ast_type_i64(), ast_block1(ast_return(ast_block_expr(inner, ast_ident("x")))));
    var body *u8 = ast_vec();
    ast_push(body, ast_var("x", ast_type_i64(), ast_int(99)));
    ast_push(body, ast_var("f", ast_type_func(ast_vec(), ast_type_i64()), lam));
    ast_push(body, ast_return(ast_call_named0("f")));
    return ast_program1(ast_func("probe", ast_vec(), ast_type_i64(), ast_block(body)));
}
#shadowprobe{}
func main() i64 { if probe() != 42 { return 90; } return 0; }
''')
    ir = d / 'shadow.ll'
    subprocess.run([compiler, source, '-o', ir], env=env, check=True, timeout=90)
    for opt in ('0', '2'):
        binary = d / ('shadow-O' + opt)
        subprocess.run(['clang', '-O' + opt, ir, '-o', binary], check=True, timeout=60)
        subprocess.run([binary], check=True, timeout=10)
    print('PASS block-local shadow O0 O2', flush=True)
