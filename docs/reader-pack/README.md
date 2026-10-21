# Reader authoring and repair pack

This is a deterministic local **smoke experiment**, not model benchmark evidence.
It demonstrates reusable readers and an oracle that refuses known defects. It
cannot establish agent superiority, authoring speed, cost, or generalization.
No paid model calls, outreach, or old LANG-AI scope is enabled. Later repeated
model runs require an explicit budget and isolated sessions before starting.

Run from the repository root with Python 3, Node, Clang, wasm-ld, and Playwright
with a locally installed Chromium. Set PLAYWRIGHT_MODULE to the installed
package's index.mjs and CHROMIUM_PATH to its executable if not discoverable.
Evidence must be outside the checkout, in a new directory for every invocation.

```bash
nice -n 10 python3 test/reader_pack/run.py contract
```

```bash
nice -n 10 python3 test/reader_pack/run.py smoke --evidence "${PACK_OUTPUT:?set a fresh absolute output directory outside the checkout}"
```

These are the only fenced command blocks in this pack; both are executed by its
acceptance checks. The smoke command builds a seed from the preserved LLVM root,
compiles the current native compiler from src and std, then uses that compiler
to build the current browser compiler. It never uses the shipped web/compiler.wasm
or an unverified out/lang. build/identity.json pins the current source commit,
input SHA-256 values and native/Wasm compiler hashes. Per-command receipts retain
argv, elapsed milliseconds, exit status, stdout and stderr. All successful and
negative observations are saved; browser results come from real Chromium using
the same compiler and program host scripts as the lab. Only loopback HTTP is used.

## Tasks and solutions

The exact prompts, matched tracks, metrics, safety boundary and counterbalanced
orders are frozen in [protocol.json](../../test/reader_pack/protocol.json).
Both tracks implement the same grammar and return the same numeric results.
The interpreter-only track uses Python's standard library; the native-plus-Wasm
track authors a Lang reader and must pass both backends. The resulting products
and tool access differ intentionally; record that when interpreting later data.

1. **Create:** implement `answer N`, returning N. Start from the reader contract
   `reader threshold(text *u8) *u8`. Reference: [create.lang](../../test/reader_pack/create.lang).
2. **Evolve:** replace the syntax with `threshold LIMIT value VALUE`. Return 1
   when VALUE >= LIMIT, otherwise 0. Reference: [threshold.lang](../../test/reader_pack/threshold.lang).
   [common.lang](../../test/reader_pack/common.lang) separates token recognition,
   decimal validation and full-input validation from AST lowering.
3. **Repair:** fix each independent wrong_*.lang fixture listed in the protocol.
   The interpreter track has matching defects in wrong_interpreters.py.
   Both tracks exercise wrong helper arity, an off-by-one boundary, ignored trailing
   input, constant output and missing numeric validation. First retain the
   failing diagnostic or wrong result, then run the corrected reference through
   the entire oracle. The replay records zero model repair attempts: these are
   supplied solutions, not measured agent repairs.

A decimal byte is one to three ASCII decimal digits with value 0..255; leading
zeros are accepted and canonicalized. Negative, float, hexadecimal, exponent,
quoted, overflow, oversized, missing and trailing inputs must fail. Whitespace,
`//` comments and `/* */` comments are skipped by the tokenizer. Successful
recognition must end at TOK_EOF. Testing TOK_NUMBER alone is insufficient:
negative tokens and numeric prefixes still need validation. Check every digit
and length before arithmetic; never overflow a conversion and then range-check.
Return nil after a diagnostic and never emit a successful AST on failure.

## Current helper signatures

The exact declarations in [helpers.json](../../test/reader_pack/helpers.json)
are checked against the source on every contract run. The executable solutions
exercise token creation, kind/text inspection, token advancement, numeric AST,
comparison AST and complete-main construction. tok_print_error takes a tokenizer
and a reader label; use it with tok_expect-based parsers for expected-token
context. pnode_require takes a PNode and capture name; generated-grammar readers
should use named captures rather than child indexes. See [READERS](../READERS.md),
[AST builders](../AST_BUILDERS.md) and [parser generator](../PARSER_GENERATOR.md)
for broader patterns; those general references are not executable pack snippets.

