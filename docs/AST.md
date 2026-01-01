# AST Reference

This document specifies the Abstract Syntax Tree (AST) format used by lang. The AST is the true language - all syntaxes (lang, lisp, or custom readers) compile to this format.

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│  any syntax → [reader] → AST S-expressions → [kernel] → x86 │
│                              ↑                               │
│                    THIS IS THE LANGUAGE                      │
└─────────────────────────────────────────────────────────────┘
```

The AST uses S-expression syntax for interchange. Readers produce it; the kernel consumes it.

## Node Types

There are **41 node types** organized into categories:

| Range | Category | Examples |
|-------|----------|----------|
| 1-3 | Declarations | func, var, struct |
| 4-8 | Statements | block, if, while, return, expr-stmt |
| 9-19 | Expressions | binop, call, field, ident, number |
| 20-26 | Macros/Readers | quote, unquote, reader, include |
| 27-32 | Control + Lambda | break, continue, let, assign, lambda |
| 33-36 | Sum Types | enum, match, pattern-variant, pattern-wildcard |
| 37-41 | Effects | effect, perform, handle, resume, block-expr |

---

## S-Expression Format

### Program Structure

```lisp
(program
  <declaration>*
)
```

A program is a list of declarations (functions, variables, structs, etc.).

**Optional version header:**
```lisp
(program
  (ast-version 2)
  <declaration>*
)
```

### AST Versioning

The `(ast-version N)` declaration controls how the AST is interpreted:

| Version | String Format | Description |
|---------|---------------|-------------|
| 1 (default) | `"hello"` (with quotes) | Strings include surrounding quotes |
| 2 | `hello` (raw) | Strings are raw content, reader adds quotes |

**Version detection:** If a program starts with `(ast-version N)`, the sexpr_reader sets the version before processing. This affects how string literals are parsed and stored.

### Naming Convention

Node names use underscores in S-expressions:
- `block_expr` not `block-expr`
- `type_base` not `type-base`
- `pattern_wildcard` not `pattern-wildcard`

---

## Declarations

### Function Declaration

```lisp
(func <name> (<param>*) <return-type> <body>)
```

| Field | Type | Description |
|-------|------|-------------|
| name | symbol | Function name |
| params | list | Parameter list |
| return-type | type | Return type |
| body | statement | Function body |

**Param format:**
```lisp
(param <name> <type>)
```

**Example:**
```lisp
(func factorial
  ((param n (type_base i64)))
  (type_base i64)
  (block
    (if (binop <= (ident n) (number 1))
      (block (return (number 1))))
    (return (binop * (ident n)
                     (call (ident factorial)
                           (binop - (ident n) (number 1)))))))
```

### Variable Declaration

```lisp
(var <name> <type> <init>?)
```

| Field | Type | Description |
|-------|------|-------------|
| name | symbol | Variable name |
| type | type | Variable type |
| init | expression | Optional initializer |

**Example:**
```lisp
(var counter (type_base i64) (number 0))
```

### Struct Declaration

```lisp
(struct <name> (<field-decl>*))
```

**Field-decl format:**
```lisp
(field_decl <name> <type>)
```

**Example:**
```lisp
(struct Point
  ((field_decl x (type_base i64))
   (field_decl y (type_base i64))))
```

### Enum Declaration (Sum Types)

```lisp
(enum <name> (<variant-decl>*))
```

**Variant-decl format:**
```lisp
(variant_decl <name> <payload-type>?)
```

**Example:**
```lisp
(enum Option
  ((variant_decl None)
   (variant_decl Some (type_base i64))))
```

### Effect Declaration

```lisp
(effect <name> (<param-type>*) <resume-type>)
```

| Field | Type | Description |
|-------|------|-------------|
| name | symbol | Effect name |
| param-types | list | Parameter types for the effect |
| resume-type | type | Type returned when resumed |

**Example:**
```lisp
(effect Ask ((type_base i64)) (type_base i64))
```

### Include Declaration

```lisp
(include "<path>")
```

Includes another source file. The path is resolved relative to the current file.

**Example:**
```lisp
(include "std/core.lang")
```

### Macro Declaration

```lisp
(macro <name> (<param-names>*) <body>)
```

Defines a compile-time macro. Parameters are just names (no types) since macros operate on AST nodes.

| Field | Type | Description |
|-------|------|-------------|
| name | symbol | Macro name |
| params | list | Parameter names (symbols) |
| body | expression | Macro body with quote/unquote |

**Memory layout:** `[kind:8][name_ptr:8][name_len:8][params:8][param_count:8][body:8]` = 48 bytes

**Example:**
```lisp
(macro debug (expr)
  (quote
    (block
      (expr_stmt (call (ident print) (string "DEBUG: ")))
      (expr_stmt (unquote expr)))))
