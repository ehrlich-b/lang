# LLVM / wasm32 linear memory

Profile: `llvm-wasm32`, version 1 (current implementation boundary).

Select with `LANGBE=llvm LANGOS=wasm`.

test/run_wasm_suite.sh emits LLVM, links with clang/wasm-ld and runs under test/wasm_host.js. A missing tool is an incomplete baseline, even though the older suite prints SKIP and exits zero.

wasm32 addresses with the historical i64-facing compiler ABI, explicit pointer conversions and host libc imports. This is not a native C ABI or per-object memory safety.

handle/perform/resume fail at compilation. Native assembly, stack switching, POSIX processes and dynamic native libraries are unavailable. Host imports supply allocation, files and output.

## Flow generators

`test/flow_wasm.lang` uses the explicit `#flow_portable` reader in
`example/flow/flow.lang`. Its stateful Fibonacci generator and synchronous
drivers print `flow answer: 42` and return 42 on native LLVM, LLVM-to-Wasm
under node, and direct Wasm under node. Run:

```bash
make build
COMPILER=out/lang_next python3 test/run_flow_wasm.py
make test-direct-wasm COMPILER=out/lang_next
```

The portable reader fuses each generator/driver pair using ordinary AST blocks,
loops, branches and fresh local bindings. A statement yield runs the driver
body before continuing the generator; its locals stay in that activation.
Arguments are evaluated once, in order; separate driver sites have separate
bindings. Generator return ends that driver site and discards the return value.
No suspended frame escapes, and no effects lowering or stack switching is used.

This is a synchronous, statement-yield profile: generators must be declared in
the same portable block and consumed through `for-in`. Recursive specialization
and expression yields (including bidirectional feedback) are refused at their
source locations. Generator names are templates rather than exported callable
functions. Ordinary flow functions remain callable from lang. The original
`#flow` effects reader remains available on native LLVM with `clang -O0`;
general handle/perform/resume operations remain unsupported on both Wasm paths.
The comparison test also runs the original native bidirectional flow demo and
checks a located refusal of portable expression yields on all three targets.

All existing readers/examples retain [legacy/internal ABI v1](../C_SUBSET.md). Struct value returns are rejected because the old lowering can return a dead local address; explicit output pointers are the supported replacement. Existing enum-return fixtures remain internal compatibility evidence, not proof of a general external aggregate-return ABI. Narrow-field layout, aggregate calls and arbitrary C interop are unverified.

[Size limits](../SIZE_LIMITS.md) apply to the compiler host. See the [profile index](../PROFILES.md) for reproducible checks and proposal status.
