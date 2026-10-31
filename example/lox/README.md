# Lox expressions

From the repository root, initialize the compiler if needed and build a
standalone Lox compiler with its target runtime:

```sh
make init
make generate-os-layer LANGBE=llvm LANGLIBC=libc
LANGBE=llvm ./out/lang compiler lox example/lox/lox.lang --runtime example/lox/runtime.lang -o /tmp/loxc
/tmp/loxc example/lox/test/expressions.lox -o /tmp/program.ll
lli /tmp/program.ll
```

The reader accepts expression and `print` statements, `//` comments, numbers,
strings, booleans and `nil`, parentheses, unary `-` and `!`, arithmetic,
comparisons and equality. It uses Lox precedence and truthiness; `+` joins two
strings. Variables, control flow, functions and classes are not yet supported.

The runtime uses indexed `f64` slots because storing an `f64` through a pointer
or struct field is not supported by this compiler. The reader copies pointers
out of struct fields before accessing bytes, and the runtime flips the stored double's sign bit because direct floating-point unary negation emits invalid LLVM.
The runtime uses libc `strtod` and `printf` for numeric conversion and output.
The compiler only emits a variadic ABI for `printf`, so numeric output uses it
and flushes immediately to preserve ordering with the standard library writes.
Run `bash example/lox/test/run.sh` for the fixtures.

Variables can be declared with `var`, assigned, and shadowed in nested blocks.
The generated program owns the scope stack and resolves values at runtime.

To score against the pinned Crafting Interpreters checkout, build its `clox`
executable and run `make lox-score LOX_SUITE=/path/to/craftinginterpreters`.
The scorer verifies clox first and then reports the supported suite count.
