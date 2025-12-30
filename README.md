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
│                             x86                                 │
└─────────────────────────────────────────────────────────────────┘
```

The compiler has two parts: a kernel (AST to x86) and readers (syntax to AST). The lang reader - the one that parses `func`, `if`, `while` - is just one reader. You can swap it for anything.

## Layer 1: It's a language

```lang
func main() void {
    print("Hello, world!\n");
}
```

```bash
./out/lang hello.lang -o hello.s
as hello.s -o hello.o && ld hello.o -o hello
./hello
Hello, world!
```

Functions, structs, pointers. See [LANG.md](./LANG.md).

## Layer 2: It outputs compilers

The kernel composes itself with any reader to produce a standalone compiler:

```bash
./out/kernel -c lisp_reader.ast -o lisp_compiler.s
# Native Lisp-to-x86 compiler
```

Define a reader for SQL, or a DSL, or Brainfuck. The kernel doesn't care what the surface syntax looks like.

## Layer 3: It compiles itself

The lang reader is written in lang. The kernel is written in lang. The whole compiler is written in the language it compiles.

```bash
# Compose kernel with lang reader (from AST)
./out/kernel -c lang_reader.ast --kernel-ast kernel.ast -o lang_composed.s

# Use that compiler to compile its own reader from source
./out/lang_composed -c lang_reader.lang --kernel-ast kernel.ast -o lang_bootstrap.s

# Identical output
diff lang_composed.s lang_bootstrap.s
```

The composed compiler parses `lang_reader.lang` using its built-in lang reader, then composes a new compiler from that. Same output. Fixed point.

Lang source becomes AST becomes x86 becomes a compiler that reads lang source. The whole thing rests on `mmap`, `read`, `write`, and `exit`. Four syscalls. No libc.

## The semantic model

Lang separates syntax from semantics. Any reader can define any surface syntax - Lisp, Python-like, your own DSL. But the AST compiles to C-like semantics: manual memory, standard call stacks, direct machine code.

The kernel is ~5000 lines because it doesn't try to be a runtime. No GC, no scheduler, no bytecode interpreter. Just AST to machine code.

This works for systems languages, config DSLs, data transforms, anything with manual memory or arenas or refcounting. One-shot effects (exceptions, generators, async) work too - they compile to state machines.

Languages needing garbage collection or green threads need runtime support the kernel doesn't provide. The LLVM backend (in progress) will let you link against libgc for conservative collection, or use `gc.statepoint` for precise GC. But the kernel itself stays simple.

Any syntax, C-like semantics. If your language fits that model, lang compiles it.

## How it got here

1. Write a lang compiler in Go. No metaprogramming, just get something working.
2. Rewrite the compiler in lang. Compile it with the Go version. Delete Go.
3. Add reader macros. Now lang can extend itself.
4. Add `--emit-ast`. Readers output S-expression AST instead of lang code.
5. Split the compiler: kernel (AST → x86) and lang reader (lang → AST). Both written in lang.
6. Compile each half to AST using the existing compiler.
7. Bootstrap: kernel composes itself with the lang reader AST. Fixed point.

The journey is in [devlog/](./devlog/). The full bootstrap chain lives in [bootstrap/](./bootstrap/) and [archive/](./archive/).

## Building

```bash
make bootstrap    # First time: assemble from preserved .s
make build        # Compile from source
make verify       # Check fixed point + run tests
make promote      # Update stable compiler
```

## Docs

- [LANG.md](./LANG.md) - Language reference
- [TODO.md](./TODO.md) - Roadmap
- [designs/ast_as_language.md](./designs/ast_as_language.md) - Architecture

## License

[MIT](./LICENSE)
