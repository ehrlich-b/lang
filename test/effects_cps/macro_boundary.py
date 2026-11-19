#!/usr/bin/env python3
"""Unexpanded macros must not bypass CPS lifetime or call-graph validation."""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
COMPILER = str(Path(os.environ.get('COMPILER', 'out/lang_next')).resolve())
LEGACY = str(Path(os.environ.get('LEGACY_COMPILER', 'out/lang')).resolve())
OUT = Path(os.environ.get('EFFECTS_MACRO_EVIDENCE_DIR') or
           tempfile.mkdtemp(prefix='effects-macro-')).resolve()
OUT.mkdir(parents=True, exist_ok=True)
ENV = dict(os.environ, LANGBE='llvm', LANG_CACHE=str(OUT / 'cache'))
DIAGNOSTIC = b'CPS: unexpanded macro call is unsupported'
SOURCES = {
    'address': '''include "std/core.lang"
effect Ask(i64) i64
macro address() { return ${ &a[0] }; }
func worker() i64 {
    var a [2]i64;
    a[0] = 42;
    var p *i64 = address();
    perform Ask(1);
    return *p;
}
func main() i64 {
    var result i64 = handle { worker() } with {
        return(v) => v, Ask(x, k) => resume k(x)
    };
    print_int(result); println(""); return 0;
}
''',
    'call': '''include "std/core.lang"
effect Ask(i64) i64
macro invoke() { return ${ worker() }; }
func worker() i64 { return perform Ask(42); }
func main() i64 {
    var result i64 = handle { invoke() } with {
        return(v) => v, Ask(x, k) => resume k(x)
    };
    print_int(result); println(""); return 0;
}
''',
    # No explicit effect is visible to the fixed-point analysis at all.
    'hidden': '''include "std/core.lang"
effect Ask(i64) i64
macro hidden() { return ${ handle { perform Ask(42) } with {
    return(v) => v, Ask(x, k) => resume k(x)
} }; }
func main() i64 { print_int(hidden()); println(""); return 0; }
''',
}


def run(args, label, env):
    result = subprocess.run(args, env=env, capture_output=True, timeout=60)
    (OUT / (label + '.stdout')).write_bytes(result.stdout)
    (OUT / (label + '.stderr')).write_bytes(result.stderr)
    (OUT / (label + '.exit')).write_text(f'{result.returncode}\n')
    return result


for name, text in SOURCES.items():
    source = OUT / (name + '.lang')
    source.write_text(text)
    # Unique paths let readiness rerun without reusing an existing output.
    scratch = Path(tempfile.mkdtemp(dir=OUT, prefix=name + '-'))
    ir = scratch / 'legacy.ll'
    result = run([LEGACY, str(source), '-o', str(ir)], name + '-legacy-emit', ENV)
    assert result.returncode == 0, result.stderr
    binary = scratch / 'legacy'
    result = run([os.environ.get('CLANG', 'clang'), '-O0', str(ir), '-o', str(binary)],
                 name + '-legacy-build', ENV)
    assert result.returncode == 0, result.stderr
    result = run([str(binary)], name + '-legacy-run', ENV)
    assert (result.returncode, result.stdout, result.stderr) == (0, b'42\n', b''), result
    # Rejection precedes IR publication, so every downstream optimizer
    # profile is denied the unsafe module, including full LTO.
    for profile in ['O0', 'O1', 'O2', 'O2-lto']:
        output = scratch / (profile + '.ll')
        result = run([COMPILER, str(source), '-o', str(output)],
                     name + '-' + profile, ENV)
        assert result.returncode != 0 and DIAGNOSTIC in result.stderr, result.stderr
        assert not output.exists(), 'unsafe macro core published IR'
        print(f'{name} {profile}: refused before IR publication; legacy O0 prints 42')

source = OUT / 'unused.lang'
source.write_text('''include "std/core.lang"
effect Ask(i64) i64
macro scalar() { return ${ 42 }; }
func main() i64 { print_int(scalar()); println(""); return 0; }
''')
result = run([COMPILER, 'run', str(source)], 'unused-run', ENV)
assert (result.returncode, result.stdout) == (0, b'42\n'), result
print('unused declaration: macro prints 42 at default optimization')
print('CPS macro boundary: PASS')