```

### Reader Declaration

```lisp
(reader <name> <param-name> <body>)
```

Defines a reader macro - a function that transforms source text to AST at compile time.

| Field | Type | Description |
|-------|------|-------------|
| name | symbol | Reader name (used as `#name{...}`) |
| param-name | symbol | Name of the text parameter |
| body | statement | Reader body (must return AST) |

**Memory layout:** `[kind:8][name_ptr:8][name_len:8][param_name_ptr:8][param_name_len:8][body:8]` = 48 bytes

**Example:**
```lisp
(reader lisp text
  (block
    (return (call (ident parse_lisp) (ident text)))))
```

---

## Statements

### Block Statement

```lisp
(block <statement>*)
```

**Example:**
```lisp
(block
  (expr_stmt (call (ident print) (string "hello")))
  (return (number 0)))
```

### If Statement

```lisp
(if <condition> <then> <else>?)
```

| Field | Type | Description |
|-------|------|-------------|
| condition | expression | Condition to test |
| then | statement | Then branch |
| else | statement | Optional else branch |

**Example:**
```lisp
(if (binop < (ident x) (number 0))
  (block (return (number -1)))
  (block (return (number 1))))
```

### While Statement

```lisp
(while <condition> <body> <label>?)
```

| Field | Type | Description |
|-------|------|-------------|
| condition | expression | Loop condition |
| body | statement | Loop body |
| label | symbol | Optional label for break/continue |

**Example:**
```lisp
(while (binop < (ident i) (number 10))
  (block
    (expr_stmt (call (ident print) (ident i)))
    (assign (ident i) (binop + (ident i) (number 1)))))
```

### Return Statement

```lisp
(return <value>?)
```

**Examples:**
```lisp
(return)              ; void return
(return (number 42))  ; return value
```

### Break/Continue Statements

```lisp
(break <label>?)
(continue <label>?)
```

**Example with label:**
```lisp
(while (bool true) outer_loop
  (block
    (while (bool true)
      (block
        (break outer_loop)))))  ; breaks outer loop
```

### Expression Statement

```lisp
(expr_stmt <expression>)
```

Wraps an expression to use in statement context:
```lisp
(expr_stmt (call (ident print) (string "hello")))
```

### Assign Statement

```lisp
(assign <target> <value>)
```

**Valid targets (lvalues):**
- `(ident x)` - variable
- `(field expr name)` - struct field
- `(index expr i)` - array element
- `(unop * expr)` - dereferenced pointer

**Example:**
```lisp
(assign (field (ident point) x) (number 10))
```

---

## Expressions

### Literals

```lisp
(number <value>)      ; integer literal
(string "<value>")    ; string literal (escaped)
(bool true)           ; boolean true
(bool false)          ; boolean false
(nil)                 ; null pointer
```

**String escapes handled:**
- `\n` → newline
- `\t` → tab
- `\r` → carriage return
- `\\` → backslash
- `\"` → quote
- `\0` → null byte

### Identifier

```lisp
(ident <name>)
```

References a variable or function:
```lisp
(ident counter)
```

### Binary Operations

```lisp
(binop <op> <left> <right>)
```

**Operators:**

| Arithmetic | Comparison | Bitwise | Logical |
|------------|------------|---------|---------|
| `+` | `==` | `&` | `&&` |
| `-` | `!=` | `\|` | `\|\|` |
| `*` | `<` | `^` | |
| `/` | `>` | `<<` | |
| `%` | `<=` | `>>` | |
| | `>=` | | |

**Note:** `&&` and `||` are short-circuit operators.

**Example:**
```lisp
(binop + (ident a) (binop * (ident b) (number 2)))
```

### Unary Operations

