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
