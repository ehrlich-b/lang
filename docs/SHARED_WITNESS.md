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
