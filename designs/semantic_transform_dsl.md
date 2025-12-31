# Semantic Transform DSL: The Last Abstraction

> "Two DSLs and glue" - the vision for trivial language implementation

## The Problem

We have `#parser{}` - a beautiful DSL for syntax. Four lines define a grammar, and you get a recursive descent parser for free. But then you're dumped into **150 lines of manual tree-walking** to produce AST.

```lang
// The beautiful part (4 lines)
#parser{
    sexp = number | symbol | operator | list
    list = '(' sexp* ')'
}

// The ugly part (150 lines)
func emit(sb *StringBuilder, node *PNode) void {
    if node.kind == 1 {
        sb_str(sb, "(number ");
        sb_str(sb, node.text);
        sb_str(sb, ")");
        return;
    }
    if is_sym(first, "defun") {
        var name *PNode = list_get(node, 1);
        var params *PNode = list_get(node, 2);
        // ... 30 more lines per construct ...
    }
    // ... repeat for every language construct ...
}
```

The ugly part is:
1. **Boilerplate-heavy**: Tree walking, kind checking, child extraction
2. **Error-prone**: Typos in S-expr strings, off-by-one in list indices
3. **Requires compiler internals knowledge**: PNode structure, AST format
4. **Obscures intent**: The *what* is buried in *how*

## What This Covers (and What It Doesn't)

**`#emit{}` is for the 80-90% case**: languages where syntax maps relatively directly to AST. Most languages fit this.

**Escape hatches exist for the other 10-20%**: desugaring, associativity folding, multi-expression bodies. These are handled by stdlib helper functions.

**Macros are out of scope**: A language with `defmacro` needs macro expansion BEFORE emission. That's a separate mechanism (see "Macros" section at the end).

---

## The Solution: `#emit{}`

The transformation from parse tree to AST is **pattern matching** followed by **AST construction**. Every emit function has this shape - we're just writing it manually each time.

`#emit{}` is a DSL for declaring these patterns:

```lang
#emit{
    // Atoms - match by parse node kind
    number($n)  => ast_number($n.text)
    IDENT($id)  => ast_ident($id.text)

    // Composite patterns - match by node kind and children
    func_decl[$name, $params, $body] => ast_func($name.text, $params, $body)
    if_stmt[$cond, $then, $else]     => ast_if($cond, $then, $else)
    binop[$left, $op, $right]        => ast_binop($op.text, $left, $right)

    // Default
    call_expr[$fn, $args*] => ast_call($fn, $args)
}
```

This generates the `emit()` function automatically.

---

## Pattern Syntax

There is ONE pattern syntax. Patterns match against the parse tree structure that `#parser{}` produces.

### Atom Patterns: `kind($var)`

Match leaf nodes (tokens) from the lexer:

```lang
number($n)   => ast_number($n.text)
IDENT($id)   => ast_ident($id.text)
string($s)   => ast_string($s.text)
operator($o) => ...
```

| Pattern | Matches when... | Binds |
|---------|-----------------|-------|
| `number($n)` | `node.kind == PNODE_NUMBER` | `$n` = the PNode |
| `IDENT($id)` | `node.kind == PNODE_IDENT` | `$id` = the PNode |

Access the string content with `$var.text`.

### Composite Patterns: `kind[$children...]`

Match nodes produced by grammar rules:

```lang
func_decl[$name, $params, $body]  => ...
if_stmt[$cond, $then, $else]      => ...
block[$stmts*]                    => ...
```

The `kind` is the **grammar rule name**. The children are the **semantic children** - punctuation is stripped by the parser.

| Element | Meaning |
|---------|---------|
| `$var` | Bind single child to `$var` |
| `$var*` | Bind zero-or-more remaining children as Vec |
| `$var+` | Bind one-or-more remaining children as Vec |
| `"literal"` | Match child whose text equals "literal" |
| `$var:kind` | Bind child and verify its node kind |

### Matching by Arity

Same node kind, different child counts = different patterns:

```lang
return_stmt[]          => ast_return(nil)        // return;
return_stmt[$val]      => ast_return($val)       // return expr;

if_stmt[$c, $t]        => ast_if($c, $t, nil)    // if without else
if_stmt[$c, $t, $e]    => ast_if($c, $t, $e)     // if with else
```

### Literal Matching in Children

Match specific content in child nodes:

```lang
list["defun", $name, $params, $body]  => ast_func(...)
list["if", $cond, $then, $else]       => ast_if(...)
list["+" , $a, $b]                    => ast_binop("+", $a, $b)
```

The `"defun"` matches a child node whose `.text` equals `"defun"`.

### Guards (Optional)

Filter matches with predicates:

```lang
list[$op, $a, $b] where is_arith($op.text) => ast_binop($op.text, $a, $b)
```

---

## Parser Cooperation: `@left_assoc`

A grammar like `add_expr = mul_expr (('+' | '-') mul_expr)*` produces a **flat list**:

```
add_expr[mul(1), OP(+), mul(2), OP(-), mul(3)]
```

