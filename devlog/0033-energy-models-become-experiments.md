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

The native slice was resumed from preserved `006944f` in an isolated draft.
Its original science checks passed again before changes. Independent source
review found that trajectory JSON was missing: numerical-report JSON was not
a substitute for trajectory samples. Generated executables now support
`--json`, carrying coordinate order, masses, run settings and sampled full
states. Binary64 values use 17 significant digits; signed zero retains a
decimal point. All JSON output shares buffered printf so punctuation cannot
overtake numeric cells written through a different stream. Bounded integer
metadata uses exact conversion through the existing f64 printf interface.

The maintained gate now starts with an explicit fractional reader → saved AST
→ LLVM → native probe, including negative constants and f64 parameter/return
types. It saves and rebuilds the generated AST for both potentials and a
coupling edit, then checks twelve O0/O2 JSON exports against CSV, including
four unequal masses, stride three, a final step off that stride, and signed
zero. Minted compiler invocations run outside the checkout with LANG_ROOT
pointing at a missing directory. Nonfinite runs fail with incomplete JSON.
Command, source, compiler and artifact receipts make the execution reviewable.

Editing only b from .4 to .9 gives maximum sampled state separation .134495.
The changed model still passes the original frozen numerical tolerances:
maximum native state error 1.22814e-5 against a refined handwritten RK4 oracle.
The explicit Ex/Ey/Eb decomposition describes sampled component energy
changes; it makes no claim of separate conservation. Independent review
reimplemented the changed-coupling RK4 and confirmed its refinement ratio
16.0486 and fine-reference error estimate 1.19e-12. A fresh unfamiliar
three-coordinate model also passed handwritten forces, energy and exact
CSV/JSON binary64 checks outside the source tree.

Final serial `JOBS=1 SEQUENTIAL=1 make bootstrap-local` passed all seven stages,
both fixed points, both cross-target object checks, and 236/236 native aggregate
checks with six platform skips. The aggregate invokes the strengthened science
gate once. Its tested native compiler and roots were promoted locally by the
standard pipeline with external publication disabled. Native-only scope,
the original checkpoint and optimized effects repro, and separate unpromoted
browser drafts are preserved; no public push, deployment or board edit occurred.
