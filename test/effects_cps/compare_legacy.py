#!/usr/bin/env python3
"""Compare unflagged LLVM bytes using two legacy compilers on the same source graph."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
os.chdir(root)
compiler = str(Path(os.environ['LEGACY_COMPILER']).resolve())
base = str(Path(os.environ['BASE_COMPILER']).resolve())
evidence = Path(os.environ.get('EFFECTS_LEGACY_EVIDENCE_DIR') or tempfile.mkdtemp(prefix='effects-legacy-')).resolve()
evidence.mkdir(parents=True, exist_ok=True)
programs = sorted(p for p in Path('test/suite').glob('*.lang')
                  if re.search(r'^\s*effect\s|\bperform\s|\bhandle\s*\{', p.read_text(), re.M))
programs += [Path('test/effects/two_performs.lang'), Path('test/effects/two_handlers.lang'), Path('test/effects_o2_twice.lang')]
programs += sorted(Path('test/effects_cps').glob('*.lang'))
rows = []
for source in programs:
    outputs = []
    for label, executable in [('base', base), ('candidate', compiler)]:
        directory = evidence / source.stem / label
        directory.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ, LANGBE='llvm', LANG_CACHE=str(directory / 'cache'))
        ir = directory / 'program.ll'
        result = subprocess.run([executable, str(source), '-o', str(ir)], env=env, capture_output=True, timeout=60)
        (directory / 'compiler.stdout').write_bytes(result.stdout)
        (directory / 'compiler.stderr').write_bytes(result.stderr)
        (directory / 'compiler.exit').write_text(f'{result.returncode}\n')
        if source.stem in ('arity_missing', 'arity_extra'):
            assert result.returncode != 0 and b"function 'worker' takes 1 argument" in result.stderr, (source, label, result.stderr)
            assert not ir.exists(), (source, label, 'refused call published IR')
            outputs.append(result.stderr)
        else:
            assert result.returncode == 0, (source, label, result.stderr)
            outputs.append(ir.read_bytes())
    assert outputs[0] == outputs[1], f'unflagged IR differs for {source}'
    kind = 'diagnostic' if source.stem in ('arity_missing', 'arity_extra') else 'IR'
    rows.append({'source': str(source), 'sha256': hashlib.sha256(outputs[0]).hexdigest(), 'kind': kind, 'verdict': 'identical'})
    print(f'{source}: legacy {kind} byte-for-byte identical')
(evidence / 'results.json').write_text(json.dumps(rows, indent=2) + '\n')
print(f'Legacy comparison: PASS ({len(rows)} programs)')
