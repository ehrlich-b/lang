# Rill v1: a modest keyword dialect of Lang

Rill reuses Lang's lexer, parser, AST and native semantics. It is a second
surface syntax for small compiler modules, not a novel semantic language or a
claim of whole-compiler self-hosting. `compiler-module.rill` implements a real
complete-token decimal parser, with pre-multiplication overflow checks, error
offsets and a reader declaration that uses it. The executable exercises that
reader and accepts one decimal argument, printing its value (exit 0) or the
first invalid byte offset (exit 65).

The five changed reserved words are:

| Rill | Lang |
| --- | --- |
| `fun` | `func` |
| `local` | `var` |
| `record` | `struct` |
| `use` | `include` |
| `syntax` | `reader` |

Those five Lang spellings are rejected as syntax. All five Rill words are
reserved everywhere outside comments and literals, including parameter/field
names. Longer identifiers such as `funny` stay identifiers. No raw source
replacement or arbitrary embedded Lang blocks are accepted.

The exact v1 subset is the shared parser's complete-program grammar restricted
to these tokens: identifiers, decimal integers and character/string literals;
`fun`, `local`, `record`, `use`, `syntax`; `if`, `else`, `while`, `return`,
`true`, `false`, `nil`, `break`, `continue`, `pub`, `fn`, `cast`, `bitcast`;
`i8/i16/i32/i64`, `u8/u16/u32/u64`, `bool`, `void`; and
`+ - * / % & ! = == != < > <= >= && || ( ) { } [ ] , ; . : | ^ << >>`
and `+= -= *= /= %=`. This includes typed functions, records, raw pointers,
function pointer types/lambdas, calls, field/index access, assignments, loops,
branches and reader declarations with Lang's semantics and constraints.
There is no top-level expression mode. Enums/match, effects, macros/quotes,
reader invocations (`#name{...}`), require/import, extern, let/in, closures,
floating point and `:=` are outside this subset and rejected before parsing.
`rill_supported` is the executable token allowlist; grammar-invalid sequences
still fail the shared parser and the entire input must be consumed.

`use "path.lang"` lowers to a normal include node. Included support files use
Lang syntax and the existing host's path resolution, deduplication and include
origin chain. Rill-to-Rill includes and a separate module resolver are not
implemented. The example uses the actual `std/core.lang` and `std/ast.lang`
libraries; it does not hide a compiler implementation in a Lang block.

The frontend changes only token kinds, retaining lexeme pointers, lengths and
line/byte columns into the untouched UTF-8 input. Comments remain in the source
snapshot; as in Lang, they are trivia and are absent from the AST. String
escapes retain the shared lexer's spelling until normal AST decoding; character
literals undergo the shared lexer's ordinary numeric normalization. A general,
opt-in `ast_emit_program_with_origins` service serializes existing parser
origins as relative `(span start end node)` wrappers. The host binds them to the
actual guest file. Parser point locations remain zero-width spans; this does
not invent full ranges for every node. Nodes without their own parser origin
inherit the containing source location through the existing interchange host.

From the repository root on Linux x86-64 with Python 3, Make, Clang and a linker:

```sh
export JOBS=2 LANGBE=llvm LANGOS=linux
make init
make build
out/lang_next read example/rill/rill.lang example/rill/compiler-module.rill
out/lang_next compiler rill example/rill/rill.lang -o out/rillc
out/rillc example/rill/compiler-module.rill -o out/rill-module.ll
clang out/rill-module.ll -o out/rill-module
out/rill-module 9223372036854775807
# Rejected with a located parser error and exit 1:
out/rillc example/rill/invalid.rill -o out/invalid.ll
```

The compiler emits LLVM; Clang performs the final native link. Includes require
the support sources at compilation time. These are trusted native readers,
without a sandbox claim. The minted compiler can emit LLVM with an empty tool
PATH, and includes the Rill frontend itself.

Run `python3 -B test/reader_author/rill.py --case compiler-module` to replay only
this fragment from a committed clone. It limits itself and all children to two
CPUs, JOBS=2 and 2 GiB of address space, retaining command, stdout/stderr, exit,
source/tool/artifact hashes and assumptions outside the checkout at
`../evidence/rill-<unique-id>` (or `--evidence DIR`). It checks positive and
negative decimal boundaries, AST equivalence with Lang, unchanged literal and
comment bytes, token positions, backend source origins, syntax rejection and
its own failed-expectation exit. For the fragment gate select
`env JOBS=2 VERIFY_CASE=rill make verify`. Plain `make verify` retains integration
fixed points and suites, which are separate from this fragment.
