#!/usr/bin/env python3
"""Measure the shipping fragment and aggregate source-bound author-path proofs."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import subprocess
import sys
import uuid

from project import ProjectReplay
from route import ROOT, dump, require, sha

BASE = '99807ed'
CELLS = ('grammar', 'tree', 'semantics', 'diagnostics', 'native output',
         'package relocation', 'formatting', 'editor facts', 'self-hosting')
# A gate receipt has none of these deliverables. The proof type fixes the roles;
# a producer cannot relabel an arbitrary successful command as a capability.
ROLES = {
    'shipping': {'ast', 'compact', 'formatted', 'llvm', 'compiler', 'isolated-llvm',
                 'fixtures-identity', 'fixtures-commands', 'fixtures-result', 'fixture-suite', 'source-build'},
    'tree': {'capture-tree'},
    'editor facts': {'editor-facts', 'editor-source', 'editor-core'},
    'self-hosting': {'llvm-1', 'llvm-2', 'reader-ast-1', 'reader-ast-2',
                     'suite-log', 'composed-route-log'},
}
MISSING = {
    'tree': 'No shipping capture-tree receipt; shared AST is not a capture tree.',
    'editor facts': 'No production editor/debug facts receipt; contract fixtures are not adapter proof.',
    'self-hosting': 'Integration must supply both fixed points, full suites and the composed author route.',
}
COMPILER_INPUTS = ['std/core.lang', 'out/version_info.lang', 'src/lexer.lang',
                   'src/parser.lang', 'src/codegen.lang', 'src/codegen_llvm.lang',
                   'src/codegen_wasm.lang', 'src/ast_emit.lang', 'src/sexpr_reader.lang',
                   'src/compiler_readers_none.lang', 'src/main.lang']


def compiler_generations(value, paths, current, stages, names, origin):
    """Connect both comparisons to generations descended from the current build.

    Like shipping receipts, these are records from a trusted runner, not a
    substitute for running the producer or a defense against forged logs.
    All command paths stay in their original coordinates after relocation.
    """
    require({'source-build', 'compiler-1', 'compiler-2'} <= paths.keys(),
            'missing source-bound compiler generations')
    build = load(paths['source-build'])
    # Match the complete input selection used by scripts/build_receipt.py.
    inputs = {p: h for p, h in current['sha256'].items()
              if p.startswith(('src/', 'std/', 'example/', 'test/reader_locations/')) or
              p in ('Makefile', 'scripts/build_receipt.py', 'scripts/lang_package.py',
                    'scripts/package_kit.py', 'web/build.sh',
                    'web/build_compiler.sh', 'web/build_stdlib.js')}
    require(set(COMPILER_INPUTS) - {'out/version_info.lang'} <= inputs.keys() and
            'src/lang_reader.lang' in inputs and build['mode'] == 'build' and
            build['source'] == {'revision': current['head'], 'dirty': False, 'inputs': inputs},
            'generations are not bound to the current source build')
    require(build['compiler']['sha256'] == sha(paths['compiler-1']) and
            build['compiler']['bytes'] == paths['compiler-1'].stat().st_size,
            'generation compiler differs from current source build')
    require('build-current-sources' in names and
            names['build-current-sources']['command'] == ['make', 'build'] and
            names['build-current-sources']['expected_exit'] == 0,
            'missing current source build command')
    cwd = names['build-current-sources']['cwd']
    positions = {row['name']: i for i, row in enumerate(stages)}

    def command(name, middle, roles, before):
        require(name in names and names[name]['expected_exit'] == 0 and
                names[name]['cwd'] == cwd and positions[before] < positions[name],
                'missing ordered compiler generation: ' + name)
        row = names[name]
        argv = row['command']
        require(len(argv) == len(middle) + 2 and argv[1:-1] == middle,
                'compiler generation command mismatch: ' + name)
        recorded_artifacts([argv[0], argv[-1]],
                           [value['artifacts'][role]['path'] for role in roles], cwd, origin)
        return row

    first = command('llvm-generation-1', [*COMPILER_INPUTS, '-o'],
                    ('compiler-1', 'llvm-1'), 'build-current-sources')
    require(first['environment']['LANGBE'] == 'llvm' and
            first['environment']['LANGOS'] in ('linux', 'macos'), 'wrong compiler generation target')
    require('link-generation-2' in names, 'missing ordered compiler generation: link-generation-2')
    link = names['link-generation-2']
    require(link['expected_exit'] == 0 and link['cwd'] == cwd and
            positions['llvm-generation-1'] < positions['link-generation-2'] and
            len(link['command']) == 5 and link['command'][:2] == [value['tools']['clang']['path'], '-O2'] and
            link['command'][3] == '-o', 'compiler generation link mismatch')
    recorded_artifacts([link['command'][2], link['command'][4]],
                       [value['artifacts'][role]['path'] for role in ('llvm-1', 'compiler-2')], cwd, origin)
    second = command('llvm-generation-2', [*COMPILER_INPUTS, '-o'],
                     ('compiler-2', 'llvm-2'), 'link-generation-2')
    require(second['environment'] == first['environment'], 'compiler generation environments differ')
    for number, before in [(1, 'build-current-sources'), (2, 'link-generation-2')]:
        row = command('reader-ast-generation-' + str(number),
                      ['src/lang_reader.lang', '--emit-expanded-ast', '-o'],
                      ('compiler-' + str(number), 'reader-ast-' + str(number)), before)
        require(row['environment'] == first['environment'], 'reader generation environment differs')
    require(positions['llvm-generation-2'] < positions['llvm-fixed-point'] and
            max(positions['reader-ast-generation-1'], positions['reader-ast-generation-2']) <
            positions['reader-ast-fixed-point'], 'comparison precedes compiler generation')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def source():
    paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    hashes = {p: sha(ROOT / p) for p in paths if p and (ROOT / p).is_file()}
    return {'head': git('rev-parse', 'HEAD'), 'sha256': hashes,
            'digest': hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()}


def artifact(root, path):
    path = Path(path).resolve()
    require(root in path.parents, 'artifact must be inside receipt directory')
    return {'path': str(path.relative_to(root)), 'sha256': sha(path), 'bytes': path.stat().st_size}


def retained(root, record):
    relative = Path(record['path'])
    require(not relative.is_absolute() and '..' not in relative.parts, 'unsafe artifact path')
    path = (root / relative).resolve()
    require(root in path.parents and path.is_file(), 'missing artifact: ' + str(relative))
    require(path.stat().st_size == record['bytes'] and sha(path) == record['sha256'],
            'artifact hash mismatch: ' + str(relative))
    return path


def load(path):
    return json.loads(path.read_text())


def recorded_artifacts(arguments, relatives, cwd, origin=None):
    """Match retained paths in the command's original coordinates, without I/O."""
    require(len(arguments) == len(relatives), 'artifact command arity mismatch')
    for argument, relative in zip(arguments, relatives):
        path, relative = Path(argument), Path(relative)
        require(not relative.is_absolute() and relative.parts and '..' not in relative.parts and
                '..' not in path.parts, 'unsafe recorded artifact path')
        if not path.is_absolute():
            require(Path(cwd).is_absolute(), 'missing original command directory')
            path = Path(cwd) / path
        require(path.parts[-len(relative.parts):] == relative.parts,
                'recorded artifact path mismatch')
        directory = path.parents[len(relative.parts) - 1]
        if origin is None:
            origin = directory
        require(directory == origin, 'recorded artifacts have different receipt directories')
    return origin


