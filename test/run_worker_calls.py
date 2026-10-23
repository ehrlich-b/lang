#!/usr/bin/env python3
"""Exercise copied-value calls through the production H compile/worker hooks."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import threading

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
parser = argparse.ArgumentParser()
parser.add_argument('--acceptance', choices=['A1', 'A2', 'A3', 'A4'])
options = parser.parse_args()
base = Path(os.environ.get('WORKER_EVIDENCE', tempfile.gettempdir())).resolve()
base.mkdir(parents=True, exist_ok=True)
out = Path(tempfile.mkdtemp(prefix='worker-calls-', dir=base))
compiler = str(Path(os.environ.get('COMPILER', 'out/lang_next')).resolve())
env = dict(os.environ, LANGBE='llvm', LANG_CACHE=str(out / 'cache'))
results = []

def run(name, args, data=b'', code=0, expected=None, error=None, extra=None):
    proc = subprocess.run([str(a) for a in args], input=data, capture_output=True,
                          env=dict(env, **(extra or {})), timeout=180)
    (out / (name + '.stdout')).write_bytes(proc.stdout)
    (out / (name + '.stderr')).write_bytes(proc.stderr)
    ok = proc.returncode == code and (expected is None or proc.stdout == expected)
    if error:
        ok = proc.returncode != 0 and not proc.stdout and error.encode() in proc.stderr
    results.append(dict(name=name, passed=ok, exit=proc.returncode,
                        stdout_sha256=hashlib.sha256(proc.stdout).hexdigest()))
    print(('PASS ' if ok else 'FAIL ') + name, flush=True)
    assert ok, (name, proc.returncode, proc.stdout[:400], proc.stderr[:3000])
    return proc

def value(tag, data):
    return struct.pack('<II', tag, len(data)) + data

def integer(n):
    return value(7, struct.pack('<q', n))

def record(*fields):
    return value(12, struct.pack('<I', len(fields)) + b''.join(fields))

arguments = record(integer(19), integer(23))
answer = integer(42)
run('compile-standalone-host', [compiler, 'test/phase_host/call_standalone.lang', '-o', out / 'standalone.ll'])
run('link-standalone-host', ['clang', '-O0', out / 'standalone.ll', '-o', out / 'standalone'])
run('execute-standalone-host', [out / 'standalone'])
run('compile-host', [compiler, 'test/phase_host/call.lang', '-o', out / 'call.ll'])
run('link-host', ['clang', '-O0', out / 'call.ll', '-o', out / 'call'])
publication = out / 'published.value'

def call(name, mode='call', source='test/phase_host/add.lang', data=arguments, **kw):
    return run(name, [out / 'call', mode, source, out, publication], data, **kw)

def source(name, body):
    path = out / (name + '.lang')
    # Executable entry wrappers consume their one framed request even when
    # the controlled function ignores its arguments.
    body = body.replace('func main() i64 {', 'func main() i64 { var incoming *PhaseBuffer = phase_read_bytes_fd(0, phase_limit(), "arguments");')
    path.write_text('include "std/core.lang"\ninclude "src/stage_values.lang"\n' + body)
    return path

if options.acceptance in (None, 'A1'):
    result = call('add-19-23', expected=answer)
    assert b'execution-target=' in result.stderr and b'output-target=wasm32-unknown-unknown/core-v2' in result.stderr
    assert publication.read_bytes() == answer
    frame = call('generated-ast', 'ast', 'test/phase_host/generated.lang').stdout
    assert struct.unpack_from('<II', frame) == (13, len(frame) - 8)
    ast = out / 'generated.ast'
    ast.write_bytes(frame[24:])
    run('compile-generated-native', [compiler, '--from-ast', ast, '-o', out / 'generated.ll'])
    run('link-generated-native', ['clang', '-O0', out / 'generated.ll', '-o', out / 'generated'])
    run('execute-generated-native', [out / 'generated'], code=42)
    run('compile-generated-output-target', [compiler, '--from-ast', ast, '-o', out / 'generated-wasm.ll'], extra={'LANGOS': 'wasm'})
    run('link-generated-output-target', ['clang', '--target=wasm32-unknown-unknown', '-nostdlib', '-Wl,--no-entry', '-Wl,--export-all', '-Wl,--allow-undefined', out / 'generated-wasm.ll', '-o', out / 'generated.wasm'])
    run('execute-generated-output-target', ['node', 'test/wasm_host.js', out / 'generated.wasm'], code=42)

if options.acceptance in (None, 'A2'):
    for tag in range(1, 10):
        width = 1 if tag <= 2 or tag == 9 else 2 if tag <= 4 else 4 if tag <= 6 else 8
        for label, data in [('zero', bytes(width)), ('high', bytes([1 if tag == 9 else 255]) * width)]:
            frame = value(tag, data)
            call(f'scalar-{tag}-{label}', 'copy', data=frame, expected=frame)
            call(f'worker-scalar-{tag}-{label}', 'echo', 'test/phase_host/echo.lang', data=frame, expected=frame)
    for name, frame in [('bytes-nul', value(10, b'a\0b\xff')),
                        ('unicode', value(11, '水🦉é\0tail'.encode())),
                        ('record', record(integer(-42), value(9, b'\1'), value(10, b'\0'), value(11, '雪'.encode())))]:
        call(name, 'copy', data=frame, expected=frame)
        call('worker-' + name, 'echo', 'test/phase_host/echo.lang', data=frame, expected=frame)
    malformed = [('short-header', b'123', 'value-length'),
                 ('length', struct.pack('<II', 7, 0xffffffff), 'value-length'),
                 ('trailing', answer + b'x', 'value-length'),
                 ('width', value(7, b'1'), 'value-width'),
                 ('bool', value(9, b'\2'), 'value-bool'),
                 ('utf8', value(11, b'\xc0\x80'), 'invalid-utf8'),
                 ('record-count', value(12, struct.pack('<I', 0xffffffff)), 'value-record'),
                 ('record-child', value(12, struct.pack('<III', 1, 7, 99)), 'value-record'),
                 ('record-trailing', value(12, struct.pack('<I', 0) + answer), 'value-record'),
                 ('pointer', value(99, struct.pack('<Q', 0x12345678)), 'unsupported-value'),
                 ('ast-origin', value(13, struct.pack('<IIII', 1, 9, 999, 0) + b'(program)'), 'wire-origin')]
    nested = integer(0)
    for _ in range(66):
        nested = record(nested)
    malformed.append(('record-depth', nested, 'value-depth'))
    for name, frame, diagnostic in malformed:
        before = publication.read_bytes() if publication.exists() else None
        call(name, data=frame, error=diagnostic)
        assert (publication.read_bytes() if publication.exists() else None) == before
    call('wrong-call-signature', 'signature', error='call-signature')
    call('wrong-result-signature', 'result-signature', error='result-signature')
    missing = source('absent-import', 'extern func absent_worker_import() i64;\nfunc main() i64 { return absent_worker_import(); }\n')
    before = publication.read_bytes() if publication.exists() else None
    call('absent-import', source=missing, code=5, expected=b'')
    assert (publication.read_bytes() if publication.exists() else None) == before
    wrong = source('wrong-entry-signature', 'func add(a i64, b i64) i64 { return a+b; }\nfunc main() i64 { return add(19); }\n')
    call('wrong-entry-signature', source=wrong, code=5, expected=b'')
    assert (publication.read_bytes() if publication.exists() else None) == before

if options.acceptance in (None, 'A3'):
    call('fresh-context', 'twice', expected=answer * 2)
    binary = value(10, b'a\0b' * 100000)
    call('binary-duplex', 'echo', 'test/phase_host/echo.lang', data=binary, expected=binary)
    call('failed-rebuild', 'rebuild-fail', expected=answer)
    assert publication.read_bytes() == answer
    bad = source('bad-response', 'func main() i64 { print("unframed stdout"); return 0; }\n')
    call('reject-worker-stdout', source=bad, error='value-length')
    assert publication.read_bytes() == answer
    failed = source('failed-worker', 'func main() i64 { var v *PhaseBuffer = phase_value_i64(99); file_write(1,v.data,v.len); return 1; }\n')
    call('reject-partial-failure', source=failed, code=5, expected=b'')
    assert publication.read_bytes() == answer
    # Repeatedly observe one shared publication while two workers compile and
    # return different, large frames. Any partial write or interleaving fails.
    frames = [value(10, bytes([65 + i]) * 200000) for i in range(2)]
    paths = []
    for i in range(2):
        paths.append(source(f'concurrent-{i}', f'''func main() i64 {{
    var b *u8 = alloc(200000); var i i64 = 0;
    while i < 200000 {{ *(b+i) = {65+i}; i = i+1; }}
    var v *PhaseBuffer = phase_value_new(10,b,200000);
    file_write(1,v.data,v.len); return 0;
}}\n'''))
    # The test host selects a bytes result signature for this pair.
    stop = threading.Event()
    observed = []
    def observe():
        while not stop.is_set():
            observed.append(hashlib.sha256(publication.read_bytes()).hexdigest())
    observer = threading.Thread(target=observe)
    observer.start()
    barrier = threading.Barrier(2)
    def simultaneous(i):
        barrier.wait(timeout=10)
        return call(f'concurrent-{i}', 'bytes', paths[i], expected=frames[i])
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(simultaneous, i) for i in range(2)]
            for future in futures:
                future.result()
    finally:
        stop.set()
        observer.join()
    allowed = {hashlib.sha256(f).hexdigest() for f in [answer, *frames]}
    assert observed and set(observed) <= allowed
    assert publication.read_bytes() in frames
    (out / 'atomic-observations.json').write_text(json.dumps({'reads': len(observed), 'hashes': sorted(set(observed)), 'allowed': sorted(allowed)}, indent=2))

if options.acceptance in (None, 'A4'):
    for tag in [0, 14, 15, 16, 99, 0xffffffff]:
        call(f'unsupported-{tag}', data=value(tag, b''), error='unsupported-value')
    call('untrusted', 'untrusted', error='untrusted-execution-refused')
    call('foreign-execution-target', 'target', error='execution-target')
    text = (ROOT / 'docs/WORKER_CALLS.md').read_text()
    for obligation in ['confinement', 'cancellation', 'fuel', 'C confinement', 'trusted-native']:
        assert obligation in text
    print('PASS residual obligations documented', flush=True)

(out / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
print(f'{len(results)} checks passed; evidence: {out}')
