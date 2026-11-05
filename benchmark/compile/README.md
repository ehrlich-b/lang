# Compile benchmark execution plan

The retained [readiness plan](readiness-plan.json) schedules the full scale and
self compilation measurements after November 6, 2026 at 18:27 America/New_York
(`2026-11-06T18:27:00-05:00`). Both numerical verdicts remain **DEFERRED** until
execution. The plan is a procedure, not a benchmark result.

Run its steps in order from a clean, committed repository root, stopping at any
nonzero exit. Run the time guard before preparing or measuring anything. Record
the candidate HEAD and retain the plan, build receipts, execution logs and
`bench.json` with the resulting artifacts. The `sources` and `evidence` sibling
directories keep the baseline and generated artifacts outside the checkout.
If `../sources/base` already exists, verify its exact HEAD and clean status
instead of cloning over it. Never replace either compiler with an unpinned
binary or change sources between the receipt check and measurement.

The deterministic generator has no random seed. Keep all three sizes, both
compiler identities, five runs for each self compilation median, the same host
and budgets, and the original inclusive thresholds: 1M/100k emission time at
most 15 and candidate/base median self emission time at most 1.10. A failed
emission fails the run. An incomplete report remains DEFERRED; a completed
measurement that exceeds a threshold is FAIL. Do not turn fragment success into
a full benchmark PASS. The final step explicitly checks both verdicts.

Before that time, use `test/run_compiler_scale.py` with `COMPILER=out/lang_next`
for the `generated`, `tables`, `budgets` and `targets` fragments. `bench.py
--sizes 10000` is a timing smoke check that leaves the full verdicts DEFERRED.
Build from the preserved seed with `make build` after committing so its receipt
pins the candidate HEAD. Both fixed points, the complete LLVM suite (included
in `make verify`) and the complete Wasm suite remain integration requirements;
the plan lists their commands separately from the deferred measurements.

See [SIZE_LIMITS.md](../../docs/SIZE_LIMITS.md) for resource and diagnostic
contracts. Leave preserved seed and generated browser artifacts unchanged.