def fixture_diagnostic(stderr, diag, source):
    """Match a located reader rejection in the producer's original coordinates."""
    require(Path(source).suffix == '.' + diag['label'], 'diagnostic label does not match source')
    pattern = (r'^(?:' + re.escape(diag['label']) + '|' + re.escape(source) + '):' +
               str(diag['line']) + ':' + str(diag['column']) + ': .*' +
               re.escape(diag['message_contains'])).encode()
    require(re.search(pattern, stderr, re.M), 'located diagnostic expectation failed')


def fixture_proof(paths, compiler_sha, current, inventory):
    """Read the real project fixture host's receipts, then recheck its assertions."""
    identity = load(paths['fixtures-identity'])
    result = load(paths['fixtures-result'])
    commands = load(paths['fixtures-commands'])
    suite = load(paths['fixture-suite'])
    require(identity['compiler']['sha256'] == compiler_sha == result['compiler_sha256'],
            'fixture compiler differs from measured source build')
    require(sha(paths['fixture-suite']) == current['sha256']['example/shipping/tests.json'], 'changed fixture assertions')
    require(identity['fixtures']['sha256'] == sha(paths['fixture-suite']) and
            identity['reader']['sha256'] == current['sha256']['example/shipping/shipping.lang'] and
            identity['project']['sha256'] == current['sha256']['example/shipping/project.lang-project'] and
            [r['sha256'] for r in identity['runtime']] == [current['sha256']['example/shipping/runtime.lang']],
            'fixture identities differ from current shipping inputs')
    build = load(paths['source-build'])
    require(build['mode'] == 'build' and build['source']['revision'] == current['head'] and
            build['source']['dirty'] is False and build['compiler']['sha256'] == compiler_sha and
            all(current['sha256'].get(p) == h for p, h in build['source']['inputs'].items()),
            'fixture compiler is not the current source build')
    require(result['pass'] is True and result['fixtures'] ==
            [{'name': c['name'], 'pass': True} for c in suite['fixtures']], 'missing fixture result')
    # Commands and outputs are retained beside the genuine commands.json.
    directory = paths['fixtures-commands'].parent
    for row in commands:
        for stream in ('stdout', 'stderr'):
            require('fixtures/' + row[stream] in inventory, 'uninventoried fixture stream')
    for case in suite['fixtures']:
        require(identity['sources'][case['source']]['sha256'] ==
                current['sha256']['example/shipping/' + case['source']], 'changed fixture source')
    require(commands and commands[0]['exit'] == 0, 'missing toolchain observation')
    index = 1
    origin = None
    for case in suite['fixtures']:
        row = commands[index]
        index += 1
        require(row['command'][0] == identity['compiler']['path'] and row['command'][1] == 'build',
                'fixture did not use the measured native driver')
        require(row['command'][4] == identity['sources'][case['source']]['path'], 'fixture source mismatch')
        stderr = (directory / row['stderr']).read_bytes()
        output = directory / (case['name'] + '.native')
        if 'diagnostic' in case:
            diag = case['diagnostic']
            require(row['exit'] == 1 and b'native build reader failed' in stderr,
                    'gate or tool failure substituted for reader diagnostic')
            fixture_diagnostic(stderr, diag, identity['sources'][case['source']]['path'])
        else:
            require(row['exit'] == 0 and output.read_bytes().startswith(b'\x7fELF'), 'missing native artifact')
            relative = 'fixtures/' + output.name
            require(relative in inventory and inventory[relative]['path'] == relative,
                    'uninventoried native artifact')
            require(len(row['command']) == 7 and row['command'][5] == '-o', 'missing native output command')
            original_output = row['command'][6]
            origin = recorded_artifacts([original_output], [relative], row['cwd'], origin)
            require(set(row['phase_exits']) == {'reader', 'validation', 'llvm', 'object', 'link'} and
                    all(code == 0 for code in row['phase_exits'].values()), 'missing native phases')
            for expected in case['runs']:
                run = commands[index]
                index += 1
                require(run['command'] == [original_output, *expected['args']] and run['cwd'] == row['cwd'],
                        'runtime command mismatch')
                require(run['exit'] == expected['exit'] and
                        (directory / run['stdout']).read_text() == expected['stdout'] and
                        (directory / run['stderr']).read_text() == expected['stderr'], 'runtime expectation failed')
    require(index == len(commands), 'unexpected fixture commands')


