#!/usr/bin/env python3
"""Replay only the Rill compiler-module fragment, with external evidence."""
import argparse
import os
from pathlib import Path
import re
import resource
import shutil
import sys
import uuid

from route import Replay, ROOT, dump, require, sha

BASE = 'cadab6056d97a0fc759c15efd338e9e9a26b9bcc'


def exact(result, stdout=b''):
    require(result.stdout == stdout and not result.stderr, 'unexpected exact stdout/stderr')


def core(text):
    """Parse the interchange independently; ignore only origin wrappers."""
    tokens = iter(re.findall(rb'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text))

    def node(first):
        if first != b'(':
            require(first != b')', 'unexpected close in AST')
            return first
        items = []
        for token in tokens:
            if token == b')':
                if items and items[0] == b'span':
                    require(len(items) == 4, 'malformed span')
                    return items[3]
                return items
            items.append(node(token))
        raise RuntimeError('unclosed AST')

    result = node(next(tokens))
    require(next(tokens, None) is None, 'trailing AST')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['compiler-module'], required=True)
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
    evidence = (args.evidence or ROOT.parent / 'evidence' / ('rill-' + token)).resolve()
    require(evidence != ROOT and ROOT not in evidence.parents, 'evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=False)
    scratch = ROOT.parent / 'scratch' / ('rill-' + token)
    scratch.mkdir(parents=True)
    replay = Replay(evidence, scratch)
    replay.env.update(MAKEFLAGS='-j2', PYTHONDONTWRITEBYTECODE='1')
    for key in ('LANG_ROOT', 'LANG_INSPECT_STAGE', 'VERIFY_CASE'):
        replay.env.pop(key, None)
    print(f'evidence: {evidence}', flush=True)
    try:
        status = replay.run(['git', 'status', '--porcelain', '--untracked-files=all'], 'clean', ROOT)
        require(not status.stdout, 'commit the candidate before replaying it')
        head = replay.run(['git', 'rev-parse', 'HEAD'], 'head', ROOT).stdout.decode().strip()
        replay.run(['git', 'merge-base', '--is-ancestor', BASE, head], 'required-base', ROOT)
        replay.run(['git', 'diff', '--exit-code', BASE, head, '--', 'bootstrap', 'web'],
                   'protected-inputs', ROOT)
        clone = scratch / 'repo'
        replay.run(['git', 'clone', '--no-hardlinks', '--quiet', str(ROOT), str(clone)], 'clone', ROOT)
        paths = replay.run(['git', 'ls-files', '-z'], 'inputs', clone).stdout.decode().split('\0')
        hashes = {p: sha(clone / p) for p in paths if p and (clone / p).is_file()}
        tools = {}
        for name in ('bash', 'make', 'clang', 'ld', 'python3', 'git'):
            path = Path(shutil.which(name)).resolve()
            tools[name] = {'path': str(path), 'sha256': sha(path)}
        dump(evidence / 'identity.json', {'head': head, 'base': BASE,
             'source_sha256': hashes, 'tools': tools,
             'limits': {'cpus': cpus, 'address_space_bytes': ceiling, 'JOBS': 2, 'MAKEFLAGS': '-j2'},
             'assumptions': 'Linux x86-64, LLVM/libc and Clang; trusted native reader; '
                 'use includes Lang support modules using existing host resolution; '
                 'parser origins are points where no range is supplied; '
                 'no OS kernel operations, whole-compiler self-hosting, full suites, fixed points, '
                 'bootstrap promotion or web generation'})
        replay.run(['make', 'init'], 'init', clone)
        replay.run(['make', 'build'], 'build-current-sources', clone)
        compiler = str(clone / 'out/lang_next')
        reader = 'example/rill/rill.lang'
        module = 'example/rill/compiler-module.rill'
        minted = scratch / 'rillc'
        replay.run([compiler, 'compiler', 'rill', reader, '-o', str(minted)], 'mint-rill-compiler', clone)
        artifacts = [Path(compiler), minted]
        # No external compiler tool may be used while the minted frontend runs.
        replay.env['PATH'] = '/nonexistent'
        ir = scratch / 'compiler-module.ll'
        exact(replay.run([str(minted), module, '-o', str(ir)], 'compile-module', clone),
              f'Wrote {ir}\n'.encode())
        replay.env['PATH'] = os.environ['PATH']
        native = scratch / 'compiler-module'
        replay.run(['clang', str(ir), '-o', str(native)], 'link-module', clone)
        artifacts.extend((ir, native))
        for index, (value, output, exit_code) in enumerate([
            ('0', b'0\n', 0), ('00042', b'42\n', 0), ('127', b'127\n', 0),
            ('9223372036854775807', b'9223372036854775807\n', 0),
            ('9223372036854775808', b'18\n', 65),
            ('9999999999999999999999999999999999', b'18\n', 65),
            ('', b'0\n', 65), ('-1', b'0\n', 65), ('4x', b'1\n', 65),
            ('1.5', b'1\n', 65), ('42 ', b'2\n', 65), ('é', b'0\n', 65),
        ]):
            exact(replay.run([str(native), value], f'decimal-{index}', clone, expected=exit_code), output)

        ast = replay.run([compiler, 'read', reader, module], 'module-shared-ast', clone)
        require(not ast.stderr and b'(span ' in ast.stdout, 'missing origin-bearing AST')
        for form in (b'func parse_decimal', b'struct Decimal', b'reader decimal', b'type_ptr', b'include '):
            require(form in ast.stdout, 'missing compiler module form: ' + repr(form))
        (evidence / 'compiler-module.ast').write_bytes(ast.stdout)
        shutil.copyfile(ir, evidence / ir.name)
        rill_ast = replay.run([compiler, 'read', reader,
            'test/reader_author/fixtures/rill/preservation.rill'], 'preservation-ast', clone)
        require(not rill_ast.stderr, 'AST diagnostic')
        source = (clone / 'test/reader_author/fixtures/rill/preservation.rill').read_bytes()
        start = source.index(b'fun marker')
        require(re.search(fr'\(span\s+{start}\s+{start}\s+\(func marker'.encode(), rill_ast.stdout),
                'declaration origin shifted after UTF-8 comment')
        (evidence / 'preservation.ast').write_bytes(rill_ast.stdout)
        probe_ir = scratch / 'preservation.ll'
        probe = scratch / 'preservation'
        replay.run([compiler, 'test/reader_author/fixtures/rill/preservation.lang',
                    '-o', str(probe_ir)], 'compile-preservation-probe', clone)
        replay.run(['clang', str(probe_ir), '-o', str(probe)], 'link-preservation-probe', clone)
        observed = replay.run([str(probe)], 'token-byte-origin-preservation', clone)
        marker = b'PASS token slices, literal/comment bytes, source snapshot, positions and emitter isolation\n'
        require(not observed.stderr and observed.stdout.startswith(marker), 'preservation probe failed')
        equivalent = observed.stdout[len(marker):]
        require(core(rill_ast.stdout) == core(equivalent), 'Rill and Lang shared AST differ')
        (evidence / 'equivalent.ast').write_bytes(equivalent)
        artifacts.extend((probe_ir, probe))

        negative = replay.run([str(minted), 'example/rill/invalid.rill',
                              '-o', str(scratch / 'invalid.ll')], 'negative-module', clone, expected=1)
        require(not negative.stdout and b'rill:4:5: error:' in negative.stderr,
                'missing located parser diagnostic')
        backend = replay.run([str(minted), 'test/reader_author/fixtures/rill/backend-error.rill',
                              '-o', str(scratch / 'backend-error.ll')], 'backend-origin', clone, expected=1)
        require(not backend.stdout and b'backend-error.rill:3:12:' in backend.stderr,
                'backend lost original guest source origin')
        for name, text, diagnostic in (
            ('old-function', 'func main() i64 { return 0; }', b'unsupported Rill token'),
            ('old-local', 'fun main() i64 { var x i64 = 0; return x; }', b'unsupported Rill token'),
            ('embedded-lang', '#lang{ func main() i64 { return 0; } }', b'unsupported Rill token'),
            ('trailing', 'fun main() i64 { return 0; } junk', b'expected declaration'),
            ('comment', 'fun main() i64 { return 0; } /*', b'*/'),
            ('string', 'fun main() *u8 { return "unclosed; }', b'unterminated string'),
            ('effect', 'effect hidden() i64', b'unsupported Rill token'),
        ):
            fixture = scratch / (name + '.rill')
            fixture.write_text(text)
            shutil.copyfile(fixture, evidence / fixture.name)
            result = replay.run([str(minted), str(fixture), '-o', str(scratch / (name + '.ll'))],
                                name, clone, expected=1)
            require(not result.stdout and diagnostic in result.stderr, name + ': wrong diagnostic')
        result = replay.run([sys.executable, '-B', '-c',
            'import runpy; from subprocess import CompletedProcess; '
            'runpy.run_path("rill.py")["exact"](CompletedProcess([], 0, b"wrong", b""))'],
            'expectation-must-fail', clone / 'test/reader_author', expected=1)
        require(b'unexpected exact stdout/stderr' in result.stderr, 'failed expectation swallowed')
        require(all(sha(clone / p) == h for p, h in hashes.items()), 'tracked source changed')
        dump(evidence / 'artifacts.json', {str(p.relative_to(scratch)): sha(p) for p in artifacts})
        dump(evidence / 'result.json', {'pass': True, 'head': head, 'observations': len(replay.rows)})
        print('PASS Rill compiler module: minted compiler, decimal reader helper, shared AST, '
              'token/literal/comment preservation, origins and failing expectations')
        return 0
    except Exception as error:
        dump(evidence / 'result.json', {'pass': False, 'error': str(error)})
        print(f'FAIL: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
