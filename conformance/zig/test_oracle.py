#!/usr/bin/env python3
"""Check replay compatibility independently of expensive compiler work."""
import argparse
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import oracle


class ReplayTests(unittest.TestCase):
    def test_serial_rerun_preserves_individual_timeout_contract(self):
        with tempfile.TemporaryDirectory(dir=OUTPUT) as temp:
            work = Path(temp)
            source, compiler = work / 'source', work / 'compiler/zig'
            source.mkdir()
            args = argparse.Namespace(work=work / 'reference', source=source, compiler=compiler,
                                      source_archive=work / 'source.tar', compiler_archive=work / 'compiler.tar',
                                      compile_timeout=240, test_timeout=10, mode_timeout=.001,
                                      mode_jobs=1, bounded=False, memory_mib=256, cpus=1,
                                      process_limit=4, receipt=work / 'receipt.json')
            calls = []

            def worker(options):
                calls.append(options.mode)
                self.assertEqual(options.test_timeout, 10)
                self.assertEqual(json.loads(options.declarations.read_text()), [])
                oracle.save(options.work / 'raw.json', {
                    'mode': options.mode, 'compile': {'outcome': 'pass'},
                    'names': [], 'origins': {}, 'instances': []})

            with patch.object(oracle, 'verify_archive', return_value={}), \
                 patch.object(oracle, 'digest', return_value='hash'), \
                 patch.object(oracle, 'inventory', return_value=[]) as inventory, \
                 patch.object(oracle.subprocess, 'check_output', side_effect=lambda command, **kw:
                              oracle.LOCK['version'] if command[-1] == 'version' else '\n debug \n safe \n fast \n'), \
                 patch.object(oracle, 'negative_cases', return_value=[]), \
                 patch.object(oracle, 'mode_worker', side_effect=worker), \
                 patch.object(oracle, 'supervise') as supervise:
                oracle.reference(args)
                oracle.reference(args)
                self.assertEqual(calls, oracle.LOCK['modes'] * 2)
                self.assertEqual(inventory.call_count, 2)
                supervise.assert_not_called()
                self.assertIsNone(json.loads(args.receipt.read_text())['resources'])
                for jobs, bounded in [(1, True), (2, False)]:
                    args.mode_jobs, args.bounded = jobs, bounded
                    supervise.side_effect = RuntimeError('supervised')
                    with self.assertRaisesRegex(RuntimeError, 'supervised'):
                        oracle.reference(args)
                    self.assertEqual(supervise.call_args.args[1], jobs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--work', type=Path, required=True)
    args, remaining = parser.parse_known_args()
    OUTPUT = args.work.resolve()
    OUTPUT.mkdir(parents=True, exist_ok=False)
    unittest.main(argv=[__file__, *remaining])
