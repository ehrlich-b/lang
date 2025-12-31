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
│          x86-64           │              LLVM IR                │
└───────────────────────────┴─────────────────────────────────────┘
```

The compiler has two parts: a kernel (AST to native code) and readers (syntax to AST). The lang reader - the one that parses `func`, `if`, `while` - is just one reader. You can swap it for anything.

**Dual backends**: The kernel emits either x86-64 assembly (Linux, no libc) or LLVM IR (cross-platform via clang).

## Layer 1: It's a language

```lang
func main() void {
    print("Hello, world!\n");
}
```

```bash
# x86-64 (direct assembly)
./out/lang hello.lang -o hello.s
as hello.s -o hello.o && ld hello.o -o hello

# LLVM (via clang)
LANGBE=llvm ./out/lang hello.lang -o hello.ll
clang hello.ll -o hello
```

Functions, structs, pointers, algebraic effects. See [LANG.md](./LANG.md).

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

Lang source becomes AST becomes native code becomes a compiler that reads lang source. The whole thing rests on `mmap`, `read`, `write`, and `exit`. Four syscalls. No libc.

## The semantic model

Lang separates syntax from semantics. Any reader can define any surface syntax - Lisp, Python-like, your own DSL. But the AST compiles to C-like semantics: manual memory, standard call stacks, direct machine code.

The kernel is ~5000 lines because it doesn't try to be a runtime. No GC, no scheduler, no bytecode interpreter. Just AST to machine code.

This works for systems languages, config DSLs, data transforms, anything with manual memory or arenas or refcounting. Algebraic effects (exceptions, generators, async) compile to continuation-passing style with stack switching.

Languages needing garbage collection or green threads need runtime support the kernel doesn't provide. The LLVM backend enables linking against libgc for conservative collection, or using `gc.statepoint` for precise GC. But the kernel itself stays simple.

Any syntax, C-like semantics. If your language fits that model, lang compiles it.

## Building

```bash
make bootstrap    # First time: assemble from preserved .s
make build        # Compile from source
make verify       # Check fixed point + run tests
make promote      # Update stable compiler
```

### LLVM backend

```bash
LANGBE=llvm ./out/lang_next src.lang -o out.ll  # Generate LLVM IR
clang -O2 out.ll -o binary                       # Compile with clang
```

The LLVM backend passes all 165 tests and enables cross-platform compilation and optimization.

## Dual-Backend Bootstrap

The compiler can bootstrap from either backend:

```
bootstrap/current/
├── x86/compiler.s    # x86-64 assembly (1.5M)
└── llvm/compiler.ll  # LLVM IR (1.9M)
```

Both are semantically equivalent. The x86 version runs directly on Linux. The LLVM version works anywhere clang does.

## Docs

- [LANG.md](./LANG.md) - Language reference
- [TODO.md](./TODO.md) - Roadmap
- [designs/ast_as_language.md](./designs/ast_as_language.md) - Architecture

## License

[MIT](./LICENSE)