def validate(root, value, current):
    require(value.get('schema') == 'lang-author-path/1', 'not a focused author-path receipt')
    require(value['source'] == current, 'stale source identity')
    kind = value['kind']
    require(kind in ROLES, 'unknown proof type; broad gates are not deliverables')
    inventory = value['inventory']
    require(inventory, 'missing artifact inventory')
    for record in inventory.values():
        retained(root, record)
    paths = {role: retained(root, record) for role, record in value['artifacts'].items()}
    require(ROLES[kind] <= paths.keys(), 'missing required deliverable')
    require(all(record in inventory.values() for record in value['artifacts'].values()), 'uninventoried deliverable')
    tools = value['tools']
    require({'python3', 'git', 'make', 'clang', 'ld'} <= tools.keys(), 'missing tool identities')
    for record in tools.values():
        require(Path(record['path']).is_file() and sha(record['path']) == record['sha256'], 'tool identity changed')
    stages = load(retained(root, value['stages']))
    require(stages and value['stages'] in inventory.values(), 'missing focused commands')
    for row in stages:
        require(row['command'] and type(row['expected_exit']) is int and row['exit'] == row['expected_exit'],
                'command expectation failed')
        for stream in ('stdout', 'stderr'):
            require(row[stream] in inventory, 'missing command ' + stream)
            retained(root, inventory[row[stream]])
    names = {row['name']: row for row in stages}
    require(len(names) == len(stages), 'duplicate focused command name')
    if kind == 'shipping':
        fixture_proof(paths, load(paths['source-build'])['compiler']['sha256'], current, inventory)
        ast = paths['ast'].read_bytes()
        require(b'(binop >=' in ast and b'(ident total)' in ast and b'(number 100)' in ast,
                'missing variable policy AST')
        require(ast == paths['formatted'].read_bytes(), 'formatting is not idempotent')
        require(re.sub(rb'\s+', b'', ast) == re.sub(rb'\s+', b'', paths['compact'].read_bytes()),
                'compact/pretty AST disagree')
        require(paths['llvm'].read_bytes() == paths['isolated-llvm'].read_bytes(), 'relocated compiler changed LLVM')
        require({'build-current-sources', 'fixtures', 'mint', 'before-relocation', 'after-relocation'} <= names.keys(),
                'missing shipping route commands')
        require(names['after-relocation']['environment']['PATH'] == '/nonexistent', 'relocation used ambient tools')
        return ('grammar', 'semantics', 'diagnostics', 'native output', 'package relocation', 'formatting')
    if kind == 'tree':
        require('capture-tree' in names and names['capture-tree']['expected_exit'] == 0 and
                paths['capture-tree'] == root / names['capture-tree']['stdout'], 'missing capture-tree producer command')
        tree = load(paths['capture-tree'])
        require(tree['kind'] == 'shipping_policy' and tree['captures'] and
                tree['source_sha256'] == current['sha256']['example/shipping/policy.shipping'],
                'missing source-bound shipping capture tree')
    elif kind == 'editor facts':
        require('editor-facts' in names and names['editor-facts']['expected_exit'] == 0 and
                paths['editor-facts'] == root / names['editor-facts']['stdout'], 'missing editor producer command')
        facts = load(paths['editor-facts'])
        require(facts['bindings'] and facts['sites'] and facts['origins'] and
                facts['core_sha256'] == sha(paths['editor-core']) and
                any(s['sha256'] == sha(paths['editor-source']) for s in facts['sources']),
                'missing source/core-bound editor facts')
        # Contract fixture snapshots cannot establish production adapter support.
        require(value['producer'] != 'contract-fixture', 'contract fixture substituted for editor producer')
    else:
        origin = None
        for name, first, second in [('llvm-fixed-point', 'llvm-1', 'llvm-2'),
                                    ('reader-ast-fixed-point', 'reader-ast-1', 'reader-ast-2')]:
            require(name in names and names[name]['expected_exit'] == 0 and
                    len(names[name]['command']) == 3 and names[name]['command'][0] == 'cmp',
                    'missing observed fixed-point comparison: ' + name)
            origin = recorded_artifacts(names[name]['command'][1:],
                                        [value['artifacts'][role]['path'] for role in (first, second)],
                                        names[name]['cwd'], origin)
        compiler_generations(value, paths, current, stages, names, origin)
        for name, command, role in [
                ('full-suites', ['make', 'test-all'], 'suite-log'),
                ('composed-author-route', ['python3', '-B', 'test/reader_author/route.py', '--case', 'shipping'],
                 'composed-route-log')]:
            require(name in names and names[name]['command'] == command and names[name]['expected_exit'] == 0 and
                    paths[role] == root / names[name]['stdout'], 'missing integration command: ' + name)
        require(paths['llvm-1'].read_bytes() == paths['llvm-2'].read_bytes() and paths['llvm-1'].stat().st_size > 0,
                'LLVM fixed point failed')
        require(paths['reader-ast-1'].read_bytes() == paths['reader-ast-2'].read_bytes() and
                paths['reader-ast-1'].stat().st_size > 0, 'reader AST fixed point failed')
        require(all(paths[k].stat().st_size for k in ('suite-log', 'composed-route-log')),
                'integration suite/composed route proof missing')
    require(all(p.stat().st_size for p in paths.values()), 'empty deliverable')
    return (kind,)


