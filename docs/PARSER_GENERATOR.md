# `#parser{}` quick reference

`#parser{}` turns a compact grammar into recursive-descent functions. It is a
good fit for token grammars, including alternatives that share a prefix.
Operator precedence stays out of the grammar: keep one flat rule and resolve it
with the [precedence table](#operator-precedence). For contextual syntax or
recovery, copy the manual recursive-descent pattern in
[`example/calc/calc.lang`](../example/calc/calc.lang).

## Smallest parser

```lang
include "std/parser_reader.lang"

#parser{
    expr = number | symbol | list
    list = '(' items:expr* ')'
}

func main() i64 {
    var tokens *Tokenizer = tok_new("(add 1 2)");
    var tree *PNode = parse_expr(tokens);
    if tree == nil || !tok_eof(tokens) { return 1; }
    var items *PNode = pnode_require(tree, "items");
    if items == nil || vec_len(items.children) != 3 { return 2; }
    return 0;
}
```

Each rule creates `parse_<rule>(tokens)`. A parser returns `nil` when it does
not match. Always check both the result and `tok_eof(tokens)` at the reader
boundary; a successful prefix is not necessarily a complete program. Name the
children used by lowering and retrieve them with `pnode_get` or
`pnode_require`; `pnode_child(node, index)` remains available for old grammars.

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
decl  = 'var' name:symbol '=' value:expr  named captures for lowering
suite = <indent> stmt+ <dedent>          a token kind the reader supplies
```

Built-in token names are `number`, `symbol`/`ident`, `string`, and `operator`.
Quoted literals match exact token text: `'return'` matches a keyword and `'=='`,
`'->'`, or `'++'` match multi-character operators.

## Supplying your own tokens

A generated parser asks the tokenizer only for the current token's kind, text
and span, and for a mark it can rewind to. Nothing requires the tokenizer to be
what produced the token, so a language that cannot be parsed by scanning
left to right — layout, a preprocessing pass, a lexer that needs to know what
the parser already decided — can lex itself and hand the result over:

```lang
var TOK_INDENT i64 = TOK_USER;
var TOK_DEDENT i64 = 101;

#parser{
    suite = <indent> body:stmt+ <dedent>
}

var toks *u8 = tok_stream_new();
tok_stream_push(toks, TOK_INDENT, offset, 0, "indent");   // synthetic
tok_stream_push(toks, TOK_NUMBER, start, len, nil);       // spans real source
var t *Tokenizer = tok_new_stream(source, toks);
var tree *PNode = parse_suite(t);
```

A token is `(kind, start, len, text)`. The span points into the same source
string the reader was given, so error locations and AST spans stay exact even
for tokens the source does not literally contain; `text` is `nil` for a token
that reads as the bytes it spans, and names one that spans none. Custom kinds
start at `TOK_USER`, which the built-in scanner never produces — a grammar
writing `<indent>` can therefore only match a token a reader put there. An
undeclared `<foo>` is an ordinary undefined-identifier error for `TOK_FOO`.

Everything else is unchanged: `tok_new` still scans, backtracking still rewinds,
and the two can appear in the same program.

## Parse tree

Generated functions return `*PNode`:

```lang
struct PNode {
    kind i64;       // 0 marker, 1 number, 2 symbol, 3 string, 4 list, 5 operator
    text *u8;       // atom or literal text
    children *u8;   // Vec of *PNode for sequences/repetitions
    start i64;      // zero-based byte start in reader input
    end i64;        // exclusive byte end
    branch *u8;     // label of the alternative that built it, or nil
}
```

Sequences, `*`, and `+` introduce list nodes. Literal markers remain in the
tree with `kind == 0`; their `text` distinguishes `(` from `[` and similar
syntax. Inspect [`example/minilisp/minilisp.lang`](../example/minilisp/minilisp.lang)
for helpers that unwrap this shape, then lower it with the
[AST builders](./AST_BUILDERS.md). Terminal nodes carry their token range;
composite nodes inherit the first and last child range. Pass either range to
`ast_span(...)` when the emitted node should retain an exact semantic location.

When recognition succeeds but lowering is wrong, inspect that boundary before
changing child indexes or converters:

```lang
var tree *PNode = parse_assignment(tokens);
pnode_dump(tree);
```

`pnode_dump` writes only to stderr, leaving a reader's AST output untouched. It
shows every node's kind, `<branch>` label, quoted token text, capture wrapper,
and byte span with two-space nesting, so native and browser runs produce the
same diffable tree.

## Named captures

Prefix any grammar element with `name:` when lowering cares about its meaning:

```lang
#parser{
    assignment = target:symbol '=' value:expr
    call = callee:symbol '(' args:expr* ')'
}

var target *PNode = pnode_require(tree, "target");
var value *PNode = pnode_require(tree, "value");
var args *PNode = pnode_get(tree, "args");
var items *u8 = pnode_get_all(tree, "item");
```

The modifier belongs to the capture, so `args:expr*` returns the whole
repetition list. `pnode_get` returns `nil` for an absent optional capture.
`pnode_require` also returns `nil`, but first prints the exact missing name as a
reader-lowering error. Captures may use the same names in different choice
branches. A name may occur only once on any one branch; otherwise `pnode_get`
would have no honest answer.

`pnode_get` and `pnode_require` also reject multiple matches that become visible
through repetitions or referenced rules; they never choose the first silently.
Use `items:expr*` when lowering wants one captured list. Use `(item:expr)*` with
`pnode_get_all(tree, "item")` when each repeated result needs its own label; the
returned Vec is empty when there are no matches.

Capture wrappers are an internal `PNode` kind and do not change the tree of a
grammar that has no captures. `pnode_child` transparently unwraps them, so a
rule can migrate one element at a time without renumbering its positional
children. Code that opts into captures should prefer the helpers over walking
the raw `children` vector at captured edges.

## Labeled alternatives

Name a whole alternative to say which one matched. Without that, lowering has to
re-derive it from a leading keyword's text or from a child's `kind`, which
couples converters to grammar order:

```lang
#parser{
    stmt    = assign:assignment | call:callexpr | ret:returnstmt
    primary = num:number | sym:symbol | paren:parenexpr
}

