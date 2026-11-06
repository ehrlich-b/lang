#!/usr/bin/env python3
"""Prove minted native emission from committed sources, outside the checkout."""
import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import sys
import uuid

from native_build import NativeReplay
from route import ROOT, dump, require, sha

BASE = '74c0af702c6065170621a53487834b2336d522b7'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['native'], required=True)
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    os.nice(10)
    cpus = sorted(os.sched_getaffinity(0))[:2]
    os.sched_setaffinity(0, cpus)
    ceiling = 2 * 1024**3
    hard = resource.getrlimit(resource.RLIMIT_AS)[1]
    if hard != resource.RLIM_INFINITY:
        ceiling = min(ceiling, hard)
    resource.setrlimit(resource.RLIMIT_AS, (ceiling, ceiling))
    token = uuid.uuid4().hex
    evidence = (args.evidence or ROOT.parent / 'evidence' / ('standalone-' + token)).resolve()
    require(evidence != ROOT and ROOT not in evidence.parents, 'evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=False)
    scratch = ROOT.parent / 'scratch' / ('standalone-' + token)
    scratch.mkdir(parents=True)
    replay = NativeReplay(evidence, scratch)
    replay.env.update(MAKEFLAGS='-j2', PYTHONDONTWRITEBYTECODE='1')
    replay.env.pop('VERIFY_CASE', None)
    replay.env.pop('LANG_CLANG', None)
    print(f'evidence: {evidence}', flush=True)
    try:
        status = replay.run(['git', 'status', '--porcelain', '--untracked-files=all'], 'clean', ROOT)
        require(not status.stdout, 'commit the candidate before replaying it')
        head = replay.run(['git', 'rev-parse', 'HEAD'], 'head', ROOT).stdout.decode().strip()
        replay.run(['git', 'merge-base', '--is-ancestor', BASE, head], 'required-base', ROOT)
        replay.run(['git', 'diff', '--exit-code', '0149c1d', head, '--', 'bootstrap/current', 'web'],
                   'protected-inputs-unchanged', ROOT)
        # Check that the adapter uses the host contract, with no second linker.
        standalone = (ROOT / 'src/standalone.lang').read_text()
        project = (ROOT / 'src/native_build.lang').read_text()
        for adapter in (standalone, project):
            require('include "src/native_host.lang"' in adapter and 'native_build_link(' in adapter
                    and 'native_build_emit_valid(' in adapter and 'os_execve(' not in adapter
                    and 'native_build_tool(' not in adapter, 'host contract was duplicated')
        clone = scratch / 'repo'
        replay.run(['git', 'clone', '--no-hardlinks', '--quiet', str(ROOT), str(clone)], 'clone', ROOT)
        files = replay.run(['git', 'ls-files', '-z'], 'inputs', clone).stdout.decode().split('\0')
        hashes = {p: sha(clone / p) for p in files if p and (clone / p).is_file()}
        tools = {}
        for name in ('make', 'clang', 'ld', 'python3', 'git'):
            found = shutil.which(name)
            require(found is not None, name + ' is required')
            path = Path(found).resolve()
            tools[name] = {'path': str(path), 'sha256': sha(path)}
        dump(evidence / 'identity.json', {
            'head': head, 'base': BASE, 'source_sha256': hashes, 'tools': tools,
            'limits': {'cpus': cpus, 'address_space_bytes': ceiling, 'JOBS': 2, 'MAKEFLAGS': '-j2'},
            'assumptions': 'Linux x86-64 libc; trusted native reader; embedded runtime; '
                           'native -O0 with explicit LANG_CLANG or PATH lookup; '
                           'no OS kernel tests, fixed points or browser rebuilds'})
        replay.run(['make', 'init'], 'init', clone)
        replay.run(['make', 'build'], 'build-current-sources', clone)
        compiler = str(clone / 'out/lang_next')
        shipping = clone / 'example/shipping'
        isolated = scratch / 'isolated with spaces'
        isolated.mkdir()
        shipc = isolated / 'shipc'
        source = isolated / 'valid.ship'
        shutil.copyfile(shipping / 'policy.shipping', source)
        # Mint exactly once; subsequent commands use only the binary and guest.
        replay.run([compiler, 'compiler', 'shipping', str(shipping / 'shipping.lang'),
                    '--runtime', str(shipping / 'runtime.lang'), '-o', str(shipc)], 'mint-shipc-once', clone)
        dump(evidence / 'isolation.json', {'cwd': str(isolated),
             'files': {p.name: sha(p) for p in isolated.iterdir()},
             'compiler': sha(shipc), 'runtime_embedded': True})
        exe = isolated / 'shipping'

        def invoke(name, extra=(), guest='valid.ship', output=exe, expected=0):
            operand = output.name if output.parent == isolated else str(output)
            result = replay.run([str(shipc), guest, *extra, '-o', operand], name, isolated, expected)
            require(not list(isolated.glob('*.lang-build-*')), name + ': staging directory leaked')
            if expected:
                require(not output.exists(), name + ': stale or partial executable survived')
                require(b'Built ' not in result.stdout, name + ': failure announced success')
            return result

        result = invoke('native-valid', ['--emit=native'])
        require(b'optimization=-O0' in result.stderr and exe.read_bytes().startswith(b'\x7fELF'),
                'native output or explicit optimization missing')
        saved = exe.read_bytes()

        def seed():
            exe.write_bytes(saved)
            exe.chmod(0o755)

        path = replay.env['PATH']
        replay.env['PATH'] = '/nonexistent'
        for total, expected in [('0', b'10\n'), ('99', b'10\n'), ('100', b'0\n'), ('120', b'0\n')]:
            result = replay.run([str(exe), total], 'runtime-' + total, isolated)
            require(result.stdout == expected and not result.stderr, 'runtime branch mismatch')
        legacy = isolated / 'legacy.ll'
        explicit = isolated / 'explicit.ll'
        invoke('legacy-llvm-no-clang', output=legacy)
        invoke('explicit-llvm-no-clang', ['--emit=llvm'], output=explicit)
        reference = json.loads((clone / 'test/reader_author/fixtures/standalone/legacy.json').read_text())
        require(legacy.read_bytes() == explicit.read_bytes(), 'explicit LLVM differs from default bytes')
        require(sha(legacy) == reference['llvm_sha256'], 'LLVM bytes differ from preserved base')
        shutil.copyfile(legacy, evidence / 'legacy.ll')
        seed()
        result = invoke('missing-path-clang', ['--emit=native'], expected=127)
        require(b'valid.ship: error: native build toolchain failed' in result.stderr and
                b'clang not found in PATH' in result.stderr, 'missing toolchain lost guest or phase')
        replay.env['PATH'] = path
        replay.env['LANG_CLANG'] = str(isolated / 'missing configured tool')
        seed()
        result = invoke('missing-configured-clang', ['--emit=native'], expected=127)
        require(b'valid.ship: error: native build toolchain failed' in result.stderr and
                b'could not execute:' in result.stderr, 'tool launch failure lost guest or phase')
        replay.env.pop('LANG_CLANG')
        for backend, target in [('x86', 'linux'), ('wasm', 'linux'), ('llvm', 'wasm')]:
            replay.env.update(LANGBE=backend, LANGOS=target)
            seed()
            result = invoke('unsupported-' + backend + '-' + target, ['--emit=native'], expected=1)
            require(b'valid.ship: error: native build backend selection failed' in result.stderr and
                    b'requires LANGBE=llvm LANGOS=linux' in result.stderr, 'backend failure lost guest or phase')
        replay.env.update(LANGBE='llvm', LANGOS='linux')
        bad = isolated / 'invalid.ship'
        shutil.copyfile(shipping / 'invalid/duplicate.shipping', bad)
        seed()
        result = invoke('reader-failure', ['--emit=native'], guest='invalid.ship', expected=1)
        require(b'duplicate setting' in result.stderr and b'invalid.ship' in result.stderr,
                'reader failure lost diagnostic or guest')
        for name, arguments in [('duplicate-emit', ['--emit=llvm', '--emit=native']),
                                ('duplicate-output', ['--emit=native', '-o', str(exe)]),
                                ('unknown-option', ['--emit=native', '--unknown'])]:
            seed()
            invoke(name, arguments, expected=1)
        sentinel = isolated / 'unselected-output'
        sentinel.write_bytes(saved)
        sentinel.chmod(0o755)
        replay.run([str(shipc), 'valid.ship', '--emit=native', '-o', '-o', str(sentinel)],
                   'missing-first-output', isolated, expected=1)
        require(sentinel.read_bytes() == saved, 'ambiguous second destination was invalidated')
        link = isolated / 'output-symlink'
        link.symlink_to(sentinel)
        replay.run([str(shipc), 'valid.ship', '--emit=native', '-o', str(link)],
                   'protect-output-symlink', isolated, expected=1)
        require(link.is_symlink() and sentinel.read_bytes() == saved, 'symlink target changed')
        original = sha(source)
        replay.run([str(shipc), 'valid.ship', '--emit=native', '-o', 'valid.ship'],
                   'protect-guest', isolated, expected=1)
        require(sha(source) == original, 'guest input overwritten')
        unrelated = isolated / 'unrelated.txt'
        unrelated.write_text('keep this\n')
        replay.run([str(shipc), 'valid.ship', '--emit=native', '-o', str(unrelated)],
                   'protect-unrelated', isolated, expected=1)
        require(unrelated.read_text() == 'keep this\n', 'unrelated file overwritten')
        # One configured tool exercises both object and linker boundaries.
        proxy = isolated / 'configured clang with spaces'
        shutil.copyfile(clone / 'test/reader_author/fixtures/native_build/clang_proxy.py', proxy)
        proxy.chmod(0o755)
        log = evidence / 'tool-argv.jsonl'
        replay.env.update(LANG_CLANG=str(proxy), NATIVE_TOOL_LOG=str(log),
                          NATIVE_REAL_CLANG=tools['clang']['path'],
                          NATIVE_BAD_IR=str(clone / 'test/reader_author/fixtures/native_build/malformed.ll'))
        seed()
        result = invoke('object-failure', ['--emit=native'], expected=1)
        require(b'valid.ship: error: native build optimizer/object compilation failed' in result.stderr and
                b'expected top-level entity' in result.stderr, 'object failure lost original diagnostic')
        replay.env.pop('NATIVE_BAD_IR')
        replay.env['NATIVE_BAD_IR'] = str(clone / 'test/reader_author/fixtures/standalone/unresolved.ll')
        seed()
        result = invoke('linker-failure', ['--emit=native'], expected=1)
        require(b'valid.ship: error: native build linker failed' in result.stderr and
                b'standalone_missing_link_symbol' in result.stderr, 'link failure lost original diagnostic')
        replay.env.pop('NATIVE_BAD_IR')
        invoke('configured-tool-valid', ['--emit=native'])
        calls = [json.loads(line) for line in log.read_text().splitlines()]
        require(any(args[:2] == ['-O0', '-c'] for args in calls) and
                any(args[0].endswith('/guest.o') and args[1] == '-o' for args in calls),
                'tool argv lost separate object/link phases')
        replay.env.pop('LANG_CLANG')
        # The project adapter still uses the extracted implementation and embeds runtime.
        project_exe = scratch / 'project-shipping'
        replay.run([compiler, 'build', '--project', str(shipping / 'project.lang-project'),
                    str(shipping / 'policy.shipping'), '-o', str(project_exe)], 'shared-project-build', scratch)
        result = replay.run([str(project_exe), '99'], 'shared-project-runtime', scratch)
        require(result.stdout == b'10\n' and not result.stderr, 'shared project driver changed runtime')
        require(all(sha(clone / p) == h for p, h in hashes.items()), 'test edited committed inputs')
        dump(evidence / 'artifacts.json', {'shipc': sha(shipc), 'native': sha(exe),
             'project_native': sha(project_exe), 'llvm': sha(legacy), 'baseline_llvm': reference['llvm_sha256']})
        dump(evidence / 'result.json', {'pass': True, 'head': head, 'observations': len(replay.rows)})
        print('PASS standalone native: one mint, isolated runtime branches, LLVM byte equality, shared host, phase/guest failures and output protection')
        return 0
    except Exception as error:
        dump(evidence / 'result.json', {'pass': False, 'error': str(error)})
        print(f'FAIL: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
