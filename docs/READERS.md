# Write a reader

Lang is a compiler compiler: give its kernel a function that turns source text
into Lang AST, and you have taught it a new language. That function is a
**reader**. The kernel supplies type checking, LLVM generation, native code,
WebAssembly, and interop with every other reader.

The smallest complete example is [`example/tiny/tiny.lang`](../example/tiny/tiny.lang):

```lang
include "std/tok.lang"
include "std/ast.lang"

reader tiny(text *u8) *u8 {
    var tokens *Tokenizer = tok_new(text);
    if tok_kind(tokens) != TOK_IDENT || !streq(tok_text(tokens), "answer") {
        return nil;
    }
    tok_next(tokens);
    if tok_kind(tokens) != TOK_NUMBER { return nil; }

    var body *u8 = ast_block1(ast_return(ast_number(tok_text(tokens))));
    return ast_program1(ast_func("main", ast_vec(), ast_type_i64(), body));
}
```

It has the whole frontend pipeline:

1. `tok_new` turns source text into tokens.
2. The reader recognizes `answer NUMBER`.
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
/tmp/tinyc example/tiny/answer.tiny -o /tmp/answer.ll
```

That is the “compiler compiler” part: `tiny.lang` is ordinary Lang code, while
`tinyc` is a native compiler produced from it. The lower-level `-c tiny` form
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

Expansion is recursive: AST emitted by one reader may contain another reader
form, and the kernel keeps expanding until only ordinary AST remains.

For a larger syntax, `#parser{}` generates recursive-descent parser functions
from a compact grammar, rewinds failed alternatives, and retains furthest-token
error context; its [quick reference](./PARSER_GENERATOR.md) documents the
notation and limits. A reader can also parse however it wants. Start here:

- [`tiny`](../example/tiny/tiny.lang): one grammar rule, one function
- [`calc`](../example/calc/calc.lang): recursive descent and operator precedence
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
token. Generated `PNode`s expose `start` and `end` byte offsets for semantic
locations.
