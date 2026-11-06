#!/usr/bin/env python3
"""Check two reader-local lexical profiles on bounded fixtures, with receipts."""
import argparse
import os
from pathlib import Path
import resource
import shutil
import sys
import uuid

from route import Replay, ROOT, dump, require, sha

BASE = '645c9dac9b124b7638126b7702a7862e111b9818'


def exact(result, stdout=b''):
    require(result.stdout == stdout and not result.stderr, 'unexpected exact stdout/stderr')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['two-readers'], required=True)
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
    evidence = (args.evidence or ROOT.parent / 'evidence' / ('lexer-profile-' + token)).resolve()
    require(evidence != ROOT and ROOT not in evidence.parents, 'evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=False)
    scratch = ROOT.parent / 'scratch' / ('lexer-profile-' + token)
    scratch.mkdir(parents=True)
    replay = Replay(evidence, scratch)
    replay.env.update(MAKEFLAGS='-j2', PYTHONDONTWRITEBYTECODE='1')
    replay.env.pop('LANG_ROOT', None)
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
        files = replay.run(['git', 'ls-files', '-z'], 'inputs', clone).stdout.decode().split('\0')
        hashes = {p: sha(clone / p) for p in files if p and (clone / p).is_file()}
        tools = {}
        for name in ('bash', 'make', 'clang', 'ld', 'python3', 'git'):
            path = Path(shutil.which(name)).resolve()
            tools[name] = {'path': str(path), 'sha256': sha(path)}
        dump(evidence / 'identity.json', {
            'head': head, 'base': BASE, 'source_sha256': hashes, 'tools': tools,
            'limits': {'cpus': cpus, 'address_space_bytes': ceiling, 'JOBS': 2, 'MAKEFLAGS': '-j2'},
            'assumptions': 'Linux x86-64 libc and Clang; unsigned decimal syntax, ASCII '
                'identifier starts and explicit continuation bytes; exact keyword text; '
                'comments are not nested; domain bounds remain reader-local; no OS kernel '
                'operations, full suites, fixed points, bootstrap edits or web regeneration'})
        replay.run(['make', 'init'], 'init', clone)
        compiler = str(clone / 'out/lang')
        fixtures = clone / 'test/reader_author/fixtures/lexer_profile'
        def build(source, name):
            ir = scratch / (name + '.ll')
            binary = scratch / name
            replay.run([compiler, str(source), '-o', str(ir)], 'compile-' + name, clone)
            replay.run(['clang', str(ir), '-o', str(binary)], 'link-' + name, clone)
            return binary

        binary = build(fixtures / 'two_readers.lang', 'two-readers')
        result = replay.run([str(binary)], 'equivalent-trees-and-defaults', clone)
        require(result.stdout == b'PASS two-readers\n' and b'order-total' in result.stderr,
                'profile/manual trees, checked captures, rewind or legacy tokens differ')
        # The same generated parser reads manual streams and both scanning policies.
        for name, extra in [('config.shipping', []), ('query.query', ['query'])]:
            source = (fixtures / name).read_text()
            result = replay.run([str(binary), source, *extra], 'tree-' + name, clone)
            require(not result.stdout and b'@' in result.stderr, 'missing complete tree and offsets')

        source = (fixtures / 'adjacent.query').read_text()
        result = replay.run([str(binary), source, 'query'], 'adjacent-identifier-comment', clone)
        require(not result.stdout and b'symbol "item" @7:11\n' in result.stderr
                and b'number "3" @27:28\n' in result.stderr,
                'adjacent line comment changed the field or original token ranges')

        bad_numbers = ['1.5', '.5', '1.', '1e3', '1E-3', '1e+3', '1e', '10base', '0x10', '1_000']
        for number in bad_numbers:
            for label, prefix, suffix, extra in [
                ('shipping', '// café\nshipping { base ', '; free_over 100; }', []),
                ('query', '-- café\nselect order-total limit ', ';', ['query']),
            ]:
                source = prefix + number + suffix
                path = scratch / (label + '-' + number.replace('.', 'dot') + '.txt')
                path.write_text(source)
                shutil.copyfile(path, evidence / path.name)
                result = replay.run([str(binary), source, *extra], label + '-number-' + number, clone, expected=1)
                start = len(prefix.encode())
                end = start + len(number.encode())
                require(not result.stdout and b'expected decimal integer, found ' + number.encode() in result.stderr
                        and f' @{start}:{end}\n'.encode() in result.stderr,
                        'bad numeric spelling was accepted or lost its complete UTF-8 byte range')

        for source, extra, token, expected in [
            ('shipping_extra { base 1; free_over 2; }', [], 'shipping_extra', "'shipping'"),
            ('select-all x limit 1;', ['query'], 'select-all', "'select'"),
            ('select2 x limit 1;', ['query'], 'select2', "'select'"),
            ('select x limit_more 1;', ['query'], 'limit_more', "'limit'"),
            ('select x limit 1; // foreign', ['query'], '/', 'end of input'),
            ('shipping { base 1; free_over 2; } -- foreign', [], '--', 'end of input'),
            ('select x limit 1; (* unfinished', ['query'], '(* unfinished', '*)'),
            ('shipping { base 1; free_over 2; } /* unfinished', [], '/* unfinished', '*/'),
        ]:
            result = replay.run([str(binary), source, *extra], 'boundary-' + str(len(replay.rows)), clone, expected=1)
            start = source.index(token)
            end = start + len(token)
            require(not result.stdout and expected.encode() in result.stderr
                    and f' @{start}:{end}\n'.encode() in result.stderr, 'boundary/comment diagnostic changed')

        # Preserve the exact prerequisite's bounded capture guarantees, including
        # its malformed/nil payload rejection paths; this is not a full suite.
        contracts = build(clone / 'test/reader_author/fixtures/captures/contracts.lang', 'contracts')
        exact(replay.run([str(contracts)], 'capture-contracts', clone), b'PASS contracts\n')
        for count in range(1, 19):
            result = replay.run([str(contracts)] + ['x'] * count,
                                'capture-negative-' + str(count), clone, expected=1)
            require(not result.stdout and b'reader-author capture contract:' in result.stderr,
                    'capture prerequisite no longer rejects invalid access')
        # Two small unchanged grammars retain their original scanner/tree behavior.
        for name in ('279_parser_named_capture', '281_parser_choice_branch'):
            legacy = build(clone / ('test/suite/' + name + '.lang'), name)
            exact(replay.run([str(legacy)], name, clone))
        result = replay.run([sys.executable, '-B', '-c',
            'from lexer_profile import exact; from subprocess import CompletedProcess; '
            'exact(CompletedProcess([], 0, b"wrong\\n", b""), b"PASS two-readers\\n")'],
            'expectation-must-fail', clone / 'test/reader_author', expected=1)
        require(b'unexpected exact stdout/stderr' in result.stderr, 'failed expectation was swallowed')

        shipping = clone / 'example/shipping/shipping.lang'
        policy = clone / 'example/shipping/policy.shipping'
        result = replay.run([compiler, 'read', str(shipping), str(policy)], 'shipping-ast', clone)
        require(b'(binop >=' in result.stdout and b'(ident total)' in result.stdout and b'(number 100)' in result.stdout
                and not result.stderr, 'shipping AST changed')
        (evidence / 'shipping.ast').write_bytes(result.stdout)
        query = fixtures / 'query.lang'
        result = replay.run([compiler, 'read', str(query), str(fixtures / 'query.query')], 'query-ast', clone)
        require(b'(number 003)' in result.stdout and not result.stderr, 'query reader changed source or lowering')
        (evidence / 'query.ast').write_bytes(result.stdout)
        minted = scratch / 'shippingc'
        replay.run([compiler, 'compiler', 'shipping', str(shipping), '--runtime',
                    'example/shipping/runtime.lang', '-o', str(minted)], 'shipping-compiler', clone)
        shipping_ir = scratch / 'shipping.ll'
        replay.run([str(minted), str(policy), '-o', str(shipping_ir)], 'shipping-llvm', clone)
        native = scratch / 'shipping'
        replay.run(['clang', str(shipping_ir), '-o', str(native)], 'shipping-link', clone)
        for total, expected in [('99', b'10\n'), ('100', b'0\n'), ('101', b'0\n')]:
            exact(replay.run([str(native), total], 'shipping-runtime-' + total, clone), expected)
        # Check the shipping artifact itself, not only the tokenizer fixture.
        for index, number in enumerate(bad_numbers):
            prefix = '// café\nshipping { base '
            source = prefix + number + '; free_over 100; }'
            path = scratch / ('invalid-' + str(index) + '.shipping')
            path.write_text(source)
            shutil.copyfile(path, evidence / path.name)
            result = replay.run([str(minted), str(path), '-o', str(scratch / ('bad-' + str(index) + '.ll'))],
                                'minted-invalid-' + str(index), clone, expected=1)
            start = len(prefix.encode())
            require(not result.stdout and b'expected decimal integer' in result.stderr and
                    f' @{start}:{start + len(number)}\n'.encode() in result.stderr, 'shipping accepted invalid numeric text')
        for name, diagnostic in [('duplicate', b'duplicate setting'), ('missing', b'missing setting'),
                                 ('unknown', b'unknown setting'), ('range', b'decimal integer')]:
            result = replay.run([str(minted), 'example/shipping/invalid/' + name + '.shipping',
                                '-o', str(scratch / (name + '.ll'))], 'shipping-' + name, clone, expected=1)
            require(diagnostic in result.stderr and not result.stdout, 'shipping semantic diagnostic regression')
        require(all(sha(clone / p) == h for p, h in hashes.items()), 'tracked sources changed during fragment')
        dump(evidence / 'artifacts.json', {'compiler': sha(compiler), 'two-readers': sha(binary),
                                          'shippingc': sha(minted), 'shipping': sha(native)})
        dump(evidence / 'result.json', {'pass': True, 'head': head, 'observations': len(replay.rows)})
        print('PASS two-readers: profiles, exact ranges, manual streams, capture contracts, defaults and minted shipping')
        return 0
    except Exception as error:
        dump(evidence / 'result.json', {'pass': False, 'error': str(error)})
        print(f'FAIL: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
