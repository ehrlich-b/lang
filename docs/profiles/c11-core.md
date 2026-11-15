# C11 core target

Select `LANGBE=c`; the compiler writes C source (`a.c` by default). Build it
with `gcc -std=c11 -O2 program.c -o program -lm` or clang with the same flags.
`LANGBE=c out/lang_next run program.lang` uses the host clang driver.
Floating remainder uses C11 `fmod`; the driver links the math library.

The emitter consumes the same core AST after include, macro and reader
expansion. Reader helpers execute on the compiler host using LLVM, even when
the selected program target is C. This is a source backend, with independent
C compiler optimization; it does not translate LLVM IR or invoke an interpreter.

Integer expressions use unsigned 64-bit words. Addition, subtraction,
multiplication and negation wrap modulo 2^64. Signed ordering uses an explicit
conversion that never casts an out-of-range unsigned value to a signed value.
Integer literals remain decimal when written with leading zeros.
Signed division and remainder use unsigned magnitudes, including INT64_MIN / -1.
Shift counts are masked to six bits; right shift explicitly fills sign bits.
Narrowing masks bits, and signed extension uses unsigned arithmetic. No
`-fwrapv` or `-fno-strict-aliasing` flag is needed.

Storage uses explicit little-endian bytes, fixed eight-byte pointer/function
slots, core array strides and core struct/enum offsets. Generated C does not
use C struct layout or cast byte storage to typed lvalues. Scalar loads and
stores and aggregate copies preserve aliasing through character accesses.
Aggregates are copied at assignment and internal parameter boundaries.
The host must have eight-bit bytes and 64-bit addresses for the native pointer
and libc ABI. Float storage requires IEEE binary32/binary64. This profile does
not establish a portable foreign struct ABI or cross-endian pointer-array ABI.
External scalar and pointer calls use the existing libc surface; arbitrary
foreign signatures require separate ABI qualification.

Functions, recursion, function pointers, lambdas, by-value closure environments,
globals, arrays, structs, enums, matches, labeled loops, let/block expressions, strings
and scalar float operations are supported. Expression lowering emits ordered
temporaries and preserves short-circuit evaluation. Effects are refused at
their source location until CPS lowering is available.
128-bit integers, numeric intrinsic families, inline assembly, raw syscalls,
external aggregate parameters/returns and external globals are outside this
profile and fail closed. Invalid memory accesses retain the core's unsafe
pointer semantics. Division by zero traps; floating casts require an in-range
finite operand.

Run `env JOBS=2 python3 test/run_c_backend_suite.py --compiler out/lang_next`.
Every `test/suite/*.lang` is attempted; located compiler refusals are counted
separately from wrong answers. C11 build errors and execution mismatches are
wrong answers. The runner prints correct/wrong/refused counts for both gcc
and clang at `-O2` and fails on any wrong answer, compiler disagreement or
fewer than 200 correct cases per compiler. The historical `// Expected:`
spelling and the extern fixture's comment oracle are also recognized. The
self-checking legacy `238_ast_statements.lang` has no header oracle; its
expected success status is explicitly zero in the runner. Existing ignore
markers do not skip C execution. `--output DIR` preserves per-input emission,
build and execution logs plus a JSON summary for inspection.

Use `--fixtures test/c_backend` for focused wrapping, layout, float and closure
regressions, including Boolean literal shifts and closure conversion at typed
let bindings and assignments through locals, fields and pointers. Closure
conversion also follows macro/reader expansions, let bodies, block tails and
every match arm, preserving captured environments and boxing plain function
pointers exactly once.

The MiniLisp float/string border probes reproduce the existing LLVM reader/runtime
bugs; their C reproductions are retained under `test/borders/bugs/`. They do not
expand the supported MiniLisp subset. Closure environments use `alloc` and
retain its runtime-owned lifetime; no automatic collection is introduced.

C11 border probes can be measured with `COMPILER=out/lang_next python3 test/borders/run.py --target c --reader lang` (or `minipy` or `minilisp`). Filtered measurements do not alter the published grid.