def aggregate(receipts, output, release=False):
    current = source()
    cells = {name: {'status': 'not measured', 'source': {'head': current['head'], 'digest': current['digest']},
                    'reason': MISSING.get(name, 'No focused shipping receipt.')} for name in CELLS}
    for receipt in receipts:
        receipt = receipt.resolve()
        for name in validate(receipt.parent, load(receipt), current):
            require(cells[name]['status'] != 'measured', 'duplicate capability proof: ' + name)
            cells[name].update(status='measured', reason='Focused deliverables and command expectations checked.',
                               receipt=str(receipt), receipt_sha256=sha(receipt))
    matrix = {'schema': 'lang-author-matrix/1', 'source': current, 'cells': cells,
              'release_ready': all(cell['status'] == 'measured' for cell in cells.values()),
              'integration_required': ['full existing suites', 'LLVM and reader-AST fixed points', 'final composed author route']}
    output.mkdir(parents=True, exist_ok=True)
    dump(output / 'matrix.json', matrix)
    lines = ['# Language author readiness', '', 'Source `' + current['head'] + '`.', '',
             '| Capability | Evidence |', '| --- | --- |']
    lines += [f'| {name} | {cell["status"]}: {cell["reason"]} |' for name, cell in cells.items()]
    lines += ['', 'Release ready: ' + ('yes' if matrix['release_ready'] else 'no') + '.',
              'Integration supplies full suites, both fixed points and the final composed route.', '']
    (output / 'README.md').write_text('\n'.join(lines))
    require(not release or matrix['release_ready'], 'release blocked: ' + ', '.join(
        name for name, cell in cells.items() if cell['status'] != 'measured'))
    return matrix


