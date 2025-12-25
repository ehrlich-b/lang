# 0002: Hello World

**Date**: 2024-12-25

## What happened

Phase 0 compiler is complete. Hello world compiles and runs:

```
func main() i64 {
    syscall(1, 1, "Hello, world!\n", 14);
    return 0;
}
```

Also tested factorial with loops, conditionals, and function calls. It works.

## Implementation

The compiler is ~600 lines of Go:
- `token.go` - Token types (~90 lines)
- `lexer.go` - Tokenizer (~200 lines)
- `ast.go` - AST node types (~160 lines)
- `parser.go` - Recursive descent parser (~300 lines)
- `codegen.go` - x86-64 code generation (~320 lines)
- `main.go` - CLI glue (~100 lines)

Key decisions:
- Stack-based expression evaluation (push/pop dance)
- Placeholder `STACKSIZE` patched via string replacement after function body
- syscall is a magic builtin, not a real function

## What works

- Functions with parameters
- Variables with initializers
- if/else, while loops
- Arithmetic (+, -, *, /, %)
- Comparisons (==, !=, <, >, <=, >=)
- Logical operators (&&, ||, !)
- Pointers (&x, *p)
- syscall builtin
- String literals

## What's missing

- Structs (not needed for Phase 1)
- Arrays (not needed for Phase 1)
- Type checking (we trust the programmer)
- Any error recovery

## Mood

Elated. Seeing "Hello, world!" print from code I compiled feels magical every time. The factorial test passing means we have real control flow working.

## Next

Either start the Phase 1 self-hosting compiler or write the stdlib first. Stdlib might be smarter - it'll shake out codegen bugs before we have to debug a compiler written in an unproven language.