But AST needs a **left-associative tree**: `binop(binop(1, +, 2), -, 3)`.

**Solution**: The parser builds the tree, not the emitter.

```lang
#parser{
    add_expr = mul_expr (('+' | '-') mul_expr)*  @left_assoc
}
```

With `@left_assoc`, the parser produces:

```
binop
├── binop
│   ├── mul(1)
│   ├── OP(+)
│   └── mul(2)
├── OP(-)
└── mul(3)
```

Now the emit pattern is trivial:

```lang
binop[$l, $op, $r] => ast_binop($op.text, $l, $r)
```

**Annotations**:
| Annotation | Meaning |
|------------|---------|
| `@left_assoc` | Build left-associative tree (default for most operators) |
| `@right_assoc` | Build right-associative tree (for `=`, `?:`, `**`) |
| (none) | Flat list (for when you want manual control) |

This keeps emit simple. Associativity is a parsing concern, not a transform concern.

---

## Right-Hand Side

The RHS of `=>` is **lang code** that produces AST (as `*u8` S-expr string):

```lang
func_decl[$name, $params, $body] =>
    ast_func($name.text,              // string extraction
             emit_params($params),     // helper function
             ast_type("i64"),          // literal AST
             $body)                    // implicit recursion
```

### Variable References

| Reference | Meaning |
|-----------|---------|
| `$name.text` | Extract the string content of the node |
| `$name.raw` | Get the raw PNode (no recursion) |
| `$name` | **Implicit recursion**: calls `emit($name)` |
| `$args` (from `$args*`) | Vec of already-emitted children |

### Available Functions

1. **ast_* constructors** (from std/ast.lang):
   ```lang
   ast_number("42")           → (number 42)
   ast_ident("x")             → (ident x)
   ast_binop("+", left, right) → (binop + left right)
   ast_func(name, params, ret, body)
   ast_if(cond, then, else_)
   ast_block(stmts)
   ast_return(expr)
   ```

2. **Combinators**:
   ```lang
   map($params, |p| ast_param(p.text, ast_type("i64")))
   fold_left($args, |acc, x| ast_binop(op, acc, x))
   vec_of(item1, item2, item3)
   ```

---

## Semantics

1. **Pattern matching is top-to-bottom, first match wins**

2. **Implicit recursion by default**: When you reference `$var` in the RHS, `emit($var)` is called automatically. Use `$var.raw` to suppress.

3. **Explicit default required**: The last pattern should be a catch-all or the generated code will error on unmatched nodes.

---

## Standard Helpers (The Escape Hatches)

Most languages need 2-4 helpers for things patterns can't express. These live in `std/emit_helpers.lang`:

### `emit_body(exprs)` - Multi-Expression Bodies

Lisp, Ruby, and expression-oriented languages have function bodies with multiple expressions where the last is the return value.

```lang
// (lambda (x) (print x) (+ x 1))  →  body has 2 exprs, last is returned
func emit_body(exprs *Vec) *u8 {
    if vec_len(exprs) == 1 {
        return vec_get(exprs, 0);
    }
    var stmts *Vec = vec_new(vec_len(exprs));
    var i i64 = 0;
    while i < vec_len(exprs) - 1 {
        vec_push(stmts, ast_expr_stmt(vec_get(exprs, i)));
        i = i + 1;
    }
    vec_push(stmts, ast_return(vec_get(exprs, vec_len(exprs) - 1)));
    return ast_block(stmts);
}
```

**Used by**: Lisp, Scheme, Ruby, Kotlin, Scala

### `desugar_for(init, cond, incr, body)` - For Loop Desugaring

C-style for loops desugar to init + while:

```lang
// for (i = 0; i < 10; i++) body  →  { i = 0; while (i < 10) { body; i++; } }
func desugar_for(init *u8, cond *u8, incr *u8, body *u8) *u8 {
    if cond == nil { cond = ast_bool(true); }
    var loop_body *u8 = ast_block(vec_of(body, ast_expr_stmt(incr)));
    return ast_block(vec_of(init, ast_while(cond, loop_body)));
}
```

**Used by**: C, Java, JavaScript, Go

### `emit_cond(clauses, emit_fn)` - Cond/Case → Nested Ifs

Pattern matching and cond expressions become nested if-else chains:

```lang
// (cond (test1 body1) (test2 body2) (else body3))
func emit_cond(clauses *Vec, get_test fn(*PNode) *u8, get_body fn(*PNode) *u8) *u8 {
    if vec_len(clauses) == 0 { return ast_nil(); }
    var c *PNode = vec_get(clauses, 0);
    return ast_if(get_test(c), get_body(c),
                  emit_cond(vec_tail(clauses), get_test, get_body));
}
```

**Used by**: Lisp, Erlang, Elixir, ML

### `emit_let(bindings, body)` - Let Bindings

Let expressions become blocks with variable declarations:

