# Write a reader with an AI assistant

Start with a small language and a written contract. A Lang reader turns source
text into the shared AST; the compiler supplies the backend. Keep syntax and
language-specific runtime behavior in the reader and its runtime.

## Give the assistant the right source

Record the full checkout commit with `git rev-parse HEAD`. Read these files from
that same checkout so helper signatures and examples agree:

| Need | Reference |
| --- | --- |
| Build and compiler selection | [Building](BUILDING.md) |
| Reader input, output and source spans | [Reader guide](READERS.md) |
| AST constructors | [AST builders](AST_BUILDERS.md) |
| Grammar notation and named captures | [Parser generator](PARSER_GENERATOR.md) |
| Executable create, evolve and repair tasks | [Authoring pack](reader-pack/README.md) |
| Target limits | [Profiles](PROFILES.md) and [executed borders](BORDERS.md) |

Use `make build` for current compiler source and `out/lang_next` for the result.
`out/lang` is the preserved stable compiler; an existing binary alone does not
prove that it contains working-tree changes. Follow the building guide for
platform requirements and the reader guide for a first reader. A native success
does not establish direct WebAssembly support; check each target separately.

The pack has a quick offline check for its frozen inputs and current helper
signatures. Run it from the repository root:

```bash
python3 test/reader_pack/run.py contract
```

The pack's separate smoke command builds current native and browser compilers,
runs supplied solutions and rejects deliberately broken ones. Follow its
prerequisites and keep evidence outside the checkout. Its reference replay is
not a measurement of an assistant's ability.

## Start with a precise task

Copy this task outline and fill in the language-specific fields:

> Build a reader named NAME for the grammar GRAMMAR. Accepted examples are
> EXAMPLES, with these exact values or output bytes: EXPECTED. Reject these
> inputs: INVALID. Use this checkout's reader, AST-builder and tokenizer APIs.
> Consume the entire input, validate numeric bounds before conversion, and
> return no successful AST after a diagnostic. Preserve source byte spans for
> errors. Keep parse, lower and emit steps separate. Include a positive fixture,
> a malformed-input fixture and a trailing-input fixture for each new construct.
> State which targets were executed and which features remain unsupported.

Generated parsers should use named captures with `pnode_require`, rather than
guessing child positions. Manual readers should use `tok_note_expected` on a
mismatch and `tok_expect_end` after a successful parse. Use `ast_span` when an
emitted node can retain its custom-source range. Check the current declarations
before calling these helpers; AST constructors take AST strings, not tokenizer
or parser objects.

Make one construct work before adding another. Inspect the shared AST with
`lang read`; then compile and execute it. On failure, keep the exact command,
exit status and diagnostic, reduce the input, and rerun both the original
failure and a valid neighbor after the repair. See [Support](SUPPORT.md) for a
report template and instructions for reporting a wrong answer.

## Interpret evidence honestly

The [frozen protocol](../test/reader_pack/protocol.json) defines matched Python
interpreter and Lang native-plus-Wasm tasks, training examples, held-out cases,
counterbalanced orders and separate correctness, time and repair metrics. The
tracks produce different artifacts; report those differences. Keep compiler
setup time separate from authoring time and retain failures.

A supplied reference passing the oracle does not show that Lang beats Python
for AI authoring. A measured trial needs fresh isolated authoring sessions,
an evaluator whose held-out cases are inaccessible to them, equal recorded
limits and a pinned model/version. The protocol currently disables those future
runs until its budget and isolation prerequisites are met. Do not expose the
held-out fixtures or reference solutions to an authoring session and then
describe its result as held-out performance.
