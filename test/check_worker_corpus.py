#!/usr/bin/env python3
"""Adversarial regressions for the test-only corpus and its independent observers."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
import run_worker_confinement as corpus


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output == corpus.ROOT or corpus.ROOT in output.parents:
        parser.error('evidence must be outside the checkout')
    output.mkdir(parents=True, exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix='observer-regressions-', dir=output))
    data = corpus.load_contract()
    rows = []
    for attack in sorted(corpus.AUTHORITY):
        folder = output / ('lying-' + attack)
        folder.mkdir()
        observed = corpus.execute(data['C'], attack, 'permissive', folder, 'lie')
        corpus.require(observed['status'] == 'authority-escaped',
                       f'lying worker concealed {attack}')
        corpus.require(b'authority-denied' in (folder / 'stdout.bin').read_bytes(),
                       'mutation must actually claim denial')
        corpus.require(observed['reaped'] and observed['group_empty'], 'cleanup failed')
        if attack == 'process':
            corpus.require(observed['reaped_descendants'], 'descendant was not reaped')
        rows.append(dict(probe='lying-' + attack, observed=observed))
        print('PASS independent observer rejects lying ' + attack, flush=True)
    for attack in ['filesystem-read', 'environment']:
        folder = output / ('denied-' + attack)
        folder.mkdir()
        observed = corpus.execute(data['C'], attack, 'permissive', folder, 'denied')
        corpus.require(observed['worker_exit'] == 1, 'expected an actual failing attempt')
        corpus.require(observed['status'] == 'authority-denied', 'real denial rejected')
        corpus.require(observed['reaped'] and observed['group_empty'], 'cleanup failed')
        rows.append(dict(probe='denied-' + attack, observed=observed))
        print('PASS independent observer accepts actual absent ' + attack, flush=True)

    # Mutate the expected result, rather than mirror the supervisor's logic.
    # Both -O and PYTHONOPTIMIZE must still reject a broken reference contract.
    for mode, flags, optimize in [('normal', [], ''), ('optimized', ['-O'], ''),
                                   ('environment', [], '1')]:
        folder = output / mode
        program = (
            'import sys; sys.dont_write_bytecode=True; '
            'sys.path.insert(0,"test"); '
            'from pathlib import Path; import run_worker_confinement as c; '
            'data=c.load_contract(); data["cases"][0]["expected"]="mutated"; '
            'c.self_test(data,Path(sys.argv[1]))'
        )
        with (output / (mode + '.log')).open('wb') as log:
            result = subprocess.run([sys.executable, *flags, '-c', program, str(folder)],
                                    cwd=corpus.ROOT, stdout=log, stderr=subprocess.STDOUT,
                                    env=dict(os.environ, PYTHONOPTIMIZE=optimize), timeout=60)
        corpus.require(result.returncode == 1, mode + ' accepted the mutated oracle')
        corpus.require('reference contract model failed' in
                       (output / (mode + '.log')).read_text(), 'wrong mutation failure')
        rows.append(dict(probe='mutated-oracle-' + mode, exit_code=result.returncode))
        print('PASS mutated oracle fails in ' + mode + ' Python', flush=True)
    (output / 'receipt.json').write_text(json.dumps(rows, indent=2) + '\n')
    print('PASS observer regressions; evidence: ' + str(output))


if __name__ == '__main__':
    main()
