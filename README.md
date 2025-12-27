# language

A self-hosted compiler compiler (not a typo).

Write a reader macro that parses some syntax. It outputs lang source. That gets compiled to x86. You now have a native compiler for whatever syntax you defined.

```lang
// Define a reader that handles lisp syntax
reader lisp(text *u8) *u8 { /* parse s-exprs, emit lang */ }

// Use it inline - this compiles to native code
var answer i64 = #lisp{(* (+ 3 3) (+ 3 4))};  // 42
```

The compiler compiles itself. Reader macros are compiled to native executables and invoked during compilation. There's no interpreter, no VM, no runtime.

The endgame (not yet implemented):

```bash
# Build-time: file extension selects the reader
# .lisp files get wrapped in #lisp{ ... } automatically
lang reader_lisp.lang program.lisp -o program

# Or generate a standalone compiler
lang -c lisp reader_lisp.lang -o lisp_compiler
./lisp_compiler program.lisp -o program
```

The file extension *is* the reader name. A `.lisp` file gets wrapped in `#lisp{ contents }`. A `.bf` file would use `#bf{ contents }`. Mix `.lang` files with any other extension - one of them needs a main.

## Status

Self-hosted and at fixed point. AST macros work. Reader macros V2 work (full lang power, native compilation). Currently polishing rough edges.

## Building

```bash
# Bootstrap from preserved assembly (first time)
make bootstrap

# Build compiler from source
make build

# Verify fixed point and promote
make verify && make promote

# Compile and run a program
make run FILE=test/hello.lang

# With stdlib
make stdlib-run FILE=test/vec_test.lang
```

## Docs

- [LANG.md](./LANG.md) - Language reference
- [TODO.md](./TODO.md) - Roadmap
- [designs/reader_v2_design.md](./designs/reader_v2_design.md) - Reader macros V2 design
- [designs/macro_design.md](./designs/macro_design.md) - AST macro design
- [devlog/](./devlog/) - Development journal

## Editor Support

VSCode extension in `editor/vscode/`:
```bash
ln -s $(pwd)/editor/vscode ~/.vscode/extensions/language-lang
```

## License

Do whatever you want with it.
