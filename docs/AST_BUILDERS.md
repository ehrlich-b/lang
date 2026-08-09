# AST builder quick reference

A reader returns Lang's shared AST as text. `std/ast.lang` builds that text for
you, so reader code can compose nodes instead of assembling S-expressions.
Every builder below returns `*u8`.

## The shape of a reader

```lang
include "std/ast.lang"

reader demo(text *u8) *u8 {
    var value *u8 = ast_add(ast_number("20"), ast_number("22"));
    var body *u8 = ast_block1(ast_return(value));
    return ast_program1(ast_func("main", ast_vec(), ast_type_i64(), body));
}
```

Whole-file readers return `ast_program(...)`. Expression readers return one
expression node. Builders compose from the inside out.

## Lists and types

```lang
ast_vec()                         // empty node list
ast_push(nodes, node)             // append in place

ast_type("Name")
ast_type_i64()                    ast_type_bool()
ast_type_u8()                     ast_type_void()
ast_type_str()                    ast_type_ptr(elem)
ast_type_array(size, elem)        ast_type_func(param_types, ret)
ast_param(name, type)
```

## Expressions

```lang
ast_number(text)                  ast_int(value)
ast_string(value)                 ast_bool(value)
ast_nil()                         ast_ident(name)

ast_add(left, right)              ast_sub(left, right)
ast_mul(left, right)              ast_div(left, right)
ast_mod(left, right)              ast_eq(left, right)
ast_ne(left, right)               ast_lt(left, right)
ast_gt(left, right)               ast_le(left, right)
ast_ge(left, right)               ast_and(left, right)
ast_or(left, right)               ast_not(expr)
ast_neg(expr)                     ast_addr(expr)
ast_deref(expr)

ast_call_named(name, args)        ast_call0(name)
ast_call1(name, a)                ast_call2(name, a, b)
ast_call3(name, a, b, c)          ast_call4(name, a, b, c, d)
ast_field(expr, name)             ast_index(expr, index)
ast_lambda(params, ret, body)
```

## Statements and blocks

```lang
ast_return(expr)                  ast_return_void()
ast_expr_stmt(expr)               ast_assign(target, value)
ast_var(name, type, init)

ast_if(cond, then_block, else_block)
ast_if_then(cond, then_block)
ast_while(cond, body)             ast_break(label)
ast_continue(label)

ast_block(statements)             ast_block1(statement)
ast_block_expr(statements, tail)
```

## Declarations and programs

```lang
ast_func(name, params, ret, body)
ast_field_decl(name, type)        ast_struct(name, fields)
ast_variant_decl(name, type)      ast_enum(name, variants)
ast_effect(name, param_types, ret)
ast_include(path)

ast_program(declarations)         ast_program1(declaration)
```

For algebraic effects and pattern matching, see the `ast_perform`, `ast_handle`,
`ast_resume`, `ast_pattern_*`, and `ast_match*` helpers in
[`std/ast.lang`](../std/ast.lang). The executable examples in
[`test/suite/235_ast_literals.lang`](../test/suite/235_ast_literals.lang) through
[`test/suite/238_ast_statements.lang`](../test/suite/238_ast_statements.lang)
show the builders in context.
