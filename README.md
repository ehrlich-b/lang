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
