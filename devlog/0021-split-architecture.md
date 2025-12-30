# 0021: Split Architecture

**Date**: 2024-12-30

## Off the Monolithic Build

The compiler is now split into two separately-bootstrappable components:

- **kernel**: AST → x86 (codegen + sexpr_reader)
- **lang_reader**: lang → AST (lexer + parser + ast_emit)

The equation: `lang_compiler = kernel + lang_reader`

## Two Fixed Points

**Kernel fixed point**:
```bash
make kernel-verify
# 1. lang_next generates expanded kernel AST
# 2. Kernel compiles its own AST
# 3. Output matches original kernel assembly
```

**Lang-reader fixed point**:
```bash
make lang-reader-verify  # (now the default `make verify`)
# 1. Build standalone lang compiler with -c
# 2. Standalone compiler can compile programs
# 3. 165/165 tests pass
```

## Bootstrap Structure

```
bootstrap/
├── current → ./006bad5/
├── escape_hatch.s              <- full compiler assembly (emergency)
└── 006bad5/
    ├── compiler.s              <- standalone lang compiler
    ├── kernel/source.ast       <- expanded kernel AST (10251 lines)
    ├── lang_reader/source.ast  <- expanded lang reader AST (4966 lines)
    └── PROVENANCE              <- what built this, when
```

## Key Fix

AST round-trip was corrupting string literals. The string value already includes quotes from the source lexeme, but `ast_emit` was re-quoting:

```
Before: (string "\"\\n\"")  <- double-quoted!
After:  (string "\n")       <- correct
```

## The Default

`make verify` and `make promote` now use the split architecture (lang-reader-verify/promote). The monolithic build is gone.

## 165 Tests Pass

All tests pass through the standalone compiler. The split architecture is complete.