```lisp
(unop <op> <expr>)
```

| Op | Description |
|----|-------------|
| `-` | Negation |
| `!` | Logical not |
| `*` | Dereference |
| `&` | Address-of |

**Example:**
```lisp
(unop * (ident ptr))      ; dereference
(unop & (ident counter))  ; address-of
```

### Call Expression

```lisp
(call <function> <arg>*)
```

| Field | Type | Description |
|-------|------|-------------|
| function | expression | Function to call |
| args | expressions | Arguments |

**Direct call:**
```lisp
(call (ident print) (string "hello"))
```

**Indirect call (function pointer):**
```lisp
(call (ident callback) (number 42))
```

### Field Access

```lisp
(field <expr> <name>)
```

**Example:**
```lisp
(field (ident point) x)  ; point.x
```

### Index Access

```lisp
(index <expr> <index>)
```

**Example:**
```lisp
(index (ident array) (number 5))  ; array[5]
```

### Let Expression

```lisp
(let <name> <type>? <init> <body>)
```

Lexically scoped binding:
```lisp
(let x (type_base i64) (number 10)
  (binop + (ident x) (number 1)))  ; evaluates to 11
```

### Lambda Expression

```lisp
(lambda (<param>*) <return-type> <body>)
```

**Example:**
```lisp
(lambda ((param x (type_base i64)))
        (type_base i64)
        (block (return (binop * (ident x) (number 2)))))
```

### Block Expression

```lisp
(block_expr <statement>* <tail-expression>)
```

A block that produces a value (the tail expression):
```lisp
(block_expr
  (var temp (type_base i64) (binop + (ident a) (ident b)))
  (binop * (ident temp) (number 2)))
```

---

## Macro Expressions

These nodes are used inside macro definitions to construct and splice AST.

### Quote Expression

```lisp
(quote <expr>)
```

Quotes an expression, preventing evaluation. Returns the AST node itself.

**Lang syntax:** `${ expr }`

**Example:**
```lisp
(quote (binop + (ident a) (ident b)))
; Returns the AST node for "a + b", not the result of a + b
```

### Unquote Expression

```lisp
(unquote <name>)
```

Splices an AST value into a quoted expression. The named variable must contain an AST node.

**Lang syntax:** `$name`

**Example:**
```lisp
(quote (binop + (unquote x) (number 1)))
; If x holds (ident a), produces (binop + (ident a) (number 1))
```

### Unquote String Expression

```lisp
(unquote_string <name>)
```

Splices a string value as a string literal node. The named variable must contain a string.

**Lang syntax:** `$@name`

**Example:**
```lisp
(quote (call (ident print) (unquote_string msg)))
; If msg is "hello", produces (call (ident print) (string "hello"))
```

### Reader Expression

```lisp
(reader_expr <name> "<content>")
```

Invokes a reader macro at compile time. The content is passed to the named reader, which returns AST.

**Lang syntax:** `#name{content}`

| Field | Type | Description |
|-------|------|-------------|
| name | symbol | Reader name |
| content | string | Raw text to pass to reader |

**Example:**
```lisp
(reader_expr lisp "(+ 1 2)")
; Calls the lisp reader with "(+ 1 2)"
; Returns whatever AST the lisp reader produces
```

---

## Sum Types

### Match Expression

```lisp
(match <scrutinee> (<case>*))
```

**Case format:**
```lisp
(case <pattern> <body>)
```

**Example:**
```lisp
(match (ident opt)
  ((case (pattern_variant Option Some x)
         (ident x))
   (case (pattern_wildcard)
         (number 0))))
```

### Patterns

```lisp
(pattern_variant <enum> <variant> <binding>?)  ; Some(x)
(pattern_wildcard)                              ; _
```

---

## Algebraic Effects

### Perform Expression

```lisp
(perform <effect-name> <arg>*)
```

Raises an effect:
```lisp
(perform Ask (number 42))
```

### Handle Expression

```lisp
(handle <body>
  (return_handler <binding> <body>)
  (effect_handler <name> <binding> <k> <body>)*)
```

| Field | Type | Description |
|-------|------|-------------|
| body | expression | Code that may perform effects |
| return_handler | handler | Handles normal completion |
| effect_handler | handler | Handles specific effect |

