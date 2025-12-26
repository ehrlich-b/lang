# Phase 2: Macro System

## The Goal

Let users capture code as data, inspect it, transform it, and generate new code at compile time.

---

## Core Concepts

### Quote: Capture Code as Data

Normally, `1 + 2` evaluates to `3`. But sometimes you want to capture the *structure* of `1 + 2` without running it.

```lang
var tree *Ast = ${ 1 + 2 };
```

`tree` now points to an AST node:

```
BinaryOp(ADD)
├── left: Int(1)
└── right: Int(2)
```

The `${ }` syntax means: "don't evaluate this—give me the AST."

### Unquote: Plug In Existing AST

Inside a quote, `$name` splices in an AST you already have:

```lang
var one *Ast = ${ 1 };
var two *Ast = ${ 2 };

var sum *Ast = ${ $one + $two };  // AST for "1 + 2"
```

Without the `$`, you'd get the AST for the literal variable names "one" and "two". With `$`, you plug in what those variables contain.

### Macros: Compile-Time Functions

A macro receives AST nodes and returns a new AST node. It runs at compile time.

```lang
macro double(expr) {
    return ${ $expr + $expr };
}

// When you write:
var x i64 = double(5);

// The compiler expands it to:
var x i64 = 5 + 5;
```

The macro saw `5` as an AST node, duplicated it, and built `5 + 5`.

---

## Syntax

### Quote

```lang
${ expression }
```

Returns `*Ast` pointing to the AST for `expression`.

### Unquote

```lang
${ ... $name ... }
```

Inside a quote, `$name` evaluates `name` (which must be `*Ast`) and splices it in.

### Unquote String (for identifiers/strings)

```lang
${ ... $@name ... }
```

`$@` splices a string as an identifier or string literal. (Tentative syntax.)

### Macro Definition

```lang
macro name(param1, param2, ...) {
    // body must return *Ast
    return ${ ... };
}
```

Parameters are `*Ast` nodes, not runtime values.

---

## AST Introspection

Functions to inspect AST nodes at compile time:

```lang
func ast_kind(node *Ast) i64;           // What kind? (binop, call, int, etc.)
func ast_int_value(node *Ast) i64;      // Get integer value
func ast_string_value(node *Ast) *u8;   // Get string value
func ast_left(node *Ast) *Ast;          // Left child of binop
func ast_right(node *Ast) *Ast;         // Right child of binop
func ast_op(node *Ast) i64;             // Operator of binop
func ast_to_string(node *Ast) *u8;      // Pretty-print AST as code
// ... more as needed
```

These let you examine the structure of captured code.

---

## Examples

### Debug Macro

Print an expression and its value:

```lang
macro debug(expr) {
    var name *u8 = ast_to_string(expr);
    return ${
        print($@name);
        print(" = ");
        print_int($expr);
        print("\n");
    };
}

// Usage:
var x i64 = 10;
var y i64 = 32;
debug(x + y);

// Output: x + y = 42
```

### Assert Macro

```lang
macro assert(cond) {
    var msg *u8 = ast_to_string(cond);
    return ${
        if !$cond {
            print("Assertion failed: ");
            print($@msg);
            print("\n");
            exit(1);
        }
    };
}

// Usage:
assert(x > 0);

// If x <= 0, prints: Assertion failed: x > 0
```

### Unless Macro

```lang
macro unless(cond, body) {
    return ${
        if !$cond {
            $body
        }
    };
}

// Usage:
unless(x == 0, ${
    print("x is not zero\n");
});
```

### Swap Macro

```lang
macro swap(a, b) {
    return ${
        var temp i64 = $a;
        $a = $b;
        $b = temp;
    };
}

// Usage:
swap(x, y);
```

---

## Implementation Plan

### Step 1: AST as Data

- Add `Ast` struct to the language (or expose existing internal AST)
- Implement `ast_kind()`, `ast_left()`, etc. as intrinsic functions
- These work at compile time only

### Step 2: Quote Syntax

- Lexer: recognize `${` as QUOTE_START, `}` closes it
- Lexer: inside quote, `$name` is UNQUOTE
- Parser: parse quote blocks, build AST that represents "an AST literal"
- Result: `${ 1 + 2 }` produces an AST node of kind "Quote" containing the AST for `1 + 2`

### Step 3: Macro Definitions

- Parser: recognize `macro name(...) { }`
- Store macro definitions separately from functions
- Macros are not compiled to assembly—they run in the compiler

### Step 4: Macro Expansion

- During parsing (or a separate pass), when we see a macro call:
  1. Parse the arguments as AST (don't evaluate)
  2. Call the macro function with those AST nodes
  3. Get the returned AST
  4. Splice it into the parse tree
- Continue compilation with expanded code

### Step 5: Compile-Time Evaluation

For macros to run, we need to execute code at compile time. Options:

**Option A: Interpreter**
- Add a simple AST interpreter to the compiler
- Macros run interpreted
- Simpler, good enough for now

**Option B: Compile-and-call**
- Compile macro code to native
- Call it via dlopen or similar
- Faster, more complex

**Start with Option A.** Performance isn't critical for macro execution.

---

## What We're NOT Doing (Yet)

- **Hygiene**: Variables in macros can capture/be captured. User beware.
- **Type-aware macros**: Macros see syntax only, not types.
- **Reader macros**: Can't change lexer/parser from user code (maybe Phase 3).
- **Syntax modules**: Can't swap entire syntaxes (maybe Phase 3).

---

## Reserved Syntax

| Syntax | Meaning |
|--------|---------|
| `${ }` | Quote (capture AST) |
| `$name` | Unquote (splice AST) |
| `$@name` | Unquote string as identifier |
| `` ` `` | Reserved for multi-line strings (future) |

---

## Open Questions

1. **Statement macros**: How to handle macros that expand to multiple statements?
2. **Macro scope**: Can macros call other macros? (Probably yes)
3. **Error messages**: How to report errors in macro-generated code?
4. **Debugging**: Can we see the expanded code? (`--expand-macros` flag?)

---

## Summary

| Feature | Syntax | What It Does |
|---------|--------|--------------|
| Quote | `${ expr }` | Capture code as AST |
| Unquote | `$x` | Splice AST into quote |
| Macro | `macro name(args) { }` | Compile-time code transformer |
| Introspection | `ast_kind(node)` | Examine AST structure |

This gives us Lisp-style metaprogramming with familiar C-like syntax.
