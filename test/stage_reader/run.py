#!/usr/bin/env python3
"""Read-time native AST evaluation, reader compatibility and failure atomicity."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import zlib

ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
compiler = Path(os.environ.get('COMPILER', 'out/lang_next')).resolve()
base = Path(os.environ.get('STAGE_READER_EVIDENCE', tempfile.gettempdir())).resolve()
base.mkdir(parents=True, exist_ok=True)
out = Path(tempfile.mkdtemp(prefix='stage-reader-', dir=base))
env = dict(os.environ, LANGBE='llvm', LANGOS='macos' if os.uname().sysname == 'Darwin' else 'linux',
           LANG_CACHE=str(out / 'cache'), LANG_STAGE_WORKSPACE=str(out / 'calls'))
rows = []

def run(name, args, code=0, extra=None, timeout=60, cwd=None, unset=()):
    start = time.monotonic()
    command_env = dict(env, **(extra or {}))
    for key in unset:
        command_env.pop(key, None)
    proc = subprocess.run(list(map(str, args)), capture_output=True,
                          env=command_env, timeout=timeout, cwd=cwd)
    (out / (name + '.stdout')).write_bytes(proc.stdout)
    (out / (name + '.stderr')).write_bytes(proc.stderr)
    rows.append(dict(name=name, command=list(map(str, args)), exit=proc.returncode,
                     seconds=time.monotonic()-start))
    (out / 'results.json').write_text(json.dumps(rows, indent=2)+'\n')
    assert proc.returncode == code, (name, proc.returncode, proc.stderr.decode(errors='replace')[-6000:])
    print('PASS ' + name, flush=True)
    return proc

def fragment(name):
    path = out / (name + '.ast')
    run('ast-' + name, [compiler, '--emit-ast', 'test/stage_reader/' + name + '.lang', '-o', path])
    return path

def compile_run(name, source, code=0):
    path = out / (name + '.lang'); path.write_text(source)
    ir = out / (name + '.ll'); binary = out / name
    run('compile-' + name, [compiler, path, '-o', ir])
    run('link-' + name, ['clang', '-Wno-override-module', '-O0', ir, '-o', binary])
    return run('execute-' + name, [binary], code=code), ir

# Included source names remain logical even when opened through LANG_ROOT.
# Neither the include nor its reader exists in this caller's working directory.
if '--path-only' not in sys.argv and '--collision-only' not in sys.argv:
    caller = out / 'resource-caller'; caller.mkdir()
    source = caller / 'main.lang'
    source.write_text('include "test/stage_reader/resource_include.lang"\n')
    resource_env = {'LANG_ROOT': str(ROOT), 'LANG_STAGE_SOURCE_PATH': '/untrusted-source-path'}
    ir = out / 'resource-include.ll'; binary = out / 'resource-include'
    run('compile-resource-include', [compiler, source, '-o', ir], extra=resource_env, cwd=caller)
    run('link-resource-include', ['clang', '-Wno-override-module', ir, '-o', binary])
    run('execute-resource-include', [binary], code=42)
    failed = out / 'resource-failure.ll'
    proc = run('resource-include-span', [compiler, source, '-o', failed],
               code=1, extra=dict(resource_env, LANG_STAGE_MAX_MS='1'), cwd=caller)
    fixture = (ROOT / 'test/stage_reader/resource_include.lang').read_bytes()
    start = fixture.index(b'#tiny'); end = fixture.index(b'}', start) + 1
    assert ('test/stage_reader/resource_include.lang:bytes ' + str(start) + '..' + str(end)).encode() in proc.stderr
    assert b'call-time-limit' in proc.stderr and b'missing-reader-source' not in proc.stderr
    assert not failed.exists() or not failed.stat().st_size
    # Project-local inputs continue to win over a resource-root namesake.
    local = caller / 'test/stage_reader/resource_include.lang'
    local.parent.mkdir(parents=True)
    local.write_text('include "example/tiny/stage.lang"\n#tiny{answer 43}\n')
    override = out / 'resource-override.ll'
    run('resource-local-precedence', [compiler, source, '-o', override],
        extra=resource_env, cwd=caller)
    assert re.search(r'define [^\n]*@main\([^\n]*\).*?ret i64 43\b', override.read_text(), re.S)
    print('PASS resource-root-include-logical-span-and-local-precedence', flush=True)
    if '--resource-only' in sys.argv:
        print('PASS resource include regression; evidence: ' + str(out), flush=True)
        sys.exit(0)

# A persistent cache may contain calls from an earlier process with this PID.
# Use the LANG_CACHE fallback, without an explicit per-reader workspace.
if '--path-only' not in sys.argv:
    echo = fragment('echo')
    source = out / 'input.collision'; source.write_text(str(echo))
    dest = out / 'collision.ast'
    cache = out / 'collision-cache'
    run('read-reused-pid', [compiler, 'read', 'test/stage_reader/collision.lang',
        source, '-o', dest], extra={'LANG_CACHE': str(cache)}, unset=('LANG_STAGE_WORKSPACE',))
    assert b'(return (number 42))' in dest.read_bytes()
    stale = [p for p in cache.glob('call-*') if (p / 'program').read_bytes() == b'stale executable']
    assert len(stale) == 2
    assert all((p / 'result.pending').read_bytes() == b'stale result' for p in stale)
    fresh = set(cache.glob('call-*')) - set(stale)
    assert len(fresh) == 2
    assert all((p / 'program.ll').is_file() and p.stat().st_mode & 0o777 == 0o700 for p in fresh)
    publication, = cache.glob('stage-value-*')
    assert publication.read_bytes() == struct.pack('<IIq', 7, 8, 43)
    print('PASS reused-pid-cache-two-fresh-calls-stale-files-preserved', flush=True)
    if '--collision-only' in sys.argv:
        print('PASS workspace collision regression; evidence: ' + str(out), flush=True)
        sys.exit(0)

# LANG_ROOT must not bypass compiler resolution for the nested stage launcher.
# Keep the bare invocation name: resolving it here would hide execve failures.
invocation = Path(os.environ.get('COMPILER', 'out/lang_next')).absolute()
path_source = out / 'path-input.tiny'; path_source.write_text('answer 42')
# execvp skips these entries. The nested compiler and linker must agree.
shadow = out / 'non-executable'; shadow.mkdir()
directories = out / 'directories'; directories.mkdir()
for name in (invocation.name, 'clang'):
    decoy = shadow / name; decoy.write_text('readable but not executable\n'); decoy.chmod(0o644)
    (directories / name).mkdir()
path_env = {'LANG_ROOT': str(ROOT),
            'PATH': os.pathsep.join(map(str, (directories, shadow, invocation.parent))) +
                    os.pathsep + os.environ.get('PATH', '')}
# Linux identifies its running image via /proc/self/exe, so independently
# exercise the shared lookup used by tools and the other native host.
lookup_ir = out / 'path-lookup.ll'; lookup = out / 'path-lookup'
run('compile-path-lookup', [compiler, 'test/stage_reader/path_lookup.lang', '-o', lookup_ir])
run('link-path-lookup', ['clang', '-Wno-override-module', lookup_ir, '-o', lookup])
for name in (invocation.name, 'clang'):
    expected_path = shutil.which(name, path=path_env['PATH'])
    proc = run('lookup-' + name, [lookup], extra=dict(path_env, LOOKUP_TOOL=name))
    assert proc.stdout.decode().strip() == expected_path
# Empty leading, interior, trailing and sole entries mean the current directory.
local_tool = out / 'local-tool'; local_tool.write_text('#!/bin/sh\nexit 0\n'); local_tool.chmod(0o111)
for i, search_path in enumerate(('', ':missing', 'missing::absent', 'missing:')):
    proc = run('lookup-empty-' + str(i), [lookup],
               extra={'PATH': search_path, 'LOOKUP_TOOL': local_tool.name}, cwd=out)
    assert proc.stdout == b'./local-tool\n'
absolute_ast = out / 'absolute-compiler.ast'
path_ast = out / 'path-compiler.ast'
run('absolute-compiler-lang-root', [compiler, 'read', 'example/tiny/stage.lang',
    path_source, '-o', absolute_ast], extra=path_env)
run('path-compiler-lang-root', [invocation.name, 'read', 'example/tiny/stage.lang',
    path_source, '-o', path_ast], extra=path_env)
assert b'(return (number 42))' in path_ast.read_bytes()
assert path_ast.read_bytes() == absolute_ast.read_bytes()
(out / 'path-proof.json').write_text(json.dumps(dict(
    readable_non_executable=True, directories_skipped=True, empty_entries=True,
    executable_without_read_permission=True, lang_root=True,
    ast_sha256=hashlib.sha256(path_ast.read_bytes()).hexdigest()), indent=2)+'\n')
print('PASS path-compiler-lang-root-copied-value', flush=True)
if '--path-only' in sys.argv:
    print('PASS PATH compiler regression; evidence: ' + str(out), flush=True)
    sys.exit(0)

# Both named example readers really invoke stage_run, using their own frontend
# lowering; ordinary input syntax and the text worker protocol are unchanged.
source = out / 'input.tiny'; source.write_text('answer 42')
tiny = out / 'tiny.ast'
run('read-tiny', [compiler, 'read', 'example/tiny/stage.lang', source, '-o', tiny], extra={'LANGOS': 'wasm'})
helpers = list((out / 'calls').glob('*/program.ll'))
assert helpers and all('target triple = ' in p.read_text() and
                       'target triple = \"wasm32' not in p.read_text() for p in helpers)
run('compile-tiny', [compiler, '--from-ast', tiny, '-o', out / 'tiny.ll'])
run('link-tiny', ['clang', '-Wno-override-module', out / 'tiny.ll', '-o', out / 'tiny'])
run('execute-tiny', [out / 'tiny'], code=42)
compile_run('minilisp', '''include "std/core.lang"
include "example/minilisp/lisp_runtime.lang"
include "example/minilisp/minilisp.lang"
func main() i64 { return lisp_to_int(#minilisp{ (stage (+ 10 32)) }); }
''', 42)

prefix = 'include "test/stage_reader/macro.lang"\n'
echo = fragment('echo')
compile_run('echo', prefix + '#staged{' + str(echo) + '}\n', 42)
owned = fragment('owned')
compile_run('owned', prefix + '#owned{' + str(owned) + '}\n', 42)
crc = fragment('crc')
proc, ir = compile_run('crc', prefix + '#staged{' + str(crc) + '}\n')
expected = [zlib.crc32(bytes([n])) for n in range(256)]
assert list(map(int, proc.stdout.splitlines())) == expected
text = ir.read_text()
for i, n in enumerate(expected):
    assert re.search(r'@crc_' + str(i) + r'\s*=.*\bi64 ' + str(n) + r'\b', text), (i, n)
assert not re.search(r'define [^\n]*@stage_entry\(', text)
main = re.search(r'define [^\n]*@main\([^\n]*\).*?\n}', text, re.S).group()
assert 'br ' not in main and ' phi ' not in main
(out / 'crc-proof.json').write_text(json.dumps(dict(entries=256, zlib=True,
    constants=True, table_loop=False, compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),
    ir_sha256=hashlib.sha256(ir.read_bytes()).hexdigest()), indent=2)+'\n')
print('PASS crc-256-zlib-and-constant-ir', flush=True)

# No failed call can change a prior publication, and failed reader compilation
# must not emit an AST. Low time budget also covers compile/link, not just exec.
for name, extra, diagnostic in [
    ('loop', {'LANG_STAGE_MAX_MS': '2000'}, b'call-time-limit'),
    ('descendant', {'LANG_STAGE_MAX_MS': '2000'}, b'call-time-limit'),
    ('overrun', {'LANG_STAGE_MAX_BYTES': '4096'}, b'byte-limit'),
    ('echo', {'LANG_STAGE_MAX_MS': '1'}, b'call-time-limit'),
    ('crc', {'LANG_STAGE_MAX_BYTES': '32'}, b'call-byte-limit')]:
    ast = fragment(name)
    before = {p: p.read_bytes() for p in (out / 'calls').glob('stage-value-*')}
    source = out / ('fail-' + name + '.staged')
    source.write_text(str(ast))
    dest = out / ('fail-' + name + '.ast')
    proc = subprocess.run([str(compiler), 'read', 'test/stage_reader/macro.lang', str(source), '-o', str(dest)],
                          env=dict(env, **extra), capture_output=True, timeout=15)
    (out / ('fail-' + name + '.stderr')).write_bytes(proc.stderr)
    assert proc.returncode != 0 and diagnostic in proc.stderr, proc.stderr
    if name == 'loop':
        assert b'fragment-entered' in proc.stderr
    if name == 'descendant':
        pid = int(re.search(rb'descendant=(\d+)', proc.stderr).group(1))
        # A killed orphan can remain a zombie until the host's init reaps it.
        stat = Path('/proc') / str(pid) / 'stat'
        if stat.exists():
            assert stat.read_text().split()[2] == 'Z'
    assert not dest.exists() or dest.stat().st_size == 0
    assert (str(source) + ':bytes 0..' + str(len(source.read_bytes()))).encode() in proc.stderr, proc.stderr
    assert {p: p.read_bytes() for p in before} == before
    assert set((out / 'calls').glob('stage-value-*')) == set(before)
    print('PASS failure-' + name + '-' + diagnostic.decode(), flush=True)

# Ordinary lang macro diagnostics point at the invocation, including UTF-8
# and multiline content, rather than at the reader definition.
source = out / 'macro-failure.lang'
source.write_text('// λ\n' + prefix + '#staged{' + str(out / 'loop.ast') + '}\n')
call_start = source.read_bytes().index(b'#staged')
call_end = len(source.read_bytes()) - 1
before = set((out / 'calls').glob('stage-value-*'))
proc = subprocess.run([str(compiler), str(source), '-o', str(out / 'macro-failure.ll')],
                      env=dict(env, LANG_STAGE_MAX_MS='2000'), capture_output=True, timeout=15)
(out / 'macro-failure.stderr').write_bytes(proc.stderr)
assert proc.returncode != 0 and b'call-time-limit' in proc.stderr
assert (str(source) + ':bytes ' + str(call_start) + '..' + str(call_end)).encode() in proc.stderr
assert set((out / 'calls').glob('stage-value-*')) == before
print('PASS macro-invocation-span', flush=True)

# A successful call followed by failure in the same reader preserves the
# process's previous publication, as well as publications from other readers.
source = out / 'after.fail_after'; source.write_text(str(out / 'loop.ast'))
dest = out / 'after.ast'
before = {p: p.read_bytes() for p in (out / 'calls').glob('stage-value-*')}
proc = subprocess.run([str(compiler), 'read', 'test/stage_reader/macro.lang', str(source), '-o', str(dest)],
                      env=dict(env, LANG_STAGE_MAX_MS='2000'), capture_output=True, timeout=15)
(out / 'failure-after-success.stderr').write_bytes(proc.stderr)
assert proc.returncode != 0 and b'call-time-limit' in proc.stderr
assert not dest.exists()
assert {p: p.read_bytes() for p in before} == before
created = set((out / 'calls').glob('stage-value-*')) - set(before)
assert len(created) == 1
assert created.pop().read_bytes() == struct.pack('<IIq', 7, 8, 42)
print('PASS failure-preserves-same-reader-publication', flush=True)

# Inputs and outputs are distinct owned copies; two calls have fresh state.
# Existing reader programs exercise the legacy adapter without fixture edits.
compile_run('legacy-tiny', Path('example/tiny/test_tiny.lang').read_text(), 42)
compile_run('legacy-minilisp', Path('example/minilisp/test_minilisp.lang').read_text())
(out / 'results.json').write_text(json.dumps(rows, indent=2)+'\n')
print('PASS stage readers; evidence: ' + str(out), flush=True)
