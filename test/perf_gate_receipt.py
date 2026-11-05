#!/usr/bin/env python3
"""Bounded receipt protocol tests and fake-executor request benchmark."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import contextlib
import io
import json
import multiprocessing
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import gate_receipt as gate


def request(root, cache, *, fail=False, mutate=False, fresh=False):
    root, cache = Path(root), Path(cache)
    def identity():
        return {'candidate': 'candidate', 'source': (root / 'source.lang').read_text(),
                'toolchain': 'fake-v1', 'options': ['llvm'], 'tests': ['all-required']}
    def execute(log):
        with (cache / 'executions').open('a') as count:
            count.write('executed\n')
        log.write(b'complete fake verification\n')
        (root / 'result').write_text('verified')
        if mutate:
            (root / 'source.lang').write_text('changed while running')
        return 1 if fail else 0
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return gate.consume(root, cache, identity, execute, ['result'], fresh=fresh)


def concurrent_request(args):
    return request(*args)


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name) / 'first'
        self.root.mkdir()
        (self.root / 'source.lang').write_text('func main() i64 { return 0; }')
        self.cache = Path(self.work.name) / 'cache'

    def count(self):
        return len((self.cache / 'executions').read_text().splitlines())

    def receipt(self):
        return next(self.cache.glob('*/receipt.json'))

    def test_equivalent_checkouts_restore_outputs_once(self):
        self.assertEqual(request(self.root, self.cache), 0)
        other = Path(self.work.name) / 'second'
        other.mkdir()
        (other / 'source.lang').write_text((self.root / 'source.lang').read_text())
        self.assertEqual(request(other, self.cache), 0)
        self.assertEqual((other / 'result').read_text(), 'verified')
        self.assertEqual(self.count(), 1)

    def test_changed_source_executes(self):
        request(self.root, self.cache)
        (self.root / 'source.lang').write_text('changed')
        self.assertEqual(request(self.root, self.cache), 0)
        self.assertEqual(self.count(), 2)

    def test_failed_and_incomplete_receipts_never_reuse(self):
        self.assertEqual(request(self.root, self.cache, fail=True), 1)
        self.assertEqual(request(self.root, self.cache), 0)
        self.assertEqual(self.count(), 2)
        for value in ({'status': 'incomplete'}, {'status': 'failed'}, [], '{broken'):
            self.receipt().write_text(value if isinstance(value, str) else json.dumps(value))
            self.assertEqual(request(self.root, self.cache), 0)
        self.assertEqual(self.count(), 6)

    def test_corrupt_artifact_or_log_executes(self):
        request(self.root, self.cache)
        entry = self.receipt().parent
        (entry / 'files/result').write_text('corrupt')
        request(self.root, self.cache)
        (entry / 'execution.log').write_text('corrupt')
        request(self.root, self.cache)
        self.assertEqual(self.count(), 3)

    def test_edit_during_execution_is_not_success(self):
        self.assertEqual(request(self.root, self.cache, mutate=True), 1)
        self.assertEqual(json.loads(self.receipt().read_text())['status'], 'failed')
        request(self.root, self.cache)
        self.assertEqual(self.count(), 2)

    def test_force_fresh_does_not_reuse_success(self):
        request(self.root, self.cache)
        request(self.root, self.cache, fresh=True)
        self.assertEqual(self.count(), 2)

    def test_concurrent_consumers_execute_once(self):
        with ProcessPoolExecutor(max_workers=2, mp_context=multiprocessing.get_context('fork')) as pool:
            self.assertEqual(list(pool.map(concurrent_request, [(self.root, self.cache)] * 2)), [0, 0])
        self.assertEqual(self.count(), 1)

    def test_input_closure_candidate_tools_options_and_suite(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Test',
                        '-c', 'user.email=test@example.com', 'commit', '--allow-empty', '-qm', 'Fixture'], check=True)
        (self.root / 'test').mkdir()
        fixture = self.root / 'test/required.lang'
        fixture.write_text('test')
        command = ['make', '_verify-complete']
        first = gate.identity(self.root, command)
        self.assertTrue(first['tools']['python3']['sha256'])
        self.assertNotEqual(first, gate.identity(self.root, command + ['JOBS=1']))
        fixture.write_text('changed test')
        self.assertNotEqual(first, gate.identity(self.root, command))
        fixture.write_text('test')
        with mock.patch.dict(os.environ, {'LANGOS': 'other'}):
            self.assertNotEqual(first, gate.identity(self.root, command))
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Test',
                        '-c', 'user.email=test@example.com', 'commit', '--allow-empty', '-qm', 'Next'], check=True)
        self.assertNotEqual(first, gate.identity(self.root, command))

    def test_identity_changes_never_reuse(self):
        base = {'candidate': 'first', 'toolchain': 'clang-a',
                'options': ['llvm'], 'required_tests': ['suite-a']}
        self.cache.mkdir()
        def execute(log):
            with (self.cache / 'executions').open('a') as count:
                count.write('executed\n')
            (self.root / 'result').write_text('done')
            return 0
        with contextlib.redirect_stdout(io.StringIO()):
            gate.consume(self.root, self.cache, lambda: base, execute, ['result'])
            for field in base:
                changed = dict(base, **{field: 'different'})
                gate.consume(self.root, self.cache, lambda: changed, execute, ['result'])
        self.assertEqual(self.count(), 5)

    def test_relocated_build_receipt_and_executable_mode(self):
        other = Path(self.work.name) / 'second'
        other.mkdir()
        identity = lambda: {'candidate': 'same', 'closure': 'same'}
        def execute(log):
            path = self.root / 'out/verify-receipt.json'
            path.parent.mkdir()
            path.write_text(json.dumps({'compiler': str(self.root / 'result')}))
            (self.root / 'result').write_text('executable')
            (self.root / 'result').chmod(0o755)
            return 0
        outputs = ['result', 'out/verify-receipt.json']
        with contextlib.redirect_stdout(io.StringIO()):
            gate.consume(self.root, self.cache, identity, execute, outputs)
            def unexpected(log):
                self.fail('equivalent consumer executed')
            gate.consume(other, self.cache, identity, unexpected, outputs)
        self.assertEqual(json.loads((other / outputs[1]).read_text())['compiler'], str(other / 'result'))
        self.assertEqual((other / 'result').stat().st_mode & 0o777, 0o755)

    def init_git(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Test',
                        '-c', 'user.email=test@example.com', 'commit', '--allow-empty', '-qm', 'Fixture'], check=True)

    def test_external_makefiles_content_identity(self):
        self.init_git()
        external = Path(self.work.name) / 'external.mk'
        external.write_text('include prerequisite.mk\n')
        with mock.patch.dict(os.environ, {'MAKEFILES': str(external)}), mock.patch.object(gate.shutil, 'which', return_value=None):
            first = gate.identity(self.root, ['make', '_verify-complete'])
            external.write_text('include different.mk\n')
            self.assertNotEqual(first, gate.identity(self.root, ['make', '_verify-complete']))

    def test_external_makefiles_never_consume_or_publish(self):
        external = Path(self.work.name) / 'external.mk'
        prerequisite = Path(self.work.name) / 'prerequisite'
        external.write_text('external make rules')
        prerequisite.write_text('first')
        old = Path.cwd()
        try:
            os.chdir(self.root)
            with mock.patch.dict(os.environ, {'MAKEFILES': str(external), 'LANG_VERIFY_CACHE': str(self.cache)}), mock.patch.object(sys, 'argv', ['gate_receipt.py', '--', 'make', '_verify-complete']), mock.patch.object(gate, 'consume', side_effect=AssertionError('external closure cached')), mock.patch.object(gate.subprocess, 'run') as run:
                run.return_value.returncode = 0
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(gate.main(), 0)
                    prerequisite.write_text('changed')
                    self.assertEqual(gate.main(), 0)
                self.assertEqual(run.call_count, 2)
                self.assertFalse(self.cache.exists())
        finally:
            os.chdir(old)

    def test_jobserver_transport_normalized_but_options_preserved(self):
        self.init_git()
        command = ['make', '_verify-complete']
        with mock.patch.object(gate.shutil, 'which', return_value=None):
            def identity(flags):
                with mock.patch.dict(os.environ, {'MAKEFLAGS': flags, 'MFLAGS': flags}):
                    return gate.identity(self.root, command)
            first = identity('-j2 --jobserver-auth=fifo:/tmp/GMfifo1')
            self.assertEqual(first, identity('-j2 --jobserver-auth=fifo:/tmp/GMfifo2'))
            self.assertEqual(first, identity('-j2 --jobserver-auth=3,4'))
            self.assertEqual(first, identity('-j2 --jobserver-fds=7,8'))
            self.assertNotEqual(first, identity('-j3 --jobserver-auth=3,4'))
            self.assertNotEqual(first, identity('-j2 -n --jobserver-auth=3,4'))

    def test_make_override_cannot_skip_verification(self):
        text = (Path(__file__).resolve().parents[1] / 'Makefile').read_text()
        recipe = text.split('bootstrap-verify:\n', 1)[1].split('\n\n', 1)[0]
        # Run the real launcher recipe against a bounded replacement verifier.
        (self.root / 'scripts').mkdir()
        (self.root / 'scripts/gate_receipt.py').write_text(
            'import subprocess, sys\nsys.exit(subprocess.call(sys.argv[2:]))\n')
        (self.root / 'Makefile').write_text('bootstrap-verify:\n' + recipe +
            '\n_verify-complete:\n\t@echo executed >> executions\n\t@test "$(MAKE)" = make\n')
        result = subprocess.run(['make', 'bootstrap-verify', 'MAKE=true'], cwd=self.root,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.root / 'executions').read_text(), 'executed\n')

    def launcher_fixture(self):
        text = (Path(__file__).resolve().parents[1] / 'Makefile').read_text()
        recipe = text.split('bootstrap-verify:\n', 1)[1].split('\n\n', 1)[0]
        (self.root / 'scripts').mkdir()
        (self.root / 'scripts/gate_receipt.py').write_text(
            Path(gate.__file__).read_text())
        (self.root / 'Makefile').write_text('bootstrap-verify:\n' + recipe +
            '\n_verify-complete:\n\t@echo executed >> executions\n'
            '\t@cat $(BOOTSTRAP_LL) > result\n\t@test "$(FAIL)" != 1\n')
        env = {k: v for k, v in os.environ.items()
               if k not in ('MAKEFLAGS', 'MFLAGS', 'GNUMAKEFLAGS', 'MAKEOVERRIDES', 'MAKEFILES')}
        env['LANG_VERIFY_CACHE'] = str(self.cache)
        return env

    def test_external_input_override_executes_after_edit_without_receipts(self):
        env = self.launcher_fixture()
        external = Path(self.work.name) / 'external.ll'
        for index, content in enumerate(('first', 'changed'), 1):
            external.write_text(content)
            result = subprocess.run(['make', 'bootstrap-verify', 'BOOTSTRAP_LL=' + str(external)],
                                    cwd=self.root, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual((self.root / 'result').read_text(), content)
            self.assertEqual(len((self.root / 'executions').read_text().splitlines()), index)
            self.assertFalse(self.cache.exists())

    def test_directory_symlink_through_verify_never_reuses(self):
        env = self.launcher_fixture()
        self.init_git()
        (self.root / '.gitignore').write_text('out/\nstd/os.lang\n')
        external = Path(self.work.name) / 'external'
        external.mkdir()
        (self.root / 'std').mkdir()
        (self.root / 'std/external').symlink_to(external, target_is_directory=True)
        outputs = gate.OUTPUTS + ['out/bootstrap_verify/' + name for name in (
            'ctrusted', 'kernel1', 'kernel1.ll', 'kernel2', 'kernel2.ll',
            'kernel3.ll', 'reader_ast1.ast', 'reader_ast2.ast')]
        (self.root / 'fake.py').write_text(
            'from pathlib import Path\n'
            'data = Path("std/external/input.lang").read_text()\n'
            'for name in ' + repr(outputs) + ':\n'
            '    p = Path(name)\n'
            '    p.parent.mkdir(parents=True, exist_ok=True)\n'
            '    p.write_text(data)\n')
        makefile = self.root / 'Makefile'
        recipe = makefile.read_text().split('_verify-complete:', 1)[0]
        makefile.write_text(recipe + '_verify-complete:\n'
            '\t@echo executed >> out/executions\n\t@python3 fake.py\n'
            '\n.PHONY: verify\nverify: bootstrap-verify\n')
        for index, content in enumerate(('original', 'changed'), 1):
            (external / 'input.lang').write_text(content)
            result = subprocess.run(['make', 'verify'], cwd=self.root, env=env,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('verification receipt reuse disabled', result.stdout)
            self.assertNotIn('Completed verification receipt reused', result.stdout)
            self.assertEqual((self.root / outputs[0]).read_text(), content)
            self.assertEqual(len((self.root / 'out/executions').read_text().splitlines()), index)
            self.assertFalse(list(self.cache.glob('*/receipt.json')))

    def test_replaced_clang_override_through_launcher_never_reuses(self):
        env = self.launcher_fixture()
        self.init_git()
        (self.root / '.gitignore').write_text('out/\nstd/os.lang\n')
        compiler = Path(self.work.name) / 'clang-override'
        env['CLANG'] = str(compiler)
        outputs = gate.OUTPUTS + ['out/bootstrap_verify/' + name for name in (
            'ctrusted', 'kernel1', 'kernel1.ll', 'kernel2', 'kernel2.ll',
            'kernel3.ll', 'reader_ast1.ast', 'reader_ast2.ast')]
        (self.root / 'fake.py').write_text(
            'import os, subprocess\nfrom pathlib import Path\n'
            'data = subprocess.check_output([os.environ["CLANG"]])\n'
            'for name in ' + repr(outputs) + ':\n'
            '    p = Path(name)\n'
            '    p.parent.mkdir(parents=True, exist_ok=True)\n'
            '    p.write_bytes(data)\n')
        makefile = self.root / 'Makefile'
        recipe = makefile.read_text().split('_verify-complete:', 1)[0]
        makefile.write_text(recipe + '_verify-complete:\n'
            '\t@echo executed >> out/executions\n\t@python3 fake.py\n')
        for index, content in enumerate(('original', 'changed'), 1):
            compiler.write_text('#!/bin/sh\necho ' + content + '\n')
            compiler.chmod(0o755)
            result = subprocess.run(['make', 'bootstrap-verify'], cwd=self.root,
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual((self.root / outputs[0]).read_text(), content + '\n')
            self.assertEqual(len((self.root / 'out/executions').read_text().splitlines()), index)
        self.assertIn('CLANG override', result.stdout)
        self.assertNotIn('Completed verification receipt reused', result.stdout)
        self.assertFalse(list(self.cache.glob('*/receipt.json')))

    def test_dangling_symlink_fails_closed(self):
        self.init_git()
        (self.root / 'test').mkdir()
        (self.root / 'test/input').symlink_to(self.root / 'missing')
        with self.assertRaises(gate.UnsupportedInputClosure):
            gate.identity(self.root, ['make', '_verify-complete'])

    def test_cyclic_directory_symlink_fails_closed(self):
        self.init_git()
        (self.root / 'test').mkdir()
        (self.root / 'test/cycle').symlink_to(self.root)
        with self.assertRaises(gate.UnsupportedInputClosure):
            gate.identity(self.root, ['make', '_verify-complete'])

    def test_inherited_ignore_errors_never_executes_or_publishes(self):
        env = self.launcher_fixture()
        for flags in (['-i'], ['--ignore-errors'], ['-ki']):
            with self.subTest(flags=flags):
                result = subprocess.run(['make', *flags, 'bootstrap-verify', 'FAIL=1'],
                                        cwd=self.root, env=env, capture_output=True, text=True)
                self.assertIn('cannot certify verification', result.stderr)
                self.assertFalse((self.root / 'executions').exists())
                self.assertFalse(self.cache.exists())

    def test_make_policy_rejects_modes_and_bypasses_external_closures(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            command = ['make', '_verify-complete']
            for name in ('MAKEFLAGS', 'MFLAGS', 'GNUMAKEFLAGS'):
                for flags in ('i', '-ki', '--ignore-errors', 'n', 'q', 't'):
                    with mock.patch.dict(os.environ, {name: flags}):
                        with self.assertRaises(ValueError):
                            gate.make_policy(command)
                for flags in ('e', '--eval=x', '--file=external.mk', 'BOOTSTRAP_LL=/external.ll'):
                    with mock.patch.dict(os.environ, {name: flags}):
                        self.assertFalse(gate.make_policy(command))
            self.assertTrue(gate.make_policy(command))
            with mock.patch.dict(os.environ, {'MAKEOVERRIDES': 'COMPILER_READERS=/external.lang'}):
                self.assertFalse(gate.make_policy(command))

    def test_production_boundary_preserves_full_suite_and_promotion(self):
        text = (Path(__file__).resolve().parents[1] / 'Makefile').read_text()
        verifier = text.split('_verify-complete: generate-os-layer generate-version-info\n', 1)[1].split('# Non-promoting', 1)[0]
        for proof in ('diff -q $(BOOTSTRAP_VERIFY_DIR)/kernel2.ll',
                      'diff -q $(BOOTSTRAP_VERIFY_DIR)/reader_ast1.ast',
                      'COMPILER=$(BOOTSTRAP_VERIFY_DIR)/kernel2 ./test/run_llvm_suite.sh',
                      'scripts/build_receipt.py finish'):
            self.assertIn(proof, verifier)
        promotion = text.split('\nbootstrap:', 1)[1].split('\nbootstrap-local:', 1)[0]
        self.assertNotIn('gate_receipt', promotion)
        self.assertIn('./test/run_llvm_suite.sh', promotion)
        baseline = (Path(__file__).resolve().parent / 'run_baseline.py').read_text()
        self.assertIn("LANG_VERIFY_FRESH='1'", baseline)


def benchmark(requests):
    with tempfile.TemporaryDirectory() as work:
        root = Path(work) / 'repo'
        root.mkdir()
        (root / 'source.lang').write_text('small fixture')
        cache = Path(work) / 'cache'
        start = resource.getrusage(resource.RUSAGE_SELF)
        for _ in range(requests):
            if request(root, cache):
                raise RuntimeError('fake verification failed')
        end = resource.getrusage(resource.RUSAGE_SELF)
        executions = len((cache / 'executions').read_text().splitlines())
        print(json.dumps({'requests': requests, 'completed_verification_executions': executions,
                          'cpu_seconds': end.ru_utime + end.ru_stime - start.ru_utime - start.ru_stime,
                          'scope': 'fake executor; no bootstrap or compiler speedup claim'}))
        return 0 if executions == 1 else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark', action='store_true')
    parser.add_argument('--requests', type=int, default=2)
    args = parser.parse_args()
    if not 1 <= args.requests <= 100:
        parser.error('requests must be 1..100')
    if args.benchmark:
        sys.exit(benchmark(args.requests))
    unittest.main(argv=[sys.argv[0]], verbosity=2)