**Example:**
```lisp
(handle
  (call (ident do_ask) (number 1))
  (return_handler v (ident v))
  (effect_handler Ask n k
    (resume (ident k) (binop + (ident counter) (ident n)))))
```

### Resume Expression

```lisp
(resume <k> <value>?)
```

Resumes a captured continuation with a value:
```lisp
(resume (ident k) (number 42))
```

---

## Types

### Base Types

```lisp
(type_base <name>)
```

| Type | Size | Description |
|------|------|-------------|
| `i64` | 8 bytes | Signed 64-bit integer |
| `u8` | 1 byte | Unsigned byte |
| `bool` | 8 bytes | Boolean (0 or 1) |
| `void` | 0 bytes | No value |

### Pointer Type

```lisp
(type_ptr <element-type>)
```

**Example:**
```lisp
(type_ptr (type_base u8))    ; *u8
(type_ptr (type_ptr (type_base i64)))  ; **i64
```

### Function Type

```lisp
(type_func (<param-type>*) <return-type>)
```

**Example:**
```lisp
(type_func ((type_base i64) (type_base i64)) (type_base i64))
; fn(i64, i64) -> i64
```

### Closure Type

```lisp
(type_closure (<param-type>*) <return-type>)
```

Same as function type but can capture variables:
```lisp
(type_closure ((type_base i64)) (type_base i64))
; closure(i64) -> i64
```

---

## Memory Layout

All nodes start with a `kind` field (8 bytes). Layouts are:

| Node | Layout | Size |
|------|--------|------|
| FuncDecl | kind:8, name_ptr:8, name_len:8, params:8, param_count:8, ret_type:8, body:8, is_extern:8 | 64 |
| VarDecl | kind:8, name_ptr:8, name_len:8, type:8, init:8, is_extern:8 | 48 |
| StructDecl | kind:8, name_ptr:8, name_len:8, fields:8, field_count:8 | 40 |
| EnumDecl | kind:8, name_ptr:8, name_len:8, variants:8, variant_count:8 | 40 |
| EffectDecl | kind:8, name_ptr:8, name_len:8, param_types:8, param_type_count:8, ret_type:8 | 48 |
| MacroDecl | kind:8, name_ptr:8, name_len:8, params:8, param_count:8, body:8 | 48 |
| ReaderDecl | kind:8, name_ptr:8, name_len:8, param_name_ptr:8, param_name_len:8, body:8 | 48 |
| IncludeDecl | kind:8, path_ptr:8, path_len:8 | 24 |
| BlockStmt | kind:8, stmts:8, stmt_count:8 | 24 |
| IfStmt | kind:8, cond:8, then:8, else:8 | 32 |
| WhileStmt | kind:8, cond:8, body:8, label_ptr:8, label_len:8 | 40 |
| ReturnStmt | kind:8, value:8 | 16 |
| BreakStmt | kind:8, label_ptr:8, label_len:8 | 24 |
| ContinueStmt | kind:8, label_ptr:8, label_len:8 | 24 |
| ExprStmt | kind:8, expr:8 | 16 |
| AssignStmt | kind:8, target:8, value:8 | 24 |
| BinaryExpr | kind:8, op:8, left:8, right:8 | 32 |
| UnaryExpr | kind:8, op:8, expr:8 | 24 |
| CallExpr | kind:8, func:8, args:8, arg_count:8 | 32 |
| IndexExpr | kind:8, expr:8, index:8 | 24 |
| FieldExpr | kind:8, expr:8, field_ptr:8, field_len:8 | 32 |
| IdentExpr | kind:8, name_ptr:8, name_len:8 | 24 |
| NumberExpr | kind:8, value_ptr:8, value_len:8 | 24 |
| StringExpr | kind:8, value_ptr:8, value_len:8 | 24 |
| BoolExpr | kind:8, value:8 | 16 |
| NilExpr | kind:8 | 8 |
| GroupExpr | kind:8, expr:8 | 16 |
| QuoteExpr | kind:8, expr:8 | 16 |
| UnquoteExpr | kind:8, name_ptr:8, name_len:8 | 24 |
| UnquoteStringExpr | kind:8, name_ptr:8, name_len:8 | 24 |
| ReaderExpr | kind:8, name_ptr:8, name_len:8, content_ptr:8, content_len:8 | 40 |
| LetExpr | kind:8, name_ptr:8, name_len:8, type:8, init:8, body:8 | 48 |
| LambdaExpr | kind:8, params:8, param_count:8, ret_type:8, body:8 | 40 |
| BlockExpr | kind:8, stmts:8, stmt_count:8, tail:8 | 32 |
| MatchExpr | kind:8, scrutinee:8, arms:8, arm_count:8 | 32 |
| PatternVariant | kind:8, enum_name_ptr:8, enum_name_len:8, name_ptr:8, name_len:8, binding_ptr:8, binding_len:8 | 56 |
| PatternWildcard | kind:8 | 8 |
| PerformExpr | kind:8, name_ptr:8, name_len:8, args:8, arg_count:8 | 40 |
| HandleExpr | kind:8, body:8, ret_bind:8, ret_bind_len:8, ret_body:8, cases:8, case_count:8 | 56 |
| ResumeExpr | kind:8, k:8, value:8 | 24 |

