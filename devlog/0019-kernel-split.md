# 0019: Kernel/Reader Split

**Date**: 2024-12-29

## The Architecture

Split the compiler into two pieces:

```
kernel = AST → x86
reader = syntax → AST
```

The kernel doesn't know lang syntax. It reads S-expression AST and emits x86. The lang reader is just one possible frontend.

### New Files

| File | Purpose |
|------|---------|
| src/kernel_main.lang | Entry point for standalone kernel |
| src/lang_reader.lang | Lang syntax as a reader (lexer + parser + ast_emit) |
| src/compiler.lang | Composition glue: reader_transform + generate |
| src/reader_main.lang | Entry point for standalone reader tools |

### Kernel Sources

The kernel needs codegen, sexpr_reader, and enough of parser.lang to have AST node accessors. But not the lang-syntax parser itself.

```make
KERNEL_CORE := std/core.lang src/limits.lang src/lexer.lang \
               src/parser.lang src/codegen.lang src/sexpr_reader.lang
```

### Lang Reader Sources

Everything needed to turn `.lang` files into AST:

```make
LANG_READER_SOURCES := std/core.lang src/limits.lang src/lexer.lang \
                       src/parser.lang src/ast_emit.lang src/lang_reader.lang
```

## Composition

The kernel can compose itself with any reader:

```bash
./out/kernel -c lang_reader.ast \
    --kernel-ast kernel.ast \
    --compiler-ast compiler.ast \
    -o lang_composed.s
```

This produces a standalone lang compiler. The kernel embeds the reader's AST and links in the composition glue.

## The ___main Problem

First attempt produced duplicate `___main` symbols. The kernel has one, and the AST files were including another.

Fix: `--emit-ast` mode skips `___main` generation. The kernel provides it.

## Makefile Targets

```bash
make build-kernel        # Build standalone kernel
make emit-kernel-ast     # Emit kernel as S-expr AST
make emit-lang-reader-ast # Emit lang reader as AST
make test-composition    # Kernel + reader.ast = working compiler
```

## Status

Composition works. `./out/lang_composed` compiles hello.lang correctly. Next: verify bootstrap (composed compiler can compile its own reader).
