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
