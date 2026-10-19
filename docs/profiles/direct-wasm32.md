# Direct Wasm / wasm32 linear memory

Profile: `direct-wasm32`, version 1 (current implementation boundary).

Select with `LANGBE=wasm LANGOS=wasm`.

test/run_direct_wasm.sh exercises emitted binary modules; test/run_compiler_wasm.sh separately builds and runs the compiler hosted in Wasm. Passing the LLVM-to-Wasm suite does not validate this emitter.

Scalar and pointer locals/parameters/globals, structured control, direct calls, strings, imports, addressable locals and the tested struct-pointer slice. Integer values use i64 and memory addresses i32.

Unsupported nodes fail with source-aware errors, including arrays, indirect calls, aggregate returns and native effects. No native OS ABI, stack switching or general closure/float/aggregate-value promise.

All existing readers/examples retain [legacy/internal ABI v1](../C_SUBSET.md). Struct value returns are rejected because the old lowering can return a dead local address; explicit output pointers are the supported replacement. Existing enum-return fixtures remain internal compatibility evidence, not proof of a general external aggregate-return ABI. Narrow-field layout, aggregate calls and arbitrary C interop are unverified.

[Size limits](../SIZE_LIMITS.md) apply to the compiler host. See the [profile index](../PROFILES.md) for reproducible checks and proposal status.
