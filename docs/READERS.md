# Write a reader

For executable create, evolve and repair exercises, use the
[reader authoring pack](reader-pack/README.md). It includes current-source build
identities and a deterministic native/browser smoke replay.

Lang is a compiler compiler: give its kernel a function that turns source text
into Lang AST, and you have taught it a new language. That function is a
**reader**. The kernel supplies type checking, LLVM generation, native code,
WebAssembly, and shared core calls between readers. Direct calls require matching
representations and ownership; see [project exports](READER_EXPORTS.md).

Start a generated-grammar reader and run its sample:

```bash
./out/lang new reader tiny
./out/lang run tiny.lang answer.tiny
echo $?    # 42
```

The command creates only `tiny.lang` and `answer.tiny`. It refuses to overwrite
either one and removes the first if it cannot finish the pair.

Inspect the frontend boundary without running codegen:

```bash
./out/lang read tiny.lang answer.tiny -o answer.ast
./out/lang --from-ast answer.ast --ast-source answer.tiny -o answer.ll
```

With no `-o`, `read` writes only the reader's shared AST to stdout, so it can be
piped into other tools. Its deterministic indentation makes diffs and snapshots
useful without changing tokens, strings, escapes, or `(span ...)` wrappers. Add
`--compact` to preserve the reader's byte-for-byte output instead. `--ast-source`
binds relative `(span START END ...)` nodes back to the custom source when the
saved AST is compiled later. The browser AST download uses the same layout.

The smallest complete example is [`example/tiny/tiny.lang`](../example/tiny/tiny.lang):

```lang
include "std/tok.lang"
include "std/ast.lang"

reader tiny(text *u8) *u8 {
    var tokens *Tokenizer = tok_new(text);
    if tok_kind(tokens) != TOK_IDENT || !streq(tok_text(tokens), "answer") {
        tok_note_expected(tokens, "answer");
        tok_print_error(tokens, "tiny");
        return nil;
    }
    tok_next(tokens);
    if tok_kind(tokens) != TOK_NUMBER {
        tok_note_expected(tokens, "number");
        tok_print_error(tokens, "tiny");
        return nil;
    }

    var value *u8 = tok_text(tokens);
    tok_next(tokens);
    if !tok_expect_end(tokens) {
        tok_print_error(tokens, "tiny");
        return nil;
    }

    return ast_main_i64(ast_number(value));
}
```

It has the whole frontend pipeline:

1. `tok_new` turns source text into tokens.
2. The reader recognizes `answer NUMBER` and checks that no tokens remain.
3. The `ast_*` calls emit a shared-AST `main` returning that number.

From a fresh clone, initialize the preserved compiler and run it:

```bash
make init
./out/lang run example/tiny/tiny.lang example/tiny/answer.tiny
echo $?    # 42
```

Or mint a native compiler that understands `.tiny` directly:

```bash
./out/lang compiler tiny example/tiny/tiny.lang -o /tmp/tinyc
/tmp/tinyc example/tiny/answer.tiny --emit=native -o /tmp/answer
/tmp/answer
echo $?    # 42
/tmp/tinyc example/tiny/answer.tiny --emit=llvm -o /tmp/answer.ll
```

That is the “compiler compiler” part: `tiny.lang` is ordinary Lang code, while
`tinyc` is a native compiler produced from it. For an editable policy reader with runtime input and the complete LLVM/link/run
route, follow the [shipping walkthrough](../example/shipping/README.md).
Minted compilers keep LLVM IR as their default on LLVM builds; `--emit=llvm`
needs no Clang on PATH. `--emit=native` uses the same host driver as `lang build`:
Linux x86-64, `LANGBE=llvm`, `LANGOS=linux`, `-O0`, and `LANG_CLANG` or `clang`
in PATH. Native failures identify the phase and guest file. A native destination
must be fresh or a previous ELF output; failed rebuilds invalidate that output.
The runtime remains embedded in either mode.

The lower-level `-c tiny` form
emits compiler IR when you need to inspect or cross-compile it.

Readers may emit calls into a Lang runtime. Embed that runtime in the compiler
instead of asking the custom reader to parse it:

