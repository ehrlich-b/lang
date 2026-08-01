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
┌─────────────────────────────────────────────────────────────────┐
│                    LLVM IR (Linux, macOS, ...)                  │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                            native exe
```

The compiler has two parts: a kernel (AST to native code) and readers (syntax to AST). The lang reader - the one that parses `func`, `if`, `while` - is just one reader. You can swap it for anything.

**Cross-platform**: Linux x86-64 and macOS ARM64 via LLVM. 177 tests pass on both.

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

## Four languages, one binary

A reader parses its own surface syntax and emits lang AST. The kernel compiles whatever any reader emits, so several readers can share one program — and because they all lower to the same AST, they share one calling convention. They call each other directly at the machine level. No FFI, no interpreter, no glue.

[`example/polyglot.lang`](./example/polyglot.lang) puts four real languages in one native binary:

```lang
#forth{ : divides? ( d x -- f ) swap mod 0 = ; }             // postfix, no grammar

#c{ int c_is_prime(int x) {                                  // imperative C,
        ... if (divides_p(d, x)) { return 0; } ...           //   calling Forth
} }

#minilisp{ (defun ml_sum (xs)                                // a real Lisp:
    (if (eq xs nil) 0 (+ (car xs) (ml_sum (cdr xs))))) }     // closures, quote, lists

#flow{                                                       // a coroutine DSL:
    gen primes(n) { ... if c_is_prime(x) { yield x; } ... }  //   suspend / resume
    func collect_primes(n) {
        var lst = lisp_nil();
        for p in primes(n) { lst = lisp_cons(lisp_int(p), lst); }
        return lst;
    }
}
```

flow's `primes` coroutine streams primes — asking C about each candidate and suspending between hits; C's trial-division loop asks Forth about each divisor; flow's driver conses each prime onto a Lisp list; Lisp folds the list. Four paradigms — stack, imperative, coroutine-effectful, functional — each doing its idiomatic job, meeting at the i64 ABI.

- **C** ([example/c/](./example/c/)) captures a large subset: all control flow, every operator, structs, pointers, arrays, enums, switch, ternary.
- **minilisp** ([example/minilisp/](./example/minilisp/)) is a real (small) Lisp: first-class closures, `let`, `quote`, cons lists. Every value is an i64 that's secretly a pointer, so it marshals across the language boundary.
- **flow** ([example/flow/](./example/flow/)) is a generator/coroutine language built on algebraic effects. `yield` is bidirectional — a generator's output can depend on what the driver sends back.
- **forth** ([example/forth/](./example/forth/)) has no expression grammar at all — just a flat stream of words over a data stack. The stack is the reader's, not the program's: it holds AST nodes at read time and is gone before codegen, so `: square ( n -- n2 ) dup * ;` compiles to a single `mul`.

None of this extended the kernel; readers are syntax plugins, not compiler patches. The honest claim isn't "capture any language" — it's *compose any syntax at the ABI level in one native binary*.

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

### Building

```bash
LANGBE=llvm ./out/lang hello.lang -o hello.ll
clang -O2 hello.ll -o hello
```

The LLVM backend is the primary target - handles closures, algebraic effects, reader macros, and all future features (floats, calling conventions, etc.). On macOS, set `LANGOS=macos`.

### Bootstrap

The compiler bootstraps from preserved LLVM IR:

```
bootstrap/current/llvm/compiler.ll   # LLVM IR (cross-platform)
```

A legacy x86 assembly bootstrap exists (`bootstrap/current/x86/compiler.s`) but is frozen - no new features will be added. The x86 backend served its purpose (self-hosting proof, educational value) but LLVM is the future for Language Forge.

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
