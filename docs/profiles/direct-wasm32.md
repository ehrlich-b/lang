# Direct Wasm / wasm32 linear memory

Profile: `direct-wasm32`, version 1 (current implementation boundary).

Select with `LANGBE=wasm LANGOS=wasm`.

test/run_direct_wasm.sh exercises emitted binary modules; test/run_compiler_wasm.sh separately builds and runs the compiler hosted in Wasm. Passing the LLVM-to-Wasm suite does not validate this emitter.

Scalar and pointer locals/parameters/globals, structured control, direct calls, strings, imports, addressable locals, struct values and fixed arrays. Integer and pointer values use i64 carriers and memory addresses use i32. Float locals, parameters, returns and mutable globals use native f32/f64 Wasm types.

Floats support `+`, `-`, `*`, `/`, unary minus, ordered comparisons (including `!=`, which is false for NaNs), numeric `cast`, equal-width `bitcast`, and typed loads/stores through pointers and `p[i]`. Mixed float arithmetic widens to f64 when either operand is f64; f32-only arithmetic stays f32. Numeric conversions use Wasm truncation toward zero; out-of-range float-to-integer conversions trap. Decimal literals are f64, rounded to nearest with ties to even; use `cast(f32, ...)` to round to f32. Global initializers accept numeric constants, grouping, unary minus and float casts.

Struct and fixed-array locals live in per-call linear-memory frames, including nested arrays and structs. Assignment, initialization from another aggregate, and by-value aggregate parameters copy the entire object; recursion preserves each invocation's storage. Uninitialized aggregate declarations are zeroed. Struct and array globals have distinct static storage; globals accept zero initialization and constant array literals (including nested arrays and floats). Field/index addresses and pointer differences use the same element strides as loads and stores.

Array literals evaluate their elements in order into private per-call frame storage before copying to the destination. A literal can therefore read the old destination through fields, indices, pointers or function calls, including nested literals and partial initializers; omitted elements become zero.

`src/layout.lang` supplies wasm32 object layout: pointers occupy four bytes in memory, scalars use their declared width and alignment, arrays use element stride, and structs align each field and round their size to the largest field alignment. The i64 pointer carrier at calls and in Wasm locals does not change this storage layout. Static data is limited to the first MiB, checked per-call frames occupy the next MiB, and host allocations start at 2 MiB.

Struct/array value returns stay refused at their declaration because a frame address would outlive its storage; use output pointers. Indirect calls and closures need a separate function-table/capture ABI. Enums and native effects remain refused because their tagged-value/control-flow lowering is not implemented. Extern globals, dynamic array counts and nonconstant aggregate global initializers remain refused. Float-to-integer global initialization (including array elements) is refused at the float literal because the static integer evaluator does not implement numeric conversion; convert in a function instead. There is no native OS ABI or stack switching.

`COMPILER=out/lang_next python3 -B test/run_direct_wasm_suite.py` measures all suite files against their expected exit codes and reports each refusal. Add `--only test/suite/260_float_basic.lang test/suite/261_float_composed.lang test/suite/290_pointer_index_floats.lang` for a focused float check. `test/direct_wasm_float_e2e.lang` also covers f32 arithmetic, globals, addressable float parameters, signed zero, NaNs and conversions.

All existing readers/examples retain [legacy/internal ABI v1](../C_SUBSET.md). Struct value returns are rejected because the old lowering can return a dead local address; explicit output pointers are the supported replacement. Existing enum-return fixtures remain internal compatibility evidence, not proof of a general external aggregate-return ABI. The direct backend uses the explicit wasm32 object layout above; this is an internal ABI, not a promise of arbitrary C interop.

[Size limits](../SIZE_LIMITS.md) apply to the compiler host. See the [profile index](../PROFILES.md) for reproducible checks and proposal status.