if pnode_is(node, "assign") { ... }
if pnode_is(node, "num") { return ast_number(node.text); }
```

A label on a whole alternative records the name **on** the chosen node instead
of wrapping it. That is what makes it survive: `pnode_child`, `pnode_get`, and
`pnode_require` all unwrap captures, so a wrapper would vanish exactly where
lowering wants to ask. Nothing is inserted into the tree, so positional access
and existing grammars are unaffected.

`pnode_branch(node)` returns the label itself, or `nil` when the grammar left
the alternative unlabeled. Use it to report a branch the converter does not
handle — a reader that emits a placeholder for an alternative it forgot turns
its own gap into a mystery in the generated program.

From the parent, a labeled alternative answers to `pnode_get`/`pnode_require`
like any other name, so `(value:number | value:symbol)` still yields one
`value`. Alternatives may share a label; a label may occur only once on any one
branch. A labeled alternative may not resolve to a rule that labels its own
alternatives — one node cannot carry two branch names — and that is rejected at
the grammar, not at lowering.

That restriction is usually not a loss: leave the outer alternative unlabeled
and the inner label still answers. The C reader's switch body does exactly this,
because a switch item is either a `case`/`default` label or an ordinary
statement, and a statement already says what kind it is:

```lang
c_stmt       = ret:c_retstmt | if:c_ifstmt | ... | expr:c_exprstmt
c_switchitem = case:c_caseval | default:c_defaultlabel | c_stmt
```

## Alternatives and errors

Alternatives are ordered and transactional. If a branch fails after consuming
tokens, the next branch restarts at the same token:

```text
action = 'do' symbol '=' number | 'do' symbol '(' number ')'
```

Sequences succeed only when every required element matches; `?` elements,
including named ones such as `else_part:else_clause?`, may be absent. Failed
sequences rewind as a unit. `*` and `+` also stop safely if their child can
match without consuming input.

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

Choice remains ordered—the first successful branch wins. Direct, indirect, and
nullable-prefix left recursion are rejected at the reference that closes the
cycle; right recursion works. Use a hand-written parser when the grammar needs
semantic lookahead or error recovery.

## Operator precedence

A precedence ladder written as grammar rules is left-recursive, so `#parser{}`
rejects it. Write one flat rule instead and give the operators their binding
powers in `std/prec.lang`:

```lang
#parser{
    expr   = first:unary rest:oprest*
    oprest = op:operator right:unary
}

func table() *PrecTable {
    var t *PrecTable = prec_new();
    prec_left(t, "+ -");        // loosest level first
    prec_left(t, "* / %");      // each call binds tighter than the last
    return t;
}
```

Lowering walks the flat tree once, pushing operands and operators in source
order; the table decides the shape of the result.

```lang
var e *PrecExpr = prec_expr(table());
prec_operand(e, emit_operand(pnode_require(tree, "first")));
// ... for each rest item: prec_op(e, op.text) then prec_operand(e, ...)
return prec_build(e);
```

`prec_right` makes a level right-associative. `prec_of(table, text)` is 0 for
an operator the table does not list, which is how a hand-written parser decides
whether the next token continues the expression at all. `prec_build` refuses an
undeclared operator, and refuses an operator missing an operand, rather than
choosing a binding power for you.

The helper owns the ladder and the climb. Walking your own parse tree and
emitting operands stays reader-local, which is where language-specific
exceptions—postfix operators, assignment peeled off as a statement—belong.

The grammar itself is checked before code generation. Missing `=`, groups or
capture elements, trailing `|`, duplicate rules or captures, undefined rules,
and left recursion report `#parser:line:column` at the offending grammar token.
They do not fall through to a missing function, a broken reader wrapper, or a
parser that recurses forever.

`#parser{}` generates recognition and failure context. The reader still owns
semantic validation, the wording around that context, lowering, and the final
shared AST.
