#!/usr/bin/env python3
"""Q0 conformance: two reader clients, frozen facts, and hostile W frames."""
import argparse
import copy
import importlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'test/tooling'))
from wire import encode

parser = argparse.ArgumentParser()
parser.add_argument('--acceptance', choices=['A1', 'A2', 'A3', 'all'], default='all')
args = parser.parse_args()
os.chdir(ROOT)
out = Path(os.environ.get('TOOLING_EVIDENCE', tempfile.mkdtemp(prefix='tooling-contract-'))).resolve()
out.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, LANGBE='llvm', LANG_CACHE=str(out / 'cache'))
compiler = str(Path(os.environ.get('COMPILER', 'out/lang')).resolve())
results = []


def run(name, command, data=b'', expected=None, error=None, code=0):
    proc = subprocess.run(command, input=data, capture_output=True, env=env, timeout=180)
    (out / (name + '.stdout')).write_bytes(proc.stdout)
    (out / (name + '.stderr')).write_bytes(proc.stderr)
    (out / (name + '.exit')).write_text(str(proc.returncode) + '\n')
    if error:
        ok = proc.returncode == 1 and proc.stdout == b'' and b'host-error' in proc.stderr and error.encode() in proc.stderr
    else:
        ok = proc.returncode == code and (expected is None or proc.stdout == expected)
    results.append({'name': name, 'pass': ok, 'exit': proc.returncode})
    print(('PASS ' if ok else 'FAIL ') + name, flush=True)
    if not ok:
        raise AssertionError(f'{name}: exit={proc.returncode} stdout={proc.stdout[:300]!r} stderr={proc.stderr[:2000]!r}')
    return proc.stdout


