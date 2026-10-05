# Reader errors point home

A reader's syntax and lowering failures now lead back to its own input. The
shared `std/reader_error.lang` toolkit accepts original source plus a byte span;
C, Flow, Forth, Minilisp, and Minipy use it rather than printing bare sentences
or carrying their own newline counter. Missing spans stay unlocated. The
helper stops at EOF for an oversized offset and does not choose a termination
policy for its caller.

Forth's stack checks carry the operation node through pop, call, shuffle, and
conditional lowering. Its parenthesized-comment normalization preserves
newlines as well as byte offsets. A multiline or non-ASCII comment therefore
cannot move a diagnostic. Reader parse guards stop failed or incomplete trees
before lowering. At successful Minilisp parses with trailing input, the parser
records an end-of-input expectation at the unconsumed token, rather than
reporting a speculative failed match inside the completed form.

The native C test uncovered a deeper compiler bug: LLVM's `&c` preferred the
reader function named `c` over the local byte `c` in `eprint_i64`. Diagnostics
printed bytes from the function's machine code instead of digits. Address
lookup now respects local and parameter shadowing before looking for a
function. The dedicated regression fails on the preserved starting compiler
and passes on the candidate; taking an actual function address still works.

The browser workbench maps each shipped reader's diagnostic label to the
custom-source editor. Selection converts UTF-8 byte columns to UTF-16 textarea
indices, so `café` and an emoji before the error do not select the wrong byte.

Verification on Bryan's ARM64 Mac:

- Native LLVM aggregate after the archive guard: 233/233 checks, six platform skips.
- LLVM-to-wasm aggregate: 176 passed, zero failed, 21 intentional skips.
  Homebrew LLVM must be first on PATH; Apple's clang cannot link these modules.
- Shared diagnostic corpus: 20 rejections across all five readers, in native
  extracted readers and browser reader modules. Native coverage also mints a
  Forth compiler, rejects bad input without output, and executes corrected
  source to 42. Helper checks cover missing source/node/span, EOF clamping,
  and replacing context between invocations.
- Browser compiler, direct-wasm, editor, shipped-reader, and target-runtime
  gates passed. The browser compiler grows from 612,860 to 612,992 bytes.
- A live local headless Chromium smoke check selected the expected text for
  each of the five readers. Build-to-error runs took 64–146 ms; corrected Forth
  took 69 ms, and a source-only rerun took 40 ms. These are one bounded smoke
  run, not a performance benchmark. The screenshot and timings are retained
  in `out/reader-diagnostic-ui.png` and `out/ui-smoke.json`.
- Independent review found the trailing-input issue above, confirmed its fix
  in native and direct wasm, checked extra aggregate/let shadow cases, and
  reported no remaining blocking findings.

Diagnostic columns remain byte-based. Precedence helpers may first emit their
own explanation, followed by the reader's located expression error. Reader
context is synchronous shared state; nested asynchronous reader invocations
would need explicit context handling. The pure printing API is available for
callers that should not use the shared context.

A fresh worktree also exposed a bootstrap archive bug: the ignored
`bootstrap/archive` parent did not exist. Failed mkdir/copy/cd commands were
ignored, so retention ran in the repository root and packed tracked
directories instead of old roots. The directories were restored exactly from
the local tarballs, and every previous root file was recovered and compared to
Git. No changes from the starting checkout were lost. The archive recipe now
creates its parent and stops on setup, copy, or directory-change failure.
Eight regressions execute the actual recipe in disposable fixtures, protecting
current roots, the stable compiler, and 25 checkout sentinel directories while
also checking archive reuse, conflicts, and retention. The original recipe
fails this gate; the repaired one passes. A second independent review confirmed
the repair and the regression fixtures.

The repaired `make bootstrap-local` completed all seven stages: LLVM and
reader-AST fixed points, Linux/macOS object checks, 233/233 tests on the exact
Mac binary, local archival, and promotion. GitHub publication was disabled.
The browser gate was rebuilt and passed using that promoted compiler.

The native five-language prime pipeline prints `POLYGLOT PASS` with the
suite's `-O0` linking policy. An additional `clang -O2` probe found an existing
effect-assembly limitation: duplicated `.Lresume0` labels stop optimized linking.
The original compiler reproduces the same failure. That optimization issue is
outside the reader-diagnostic change and remains open.
