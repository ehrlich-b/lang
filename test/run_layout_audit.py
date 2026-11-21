#!/usr/bin/env python3
"""Audit real storage calculators and fail-closed profile admission."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, help='new artifact directory (default: a fresh temporary directory)')
args = parser.parse_args()
if args.output is None:
    out = Path(tempfile.mkdtemp(prefix='lang-layout-audit-')).resolve()
else:
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
print(f'Layout audit artifacts: {out}', flush=True)
os.chdir(ROOT)
compiler=str(Path(os.environ.get('COMPILER','out/bootstrap_verify/kernel2')).resolve());rows=[]
def check(name,command,env=None,expected=0,stdout=None,diagnostic=None):
    r=subprocess.run(command,env=env,capture_output=True,timeout=180)
    (out/(name+'.stdout')).write_bytes(r.stdout);(out/(name+'.stderr')).write_bytes(r.stderr)
    good=r.returncode==expected and (stdout is None or r.stdout==stdout) and (diagnostic is None or diagnostic in r.stderr)
    rows.append(dict(name=name,command=command,exit=r.returncode,pass_=good))
    if not good:
        (out/'receipt.json').write_text(json.dumps(dict(rows=rows,pass_=False),indent=2)+'\n')
        raise RuntimeError(name+': unexpected result; inspect saved stdout/stderr')
    return r
base=dict(os.environ,LANGBE='llvm',LANGOS='macos' if os.uname().sysname=='Darwin' else 'linux',LANG_LAYOUT_PROFILE='bootstrap-internal-v1')
check('emit',[compiler,'test/layout_audit.lang','-o',str(out/'audit.ll')],base)
check('link',['clang','-O0',str(out/'audit.ll'),'-o',str(out/'audit')])
check('calculators',[str(out/'audit')],base,stdout=b'16 0 8 16 0 8\n8 0 8 2 0 1\n')
ref=out/'reference.c';ref.write_text('#include <stddef.h>\n#include <stdio.h>\nstruct Pair { long long a,b; }; struct Bytes { unsigned char a,b; };\nint main(void) { printf("%zu %zu %zu\\n%zu %zu %zu\\n",sizeof(struct Pair),offsetof(struct Pair,a),offsetof(struct Pair,b),sizeof(struct Bytes),offsetof(struct Bytes,a),offsetof(struct Bytes,b)); }\n')
check('reference-link',['clang','-std=c11',str(ref),'-o',str(out/'reference')]);check('reference',[str(out/'reference')],stdout=b'16 0 8\n2 0 1\n')
for backend,target in [('llvm',base['LANGOS']),('llvm','wasm'),('wasm','wasm'),('x86','linux')]:
    if backend=='x86' and os.uname().sysname!='Linux':continue
    env=dict(base,LANGBE=backend,LANGOS=target,LANG_LAYOUT_PROFILE='audited-slots-v1')
    for name,field,accepted in [('pair','i64',True),('bytes','u8',False),('array','[2]i64',False),('unknown','Mystery',False)]:
        source=out/(name+'.lang');source.write_text('struct P { a '+field+'; b '+field+'; }\nfunc main() i64 { return 42; }\n')
        check(backend+'-'+target+'-'+name,[compiler,str(source),'-o',str(out/(backend+'-'+target+'-'+name+'.output'))],env,expected=0 if accepted else 1,diagnostic=None if accepted else b'unaudited field layout')
(out/'receipt.json').write_text(json.dumps(dict(rows=rows,pass_=all(r['pass_'] for r in rows)),indent=2)+'\n')
for r in rows:print(('PASS' if r['pass_'] else 'FAIL')+' '+r['name'])
raise SystemExit(0 if all(r['pass_'] for r in rows) else 1)
