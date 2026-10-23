#!/usr/bin/env python3
"""Run required numeric gates with retained logs and exact baseline skips."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('gate', choices=['bootstrap', 'llvm', 'effects', 'wasm'])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix=args.gate + '-', dir=args.output)).resolve()
    env = dict(os.environ, JOBS='2', TMPDIR=str(directory / 'tmp'),
               COMPILER=str(ROOT / 'out/lang_next'), LANG_CACHE=str(directory / 'cache'),
               EFFECTS_EVIDENCE_DIR=str(directory / 'effects'))
    (directory / 'tmp').mkdir()
    inventory = json.loads((ROOT / 'test/baseline_skips.json').read_text())

    def run(name, command, cwd=ROOT, skip_key=None):
        with (directory / (name + '.txt')).open('w') as log:
            result = subprocess.run(command, cwd=cwd, env=env, stdout=log,
                                    stderr=subprocess.STDOUT, timeout=850)
        text = (directory / (name + '.txt')).read_text()
        (directory / (name + '.command.json')).write_text(json.dumps({
            'command': command, 'cwd': str(cwd), 'exit': result.returncode}) + '\n')
        assert result.returncode == 0, f'{name} exit {result.returncode}: {directory / (name + ".txt")}'
        if skip_key:
            skips = sorted(re.findall(r'^SKIP .+$', text, re.M))
            assert skips == inventory[skip_key], f'changed {name} skip inventory: {skips}'
        print(f'PASS {name}: {directory / (name + ".txt")}', flush=True)
        return text

    if args.gate == 'bootstrap':
        checkout = directory / 'checkout'
        subprocess.run(['git', 'clone', '--shared', '--quiet', str(ROOT), str(checkout)], check=True)
        env.pop('COMPILER')
        text = run('bootstrap', ['make', 'bootstrap', 'PUBLISH_BOOTSTRAP=0'], checkout,
                   'llvm-linux')
        for marker in ('LLVM FIXED POINT VERIFIED', 'AST FIXED POINT VERIFIED', 'BOOTSTRAP COMPLETE'):
            assert marker in text, f'missing bootstrap milestone {marker}'
    elif args.gate == 'llvm':
        run('llvm', ['test/run_llvm_suite.sh'], skip_key='llvm-linux')
    elif args.gate == 'effects':
        text = run('effects', ['python3', 'test/run_effects_safety.py'])
        assert 'Effects safety: PASS' in text
    else:
        for tool in ('clang', 'wasm-ld', 'node'):
            import shutil
            assert shutil.which(tool), f'required Wasm tool missing: {tool}'
        run('wasm', ['test/run_wasm_suite.sh'], skip_key='llvm-wasm32')
        run('direct-wasm', ['test/run_direct_wasm.sh'])


if __name__ == '__main__':
    main()