class PathReplay(ProjectReplay):
    def run(self, command, name, cwd, expected=0):
        try:
            return super().run(command, name, cwd, expected)
        finally:
            if self.rows and self.rows[-1]['name'] == name:
                self.rows[-1]['expected_exit'] = expected
                dump(self.evidence / 'stages.json', self.rows)


def limits():
    os.nice(10)
    cpus = sorted(os.sched_getaffinity(0))[:2]
    os.sched_setaffinity(0, cpus)
    hard = resource.getrlimit(resource.RLIMIT_AS)[1]
    ceiling = min(2 * 1024**3, hard) if hard != resource.RLIM_INFINITY else 2 * 1024**3
    resource.setrlimit(resource.RLIMIT_AS, (ceiling, ceiling))
    return {'cpus': cpus, 'address_space_bytes': ceiling, 'JOBS': 2, 'MAKEFLAGS': '-j2'}


def controls(value, evidence, scratch):
    """Small aggregation controls use real receipts without rerunning the route."""
    current = source()
    relocated = scratch / 'retained-receipt'
    relocated.mkdir()
    for record in value['inventory'].values():
        target = relocated / record['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(retained(evidence, record), target)
    shutil.copyfile(evidence / 'focused.json', relocated / 'focused.json')
    command = [sys.executable, '-B', str(ROOT / 'test/reader_author/path_receipt.py'),
               '--case', 'aggregate', '--receipt', str(relocated / 'focused.json'),
               '--evidence', str(scratch / 'relocated-matrix')]
    result = subprocess.run(command, capture_output=True, timeout=30)
    (evidence / 'relocation-control.stdout').write_bytes(result.stdout)
    (evidence / 'relocation-control.stderr').write_bytes(result.stderr)
    dump(evidence / 'relocation-control.json', {'command': command, 'exit': result.returncode,
         'receipt_sha256': sha(relocated / 'focused.json'),
         'original_receipt_sha256': sha(evidence / 'focused.json')})
    require(result.returncode == 0, 'relocated genuine receipt rejected: ' + result.stderr.decode())
    matrix = load(scratch / 'relocated-matrix/matrix.json')
    require(matrix['source'] == current and not matrix['release_ready'] and
            {name for name, cell in matrix['cells'].items() if cell['status'] == 'measured'} ==
            {'grammar', 'semantics', 'diagnostics', 'native output', 'package relocation', 'formatting'},
            'relocation changed measured capabilities')
    cases = {}
    for name in ('stale-head', 'changed-source', 'missing-artifact', 'altered-artifact', 'wrong-exit',
                 'runtime-path', 'runtime-args', 'build-output-path', 'gate-only'):
        changed = copy.deepcopy(value)
        if name == 'stale-head':
            changed['source']['head'] = '0' * 40
        elif name == 'changed-source':
            changed['source']['sha256']['example/shipping/shipping.lang'] = '0' * 64
        elif name == 'missing-artifact':
            changed['artifacts']['ast']['path'] = 'absent.ast'
        elif name == 'altered-artifact':
            changed['artifacts']['ast']['sha256'] = '0' * 64
        elif name == 'wrong-exit':
            rows = load(evidence / 'stages.json')
            rows[-1]['expected_exit'] = 91
            path = evidence / 'wrong-exit-stages.json'
            dump(path, rows)
            changed['stages'] = artifact(evidence, path)
            changed['inventory'][path.name] = changed['stages']
        elif name in ('runtime-path', 'runtime-args', 'build-output-path'):
            rows = load(evidence / 'fixtures/commands.json')
            if name == 'runtime-path':
                rows[2]['command'][0] = '/another/receipt/fixtures/policy.native'
            elif name == 'runtime-args':
                rows[2]['command'][1] = 'unexpected'
            else:
                rows[1]['command'][6] = '/another/receipt/policy.native'
                for row in rows[2:5]:
                    row['command'][0] = rows[1]['command'][6]
            path = evidence / 'fixtures' / (name + '-commands.json')
            dump(path, rows)
            changed['artifacts']['fixtures-commands'] = artifact(evidence, path)
            changed['inventory'][str(path.relative_to(evidence))] = changed['artifacts']['fixtures-commands']
        else:
            changed = {'pass': True, 'command': 'make verify', 'head': current['head']}
        dump(evidence / (name + '-receipt.json'), changed)
        try:
            validate(evidence, changed, current)
        except (RuntimeError, KeyError, ValueError) as error:
            expected = {'runtime-path': 'runtime command mismatch',
                        'runtime-args': 'runtime command mismatch',
                        'build-output-path': 'recorded artifact path mismatch'}.get(name)
            require(expected is None or str(error) == expected, 'wrong rejection for ' + name + ': ' + str(error))
            cases[name] = {'rejected': True, 'reason': str(error)}
        else:
            raise RuntimeError('aggregation accepted ' + name)
    dump(evidence / 'aggregation-controls.json', cases)
    # Exercise the public runner too: a failed expectation must be a failed process.
    command = [sys.executable, '-B', str(ROOT / 'test/reader_author/path_receipt.py'),
               '--case', 'aggregate', '--receipt', str(evidence / 'wrong-exit-receipt.json'),
               '--evidence', str(evidence / 'failed-expectation')]
    result = subprocess.run(command, capture_output=True, timeout=30)
    (evidence / 'failed-expectation.stdout').write_bytes(result.stdout)
    (evidence / 'failed-expectation.stderr').write_bytes(result.stderr)
    dump(evidence / 'failed-expectation-command.json', {'command': command, 'exit': result.returncode})
    require(result.returncode == 1 and b'command expectation failed' in result.stderr,
            'failed expectation did not make the public runner fail')


def shipping(evidence, bounded):
    scratch = ROOT.parent / 'scratch' / ('path-' + uuid.uuid4().hex)
    scratch.mkdir(parents=True)
    replay = PathReplay(evidence, scratch)
    replay.env.update(MAKEFLAGS='-j2', PYTHONDONTWRITEBYTECODE='1')
    for key in ('VERIFY_CASE', 'LANG_ROOT', 'LANG_CLANG', 'MAKEOVERRIDES'):
        replay.env.pop(key, None)
    status = replay.run(['git', 'status', '--porcelain', '--untracked-files=all'], 'clean', ROOT)
    require(not status.stdout, 'commit candidate before measurement')
    replay.run(['git', 'merge-base', '--is-ancestor', BASE, 'HEAD'], 'required-base', ROOT)
    replay.run(['git', 'diff', '--exit-code', BASE, 'HEAD', '--', 'bootstrap/current', 'web'], 'protected-inputs', ROOT)
    clone = scratch / 'repo'
    replay.run(['git', 'clone', '--quiet', '--no-hardlinks', str(ROOT), str(clone)], 'clone', ROOT)
    identity = source()
    tools = {name: {'path': str(Path(shutil.which(name)).resolve()),
                    'sha256': sha(Path(shutil.which(name)).resolve())}
             for name in ('python3', 'git', 'make', 'clang', 'ld')}
    dump(evidence / 'identity.json', {'source': identity, 'tools': tools, 'limits': bounded,
         'assumptions': 'Headless Linux x86-64 libc; trusted native shipping reader; whole-unit inclusive policy; '
                        'no OS kernel operations; capture tree and production editor/debug facts unmeasured; '
                        'source build is not a self-hosting fixed point; integration alone runs full suites and fixed points.'})
    replay.run(['make', 'init'], 'init', clone)
    replay.run(['make', 'build'], 'build-current-sources', clone)
    shutil.copyfile(clone / 'out/build-receipt.json', evidence / 'source-build.json')
    compiler = str(clone / 'out/lang_next')
    project = clone / 'example/shipping/project.lang-project'
    reader = clone / 'example/shipping/shipping.lang'
    policy = clone / 'example/shipping/policy.shipping'
    replay.run([compiler, 'project', 'check', str(project)], 'project-inputs', scratch)
    ast = replay.run([compiler, 'project', 'read', str(project)], 'ast', scratch)
    compact = replay.run([compiler, 'read', str(reader), str(policy), '--compact'], 'compact', scratch)
    (evidence / 'policy.ast').write_bytes(ast.stdout)
    (evidence / 'compact.ast').write_bytes(compact.stdout)
    formatted = replay.run([compiler, 'read', str(clone / 'test/fixtures/ast_format/identity.lang'),
                            str(evidence / 'policy.ast')], 'formatted', scratch)
    (evidence / 'formatted.ast').write_bytes(formatted.stdout)
    # The shipping fixture host runs this authored suite exactly once.
    replay.run([compiler, 'test', '--project', str(project), '--evidence', str(evidence / 'fixtures')], 'fixtures', scratch)
    shutil.copyfile(clone / 'example/shipping/tests.json', evidence / 'fixture-suite.json')
    minted = scratch / 'shippingc'
    replay.run([compiler, 'project', 'compiler', str(project), '-o', str(minted)], 'mint', scratch)
    replay.run([str(minted), str(policy), '-o', str(evidence / 'policy.ll')], 'before-relocation', scratch)
    isolated = scratch / 'isolated'
    isolated.mkdir()
    shutil.copyfile(minted, isolated / 'shippingc')
    (isolated / 'shippingc').chmod(0o755)
    shutil.copyfile(policy, isolated / 'policy.shipping')
    require(sorted(p.name for p in isolated.iterdir()) == ['policy.shipping', 'shippingc'], 'isolation contains extra inputs')
    saved = replay.env['PATH']
    replay.env['PATH'] = '/nonexistent'
    replay.run([str(isolated / 'shippingc'), 'policy.shipping', '-o', str(evidence / 'isolated.ll')], 'after-relocation', isolated)
    replay.env['PATH'] = saved
    shutil.copyfile(minted, evidence / 'shippingc')
    require(all(sha(clone / p) == h for p, h in identity['sha256'].items()), 'measured source inputs changed')
    roles = dict(zip(('ast', 'compact', 'formatted', 'llvm', 'compiler', 'isolated-llvm',
                      'fixtures-identity', 'fixtures-commands', 'fixtures-result', 'fixture-suite', 'source-build'),
                     ('policy.ast', 'compact.ast', 'formatted.ast', 'policy.ll', 'shippingc', 'isolated.ll',
                      'fixtures/identity.json', 'fixtures/commands.json', 'fixtures/result.json', 'fixture-suite.json', 'source-build.json')))
    inventory = {str(p.relative_to(evidence)): artifact(evidence, p)
                 for p in evidence.rglob('*') if p.is_file()}
    value = {'schema': 'lang-author-path/1', 'kind': 'shipping', 'producer': 'test/reader_author/path_receipt.py',
             'source': identity, 'tools': tools, 'inventory': inventory,
             'stages': inventory['stages.json'], 'artifacts': {role: inventory[path] for role, path in roles.items()}}
    dump(evidence / 'focused.json', value)
    controls(value, evidence, scratch)
    matrix = aggregate([evidence / 'focused.json'], evidence)
    require(not matrix['release_ready'], 'fragment alone incorrectly authorized release')
    try:
        aggregate([evidence / 'focused.json'], evidence / 'release-control', release=True)
    except RuntimeError as error:
        dump(evidence / 'release-control.json', {'rejected': True, 'reason': str(error)})
    else:
        raise RuntimeError('release accepted missing whole-path evidence')
    print('PASS shipping path: focused fixtures, source-bound matrix, aggregation controls; release remains blocked')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['shipping', 'aggregate'], required=True)
    parser.add_argument('--receipt', type=Path, action='append', default=[])
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--require-release', action='store_true')
    args = parser.parse_args()
    bounded = limits()
    evidence = (args.evidence or ROOT.parent / 'evidence' / ('path-' + uuid.uuid4().hex)).resolve()
    require(ROOT not in evidence.parents and ROOT != evidence, 'evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=False)
    print('evidence: ' + str(evidence), flush=True)
    try:
        require(not git('status', '--porcelain', '--untracked-files=all'), 'commit candidate before checking receipts')
        if args.case == 'shipping':
            require(not args.receipt and not args.require_release, 'shipping is a fragment, use aggregate for release')
            shipping(evidence, bounded)
        else:
            aggregate(args.receipt, evidence, args.require_release)
        dump(evidence / 'result.json', {'pass': True, 'head': git('rev-parse', 'HEAD')})
        return 0
    except (RuntimeError, KeyError, TypeError, ValueError, OSError, subprocess.SubprocessError) as error:
        dump(evidence / 'result.json', {'pass': False, 'head': git('rev-parse', 'HEAD'), 'error': str(error)})
        print('FAIL: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
