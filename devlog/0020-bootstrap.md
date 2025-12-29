# 0020: Bootstrap

**Date**: 2024-12-29

## The Test

Can the composed compiler compile its own reader?

```bash
# Step 1: Kernel composes with lang reader AST
./out/kernel -c lang_reader.ast --kernel-ast kernel.ast -o lang_composed.s

# Step 2: Composed compiler compiles lang reader SOURCE
./out/lang_composed -c lang_reader.lang --kernel-ast kernel.ast -o lang_bootstrap.s

# Step 3: Compare
diff lang_composed.s lang_bootstrap.s
```

No output. Identical.

## Fixed Point

One more step. Can the bootstrapped compiler bootstrap itself?

```bash
./out/lang_bootstrap -c lang_reader.lang --kernel-ast kernel.ast -o lang_bootstrap2.s
diff lang_bootstrap.s lang_bootstrap2.s
```

No output. Fixed point achieved.

## What This Proves

1. The S-expression AST format is complete (nothing lost in translation)
2. The kernel correctly compiles reader AST to x86
3. The composed compiler correctly parses lang syntax
4. The whole thing is a closed loop

## The Stack

```
mmap, read, write, exit     <- 4 syscalls
        ↑
    std/core.lang           <- allocation, I/O
        ↑
    AST (S-expressions)     <- the interchange format
        ↑
    kernel (codegen.lang)   <- AST → x86
        ↑
    lang reader             <- lang → AST
        ↑
    .lang source files      <- what you write
```

Everything above the syscalls is written in lang and compiles itself.

## Rename

Project renamed from "language" to "lang". The `.lang` extension stays. Search for it as "langlang" (like golang, rustlang).

## Preserved Artifacts

- `bootstrap/current.s` → latest stable compiler assembly
- `bootstrap/*.s` → historical snapshots by git commit
- `archive/boot-go/` → the original Go bootstrap (deleted from active use)

## 159 Tests Pass

`make verify` runs the full test suite against the new compiler. All pass.

This is the actual grand finale. For now.
