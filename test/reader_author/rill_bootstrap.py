#!/usr/bin/env python3
"""Two-generation module fragment; complete Rill fixed points are opt-in integration."""
import argparse
import json
import os
from pathlib import Path
import re
import resource
import shutil
import sys
import uuid

from route import Replay, ROOT, dump, require, sha
from rill_export import archive, tree, validate

BASE = '2d80f9c271437e33f7637304caa315cfe74afdb0'
FIXTURES = 'test/reader_author/fixtures/rill/'


def same(left, right, label):
    require(left.read_bytes() == right.read_bytes(), label + ': bytes differ')


def exact(result, output=b''):
    require(result.stdout == output and not result.stderr, 'unexpected stdout/stderr')


class Bootstrap:
    def __init__(self, replay, isolated):
        self.replay = replay
        self.isolated = isolated
        self.rows = []

    def compile(self, compiler, source, output, name, options=()):
        # Compiler binaries and exported packages are outside any source tree.
        # No tool subprocess or original-source resource root is available.
        old_path = self.replay.env['PATH']
        self.replay.env['PATH'] = '/nonexistent'
        try:
            result = self.replay.run([str(compiler), str(source), *options, '-o', str(output)],
                                     name, self.isolated)
        finally:
            self.replay.env['PATH'] = old_path
        require(not result.stderr and output.is_file(), name + ': missing output or diagnostic')
        row = {'name': name, 'compiler_sha256': sha(compiler),
               'input': source.relative_to(self.isolated).as_posix(), 'input_sha256': sha(source),
               'options': list(options), 'output': output.name, 'output_sha256': sha(output),
               'PATH': '/nonexistent', 'native_backend': 'Clang (separate link command)'}
        self.rows.append(row)
        dump(self.replay.evidence / 'stage-manifest.json', self.rows)

    def link(self, ir, binary, name):
        self.replay.run(['clang', '-O1', str(ir), '-o', str(binary)], name, self.isolated)
        self.rows.append({'name': name, 'input': ir.name, 'input_sha256': sha(ir),
                          'output': binary.name, 'output_sha256': sha(binary),
                          'native_backend': 'Clang -O1; system native linker'})
        dump(self.replay.evidence / 'stage-manifest.json', self.rows)