```lang
// (let ((x 1) (y 2)) body)  →  { var x = 1; var y = 2; body }
func emit_let(bindings *Vec, body *u8) *u8 {
    var stmts *Vec = vec_new(vec_len(bindings) + 1);
    var i i64 = 0;
    while i < vec_len(bindings) {
        vec_push(stmts, vec_get(bindings, i));
        i = i + 1;
    }
    vec_push(stmts, body);
    return ast_block(stmts);
}
```

**Used by**: Lisp, ML, Haskell, Rust

### The Philosophy

These helpers are **not failures of the abstraction**. They're the documented way to handle common patterns that don't fit pure pattern matching:

> `#emit{}` is pattern matching. Helpers are for everything else.
> This is expected. This is normal.

---

## The `@manual` Escape Hatch

For truly unusual cases, drop into raw code:

```lang
#emit{
    // Normal patterns
    if_stmt[$c, $t, $e] => ast_if($c, $t, $e)

    // Complex case needs full code
    weird_construct[$x, $y, $z] => @manual {
        if some_complex_condition($x.raw) {
            return special_handling($x, $y);
        }
        return fallback($z);
    }
}
```

`@manual` blocks contain arbitrary lang code. Use sparingly—if you need many `@manual` blocks, you might be better off writing `emit()` by hand.

---

## Generated Code

`#emit{}` generates an `emit(node *PNode) *u8` function. For example:

```lang
#emit{
    number($n)           => ast_number($n.text)
    symbol($s)           => ast_ident($s.text)
    list["+" , $a, $b]   => ast_binop("+", $a, $b)
    list[$fn, $args*]    => ast_call(ast_ident($fn.text), $args)
}
```

Generates:

```lang
func emit(node *PNode) *u8 {
    // Atom: number
    if node.kind == PNODE_NUMBER {
        var _n *PNode = node;
        return ast_number(_n.text);
    }

    // Atom: symbol
    if node.kind == PNODE_SYMBOL {
        var _s *PNode = node;
        return ast_ident(_s.text);
    }

    // Composite: list
    if node.kind == PNODE_LIST {
        var _len i64 = list_len(node);
        var _first *PNode = list_get(node, 0);

        // list["+", $a, $b]
        if streq(_first.text, "+") && _len == 3 {
            var _a *PNode = list_get(node, 1);
            var _b *PNode = list_get(node, 2);
            return ast_binop("+", emit(_a), emit(_b));
        }

        // list[$fn, $args*] - default
        var _fn *PNode = _first;
        var _args *Vec = vec_new(8);
        var _i i64 = 1;
        while _i < _len {
            vec_push(_args, emit(list_get(node, _i)));
            _i = _i + 1;
        }
        return ast_call(ast_ident(_fn.text), _args);
    }

    return ast_error("unmatched pattern");
}
```

---

## Complete Example: C Subset

A realistic C subset with structs, pointers, for loops, and full expression grammar.

### Source Language

```c
struct Point {
    int x;
    int y;
};

int distance(struct Point* p1, struct Point* p2) {
    int dx = p2->x - p1->x;
    int dy = p2->y - p1->y;
    return dx * dx + dy * dy;
}

int main() {
    struct Point a;
    a.x = 0;
    a.y = 0;

    for (int i = 0; i < 10; i++) {
        a.x = a.x + i;
    }

    return a.x;
}
```

### Grammar

```lang
#parser{
    program    = decl*
    decl       = struct_decl | func_decl | global_var

    struct_decl = 'struct' IDENT '{' field* '}' ';'
    field      = type IDENT ';'

    func_decl  = type IDENT '(' params? ')' (block | ';')
    params     = param (',' param)*
    param      = type IDENT

    type       = base_type '*'*
    base_type  = 'int' | 'char' | 'void' | 'struct' IDENT

    block      = '{' stmt* '}'
    stmt       = local_var | if_stmt | while_stmt | for_stmt
               | return_stmt | break_stmt | continue_stmt | expr_stmt

    local_var  = type IDENT ('=' expr)? ';'
    if_stmt    = 'if' '(' expr ')' stmt ('else' stmt)?
    while_stmt = 'while' '(' expr ')' stmt
    for_stmt   = 'for' '(' for_init ';' expr? ';' expr? ')' stmt
    for_init   = local_var | expr | /*empty*/
    return_stmt = 'return' expr? ';'
    break_stmt = 'break' ';'
    continue_stmt = 'continue' ';'
    expr_stmt  = expr ';'

    expr       = assign
    assign     = ternary (ASSIGN_OP assign)?                  @right_assoc
    ternary    = or_expr ('?' expr ':' ternary)?
    or_expr    = and_expr ('||' and_expr)*                    @left_assoc
    and_expr   = cmp_expr ('&&' cmp_expr)*                    @left_assoc
    cmp_expr   = add_expr (CMP_OP add_expr)?
    add_expr   = mul_expr (('+' | '-') mul_expr)*             @left_assoc
    mul_expr   = unary (('*' | '/' | '%') unary)*             @left_assoc
    unary      = ('!' | '-' | '*' | '&' | '++' | '--') unary | postfix
    postfix    = primary (call | index | field | arrow | '++' | '--')*
    primary    = NUMBER | IDENT | STRING | '(' expr ')'
    call       = '(' args? ')'
    args       = expr (',' expr)*
    index      = '[' expr ']'
    field      = '.' IDENT
    arrow      = '->' IDENT
}
```

