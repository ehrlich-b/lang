#!/usr/bin/env python3
"""Replay only the committed Rill compiler-source closure fragment."""
import argparse
import io
import json
import lzma
import os
from pathlib import Path
import re
import resource
import shutil
import sys
import tarfile
import uuid

from route import Replay, ROOT, dump, require, sha
from rill import core

BASE = '3037f44e6332a7404152a459fba1c52ed1b7dbe8'
WORDS = {b'func': b'fun', b'var': b'local', b'struct': b'record',
         b'include': b'use', b'reader': b'syntax', b'require': b'needs'}
PROTECTED = re.compile(rb'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', re.S)


def expect_output(result, value):
    require(result.stdout == value and not result.stderr, 'unexpected exact stdout/stderr')


def tree(path):
    return {p.relative_to(path).as_posix(): sha(p) for p in sorted(path.rglob('*')) if p.is_file()}


def validate(pack, source):
    """Independently verify complete byte coverage and every permitted edit."""
    manifest = json.loads((pack / 'manifest.json').read_text())
    modules = {row['source']: row for row in manifest['modules']}
    changes = 0
    for name, row in modules.items():
        original = (source / name).read_bytes()
        exported = (pack / row['export']).read_bytes()
        require(sha(source / name) == row['source_sha256'], 'source hash mismatch: ' + name)
        require(sha(pack / row['export']) == row['export_sha256'], 'export hash mismatch: ' + name)
        protected = list(PROTECTED.finditer(original))
        old_end = new_end = 0
        for a, b, c, d, kind in row['spans']:
            require(a == old_end and c == new_end and a < b and c <= d, 'span gap/overlap: ' + name)
            old, new = original[a:b], exported[c:d]
            if kind == 'copy':
                require(old == new, 'copy changed bytes: ' + name)
            else:
                require(all(b <= m.start() or a >= m.end() for m in protected),
                        'literal/comment edit: ' + name)
                if kind == 'keyword':
                    require(old in WORDS and new == WORDS[old], 'invalid keyword edit')
                else:
                    require(kind == 'identifier' and new == b'rill__' + old and
                            (old in WORDS.values() or old.startswith(b'rill__')), 'invalid identifier escape')
                changes += 1
            old_end, new_end = b, d
        require(old_end == len(original) and new_end == len(exported), 'incomplete source map')
        for dep in row['dependencies']:
            require(dep['source'] in modules, 'missing dependency: ' + dep['source'])
    for label, closure in manifest['closures'].items():
        require(sha(pack / closure['export']) == closure['export_sha256'], 'bundle hash mismatch')
        seen, expected = set(), []

        def visit(name):
            if name in seen:
                return
            seen.add(name)
            for dep in modules[name]['dependencies']:
                visit(dep['source'])
            expected.append(name)

        for name in closure['roots']:
            visit(name)
        require(closure['order'] == expected, 'incomplete/noncanonical closure order: ' + label)
        bundle = (pack / closure['export']).read_bytes()
        offset = 0
        for row in closure['modules']:
            original = (source / row['source']).read_bytes()
            module = modules[row['source']]
            require(row['export_start'] == offset, 'bundle gap')
            section = bundle[offset:row['export_end']]
            omitted = {t for dep in module['dependencies'] for t in dep['tokens']}
            old_end = new_end = 0
            for a, b, c, d, kind in row['spans']:
                require(a == old_end and c == new_end and a < b, 'bundle span gap')
                old, new = original[a:b], section[c:d]
                if kind == 'dependency':
                    require(a in omitted and not new, 'non-dependency omitted')
                elif kind == 'copy':
                    require(old == new, 'bundle copy mismatch')
                elif kind == 'keyword':
                    require(new == WORDS.get(old), 'bundle keyword mismatch')
                else:
                    require(kind == 'identifier' and new == b'rill__' + old, 'bundle identifier mismatch')
                old_end, new_end = b, d
            require(old_end == len(original) and new_end == len(section), 'bundle map incomplete')
            require(bundle[row['export_end']:row['export_end'] + 1] == b'\n', 'missing separator')
            offset = row['export_end'] + 1
        require(offset == len(bundle), 'trailing bundle bytes')
    return manifest, changes


