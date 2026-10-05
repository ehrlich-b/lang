#!/usr/bin/env python3
"""Optional scientific figures from the verified native CSV receipts."""
import csv
import json
import os
from pathlib import Path
import sys
import tempfile

cache = tempfile.TemporaryDirectory(prefix='lang-science-plot-')
os.environ.setdefault('MPLCONFIGDIR', str(Path(cache.name) / 'matplotlib'))
os.environ.setdefault('XDG_CACHE_HOME', str(Path(cache.name) / 'fonts'))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

folder = Path(sys.argv[1] if len(sys.argv) > 1 else 'out/hamiltonian')
report = json.loads((folder / 'numerical-report.json').read_text())
assert report['passed'], 'Verify numerical evidence before plotting it'

def rows(path):
    with Path(path).open() as handle:
        return [{k: float(v) for k, v in row.items()} for row in csv.DictReader(handle)]

fig, axes = plt.subplots(2, 2, figsize=(11, 7.5))
harmonic = report['checks']['harmonic']['runs']
h = [run['step'] for run in harmonic]
error = [run['endpoint_error'] for run in harmonic]
axes[0, 0].loglog(h, error, 'o-', label='Native endpoint error')
axes[0, 0].loglog(h, [error[0]*(step/h[0])**2 for step in h], '--', label='h² guide')
axes[0, 0].set(xlabel='Step h', ylabel='Max coordinate/momentum error', title='Harmonic analytic solution, T=3.68')
axes[0, 0].legend()
for run in report['checks']['long_harmonic']['runs']:
    data = rows(run['path']); initial = data[0]['energy']
    axes[0, 1].plot([r['time'] for r in data], [r['energy']-initial for r in data], lw=.65, label=f"h={run['step']}")
axes[0, 1].set(xlabel='Time', ylabel='H(t) − H(0)', title='Sampled harmonic energy error, T=1000')
axes[0, 1].legend()
data = rows(report['checks']['quartic']['path'])
for coordinate in ('x', 'y'):
    axes[1, 0].plot([r['time'] for r in data], [r[f'q_{coordinate}'] for r in data], label=f'q_{coordinate}')
axes[1, 0].set(xlabel='Time', ylabel='Position', title='Coupled quartic trajectory, h=.01')
axes[1, 0].legend()
for name in ('quartic', 'double_well'):
    data = rows(report['checks'][name]['path']); initial = data[0]['energy']
    axes[1, 1].plot([r['time'] for r in data], [(r['energy']-initial)/abs(initial) for r in data], label=name)
axes[1, 1].set(xlabel='Time', ylabel='[H(t) − H(0)] / |H(0)|', title='Nonlinear relative energy error, h=.01')
axes[1, 1].legend()
for ax in axes.flat:
    ax.grid(alpha=.2)
fig.suptitle('Lang-generated Hamiltonian experiments · nondimensional · native ARM64')
fig.tight_layout()
fig.savefig(folder / 'scientific-evidence.png', dpi=160)
fig.savefig(folder / 'scientific-evidence.svg')
if 'coupling_variation' in report['checks']:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for run in report['checks']['coupling_variation']['runs']:
        data = rows(run['path'])
        axes[0].plot([r['time'] for r in data], [r['q_x'] for r in data], label=f"q_x, b={run['coupling']}")
    axes[0].set(xlabel='Time', ylabel='Position', title='Recompile the same model with a changed coupling')
    data = rows(report['checks']['quartic']['path'])
    times = [r['time'] for r in data]
    components = [
        [r['p_x']**2/2.6 + .4*r['q_x']**2 + .15*r['q_x']**4 for r in data],
        [r['p_y']**2/2.6 + .4*r['q_y']**2 + .15*r['q_y']**4 for r in data],
        [.2*r['q_x']**2*r['q_y']**2 for r in data],
    ]
    for values, label in zip(components, ('Ex (excludes interaction)', 'Ey (excludes interaction)', 'Eb (interaction)')):
        axes[1].plot(times, values, label=label)
    axes[1].set(xlabel='Time', ylabel='Component energy', title='Stated decomposition, b=.4; components vary')
    for ax in axes:
        ax.legend(); ax.grid(alpha=.2)
    fig.suptitle('Native coupled quartic · nondimensional · h=.01, T=3.68')
    fig.tight_layout()
    fig.savefig(folder / 'coupling-variation.png', dpi=160)
    fig.savefig(folder / 'coupling-variation.svg')
cache.cleanup()
