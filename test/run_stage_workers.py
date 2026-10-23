#!/usr/bin/env python3
"""P1 exercises real host AOT workers and both independent wire decoders."""
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))
from stage_protocol import Value as V, WireError, frame, unframe, read_frame, encode, MAX_BYTES
from stage_host import Host, StageError

os.chdir(ROOT)
base = Path(os.environ.get('STAGING_EVIDENCE', tempfile.gettempdir())).resolve()
base.mkdir(parents=True, exist_ok=True)
OUT = Path(tempfile.mkdtemp(prefix='p1-', dir=base))
compiler = Path(os.environ.get('COMPILER', 'out/lang')).resolve()
rows = []

def check(name, action):
    try:
        action()
    except Exception as error:
        rows.append({'name': name, 'pass': False, 'error': repr(error)})
        (OUT / 'results.json').write_text(json.dumps(rows, indent=2)+'\n')
        raise
    rows.append({'name': name, 'pass': True})
    print('PASS '+name, flush=True)

def equal(a, b):
    assert a == b, (a, b)

def rejects(action, error):
    try: action()
    except (WireError, StageError) as e:
        assert error in str(e), (error, str(e))
    else: raise AssertionError('accepted '+error)

host = Host(compiler, OUT / 'workers', controlled_fixtures=True)
target = V('descriptor', {'backend': V('text', 'llvm'), 'target': V('text', 'wasm32'),
                          'pointer_bits': V('i64', 32)})
def compile_fixture(name, output=target):
    spec = host.fixtures[name]
    return host.compile(name, spec['params'], spec['result'], output)

def command(name, args, expected=0, data=None, env=None):
    proc = subprocess.run(list(map(str, args)), input=data, capture_output=True, timeout=120, env=env)
    (OUT / (name+'.stdout')).write_bytes(proc.stdout)
    (OUT / (name+'.stderr')).write_bytes(proc.stderr)
    (OUT / (name+'.json')).write_text(json.dumps({'command': list(map(str,args)), 'exit': proc.returncode})+'\n')
    assert proc.returncode == expected, (name, proc.returncode, proc.stderr.decode(errors='replace')[:2000])
    return proc

add = compile_fixture('add')
check('host-aot-add-19-23', lambda: equal(host.call(add,V('list',[V('i64',19),V('i64',23)])),V('i64',42)))
check('host-executable-format', lambda: equal(host.artifacts[add].path.read_bytes()[:4], b'\x7fELF' if sys.platform == 'linux' else b'\xcf\xfa\xed\xfe'))

def ast_program():
    ast = host.call(compile_fixture('ast'),V('list',[]))
    equal(ast.kind,'syntax')
    source = OUT / 'generated.ast'; source.write_text(ast.data)
    llvm = OUT / 'generated.ll'; binary = OUT / 'generated'
    env = dict(os.environ, LANGBE='llvm', LANGOS='macos' if sys.platform=='darwin' else 'linux', LANG_CACHE=str(OUT/'ast-cache'))
    command('generated-compile',[compiler,'--from-ast',source,'-o',llvm],env=env)
    command('generated-link',['clang','-O0',llvm,'-o',binary])
    command('generated-run',[binary],42)
check('ast-return-generates-program-42', ast_program)

payload = V('list',[
    *[V('i'+str(bits),n) for bits in (8,16,32,64) for n in (-(1<<(bits-1)),-1,0,(1<<(bits-1))-1)],
    V('bool',True),V('bool',False),V('null'),V('bytes',b'a\0b\xff'),V('text','a\0é漢字🦋'),
    V('record',{'a':V('list',[V('i16',-1234)]),'z':V('text','λ')}),
    V('syntax','(program (func main () (type_base i64) (block (return (number 42)))))'),target])
echo = compile_fixture('echo')
check('copied-widths-nul-unicode-list-record-syntax-descriptor',lambda:equal(host.call(echo,V('list',[payload])),payload))
def copied():
    response = host.call(echo,V('list',[payload]))
    response.data[-1].data['target'] = V('text','modified')
    equal(payload.data[-1].data['target'],V('text','wasm32'))
    equal(host.call(echo,V('list',[payload])),payload)