def archive(path, files):
    # Stable metadata, safe relative member names, no copied build trees/binaries.
    with lzma.open(path, 'wb', preset=6) as compressed:
        with tarfile.open(fileobj=compressed, mode='w') as tar:
            for name, source in sorted(files.items()):
                data = source.read_bytes()
                info = tarfile.TarInfo(name)
                info.size, info.mode = len(data), 0o644
                tar.addfile(info, io.BytesIO(data))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['compiler-closure'], required=True)
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
    sys.setrecursionlimit(10000)
    token = uuid.uuid4().hex
    evidence = (args.evidence or ROOT.parent / 'evidence' / ('rill-export-' + token)).resolve()
    require(evidence != ROOT and ROOT not in evidence.parents, 'evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=False)
    scratch = ROOT.parent / 'scratch' / ('rill-export-' + token)
    scratch.mkdir(parents=True)
    replay = Replay(evidence, scratch)
    replay.env.update(JOBS='2', MAKEFLAGS='-j2', PYTHONDONTWRITEBYTECODE='1')
    for key in ('LANG_ROOT', 'LANG_INSPECT_STAGE', 'VERIFY_CASE'):
        replay.env.pop(key, None)
    print(f'evidence: {evidence}', flush=True)
    try:
        clean = replay.run(['git', 'status', '--porcelain', '--untracked-files=all'], 'clean', ROOT)
        require(not clean.stdout, 'commit the candidate before replaying it')
        head = replay.run(['git', 'rev-parse', 'HEAD'], 'head', ROOT).stdout.decode().strip()
        replay.run(['git', 'merge-base', '--is-ancestor', BASE, head], 'required-base', ROOT)
        replay.run(['git', 'diff', '--exit-code', BASE, head, '--', 'bootstrap', 'web'], 'protected-inputs', ROOT)
        clone = scratch / 'repo'
        replay.run(['git', 'clone', '--quiet', '--no-hardlinks', str(ROOT), str(clone)], 'clone', ROOT)
        tracked = replay.run(['git', 'ls-files', '-z'], 'inputs', clone).stdout.decode().split('\0')
        hashes = {p: sha(clone / p) for p in tracked if p and (clone / p).is_file()}
        tools = {}
        for name in ('bash', 'make', 'clang', 'ld', 'python3', 'git'):
            path = Path(shutil.which(name)).resolve()
            tools[name] = {'path': str(path), 'sha256': sha(path)}
        dump(evidence / 'identity.json', {'head': head, 'base': BASE, 'source_sha256': hashes,
             'tools': tools, 'limits': {'cpus': cpus, 'address_space_bytes': ceiling, 'JOBS': 2,
                                       'MAKEFLAGS': '-j2'},
             'assumptions': 'Linux x86-64 LLVM/libc; trusted native reader; generated OS/version '
                 'inputs come from make build; includes/requires identify repository-root paths; '
                 'dependency bundles deduplicate modules in depth-first source order; '
                 'no OS kernel operations, full suites, fixed points, bootstrap promotion or web generation'})
        replay.run(['make', 'init'], 'init', clone)
        replay.run(['make', 'build'], 'build-current-sources', clone)
        compiler = str(clone / 'out/lang_next')
        exporter = str(clone / 'scripts/rill_export.py')
        spec = json.loads((clone / 'example/rill/compiler-closure.json').read_text())
        build = (clone / 'Makefile').read_text().split('\nbuild:\n', 1)[1].split('\n# ===', 1)[0]
        command = next(line for line in build.splitlines() if '$(LANG) std/core.lang' in line)
        roots = command.split('$(LANG) ', 1)[1].split(' -o ', 1)[0].replace('$(COMPILER_READERS)', 'src/compiler_readers_none.lang').split()
        require(roots == spec['closures']['compiler'], 'compiler source specification drifted from make build')
        first, second = scratch / 'export-1', scratch / 'export-2'
        for index, output in enumerate((first, second), 1):
            replay.run([sys.executable, '-B', exporter, '--output', str(output)], f'export-{index}', clone)
        require(tree(first) == tree(second), 'unchanged exports differ')
        manifest, changes = validate(first, clone)
        require(changes > 1000, 'compiler keywords were not exported')
        oracle_ir, oracle = scratch / 'oracle.ll', scratch / 'oracle'
        replay.run([compiler, 'test/reader_author/fixtures/rill/export-oracle.lang', '-o', str(oracle_ir)], 'compile-oracle', clone)
        replay.run(['clang', str(oracle_ir), '-o', str(oracle)], 'link-oracle', clone)
        selected = ['src/lexer.lang', 'src/parser.lang', 'src/numeric_llvm.lang',
                    'src/sexpr_reader.lang', 'std/os/libc.lang', 'example/rill/rill.lang']
        files = {('export/' + name): first / name for name in tree(first)}
        files.update({('source/' + row['source']): clone / row['source'] for row in manifest['modules']})
        comparisons = {}
        by_source = {row['source']: row for row in manifest['modules']}
        for index, name in enumerate(selected):
            original_ast = scratch / f'original-{index}.ast'
            exported_ast = scratch / f'exported-{index}.ast'
            replay.run([str(oracle), 'lang', name, str(original_ast)], f'original-core-{index}', clone)
            replay.run([str(oracle), 'rill', str(first / by_source[name]['export']), str(exported_ast)], f'exported-core-{index}', clone)
            require(core(original_ast.read_bytes()) == core(exported_ast.read_bytes()), 'parsed core differs: ' + name)
            comparisons[name] = {'original_ast_sha256': sha(original_ast), 'exported_ast_sha256': sha(exported_ast), 'equal_core': True}
            files['core/' + original_ast.name] = original_ast
            files['core/' + exported_ast.name] = exported_ast
        # Parse every complete exported bundle through the actual Rill frontend.
        for label, row in manifest['closures'].items():
            replay.run([str(oracle), 'rill', str(first / row['export']), str(scratch / (label + '.ast'))], 'parse-' + label, clone)
        probe, edited_probe = scratch / 'probe', scratch / 'edited-probe'
        entry = 'test/reader_author/fixtures/rill/closure-main.lang'
        replay.run([sys.executable, '-B', exporter, '--entry', entry, '--output', str(probe)], 'export-probe', clone)
        validate(probe, clone)
        minted = scratch / 'rillc'
        replay.run([compiler, 'compiler', 'rill', 'example/rill/rill.lang', '-o', str(minted)], 'mint-rill-compiler', clone)

        def execute(pack, name, expected):
            ir, binary = scratch / (name + '.ll'), scratch / name
            replay.env['PATH'] = '/nonexistent'
            replay.run([str(minted), str(pack / 'program.rill'), '-o', str(ir)], name + '-compile', clone)
            replay.env['PATH'] = os.environ['PATH']
            replay.run(['clang', str(ir), '-o', str(binary)], name + '-link', clone)
            expect_output(replay.run([str(binary)], name + '-run', clone), expected)
            return sha(ir)

        before_ir = execute(probe, 'before-edit', b'16\n')
        limits = clone / 'src/limits.lang'
        old = limits.read_bytes()
        original_limits = scratch / 'original-limits.lang'
        original_limits.write_bytes(old)
        files['source/src/limits.lang'] = original_limits
        require(old.count(b'LIMIT_CALL_ARGS i64 = 16;') == 1, 'edit anchor changed')
        limits.write_bytes(old.replace(b'LIMIT_CALL_ARGS i64 = 16;', b'LIMIT_CALL_ARGS i64 = 17;'))
        changed = scratch / 'export-edited'
        replay.run([sys.executable, '-B', exporter, '--output', str(changed)], 'export-edited-closure', clone)
        validate(changed, clone)
        old_tree, new_tree = tree(first / 'modules'), tree(changed / 'modules')
        different = [name for name in old_tree if old_tree[name] != new_tree[name]]
        require(different == ['src/limits.rill'], 'one-module edit changed unrelated exported modules')
        require(sha(first / 'compiler.rill') != sha(changed / 'compiler.rill'), 'compiler bundle ignored edit')
        replay.run([sys.executable, '-B', exporter, '--entry', entry, '--output', str(edited_probe)], 'export-edited-probe', clone)
        after_ir = execute(edited_probe, 'after-edit', b'17\n')
        require(before_ir != after_ir, 'generated LLVM ignored source edit')
        files['edited/src/limits.lang'] = limits
        files['edited/src/limits.rill'] = changed / 'modules/src/limits.rill'
        files['probe/before.rill'] = probe / 'program.rill'
        files['probe/after.rill'] = edited_probe / 'program.rill'
        # Snapshot source bytes before restoring the intentionally edited scratch clone.
        archive(evidence / 'closure.tar.xz', files)
        with tarfile.open(evidence / 'closure.tar.xz', 'r:xz') as saved:
            import hashlib
            for row in manifest['modules']:
                for name, expected in [('source/' + row['source'], row['source_sha256']),
                                       ('export/' + row['export'], row['export_sha256'])]:
                    require(hashlib.sha256(saved.extractfile(name).read()).hexdigest() == expected,
                            'archived source/export hash mismatch: ' + name)
        limits.write_bytes(old)
        # Rejected constructs cannot produce a partial export, Lang envelope or AST.
        rejected = {}
        for index, source in enumerate([
            b'effect Hidden() i64', b'macro hidden(x) { return x; }',
            b'#lang{ func main() i64 { return 0; } }', b'enum E { A }',
            b'func f() i64 { let x = 1 in x; }', b'var x i64 := 1;',
            b'var x i64 = 0x10;', b'func f() *u8 { return "unclosed; }', b'/* unclosed',
            b'include "../outside.lang"',
        ]):
            fixture = clone / 'test/reader_author/fixtures/rill/export-negative.lang'
            fixture.write_bytes(source)
            output = scratch / f'rejected-{index}'
            result = replay.run([sys.executable, '-B', exporter, '--entry', fixture.relative_to(clone).as_posix(), '--output', str(output)],
                                f'reject-{index}', clone, expected=1)
            require(b'rill export:' in result.stderr and not output.exists(), 'unsupported construct partially exported')
            (evidence / f'rejected-{index}.lang').write_bytes(source)
            rejected[str(index)] = result.stderr.decode().strip()
        # The oracle must reject unsupported Rill too, rather than return a plausible AST.
        invalid = scratch / 'invalid.rill'
        invalid.write_text('effect Hidden() i64\n')
        result = replay.run([str(oracle), 'rill', str(invalid), str(scratch / 'invalid.ast')], 'reader-reject', clone, expected=66)
        require(b'unsupported Rill token' in result.stderr, 'reader accepted unsupported form')
        result = replay.run([sys.executable, '-B', '-c',
            'import runpy; from subprocess import CompletedProcess; '
            'runpy.run_path("rill_export.py")["expect_output"](CompletedProcess([], 0, b"wrong", b""), b"right")'],
            'expectation-must-fail', clone / 'test/reader_author', expected=1)
        require(b'unexpected exact stdout/stderr' in result.stderr, 'failed expectation swallowed')
        require(all(sha(clone / p) == h for p, h in hashes.items()), 'tracked sources changed')
        memory = {'runner_peak_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                  'child_peak_bytes': resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss * 1024}
        require(sum(memory.values()) <= ceiling, 'runner and child memory peaks exceeded 2 GiB')
        dump(evidence / 'checks.json', {'modules': len(manifest['modules']), 'keyword_identifier_edits': changes,
             'memory_peaks': memory,
             'unchanged_exports_identical': True, 'core_comparisons': comparisons, 'rejections': rejected,
             'changed_modules': different, 'runtime_stdout_before': '16\n', 'runtime_stdout_after': '17\n',
             'llvm_before_sha256': before_ir, 'llvm_after_sha256': after_ir,
             'remaining_closure_source_blockers': [],
             'outside_subset': ['macros/quotes', 'reader invocations', 'enums/match', 'effects',
                                'let/in', 'closures', 'import', ':=', 'nondecimal numbers']})
        dump(evidence / 'artifacts.json', {'closure.tar.xz': sha(evidence / 'closure.tar.xz'),
             'compiler': sha(compiler), 'rillc': sha(minted), 'oracle': sha(oracle)})
        dump(evidence / 'result.json', {'pass': True, 'head': head, 'observations': len(replay.rows)})
        print(f'PASS compiler closure: {len(manifest["modules"])} genuine Rill modules, '
              'hashes/spans, preserved literals/comments, parsed core, deterministic exports, '
              '16→17 source edit and runtime output, rejection and failing expectations')
        return 0
    except Exception as error:
        dump(evidence / 'result.json', {'pass': False, 'error': str(error)})
        print(f'FAIL: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
