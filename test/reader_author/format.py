#!/usr/bin/env python3
"""Verify only the shipping CST source layout recipe, retaining external receipts."""
import argparse
import os
from pathlib import Path
import re
import resource
import shutil
import sys
import uuid

from route import Replay, ROOT, dump, require, sha

BASE = '1b9c9751cb23c5ca0fd4fefc290833e5b7e47a6d'


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
    evidence = (args.evidence or ROOT.parent / 'evidence' / ('format-' + token)).resolve()
    require(evidence != ROOT and ROOT not in evidence.parents, 'evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=False)
    scratch = ROOT.parent / 'scratch' / ('format-' + token)
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
        files = replay.run(['git', 'ls-files', '-z'], 'inputs', clone).stdout.decode().split('\0')
        hashes = {p: sha(clone / p) for p in files if p and (clone / p).is_file()}
        tools = {}
        for name in ('bash', 'make', 'clang', 'ld', 'python3', 'git'):
            path = Path(shutil.which(name)).resolve()
            tools[name] = {'path': str(path), 'sha256': sha(path)}
        dump(evidence / 'identity.json', {'head': head, 'base': BASE,
             'source_sha256': hashes, 'tools': tools,
             'limits': {'cpus': cpus, 'address_space_bytes': ceiling, 'JOBS': 2, 'MAKEFLAGS': '-j2'},
             'assumptions': 'Linux x86-64 libc/Clang; trusted native readers; whitespace-only shipping recipe; '
                'four-space indentation, input field order and decimal spelling retained; '
                'no OS kernel operations, full suites, fixed points or bootstrap/web regeneration'})
        replay.run(['make', 'init'], 'init', clone)
        replay.run(['make', 'build'], 'build-current-sources', clone)
        compiler = str(clone / 'out/lang_next')
        project = clone / 'example/shipping/project.lang-project'
        shipping = clone / 'example/shipping/shipping.lang'
        policy = clone / 'example/shipping/policy.shipping'
        original = shipping.read_text()
        source = policy.read_bytes()
        core = lambda data: re.sub(rb'\(span\s+\d+\s+\d+\s+', b'(span ', data)

        def format_source(name, expected=0, manifest=project, extra=()):
            return replay.run([compiler, 'project', 'format', str(manifest), *map(str, extra)],
                              name, clone, expected=expected)

        def read_core(name):
            return replay.run([compiler, 'project', 'read', str(project)], name, clone)

        # Compare the actual shared semantic model, ignoring only source spans.
        cases = [
            ('canonical', source, source),
            ('compact', b'shipping{base 10;free_over 100;}', source),
            ('reordered', b' \tshipping { free_over 00080; base 00007; }\r\n',
             b'shipping {\n    free_over 00080;\n    base 00007;\n}\n'),
            ('limits', b'shipping {base 0;free_over 1000000;}',
             b'shipping {\n    base 0;\n    free_over 1000000;\n}\n'),
        ]
        models = {}
        for name, guest, expected in cases:
            policy.write_bytes(guest)
            before = read_core(name + '-model-before')
            require(before.stdout and not before.stderr, 'missing semantic model')
            result = format_source(name + '-format')
            exact(result, expected)
            require(policy.read_bytes() == guest, 'formatter changed its input')
            saved = scratch / (name + '.shipping')
            exact(format_source(name + '-save', extra=('-o', saved)))
            require(saved.read_bytes() == expected, '-o changed canonical bytes')
            policy.write_bytes(result.stdout)
            exact(format_source(name + '-idempotent'), result.stdout)
            after = read_core(name + '-model-after')
            require(core(before.stdout) == core(after.stdout), 'parse-format-parse changed semantic model')
            models[name] = core(before.stdout).decode()
            (evidence / (name + '.input.shipping')).write_bytes(guest)
            (evidence / (name + '.shipping')).write_bytes(result.stdout)
        require('(number 80)' in models['reordered'] and '(number 7)' in models['reordered'],
                'edited policy values were not preserved')
        dump(evidence / 'models.json', models)
        policy.write_bytes(source)

        def retain_reader(name):
            path = evidence / (name + '.lang')
            shutil.copyfile(shipping, path)
            dump(evidence / (name + '.sha256.json'), {path.name: sha(path)})

        # The host must preserve the author's explicit ending on both outputs.
        ending = 'layout_text(doc, "}"); layout_line(doc, 0);'
        require(original.count(ending) == 1, 'ambiguous layout ending mutation')
        for name, recipe, suffix in (
            ('no-final-newline', 'layout_text(doc, "}");', b''),
            ('trailing-space', 'layout_text(doc, "} \\t");', b' \t'),
            ('blank-final-line', ending + ' layout_line(doc, 0);', b'\n\n'),
        ):
            shipping.write_text(original.replace(ending, recipe))
            retain_reader(name + '-reader')
            expected = source[:-1] + suffix
            policy.write_bytes(source)
            result = format_source(name + '-format')
            exact(result, expected)
            require(policy.read_bytes() == source, 'formatter changed its input')
            saved = scratch / (name + '.shipping')
            saved.write_bytes(b'replace existing output')
            exact(format_source(name + '-save', extra=('-o', saved)))
            require(saved.read_bytes() == expected, '-o changed explicit layout ending')
            policy.write_bytes(result.stdout)
            exact(format_source(name + '-idempotent'), expected)
            after = read_core(name + '-model-after')
            require(core(after.stdout).decode() == models['canonical'] and not after.stderr,
                    'explicit layout ending changed semantic model')
            (evidence / (name + '.shipping')).write_bytes(result.stdout)
        shipping.write_text(original); policy.write_bytes(source)

        # No lowering inversion: a recipe still works when lowering cannot run.
        require(original.count('return ast_program(decls);') == 1, 'ambiguous lowering mutation')
        shipping.write_text(original.replace('return ast_program(decls);',
            'pnode_print_error(tree, text, "shipping", "deliberate lowering error"); return nil;'))
        retain_reader('lowering-error-reader')
        exact(format_source('independent-of-lowering'), source)
        result = replay.run([compiler, 'project', 'read', str(project)],
                            'prove-lowering-fails', clone, expected=1)
        require(not result.stdout and b'deliberate lowering error' in result.stderr, 'lowering mutation did not fail')
        shipping.write_text(original)

        # Grammar access is checked, rather than using positional children.
        shipping.write_text(original.replace('value:shipping_value', 'amount:shipping_value'))
        retain_reader('renamed-capture-reader')
        result = format_source('capture-contract', expected=1)
        require(not result.stdout and b"rule 'shipping_setting', capture 'value'" in result.stderr,
                'recipe bypassed capture contract')
        shipping.write_text(original)

        # No fallback from a reader AST to guest syntax.
        custom = scratch / 'custom'; custom.mkdir()
        (custom / 'project.lang-project').write_text(project.read_text().replace('shipping', 'same'))
        (custom / 'runtime.lang').write_text('')
        (custom / 'policy.same').write_text('ignored')
        (custom / 'same.lang').write_text('include "std/ast.lang"\n'
            'reader same(text *u8) *u8 { return ast_main_i64(ast_int(42)); }\n')
        shutil.copytree(custom, evidence / 'unsupported-reader-inputs')
        dump(evidence / 'unsupported-reader.sha256.json', {p.name: sha(p) for p in custom.iterdir()})
        result = format_source('unsupported-reader', expected=1, manifest=custom / 'project.lang-project')
        require(not result.stdout and b'unsupported format' in result.stderr, 'reader AST printed as guest syntax')

        # All failures must leave stdout empty and an existing destination intact.
        invalid = [(name, path.read_bytes(), message) for name, message in (
            ('duplicate', b'duplicate setting'), ('unknown', b'unknown setting'),
            ('missing', b'missing setting'), ('range', b'decimal integer'))
            for path in [clone / ('example/shipping/invalid/' + name + '.shipping')]]
        invalid += [
            ('syntax', b'shipping {base 10 free_over 100;}', b'expected'),
            ('trailing', b'shipping {base 10;free_over 100;} junk', b'end of input'),
            ('negative', b'shipping {base -1;free_over 100;}', b'decimal integer'),
            ('fraction', b'shipping {base 1.5;free_over 100;}', b'expected'),
            ('hex', b'shipping {base 0x10;free_over 100;}', b'expected'),
            ('overflow', b'shipping {base 99999999999999999999999;free_over 100;}', b'decimal integer'),
            ('empty', b'shipping {}', b'missing setting'),
            ('unclosed', source + b'/*', b'*/'),
            ('line-comment', b'// caf\xc3\xa9\n' + source, b'unsupported-trivia'),
            ('block-comment', b'shipping {base /* note */ 10;free_over 100;}', b'unsupported-trivia'),
            ('tail-comment', source + b'// tail', b'unsupported-trivia'),
        ]
        output = scratch / 'guard.shipping'
        for name, guest, message in invalid:
            policy.write_bytes(guest); output.write_bytes(b'keep existing output')
            result = format_source('reject-' + name, expected=1, extra=('-o', output))
            require(not result.stdout and message in result.stderr and re.search(rb'shipping:\d+:\d+:', result.stderr),
                    name + ': missing located error or unexpected output')
            require(output.read_bytes() == b'keep existing output', name + ': failure overwrote output')
            (evidence / (name + '.input.shipping')).write_bytes(guest)
        policy.write_bytes(source)

        # The trivia policy follows the tokenizer the reader actually supplied.
        shipping.write_text(original.replace('tok_new(text)', 'tok_new_comments(text, "#", nil, nil)'))
        policy.write_bytes(b'# configured by reader\n' + source)
        retain_reader('custom-trivia-reader')
        result = format_source('custom-trivia', expected=1)
        require(not result.stdout and b'unsupported-trivia' in result.stderr, 'custom trivia silently discarded')
        shipping.write_text(original); policy.write_bytes(source)

        # Inherited syntax requests cannot affect explicit project formatting or read.
        for inherited in ('tree', 'format'):
            replay.env['LANG_INSPECT_STAGE'] = inherited
            exact(format_source('ambient-' + inherited + '-format'), source)
            result = read_core('ambient-' + inherited + '-read')
            require(core(result.stdout).decode() == models['canonical'] and not result.stderr,
                    'ambient request changed normal reader output')
        replay.env.pop('LANG_INSPECT_STAGE', None)
        for name, arguments in [('missing', []), ('option', [str(project), '--unknown', 'x']),
                                ('output', [str(project), '-o'])]:
            result = replay.run([compiler, 'project', 'format', *arguments],
                                'invalid-option-' + name, clone, expected=1)
            require(not result.stdout and result.stderr, 'invalid command wrote source')
        result = replay.run([sys.executable, '-B', '-c',
            'import runpy; from subprocess import CompletedProcess; '
            'runpy.run_path("format.py")["exact"](CompletedProcess([], 0, b"wrong", b""))'],
            'expectation-must-fail', clone / 'test/reader_author', expected=1)
        require(b'unexpected exact stdout/stderr' in result.stderr, 'failed expectation was swallowed')
        require(all(sha(clone / p) == h for p, h in hashes.items()), 'tracked sources changed during fragment')
        dump(evidence / 'artifacts.json', {'compiler': sha(compiler)})
        dump(evidence / 'result.json', {'pass': True, 'head': head, 'observations': len(replay.rows)})
        print('PASS format: exact recipe bytes, CST recipe, setting order/values, semantic round trip, idempotence, trivia refusal, '
              'malformed input, unsupported reader, lowering independence and failure propagation')
        return 0
    except Exception as error:
        dump(evidence / 'result.json', {'pass': False, 'error': str(error)})
        print(f'FAIL: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
