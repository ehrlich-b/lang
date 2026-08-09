# `#parser{}` quick reference

`#parser{}` turns a compact grammar into recursive-descent functions. It is a
good fit for prefix syntax and rules whose alternatives start differently. For
operator precedence, contextual syntax, or precise diagnostics, copy the manual
recursive-descent pattern in [`example/calc/calc.lang`](../example/calc/calc.lang).

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
Quoted one-character literals match punctuation tokens. Longer quoted literals
match identifier text, so `'return'` is a keyword match.

## Parse tree

Generated functions return `*PNode`:

```lang
struct PNode {
    kind i64;       // 0 marker, 1 number, 2 symbol, 3 string, 4 list, 5 operator
    text *u8;       // atom or literal text
    children *u8;   // Vec of *PNode for sequences/repetitions
}
```

Sequences, `*`, and `+` introduce list nodes. Literal markers remain in the
tree with `kind == 0`; their `text` distinguishes `(` from `[` and similar
syntax. Inspect [`example/minilisp/minilisp.lang`](../example/minilisp/minilisp.lang)
for helpers that unwrap this shape, then lower it with the
[AST builders](./AST_BUILDERS.md).

## Current boundary

The generated parser does not rewind the tokenizer between alternatives. Keep
choice prefixes disjoint: `number | symbol | list` is safe; two branches that
both begin with `'if'` are not. Left recursion is also unsupported. Factor a
shared prefix into one rule, or use a hand-written parser when the grammar needs
lookahead, precedence, recovery, or custom error messages.

`#parser{}` generates recognition only. The reader still owns validation,
diagnostics, semantic lowering, and the final shared AST.
