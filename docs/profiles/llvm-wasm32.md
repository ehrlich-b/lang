# LLVM / wasm32 linear memory

Profile: `llvm-wasm32`, version 1 (current implementation boundary).

Select with `LANGBE=llvm LANGOS=wasm`.

test/run_wasm_suite.sh emits LLVM, links with clang/wasm-ld and runs under test/wasm_host.js. A missing tool is an incomplete baseline, even though the older suite prints SKIP and exits zero.

wasm32 addresses with the historical i64-facing compiler ABI, explicit pointer conversions and host libc imports. This is not a native C ABI or per-object memory safety.

handle/perform/resume fail at compilation. Native assembly, stack switching, POSIX processes and dynamic native libraries are unavailable. Host imports supply allocation, files and output.

All existing readers/examples retain [legacy/internal ABI v1](../C_SUBSET.md). Struct value returns are rejected because the old lowering can return a dead local address; explicit output pointers are the supported replacement. Existing enum-return fixtures remain internal compatibility evidence, not proof of a general external aggregate-return ABI. Narrow-field layout, aggregate calls and arbitrary C interop are unverified.

[Size limits](../SIZE_LIMITS.md) apply to the compiler host. See the [profile index](../PROFILES.md) for reproducible checks and proposal status.