The key types are `tok_new(input *u8) *Tokenizer`,
`tok_kind(t *Tokenizer) i64`, `tok_text(t *Tokenizer) *u8`,
`tok_next(t *Tokenizer) void`, `ast_number(val *u8) *u8`,
`ast_ge(l *u8, r *u8) *u8`, and `ast_main_i64(expr *u8) *u8`.
AST helpers take AST strings, not numeric values or parser nodes. ast_ge needs
both operands. An arity diagnostic means repair the call before changing syntax.

## Native and browser commands

The smoke entry point records and runs the exact commands, with absolute artifact
paths, in numbered JSON receipts. Native steps are: clang the bootstrap IR; use
that seed with the current compiler source list; clang compiler.ll; compile the
reader wrapper with the new compiler; clang reader.ll; feed custom source on
stdin; compile the returned AST with --from-ast; clang and run the program.
The native wrapper returns exit 1 and no AST on reader failure.

For the browser, the same current native compiler emits compiler LLVM with
LANGOS=wasm and the web readers; clang --target=wasm32-unknown-unknown links it.
Inside Chromium, runLangCompiler builds a reader wrapper with LANGBE=wasm;
runLangProgram supplies custom source on stdin and returns its AST pointer.
The same compiler turns that AST into direct Wasm, which runLangProgram executes.
One compiled reader is reused for all cases in a stage. Browser artifacts retain
reader and program modules, AST strings, successes and diagnostics. These steps
also document the native/Wasm commands without relying on a stale downloaded build.

## Frozen comparison and limits

[training.json](../../test/reader_pack/training.json) contains public examples;
[heldout.json](../../test/reader_pack/heldout.json) was authored separately, with
new boundaries, zero/max values, comments and malformed numeric forms. Heldout
expected values are explicit, independent of either implementation. freeze.json
hashes prompts, fixtures, helpers and references. Do not update it to accept a
failed oracle. An intentional task revision needs a new protocol version.

Two fresh sessions use orders interpreter/native+Wasm and native+Wasm/interpreter.
The smoke replay executes both orders and reports each backend separately.
A later model authoring session gets only its prompt, training examples, relevant
helper documentation and broken fixture for repair; never heldout cases or
reference solutions. Its isolated evaluator receives the submitted artifact.
Record equal time, token and repair-attempt limits in the run manifest *before*
starting; use the same pinned model/version. No model evaluation is scheduled.

observations.json retains per-case correctness and read/build/run times;
repairs.json retains failing controls on all three backends and identifies the
corrected reference, verified against the full evolved oracle.
summary.json reports counts and the build identity. Compiler setup time is in
separate command receipts and must not be counted as authoring time. Wall times
here include host overhead, are uncalibrated and say nothing about model ability.
Report correctness by split, stage and backend, elapsed task time and repair
attempts; retain all failures rather than ranking by successful runs alone.

This small DSL does not support arithmetic expressions, identifiers, functions,
imports, multiple queries, signed numbers, floats, effects or a general runtime.
The interpreter is a reference for this DSL, not an interpreter for Lang. Wasm
has no effects stack switching; the native effects contract remains O0 only.
No new language-specific behavior is added to the kernel. This pack does not
revive broader LANG-AI work or authorize paid calls, outreach or deployment.

## Evaluate a submission

Use `python3 test/reader_pack/run.py evaluate --track interpreter-only --stage evolve --candidate PATH --evidence OUTPUT`
for a trusted Python module exposing `interpret(source, stage)` and returning
`{"value": integer}` or `{"diagnostic": text}`. Use `--track native-plus-wasm`
for a Lang source declaring `reader threshold(text *u8) *u8`; it must pass native
and Chromium. `--stage create` selects the original grammar. Reader submissions
may include std and this pack's common helper; keep other helpers in the submitted
file. A nonzero exit rejects a submission. evaluation.json retains all observed
values, diagnostics, elapsed times and a hash of the submitted source. Compilation
failures retain command stderr and fail immediately. This evaluator is local test
infrastructure; execute untrusted submissions only inside the separately approved
isolated environment required by the future-run protocol.
