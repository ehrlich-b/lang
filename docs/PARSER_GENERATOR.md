# `#parser{}` quick reference

`#parser{}` turns a compact grammar into recursive-descent functions. It is a
good fit for token grammars, including alternatives that share a prefix.
For operator precedence, keep one flat rule and resolve it
with the [precedence table](#operator-precedence). For contextual syntax, copy
the manual recursive-descent pattern in
[`example/calc/calc.lang`](../example/calc/calc.lang).
For several independent errors in one source file, use the explicit
[recovery session](#collecting-errors-and-recovering). The
[capability comparison](./GRAMMAR_CAPABILITIES.md) explains where this toolkit
differs from Bison/yacc and ANTLR.

## Smallest parser

```lang
include "std/parser_reader.lang"

#parser{
    file = expr eof
    expr = number | symbol | list
    list = '(' items:expr* ')'
}

func main() i64 {
    var tokens *Tokenizer = tok_new("(add 1 2)");
    var tree *PNode = parse_file(tokens);
    if tree == nil || !tok_eof(tokens) { return 1; }
    var items *PNode = pnode_require(tree, "items");
    if items == nil || vec_len(items.children) != 3 { return 2; }
    return 0;
}
```

Each rule creates `parse_<rule>(tokens)`. A parser returns `nil` when it does
not match. Put `eof` in a whole-file rule, or check `tok_eof(tokens)` separately
at the reader boundary; a successful prefix is not necessarily a complete
program. Name the
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
file  = stmt* eof                       require the complete input
```

Built-in token names are `number`, `symbol`/`ident`, `string`, and `operator`.
With the shared scanner, `number` contains integer digits and absorbs a minus
directly followed by digits. Thus Calc accepts `answer 1 - 2`, while
`answer 1-2` produces adjacent number tokens and is rejected. The Hamiltonian
reader supplies a token stream that splits signed numbers into minus and digits
and recognizes decimals, so its subtraction does not depend on spaces. Grammar
notation alone does not change lexing.
`eof` is a reserved zero-width assertion: it matches only at the end of input
and creates a kind-0 marker with text `end of input` and an empty source span.
It does not advance the tokenizer. Repeating it stops safely, and recursion
through it is rejected like any other nullable-prefix cycle.
Quoted literals match exact token text: `'return'` matches a keyword and `'=='`,
`'->'`, or `'++'` match multi-character operators.
Single-character text such as `'x'`, `'0'`, or `'^'` follows the same rule,
independent of token kind. A literal must match one token; it does not ask the
scanner to recognize a new spelling. Literal contents are raw bytes between
the quotes, without escape decoding. Generated code safely quotes those bytes,
including backslashes and double quotes. Empty literals are rejected; use `eof`
for a zero-width end assertion or `?` for an optional element.

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
and the two can appear in the same program. `tok_new_stream` wraps a prebuilt
token vector; it is not an incremental input-streaming interface.

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

Sequences, `*`, and `+` introduce list nodes. One-byte literal markers remain
in the tree with `kind == 0`; longer literals use kind 2 for compatibility with
existing readers. Their `text` distinguishes `(` from `[` and similar syntax.
Inspect [`example/minilisp/minilisp.lang`](../example/minilisp/minilisp.lang)
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

Choice remains ordered—the first successful branch wins. A successful inner
choice is not retried merely because a later element of its enclosing sequence
fails: `part = number | number symbol` then `file = part eof` rejects `1 name`.
Place the longer alternative first, or put the whole alternatives including
their continuation in one choice. There is no global ambiguity analysis or
packrat memoization.

Direct, indirect, and
nullable-prefix left recursion are rejected at the reference that closes the
cycle; right recursion works. Use a hand-written parser when the grammar needs
semantic lookahead. Deep recursion and repeated shared-prefix exploration
remain the reader author's performance responsibility.

## Collecting errors and recovering

Generated parsers return `nil` and rewind on a failed item. A reader may collect
several independent errors with `std/parse.lang`, then refuse to lower the
partially recognized source:

```lang
include "std/parser_reader.lang"
include "std/parse.lang"

#parser{
    statement = 'add' value:number ';'
}

func recognize(text *u8) bool {
    var tokens *Tokenizer = tok_new(text);
    var session *ParseSession = parse_session_new(tokens, 8);
    while !tok_eof(tokens) && parse_begin(session) {
        var item *PNode = parse_statement(tokens);
        if item == nil {
            parse_report(session);
            if parse_sync_text(session, ";", true, 1024) == PARSE_SYNC_LIMIT {
                break;
            }
        }
        // Store successful items here; lower them only after the error check.
    }
    if parse_has_errors(session) {
        parse_print_diagnostics(session, "myreader");
        return false;
    }
    return tok_eof(tokens);
}
```

For `add ;` followed by `add word;`, this reports both located `expected number`
errors. It can continue recognizing a later correct statement but still fails
the whole reader invocation. The complete runnable example is
[`example/workshop/workshop.lang`](../example/workshop/workshop.lang).

`parse_begin` clears speculative expectations before each independent item;
it returns false once the diagnostic limit is reached. Do not call it inside
generated alternatives. `parse_report` copies offset, line, byte column,
expected text and found text into an immutable `ParseDiagnostic`, available
through `parse_diagnostic_count` and `parse_error_at`. Its limit is clamped to
1–256. Clearing the tokenizer for the next item cannot mutate earlier errors.

`parse_sync_text(session, boundary, consume, budget)` scans from the parser's
rewound position to one exact token text. `parse_sync_kind` instead matches a
token kind, including synthetic layout boundaries. The return value is
`PARSE_SYNC_FOUND`, `PARSE_SYNC_EOF`, or `PARSE_SYNC_LIMIT`. A budget must be
1–65536 and bounds the number of non-boundary tokens discarded. `consume=true`
also advances past the boundary. With `false`, its enclosing parser must
consume the boundary before retrying, to ensure progress.

This is explicit panic synchronization, not automatic correction. It does not
insert tokens, infer follow sets, balance nested delimiters, or guarantee every
later error is independent. Pick boundaries appropriate to the language; a
semicolon inside a nested construct may need a reader-specific nesting policy.
Always reject output when the session has errors. Recovered trees are useful
for diagnostics, not permission to emit a partially valid executable.
The caps bound recovery diagnostics and discarded tokens, not source length,
generated-parser recursion depth, or shared-prefix backtracking complexity.

## Operator precedence

A left-recursive expression grammar is rejected by `#parser{}`. You can write
a non-left-recursive ladder yourself, or keep one flat rule and give the
operators their binding powers in `std/prec.lang`:

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

Operands and operators go into one list in source order, so their position is
what says which is which. An operator pushed where an operand was expected is a
**prefix** operator, declared with `prec_prefix`:

```lang
#parser{
    expr   = pre:preop* first:unary rest:oprest*
    oprest = op:operator pre:preop* right:unary
    preop  = 'not'
}
```

A prefix level binds everything tighter than itself, so declaring `not` above
the comparisons makes `not a == b` mean `not (a == b)` with no hand-written
tier—and makes `a == not b`, where it would bind too loosely, an error.

`prec_assign` declares assignment: right-associative, its own kind because the
shared AST spells it `(assign target value)` rather than `(binop = ...)`, and
`<op>=` lowers to `lv = lv <op> rhs` when `<op>` is declared on the same table.
Because assignment is a statement and not an expression, `prec_build_stmt`
builds one—returning `(assign ...)` or `(expr_stmt ...)`—and `prec_build`
refuses one, which is what makes `f(a = b)` a diagnostic rather than a tree the
backend cannot emit.

The helper owns the ladder and the climb. Walking your own parse tree and
emitting operands stays reader-local, which is where language-specific
exceptions—postfix operators, a ternary tail—belong.

The grammar itself is checked before code generation. Missing `=`, groups or
capture elements, trailing `|`, duplicate rules or captures, undefined rules,
and left recursion report `#parser:line:column` at the offending grammar token.
They do not fall through to a missing function, a broken reader wrapper, or a
parser that recurses forever.

`#parser{}` generates recognition and failure context. The reader still owns
semantic validation, the wording around that context, lowering, and the final
shared AST.
