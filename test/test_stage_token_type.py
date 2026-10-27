#!/usr/bin/env python3
"""Capability token validation at the host call boundary."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))
from stage_host import Artifact, Host, StageError
from stage_protocol import Value, frame, unframe


class TokenTypeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.host = Host(sys.executable, self.temp.name, controlled_fixtures=True)
        self.artifact = Artifact(Path('unused'), 'digest', ('i64',), 'i64',
                                 self.host.host, Value('descriptor', {}))
        self.host.artifacts['retained-token'] = self.artifact
        self.worker = mock.Mock(return_value=frame(Value('i64', 42), 2))
        self.host.call_hook = self.worker
        self.args = Value('list', [Value('i64', 7)])

    def test_invalid_tokens_do_not_call_worker_or_mutate_artifacts(self):
        # Numeric keys expose bool/int equality as well as merely unknown keys.
        self.host.artifacts[1] = self.artifact
        before = self.host.artifacts.copy()
        for token in ([], {}, True, False, 1, 0, 1.0, b'retained-token', None,
                      'missing-token', 'Retained-token'):
            with self.subTest(token=token):
                self.worker.reset_mock()
                with self.assertRaisesRegex(StageError, '^unknown-artifact$'):
                    self.host.call(token, self.args)
                self.worker.assert_not_called()
                self.assertEqual(self.host.artifacts, before)

    def test_retained_token_and_validation(self):
        before = self.host.artifacts.copy()
        self.assertEqual(self.host.call('retained-token', self.args), Value('i64', 42))
        artifact, request = self.worker.call_args.args
        self.assertIs(artifact, self.artifact)
        self.assertEqual(unframe(request), self.args)
        self.worker.reset_mock()
        with self.assertRaisesRegex(StageError, '^wrong-signature$'):
            self.host.call('retained-token', Value('list', [Value('text', 'bad')]))
        self.worker.assert_not_called()
        self.worker.return_value = frame(Value('text', 'bad'), 2)
        with self.assertRaisesRegex(StageError, '^wrong-result-signature$'):
            self.host.call('retained-token', self.args)
        self.assertEqual(self.host.artifacts, before)


if __name__ == '__main__':
    unittest.main()
