# language

*"There are many like it but this one is mine."*

**Racket-style power with Zig-style minimalism. For fun.**

A self-hosted language forge: full-power reader macros, parsing toolkit, bare-metal output.

## The Gist

```lang
// C-like syntax, bare-metal output
struct Point {
    x i64;
    y i64;
}

func main() i64 {
    var p Point;
    p.x = 42;
    p.y = 100;
    return p.x + p.y;  // 142
}

// AST macros for compile-time code generation
macro double(x) {
    return ${ $x + $x };
}

var n i64 = double(21);  // expands to (21 + 21) = 42

// Reader macros for custom syntax (WIP: full-power V2)
reader lisp(text *u8) *u8 { /* parse s-exprs, emit lang */ }

var answer i64 = #lisp{(* (+ 3 3) (+ 3 4))};  // 42
```

## What Is This?

A language that can extend its own syntax and compiles to native code with no runtime.

**Inspired by:**
- [Racket](https://racket-lang.org/) - Language-oriented programming, reader macros, `#lang`
- [Zig](https://ziglang.org/) - No runtime, comptime, simplicity

**The goal:** Racket's metaprogramming power without the runtime. Zig's bare-metal philosophy with real syntax extensibility.

## Status

- **Self-hosted**: Compiler compiles itself, reaches fixed point
- **AST macros**: Working (`macro`, `${ }`, `$name`, `$@name`)
- **Reader macros V1**: Syntax works, toy interpreter (V2 in progress with full lang power)

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
