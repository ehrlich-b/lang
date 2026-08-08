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

Run it alongside the regular compiler:

```bash
LANGBE=llvm ./out/lang run example/tiny/tiny.lang example/tiny/answer.tiny
echo $?    # 42
```

Or mint a compiler that understands `.tiny` directly:

```bash
LANGBE=llvm ./out/lang -c tiny example/tiny/tiny.lang -o /tmp/tinyc.ll
clang -O2 /tmp/tinyc.ll -o /tmp/tinyc
/tmp/tinyc example/tiny/answer.tiny -o /tmp/answer.ll
```

That is the “compiler compiler” part: `tiny.lang` is ordinary Lang code, while
`tinyc` is a native compiler produced from it.

## The reader contract

```lang
reader name(text *u8) *u8 { ... }
```

The input is the text inside `#name{...}`, or the full contents of a `.name`
file. The result is an AST S-expression. Return an expression node when the
reader is used inside an expression; return `(program ...)` for a whole file.
Use [`std/ast.lang`](../std/ast.lang) to build the result instead of assembling
S-expressions by hand.

Expansion is recursive: AST emitted by one reader may contain another reader
form, and the kernel keeps expanding until only ordinary AST remains.

For a larger syntax, `#parser{}` generates recursive-descent parser functions
from a grammar; [`std/parser_reader.lang`](../std/parser_reader.lang) documents
its grammar notation. A reader can also parse however it wants. Start here:

- [`tiny`](../example/tiny/tiny.lang): one grammar rule, one function
- [`forth`](../example/forth/forth.lang): flat words and a compile-time stack
- [`minilisp`](../example/minilisp/minilisp.lang): expressions and closures
- [`minipy`](../example/minipy/minipy.lang): indentation-sensitive blocks
- [`C`](../example/c/c.lang): a broad imperative grammar
- [`flow`](../example/flow/flow.lang): generators lowered to algebraic effects

Keep the reader in three layers—parse, lower, emit—and test the smallest source
that exercises each new construct. The generated reader executable and wrapper
source live in `${LANG_CACHE:-.lang-cache}/readers/` when debugging.