### Emit Rules

```lang
#emit{
    // === Types ===
    type_int[]         => ast_type("i64")
    type_char[]        => ast_type("u8")
    type_void[]        => ast_type("void")
    type_ptr[$base]    => ast_type_ptr($base)
    type_struct[$name] => ast_type($name.text)

    // === Program structure ===
    program[$decls*]   => ast_program($decls)

    struct_decl[$name, $fields*] => ast_struct($name.text, $fields)
    field_decl[$type, $name]     => ast_field_decl($name.text, $type)

    func_decl[$ret, $name, $params, $body] =>
        ast_func($name.text, $params, $ret, $body)
    func_decl[$ret, $name, $params] =>   // forward declaration
        ast_func_fwd($name.text, $params, $ret)
    params[$ps*]       => $ps
    param[$type, $name] => ast_param($name.text, $type)

    // === Statements ===
    block[$stmts*]     => ast_block($stmts)
    local_var[$t, $n]  => ast_var($n.text, $t, nil)
    local_var[$t, $n, $v] => ast_var($n.text, $t, $v)

    if_stmt[$c, $t]    => ast_if($c, $t, nil)
    if_stmt[$c, $t, $e] => ast_if($c, $t, $e)
    while_stmt[$c, $b] => ast_while($c, $b)

    // For loop - uses helper (the ONE escape hatch)
    for_stmt[$init, $cond, $incr, $body] =>
        desugar_for($init, $cond, $incr, $body)

    return_stmt[]      => ast_return(nil)
    return_stmt[$e]    => ast_return($e)
    break_stmt[]       => ast_break()
    continue_stmt[]    => ast_continue()
    expr_stmt[$e]      => ast_expr_stmt($e)

    // === Expressions ===
    NUMBER($n)         => ast_number($n.text)
    IDENT($id)         => ast_ident($id.text)
    STRING($s)         => ast_string($s.text)

    // Binary ops - parser builds tree via @left_assoc
    binop[$l, $op, $r] => ast_binop($op.text, $l, $r)
    assign[$l, $op, $r] => ast_assign_op($op.text, $l, $r)
    ternary[$c, $t, $e] => ast_ternary($c, $t, $e)

    // Unary ops
    unop[$op, $e]      => ast_unop($op.text, $e)
    deref[$e]          => ast_deref($e)
    addr[$e]           => ast_addr($e)
    pre_inc[$e]        => ast_pre_inc($e)
    pre_dec[$e]        => ast_pre_dec($e)
    post_inc[$e]       => ast_post_inc($e)
    post_dec[$e]       => ast_post_dec($e)

    // Postfix
    call[$fn, $args*]  => ast_call($fn, $args)
    index[$arr, $i]    => ast_index($arr, $i)
    field[$obj, $f]    => ast_field($obj, $f.text)
    arrow[$obj, $f]    => ast_field(ast_deref($obj), $f.text)
    paren[$e]          => $e
}
```

### Complete Reader

