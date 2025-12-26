# 0006: Macros Working

*December 2024*

## What Happened

Implemented Phase 2: the macro system. It works.

### The Pieces

1. **Lexer**: Added `$`, `${`, `$@` tokens and `macro` keyword
2. **Parser**: Quote expressions `${ expr }`, unquote `$name`, macro definitions
3. **Codegen**: Macro registry (like struct registry)
4. **Interpreter**: Compile-time AST interpreter for macro execution
5. **Quote expansion**: Substitute unquotes with bound AST values
6. **Macro expansion**: When calling a macro, invoke interpreter instead of generating call

### How It Works

```lang
macro double(x) {
    return ${ $x + $x };
}

func main() i64 {
    return double(42);  // expands to 42 + 42 = 84
}
```

At compile time:
1. Parser sees `double(42)`, looks up macro
2. Binds `x` to the AST node for `42`
3. Runs the macro body, evaluates `${ $x + $x }`
4. Quote expansion substitutes `$x` with the `42` AST
5. Returns AST for `42 + 42`
6. Codegen generates code for `42 + 42`

### What's Cool

- Nested macros work: `double(double(25))` = 100
- Macros are real compile-time code, not text substitution
- Quote/unquote is the minimal useful metaprogramming primitive
- The interpreter is ~200 lines of code

## What's Not Done Yet

- `$@name` for string-to-identifier splicing
- `--expand-macros` debug flag
- Proper error messages for macro failures
- More complex macros (debug, assert, unless)

## How It Feels

This was satisfying. The design was right - quote/unquote plus a simple interpreter gets you a lot. The implementation had a few gotchas (variable name conflicts, quote expansion) but nothing major.

Next: polish, documentation, cool examples.