check('responses-own-storage',copied)
check('process-pointer-rejected',lambda:rejects(lambda:frame(V('pointer',1234)),'non-wire-value'))
check('native-pointer-rejected',lambda:rejects(lambda:frame(object()),'non-wire-value'))
check('closure-rejected',lambda:rejects(lambda:frame(lambda:42),'non-wire-value'))
cycle = V('list',[]); cycle.data.append(cycle)
check('cyclic-wire-object-rejected',lambda:rejects(lambda:frame(cycle),'cyclic-wire-object'))
check('integer-overflow-rejected',lambda:rejects(lambda:frame(V('i8',128)),'integer-range'))
check('wrong-call-signature-rejected',lambda:rejects(lambda:host.call(add,V('list',[V('i32',19),V('i64',23)])),'wrong-signature'))
check('wrong-compile-signature-rejected',lambda:rejects(lambda:host.compile('add',['i32','i64'],'i64',target),'wrong-signature'))
check('wrong-result-signature-rejected',lambda:rejects(lambda:host.call(compile_fixture('wrong_result'),V('list',[])),'wrong-result-signature'))
check('missing-import-rejected',lambda:rejects(lambda:compile_fixture('missing'),'missing-import'))
check('uncontrolled-source-rejected',lambda:rejects(lambda:host.compile('../source',[],'i64',target),'uncontrolled-source'))
check('native-default-fails-closed',lambda:rejects(lambda:Host(compiler,OUT/'denied'),'native-confinement-unavailable'))

# Adversarial raw frames go directly to the AOT process, bypassing the Python
# encoder. Both decoders must reject the same bytes; no fixture executes.
valid = frame(V('list',[payload]))
raw_value = encode(V('i64',0))
bad_cases = {
    'short-header': valid[:15],
    'truncated-payload': valid[:-1],
    'trailing-frame': valid+b'x',
    'oversize-frame': b'STG1'+struct.pack('<III',MAX_BYTES+1,1,0),
    'wrong-version': b'STG2'+valid[4:],
    'reserved-bits': valid[:12]+struct.pack('<I',1)+valid[16:],
    'integer-length': b'STG1'+struct.pack('<III',len(raw_value),1,0)+raw_value[:1]+struct.pack('<I',7)+raw_value[5:],
    'unknown-pointer-tag': b'STG1'+struct.pack('<III',5,1,0)+b'\x0c\0\0\0\0',
    'container-count': frame(V('list',[]))[:21]+struct.pack('<I',100001),
    'duplicate-record-key': b'STG1'+struct.pack('<III',31,1,0)+b'\x09'+struct.pack('<I',26)+struct.pack('<I',2)+(b'\x07\x01\0\0\0a\x00\0\0\0\0')*2,
    'invalid-utf8': frame(V('bytes',b'\xc0\x80'))[:16]+b'\x07\x02\0\0\0\xc0\x80',
}
def reject_raw(name, raw):
    try: unframe(raw,1)
    except WireError: pass
    else: raise AssertionError('Python accepted '+name)
    p = subprocess.run([host.artifacts[echo].path],input=raw,capture_output=True,timeout=10)
    (OUT/(name+'.stderr')).write_bytes(p.stderr)
    assert p.returncode != 0 and not p.stdout and b'stage-error:' in p.stderr, (name,p)
deep = b'\x00\0\0\0\0'
for _ in range(66):
    deep = b'\x08' + struct.pack('<I',len(deep)+4) + struct.pack('<I',1) + deep
bad_cases['depth-budget'] = b'STG1' + struct.pack('<III',len(deep),1,0) + deep
bad_cases['unsorted-record-keys'] = (b'STG1'+struct.pack('<III',31,1,0)+b'\x09'+struct.pack('<I',26)+struct.pack('<I',2)
                                    +b'\x07\x01\0\0\0b\x00\0\0\0\0'+b'\x07\x01\0\0\0a\x00\0\0\0\0')
for name,raw in bad_cases.items():
    check('both-decoders-reject-'+name,lambda n=name,r=raw:reject_raw(n,r))
# Wrong signature also fails at the generated worker boundary.
check('worker-rejects-wrong-signature',lambda:command('worker-wrong-signature',[host.artifacts[add].path],1,frame(V('list',[V('i32',19),V('i64',23)]))))

state = compile_fixture('state')
for i in range(3):
    check('fresh-mutable-state-'+str(i),lambda:equal(host.call(state,V('list',[])),V('i64',41)))
check('failed-compile-no-stale-artifact',lambda:rejects(lambda:compile_fixture('invalid'),'worker-failed'))
check('failed-compile-no-capability',lambda:rejects(lambda:host.call('invalid',V('list',[])),'unknown-artifact'))
def fresh_compilers():
    second = compile_fixture('add')
    assert host.artifacts[second].path != host.artifacts[add].path
    equal(host.call(second,V('list',[V('i64',19),V('i64',23)])),V('i64',42))
    for artifact in host.artifacts.values():
        assert artifact.path.name == 'entry' and not artifact.path.with_name('entry.pending').exists()
    assert not list((OUT/'workers').glob('compile-*/entry.pending'))
