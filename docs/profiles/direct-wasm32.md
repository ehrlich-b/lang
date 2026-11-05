# Direct Wasm / wasm32 linear memory

Profile: `direct-wasm32`, version 1 (current implementation boundary).

Select with `LANGBE=wasm LANGOS=wasm`.

test/run_direct_wasm.sh exercises emitted binary modules; test/run_compiler_wasm.sh separately builds and runs the compiler hosted in Wasm. Passing the LLVM-to-Wasm suite does not validate this emitter.

Scalar and pointer locals/parameters/globals, structured control, direct calls, strings, imports, addressable locals and the tested struct-pointer slice. Integer and pointer values use i64 carriers and memory addresses use i32. Float locals, parameters, returns and mutable globals use native f32/f64 Wasm types.

Floats support `+`, `-`, `*`, `/`, unary minus, ordered comparisons (including `!=`, which is false for NaNs), numeric `cast`, equal-width `bitcast`, and typed loads/stores through pointers and `p[i]`. Mixed float arithmetic widens to f64 when either operand is f64; f32-only arithmetic stays f32. Numeric conversions use Wasm truncation toward zero; out-of-range float-to-integer conversions trap. Decimal literals are f64, rounded to nearest with ties to even; use `cast(f32, ...)` to round to f32. Global initializers accept numeric constants, grouping, unary minus and float casts.

Literal-initialized fixed local arrays of scalar elements provide addressable storage (up to 65536 elements). Uninitialized arrays, array parameters/returns/globals, indirect calls, aggregate returns and native effects still fail with source-aware errors. No native OS ABI, stack switching or general closure/aggregate-value promise.

`COMPILER=out/lang_next python3 -B test/run_direct_wasm_suite.py` measures all suite files against their expected exit codes and reports each refusal. Add `--only test/suite/260_float_basic.lang test/suite/261_float_composed.lang test/suite/290_pointer_index_floats.lang` for a focused float check. `test/direct_wasm_float_e2e.lang` also covers f32 arithmetic, globals, addressable float parameters, signed zero, NaNs and conversions.

All existing readers/examples retain [legacy/internal ABI v1](../C_SUBSET.md). Struct value returns are rejected because the old lowering can return a dead local address; explicit output pointers are the supported replacement. Existing enum-return fixtures remain internal compatibility evidence, not proof of a general external aggregate-return ABI. Narrow-field layout, aggregate calls and arbitrary C interop are unverified.

[Size limits](../SIZE_LIMITS.md) apply to the compiler host. See the [profile index](../PROFILES.md) for reproducible checks and proposal status.
