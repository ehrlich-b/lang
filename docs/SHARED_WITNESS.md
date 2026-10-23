# Shared reader witness

Run `python3 scripts/check_shared_witness.py --evidence /path/outside/checkout`
after `make bootstrap-verify JOBS=2`. The default compiler and receipt are the
verified generation-2 compiler and its build receipt. Evidence records every
command, exit, stdout and stderr, compiler/receipt hashes and a walkthrough.
`--controls-only` exercises contract and receipt refusal; it also works with
`python3 -O`.

The existing Lang parser and S-expression reader consume the same program:
`test/shared_witness/program.lang` becomes a closed core containing exact
numeric calls and fixed-array types. Both feed `numeric_validate_tree`,
`llvm_numeric_emit` and the allocation consumer `llvm_storage_size`, which
calls `layout_query`. Independent fixed vectors include signed high bits,
u64 boundaries, u8 wrapping and an array sum of 42, executed at O0 and O2.
The existing schema reader supplies the larger independent numeric matrix.
The storage oracle uses C sizeof, alignment and array stride, checks failure
statuses and cleared outputs, and separately checks wasm32 target constants.

Reader hashes freeze the adapters used by this proof; changing them requires
examining and updating the contract. Shared service implementation inside a
reader is rejected. A duplicate implementation injected into an external copy
must fail the same audit. Build receipts are checked against current source,
revision, compiler and fixed-point artifacts, including under optimized Python.
Negative controls change each hash domain and substitute the actual older
bootstrap compiler. Source span probes check independent byte offsets and
invalid ranges; compiler refusals must include origins and publish no module.

The f32 decimal literal regression runs through Lang. The existing core reader
cannot parse decimal float tokens, so the shared closed-core witness uses
uninitialized f32 arrays; the numeric matrix uses bit-preserving float carriers.
No decimal core round-trip claim is made. Legacy aggregate and relocation
lowering remains separate; the bounded layout API explicitly refuses those
forms. Full aggregate layout, relocatable constants, general ABI, reflection,
phase scheduling and native arm64 qualification remain outstanding.

Fixed f32 literal arrays also have independent runtime oracles:
`test/run_f32_array_literals.py` covers local initialization, and
`test/run_global_f32_arrays.py` covers global aggregates and refusal of integer
expressions. Both require `--compiler` and an external `--evidence` directory,
execute native Linux x86-64 and LLVM-to-Wasm/Node at O0/O2, and check frozen
IEEE-754 words, including halfway rounding and negative decimal zero. Malformed
IR and a wrong expected bit must fail the same real assembler/runtime checks.

The shared LLVM emitter accepts i64 integer and finite decimal literals in fixed
f32 arrays, including grouping and unary minus. Integer globals round directly
from i64 to binary32 and use LLVM's hexadecimal floating constant spelling;
local integer literals retain their runtime `sitofp`. Decimal digit arithmetic
rounds directly to binary32, ties to even, including subnormals; hexadecimal
constants avoid LLVM's restriction on inexact decimal spelling. No intermediate
binary64 rounding occurs. Decimal signs are kept, including underflow to zero,
and omitted slots use floating zero (an absent initializer uses
`zeroinitializer`). Global elements must be literals. Local elements may also
have a native f32 representation or an explicit `__core_numeric` result of type
f32 (including conversion and bitcast). Integer arithmetic, identifiers,
and calls do not acquire implicit f32 conversion from array context: they
require an explicit f32 conversion or receive a nonzero diagnostic before any
module is published. Integer literals outside i64 and decimals rounding beyond
finite binary32 receive range diagnostics. This does not extend f64 aggregates,
reader syntax, full aggregate layout or the ABI. Decimal core-reader syntax
remains unsupported.