```lang
include "std/core.lang"
include "std/tok.lang"
include "std/parser_reader.lang"
include "std/ast.lang"
include "std/emit_helpers.lang"

#parser{
    program    = decl*
    decl       = struct_decl | func_decl

    struct_decl = 'struct' IDENT '{' field* '}' ';'
    field      = type IDENT ';'

    func_decl  = type IDENT '(' params? ')' (block | ';')
    params     = param (',' param)*
    param      = type IDENT

    type       = base_type '*'*
    base_type  = 'int' | 'char' | 'void' | 'struct' IDENT

    block      = '{' stmt* '}'
    stmt       = local_var | if_stmt | while_stmt | for_stmt
               | return_stmt | break_stmt | continue_stmt | expr_stmt

    local_var  = type IDENT ('=' expr)? ';'
    if_stmt    = 'if' '(' expr ')' stmt ('else' stmt)?
    while_stmt = 'while' '(' expr ')' stmt
    for_stmt   = 'for' '(' for_init ';' expr? ';' expr? ')' stmt
    return_stmt = 'return' expr? ';'
    expr_stmt  = expr ';'

    expr       = assign
    assign     = ternary (ASSIGN_OP assign)?                  @right_assoc
    ternary    = or_expr ('?' expr ':' ternary)?
    or_expr    = and_expr ('||' and_expr)*                    @left_assoc
    and_expr   = cmp_expr ('&&' cmp_expr)*                    @left_assoc
    cmp_expr   = add_expr (CMP_OP add_expr)?
    add_expr   = mul_expr (('+' | '-') mul_expr)*             @left_assoc
    mul_expr   = unary (('*' | '/' | '%') unary)*             @left_assoc
    unary      = ('!' | '-' | '*' | '&' | '++' | '--') unary | postfix
    postfix    = primary (call | index | field | arrow | '++' | '--')*
    primary    = NUMBER | IDENT | STRING | '(' expr ')'
    call       = '(' args? ')'
    args       = expr (',' expr)*
    index      = '[' expr ']'
    field      = '.' IDENT
    arrow      = '->' IDENT
}

#emit{
    // Types
    type_int[]         => ast_type("i64")
    type_char[]        => ast_type("u8")
    type_void[]        => ast_type("void")
    type_ptr[$base]    => ast_type_ptr($base)
    type_struct[$name] => ast_type($name.text)

    // Program
    program[$decls*]   => ast_program($decls)
    struct_decl[$name, $fields*] => ast_struct($name.text, $fields)
    field_decl[$type, $name]     => ast_field_decl($name.text, $type)

    func_decl[$ret, $name, $params, $body] =>
        ast_func($name.text, $params, $ret, $body)
    params[$ps*]       => $ps
    param[$type, $name] => ast_param($name.text, $type)

    // Statements
    block[$stmts*]     => ast_block($stmts)
    local_var[$t, $n]  => ast_var($n.text, $t, nil)
    local_var[$t, $n, $v] => ast_var($n.text, $t, $v)
    if_stmt[$c, $t]    => ast_if($c, $t, nil)
    if_stmt[$c, $t, $e] => ast_if($c, $t, $e)
    while_stmt[$c, $b] => ast_while($c, $b)
    for_stmt[$init, $cond, $incr, $body] => desugar_for($init, $cond, $incr, $body)
    return_stmt[]      => ast_return(nil)
    return_stmt[$e]    => ast_return($e)
    expr_stmt[$e]      => ast_expr_stmt($e)

    // Expressions
    NUMBER($n)         => ast_number($n.text)
    IDENT($id)         => ast_ident($id.text)
    STRING($s)         => ast_string($s.text)
    binop[$l, $op, $r] => ast_binop($op.text, $l, $r)
    assign[$l, $op, $r] => ast_assign_op($op.text, $l, $r)
    ternary[$c, $t, $e] => ast_ternary($c, $t, $e)
    unop[$op, $e]      => ast_unop($op.text, $e)
    deref[$e]          => ast_deref($e)
    addr[$e]           => ast_addr($e)
    call[$fn, $args*]  => ast_call($fn, $args)
    index[$arr, $i]    => ast_index($arr, $i)
    field[$obj, $f]    => ast_field($obj, $f.text)
    arrow[$obj, $f]    => ast_field(ast_deref($obj), $f.text)
    paren[$e]          => $e
}

reader c(text *u8) *u8 {
    var t *Tokenizer = tok_new_c(text);
    var tree *PNode = parse_program(t);
    return emit(tree);
}
```

**~110 lines** for a substantial C subset. Only ONE helper call (`desugar_for`).

---

## Complete Example: Scheme Subset

A realistic Scheme with define, lambda, let, if, cond, and multi-expression bodies.

### Source Language

```scheme
(define (factorial n)
  (if (< n 2)
      1
      (* n (factorial (- n 1)))))

(define (map f xs)
  (if (null? xs)
      '()
      (cons (f (car xs))
            (map f (cdr xs)))))

(define (main)
  (let ((x 10)
        (y 20))
    (print x)
    (print y)
    (+ x y)))
```

### Grammar

```lang
#parser{
    program    = form*
    form       = definition | expr

    definition = '(' 'define' '(' IDENT IDENT* ')' expr+ ')'   // function
               | '(' 'define' IDENT expr ')'                   // variable

    expr       = atom | special | call
    atom       = NUMBER | IDENT | STRING | BOOL

    special    = '(' special_form ')'
    special_form = lambda_form | let_form | if_form | cond_form
                 | begin_form | quote_form

    lambda_form = 'lambda' '(' IDENT* ')' expr+
    let_form   = 'let' '(' binding* ')' expr+
    binding    = '(' IDENT expr ')'
    if_form    = 'if' expr expr expr?
    cond_form  = 'cond' clause+
    clause     = '(' expr expr+ ')'
    begin_form = 'begin' expr+
    quote_form = 'quote' sexpr

    call       = '(' expr expr* ')'
    sexpr      = atom | '(' sexpr* ')'
}
```

### Emit Rules

```lang
#emit{
    // Atoms
    NUMBER($n)   => ast_number($n.text)
    IDENT($s)    => ast_ident($s.text)
    STRING($s)   => ast_string($s.text)
    BOOL($b)     => ast_bool(streq($b.text, "#t"))

    // Program
    program[$forms*] => ast_program($forms)

    // Definitions
    define_func[$name, $params*, $body+] =>
        ast_func($name.text,
                 map($params, |p| ast_param(p.text, ast_type("any"))),
                 ast_type("any"),
                 emit_body($body))

    define_var[$name, $val] =>
        ast_var($name.text, ast_type("any"), $val)

    // Lambda
    lambda_form[$params*, $body+] =>
        ast_lambda(map($params, |p| ast_param(p.text, ast_type("any"))),
                   emit_body($body))

    // Let
    let_form[$bindings*, $body+] =>
        emit_let(map($bindings, |b| emit(b)), emit_body($body))

    binding[$name, $val] =>
        ast_var($name.text, ast_type("any"), $val)

    // Control flow
    if_form[$cond, $then]        => ast_if($cond, $then, ast_nil())
    if_form[$cond, $then, $else] => ast_if($cond, $then, $else)

    cond_form[$clauses+] => emit_cond_scheme($clauses)

    begin_form[$exprs+] => emit_body($exprs)

    // Quote (data, not code)
    quote_form[$e] => quote_to_data($e.raw)

    // Function call
    call[$fn, $args*] => ast_call($fn, $args)
}
```

