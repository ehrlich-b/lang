# AST Builder API

## The Problem

minilisp.lang is ugly:

```lang
sb_str(sb, "(binop ");
sb_str(sb, op);
sb_str(sb, " ");
emit(sb, left);
sb_str(sb, " ");
emit(sb, right);
sb_str(sb, ")");
```

This is write-only code. The string manipulation obscures intent. You can't see the tree for the quotes.

## The Vision

```lang
return ast_binop(op, emit(left), emit(right));
```

Think in trees. Output is still S-expr text, but you never see it.

## API Design

### Core Principle

Every function returns `*u8` (the S-expr text). Functions compose by nesting:

```lang
ast_binop("+", ast_number("1"), ast_number("2"))
// Returns: "(binop + (number 1) (number 2))"
```

### Expressions

```lang
// Literals
func ast_number(val *u8) *u8;           // (number 42)
func ast_string(val *u8) *u8;           // (string "hello")
func ast_bool(val bool) *u8;            // (bool true)
func ast_nil() *u8;                     // (nil)
func ast_ident(name *u8) *u8;           // (ident foo)

// Operations
func ast_binop(op *u8, left *u8, right *u8) *u8;  // (binop + left right)
func ast_unop(op *u8, expr *u8) *u8;              // (unop ! expr)

// Calls
func ast_call(fn *u8, args *u8) *u8;    // (call fn args...) - args is vec
func ast_call1(fn *u8, a *u8) *u8;      // convenience
func ast_call2(fn *u8, a *u8, b *u8) *u8;

// Access
func ast_field(expr *u8, name *u8) *u8; // (field expr name)
func ast_index(expr *u8, idx *u8) *u8;  // (index expr idx)
```

### Statements

```lang
func ast_return(expr *u8) *u8;          // (return expr)
func ast_return_void() *u8;             // (return)
func ast_expr_stmt(expr *u8) *u8;       // (expr_stmt expr)
func ast_assign(target *u8, val *u8) *u8; // (assign target val)
func ast_if(cond *u8, then *u8, els *u8) *u8;  // (if cond then else)
func ast_while(cond *u8, body *u8) *u8; // (while cond body)
func ast_block(stmts *u8) *u8;          // (block stmt...) - stmts is vec
```

### Declarations

```lang
func ast_var(name *u8, typ *u8, init *u8) *u8;  // (var name type init)
func ast_func(name *u8, params *u8, ret *u8, body *u8) *u8;
func ast_program(decls *u8) *u8;        // (program decl...) - decls is vec
```

### Types

```lang
func ast_type(name *u8) *u8;            // (type_base i64)
func ast_type_ptr(elem *u8) *u8;        // (type_ptr elem)
```

### Params (for functions)

```lang
func ast_param(name *u8, typ *u8) *u8;  // (param name type)
```

### Vec helpers (for variadic args)

```lang
func ast_vec() *u8;                     // new vec for collecting
func ast_vec_push(v *u8, item *u8) void;
```

## minilisp with AST Builder

Before (ugly):
```lang
func emit(sb *StringBuilder, node *PNode) void {
    if node.kind == 1 {
        sb_str(sb, "(number ");
        sb_str(sb, node.text);
        sb_str(sb, ")");
        return;
    }
    // ... 100 more lines of string munging
}
```

After (beautiful):
```lang
func emit(node *PNode) *u8 {
    if node.kind == 1 {
        return ast_number(node.text);
    }
    if node.kind == 2 {
        return ast_ident(node.text);
    }
    // ... operators
    if is_sym(first, "and") {
        return ast_binop("&&", emit(list_get(node, 1)), emit(list_get(node, 2)));
    }
    // ... function call
    var args *u8 = ast_vec();
    var i i64 = 1;
    while i < count {
        ast_vec_push(args, emit(list_get(node, i)));
        i = i + 1;
    }
    return ast_call(ast_ident(first.text), args);
}
```

The structure is visible. The intent is clear. "Huh, neat."

## Implementation

Simple string builders internally:

```lang
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
```

The ugliness is hidden once, in the library. Users never see it.

## File Location

`std/ast.lang` - the AST builder API for reader authors.

## Usage

```lang
include "std/ast.lang"

reader myreader(text *u8) *u8 {
    // parse...
    return ast_binop("+", ast_number("1"), ast_number("2"));
}
```

## Why This Matters

1. **Readers become readable** - The tree structure is visible in the code
2. **Errors caught early** - Typo in `(binpo` vs type error on `ast_binop`
3. **Composable** - Functions return strings, nest naturally
4. **Discoverable** - API documents what AST nodes exist
5. **Beautiful** - "Huh, neat"
