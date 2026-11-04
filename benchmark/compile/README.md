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

Run `make build`, then `COMPILER=out/lang_next python3 benchmark/compile/phases.py
--output /path/to/baseline.json` from the repository root. This runs the same
source list as `make build` three times, emitting LLVM IR without invoking clang.
The JSON contains each run, median CPU milliseconds and stable input counts.
The three compiler processes together must consume less than 120 CPU seconds.

`lang compile --timings ...` writes six records to stderr. CPU time is process
user plus system time (`getrusage(RUSAGE_SELF)`), excluding reader subprocesses
and any subsequent clang/link step. Milliseconds retain microsecond precision.
Nested phases are subtracted from their caller so time is not counted twice.
When disabled, hooks only test the flag at phase boundaries; they do no clock
reads, counting, allocation, or AST walks. Timer storage is fixed and bounded.

| Phase | Input count |
| --- | --- |
| reading | Source bytes supplied, including cached snapshots and repeated reads |
| tokens | Tokens produced, including EOF and synthetic input wrappers |
| parsing | Top-level declarations parsed, including included sources |
| expansion-registration | Registered functions/globals/structs/enums (LLVM); root declarations (x86); collected functions/globals/structs (Wasm) |
| type-checking-lowering-ir-emission | The same backend input count |
| output | Buffered output bytes consumed (x86 code buffer excludes streamed data) |

The compiler does not have separate whole-program type-checking, lowering and
IR-emission passes. Those operations are interleaved in its AST walk, including
expression macro expansion. Includes and declaration readers expand during
registration and may be visited again during emission. The combined names
reflect those boundaries; they do not imply independent passes or invented
zero-duration measurements. Reading/tokenization/parsing include work nested
inside either backend phase. Counts measure work performed, not unique files.