### Complete Reader

```lang
include "std/core.lang"
include "std/tok.lang"
include "std/parser_reader.lang"
include "std/ast.lang"
include "std/emit_helpers.lang"

#parser{
    program    = form*
    form       = definition | expr

    definition = '(' 'define' '(' IDENT IDENT* ')' expr+ ')'
               | '(' 'define' IDENT expr ')'

    expr       = atom | special | call
    atom       = NUMBER | IDENT | STRING | BOOL

    special    = '(' special_form ')'
    special_form = lambda_form | let_form | if_form | cond_form
                 | begin_form | quote_form

    lambda_form = 'lambda' '(' IDENT* ')' expr+
    let_form   = 'let' '(' binding* ')' expr+
    binding    = '(' IDENT expr ')'
    if_form    = 'if' expr expr expr?
    cond_form  = 'cond' clause+
    clause     = '(' expr expr+ ')'
    begin_form = 'begin' expr+
    quote_form = 'quote' sexpr

    call       = '(' expr expr* ')'
    sexpr      = atom | '(' sexpr* ')'
}

#emit{
    NUMBER($n)   => ast_number($n.text)
    IDENT($s)    => ast_ident($s.text)
    STRING($s)   => ast_string($s.text)
    BOOL($b)     => ast_bool(streq($b.text, "#t"))

    program[$forms*] => ast_program($forms)

    define_func[$name, $params*, $body+] =>
        ast_func($name.text,
                 map($params, |p| ast_param(p.text, ast_type("any"))),
                 ast_type("any"),
                 emit_body($body))
    define_var[$name, $val] =>
        ast_var($name.text, ast_type("any"), $val)

    lambda_form[$params*, $body+] =>
        ast_lambda(map($params, |p| ast_param(p.text, ast_type("any"))),
                   emit_body($body))

    let_form[$bindings*, $body+] =>
        emit_let(map($bindings, |b| emit(b)), emit_body($body))
    binding[$name, $val] =>
        ast_var($name.text, ast_type("any"), $val)

    if_form[$cond, $then]        => ast_if($cond, $then, ast_nil())
    if_form[$cond, $then, $else] => ast_if($cond, $then, $else)
    cond_form[$clauses+]         => emit_cond_scheme($clauses)
    begin_form[$exprs+]          => emit_body($exprs)

    quote_form[$e] => quote_to_data($e.raw)
    call[$fn, $args*] => ast_call($fn, $args)
}

// Scheme-specific cond helper (20 lines)
func emit_cond_scheme(clauses *Vec) *u8 {
    if vec_len(clauses) == 0 { return ast_nil(); }
    var c *PNode = vec_get(clauses, 0);
    var test *PNode = list_get(c, 0);
    var body *Vec = list_rest(c, 1);

    if streq(test.text, "else") {
        return emit_body(map(body, |e| emit(e)));
    }

    return ast_if(emit(test),
                  emit_body(map(body, |e| emit(e))),
                  emit_cond_scheme(vec_tail(clauses)));
}

// Quote → runtime data (15 lines)
func quote_to_data(node *PNode) *u8 {
    if node.kind == PNODE_NUMBER { return ast_number(node.text); }
    if node.kind == PNODE_IDENT  { return ast_symbol(node.text); }
    if node.kind == PNODE_LIST {
        var items *Vec = vec_new(8);
        var i i64 = 0;
        while i < list_len(node) {
            vec_push(items, quote_to_data(list_get(node, i)));
            i = i + 1;
        }
        return ast_list(items);
    }
    return ast_nil();
}

reader scheme(text *u8) *u8 {
    var t *Tokenizer = tok_new_lisp(text);
    var tree *PNode = parse_program(t);
    return emit(tree);
}
```

**~120 lines** for a real Scheme subset (without macros). Uses 2 stdlib helpers plus 2 small language-specific helpers.

---

## Reader Embedding: The Macro System

Traditional macros (`defmacro`) are out of scope. But we have something better: **readers calling readers**.

### The Key Insight

A reader is a function: `*u8 → *u8` (text → AST string).

Readers can call other readers. That's the whole macro system.

