#!/usr/bin/env python3
"""Regenerate real-compiler panels and execute the tutorial from the docs."""
import html
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('maker', ROOT / 'web/generate_language_maker.py')
maker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(maker)
compiler = str(Path(os.environ.get('COMPILER', './out/lang_next')).resolve())
maker.generate(compiler, check=True)
source = maker.tutorial_source()
assert len(source.splitlines()) < 100
assert html.escape(source.rstrip()) in (ROOT / 'web/readers.html').read_text()
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    reader, program = root / 'tiny.lang', root / 'answer.tiny'
    reader.write_text(source)
    program.write_text('answer 42\n')
    env = {**os.environ, 'LANGBE': 'llvm', 'LANG_CACHE': str(root / 'cache')}
    result = subprocess.run([compiler, 'run', str(reader), str(program)], cwd=ROOT, env=env, capture_output=True, text=True)
    assert result.returncode == 42, result.stdout + result.stderr
    program.write_text('answer 42 ignored tokens\n')
    result = subprocess.run([compiler, 'run', str(reader), str(program)], cwd=ROOT, env=env, capture_output=True, text=True)
    assert result.returncode not in (0, 42), result.stdout + result.stderr
    assert 'end of input' in result.stderr, result.stderr
print(f'PASS three real-compiler trace panels regenerate; first docs reader ({len(source.splitlines())} lines) runs to 42 and rejects trailing tokens')
