#!/usr/bin/env python3
"""Independently verify Wasm output using the existing handwritten science oracle.

No generated AST, force code or solver is imported. Native/browser comparisons
use the frozen O0/O2 tolerance as a numeric portability tolerance, not a claim
that these targets or outputs must be bitwise identical.
"""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import hamiltonian_reference as reference


def verify(manifest):
    checks = {
        'harmonic': reference.analyze_harmonic(manifest['harmonic']),
        'long_harmonic': reference.analyze_long_harmonic(manifest['long_harmonic']),
        'quartic': reference.analyze_nonlinear(manifest['quartic'], 'quartic'),
        'double_well': reference.analyze_nonlinear(manifest['double_well'], 'double_well'),
        'reversal': reference.analyze_reversal(manifest['reversal']),
        'gradients': reference.analyze_gradients(manifest['gradients']),
    }
    if manifest.get('native_browser_pairs'):
        pairs = [reference.analyze_optimization(pair) for pair in manifest['native_browser_pairs']]
        checks['native_browser_trajectories'] = {
            'pairs': pairs, 'passed': all(pair['passed'] for pair in pairs)}
        comparisons = reference.analyze_gradient_optimizations(
            [manifest['gradients'], manifest['native_gradients']])
        checks['native_browser_gradients'] = {
            'maximum_difference': comparisons['maximum_O0_O2_difference'],
            'passed': comparisons['passed'],
            'interpretation': 'Wasm versus native O2; shared numeric portability tolerance'}
    if manifest.get('quartic_changed'):
        checks['quartic_changed'] = reference.analyze_nonlinear(manifest['quartic_changed'], 'quartic_changed')
        checks['coupling_variation'] = reference.analyze_coupling_variation(manifest['quartic'], manifest['quartic_changed'])
    return {
        'target': 'direct-wasm', 'variables': 'nondimensional',
        'oracle': 'independently handwritten derivatives and refined Python RK4',
        'tolerances': reference.TOLERANCES,
        'native_parity_verified': bool(manifest.get('native_browser_pairs')),
        'checks': checks, 'passed': all(check['passed'] for check in checks.values()),
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    report = verify(json.loads(Path(args.manifest).read_text()))
    Path(args.output).write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print('PASS' if report['passed'] else 'FAIL', 'independent direct-Wasm scientific reference')
    raise SystemExit(0 if report['passed'] else 1)
