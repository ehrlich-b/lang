# `#parser{}` quick reference

`#parser{}` turns a compact grammar into recursive-descent functions. It is a
good fit for token grammars, including alternatives that share a prefix.
Operator precedence stays out of the grammar: keep one flat rule and resolve it
with the [precedence table](#operator-precedence). For contextual syntax, copy the manual recursive-descent pattern in
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
    var complete bool = false;
    if tree != nil { complete = tok_expect_end(tokens); }
    if !complete {
        tok_print_error(tokens, "mylang");
        return 1;
    }
    var items *PNode = pnode_require(tree, "items");
    if items == nil || vec_len(items.children) != 3 { return 2; }
    return 0;
}
```

Each rule creates `parse_<rule>(tokens)`. A parser returns `nil` when it does
not match. After a successful root parse, call `tok_expect_end(tokens)` at the
reader boundary; a successful prefix is not necessarily a complete program.
The helper returns true at EOF. With input remaining, it keeps the furthest
recorded mismatch if that mismatch lies beyond the remaining token's start;
otherwise it reports `expected end of input` at the remaining token. Both errors
include the exact UTF-8 byte span. For example, with `file = line*` and
`line = symbol '=' number`, `a = 1\nworkers 4\n` reports `expected '='` at 2:9,
while `a = 1\n!` reports `expected end of input` at 2:1. Call it only when the
root is non-nil, so a failed parse keeps its furthest mismatch. Use an explicit
guard as above on both native and browser hosts. Name the
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

## Reader-local lexical profiles

Declare a profile beside the grammar and pass it when creating the tokenizer.
The generated `parse_rule(tokens)` functions also accept manual token streams;
no compiler or grammar-generator special case is needed for the language.

```lang
#parser{
    setting = 'limit' value:number ';'
}

func config_profile() *TokProfile {
    return tok_profile_new(TOK_NUM_DECIMAL, nil, "//", "/*", "*/");
}

