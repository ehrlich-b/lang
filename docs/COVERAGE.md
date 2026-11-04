# Compiler function coverage

Run `JOBS=2 make coverage`. This first runs the non-promoting verifier (LLVM
and reader AST fixed points plus the LLVM suite), compiles its `kernel2.ll`
with `clang -O0 -fprofile-generate`, runs the complete LLVM suite again with
`COMPILER` pointing at that binary, and merges the profiles with
`llvm-profdata`. Clang and llvm-profdata must have compatible profile formats.
No compiler source or emitted IR is rewritten.

Verification and the instrumented suite use the runner's existing sequential
mode to avoid concurrent JIT timeouts and keep the unoptimized compiler from
contending with a neighboring test's two-second JIT budget. All assertions, timeouts and skip rules remain unchanged. The separate
`env JOBS=2 make verify` gate keeps its ordinary scheduling.

The report prints executed/total functions for each source file and lists
the twenty largest unreached functions. Every defined IR function must have
both a profile record and a source declaration; missing records are errors,
not assumed zeros. The denominator includes zero-count functions and excludes
external declarations and LLVM's profiling runtime. Source attribution walks
the compiler input/include closure and matches declaration names to IR symbols;
it does not need debug information. Size means LLVM body lines, excluding blank
lines, comments and labels, rather than machine code size.

Reach means at least one IR PGO edge counter was positive. IR profiles need not
store the entry counter first, so these are not invocation counts. Instrumenting
at O0 preserves the function inventory without inlining. Compilers/readers
generated during the tests are uninstrumented: this measures functions reached
in the compiler under test, not functions in its outputs. The workload includes
the suite's native, reader, error-path and effects checks, but is not a claim
about coverage of other suites or targets. An unreached function can be a test
gap, a target-specific path or dead code; coverage alone cannot decide which.
As with ordinary PGO, an invocation terminated without flushing its profile
cannot contribute counters; this is not a crash-coverage measurement.

`test/coverage_baseline.json` records this workload's measured inventory and
per-file counts. To compare a run, use:

```
JOBS=2 make coverage COVERAGE_ARGS=--check-baseline
```

After reviewing intentional workload/compiler changes, regenerate it with
`COVERAGE_ARGS=--write-baseline`. Compare the unreached inventory as well as
the totals. `--ir out/bootstrap_verify/kernel2.ll` explicitly reuses an already
verified IR file and skips the preliminary verification. `--work-dir` selects
the artifact directory (default `out/coverage`); `--log-dir` selects the logs
and JSON reports (default the work directory's `logs` subdirectory). Each run
uses fresh profiles and keeps earlier artifacts. A failed suite, incompatible
profile, missing source mapping or baseline mismatch fails the command.

Run the parser/inventory regression checks with
`python3 test/test_coverage_functions.py`.
