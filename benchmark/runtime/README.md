# Native runtime comparison

Six independent C/Lang pairs exercise recursive fib, a byte sieve, n-body
integration with softened inverse-cube acceleration over f64 arrays, mandelbrot, a linear-probing hash map, and a pointer
string scan. Each accepts one workload size and prints a checksum. The checked-in
`workloads.json` fixes all sizes and smoke outputs; there is no randomness. C uses
explicit 64-bit integers to match Lang, identical loop order and array layouts.
Inputs avoid signed overflow, out-of-bounds access and overlapping copies.

The n-body pair calls the identical `math_bridge.c` adapter to libm sqrt through
an i64 bit carrier. The preserved baseline declares floating extern parameters
as i64 even when its call site uses double; using a shared integer-ABI adapter
keeps that compiler unchanged and both programs correct. The bit copies optimize
away, and both sides pay the same external call. Its source hash is recorded.

Both versions are compiled with clang `-O2 -ffp-contract=off`, linked against libm, without LTO or fast math. Disabling contraction keeps C's floating-point evaluation consistent with
Lang's uncontracted LLVM operations. Timing covers process startup and the
checksum print; compilation is excluded. Five fresh processes per language are
measured, alternating execution order. Raw samples, medians, Lang/C ratios,
geometric mean, compiler/source hashes, tool versions and host metadata are
recorded. Every execution must have exit zero, empty stderr and identical output.
The final verdict is PASS only when the geometric mean is at most 1.15.

Run from the repository root, supplying immutable compiler binaries and their
recorded SHA-256 hashes. Keep outputs outside the checkout:

```sh
python3 benchmark/runtime/run.py --smoke \
  --compiler "$CANDIDATE" --compiler-sha256 "$CANDIDATE_SHA256" \
  --output-dir "$EVIDENCE/smoke-check"
python3 test/runtime_codegen.py --compiler "$CANDIDATE" \
  --baseline-compiler "$BASE_COMPILER" --output-dir "$EVIDENCE/codegen"
```

Smoke checks execute all six small workloads once, check independent golden
outputs, and emit `smoke.json` with status SMOKE_ONLY. They do not emit timings,
ratios or a performance verdict. The full experiment is DEFERRED until after
2026-11-06 18:27 America/New_York. The runner refuses it before that time.
After that time, use a fresh evidence directory:

```sh
python3 benchmark/runtime/run.py \
  --baseline-compiler "$BASE_COMPILER" --baseline-sha256 "$BASE_SHA256" \
  --compiler "$CANDIDATE" --compiler-sha256 "$CANDIDATE_SHA256" \
  --output-dir "$EVIDENCE"
```

The baseline compiler must be built from commit
`4b93dcaa32c177ed827fb7597b02d8431ace2dec` using its preserved bootstrap seed.
Keep the seed hash, baseline source/build receipt and baseline executable hash
with the evidence. The runner measures that baseline first and writes
`perf-before.json` before running the candidate and writing `perf.json`. It
refuses to overwrite either measurement. The same paired sources and sizes are
used for both compilers. A failure is a failure; do not alter sizes, runs, source
identities or the 1.15 threshold after seeing results.

Native pointer addition/subtraction now uses non-inbounds typed GEPs, retaining
pointer induction information for LLVM. There are no new overflow, aliasing or
fast-math promises. Pointer scaling remains as specified in LANG.md. Intermediate
addresses can leave an object and return before dereferencing. Address-taken
locals and allocation lifetimes are unchanged. Wasm retains the existing i64
carrier arithmetic to preserve high bits until an actual memory access.

`test/runtime_codegen.py` checks byte/bool/integer/f64/aggregate pointer strides,
including heap reads and recursive fixed-array strides over multi-field structs,
local nested aggregate array storage at O0 and O2,
subtraction, negative offsets, intermediate out-of-object addresses, wrapping,
and Wasm carrier high bits at O0/O2. It also executes an expanding reader,
cross-compiles the positive fixture to arm64, executes it on Wasm, and confirms
that the negative wide-integer fixture rejects. Keep the complete LLVM, LLVM-to-
Wasm and direct-Wasm suites and both compiler fixed points as integration gates.
