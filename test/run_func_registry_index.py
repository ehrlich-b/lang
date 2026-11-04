#!/usr/bin/env python3
"""Bounded registry fragment and parent/candidate diagnostic/IR comparisons."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import subprocess

p = argparse.ArgumentParser()
p.add_argument('--compiler', default='out/lang_next')
p.add_argument('--reference', required=True)
p.add_argument('--output', required=True)
a = p.parse_args()
out = Path(a.output).resolve()
out.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, LANGBE='llvm', LANGOS='linux', TMPDIR=str(out))
records = []

def run(cmd, label, expected=None):
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    r = subprocess.run(list(map(str, cmd)), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    (out / (label + '.stdout')).write_bytes(r.stdout)
    (out / (label + '.stderr')).write_bytes(r.stderr)
    record = dict(argv=list(map(str, cmd)), exit=r.returncode,
                  cpu_seconds=after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime)
    records.append(record)
    (out / 'executions.json').write_text(json.dumps(records, indent=2) + '\n')
    if expected is not None:
        assert r.returncode == expected, (cmd, r.returncode, r.stderr.decode())
    return r

# Compile the actual registry and accessors as a small isolated executable.
code = Path('src/codegen.lang').read_text()
parser = Path('src/parser.lang').read_text()
fragment = 'include "std/core.lang"\n'
for name in ['func_decl_name', 'func_decl_name_len', 'func_decl_param_count', 'func_decl_is_pub']:
    fragment += re.search(r'(?:pub )?func ' + name + r'\([^}]+\}', parser).group() + '\n'
fragment += code[code.index('var cg_funcs '):code.index('// Visibility tracking')]
fragment += 'var cg_func_is_pub *u8 = nil;\nvar cg_func_module *u8 = nil;\nvar cg_current_module i64 = 0;\n'
fragment += code[code.index('func init_func_registry('):code.index('// Both backends report')]
fragment += code[code.index('func find_func_arity('):code.index('// Check visibility for a function call')]
fragment += code[code.index('func memcmp('):code.index('\nfunc ', code.index('func memcmp(') + 1)]
fragment += Path('test/registry_index/registry.lang').read_text()
(out / 'registry-fragment.lang').write_text(fragment)
run([a.compiler, out / 'registry-fragment.lang', '-o', out / 'registry.ll'], 'registry-compile', 0)
run(['clang', '-O0', out / 'registry.ll', '-o', out / 'registry'], 'registry-link', 0)
run([out / 'registry'], 'registry-runtime', 0)

for case, want, diagnostic in [
    ('overloads', 0, None), ('runtime', 0, None),
    # Both compilers hit the inherited reader/libc LLVM symbol collision.
    # The isolated registry probe above verifies read/1 versus read/3 lookup.
    ('read', 1, "error: linking reader 'read' failed"),
    ('wrong', 1, "function 'shape' takes 1 argument, called with 2"),
    ('unknown', 1, "undefined function 'missing'"),
    ('cross_module', 1, "function 'hidden' is not public"),
]:
    outputs = []
    for label, compiler in [('parent', a.reference), ('candidate', a.compiler)]:
        ir = out / (case + '-' + label + '.ll')
        r = run([compiler, 'test/registry_index/' + case + '.lang', '-o', ir], case + '-' + label, want)
        if diagnostic:
            assert diagnostic.encode() in r.stderr, r.stderr
            assert re.search(rb':\d+:\d+:', r.stderr), r.stderr
        outputs.append((r.stderr, ir.read_bytes() if ir.exists() else None))
    assert outputs[0] == outputs[1], (case, 'IR or diagnostic/location changed')
    if case == 'runtime':
        run(['clang', '-O0', out / 'runtime-candidate.ll', '-o', out / 'runtime'], 'runtime-link', 0)
        run([out / 'runtime'], 'runtime-execute', 0)
inputs = [Path('src/codegen.lang'), Path('src/codegen_llvm.lang'), Path('src/parser.lang'),
          Path(a.compiler).resolve(), Path(a.reference).resolve(), Path(__file__)]
inputs += sorted(Path('test/registry_index').glob('*.lang'))
(out / 'input-hashes.json').write_text(json.dumps({str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in inputs}, indent=2) + '\n')
print('PASS: first-match/arity/collision/reset fragment, read overload, forward runtime, wrong-arity/private diagnostic locations, unknown-name IR; exact parent/candidate equality')
