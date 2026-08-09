# `#parser{}` quick reference

`#parser{}` turns a compact grammar into recursive-descent functions. It is a
good fit for token grammars, including alternatives that share a prefix. For
operator precedence, contextual syntax, or recovery, copy the manual recursive-
descent pattern in [`example/calc/calc.lang`](../example/calc/calc.lang).

## Smallest parser

```lang
include "std/parser_reader.lang"

#parser{
    expr = number | symbol | list
    list = '(' expr* ')'
}

func main() i64 {
    var tokens *Tokenizer = tok_new("(+ 1 2)");
    var tree *PNode = parse_expr(tokens);
    if tree == nil || !tok_eof(tokens) { return 1; }
    return 0;
}
```

Each rule creates `parse_<rule>(tokens)`. A parser returns `nil` when it does
not match. Always check both the result and `tok_eof(tokens)` at the reader
boundary; a successful prefix is not necessarily a complete program.

The browser lab uses `include "std/parser_runtime.lang"` to make the artifact
boundary visible: compiler.wasm owns the build-time generator, while the reader
module needs only tokens and `PNode`. Existing reader sources may keep
`include "std/parser_reader.lang"`; the direct browser build substitutes that
same target runtime automatically.

## Grammar notation

```text
value = number | symbol | string | list   alternatives
list  = '(' value* ')'                   sequence, zero or more
args  = value+                           one or more
item  = symbol value?                    optional
atom  = (number | symbol)                grouping
stmt  = 'return' value ';'               keyword and punctuation literals
```

Built-in token names are `number`, `symbol`/`ident`, `string`, and `operator`.
Quoted literals match exact token text: `'return'` matches a keyword and `'=='`,
`'->'`, or `'++'` match multi-character operators.

## Parse tree

Generated functions return `*PNode`:

```lang
struct PNode {
    kind i64;       // 0 marker, 1 number, 2 symbol, 3 string, 4 list, 5 operator
    text *u8;       // atom or literal text
    children *u8;   // Vec of *PNode for sequences/repetitions
    start i64;      // zero-based byte start in reader input
    end i64;        // exclusive byte end
}
```

Sequences, `*`, and `+` introduce list nodes. Literal markers remain in the
tree with `kind == 0`; their `text` distinguishes `(` from `[` and similar
syntax. Inspect [`example/minilisp/minilisp.lang`](../example/minilisp/minilisp.lang)
for helpers that unwrap this shape, then lower it with the
[AST builders](./AST_BUILDERS.md). Terminal nodes carry their token range;
composite nodes inherit the first and last child range. Pass either range to
`ast_span(...)` when the emitted node should retain an exact semantic location.

## Alternatives and errors

Alternatives are ordered and transactional. If a branch fails after consuming
tokens, the next branch restarts at the same token:

```text
action = 'do' symbol '=' number | 'do' symbol '(' number ')'
```

Sequences succeed only when every required element matches; `?` elements may be
absent. Failed sequences rewind as a unit. `*` and `+` also stop safely if their
child can match without consuming input.

On failure, the tokenizer retains the furthest mismatch across tried branches:

```lang
var tree *PNode = parse_action(tokens);
if tree == nil {
    tok_print_error(tokens, "mylang");
    return nil;
}
```

That prints, for example, `mylang:2:9: expected number or string, found name`.
Use the query functions when you want different wording or structured output.

`tok_error_offset` exposes the zero-based byte offset; line and column are
one-based. Expectations from alternatives failing at the same furthest token
are combined (`number or string`).

Choice remains ordered—the first successful branch wins—and left recursion is
unsupported. Use a hand-written parser when the grammar needs precedence,
semantic lookahead, or error recovery.

`#parser{}` generates recognition and failure context. The reader still owns
semantic validation, the wording around that context, lowering, and the final
shared AST.
