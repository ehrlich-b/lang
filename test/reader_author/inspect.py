#!/usr/bin/env python3
"""Exercise project inspection through the actual shipping reader, with receipts."""
import argparse
import os
from pathlib import Path
import re
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
    parser.add_argument('--case', choices=['shipping'], required=True)
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
    evidence = (args.evidence or ROOT.parent / 'evidence' / ('inspect-' + token)).resolve()
    require(evidence != ROOT and ROOT not in evidence.parents, 'evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=False)
    scratch = ROOT.parent / 'scratch' / ('inspect-' + token)
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
        replay.run(['git', 'diff', '--exit-code', BASE, head, '--',
                    'bootstrap', 'web', 'std/capture_contract.lang', 'std/capture_gen.lang'],
                   'protected-inputs', ROOT)
        clone = scratch / 'repo'
        replay.run(['git', 'clone', '--no-hardlinks', '--quiet', str(ROOT), str(clone)], 'clone', ROOT)
        files = replay.run(['git', 'ls-files', '-z'], 'inputs', clone).stdout.decode().split('\0')
        hashes = {p: sha(clone / p) for p in files if p and (clone / p).is_file()}
        tools = {}
        for name in ('bash', 'make', 'clang', 'ld', 'python3', 'git'):
            path = Path(shutil.which(name)).resolve()
            tools[name] = {'path': str(path), 'sha256': sha(path)}
        dump(evidence / 'identity.json', {'head': head, 'base': BASE,
             'source_sha256': hashes, 'tools': tools,
             'limits': {'cpus': cpus, 'address_space_bytes': ceiling, 'JOBS': 2, 'MAKEFLAGS': '-j2'},
             'assumptions': 'Linux x86-64 libc/Clang; one explicit complete-input grammar boundary; '
                'core is reader AST with runtime calls, LLVM links project runtime; trusted native readers; '
                'no OS kernel operations, full suites, fixed points or bootstrap/web regeneration'})
        replay.run(['make', 'init'], 'init', clone)
        replay.run(['make', 'build'], 'build-current-sources', clone)
        compiler = str(clone / 'out/lang_next')
        project = clone / 'example/shipping/project.lang-project'
        shipping = clone / 'example/shipping/shipping.lang'
        policy = clone / 'example/shipping/policy.shipping'

        def inspect(manifest, stage, name, expected=0, extra=()):
            return replay.run([compiler, 'inspect', '--project', str(manifest), '--stage', stage,
                               *map(str, extra)], name, clone, expected=expected)

        help_output = replay.run([compiler, 'inspect', '--help'], 'inspect-help', clone)
        require(b'--project' in help_output.stdout and not help_output.stderr, 'inspect help missing')
        exact(replay.run([compiler, 'help', 'inspect'], 'help-inspect', clone), help_output.stdout)
        snapshots = {}
        for stage in ('tokens', 'tree', 'core', 'llvm'):
            result = inspect(project, stage, 'shipping-' + stage)
            require(result.stdout and not result.stderr, stage + ': missing artifact or diagnostic on success')
            require(b'LANG-INSPECT/' not in result.stdout and not result.stdout.startswith(b'Wrote '),
                    stage + ': transport or status contaminated artifact')
            snapshots[stage] = result.stdout
            (evidence / ('shipping.' + stage)).write_bytes(result.stdout)
            output = scratch / ('saved.' + stage)
            exact(inspect(project, stage, 'save-' + stage, extra=('-o', output)))
            require(output.read_bytes() == result.stdout, stage + ': -o changed artifact')
        source = policy.read_bytes()
        tokens = snapshots['tokens']
        require(len(tokens.splitlines()) == 9, 'wrong shipping token count')
        for value in (b'base', b'10', b'free_over', b'100'):
            start = source.index(value)
            span = f'@{start}:{start + len(value)}'.encode()
            require(b'"' + value + b'" ' + span in tokens, 'token value/span lost')
            require(b'"' + value + b'" ' + span in snapshots['tree'], 'tree value/span lost')
        require(b'capture "name"' in snapshots['tree'] and b'capture "value"' in snapshots['tree']
                and b'capture "settings"' in snapshots['tree'], 'named keys lost')
        core = snapshots['core']
        require(core.startswith(b'(program\n') and b'(func shipping_fee' in core
                and b'(ident shipping_total)' in core and b'(ident shipping_print)' in core
                and b'(binop >= (ident total) (number 100))' in core,
                'core lost function, policy or runtime boundary')
        require(b'define i64 @shipping_fee(' in snapshots['llvm']
                and b'define i64 @shipping_print(' in snapshots['llvm'], 'LLVM lost policy or linked runtime')
        legacy = replay.run([compiler, 'read', str(shipping), str(policy)], 'reader-core-oracle', clone)
        exact(legacy, core)
        # An inherited syntax request must neither replace an AST request nor
        # override the explicit CLI stage, including on a cold reader cache.
        normal_cache = replay.env['LANG_CACHE']
        try:
            for inherited in ('tree', 'tokens'):
                replay.env['LANG_INSPECT_STAGE'] = inherited
                replay.env['LANG_CACHE'] = str(scratch / ('ambient-' + inherited))
                exact(replay.run([compiler, 'read', str(shipping), str(policy)],
                                 'ambient-' + inherited + '-read-cold', clone), core)
                exact(replay.run([compiler, 'read', str(shipping), str(policy)],
                                 'ambient-' + inherited + '-read-warm', clone), core)
                for stage in ('tokens', 'tree', 'core', 'llvm'):
                    exact(inspect(project, stage, 'ambient-' + inherited + '-' + stage),
                          snapshots[stage])
        finally:
            replay.env.pop('LANG_INSPECT_STAGE', None)
            replay.env['LANG_CACHE'] = normal_cache
        # Independently dump the real reader's tree after its existing end check.
        oracle = scratch / 'oracle.lang'
        original = shipping.read_text()
        anchor = '    var settings *u8 = capture_shipping_policy_repeated(tree, "settings");'
        require(original.count(anchor) == 1, 'oracle insertion is ambiguous')
        oracle.write_text(original.replace(anchor, '    pnode_dump(tree);\n' + anchor))
        shutil.copyfile(oracle, evidence / oracle.name)
        observed = replay.run([compiler, 'read', str(oracle), str(policy)], 'reader-tree-oracle', clone)
        require(observed.stdout == core and observed.stderr == snapshots['tree'],
                'tree does not match existing dump in actual reader')
        llvm = scratch / 'shipping.ll'; llvm.write_bytes(snapshots['llvm'])
        native = scratch / 'shipping'
        replay.run(['clang', str(llvm), '-o', str(native)], 'link-inspected-llvm', clone)
        for total, expected in [('99', b'10\n'), ('100', b'0\n'), ('101', b'0\n')]:
            exact(replay.run([str(native), total], 'runtime-' + total, clone), expected)

        def variant(name, reader=original, guest=None):
            dest = scratch / name
            shutil.copytree(clone / 'example/shipping', dest)
            (dest / 'shipping.lang').write_text(reader)
            if guest is not None:
                (dest / 'policy.shipping').write_text(guest)
            retained = evidence / name; retained.mkdir()
            for filename in ('shipping.lang', 'policy.shipping', 'runtime.lang', 'project.lang-project'):
                shutil.copyfile(dest / filename, retained / filename)
            dump(retained / 'sha256.json', {p.name: sha(p) for p in retained.iterdir() if p.is_file()})
            return dest / 'project.lang-project'

        # Stop before a deliberate reader-lowering failure, not a substitute parser.
        failed = variant('lowering-error', original.replace('return ast_program(decls);',
            'pnode_print_error(tree, text, "shipping", "deliberate lowering error"); return nil;'))
        exact(inspect(failed, 'tree', 'lowering-error-tree'), snapshots['tree'])
        result = inspect(failed, 'core', 'lowering-error-core', expected=1)
        require(not result.stdout and b'deliberate lowering error' in result.stderr, 'core swallowed lowering error')
        result = inspect(failed, 'llvm', 'lowering-error-llvm', expected=1)
        require(not result.stdout and b'deliberate lowering error' in result.stderr, 'LLVM swallowed lowering error')
        # A same-path input edit must change values and preserve UTF-8 byte offsets.
        edited = variant('edited', guest='// café\nshipping { free_over 80; base 7; }\n')
        changed = inspect(edited, 'tree', 'edited-tree').stdout
        edited_source = (edited.parent / 'policy.shipping').read_bytes()
        for value in (b'80', b'7'):
            start = edited_source.index(value)
            require(b'"' + value + f'" @{start}:{start + len(value)}'.encode() in changed,
                    'edited tree ignored input bytes')
        result = inspect(edited, 'core', 'edited-core')
        require(b'(number 80)' in result.stdout and b'(number 7)' in result.stdout and not result.stderr,
                'edited policy did not lower')
        configured = variant('custom-comments', original.replace('tok_new(text)',
            'tok_new_comments(text, "#", nil, nil)'), '# configured by reader\nshipping { base 10; free_over 100; }')
        result = inspect(configured, 'tokens', 'actual-tokenizer')
        require(b'"#"' not in result.stdout and b'"shipping" @23:31' in result.stdout and not result.stderr,
                'inspection substituted a default scanner')
        exact(inspect(configured, 'core', 'custom-comments-core'),
              replay.run([compiler, 'read', str(configured.parent / 'shipping.lang'),
                          str(configured.parent / 'policy.shipping')], 'custom-comments-oracle', clone).stdout)
        # Inherited checked capture accessors still reject a grammar-only rename.
        renamed = variant('capture-rename', original.replace('value:shipping_value', 'amount:shipping_value'))
        require(b'capture "amount"' in inspect(renamed, 'tree', 'renamed-tree').stdout, 'stale generated grammar')
        result = inspect(renamed, 'core', 'renamed-core', expected=1)
        require(not result.stdout and b"rule 'shipping_setting', capture 'value'" in result.stderr
                and b'not declared' in result.stderr, 'capture contract regressed')
        custom = clone / 'test/reader_author/fixtures/project/alpha/project.lang-project'
        for stage in ('tokens', 'tree'):
            result = inspect(custom, stage, 'unsupported-' + stage, expected=1)
            require(not result.stdout and b'unsupported ' + stage.encode() + b' stage' in result.stderr,
                    'unsupported stage was substituted')
        result = inspect(custom, 'core', 'custom-core')
        require(b'(number 42)' in result.stdout and not result.stderr, 'custom reader core unavailable')
        for name, guest in [('syntax', 'shipping { base 10 free_over 100; }'),
                            ('trailing', 'shipping { base 10; free_over 100; } junk'),
                            ('comment', 'shipping { base 10; free_over 100; } /*')]:
            invalid = variant(name, guest=guest)
            result = inspect(invalid, 'tree', name + '-tree', expected=1)
            require(not result.stdout and b'error:' in result.stderr, 'bad input produced a success artifact')
            if name == 'comment':
                result = inspect(invalid, 'tokens', 'unterminated-comment-tokens', expected=1)
                require(not result.stdout and b'*/' in result.stderr, 'scanner error swallowed')
        missing = variant('missing-inspect-rule', original.replace('!inspect shipping_policy;', '!inspect absent;'))
        result = inspect(missing, 'tree', 'missing-inspect-rule', expected=1)
        require(not result.stdout and b'declared inspection rule' in result.stderr, 'bad inspection metadata accepted')
        for name, arguments in [('missing', []), ('unknown', ['--project', str(project), '--stage', 'bogus']),
                                ('duplicate', ['--project', str(project), '--stage', 'tree', '--stage', 'core'])]:
            result = replay.run([compiler, 'inspect', *arguments], 'option-' + name, clone, expected=1)
            require(not result.stdout and result.stderr, 'invalid CLI wrote stdout')
        result = replay.run([sys.executable, '-B', '-c',
            'import runpy; from subprocess import CompletedProcess; '
            'runpy.run_path("inspect.py")["exact"](CompletedProcess([], 0, b"wrong", b""))'],
            'expectation-must-fail', clone / 'test/reader_author', expected=1)
        require(b'unexpected exact stdout/stderr' in result.stderr, 'failed expectation was swallowed')
        require(all(sha(clone / p) == h for p, h in hashes.items()), 'tracked source changed during fragment')
        dump(evidence / 'artifacts.json', {p.name: sha(p) for p in (Path(compiler), llvm, native)})
        dump(evidence / 'result.json', {'pass': True, 'head': head, 'observations': len(replay.rows)})
        print('PASS inspect: actual tokenizer/tree, core/runtime, LLVM, lowering failure, capture contract and stdout isolation')
        return 0
    except Exception as error:
        dump(evidence / 'result.json', {'pass': False, 'error': str(error)})
        print(f'FAIL: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