check('fresh-compiler-and-complete-atomic-publication',fresh_compilers)
def integrity():
    token = compile_fixture('add')
    with host.artifacts[token].path.open('ab') as f: f.write(b'changed')
    rejects(lambda:host.call(token,V('list',[V('i64',19),V('i64',23)])),'artifact-integrity')
check('artifact-integrity',integrity)

def output_target_copy():
    desc = V('descriptor',{'target':V('text','wasm32'),'pointer_bits':V('i64',32)})
    token = compile_fixture('add',desc)
    desc.data['target']=V('text','changed')
    equal(host.artifacts[token].output_target.data['target'],V('text','wasm32'))
    equal(host.call(token,V('list',[V('i64',19),V('i64',23)])),V('i64',42))
check('wasm-output-target-is-copied-data-helper-is-host-aot',output_target_copy)

def rpc():
    server = subprocess.Popen([sys.executable,'src/stage_host.py','--controlled-fixtures','--compiler',str(compiler),'--storage',str(OUT/'rpc')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    def send(v,kind=2):
        server.stdin.write(frame(v)); server.stdin.flush()
        return unframe(read_frame(server.stdout),kind)
    try:
        token=send(V('record',{'op':V('text','compile'),'fixture':V('text','state'),'signature':V('list',[]),'result':V('text','i64'),'output_target':target}))
        for _ in range(2): equal(send(V('record',{'op':V('text','call'),'artifact':token,'args':V('list',[])})),V('i64',41))
        equal(send(V('record',{'op':V('text','bad')}),3),V('text','request-operation'))
        server.stdin.close(); server.wait(timeout=10)
        equal(server.stderr.read(),b'')
        equal(server.returncode,0)
        diagnostics=list((OUT/'rpc').glob('call-*/*.stderr'))
        assert any(b'fixture diagnostic on stderr' in p.read_bytes() for p in diagnostics)
    finally:
        if server.poll() is None: server.kill(); server.wait()
check('persistent-rpc-stderr-separated-and-error-framed',rpc)

# Exercise the opt-in H hook through ordinary reader expansion with a Wasm
# output target. The helper executable is native; only the generated program
# uses Wasm descriptors and wasm32 layouts.
def wasm_reader():
    env=dict(os.environ, LANGBE='llvm',LANGOS='wasm',LANG_STAGE_FRESH_COMPILER='1',LANG_STAGE_CONTROLLED_FIXTURES='1',LANG_ROOT=str(ROOT),LANG_CACHE=str(OUT/'reader-cache'))
    ir=OUT/'reader-wasm.ll'; wasm=OUT/'reader.wasm'
    # Preserve argv[0] through a logging launcher. An inherited fork-parser
    # path would launch only once; the fresh H hook must exec the launcher
    # again with a generated wrapper source.
    launcher = OUT / 'compiler-launcher'
    launches = OUT / 'compiler-launches.jsonl'
    launcher.write_text('#!'+sys.executable+'\nimport os,sys,json\n'
                        +'with open('+repr(str(launches))+',"a") as f: f.write(json.dumps(sys.argv)+"\\n")\n'
                        +'os.execv('+repr(str(compiler))+',[sys.argv[0]]+sys.argv[1:])\n')
    launcher.chmod(0o755)
    command('reader-host-compile',[launcher,'test/staging/reader.lang','test/staging/answer.staged','-o',ir],env=env)
    invocations = [json.loads(line) for line in launches.read_text().splitlines()]
    assert len(invocations) >= 2 and any('readers/staged.lang' in str(call) for call in invocations[1:]), invocations
    command('reader-wasm-link',['clang','--target=wasm32-unknown-unknown','-nostdlib','-Wl,--no-entry','-Wl,--export-all','-Wl,--allow-undefined',ir,'-o',wasm])
    command('reader-wasm-run',['node','test/wasm_host.js',wasm],42)
    generated = (OUT/'reader-cache/readers/staged.lang').read_text()
    assert 'stage_read()' in generated and 'stage_write(stage_blob(7' in generated
    assert not list((OUT/'reader-cache/readers').glob('*.pending-*'))
    helper=OUT/'reader-cache/readers/staged'
    equal(helper.read_bytes()[:4],b'\x7fELF' if sys.platform=='linux' else b'\xcf\xfa\xed\xfe')
check('H-fresh-compile-hook-wasm-output-host-helper',wasm_reader)

(OUT/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print(str(len(rows))+' staging checks passed; evidence: '+str(OUT))
