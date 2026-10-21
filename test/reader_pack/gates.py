#!/usr/bin/env python3
"""Run destructive build recipes in a retained copy of the committed candidate."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('gate', choices=['bootstrap', 'llvm', 'effects', 'wasm', 'publish'])
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
output = args.output.resolve()
assert output != root and root not in output.parents, 'evidence must be outside checkout'
output.mkdir(parents=True, exist_ok=True)
run = Path(tempfile.mkdtemp(prefix=args.gate + '-', dir=output))
repo = run / 'repo'
env = dict(os.environ, JOBS='2', PUBLISH_BOOTSTRAP='0', TMPDIR=str(run / 'tmp'),
           EFFECTS_EVIDENCE_DIR=str(run / 'effects'))
(run / 'tmp').mkdir()
for key in ['LANGBE', 'LANGOS', 'LANG_ROOT', 'LANG_LAYOUT_PROFILE', 'COMPILER']:
    env.pop(key, None)
rows = []


def command(argv, name, cwd=repo, skips=None, tokens=()):
    with (run / (name + '.txt')).open('w') as log:
        result = subprocess.run(argv, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
    text = (run / (name + '.txt')).read_text(errors='replace')
    row = {'command': argv, 'exit': result.returncode, 'log': name + '.txt'}
    rows.append(row)
    (run / 'commands.json').write_text(json.dumps(rows, indent=2) + '\n')
    assert result.returncode == 0, f'{name} failed; see {run / (name + ".txt")}'
    assert all(token in text for token in tokens), f'{name} missing required proof'
    if skips:
        actual = sorted(re.findall(r'^SKIP .+$', text, re.M))
        expected = json.loads((repo / 'test/baseline_skips.json').read_text())[skips]
        assert actual == expected, f'{name} changed skips: {actual}'
    print(f'PASS {name}: {run / (name + ".txt")}', flush=True)


head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
if args.gate == 'publish':
    env['PUBLISHED_REPO'] = 'lang'
    command([str(Path(os.environ['PREPUBLISH_CHECK'])), 'repo', '480e61e'], 'publish', cwd=root.parent)
else:
    command(['git', 'clone', '--no-hardlinks', '--quiet', str(root), str(repo)], 'clone', cwd=root)
    command(['git', 'checkout', '--detach', head], 'candidate')
    if args.gate == 'bootstrap':
        command(['make', 'bootstrap', 'PUBLISH_BOOTSTRAP=0'], 'bootstrap',
                tokens=['LLVM FIXED POINT VERIFIED', 'AST FIXED POINT VERIFIED', 'BOOTSTRAP COMPLETE'], skips='llvm-linux')
    else:
        command(['make', 'init'], 'init')
        command(['make', 'build'], 'current-source-build')
        env['COMPILER'] = str(repo / 'out/lang_next')
        if args.gate == 'llvm':
            command(['test/run_llvm_suite.sh'], 'llvm', skips='llvm-linux', tokens=['All tests passed!'])
        elif args.gate == 'effects':
            command(['python3', 'test/run_effects_safety.py'], 'effects', tokens=['Effects safety: PASS'])
        else:
            for tool in ['clang', 'wasm-ld', 'node']:
                command([tool, '--version'], tool)
            command(['test/run_wasm_suite.sh'], 'wasm', skips='llvm-wasm32', tokens=['0 failed'])
            command(['test/run_direct_wasm.sh'], 'direct-wasm', tokens=['direct wasm: passed'])
            command(['test/run_compiler_wasm.sh'], 'compiler-wasm', tokens=['PASS compiler_wasm_e2e'])
print(f'PASS {args.gate} at {head}; retained {run}')
