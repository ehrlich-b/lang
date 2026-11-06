#!/usr/bin/env python3
"""Run only generated capture contracts and the shipping reader, with receipts."""
import argparse
import os
from pathlib import Path
import resource
import shutil
import sys
import uuid

from route import Replay, ROOT, dump, require, sha

BASE = 'ed73e20a974eccdba76e0cdb4ca9409260ffa37f'


def exact(result, stdout=b''):
    require(result.stdout == stdout and not result.stderr, 'unexpected exact stdout/stderr')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['contracts'], required=True)
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
    evidence = (args.evidence or ROOT.parent / 'evidence' / ('contracts-' + token)).resolve()
    require(evidence != ROOT and ROOT not in evidence.parents, 'evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=False)
    scratch = ROOT.parent / 'scratch' / ('contracts-' + token)
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
            'assumptions': 'Linux x86-64 libc and Clang; syntax-only schemas; fail-fast reader-author '
                'contracts; source-order alternative indexes; lexical rule boundaries; no OS kernel '
                'tests, full suites, fixed points, bootstrap changes or web regeneration'})
        replay.run(['make', 'init'], 'init', clone)
        compiler = str(clone / 'out/lang')
        fixture = clone / 'test/reader_author/fixtures/captures/contracts.lang'
        ir = scratch / 'contracts.ll'
        binary = scratch / 'contracts'
        replay.run([compiler, str(fixture), '-o', str(ir)], 'compile-contracts', clone)
        replay.run(['clang', str(ir), '-o', str(binary)], 'link-contracts', clone)
        exact(replay.run([str(binary)], 'contracts-happy', clone), b'PASS contracts\n')
        errors = [
            ('packet', 'note', 'accessor cardinality'),
            ('packet', 'renamed', 'not declared'),
            ('packet', 'first', 'tree cardinality'),
            ('packet', 'first', 'tree cardinality'),
            ('nonempty', 'items', 'tree cardinality'),
            ('chain', 'value', 'another rule'),
            ('packet', 'first', 'accessor cardinality'),
        ]
        for index, (rule, name, message) in enumerate(errors, 1):
            result = replay.run([str(binary)] + ['x'] * index, 'contract-negative-' + str(index), clone, expected=1)
            diagnostic = f"reader-author capture contract: rule '{rule}', capture '{name}': ".encode()
            require(not result.stdout and diagnostic in result.stderr and message.encode() in result.stderr,
                    'missing rule/capture/cardinality diagnostic')
        # Prove the same assertion used above cannot swallow a wrong expectation.
        result = replay.run([sys.executable, '-B', '-c',
            'from captures import exact; from subprocess import CompletedProcess; '
            'exact(CompletedProcess([], 0, b"wrong\\n", b""), b"PASS contracts\\n")'],
            'expectation-must-fail', clone / 'test/reader_author', expected=1)
        require(b'unexpected exact stdout/stderr' in result.stderr, 'failed expectation was swallowed')
        # Legacy, non-opt-in tree/accessor compatibility: only two tiny fixtures.
        for name in ('279_parser_named_capture', '281_parser_choice_branch'):
            legacy_ir = scratch / (name + '.ll')
            legacy = scratch / name
            replay.run([compiler, 'test/suite/' + name + '.lang', '-o', str(legacy_ir)], name + '-compile', clone)
            replay.run(['clang', str(legacy_ir), '-o', str(legacy)], name + '-link', clone)
            exact(replay.run([str(legacy)], name + '-run', clone))
        shipping = clone / 'example/shipping/shipping.lang'
        policy = clone / 'example/shipping/policy.shipping'
        result = replay.run([compiler, 'read', str(shipping), str(policy)], 'shipping-ast', clone)
        require(b'(binop >=' in result.stdout and b'(ident total)' in result.stdout and b'(number 100)' in result.stdout
                and not result.stderr, 'shipping AST changed')
        (evidence / 'shipping.ast').write_bytes(result.stdout)
        minted = scratch / 'shippingc'
        replay.run([compiler, 'compiler', 'shipping', str(shipping), '--runtime',
                    'example/shipping/runtime.lang', '-o', str(minted)], 'shipping-compiler', clone)
        shipping_ir = scratch / 'shipping.ll'
        replay.run([str(minted), str(policy), '-o', str(shipping_ir)], 'shipping-llvm', clone)
        native = scratch / 'shipping'
        replay.run(['clang', str(shipping_ir), '-o', str(native)], 'shipping-link', clone)
        for total, expected in [('99', b'10\n'), ('100', b'0\n'), ('101', b'0\n')]:
            exact(replay.run([str(native), total], 'shipping-runtime-' + total, clone), expected)
        result = replay.run([compiler, 'read', str(shipping), 'example/shipping/reordered.shipping'], 'shipping-reordered', clone)
        require(b'(binop >=' in result.stdout and not result.stderr, 'reordered shipping parser failed')
        for name, diagnostic in [('duplicate', b'duplicate setting'), ('missing', b'missing setting'),
                                 ('unknown', b'unknown setting'), ('range', b'decimal integer')]:
            result = replay.run([str(minted), 'example/shipping/invalid/' + name + '.shipping',
                                '-o', str(scratch / (name + '.ll'))], 'shipping-' + name, clone, expected=1)
            require(diagnostic in result.stderr and not result.stdout, 'shipping diagnostic regression')
        # Change only grammar declarations; lowering remains byte-for-byte intact.
        original = shipping.read_text()
        for name, replacement, message in [
            ('rename', 'amount:shipping_value', b'not declared'),
            ('optional', 'value:shipping_value?', b'accessor cardinality'),
            ('repeated', 'value:shipping_value+', b'accessor cardinality'),
        ]:
            edited = scratch / (name + '.lang')
            require(original.count('value:shipping_value') == 1, 'shipping mutation must be unique')
            edited.write_text(original.replace('value:shipping_value', replacement))
            shutil.copyfile(edited, evidence / edited.name)
            result = replay.run([compiler, 'read', str(edited), str(policy)], 'shipping-grammar-' + name, clone, expected=1)
            require(b"rule 'shipping_setting', capture 'value'" in result.stderr and
                    message in result.stderr and not result.stdout, 'grammar edit did not fail safely')
        require(all(sha(clone / p) == h for p, h in hashes.items()), 'tracked sources changed during fragment')
        dump(evidence / 'artifacts.json', {'compiler': sha(compiler), 'contracts': sha(binary),
                                          'shippingc': sha(minted), 'shipping': sha(native)})
        dump(evidence / 'result.json', {'pass': True, 'head': head, 'observations': len(replay.rows)})
        print('PASS contracts: schema, alternatives, required/optional/repeated, lexical scope, legacy PNode, shipping and grammar-edit diagnostics')
        return 0
    except Exception as error:
        dump(evidence / 'result.json', {'pass': False, 'error': str(error)})
        print(f'FAIL: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
