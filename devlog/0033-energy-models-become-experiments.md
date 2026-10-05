# Energy models become native experiments

The scientific milestone uses Lang's forge to compile an energy model into
specialized numerical code. `ham` accepts an explicitly nondimensional,
constant-mass separable Hamiltonian. A bounded polynomial IR differentiates V
at compile time, then shared AST builders emit force functions and whole-state
kick–drift–kick phases. No model recognition, force lookup table, runtime
interpreter, effects, browser work, or unit-system claims enter this slice.

The initial floating AST probe failed: `(number 1.25)` was tokenized as integer,
dot, integer. A root-reader-only decimal extension fixed roundtrips without
changing other readers' integer tokenizer. Scientific data then exposed f64
struct fields being loaded/stored as integers and unary minus emitting integer
subtraction. Typed field memory operations reuse the existing field-address
path; floating negation uses fneg. Both changes were separately bootstrapped,
with regressions 287 and 288. The native aggregate passed 234, then 235 checks,
with six platform skips.

Two independent reviewers caught substantive issues before the final gate:

- Manual decimal accumulation disagreed with LLVM's binary64 literal parsing.
  It could discard `(0.3-0.30000000000000002)*x` or admit a denominator that
  emitted as zero. A shared syntax-checked strtod conversion repaired both.
- A literal IR node could hide a long prebuilt constant AST. Repeated parameter
  references bypassed the expansion budget. Canonical sign normalization,
  counting the optional negation, and a lexer prefix-depth bound repaired it.

Reviewers independently confirmed those repairs, checked unfamiliar potentials
with three unequal-mass coordinates, and ran copied minted compilers outside
the checkout with the source root unavailable. The maintained scientific test
also checks four unequal masses, free motion, powers, decimal cancellation,
31 located rejection cases, and explicit nonfinite runtime failures.

All numerical tolerances were frozen by the independent reference author
before generated trajectories were inspected. At T=3.68 the harmonic endpoint
errors decrease by factors 4.00007 and 4.00002 as h halves. The coupled quartic
endpoint error is 7.5769e-6 against independently handwritten, refined RK4;
maximum sampled state error is 1.0936e-5. The different double-well potential
also passes. A two-flip reversal returns the initial full state within
1.1102e-16. Analytic gradients differ by at most 4.4409e-16. The O0/O2 receipts
show no differences; equality is observed evidence, not a bitwise promise.

Long harmonic runs through T=1000 have sampled maximum energy errors
5.1761e-5 and 1.2941e-5 at h=.04/.02, below their independently calculated
bounds. Short nonlinear relative energy errors remain within the frozen
regime. No exact conservation, chaos, or physics novelty is claimed.

The full focused experiment took about ten seconds on this Mac, including
minting, model compilation outside the checkout, linking both optimization
levels, execution, and reference checks. These are single-run receipts with
process startup and CSV I/O, not a performance benchmark.

Commands, models, generated LLVM, raw CSV, refined reference CSV, numerical
JSON, independent review probes, and PNG/SVG figures live in
`out/hamiltonian/`. `test/hamiltonian_e2e.py --output out/hamiltonian` regenerates
them. [The language contract and workflow](../docs/HAMILTONIAN.md) document
assumptions and limits. Final full bootstrap verified both fixed points and
cross-target roots, passed 236/236 native checks with six platform skips, and
promoted the exact tested Mac compiler. The LLVM-to-Wasm suite passed 178 checks
with no failures and 21 documented skips, including both new float regressions.
The chunk ends at a clean local checkpoint; no follow-on work is admitted.
