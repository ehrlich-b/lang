#!/usr/bin/env python3
"""Tiny aggregation fixtures; these do not measure compiler fixed points."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from path_receipt import COMPILER_INPUTS, ROOT, artifact, dump, fixture_diagnostic, recorded_artifacts, sha, validate


class RetainedPaths(unittest.TestCase):
    def test_original_coordinates(self):
        self.assertEqual(recorded_artifacts(
            ['/old/proof/llvm/one.ll', 'llvm/two.ll'],
            ['llvm/one.ll', 'llvm/two.ll'], '/old/proof'), Path('/old/proof'))

    def test_wrong_directory_and_traversal(self):
        for paths in [
                ['/old/proof/llvm/one.ll', '/other/proof/llvm/two.ll'],
                ['/old/proof/one.ll', '/old/proof/llvm/two.ll'],
                ['/old/proof/llvm/one.ll', '/old/proof/llvm/../llvm/two.ll']]:
            with self.subTest(paths=paths), self.assertRaises(RuntimeError):
                recorded_artifacts(paths, ['llvm/one.ll', 'llvm/two.ll'], '/old/proof')

    def test_source_path_diagnostic_after_relocation(self):
        source = '/original/source [1]/invalid/duplicate.shipping'
        diag = {'label': 'shipping', 'line': 1, 'column': 21,
                'message_contains': 'duplicate setting'}
        for label in ('shipping', source):
            fixture_diagnostic((label + ':1:21: duplicate setting\n').encode(), diag, source)
        for label, line, column, message in [
                ('/other/source/duplicate.shipping', 1, 21, 'duplicate setting'),
                ('/original/source 1/invalid/duplicate.shipping', 1, 21, 'duplicate setting'),
                (source, 2, 21, 'duplicate setting'),
                (source, 1, 20, 'duplicate setting'),
                (source, 1, 21, 'tool unavailable')]:
            with self.subTest(label=label, line=line, column=column), self.assertRaisesRegex(
                    RuntimeError, 'located diagnostic expectation failed'):
                fixture_diagnostic(f'{label}:{line}:{column}: {message}\n'.encode(), diag, source)

    def test_relocated_self_hosting_validation(self):
        # The original equal-text reproducer must be rejected, even relocated.
        self.check_self_hosting(generations=False)

    def test_source_bound_generations(self):
        # Synthetic command records test validation only, not real fixed points.
        self.check_self_hosting(generations=True)

    def check_self_hosting(self, generations):
        scratch = ROOT.parent / 'scratch'
        scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            original = Path(temporary) / 'original'
            original.mkdir()
            roles = {'llvm-1': 'llvm/one.ll', 'llvm-2': 'llvm/two.ll',
                     'reader-ast-1': 'ast/one.ast', 'reader-ast-2': 'ast/two.ast',
                     'suite-log': 'suite.stdout', 'composed-route-log': 'route.stdout'}
            for role, relative in roles.items():
                path = original / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('aggregation fixture\n')
            stages = []
            for name, first, second in [('llvm-fixed-point', 'llvm-1', 'llvm-2'),
                                        ('reader-ast-fixed-point', 'reader-ast-1', 'reader-ast-2')]:
                stages.append({'name': name, 'command': ['cmp', str(original / roles[first]),
                                                       str(original / roles[second])],
                               'cwd': str(original), 'stdout': 'compare.stdout', 'stderr': 'compare.stderr',
                               'exit': 0, 'expected_exit': 0})
            for name, command, role in [
                    ('full-suites', ['make', 'test-all'], 'suite-log'),
                    ('composed-author-route', ['python3', '-B', 'test/reader_author/route.py',
                                               '--case', 'shipping'], 'composed-route-log')]:
                stages.append({'name': name, 'command': command, 'cwd': str(original),
                               'stdout': roles[role], 'stderr': 'compare.stderr', 'exit': 0, 'expected_exit': 0})
            current = {'head': 'a' * 40, 'sha256': {
                p: 'b' * 64 for p in [*COMPILER_INPUTS, 'src/lang_reader.lang',
                                     'scripts/lang_package.py', 'scripts/package_kit.py']
                if p != 'out/version_info.lang'}}
            tool = {'path': sys.executable, 'sha256': sha(sys.executable)}
            if generations:
                roles.update({'source-build': 'build.json', 'compiler-1': 'bin/one', 'compiler-2': 'bin/two'})
                for role in ('compiler-1', 'compiler-2'):
                    path = original / roles[role]
                    path.parent.mkdir(exist_ok=True)
                    path.write_bytes(b'\x7fELF synthetic compiler fixture')
                dump(original / roles['source-build'], {
                    'mode': 'build', 'source': {'revision': current['head'], 'dirty': False,
                                               'inputs': current['sha256']},
                    'compiler': {'sha256': sha(original / roles['compiler-1']),
                                 'bytes': (original / roles['compiler-1']).stat().st_size}})
                generation_stages = []

                def stage(name, command):
                    generation_stages.append({
                        'name': name, 'command': command, 'cwd': '/old/source-checkout',
                        'environment': {'LANGBE': 'llvm', 'LANGOS': 'linux'},
                        'stdout': 'compare.stdout', 'stderr': 'compare.stderr', 'exit': 0, 'expected_exit': 0})

                def path(role):
                    return str(original / roles[role])

                stage('build-current-sources', ['make', 'build'])
                stage('llvm-generation-1', [path('compiler-1'), *COMPILER_INPUTS, '-o', path('llvm-1')])
                stage('link-generation-2', [tool['path'], '-O2', path('llvm-1'), '-o', path('compiler-2')])
                stage('llvm-generation-2', [path('compiler-2'), *COMPILER_INPUTS, '-o', path('llvm-2')])
                for number in (1, 2):
                    stage('reader-ast-generation-' + str(number), [path('compiler-' + str(number)),
                          'src/lang_reader.lang', '--emit-expanded-ast', '-o', path('reader-ast-' + str(number))])
                stages = generation_stages + stages
            for stream in ('compare.stdout', 'compare.stderr'):
                (original / stream).write_bytes(b'')
            dump(original / 'stages.json', stages)
            inventory = {str(p.relative_to(original)): artifact(original, p)
                         for p in original.rglob('*') if p.is_file()}
            value = {'schema': 'lang-author-path/1', 'source': current,
                     'kind': 'self-hosting', 'producer': 'unit-test', 'inventory': inventory,
                     'tools': dict.fromkeys(('python3', 'git', 'make', 'clang', 'ld'), tool),
                     'stages': inventory['stages.json'],
                     'artifacts': {role: inventory[path] for role, path in roles.items()}}
            relocated = Path(temporary) / 'relocated'
            shutil.copytree(original, relocated)
            if not generations:
                with self.assertRaisesRegex(RuntimeError, 'missing source-bound compiler generations'):
                    validate(relocated, value, current)
                return
            self.assertEqual(validate(relocated, value, current), ('self-hosting',))

            def check_changed(rows, message):
                changed = copy.deepcopy(value)
                dump(relocated / 'changed-stages.json', rows)
                record = artifact(relocated, relocated / 'changed-stages.json')
                changed['stages'] = record
                changed['inventory']['changed-stages.json'] = record
                with self.assertRaisesRegex(RuntimeError, message):
                    validate(relocated, changed, value['source'])

            for index in (6, 7):
                rows = copy.deepcopy(stages)
                rows[index]['command'][1:] = rows[index]['command'][1:][::-1]
                check_changed(rows, 'recorded artifact path mismatch')
            rows = copy.deepcopy(stages)
            rows[7]['command'][1:] = [str(Path(temporary) / 'other' / roles[role])
                                      for role in ('reader-ast-1', 'reader-ast-2')]
            check_changed(rows, 'different receipt directories')
            rows = copy.deepcopy(stages)
            rows[6]['command'].append('unexpected')
            check_changed(rows, 'missing observed fixed-point comparison')
            rows = copy.deepcopy(stages)
            rows[7]['exit'] = 1
            check_changed(rows, 'command expectation failed')

            for index in range(6):
                rows = copy.deepcopy(stages)
                del rows[index]
                check_changed(rows, 'missing .*command|missing ordered compiler generation')
            for index in (1, 3, 4, 5):
                rows = copy.deepcopy(stages)
                rows[index]['command'][-1] = str(original / 'unrelated-output')
                check_changed(rows, 'recorded artifact path mismatch')
                rows = copy.deepcopy(stages)
                rows[index]['command'][0] = str(original / roles['compiler-2' if index in (1, 4) else 'compiler-1'])
                check_changed(rows, 'recorded artifact path mismatch')
            rows = copy.deepcopy(stages)
            rows[3]['command'][1] = 'unrelated.lang'
            check_changed(rows, 'compiler generation command mismatch')
            rows = copy.deepcopy(stages)
            rows[4]['command'][1] = 'unrelated-reader.lang'
            check_changed(rows, 'compiler generation command mismatch')
            rows = copy.deepcopy(stages)
            rows[1]['cwd'] = '/other/source-checkout'
            check_changed(rows, 'missing ordered compiler generation')
            rows = copy.deepcopy(stages)
            rows[3]['environment']['LANGBE'] = 'wasm'
            check_changed(rows, 'compiler generation environments differ')
            rows = copy.deepcopy(stages)
            rows[2]['command'][2] = str(original / 'unrelated.ll')
            check_changed(rows, 'recorded artifact path mismatch')
            rows = copy.deepcopy(stages)
            rows[3], rows[6] = rows[6], rows[3]
            check_changed(rows, 'comparison precedes compiler generation')

            build = json.loads((relocated / roles['source-build']).read_text())
            for mutation in ('stale', 'dirty', 'missing-input', 'changed-input', 'package-input', 'compiler'):
                changed_build = copy.deepcopy(build)
                if mutation == 'stale':
                    changed_build['source']['revision'] = '0' * 40
                elif mutation == 'dirty':
                    changed_build['source']['dirty'] = True
                elif mutation == 'missing-input':
                    del changed_build['source']['inputs']['src/parser.lang']
                elif mutation == 'changed-input':
                    changed_build['source']['inputs']['src/parser.lang'] = '0' * 64
                elif mutation == 'package-input':
                    del changed_build['source']['inputs']['scripts/package_kit.py']
                else:
                    changed_build['compiler']['sha256'] = '0' * 64
                changed = copy.deepcopy(value)
                dump(relocated / 'changed-build.json', changed_build)
                record = artifact(relocated, relocated / 'changed-build.json')
                changed['artifacts']['source-build'] = record
                changed['inventory']['changed-build.json'] = record
                with self.subTest(mutation=mutation), self.assertRaisesRegex(
                        RuntimeError, 'current source build'):
                    validate(relocated, changed, current)


if __name__ == '__main__':
    unittest.main()
