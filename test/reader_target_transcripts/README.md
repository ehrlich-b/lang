The frozen corpus has 21 cases: two portable positive inputs and one negative
input for each shipped reader (Tiny, Calc, Forth, Minilisp, C, Flow, Minipy).
The six reader rejections preserve the complete existing diagnostic, empty AST
output and exit 1. Flow's third input is valid native code but exercises its
unsupported direct Wasm generator path: native prints 42 and returns 42; Wasm
must fail compilation with the exact frozen diagnostic. It is an assertion,
never a skipped test. This small corpus does not promise full target parity.

Build fresh compilers from this checkout, without bootstrap promotion:

```sh
make build JOBS=2
COMPILER=./out/lang_next bash web/build_compiler.sh
node test/reader_target_transcripts.js
JOBS=2 node --test test/reader_target_transcripts.js
```

The native build receipt must match HEAD, current source hashes and the compiler
binary; the browser receipt must match that source and native builder, as well
as the browser compiler and standard library hashes. COMPILER,
COMPILER_RECEIPT and COMPILER_WASM can select these verified artifacts elsewhere.
No tools or packages are downloaded. Native linking uses clang -O0 because the
native Flow generator uses effects. This test does not build or promote roots.

Each reader is compiled once per host and reused with stdin for all three
inputs. Both hosts independently execute source -> reader -> shared AST ->
final program. A test adapter renames the single main declaration, calls it,
prints its integer result and returns that result. Minilisp's boxed result is
unboxed with its own lisp_to_int runtime function. Reader-specific rules stay
in the readers and test harness. No shared code generation is changed.

Comparisons retain stdout, stderr and exit status exactly. Only CRLF becomes LF
for cross-host comparisons. Shared AST formatting ignores insignificant layout;
Flow's fl_gensym uses node addresses for __k, __rv and __send identifiers, so
those atoms are consistently alpha-renamed before formatting for comparison.
Strings, spans, numeric values and other identifiers are preserved. Neither
host's executable input is replaced by the other's normalized AST.

Set READER_TRANSCRIPT_REPORT to write a JSON report outside the source checkout.
It records exact reader/compiler/program outputs and statuses, source/compiler/
reader-module/final-module hashes, raw and adapted AST hashes, adapter hashes,
source revision, and tool versions. Generated files remain in a fresh directory
under READER_TRANSCRIPT_WORK (or the system temporary directory) for diagnosis.
READER_TRANSCRIPT_CASE or READER_TRANSCRIPT_READER selects a narrow fragment;
unknown selections fail. --check-corpus checks the seven-reader case inventory.
READER_TRANSCRIPT_CORPUS selects an alternate expectations file: changing an
expected stdout must make the corresponding test fail. The test never updates
expectations automatically and does not alter existing suites or skip lists.