```
┌─────────────────────────────────────────────────────────────┐
│  Scheme source with embedded lang                            │
│                                                              │
│  (define (main)                                              │
│    <lang#(var x i64 = 10; return x;)>)                       │
│                                                              │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Scheme reader                                               │
│                                                              │
│  1. Sees <lang#(...)>                                        │
│  2. Extracts text: "var x i64 = 10; return x;"               │
│  3. CALLS lang_reader(text) directly                         │
│  4. Gets back AST string                                     │
│  5. Splices into output                                      │
│                                                              │
│  The reader does the work. Not the kernel.                   │
│                                                              │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Pure AST output                                             │
│                                                              │
│  (program                                                    │
│    (func main () i64                                         │
│      (block                                                  │
│        (var x i64 (number 10))                               │
│        (return (ident x)))))                                 │
│                                                              │
│  No reader references. No macro nodes. Just AST.             │
│                                                              │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Kernel                                                      │
│                                                              │
│  Sees pure AST. Doesn't know readers exist.                  │
│  Type checks. Generates code. Done.                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Critical**: The reader calls the other reader and splices the result. Nothing is "passed to the kernel for later expansion." By the time the kernel sees the AST, all reader embedding is resolved.

### Choosing Your Embedding Syntax

Each language has different punctuation available. Choose syntax that doesn't conflict:

| Language style | Suggested syntax | Example |
|----------------|------------------|---------|
| Lisp-like | `<name#(...)>` | `<lang#(x + 1)>` |
| C-like | `#name{...}` | `#sql{SELECT * FROM users}` |
| ML-like | `[%name ...]` | `[%lang x + 1]` |
| Python-like | `@name(...)` | `@lang(return x)` |

The syntax is up to you. Pick something that parses unambiguously in your grammar.

### Grammar Addition

Add the embedding syntax to your grammar:

```lang
#parser{
    expr = ... | reader_embed

    // Lisp-style: <name#(text)>
    reader_embed = '<' IDENT '#(' raw_text ')>'
}
```

The `raw_text` token captures everything between balanced delimiters. This needs tokenizer support—it's not a normal token, it's "grab everything until matching close paren, respecting nesting."

### Emit Rule

```lang
#emit{
    // All your normal patterns...

    reader_embed[$name, $text] => find_reader($name.text)($text.text)
}
```

### The `find_reader` Function

`find_reader` is a **stdlib function** that returns a reader as a callable:

```lang
// Provided by std/reader.lang
func find_reader(name *u8) fn(*u8) *u8;
```

It:
1. Finds the reader by name (checks cache, std/, project paths)
2. Compiles the reader if needed (using the cached compiler infrastructure)
3. Returns a **function pointer** you can call

**You get back a callable, then you invoke it:**

```lang
// Find the reader
var lang_reader fn(*u8) *u8 = find_reader("lang");

// Call it with your text
var ast *u8 = lang_reader("x + 1");
```

Or inline in emit rules:

```lang
#emit{
    reader_embed[$name, $text] => find_reader($name.text)($text.text)
}

// find_reader("lang")("x + 1")  → AST
// find_reader("sql")("SELECT...") → AST
```

This is the same mechanism that powers `#foo{}` in lang source. Reader discovery, caching, compilation—all handled by the infrastructure. You just get a function and call it.

### Complete Example: Scheme with Embedded Lang

```lang
include "std/core.lang"
include "std/tok.lang"
include "std/parser_reader.lang"
include "std/ast.lang"
include "std/emit_helpers.lang"
include "std/reader.lang"           // For find_reader()

#parser{
    program    = form*
    form       = definition | expr

    definition = '(' 'define' '(' IDENT IDENT* ')' expr+ ')'

    expr       = atom | special | call | reader_embed
    atom       = NUMBER | IDENT | STRING | BOOL

    special    = '(' special_form ')'
    special_form = lambda_form | let_form | if_form | begin_form
    // ... other special forms ...

    call       = '(' expr expr* ')'

    // Reader embedding: <name#(text)>
    reader_embed = '<' IDENT '#(' raw_text ')>'
}

#emit{
    NUMBER($n)   => ast_number($n.text)
    IDENT($s)    => ast_ident($s.text)
    // ... all your normal patterns ...

    // Reader embedding - find reader by name, call it
    reader_embed[$name, $text] => find_reader($name.text)($text.text)
}

reader scheme(text *u8) *u8 {
    var t *Tokenizer = tok_new_lisp(text);
    var tree *PNode = parse_program(t);
    return emit(tree);
}
```

### Usage

```scheme
(define (factorial n)
  (if (< n 2)
      1
      (* n (factorial (- n 1)))))

(define (main)
  ;; Mix Scheme and lang freely
  (let ((x <lang#(factorial(10))>))
    (print x)
    <lang#(
      var result i64 = x * 2;
      if result > 100 {
        print("big number!");
      }
      return result;
    )>))
```

The Scheme reader sees `<lang#(...)>`, calls `lang_reader()`, gets AST, splices it in. The kernel sees pure AST with no trace of readers.

### Why Reader Embedding > defmacro

| defmacro | Reader embedding |
|----------|------------------|
| Same syntax, magic semantics | Different syntax, explicit |
| Hygiene is a PhD thesis | No hygiene needed—clear boundaries |
| Debugging: "why did this expand to that?" | Debugging: "what did the reader return?" |
| Complex implementation (expander, environments) | ~15 lines of code |
| Single language | Cross-language by design |
| Must learn macro system | Just call a function |

