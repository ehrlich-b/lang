# Devlog 0010: Lisp Gets Real - defun and Cross-File Interop

**Date**: 2024-12-26

## The Challenge

Can we implement `defun` in our Lisp reader? This would let us define functions in Lisp syntax that compile to native x86 and are callable from regular .lang files.

## What We Built

Extended `example/lisp/lisp.lang` to support:
- `defun` - define functions
- `if` - conditionals (with proper short-circuit for recursion)
- Comparisons: `<`, `>`, `<=`, `>=`, `=`, `!=`
- Boolean operators: `and`, `or`, `not`
- Arithmetic: `+`, `-`, `*`, `/`, `%`
- Function calls

## The Killer Demo

**mathlib.lang** - A math library written in Lisp:
```lang
include "example/lisp/lisp.lang"

#lisp{ (defun abs (x) (if (< x 0) (- 0 x) x)) }
#lisp{ (defun factorial (n) (if (< n 2) 1 (* n (factorial (- n 1))))) }
#lisp{ (defun fib (n) (if (< n 2) n (+ (fib (- n 1)) (fib (- n 2))))) }
#lisp{ (defun gcd (a b) (if (= b 0) a (gcd b (% a b)))) }
```

**test_mathlib.lang** - Using Lisp functions from regular lang:
```lang
include "example/lisp/mathlib.lang"

func main() i64 {
    print_int(factorial(6));  // 720
    print_int(fib(10));       // 55
    print_int(gcd(48, 18));   // 6
    return 0;
}
```

This is compile-time macro interop. The Lisp code compiles to lang source, which compiles to x86. No interpreter, no runtime.

## Technical Hurdles

### 1. Recursive Functions and Short-Circuit Evaluation

Naive approach: `(if cond then else)` -> `cond*then + !cond*else`

Problem: This evaluates BOTH branches! Factorial blows the stack.

Solution: For `defun` bodies that start with `if`, generate proper if-statements:
```lang
func factorial(n i64) i64 {
    if (n < 2) {
        return 1;
    }
    return (n * factorial((n - 1)));
}
```

### 2. Operator Token Types

The `#parser{}` reader needed to recognize `<`, `>`, `%`, `=` as operators.

Fixed in `std/rdgen.lang`:
```lang
// operator matches +, -, *, /, %, <, >, =
sb_str(rd.sb, "TOK_PLUS || ... || TOK_LT || TOK_GT || TOK_PERCENT || TOK_EQ");
```

### 3. Mixed Symbol/Operator Handling

After adding operators to the token type, `=` became kind 5 (operator) instead of kind 2 (symbol). The comparison check needed updating:
```lang
if (first.kind == 2 || first.kind == 5) && is_comparison(first.text) {
```

## What's Still Ugly

The lisp.lang implementation exposes too much lang internals:

1. **Magic numbers**: `node.kind == 2` instead of `PNODE_SYMBOL`
2. **Parser structure knowledge**: Need to know `list = ['(', sexp*, ')']` means index 1
3. **No switch/match**: Verbose if/return chains

These are lang problems to fix, not lisp problems.

## Stats

- lisp.lang: ~390 lines (includes parser grammar, emitter, everything)
- mathlib.lang: 33 lines
- All 81 tests pass
- Recursive factorial, fib, gcd all work

## What This Proves

The compiler-compiler vision works. You can:
1. Define a grammar with `#parser{}`
2. Write a transpiler to lang source
3. Use `reader` to expose it as a syntax
4. Functions defined in that syntax are first-class lang functions

Next: Back to code review. We keep tripping over lang problems.
