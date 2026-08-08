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

**Cross-platform**: Linux x86-64 and macOS ARM64 via LLVM. 198 checks pass on both.

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

That makes lang a **compiler compiler**: you write one reader function—source
text in, shared AST out—and lang turns it into a native compiler. The `-c` flag
composes the kernel with that reader:

```bash
LANGBE=llvm ./out/lang -c tiny example/tiny/tiny.lang -o tinyc.ll
clang -O2 tinyc.ll -o tinyc
```

Now `tinyc` is a native compiler for `.tiny` files:

```bash
./tinyc example/tiny/answer.tiny -o answer.ll
```

Same AST means same calling convention. Functions call each other directly at the machine level, no wrappers or runtime glue.

Start with the copyable [reader guide](./docs/READERS.md), then grow into the
shipped examples below.

## Five languages, one binary

A reader parses its own surface syntax and emits lang AST. The kernel compiles whatever any reader emits, so several readers can share one program — and because they all lower to the same AST, they share one calling convention. They call each other directly at the machine level. No FFI, no interpreter, no glue.

[`example/polyglot.lang`](./example/polyglot.lang) puts five real languages in one native binary:

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

#minipy{                                    // layout: no block delimiters at all
def report(n):
    lst = collect_primes(n)                 # flow's coroutine -> C -> forth
    total = lisp_to_int(ml_sum(lst))        # minilisp, folding a cons list
    print("primes <=", n, "sum", total, "digitsum", digit_sum(total))
    return total                            #                       ^ forth
}
```

flow's `primes` coroutine streams primes — asking C about each candidate and suspending between hits; C's trial-division loop asks Forth about each divisor; flow's driver conses each prime onto a Lisp list; Lisp folds the list; minipy loops over the whole pipeline and formats the answer. Five paradigms — stack, imperative, coroutine-effectful, functional, scripting — each doing its idiomatic job, meeting at the i64 ABI.

No two of the five agree on so much as where a block ends: parens, braces, `;`, `then`, and — in minipy — nothing but the column the line starts in.

- **C** ([example/c/](./example/c/)) captures a large subset: all control flow, every operator, structs, pointers, arrays, enums, switch, ternary.
- **minilisp** ([example/minilisp/](./example/minilisp/)) is a real (small) Lisp: first-class closures, `let`, `quote`, cons lists. Every value is an i64 that's secretly a pointer, so it marshals across the language boundary.
- **flow** ([example/flow/](./example/flow/)) is a generator/coroutine language built on algebraic effects. `yield` is bidirectional — a generator's output can depend on what the driver sends back.
- **forth** ([example/forth/](./example/forth/)) has no expression grammar at all — just a flat stream of words over a data stack. The stack is the reader's, not the program's: it holds AST nodes at read time and is gone before codegen, so `: square ( n -- n2 ) dup * ;` compiles to a single `mul`.
- **minipy** ([example/minipy/](./example/minipy/)) is layout-delimited: block structure lives in the whitespace every other reader discards. It needed no change to the shared tokenizer — a token carries its byte offset, so the reader recovers the columns and synthesizes INDENT/DEDENT itself. Layout is reader-local.

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

Or use the compiler directly: `./out/lang run hello.lang`.

Reader and tooling authors can inspect the exact lexer stream without parsing
or compiling:

```bash
./out/lang --dump-tokens hello.lang
```

Two compilers live in `out/`: **`out/lang`** is the stable compiler, promoted by
the last successful `make bootstrap` - use this one. **`out/lang_next`** is
whatever `make build` just compiled from source; it only matters when you are
testing compiler changes you have not bootstrapped yet.

### Compiling programs

```bash
./out/lang hello.lang -o hello.ll
clang -O2 hello.ll -o hello
```

No environment variables needed: the compiler defaults `LANGBE`/`LANGOS` to the
platform it was built for. Set them only to cross-target (`LANGOS=macos`,
`LANGOS=wasm`; `LANGBE=x86` for the frozen assembly backend on Linux).

The LLVM backend is the primary target - handles closures, algebraic effects, reader macros, and all future features (floats, calling conventions, etc.).

### WebAssembly

```bash
LANGOS=wasm LANGBE=llvm ./out/lang hello.lang -o hello.ll
clang --target=wasm32-unknown-unknown -nostdlib -Wl,--no-entry -Wl,--export-all \
      -Wl,--allow-undefined -Wl,-z,stack-size=8388608 hello.ll -o hello.wasm
node test/wasm_host.js hello.wasm
```

`test/wasm_host.js` is a small node host providing the libc surface
(write/alloc/exit). 165 of the suite's tests pass on wasm
(`./test/run_wasm_suite.sh`); the exception is algebraic effects, which need
stack switching that core wasm cannot express - the compiler rejects them
cleanly for this target.

### Bootstrap

The compiler bootstraps from preserved LLVM IR:

```
bootstrap/current/compiler_linux.ll
bootstrap/current/compiler_macos.ll
```

The legacy x86 assembly backend is frozen. It served the self-hosting proof and
remains a historical recovery path, but LLVM is the future for Language Forge.

## Docs

- [LANG.md](./LANG.md) - Language reference
- [TODO.md](./TODO.md) - Roadmap
- [docs/](./docs/) - Technical documentation
  - [READERS.md](./docs/READERS.md) - Write a syntax reader and mint a compiler
  - [BUILDING.md](./docs/BUILDING.md) - Build instructions and compilation pipeline
  - [BOOTSTRAP.md](./docs/BOOTSTRAP.md) - Bootstrap process and trust chain
  - [AST.md](./docs/AST.md) - AST node reference (41 node types)
- [designs/ast_as_language.md](./designs/ast_as_language.md) - Architecture vision

## License

[MIT](./LICENSE)