### The Philosophy

> **Want custom syntax? Write a reader.**
> **Want to mix syntaxes? Import a reader and call it.**
> **That's the whole macro system.**

Traditional macros transform syntax→syntax within one language. Reader embedding lets you drop into **any syntax** and get back **any AST**. It's more powerful and simpler.

### Advanced: Reader Chains

Readers can embed readers that embed readers:

```
lang source
  └─> #scheme{ ... <sql#(SELECT ...)> ... }
        │              │
        │              └─> sql_reader() → AST for DB query
        │
        └─> scheme_reader() → AST with embedded SQL result
```

Each reader calls the next, returns AST. The chain resolves at compile time. Kernel sees flat AST.

### What About "Real" Lisp Macros?

If someone truly needs `defmacro` with quasiquote and hygiene, they implement it as preprocessing:

```lang
reader scheme_with_macros(text *u8) *u8 {
    var t *Tokenizer = tok_new_lisp(text);
    var tree *PNode = parse_program(t);

    // Their problem: expand (defmacro ...) forms
    var expanded *PNode = expand_lisp_macros(tree);

    return emit(expanded);
}
```

We provide building blocks. They can build a macro expander (~200 lines). But our native answer is reader embedding—it solves 90% of "I want custom syntax" use cases with zero complexity.

---

## Implementation

### Step 1: std/ast.lang (AST Constructors)

```lang
func ast_number(val *u8) *u8 {
    var sb *StringBuilder = sb_new();
    sb_str(sb, "(number ");
    sb_str(sb, val);
    sb_str(sb, ")");
    return sb_finish(sb);
}

func ast_binop(op *u8, left *u8, right *u8) *u8 {
    var sb *StringBuilder = sb_new();
    sb_str(sb, "(binop ");
    sb_str(sb, op);
    sb_str(sb, " ");
    sb_str(sb, left);
    sb_str(sb, " ");
    sb_str(sb, right);
    sb_str(sb, ")");
    return sb_finish(sb);
}

// ... etc for all AST nodes
```

**~200 lines** covering all AST node types.

### Step 2: #emit{} Reader

The `#emit{}` reader parses emit rules and generates the `emit()` function.

**Grammar for #emit{}:**

```lang
#parser{
    emit_block   = '{' rule* '}'
    rule         = pattern '=>' rhs

    pattern      = atom_pattern | composite_pattern
    atom_pattern = IDENT '(' '$' IDENT ')'
    composite_pattern = IDENT '[' elements? ']'

    elements     = element (',' element)*
    element      = STRING                            // "defun" literal
                 | '$' IDENT modifier? typeguard?    // $name, $args*, $x:list
    modifier     = '*' | '+'
    typeguard    = ':' IDENT
}
```

**Code generation:**

1. Parse all rules into `(pattern, rhs)` pairs
2. Generate `func emit(node *PNode) *u8 { ... }`
3. For each pattern:
   - Generate kind check: `if node.kind == KIND_xxx {`
   - For composites, generate length check and child extraction
   - For literals, generate `streq(child.text, "literal")` checks
   - Bind variables to extracted children
   - Generate RHS with `emit()` calls for implicit recursion

**~400 lines**.

### Step 3: Helpers Library

```lang
func fold_binop(op *u8, args *Vec) *u8 {
    var result *u8 = vec_get(args, 0);
    var i i64 = 1;
    while i < vec_len(args) {
        result = ast_binop(op, result, vec_get(args, i));
        i = i + 1;
    }
    return result;
}

func list_children(node *PNode) *Vec {
    // Extract children from a list node
    return node.children;
}
```

**~150 lines**.

---

## The Stack

```
┌────────────────────────────────────────────────────────────┐
│  Source Code         "func add(a, b) { return a + b; }"    │
└──────────────────────────────┬─────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────┐
│  #parser{}           Grammar → Recursive descent parser    │
└──────────────────────────────┬─────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────┐
│  Parse Tree          func_decl[IDENT("add"), ...]          │
└──────────────────────────────┬─────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────┐
│  #emit{}             Pattern matching → AST construction   │
└──────────────────────────────┬─────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────┐
│  AST S-expr          (func add ((param a i64) ...) ...)    │
└──────────────────────────────┬─────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────┐
│  Kernel              Type check → Codegen → x86            │
└────────────────────────────────────────────────────────────┘
```

---

## Summary

**The equation:**
```
#parser{}  →  parse(text)  →  ParseTree
#emit{}    →  emit(tree)   →  AST
kernel     →  compile(AST) →  x86
```

**One pattern syntax:**
```
kind($var)              // atom: match token kind, bind node
kind[$children...]      // composite: match rule kind, bind children
"literal"               // in children: match exact text
$var*                   // bind remaining as Vec
```

**Realistic languages:**
- C subset: ~110 lines, 1 helper
- Scheme subset: ~120 lines, 2 stdlib helpers + 2 language-specific helpers

---

*"The last abstraction is the one you don't have to think about."*