def integration(boot, stage1, compiler_source, reader_source, clone, scratch, files):
    """This branch is intentionally not executed by the local module fragment."""
    replay, isolated = boot.replay, boot.isolated
    stages = {1: stage1}
    for n in (2, 3):
        ir, binary = isolated / f'compiler-stage{n}.ll', isolated / f'rill-stage{n}'
        boot.compile(stages[n - 1], compiler_source, ir, f'compiler-stage{n}')
        boot.link(ir, binary, f'link-compiler-stage{n}')
        stages[n] = binary
        files[ir.name] = ir
    # Exact complete output comparison: no normalization or selected-function diff.
    same(isolated / 'compiler-stage2.ll', isolated / 'compiler-stage3.ll', 'compiler LLVM fixed point')
    for n in (2, 3):
        ast = isolated / f'reader-stage{n}.ast'
        boot.compile(stages[n], reader_source, ast, f'reader-AST-stage{n}', ('--emit-expanded-ast',))
        require(ast.stat().st_size > 10000 and b'(reader_expr rill ' not in ast.read_bytes()
                and b'(func rill_parse_source ' in ast.read_bytes(), 'reader AST was not fully expanded')
        files[ast.name] = ast
    same(isolated / 'reader-stage2.ast', isolated / 'reader-stage3.ast', 'reader AST fixed point')

    # Shipping is an explicit application boundary, using the recorded authored
    # Lang reader/runtime and toolkit, rather than a compiler rebuild fallback.
    for n in (2, 3):
        shippingc = isolated / f'shippingc-stage{n}'
        replay.run([str(stages[n]), 'compiler', 'shipping', 'example/shipping/shipping.lang',
                    '--runtime', 'example/shipping/runtime.lang', '-o', str(shippingc)],
                   f'mint-shipping-stage{n}', clone)
        policy = isolated / 'policy.shipping'
        policy.write_bytes((clone / 'example/shipping/policy.shipping').read_bytes())
        ir, binary = isolated / f'shipping-stage{n}.ll', isolated / f'shipping-stage{n}'
        boot.compile(shippingc, policy, ir, f'shipping-compile-stage{n}')
        boot.link(ir, binary, f'shipping-link-stage{n}')
        for value, expected in [('99', b'10\n'), ('100', b'0\n'), ('120', b'0\n')]:
            exact(replay.run([str(binary), value], f'shipping-stage{n}-{value}', isolated), expected)
        changed = isolated / 'changed.shipping'
        require(b'100' in policy.read_bytes(), 'shipping fixture threshold drifted')
        changed.write_bytes(policy.read_bytes().replace(b'100', b'101'))
        edited_ir, edited = isolated / f'changed-stage{n}.ll', isolated / f'changed-stage{n}'
        boot.compile(shippingc, changed, edited_ir, f'changed-policy-stage{n}')
        require(sha(ir) != sha(edited_ir), 'changed semantic input produced identical IR')
        boot.link(edited_ir, edited, f'changed-link-stage{n}')
        exact(replay.run([str(edited), '100'], f'changed-runtime-stage{n}', isolated), b'10\n')
        reject_comparison(replay, ir, edited_ir, f'reject-changed-semantics-stage{n}', isolated)
        for p in (policy, changed, ir, edited_ir):
            files[p.name] = p
    return {'compiler_stage2': 'passed', 'compiler_stage3': 'passed',
            'compiler_LLVM': 'passed', 'reader_AST': 'passed', 'shipping': 'passed',
            'changed_semantic_input': 'rejected', 'diverse_double_compilation': 'not performed'}


