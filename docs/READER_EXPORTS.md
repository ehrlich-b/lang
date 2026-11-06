# Project export signatures

Sharing an AST supplies call instructions, not arbitrary language FFI. A project
frontend must agree on scalar storage, representation and ownership before it
erases that information. `std/reader_exports.lang` is a frontend library; no
language-specific inference or tag rules enter the compiler core.

The shipping project's catalog is [`exports.lang`](../example/shipping/exports.lang).
It describes `shipping_cost` as version 1, ABI `lang-native-v1`, one parameter and
one result, both `(core_type i64, representation signed-i64, ownership value)`.
These are signed 64-bit whole units, passed and returned by copy. There are no
tags, pointers, allocation, retained arguments, cleanup obligations or ownership
transfers. The policy treats `total >= free_over` as free shipping.

`ReaderExport` holds version, ABI, native symbol, ordered parameter scalars and
result scalar. Each `ReaderScalar` holds core type, representation and ownership.
The shipping reader creates its function with `reader_export_func` from the same
catalog the consumer checks, so the core types and arity come from one definition.
The builder currently accepts only i64 scalar storage. Representation names are
explicit frontend agreements, not inferred semantics or a runtime codec.

`shippinglib` emits the shipping function without `main`; the original `shipping`
reader and project manifest keep their executable behavior. The project's
[`shippingforth`](../example/shipping/client/reader.lang) reader calls
`fo_read(text, shipping_exports())`. Before emitting any calls it checks each
Forth `extern` against the producer catalog. Raw i64 value parameters and one
raw i64 value result match directly. Missing or duplicate exports, duplicate
words, shadowing, different arity, ABI, version, storage, representation or
ownership fail at the Forth import. No runtime wrapper is inserted for a match.

A tagged integer such as `(n << 1) | 1` still occupies i64 storage, but is a
different representation. It requires a separately named, explicit adapter with
documented decoding, range/overflow checks, ownership and result encoding.
This profile refuses incompatible signatures; it provides no implicit adapter.
Managed objects, pointers, callbacks, unwinding, moving heaps, external C ABIs
and runtime ownership policies need their own contracts.

The catalog is trusted frontend code, not a global linker verifier or a sandbox.
An author remains responsible for the declared semantics of the function body.
Unrestricted Lang and the original `forth` reader's handwritten `extern`s remain
trusted low-level paths. Use a checked project reader for this guarantee; client
syntax cannot override its catalog. Other projects may supply another catalog to
`fo_read`. This is not a new field in version 1 project manifests.

From a committed checkout, compile two readers into one native program:

```bash
make init
make build
export LANGBE=llvm LANGOS=linux
./out/lang_next example/shipping/shipping.lang example/shipping/client/reader.lang example/shipping/client/policy.shippinglib example/shipping/client/client.shippingforth example/shipping/client/main.lang -o out/shipping-client.ll
clang -O0 out/shipping-client.ll -o out/shipping-client
./out/shipping-client 80
./out/shipping-client 100
```

The outputs are `10` and `0`. In the unoptimized IR, `client_fee` calls
`shipping_cost(i64)` directly and returns i64, with no boxing or adapter.

Run `python3 -B test/reader_author/interop.py --case shipping-client` for the
fragment, or `env JOBS=2 VERIFY_CASE=shipping-client make verify` for its make
gate. The runner builds committed current sources in a fresh clone, restricts
execution to two CPUs and 2 GiB, and retains commands, input/tool hashes, IR,
source ASTs, stdout, stderr and exits outside the checkout. It checks exact
boundary answers (including a changed policy), direct-call IR and located
refusals for tagged inputs/results and ownership mismatches before native IR
can be emitted. Any failed expectation exits nonzero. Full suites and fixed
points remain integration work.