```bash
./out/lang compiler minilisp example/minilisp/minilisp.lang \
  --runtime example/minilisp/lisp_runtime.lang -o /tmp/minilispc
/tmp/minilispc program.minilisp -o program.ll
```

`--runtime` expands includes at compiler-build time and stores the resulting
AST in the native artifact, so using the compiler does not need the runtime
source tree. Repeat the option to embed more than one runtime file. The same
option works with `--from-ast`, which is how the browser lab compiles AST plus
an optional editable target runtime.

## The reader contract

```lang
reader name(text *u8) *u8 { ... }
```

The input is the text inside `#name{...}`, or the full contents of a `.name`
file. The result is an AST S-expression. Return an expression node when the
reader is used inside an expression; return `(program ...)` for a whole file.
Use the [AST builder quick reference](./AST_BUILDERS.md) to build the result
instead of assembling S-expressions by hand.

The balanced form `#name{...}` counts nested braces outside quoted strings and
complete character literals. Slash bytes have no comment meaning at this
boundary: `#name{https://example.test}` passes the URL unchanged. A reader that
needs arbitrary delimiters or unmatched quotes can use `#name[N]{...}`, where
`N` is the decimal UTF-8 byte count of the body, excluding its closing brace.
For example, `#name[4]{a}b{}` passes the four bytes `a}b{`. The closing brace must
follow exactly those bytes; missing, overflowing or mismatched counts are lexer
errors. The CLI uses this counted form for non-Lang input files, so the complete
file reaches its reader without applying Lang comment or delimiter conventions.

Consume the whole input before returning an AST. After the last expected token,
advance once and require `tok_eof(tokens)`; return `nil` on extra tokens or
incomplete input. Whitespace and comments may follow the program, but
`answer 42 ignored tokens`, `answer 42 7`, `answer 42;`, and a second `answer`
program must fail. Save any token text needed for the AST before advancing.

Expansion is recursive: AST emitted by one reader may contain another reader
form, and the kernel keeps expanding until only ordinary AST remains.

For a larger syntax, `#parser{}` generates recursive-descent parser functions
from a compact grammar, rewinds failed alternatives, and retains furthest-token
error context; its [quick reference](./PARSER_GENERATOR.md) documents the
notation and limits. Name lowering inputs in the grammar (`value:number`) and
use `pnode_require(tree, "value")` instead of coupling converters to child
indexes. Singular lookup rejects multiple visible matches; use
`pnode_get_all(tree, "item")` only when repeated captures are deliberate. Label
whole alternatives (`stmt = assign:assignment | ret:returnstmt`) and dispatch
with `pnode_is(node, "assign")` instead of sniffing a leading keyword or a
child's kind; `pnode_branch(node)` names a branch the converter does not handle.
A reader can also parse however it wants.

A reader tells the scanner how its language spells a comment when it makes the
tokenizer—`tok_new_comments(text, line, open, close)`, nil for a form the
language does not have. minipy declares `#` and no block form, which also says
`//` is floor division; minilisp declares `;`; forth declares `\`. A reader that
says nothing gets lang's `//` and `/* */`. Comments are skipped between tokens,
which is why the syntax has to be settled before the first one is scanned—and
why a reader used to have to rewrite its own source text instead.

Operator precedence is shared rather than rewritten per reader: declare the
ladder with `std/prec.lang` (`prec_assign`/`prec_left`/`prec_right`/
`prec_prefix`, loosest level first), push operands and operators in source
order, and let `prec_build` shape the tree. Operands and operators go into one
list, so position says which is which: an operator pushed where an operand was
expected is a prefix operator, which is how Python's `not`—looser than the
comparisons it wraps—needs no hand-written tier. Assignment is a statement in
the shared AST, so `prec_build_stmt` builds one and `prec_build` refuses it. It
works the same from a hand-written parser and from a flat `#parser{}` rule, and
it refuses an operator the table never declared. Start here:

- [`tiny`](../example/tiny/tiny.lang): one grammar rule, one function
- [`calc`](../example/calc/calc.lang): recursive descent and a precedence table
- [`forth`](../example/forth/forth.lang): flat words and a compile-time stack
- [`minilisp`](../example/minilisp/minilisp.lang): expressions and closures
- [`minipy`](../example/minipy/minipy.lang): indentation-sensitive blocks
- [`C`](../example/c/c.lang): a broad imperative grammar
- [`flow`](../example/flow/flow.lang): generators lowered to algebraic effects