var tokens *Tokenizer = tok_new_profile(source, config_profile());
var tree *PNode = parse_setting(tokens);
```

`tok_profile_new(numbers, identifier_extra, line, open, close)` declares:

- `TOK_NUM_DECIMAL`: unsigned ASCII `[0-9]+`, including leading zeroes. Signs
  are separate punctuation tokens. Fractions (`1.5`, `.5`, `1.`), exponents
  (`1e3`, `1E-3`) and glued number/name spellings (`10base`, `0x10`, `1_000`)
  fail lexically over the complete spelling, rather than accepting a prefix.
  Numeric bounds and sign restrictions still belong to the reader's lowering.
- Identifiers start with ASCII letters or `_`, and continue with letters,
  digits, `_`, or bytes from `identifier_extra` (nil means no extra bytes).
  Keywords in quoted grammar literals match the **whole** token. For example,
  an extra `"-"` keeps `select-all` one identifier, distinct from `'select'`.
  Configured comment openers terminate an identifier even when their bytes are
  identifier continuations: with `"-"` and line marker `"--"`, `item--comment`
  yields `item` followed by a comment. A single hyphen still continues the name.
  This is a byte policy, not Unicode identifier classification.
- Comment delimiters use the existing `tok_new_comments` contract: nil disables
  a form, both block markers are required, blocks do not nest, and line comments
  may end at EOF. A comment may immediately follow a decimal or identifier token.

`tok_new_profile` snapshots these fields before scanning the first token;
independent tokenizers can use different profiles at the same time. Input text
is never rewritten. Token, tree and diagnostic spans remain half-open UTF-8
byte offsets into that exact input, including skipped comments. Invalid numeric
spellings and unclosed comments retain their lexical diagnostic across parser
backtracking and cannot satisfy `tok_expect_end`.

`TOK_NUM_DEFAULT` preserves the inherited number scanning (including negative
integer tokens and splitting `1.5` or `1e3`). `tok_new`, `tok_new_comments`,
manual `tok_new_stream`, existing grammars and checked capture schemas keep
their existing behavior. A profile changes scanning only; supplied streams
remain the reader's responsibility and are not revalidated against a profile.

See [Shipping](../example/shipping/shipping.lang) and the independent
[query reader](../test/reader_author/fixtures/lexer_profile/query.lang), which
uses `--` and `(* ... *)` comments and hyphenated identifiers. Run only this
fragment with `python3 -B test/reader_author/lexer_profile.py --case two-readers`
or `env JOBS=2 make verify VERIFY_CASE=two-readers`. The runner requires a
committed candidate, uses two CPUs and a 2 GiB address-space limit, and retains
commands, source/tool hashes, stdout, stderr and exit codes outside the checkout.
It compares complete generated trees from scanned and independently authored
manual streams, checks exact rejection ranges, exercises both reader wrappers
and the minted Shipping compiler, and retains bounded capture/default-grammar
checks. A deliberately failed expectation must exit unsuccessfully.

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
one-based. `tok_error_end_offset` is the exclusive UTF-8 byte end of that
complete token, so diagnostics can select it exactly. Expectations from alternatives failing at the same furthest token
are combined (`number or string`).

Choice remains ordered—the first successful branch wins. Direct, indirect, and
nullable-prefix left recursion are rejected at the reference that closes the
cycle; right recursion works. Use a hand-written parser when the grammar needs
semantic lookahead. Editor statement recovery is opt-in below.

## Editor statement recovery

The `@` sigil keeps existing rule names and grouped sequences unambiguous.
Declare one statement boundary with `@recover(rule, 'terminator', 'stop')`:

```lang
#parser{
    policy = 'shipping' '{' settings:setting* '}'
    setting = @recover(strict_setting, ';', "}")
    strict_setting = name:symbol value:number ';'
}
var tokens *Tokenizer = tok_new(text);
tokens.recovery = 1; // editor syntax inspection only
var partial *PNode = parse_policy(tokens);
```

Ordinary `tok_new` and `tok_new_stream` leave recovery disabled: the same form
then behaves exactly like its referenced rule. The referenced rule always runs
with recovery disabled, including its nested calls and ordered alternatives.
Successful parses return the original tree, without extra wrappers. Use recovery
at a statement boundary after choosing the surrounding construct; it deliberately
turns a failed statement into a successful error node in editor mode.

On failure, rewind the whole statement and skip through the first exact
terminator token (consumed), stopping before the enclosing stop token or EOF.
Sync declarations require two nonempty plain token literals. Use double quotes
for a brace sync literal: the host macro scanner skips double-quoted strings
when balancing the outer block. No token is
invented or fed back into recognition. The error replaces the entire failed
statement, including any recognized prefix. An empty attempt at EOF or at the
stop token returns nil. Each scan advances a token mark or stops; a further
budget of source bytes + 1 (supplied token count + 1 for streams) bounds scans.
Zero-byte synthetic tokens progress by stream index; a sticky lexical failure
stops after one attempt. Existing repetition guards bound nullable rules.

Partial trees use the existing six-field `PNode` layout and half-open UTF-8
byte spans in the immutable reader input. The LSP can walk ordinary captures
and lists and recognize this stable shape:

```text
error (kind 8, text = expected …, found …, span = discarded statement)
  skipped (kind 9, text = nil, span = exact discarded bytes including terminator)
  missing (kind 10, text = expectation set, span = [mismatch start, same start))
  mismatch (kind 11, text = expectation set, span = original offending token)
```

At EOF the mismatch is also zero-width. The missing marker describes expected
token(s), potentially an alternative set, rather than an inserted AST value.
The mismatch node's `branch` stores the original found text. Multiple error
nodes remain in source order alongside valid statements. Diagnostics live in
the tree; speculative recovery never prints them. `pnode_dump` names all four
kinds, and `pnode_has_error` lets a lowering boundary reject an entire partial
tree. These are syntax nodes, never shared core AST forms. Compiler readers
must use ordinary tokenizers and reject trees containing recovery markers
before lowering; `example/shipping/shipping.lang` demonstrates both strict
lowering and the syntax-only `shipping_partial` editor entry point. An outer
syntax error (for example a missing closing brace) can still return nil; this
form only recovers declared statements.

Run `python3 -B test/reader_author/recovery.py --case settings` for the small
native fragment. It records commands, hashes, outputs, exits and limits outside
the checkout. `VERIFY_CASE=settings-recovery env JOBS=2 make verify` selects the
same fragment; unselected verification retains its integration checks.

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
