#!/usr/bin/env python3
"""Assert exact snippet bytes on small files; retain receipts outside checkout."""
import json
import os
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'test/reader_error_snippet'


def main():
    evidence_root = ROOT.parent / 'evidence'
    evidence_root.mkdir(exist_ok=True)
    evidence = Path(tempfile.mkdtemp(prefix='snippets-', dir=evidence_root))
    scratch_root = ROOT.parent / 'scratch'
    scratch_root.mkdir(exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix='snippets-', dir=scratch_root))
    env = dict(os.environ, LANGBE='llvm', LANG_CACHE=str(scratch / 'cache'))
    receipts = []

    def run(command, name):
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=60)
        (evidence / (name + '.stdout')).write_bytes(result.stdout)
        (evidence / (name + '.stderr')).write_bytes(result.stderr)
        receipts.append({'command': [str(x) for x in command], 'exit': result.returncode, 'name': name})
        (evidence / 'commands.json').write_text(json.dumps(receipts, indent=2) + '\n')
        assert result.returncode == 0, (name, result.stderr)
        return result

    compiler = Path(os.environ.get('COMPILER', ROOT / 'out/lang')).resolve()
    run([compiler, FIXTURES / 'driver.lang', '-o', scratch / 'driver.ll'], 'compile')
    run(['clang', '-O0', scratch / 'driver.ll', '-o', scratch / 'driver'], 'link')
    cases = [
        ('lf', 'oops', b"fixture:2:5: expected '=', found oops @11:15\nkey oops tail\n    ^^^^\n"),
        ('crlf', 'oops', b"fixture:2:5: expected '=', found oops @12:16\nkey oops tail\n    ^^^^\n"),
        ('tab-utf8', 'oops', "fixture:2:5: expected '=', found oops @11:15\n\té oops tail\n\t  ^^^^\n".encode()),
        ('eof', '', b"fixture:2:4: expected '=', found end of input @10:10\nkey\n   ^\n"),
        ('eof-newline', '', b"fixture:2:1: expected '=', found end of input @7:7\n\n^\n"),
        ('utf8-token', 'é', "fixture:2:1: expected '=', found é @7:9\né\n^\n".encode()),
        ('tab-token', '"a\tb"', b"fixture:2:1: expected '=', found \"a\tb\" @7:12\n\"a\tb\"\n^^^^^^^^^^\n"),
        ('tab-token-prefix', '"a\tb"', "fixture:2:5: expected '=', found \"a\tb\" @11:16\n\té \"a\tb\"\n\t  ^^^^^^^^\n".encode()),
    ]
    for name, token, expected in cases:
        command = [scratch / 'driver', FIXTURES / (name + '.source'), token]
        result = run(command + ['snippet'], name)
        assert not result.stdout and result.stderr == expected, (name, expected, result.stderr)
        compact = run(command + ['compact'], name + '-compact')
        assert not compact.stdout and compact.stderr == expected.split(b'\n')[0] + b'\n', name
        print('PASS', name, 'exact three-line snippet and unchanged compact diagnostic')
    result = run([scratch / 'driver', FIXTURES / 'utf8-token.source', 'é', 'fallback'], 'fallback')
    assert result.stderr == "fixture:2:1: expected valid token, found é @7:9\né\n^\n".encode()
    print('PASS fallback without a recorded mismatch')
    print('evidence:', evidence)


if __name__ == '__main__':
    main()
