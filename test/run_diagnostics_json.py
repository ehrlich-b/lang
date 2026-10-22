#!/usr/bin/env python3
"""Exercise the versioned compiler transport and a byte-based fixture repair."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / 'test/diagnostics'
COMPILER = Path(os.environ.get('COMPILER', ROOT / 'out/lang_next')).resolve()
FIELDS = {'version', 'code', 'severity', 'path', 'span', 'message', 'truncated'}
parser = argparse.ArgumentParser()
parser.add_argument('--case', choices=['A1', 'A2', 'A3', 'A4', 'all'], default='all')
args = parser.parse_args()
base = Path(os.environ.get('DIAGNOSTICS_EVIDENCE_DIR') or tempfile.mkdtemp(prefix='diagnostics-'))
base.mkdir(parents=True, exist_ok=True)
work = Path(tempfile.mkdtemp(prefix=args.case + '-', dir=base)).resolve()
counter = 0


def invoke(source=None, flags=(), env=None, json_mode=True, success=False):
    global counter
    counter += 1
    command = [str(COMPILER), *(['--diagnostics=json'] if json_mode else []), *flags]
    if source is not None:
        command += [str(source), '-o', str(work / f'output-{counter}.ll')]
    run_env = dict(os.environ, LANGBE='llvm', LANG_CACHE=str(work / 'cache'))
    run_env.update(env or {})
    result = subprocess.run(command, capture_output=True, timeout=30, env=run_env)
    prefix = work / str(counter)
    prefix.with_suffix('.command.json').write_text(json.dumps(command))
    prefix.with_suffix('.stdout').write_bytes(result.stdout)
    prefix.with_suffix('.stderr').write_bytes(result.stderr)
    prefix.with_suffix('.exit').write_text(str(result.returncode))
    assert (result.returncode == 0) == success, (command, result)
    if not json_mode:
        return result
    records = [json.loads(line) for line in result.stderr.decode('utf-8', errors='strict').splitlines()]
    assert success or records, result
    for d in records:
        assert set(d) == FIELDS, d
        assert d['version'] == 1 and d['severity'] == 'error' and not d['truncated'], d
        assert isinstance(d['code'], str) and isinstance(d['message'], str), d
        if d['span'] is not None:
            assert set(d['span']) == {'start', 'end'} and 0 <= d['span']['start'] <= d['span']['end'], d
    return result, records


def fixture(name, dest=None):
    path = work / (dest or name)
    path.write_bytes((FIXTURES / name).read_bytes())
    return path


def located(records, code, source, token):
    matches = [d for d in records if d['code'] == code and d['path'] == str(source)]
    assert matches, records
    span = matches[0]['span']
    assert source.read_bytes()[span['start']:span['end']] == token, matches[0]
    return matches[0]


def a1():
    source = fixture('syntax.lang')
    _, records = invoke(source)
    d = located(records, 'syntax-error', source, b'}')
    assert d['span']['start'] == source.read_bytes().index(b'}')
    human = invoke(source, json_mode=False)
    assert human.stderr.splitlines()[0] == (f"{source}:2:28: error: expected ';' after return".encode())
    assert b'{"version"' not in human.stderr
    print('A1 PASS: version, stable fields, byte span, unchanged human message')


def a2():
    source = fixture('syntax.lang')
    located(invoke(source)[1], 'syntax-error', source, b'}')
    source = fixture('trailing.lang')
    located(invoke(source)[1], 'trailing-input', source, b'stray')
    # Invalid scalars, continuations, truncated sequences, and invalid bytes in
    # otherwise ignored comments/strings must all remain valid UTF-8 JSON.
    for index, bad in enumerate([b'\xff', b'\x80', b'\xc0\xaf', b'\xe2\x82', b'\xed\xa0\x80',
                                 b'\xf4\x90\x80\x80', b'\xe2A', b'\xf5\x80\x80\x80']):
        source = work / f'invalid-{index}.lang'
        prefix = b'// comment: '
        source.write_bytes(prefix + bad + b'\nfunc main() i64 { return 0; }\n')
        d = located(invoke(source)[1], 'invalid-utf8', source, bad[:1])
        assert d['span'] == {'start': len(prefix), 'end': len(prefix) + 1}
    source.write_bytes(b'func main() i64 { return 0; }\n\0invisible')
    located(invoke(source)[1], 'embedded-nul', source, b'\0')
    source = fixture('unsupported.lang')
    _, records = invoke(source, env={'LANGOS': 'wasm'})
    d = located(records, 'unsupported-feature', source, b'perform')
    assert 'not supported on the wasm target' in d['message']
    _, records = invoke(source, env={'LANGBE': 'wasm'})
    assert any(d['code'] == 'unsupported-feature' and d['path'] == str(source)
               and d['span'] is not None for d in records), records
    print('A2 PASS: syntax, trailing input, invalid UTF-8/NUL, LLVM/Wasm unsupported effects')


def a3():
    spec = importlib.util.spec_from_file_location('repair_diagnostic', ROOT / 'scripts/repair_diagnostic.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Delimiters and Unicode in paths must survive both source wrapping and JSON.
    source = fixture('syntax.lang', 'λ-"},"severity":"injected"-\\\n.lang')
    _, records = invoke(source)
    d = located(records, 'syntax-error', source, b'}')
    assert '\n' in d['message'] and 'λ-' in d['message']
    result = module.repair(COMPILER, source, work / 'repaired.ll')
    (work / 'repair.json').write_text(json.dumps(result, indent=2))
    assert source.read_bytes() == (FIXTURES / 'syntax.lang').read_bytes().replace(b'}', b'; }')
    assert (work / 'repaired.ll').stat().st_size > 0
    # An invalid OS filename byte must also be safely escaped.
    bad_path = work / os.fsdecode(b'bad-\xff.lang')
    bad_path.write_bytes(b'\xff')
    _, records = invoke(bad_path)
    assert records[0]['code'] == 'invalid-utf8' and 'bad-ÿ.lang' in records[0]['path']
    print('A3 PASS: exact byte repair/recompile, hostile paths/messages, Unicode, invalid filename bytes')


def a4():
    for flags, code in [(['--unknown'], 'invalid-option'),
                        (['--diagnostics=xml'], 'invalid-option'),
                        (['--diagnostics'], 'invalid-option'),
                        (['--from-ast'], 'unsupported-mode'),
                        (['--dump-tokens'], 'unsupported-mode'),
                        (['--expand-macros'], 'unsupported-mode')]:
        result, records = invoke(flags=flags)
        assert records[0]['code'] == code and not result.stdout
    for flag in ['--unknown', '--diagnostics=xml']:
        result = invoke(flags=[flag], json_mode=False)
        assert b'Error:' in result.stderr and not result.stdout
    # Selection is independent of flag order.
    result = subprocess.run([str(COMPILER), '--unknown', '--diagnostics=json'], capture_output=True)
    assert result.returncode and json.loads(result.stderr)['code'] == 'invalid-option'
    for command in ['run', 'compiler', 'read', 'new']:
        result = subprocess.run([str(COMPILER), command, 'fixture', '--diagnostics=json'], capture_output=True)
        assert result.returncode and json.loads(result.stderr)['code'] == 'unsupported-mode', result
    source = fixture('success.lang')
    result, records = invoke(source, success=True)
    assert result.stdout.startswith(b'Wrote ') and not records
    # An output filename is data and cannot silently select JSON mode.
    result = subprocess.run([str(COMPILER), str(fixture('syntax.lang')), '-o', '--diagnostics=json'],
                            capture_output=True, env=dict(os.environ, LANGBE='llvm'))
    assert result.returncode and not result.stderr.startswith(b'{"version"')
    # Frontend output remains a separate artifact too.
    result, records = invoke(source, flags=['--emit-expanded-ast'], success=True)
    assert result.stdout.startswith(b'Wrote expanded AST') and not records
    # Standard stderr must still work when a program is compiled by the direct
    # Wasm backend, which does not support function-typed locals or globals.
    source = fixture('stderr.lang')
    invoke(source, env={'LANGBE': 'wasm'}, success=True)
    ran = subprocess.run(['node', str(ROOT / 'test/wasm_host.js'),
                          str(work / f'output-{counter}.ll')],
                         capture_output=True, timeout=30)
    (work / 'direct-stderr.stdout').write_bytes(ran.stdout)
    (work / 'direct-stderr.stderr').write_bytes(ran.stderr)
    (work / 'direct-stderr.exit').write_text(str(ran.returncode))
    assert ran.returncode == 0 and not ran.stdout and ran.stderr == b'hello\n', ran
    print('A4 PASS: flags/modes rejected, option values respected, success/artifacts separate, direct Wasm stderr')


for name, test in [('A1', a1), ('A2', a2), ('A3', a3), ('A4', a4)]:
    if args.case in [name, 'all']:
        test()
print('Evidence:', work)