try:
    ir = out / 'probe.ll'
    probe = out / 'probe'
    run('build-probe', [compiler, 'test/tooling/probe.lang', '-o', str(ir)])
    run('link-probe', ['clang', '-O2', str(ir), '-o', str(probe)])
    if args.acceptance in ['A3', 'all']:
        run('cli-capabilities', [compiler, 'tooling', 'capabilities'], expected=b'compile,limited-tooling\n')
        for query in ['Q1', 'Q2', 'Q3', 'Q4']:
            run('cli-' + query, [compiler, 'tooling', query], error='tooling-unimplemented')
        run('cli-rename', [compiler, 'tooling', 'rename'], error='tooling-unmapped-rename')
    for client in ['lang', 'minilisp']:
        fixture = Path(f'test/tooling/{client}.lang')
        source = fixture.read_bytes()
        ast = out / (client + '.ast')
        run(client + '-read', [compiler, str(fixture), '--emit-expanded-ast', '-o', str(ast)])
        syntax = ast.read_bytes()
        assert b'(lambda ' in syntax and b'(reader_expr ' in syntax, syntax[-2000:]
        e = importlib.import_module(client + '_client').read(source, syntax)
        facts = {k: v for k, v in e.items() if k != 'syntax'}
        frozen = json.loads(Path(f'test/tooling/{client}.json').read_text())
        assert facts == frozen, f'{client}: frozen envelope changed'
        (out / (client + '-facts.json')).write_text(json.dumps(facts, indent=2) + '\n')
        frame, offsets = encode(e)
        (out / (client + '.wire')).write_bytes(frame)

        def invoke(name, data=frame, mode='program', expected=b'validated-before-analysis\n', error=None):
            return run(client + '-' + name, [str(probe), mode, str(fixture), str(e['start']), str(e['end'])],
                       data.hex().encode(), expected=expected, error=error)

        if args.acceptance in ['A1', 'all']:
            guest = out / (client + ('.q0lang' if client == 'lang' else '.q0lisp'))
            guest.write_bytes(source[e['start']:e['end']])
            guest_ast = out / (client + '-guest.ast')
            reader = 'test/tooling/lang_reader.lang' if client == 'lang' else 'test/tooling/minilisp_reader.lang'
            run(client + '-reader-client', [compiler, 'read', reader, str(guest), '--compact', '-o', str(guest_ast)])
            assert b'(let x ' in guest_ast.read_bytes()
            invoke('roundtrip', mode='roundtrip', expected=frame)
            invoke('handoff')
            invoke('capabilities', mode='capabilities', expected=b'compile,Q0\n')
            # The actual compiler runs the same fixture with the reader and closure.
            program_ir = out / (client + '.ll')
            program = out / (client + '-program')
            run(client + '-compile', [compiler, str(fixture), '-o', str(program_ir)])
            run(client + '-link', ['clang', '-O0', str(program_ir), '-o', str(program)])
            run(client + '-execute', [str(program)], code=42)
        if args.acceptance in ['A2', 'all']:
            def mutate(name, field, value, error):
                changed = bytearray(frame)
                struct.pack_into('<I', changed, offsets[field], value)
                invoke(name, bytes(changed), error=error)

            for name, field, value, error in [
                ('unknown-source', 'sources.0.id', 999999, 'tooling-source'),
                ('split-codepoint', 'sites.0.start', source.index('é'.encode()) + 1, 'tooling-span'),
                ('out-of-range', 'sites.0.end', len(source) + 1, 'tooling-span'),
                ('reversed-span', 'sites.0.start', len(source), 'tooling-span'),
                ('dangling-binding', 'sites.0.binding', 9999, 'tooling-binding'),
                ('conflicting-scopes', 'bindings.4.scope', 4, 'tooling-conflicting-scope'),
                ('cycle', 'scopes.2.parent', 3, 'tooling-scope'),
                ('unknown-scope', 'sites.0.scope', 99, 'tooling-scope'),
                ('duplicate-scope-id', 'scopes.1.id', 1, 'tooling-scope'),
                ('duplicate-source-id', 'sources.1.id', 1, 'tooling-stale-source'),
                ('invisible-binding', 'sites.5.binding', 4, 'tooling-visibility'),
                ('unknown-site-source', 'sites.0.source', 999, 'tooling-span'),
                ('forged-origin', 'sites.0.origin', 999, 'tooling-origin'),
                ('wrong-origin-source', 'sites.0.origin', 3, 'tooling-site-origin'),
                ('bad-role', 'sites.0.role', 0, 'tooling-role'),
                ('huge-count', 'sources.count', 4294967295, 'tooling-wire-length'),
                ('unknown-version', 'version', 2, 'tooling-version'),
                ('invalid-mapped', 'mapped', 2, 'tooling-version'),
                ('unmapped-metadata', 'mapped', 0, 'tooling-unmapped'),
            ]:
                mutate(name, field, value, error)
            mutate('cross-phase-reference', 'sites.7.scope', 2, 'tooling-phase')
            changed = bytearray(frame)
            changed[offsets['sources.0.digest']] ^= 1
            invoke('wrong-digest', bytes(changed), error='tooling-stale-source')
            invoke('stale-snapshot', mode='stale', error='tooling-stale-source')
            invoke('truncated', frame[:-1], error='tooling-wire-length')
            invoke('trailing', frame + b'x', error='tooling-wire-length')
            changed = bytearray(frame)
            struct.pack_into('<I', changed, 8, 2)
            invoke('ungranted-origin', bytes(changed), error='tooling-origin')
            for position, error in [(0, 'tooling-wire-version'), (12, 'tooling-wire-version'),
                                    (offsets['bindings.0.name'], 'embedded-nul')]:
                changed = bytearray(frame)
                changed[position] = 0
                invoke('byte-' + str(position), bytes(changed), error=error)
            changed = bytearray(frame)
            changed[offsets['bindings.0.name']] = 255
            invoke('invalid-name-utf8', bytes(changed), error='invalid-utf8')
            changed = bytearray(frame[:-2])
            struct.pack_into('<I', changed, 4, len(changed) - 16)
            invoke('internal-truncation', bytes(changed), error='tooling-wire-length')
            changed = bytearray(frame + b'x')
            struct.pack_into('<I', changed, 4, len(changed) - 16)
            invoke('internal-trailing', bytes(changed), error='tooling-wire-length')
            # A valid neighbor still passes after all mutations.
            invoke('valid-control')
        if args.acceptance in ['A3', 'all']:
            for query in ['Q1', 'Q2', 'Q3', 'Q4']:
                invoke(query, mode=query, error='tooling-unimplemented')
            invoke('old-W-rejects-extension', mode='old-W', error='wire-version')
            legacy = copy.deepcopy(e)
            legacy.update(mapped=0, scopes=[], bindings=[], sites=[])
            legacy_frame, _ = encode(legacy)
            invoke('legacy-capabilities', legacy_frame, mode='capabilities', expected=b'compile,limited-tooling\n')
            invoke('legacy-handoff', legacy_frame)
            invoke('legacy-cannot-rename', legacy_frame, mode='Q4', error='tooling-unmapped-rename')
            legacy_ir = out / (client + '-legacy.ll')
            # Existing, unmodified reader declarations continue through the old ABI.
            run(client + '-legacy-compile', [compiler, str(fixture), '-o', str(legacy_ir)])
finally:
    (out / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
print(f'{len(results)} tooling checks passed; evidence: {out}')