def reject_comparison(replay, left, right, name, cwd):
    result = replay.run([sys.executable, '-B', '-c',
        'from pathlib import Path; import sys; '
        'sys.path.insert(0, sys.argv[1]); from rill_bootstrap import same; '
        'same(Path(sys.argv[2]), Path(sys.argv[3]), "semantic-input")',
        str(ROOT / 'test/reader_author'), str(left), str(right)], name, cwd, expected=1)
    require(b'semantic-input: bytes differ' in result.stderr, 'comparison failure was swallowed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', required=True, choices=['module', 'integration'])
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    os.nice(10)
    cpus = sorted(os.sched_getaffinity(0))[:2]
    os.sched_setaffinity(0, cpus)
    limit = 2 * 1024**3
    hard = resource.getrlimit(resource.RLIMIT_AS)[1]
    if hard != resource.RLIM_INFINITY:
        limit = min(limit, hard)
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    sys.setrecursionlimit(10000)
    token = uuid.uuid4().hex
    evidence = (args.evidence or ROOT.parent / 'evidence' / ('rill-bootstrap-' + token)).resolve()
    require(ROOT != evidence and ROOT not in evidence.parents, 'evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=False)
    scratch = ROOT.parent / 'scratch' / ('rill-bootstrap-' + token)
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
            'tools': tools, 'limits': {'cpus': cpus, 'address_space_bytes': limit, 'JOBS': 2,
                                      'MAKEFLAGS': '-j2', 'execution': 'sequential'},
            'assumptions': 'Linux x86-64, LLVM/libc, trusted native readers, Clang native backend; '
                'generated OS/version inputs frozen before export; no OS kernel operations; '
                'compiler rebuilds use only complete Rill packages in a source-free directory; '
                'module case compares only limits module generations, not full compiler fixed points; '
                'shipping integration explicitly consumes its authored Lang application/toolkit sources; '
                'fixed-point equality is repeatability, not diverse double compilation or correctness'})
        replay.run(['make', 'init'], 'init', clone)
        replay.run(['make', 'build'], 'build-host', clone)
        host = clone / 'out/lang_next'
        isolated = scratch / 'isolated'
        isolated.mkdir()
        delimiter_ir, delimiter_probe = isolated / 'delimiters.ll', isolated / 'delimiters'
        replay.run([str(host), FIXTURES + 'bootstrap-delimiters.lang', '-o', str(delimiter_ir)],
                   'compile-delimiter-probe', clone)
        replay.run(['clang', str(delimiter_ir), '-o', str(delimiter_probe)], 'link-delimiter-probe', clone)
        exact(replay.run([str(delimiter_probe)], 'raw-delimiter-regression', isolated))
        seed = isolated / 'rill-seed'
        seed_ir = isolated / 'rill-seed.ll'
        replay.run([str(host), FIXTURES + 'bootstrap-compiler.lang', '-o', str(seed_ir)],
                   'compile-seed-from-Lang', clone)
        replay.run(['clang', '-O1', str(seed_ir), '-o', str(seed)], 'link-seed', clone)
        boot = Bootstrap(replay, isolated)
        exporter = clone / 'scripts/rill_export.py'
        spec = json.loads((clone / 'example/rill/compiler-closure.json').read_text())
        driver = (clone / (FIXTURES + 'bootstrap-compiler.lang')).read_text()
        build = (clone / 'Makefile').read_text().split('\nbuild:\n', 1)[1].split('\n# ===', 1)[0]
        command = next(line for line in build.splitlines() if '$(LANG) std/core.lang' in line)
        build_roots = command.split('$(LANG) ', 1)[1].split(' -o ', 1)[0].replace(
            '$(COMPILER_READERS)', 'src/compiler_readers_none.lang').split()
        require(build_roots == spec['closures']['compiler'], 'compiler closure drifted from make build')
        roots = re.findall(r'^include "([^"]+)"', driver, re.M)
        expected = [FIXTURES + 'bootstrap-readers.lang' if p == 'src/compiler_readers_none.lang' else p
                    for p in spec['closures']['compiler']]
        require(roots == expected, 'bootstrap compiler roots differ from declared compiler closure')
        files = {seed_ir.name: seed_ir}
        packages = {}
        entries = {'compiler': FIXTURES + 'bootstrap-compiler.lang',
                   'module': FIXTURES + 'bootstrap-module.lang'}
        for label, entry in entries.items():
            pack = isolated / (label + '-sources')
            replay.run([sys.executable, '-B', str(exporter), '--entry', entry, '--output', str(pack)],
                       'export-' + label, clone)
            manifest, _ = validate(pack, clone)
            packages[label] = pack / 'program.rill'
            files.update({label + '/export/' + p: pack / p for p in tree(pack)})
            files.update({'source/' + row['source']: clone / row['source'] for row in manifest['modules']})
        dump(evidence / 'isolation.json', {'cwd': str(isolated), 'source_root': None,
             'PATH_during_compilation': '/nonexistent', 'initial_files': sorted(p.name for p in isolated.iterdir()),
             'packages': {k: sha(v) for k, v in packages.items()}})
        stage1_ir, stage1 = isolated / 'compiler-stage1.ll', isolated / 'rill-stage1'
        boot.compile(seed, packages['compiler'], stage1_ir, 'compiler-stage1')
        boot.link(stage1_ir, stage1, 'link-compiler-stage1')
        files[stage1_ir.name] = stage1_ir
        # Two compiler generations process the same smallest real compiler module.
        # Stage 2 of the complete compiler is an integration obligation below.
        module_irs = []
        for n, compiler in enumerate((seed, stage1), 1):
            ir, binary = isolated / f'module-generation{n}.ll', isolated / f'module-generation{n}'
            boot.compile(compiler, packages['module'], ir, f'module-generation{n}')
            boot.link(ir, binary, f'link-module-generation{n}')
            exact(replay.run([str(binary)], f'run-module-generation{n}', isolated, expected=16))
            module_irs.append(ir)
            files[ir.name] = ir
        same(*module_irs, 'limits module LLVM')
        module_ast = isolated / 'module-expanded.ast'
        boot.compile(stage1, packages['module'], module_ast, 'module-expanded-AST', ('--emit-expanded-ast',))
        require(b'LIMIT_CALL_ARGS' in module_ast.read_bytes() and b'(func main ' in module_ast.read_bytes()
                and b'(reader_expr ' not in module_ast.read_bytes(), 'module AST did not expand source packages')
        files[module_ast.name] = module_ast
        # A semantic edit changes both IR and execution, and the equality oracle fails.
        changed = isolated / 'changed-module.rill'
        original = packages['module'].read_bytes()
        require(original.count(b'LIMIT_CALL_ARGS i64 = 16;') == 1, 'limits input drifted')
        changed.write_bytes(original.replace(b'LIMIT_CALL_ARGS i64 = 16;', b'LIMIT_CALL_ARGS i64 = 17;'))
        changed_ir, changed_binary = isolated / 'changed-module.ll', isolated / 'changed-module'
        boot.compile(stage1, changed, changed_ir, 'semantic-edit')
        boot.link(changed_ir, changed_binary, 'link-semantic-edit')
        exact(replay.run([str(changed_binary)], 'run-semantic-edit', isolated, expected=17))
        reject_comparison(replay, module_irs[1], changed_ir, 'expectation-must-fail', isolated)
        for label, source, diagnostic in (
            ('frontend', 'fun main() i64 { local = ; }', b'rill:'),
            ('backend', 'fun main() i64 { return absent_name; }', b'absent_name'),
            ('missing-dependency', 'package { source "probe.lang" { use "src/limits.lang" } entry { use "probe.lang" } }',
             b'rill: missing package dependency: src/limits.lang'),
        ):
            path, output = isolated / (label + '.rill'), isolated / (label + '.ll')
            path.write_text(source)
            result = replay.run([str(stage1), str(path), '-o', str(output)], label + '-attribution', isolated, expected=1)
            require(not result.stdout and diagnostic in result.stderr and not output.exists(),
                    label + ': wrong attribution or partial output')
            files[path.name] = path
        files.update({p.name: p for p in (changed, changed_ir)})
        obligations = {'compiler_stage2': 'pending integration', 'compiler_stage3': 'pending integration',
                       'compiler_LLVM': 'pending integration', 'reader_AST': 'pending integration',
                       'shipping': 'pending integration', 'diverse_double_compilation': 'not performed'}
        if args.case == 'integration':
            reader_pack = isolated / 'reader-sources'
            replay.run([sys.executable, '-B', str(exporter), '--entry', 'example/rill/rill.lang',
                        '--output', str(reader_pack)], 'export-reader', clone)
            files.update({'reader/export/' + p: reader_pack / p for p in tree(reader_pack)})
            obligations = integration(boot, stage1, packages['compiler'], reader_pack / 'program.rill',
                                      clone, scratch, files)
        require(all(sha(clone / p) == h for p, h in hashes.items()), 'tracked source changed')
        archive(evidence / 'sources-and-stages.tar.xz', files)
        dump(evidence / 'result.json', {'pass': True, 'head': head, 'case': args.case,
            'observations': len(replay.rows), 'module_IR_equal': True,
            'module_exits': [16, 16], 'changed_module_exit': 17,
            'obligations': obligations, 'archive_sha256': sha(evidence / 'sources-and-stages.tar.xz')})
        print('PASS Rill bootstrap ' + args.case + ': two module generations, semantic edit, failure attribution; '
              + json.dumps(obligations, sort_keys=True))
        return 0
    except Exception as error:
        dump(evidence / 'result.json', {'pass': False, 'case': args.case, 'error': str(error)})
        print(f'FAIL: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
