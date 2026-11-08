# An editable shipping language, through native execution

A policy has exactly two settings, in either order:
`shipping { base 10; free_over 100; }`. Both are decimal integers in
0..1000000. `free_over` is an inclusive threshold: orders at or above it ship
free; smaller orders pay `base`. Amounts use whole units, without tax or currency
conversion. Duplicate, unknown, missing and out-of-range settings are errors.
Whitespace and Lang-style comments are allowed. The order total arrives at
runtime as one decimal command-line argument in the same range.

To build the policy directly with the current compiler, run `make init` and
`make build`, then:

```bash
./out/lang_next build --project example/shipping/project.lang-project example/shipping/policy.shipping -o out/shipping
PATH=/nonexistent ./out/shipping 100
```

This prints `0`. The [project driver](../../docs/LANGUAGE_PROJECT.md#build-a-guest-directly)
uses `-O0` by default and provides `--emit=ast` and `--emit=llvm` for inspection.
Replay it with `python3 -B test/reader_author/native_build.py --case shipping`.

The longer walkthrough below exposes each boundary for editing and minting a
standalone compiler. From a fresh clone, start in its root. Prerequisites: Linux x86-64, Python 3,
Make, Clang and its native linker. No services or elevated permissions are
needed. Copy and run this entire block. The copied reader is your editable
language implementation: replace the generated scaffold, then change the
threshold relation below to see the language's behavior change.

<!-- shipping-walkthrough -->
```bash
set -euo pipefail
export JOBS=2 LANGBE=llvm LANGOS=linux
make init
mkdir -p out/shipping-work
cd out/shipping-work
../../out/lang new reader shipping
cp ../../example/shipping/shipping.lang shipping.lang
# Edit the reader: make free_over exclusive, then inspect its shared AST.
python3 -c 'from pathlib import Path; p=Path("shipping.lang"); s=p.read_text(); assert s.count("ast_ge(")==1; p.write_text(s.replace("ast_ge(", "ast_gt("))'
../../out/lang read shipping.lang ../../example/shipping/policy.shipping -o exclusive.ast
../../out/lang --from-ast exclusive.ast --ast-source ../../example/shipping/policy.shipping --runtime ../../example/shipping/runtime.lang -o exclusive.ll
clang exclusive.ll -o exclusive
./exclusive 100
# Restore the documented inclusive policy and inspect the final shared AST.
python3 -c 'from pathlib import Path; p=Path("shipping.lang"); s=p.read_text(); assert s.count("ast_gt(")==1; p.write_text(s.replace("ast_gt(", "ast_ge("))'
../../out/lang read shipping.lang ../../example/shipping/policy.shipping -o policy.ast
cat policy.ast
# AST is the frontend boundary; the runtime is embedded at compiler-build time.
../../out/lang compiler shipping shipping.lang --runtime ../../example/shipping/runtime.lang -o shippingc
mkdir isolated
cp shippingc isolated/shippingc
cp ../../example/shipping/policy.shipping isolated/policy.shipping
cd isolated
# Only binary and guest source are here. No compiler tools are available in PATH.
PATH=/nonexistent ./shippingc policy.shipping -o policy.ll
# Clang boundary: Lang emits LLVM; Clang and the native linker produce the executable.
clang policy.ll -o shipping
./shipping 0
./shipping 80
./shipping 99
./shipping 100
./shipping 120
```

The final five commands print exactly `10`, `10`, `10`, `0`, `0`, each followed
by a newline, and exit 0. Before linking, `policy.ast` contains a comparison of
`total` with 100, not a precomputed answer. `exclusive.ast` contains `>` instead
of `>=`; the runner links that edited policy too and verifies that 100 then
costs 10. `isolated/policy.ll` contains the embedded runtime; it needs no reader
or runtime source files. The isolated IR command needs no Clang, assembler or
linker. Linking does need Clang and the system's native libraries.

`reordered.shipping` is an equivalent valid policy. The files in `invalid/`
show the four semantic diagnostics, which include source line and column.
Malformed syntax, trailing text, negative/fractional/overflowing settings and
invalid runtime arguments are also rejected.

Replay this fragment with `python3 -B test/reader_author/route.py --case shipping`.
It clones the committed checkout, executes the block above, and fails on any
unexpected stdout, stderr, exit or AST. It retains command receipts, source and
tool hashes, authored line counts, and stage CPU/wall times outside the checkout
(default: `../evidence/shipping-<unique-id>`; override with `--evidence DIR`).
Those times measure machine work, not human authoring time. The runner limits
itself and children to two CPUs, JOBS=2 and a 2 GiB address-space ceiling.
For the fragment gate, run `env JOBS=2 make verify VERIFY_CASE=shipping`;
plain `make verify` retains the integration suites and fixed-point checks.

Run all authored fixtures with `./out/lang_next test --project example/shipping/project.lang-project`,
or add `--fixture policy` to select one. `tests.json` includes two positive
sources, syntax and semantic negatives, runtime inputs and exact stdout/exits.
See the [fixture format](../../docs/LANGUAGE_PROJECT.md#run-project-fixtures).

To finish with a native program directly from the minted compiler, run outside
the repository with the compiler and guest source:

```bash
./shippingc policy.shipping --emit=native -o shipping
./shipping 99
./shipping 100
```

These print `10` and `0`. Native emission needs Clang and its system linker;
`--emit=llvm` and the original default IR mode still work without either tool.
Replay this path with `python3 -B test/reader_author/standalone.py --case native`.
Use `env JOBS=2 make verify VERIFY_CASE=standalone-native` for this fragment gate.
### Inspect the project

With the compiler built from current sources (`make init`, then `make build`),
run `out/lang_next inspect --project example/shipping/project.lang-project --stage tree`
from the checkout root. Select `tokens`, `tree`, `core` or `llvm`; add `-o path`
to save the artifact. Stdout contains only that artifact; errors go to stderr.
The tree keeps named captures, values and half-open UTF-8 byte spans. Core shows
`shipping_cost` and calls across the separate `shipping_total` / `shipping_print`
runtime boundary; LLVM includes the runtime implementations.

The grammar's `!inspect shipping_policy;` metadata names its complete-input
boundary. Inspection invokes the actual reader and uses its configured tokenizer
and generated parser. Tree inspection stops before lowering, so a lowering error
can still be diagnosed from the tree. A tree parse checks end of input. Tokens
stop at the scanner boundary and can succeed even when later parsing would fail.
Custom readers without this opt-in boundary report tokens/tree as unsupported;
their core and LLVM remain available. Native readers retain their normal host
access; this command does not imply sandboxing.
