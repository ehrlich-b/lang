# A native Hamiltonian model compiler

Lang can turn a polynomial energy model into a standalone compiler and native
numerical experiment. The `ham` reader differentiates the potential at compile
time, builds specialized force functions, and emits a kick–drift–kick solver
through the shared AST and LLVM backend. The executable contains neither a
runtime expression interpreter nor handwritten model-specific forces.

This first slice is explicitly **nondimensional**. It represents

```
H(q,p) = sum_i p_i^2 / (2*m_i) + V(q)
F_i(q) = -dV/dq_i
```

The fixed-step method is Störmer–Verlet splitting for this separable Hamiltonian.
Its second-order convergence and sampled energy behavior are tested, rather than
assumed. It does not conserve the original energy exactly. See
[Hairer's method notes](https://www.unige.ch/~hairer/poly_geoint/week2.pdf).

## Compile and run in the browser

The local [scientific workbench](../web/science.html) uses this same
reader and runtime: source → compiled reader → shared AST → direct WebAssembly
experiment. Edit the coupling or full potential, inspect generated forces and
solver phases, and export 17-digit CSV, JSON, AST or the compiled module.
Harmonic, coupled quartic and double-well presets are editable models rather
than built-in force implementations. Force probes and two-flip reversal use the
compiled runtime's argument interface.

Compilation and execution run in a cancellable worker. The browser solver host
caps output at 8 MiB and allocation at 256 MiB; a resource failure is reported
instead of offering an incomplete trajectory as a successful export. Saved
drafts stay local, and model files can be reopened. Nondimensional assumptions
and the frozen expression contract below apply to both targets.

`test/hamiltonian_browser_e2e.js` runs the actual packed browser compiler and
reader, with independent analytic/RK4 checks from
`test/hamiltonian_browser_reference.py`. `test/science_browser_ui.py` exercises
the real Chromium page locally or on an explicitly selected deployed URL.

## Write and compile a model

[quartic.ham](../example/hamiltonian/quartic.ham) is the first experiment:

```text
model quartic {
    nondimensional;
    param m = 1.3;
    param k = 0.8;
    param a = 0.6;
    param b = 0.4;
    pair x mass m position 0.7 momentum 0.2;
    pair y mass m position -0.4 momentum 0.3;
    potential = k*(x^2+y^2)/2 + a*(x^4+y^4)/4 + b*x^2*y^2/2;
    run step 0.01 steps 368 sample 1;
}
```

Mint a compiler with its runtime embedded:

```sh
LANGBE=llvm ./out/lang compiler ham example/hamiltonian/hamiltonian.lang \
  --runtime example/hamiltonian/runtime.lang -o /tmp/hamc
experiment_dir=$(mktemp -d)
cp example/hamiltonian/quartic.ham "$experiment_dir/"
cd "$experiment_dir"
/tmp/hamc quartic.ham -o quartic.ll
clang -O2 quartic.ll -o quartic
./quartic > trajectory.csv
./quartic --json > trajectory.json
./quartic --forces 0.7 -0.4
./quartic --reverse > reversal.csv
```

The minted compiler and changed model files work outside the source checkout;
the runtime is expanded and embedded during minting. Change the potential or
coupling and recompile the model. No force or solver edits are needed.
[double_well.ham](../example/hamiltonian/double_well.ham) supplies a second,
algebraically different potential, including a squared polynomial.

Trajectory CSV columns are `step,time,q_NAME...,p_NAME...,energy`. Every numeric
cell uses 17 significant digits. Time is `step*h`, avoiding accumulated-clock
drift. `--forces` emits the coordinates, generated forces, and potential at a
specified point. `--reverse` performs N steps, flips all momenta, performs N
more steps, flips again, and emits the initial and returned full states.

`--json` emits the same sampled trajectory from the native executable:

```json
{
  "schema": "lang.hamiltonian.trajectory.v1",
  "nondimensional": true,
  "method": "velocity-verlet",
  "coordinates": ["x", "y"],
  "masses": [1.3, 1.3],
  "step_size": 0.01,
  "steps": 368,
  "sample_stride": 1,
  "samples": [
    {"step": 0, "time": 0.0, "q": [0.7, -0.4], "p": [0.2, 0.3], "energy": 0.36553499999999994}
  ]
}
```

This shortened example shows the initial sample; successful output includes
every requested sample and the final state. Arrays follow `coordinates` order.
Floating numbers roundtrip to binary64, including signed zero (`-0.0`). Integer
step indices and run metadata stay integers. A failed run exits nonzero and
leaves incomplete output; discard its CSV or JSON rather than treating it as a
complete experiment. JSON output concerns forward trajectories; reversal and
force inspection retain their CSV interfaces.

Inspect the generated potential, forces, source spans, and solver phases:

```sh
./out/lang read example/hamiltonian/hamiltonian.lang \
  example/hamiltonian/quartic.ham -o /tmp/quartic.ast
./out/lang --from-ast /tmp/quartic.ast \
  --runtime example/hamiltonian/runtime.lang -o /tmp/quartic.ll
```

## Frozen language contract

- One to four canonical pairs; each has a positive finite constant mass and
  finite constant initial position and momentum.
- At most 32 constant parameters. Constant initializers support decimal
  literals, previously declared parameters, and unary minus.
- Potentials support coordinates, parameters, decimal constants, parentheses,
  unary minus, `+`, `-`, `*`, powers with literal integer exponents 0–8, and
  division by a proven state-independent, nonzero constant expression.
- Power binds before unary minus; `-x^2` means `-(x^2)`. Power chains require
  parentheses. `x^0` is the polynomial constant 1, including at zero.
- Decimal syntax is digits or digits.digits, with unary minus. Exponents,
  hexadecimal numbers, NaN, infinity, arbitrary functions, momentum-dependent
  potentials, user-defined kinetics, dissipation, constraints, and adaptive
  timesteps are unsupported and produce located errors.
- Input is bounded to 65,536 bytes, 4,096 tokens, 32 nested parentheses,
  32 consecutive unary minuses, and 128 bytes per decimal literal. Compilation
  allows 8,192 polynomial/derivative IR nodes and 65,536 expanded potential/force
  AST nodes. Constant signs are normalized across parameter aliases.
- Step must be positive and finite. Steps and sample stride are integers in
  1–1,000,000; stride cannot exceed steps. The final sample is always emitted.
- Every initial and completed state, energy, and printed force value is checked
  for nonfiniteness. Runtime failure exits 3 with a diagnostic; a CSV emitted
  before failure is an incomplete trajectory.

The expression IR represents a real polynomial with binary64 coefficients.
Zero/one simplification and symbolic differentiation use that algebraic domain;
they do not preserve an unreduced expression's IEEE overflow or signed-zero
operation trace. Shared native `strtod` conversion makes compile-time checks
agree with the binary64 decimal constants LLVM receives. Native execution uses
ordinary binary64 operations without fast-math. A large or unstable step can
still yield a poor finite trajectory: finiteness is not an accuracy guarantee.

## Reproduce the scientific evidence

```sh
python3 test/hamiltonian_e2e.py ./out/lang --output out/hamiltonian
python3 test/hamiltonian_reference.py verify out/hamiltonian/manifest.json \
  --output out/hamiltonian/numerical-report.json
python3 test/hamiltonian_reference.py reference quartic \
  --output out/hamiltonian/rk4-reference.csv
```

The independent Python oracle uses handwritten analytic derivatives and a
separate RK4 implementation. Its tolerances were fixed before observing Lang
trajectories. It checks both optimization levels against those derivatives,
refines its own RK4 timestep, and validates the CSV energy formula at every row.
The native harness first checks positive/negative fractional reader literals,
saved ASTs, and the f64 parameter/return ABI. It then saves each model's generated
force/solver AST and independently rebuilds both optimization levels from that
serialized AST. JSON samples must match CSV values exactly, including signed
zero and a stride that does not divide the final step. Every copied minted
compiler invocation uses a missing `LANG_ROOT` outside the checkout.
`commands.json` preserves actual invocations and durations, including failures;
`evidence.json` records source/compiler and artifact SHA-256 hashes. The full
native aggregate and bootstrap validation include this strengthened scientific gate.
Python's standard library and clang suffice for these tests. Optional plots use
the already installed Matplotlib:

```sh
python3 example/hamiltonian/plot_evidence.py out/hamiltonian
```

Initial Mac ARM64 evidence, with `m=1.3`, `k=.8`, `a=.6`, `b=.4`,
`q=(.7,-.4)`, `p=(.2,.3)`:

| Check | Measured result |
|---|---|
| Harmonic endpoint error at T=3.68, h=.04/.02/.01 | 9.7992e-5 / 2.4498e-5 / 6.1243e-6 |
| Harmonic error ratios | 4.00007 / 4.00002 |
| Maximum harmonic energy error through T=1000, h=.04/.02 | 5.1761e-5 / 1.2941e-5 |
| Corresponding analytic error bounds | 7.6311e-5 / 1.9077e-5 |
| Quartic endpoint / maximum sampled state error, h=.01 | 7.5769e-6 / 1.0936e-5 |
| Double-well endpoint / maximum sampled state error | 1.1205e-5 / 1.5454e-5 |
| Quartic maximum relative energy error through T=3.68 | 1.4665e-5 |
| Two-flip reversal maximum full-state error | 1.1102e-16 |
| Handwritten gradient oracle maximum discrepancy | 4.4409e-16 |
| Observed O0/O2 trajectory and gradient differences | zero in these receipts |

The fine RK4 endpoint error estimates are approximately 1e-12 after three
refinement levels. These are numerical estimates, not rigorous error bounds.
The maintained experiment also edits only `b` from `.4` to `.9`, recompiles,
and checks the changed gradients and trajectory against the handwritten RK4
oracle under the same frozen tolerances. At h=.01, T=3.68, the changed run has
maximum sampled state error 1.2281e-5 and maximum relative energy error
1.6138e-5. The two trajectories differ by up to .13450 in sampled state.
The report describes energy exchange with the explicit decomposition
`Ex=px²/(2m)+kx²/2+ax⁴/4`, `Ey=py²/(2m)+ky²/2+ay⁴/4`, and
`Eb=bx²y²/2`. At b=.4 their sampled ranges are .022400, .021125, and .019489;
these components are not separately conserved. The optional plots include
both the coupling edit and this decomposition.
The test also exercises four unequal masses, free motion, exponent boundaries,
decimal cancellation, invalid models, bounded expansion, and explicit runtime
overflow. Independent review additionally used an unfamiliar three-coordinate
potential and checked force generation and standalone portability.

Evidence concerns these models, horizons, and timesteps. It does not establish
physics novelty, chaotic behavior, or a conservation theorem. This deliverable
targets native LLVM and direct Wasm. Dimensions and generalized symbolic
algebra remain outside the slice. Other backend features have separate
acceptance gates; scientific scalar parity does not prove general language parity.