---

## Node Kind Constants

```lang
NODE_FUNC_DECL         = 1
NODE_VAR_DECL          = 2
NODE_STRUCT_DECL       = 3
NODE_BLOCK_STMT        = 4
NODE_IF_STMT           = 5
NODE_WHILE_STMT        = 6
NODE_RETURN_STMT       = 7
NODE_EXPR_STMT         = 8
NODE_BINARY_EXPR       = 9
NODE_UNARY_EXPR        = 10
NODE_CALL_EXPR         = 11
NODE_INDEX_EXPR        = 12
NODE_FIELD_EXPR        = 13
NODE_IDENT_EXPR        = 14
NODE_NUMBER_EXPR       = 15
NODE_STRING_EXPR       = 16
NODE_BOOL_EXPR         = 17
NODE_NIL_EXPR          = 18
NODE_GROUP_EXPR        = 19
NODE_QUOTE_EXPR        = 20
NODE_UNQUOTE_EXPR      = 21
NODE_MACRO_DECL        = 22
NODE_UNQUOTE_STRING_EXPR = 23
NODE_IMPORT            = 24
NODE_READER_DECL       = 25
NODE_READER_EXPR       = 26
NODE_INCLUDE_DECL      = 27
NODE_BREAK_STMT        = 28
NODE_CONTINUE_STMT     = 29
NODE_LET_EXPR          = 30
NODE_ASSIGN_STMT       = 31
NODE_LAMBDA_EXPR       = 32
NODE_ENUM_DECL         = 33
NODE_MATCH_EXPR        = 34
NODE_PATTERN_VARIANT   = 35
NODE_PATTERN_WILDCARD  = 36
NODE_EFFECT_DECL       = 37
NODE_PERFORM_EXPR      = 38
NODE_HANDLE_EXPR       = 39
NODE_RESUME_EXPR       = 40
NODE_BLOCK_EXPR        = 41
```

## Type Kind Constants

```lang
TYPE_BASE    = 1
TYPE_PTR     = 2
TYPE_ARRAY   = 3
TYPE_FUNC    = 4
TYPE_CLOSURE = 5
```

---

## Complete Example

Here's a complete program showing multiple features:

**Lang syntax:**
```lang
include "std/core.lang"

effect Ask(i64) i64

func do_ask(x i64) i64 {
    return perform Ask(x);
}

func main() i64 {
    var counter i64 = 42;
    var result i64 = handle { do_ask(1); } with {
        return(v) => v,
        Ask(n, k) => {
            resume k(counter + n);
        }
    };
    return result - 43;  // returns 0
}
```

**AST S-expression:**
```lisp
(program
  (include "std/core.lang")
  (effect Ask ((type_base i64)) (type_base i64))
  (func do_ask ((param x (type_base i64))) (type_base i64)
    (block (return (perform Ask (ident x)))))
  (func main () (type_base i64)
    (block
      (var counter (type_base i64) (number 42))
      (var result (type_base i64)
        (handle
          (call (ident do_ask) (number 1))
          (return_handler v (ident v))
          (effect_handler Ask n k
            (block (resume (ident k) (binop + (ident counter) (ident n)))))))
      (return (binop - (ident result) (number 43))))))
```
