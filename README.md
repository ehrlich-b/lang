# lang

A self-hosted compiler where syntax is a plugin.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   .lang file    │     │   .lisp file    │     │   .whatever     │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │ lang reader           │ lisp reader           │ your reader
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                              AST                                │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 │ kernel
                                 ▼
┌───────────────────────────┬─────────────────────────────────────┐
│     x86-64 (Linux)        │     LLVM IR (Linux, macOS, ...)     │
└───────────────────────────┴─────────────────────────────────────┘
                                 │
                                 ▼
                            native exe
```

The compiler has two parts: a kernel (AST to native code) and readers (syntax to AST). The lang reader - the one that parses `func`, `if`, `while` - is just one reader. You can swap it for anything.

**Cross-platform**: Linux x86-64 (direct assembly, no libc) and macOS ARM64 (via LLVM). 167 tests pass on both.

## It's a language

```lang
func factorial(n i64) i64 {
    if n < 2 { return 1; }
    return n * factorial(n - 1);
}

func main() void {
    print_int(factorial(10));
}
```

Functions, structs, pointers, algebraic effects. See [LANG.md](./LANG.md).

## It outputs compilers

The `-c` flag composes the kernel with a reader to produce a standalone compiler:

```bash
./out/lang -c lisp_reader.lang -o lang_lisp
```

Now `lang_lisp` is a native compiler that understands both `.lang` and `.lisp` files:

```bash
./lang_lisp main.lang mathlib.lisp -o program
```

Same AST means same calling convention. Functions call each other directly at the machine level, no wrappers or runtime glue.

## Mix syntaxes, compile to native

Define a function in Lisp:

```lang
include "example/lisp/lisp.lang"

#lisp{ (defun factorial (n) (if (< n 2) 1 (* n (factorial (- n 1))))) }

func main() i64 {
    return factorial(10);  // 3628800
}
```

Both syntaxes compile to the same AST, then to machine code. No interpreter. The Lisp `factorial` is a normal function - call it from lang, pass it as a pointer, whatever.

This works for any reader. The kernel doesn't care what the surface syntax looks like. See [example/minilisp/](./example/minilisp/) - the Lisp reader is about 230 lines.

Readers are also emitted as regular functions, so you can call them at runtime for JIT compilation or REPLs.

## It compiles itself

The lang reader is written in lang. The kernel is written in lang. The compiler compiles itself from source, producing identical output. Fixed point.

```bash
make bootstrap    # Verify fixed point, run tests, promote stable compiler
```

## Building

```bash
make build        # Compile from source → out/lang_next
make run FILE=... # Compile and run a program
```

### LLVM backend

```bash
LANGBE=llvm ./out/lang hello.lang -o hello.ll
clang -O2 hello.ll -o hello
```

The LLVM backend handles everything the x86 backend does: closures, algebraic effects, reader macros. On macOS, set `LANGOS=macos`.

### Dual-backend bootstrap

The compiler bootstraps from preserved assembly or LLVM IR:

```
bootstrap/current/
├── x86/compiler.s       # x86-64 assembly (Linux)
└── llvm/compiler.ll     # LLVM IR (cross-platform)
```

On Linux, `make bootstrap` uses x86 assembly. On macOS, `make llvm-verify` uses the LLVM bootstrap. Both produce compilers that pass 167 tests and rebuild themselves.

## Docs

- [LANG.md](./LANG.md) - Language reference
- [TODO.md](./TODO.md) - Roadmap
- [docs/](./docs/) - Technical documentation
  - [BUILDING.md](./docs/BUILDING.md) - Build instructions and compilation pipeline
  - [BOOTSTRAP.md](./docs/BOOTSTRAP.md) - Bootstrap process and trust chain
  - [AST.md](./docs/AST.md) - AST node reference (41 node types)
- [designs/ast_as_language.md](./designs/ast_as_language.md) - Architecture vision

## License

[MIT](./LICENSE)
