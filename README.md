# language

*"There are many like it but this one is mine."*

A self-bootstrapping programming language. C-like feel with modern ergonomics. Written for fun and a blog post.

## Status

**Phase 1 complete!** The compiler is self-hosting - it compiles itself and reaches a fixed point.

## The Gist

```
func main() i64 {
    var x i32 = 42;
    var p *i32 = &x;

    if *p > 0 {
        syscall(1, 1, "positive\n", 9);
    }

    return 0;
}

struct Point {
    x i32;
    y i32;
}

func add(a Point, b Point) Point {
    return Point{x: a.x + b.x, y: a.y + b.y};
}
```

## Goals

1. **Self-bootstrapping** - Compiler written in `language`, compiles itself
2. **x86-64 native** - Emits assembly, no VM
3. **Extreme metaprogramming** - AST macros, syntax extensions (eventually)
4. **Simple** - You can read the whole compiler

## Non-Goals

- Production-ready
- Fast compilation
- Complete tooling
- Windows support

## Building

```bash
# Bootstrap from preserved assembly (first time or clean slate)
make bootstrap

# Build the compiler from source
make build

# Verify fixed point and promote
make verify
make promote

# Compile and run a program
make run FILE=test/hello.lang

# Or manually:
./out/lang test/hello.lang -o out/hello.s
as out/hello.s -o out/hello.o
ld out/hello.o -o out/hello
./out/hello
```

## Editor Support

VSCode extension in `editor/vscode/`. To install:
```bash
ln -s $(pwd)/editor/vscode ~/.vscode/extensions/language-lang
```

## Docs

- [LANG.md](./LANG.md) - Language reference (what works now)
- [INITIAL_DESIGN.md](./INITIAL_DESIGN.md) - Original syntax design, grammar
- [designs/](./designs/) - Implementation design docs
- [devlog/](./devlog/) - Development journal

## License

Do whatever you want with it. It's a toy.