The [browser lab](https://lang.ehrlich.dev/lab.html) embeds the parser generator
in `compiler.wasm`. Its editable reader includes `std/parser_runtime.lang`, the
small target-side half containing tokens and `PNode`; the build-only grammar
generator stays in the compiler. Existing readers that include
`std/parser_reader.lang` work unchanged—the browser compiler selects the runtime
half when it builds the reader module. A collapsed target-runtime editor accepts
Lang helpers called by emitted AST without adding height until it is opened.
The direct backend also preserves address-taken locals, including parameters
and recursive calls; reader authors do not need to replace `&cursor` with manual
heap allocation for the browser.
Use the compact examples menu to load a reader, matching source, and any target
runtime without changing the lab's height. Each workspace keeps a local draft,
and a successful run exposes both reader and program Wasm downloads. Save/open
uses a versioned workspace file, so even the larger readers can be shared
without oversized URLs.

Downloaded reader Wasm is reusable: its `main` reads custom-language source
from UTF-8 stdin and returns a pointer to the emitted, null-terminated AST.
`runLangProgram(readerBytes, undefined, sourceText)` in `web/program_host.js`
is the reference host contract. The lab retains that module until reader code
changes, so editing only custom source skips the reader-build phase.

Keep the reader in three layers—parse, lower, emit—and test the smallest source
that exercises each new construct. Imports, `#parser{}` grammars, types, globals,
and helper functions may appear before or after the `reader` declaration. Lang
builds its standalone wrapper from the reader's transitive sibling dependencies,
so unrelated functions in the including program stay out. The generated
executable and wrapper source live in `${LANG_CACHE:-.lang-cache}/readers/` when
debugging.

## Errors and source locations

Syntax errors in `.lang` files report `path:line:column`. If a reader fails to
compile, Lang points to its declaration and also names the generated wrapper in
the cache. Reader-emitted AST may retain an exact custom-source range with
`ast_span(node, start, end)`; old unspanned AST still falls back to the invoking
file.

Your reader still has the best information about its own syntax. Manual readers
can track tokens directly; generated parsers retain the furthest failure. Use
`tok_print_error(tokens, "mylang")` before returning `nil` for a one-line parse
diagnostic with the custom source's line, column, expected forms, and found
token. After a successful root parse, call `tok_expect_end(tokens)` before
lowering; it rejects trailing tokens with `expected end of input` and their
exact UTF-8 byte span, replacing speculative failures from successful
alternatives. Guard this call with `if tree != nil`, as shown in the
[smallest parser](./PARSER_GENERATOR.md#smallest-parser), so a failed root
keeps its grammar expectations. Manual readers should call `tok_note_expected`
on a mismatch; without a recorded expectation, `tok_print_error` uses the
generic `expected valid token`. Generated `PNode`s expose `start` and `end` byte offsets for semantic
locations. Call `pnode_dump(tree)` after a successful generated parse to print
the complete tree—including named-capture wrappers and spans—to stderr without
mixing debug output into `lang read`'s AST stdout.

Use `tok_print_error_snippet(tokens, "mylang")` to append the offending source
line and a caret run to the same diagnostic line. New `lang new language`
projects use this helper. It preserves tabs in the padding, underlines tabs
inside the span through the next eight-column tab stop, counts Unicode 15.1
wide and fullwidth scalars as two display cells (other scalars as one), and
strips the CR from CRLF line endings. Widths are independent of the host locale;
ambiguous characters use one cell. An empty span, including EOF, gets one caret;
a multiline token is underlined through
the end of its first line. Line and column numbers remain byte based.
The helper emits a `reader-syntax-snippet` record so native hosts can map and
validate its span before displaying context. JSON diagnostics retain a single
structured record without source or caret text in the message.

For a reader-owned semantic failure, call
`pnode_print_error(node, text, "mylang", "explanation")` and stop with `exit(1)`
or return `nil`. Pass the original reader input as `text`, so skipped comments
and non-ASCII text keep their offsets. The helper prints
`mylang:line:column: explanation` with 1-based lines and UTF-8 byte columns;
nodes without a span retain a plain diagnostic. All five shipped readers share
this helper. In the browser lab, diagnostics labeled with the active reader's
name focus the custom source; the editor converts byte columns to UTF-16 before
selecting a token. Choose a **find an error** workspace to try it.

A configured block comment must close before EOF. An unfinished comment is a
lexical error: its byte span runs from the opener through EOF, and its expected
text is the configured closer. It cannot satisfy `tok_eof` or `tok_expect_end`,
and parser backtracking preserves that diagnostic. Line comments may end at EOF;
readers with no configured comments continue to receive ordinary tokens.

### Reader diagnostic records

`reader_error(code, message, source_key, text, start, end)` reports a guest
error independently of the returned AST. `source_key` is the reader name;
`text` is its exact input. Ranges are half-open UTF-8 byte offsets, with
`-1, -1` for an absent span. `tok_print_error` retains the furthest mismatch
and its exact token bytes; `pnode_print_error` uses the same record API.
Standalone use retains the existing text format. Shipping supplies stable
codes for syntax, duplicate, unknown, missing and out-of-range settings.

The native host maps the source key to the invoking file snapshot, validates
UTF-8 boundaries, and rejects diagnostics before parsing any returned AST.
`lang read ... --diagnostics=json` and minted compilers' `--diagnostics=json`
produce version 1 JSON Lines on stderr, with separate code, message, path,
source ID, optional span, category and origin chain. Source IDs are local to
a compilation and distinguish immutable snapshots, even with equal names.
Missing spans remain null. Nested expansions retain their invocation origins.
A `ReaderDiagnostic` with category 1 identifies a reader implementation error;
its guest span remains absent. Failed reader compilation uses compiler errors
at the reader source, independently of guest diagnostics.

Native wrappers and browser reader harnesses enable `reader_diagnostic_wire`.
They send bounded NUL-prefixed RDI1 records on stderr while stdout/return values carry AST.
The reserved five-byte `\0RDI1` marker starts a structured record. Printable
`RDI1`, including symbols in `pnode_dump`, remains ordinary stderr. Other stderr passes
through unchanged, including `pnode_dump` output and legacy reader errors;
plain debug output does not reject a successful reader. Records may appear
between plain stderr segments. A malformed record is fatal even when preceded
by debug output or followed by valid AST. Invalid diagnostic API calls emit a
malformed marker in wire mode so they cannot become ordinary debug text.
The 29-byte header contains a NUL byte, magic RDI1 and six little-endian u32 values:
category, start+1, end+1, code length, source-key length, message length,
followed by the three UTF-8 strings. Absent spans encode as 0,0. Keys and codes
must be nonempty; embedded NULs, unknown keys, bad lengths and invalid ranges
are rejected. Any diagnostic blocks AST, including when a reader returns a
well-formed AST anyway. This protocol validates data; trusted native readers
still run with host process authority.

The browser `runLangProgram` accepts an optional fourth reader context
`{key, path, sourceId, text, originChain}` and returns `diagnostics` alongside
text stderr. The Lab uses this host mapping; it never infers a source from a
reader-controlled filename. The UI still converts UTF-8 offsets to UTF-16
only when selecting text.

Run the bounded shipping diagnostic fragment with
`python3 -B test/reader_author/diagnostics.py --case shipping`, or
`env JOBS=2 make verify VERIFY_CASE=shipping-diagnostics`. Evidence defaults
to a unique directory outside the checkout. Full suites and compiler fixed
points remain integration checks.
Opt in to checked capture contracts with `!captures;` at the start of a
`#parser{}` block. Existing grammars keep their original trees and functions.
For each rule `r`, the generator adds:

- `schema_r_alternatives()` and `schema_r_alternative(index)` enumerate the
  top-level alternatives in source order (zero based). An unlabeled alternative
  has the empty label; an invalid index returns nil.
- `schema_r_name(index)` enumerates lexical capture names, ending with nil.
  `schema_r_capture(alternative, name)` returns a `CaptureSpec` with `minimum`,
  `maximum` (-1 means unbounded), and `mode` (1 required, 2 optional, 3 repeated).
  A field not declared in that alternative returns nil. Nested choices merge
  syntax bounds; referenced rules keep their own schemas.
- `capture_r_required(tree, name)` returns one `*PNode`;
  `capture_r_optional(tree, name)` returns one or nil;
  `capture_r_repeated(tree, name)` returns a Vec of nodes. Both `items:expr*`
  and `(item:expr)*` expose repeated elements. `+` enforces a nonempty result.

Use these accessors in lowering, for example
`capture_shipping_setting_required(setting, "value")`. They check the rule,
chosen alternative, declared accessor mode and actual count. A renamed capture,
wrong accessor mode or malformed count stops with a `reader-author capture
contract` diagnostic naming the rule and capture, before returning a pointer.
Field names remain strings so grammar edits get this diagnostic too.

Checked trees use transparent internal capture wrappers with reserved `@` names.
The six-field `PNode` layout, spans, branch dispatch, `pnode_child` and legacy
named access stay compatible. Accessors preserve referenced rule wrappers so
another checked accessor can read the nested rule; use `pnode_unwrap(node)` to
read an atom returned by a referenced rule. Capture lookup stops at referenced
rules, including recursive references, and does not search their fields. These
schemas describe syntax and cardinality only; readers still own domain types,
validation and semantic meaning. Generated symbols share the existing rule-name
namespace, so choose distinct rule names when composing grammars.

Run just this fragment with `python3 -B test/reader_author/captures.py --case
contracts`, or `env JOBS=2 make verify VERIFY_CASE=contracts`. It retains command
receipts, source/tool hashes and exact output outside the checkout. Plain
`make verify` remains the integration fixed-point gate.

### Project stage inspection

`lang inspect --project path.lang-project --stage tokens|tree|core|llvm [-o output]`
selects one artifact. Diagnostics stay on stderr, including when `-o` is used.
Core is the existing reader AST, formatted with spans intact; calls into the
project runtime remain visible there. LLVM combines that core with the manifest's
runtime files and uses its native LLVM profile.

A `#parser{}` grammar can declare `!inspect complete_input_rule;` alongside
`!captures;`. The generator records this boundary and emits inspection hooks only
for that rule. It must be the reader's complete-input entry, not an internal
expression rule. The real reader still constructs the tokenizer (including
custom streams/comment rules), then calls its generated parser normally. Tokens
capture that stream; tree validates end of input and dumps the resulting PNode
before lowering. Recursive calls to the boundary rule finish before the outer
entry is captured. No source-text or core-AST reconstruction stands in for a tree.
Readers without an explicit generated boundary report those syntax stages as
unsupported. Choose core or LLVM for such readers.

Syntax requests are activated only by the reader worker entry point. Embedded
readers, including minted standalone compilers, produce their normal core even
when the caller has inherited `LANG_INSPECT_STAGE=tree` or `tokens`.

## Native debug lines

Pass `-g` when emitting LLVM IR, then link that IR with clang:

```bash
LANGBE=llvm ./out/lang -g example/polyglot.lang -o polyglot.ll
clang -O0 polyglot.ll -o polyglot
llvm-dwarfdump --debug-line polyglot
```

Each source file gets a DWARF compile unit and each located function a
subprogram. Instructions carry line locations from the shared node origins;
LLVM turns these into native address-to-source line tables. Reader names and
syntax rules are absent from this backend policy. Minted reader compilers also
accept `-g`.

`ast_span(node, start, end)` preserves a half-open UTF-8 byte range in the
reader's original input. The adapter binds that range to the input's source ID;
the backend uses its immutable line index to derive 1-based lines and byte
columns. Inline `#reader{...}` offsets are rebased to the containing source
file, including the opening line's column. Separate custom input files retain
their own names, even when several readers contribute to one binary. Forth
retains definition and call spans; the other shipped readers also preserve
statement and definition spans where they lower those constructs.

Generated children without explicit spans inherit their enclosing location.
Unspanned reader output has only the adapter's invocation fallback; emit spans
for statements that need exact stepping. Plain AST without source origins gets
no invented locations. For saved reader AST, supply `--from-ast --ast-source
original.ext` to bind its spans. This emits line tables and function names,
without variable inspection or a promise that optimized-away statements remain
steppable. Debug modules containing effects keep all functions unoptimized to protect the
nonlocal transfers, even when linked with `clang -O2`. Without `-g`, the existing
effects optimization restriction still applies and LLVM output is unchanged. `python3 test/run_debug_info.py` checks
exact unoptimized line rows, optimized file retention, IR verification, and
native execution; add `--base-ref REV` to compare non-debug IR byte for byte.

### Opt-in guest source formatting

`lang project format path.lang-project [-o output]` prints the entry in its
reader's guest syntax. It requires a reader that explicitly publishes a layout
recipe; a handwritten reader without one gets `unsupported format`. There is
no shared-AST-to-guest fallback: lowering may erase syntax, order and trivia.
Output goes to stdout or the named file, with no status text. Parsing and
validation finish before publication or opening the output file, so malformed
input cannot be silently repaired or truncate an existing destination.

Include `std/layout_recipe.lang` and check `layout_requested()` **after** complete
parsing and language-specific validation, **before** lowering. Build a document
with `layout_new`, `layout_text`, `layout_field` (original CST byte spans), and
`layout_line` (newline followed by an explicit count of spaces). End with
`layout_publish`, which returns the private source artifact to the project host.
The reader chooses fields, repetition order, punctuation and indentation. The
host writes the published bytes exactly, including the presence or absence of a
final newline, to both stdout and `-o`. The library has no language-specific
rules and does not inspect shared core nodes.
Readers own the validity and round-trip contract of their recipes.

The [shipping recipe](../example/shipping/shipping.lang) uses checked named
captures, preserves setting order and decimal spelling (including leading
zeros), indents settings by four spaces, and emits a final newline. Its
parse-format-parse semantic model is unchanged and formatting is byte-idempotent.
It calls `layout_whitespace_only` on its actual tokenizer, refusing comments
anywhere with a located `unsupported-trivia` error. Ordinary shipping parsing
still accepts comments. A recipe that retains comments must place their source
spans explicitly instead of calling this refusal helper. This helper checks
skipped gaps between tokens; it does not infer trivia rules from a second lexer.

Run the focused fragment with `JOBS=2 python3 -B test/reader_author/format.py --case shipping`
or `VERIFY_CASE=format JOBS=2 make verify`. It records command exits, stdout,
stderr, source/tool hashes and resource limits outside the checkout. Full
bootstrap fixed points remain part of integration verification.

### Embedded runtime exports and reachability

A minted compiler retains runtime functions referenced by the emitted guest
program, including function values stored in global initializers. The explicit
artifact export set consists of `pub func` declarations in the files passed to
`--runtime`. These functions remain available to external callers even if no
guest function calls them. A public wrapper in a supplied runtime file can
export a helper from an included module. `pub` declarations inside transitively
included modules describe module visibility; they do not automatically become
external entry points of each minted artifact.

Runtime globals, their initializers, types and every guest declaration remain
included. Function references retain all matching overloads. Indirect or
unresolved calls, opaque syntax, pointer casts and reachable foreign imports keep
the whole runtime by default. Even a libc-compatible name and ABI do not establish
its implementation: an interposed `write` may call an otherwise unused helper.
This conservative fallback also preserves diagnostics and supports runtimes whose
dependencies cannot be determined statically. The same boundary applies to
`--from-ast --runtime`.

A build that controls its foreign implementations may repeat `--runtime-leaf NAME`
with `compiler` or `--from-ast --runtime`. Each entry is an explicit contract that
**every linked implementation of that symbol has no hidden runtime dependencies**,
including callbacks or dynamic symbol lookup. The contract is embedded with the
minted runtime, and applies to all overloads of that symbol. It does not follow
from a declaration's name, ABI or module origin. Omit the option when interposition
or other linkage makes that assertion uncertain; the complete runtime is retained.
Indirect calls and other unknown dependencies still force full inclusion.

For the shipping example linked against ordinary system libc with no interposition,
`--runtime-leaf write --runtime-leaf exit --runtime-leaf calloc` states the foreign
leaf contracts needed to prune unused standard helpers. Without those explicit
contracts shipping retains the complete runtime and has the same output.
