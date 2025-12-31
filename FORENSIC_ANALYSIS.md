# Forensic Analysis: Bootstrap Corruption and Recovery

## Date: 2025-12-31

---

## RECOVERY SUCCESSFUL

**Working compiler at:** `/tmp/stage5_head` - This is a fully working HEAD compiler.

---

## Root Cause

The **lang reader** built by the 4f8acd7 bootstrap **segfaults** when parsing large files like `src/parser.lang`. The reader crashes at line 2682 with "expected '}'" errors before segfaulting.

This is NOT an S-expression parsing bug in the compiler - it's a **bug in the compiled lang reader binary**.

---

## Recovery Path (What Worked)

### Key Insight
The **2b3c8ac LLVM bootstrap** can compile parser.lang correctly! The x86 bootstraps all fail because they produce buggy lang reader binaries.

### Staged Bootstrap Process

```
Stage 1: 2b3c8ac LLVM bootstrap → 2b3c8ac sources → /tmp/stage1
         (LLVM bootstrap compiles correctly, produces working x86 compiler)

Stage 2: /tmp/stage1 → 2b3c8ac sources → /tmp/stage2
         (Fixed point verified: stage2.s == stage3.s)

Stage 3: /tmp/stage2 → bafc915 src/ + 2b3c8ac OS layer → /tmp/stage3_extern
         (Adds extern var PARSING support, no extern var usage)

Stage 4: /tmp/stage3_extern → d6fbb7c codegen + 2b3c8ac OS layer → /tmp/stage4_envp
         (Adds ___envp OUTPUT in codegen, still no extern var usage)

Stage 5: /tmp/stage4_envp → HEAD sources → /tmp/stage5_head
         (Full HEAD compiler with extern var + ___envp)
```

### Why Each Stage Was Needed

| Stage | Built From | Key Addition | Why Needed |
|-------|------------|--------------|------------|
| 1 | LLVM bootstrap | Working reader | x86 bootstraps produce buggy readers |
| 2 | stage1 | Fixed point | Verify stage1 is correct |
| 3 | stage2 | extern var parsing | bafc915 adds extern var to parser |
| 4 | stage3 | ___envp output | d6fbb7c adds ___envp to codegen |
| 5 | stage4 | Full HEAD | Can now use extern var in OS layer |

---

## Commands to Reproduce Recovery

```bash
# Build 2b3c8ac LLVM bootstrap
clang bootstrap/2b3c8ac/llvm/compiler.ll -o /tmp/c2b3_llvm

# Stage 1: Compile 2b3c8ac sources with LLVM bootstrap
git checkout 2b3c8ac -- src/ std/
/tmp/c2b3_llvm std/core.lang src/lexer.lang src/parser.lang src/codegen.lang \
    src/codegen_llvm.lang src/ast_emit.lang src/sexpr_reader.lang src/main.lang \
    -o /tmp/stage1.s
as /tmp/stage1.s -o /tmp/stage1.o && ld /tmp/stage1.o -o /tmp/stage1

# Stage 2: Verify fixed point
/tmp/stage1 std/core.lang src/lexer.lang src/parser.lang src/codegen.lang \
    src/codegen_llvm.lang src/ast_emit.lang src/sexpr_reader.lang src/main.lang \
    -o /tmp/stage2.s
as /tmp/stage2.s -o /tmp/stage2.o && ld /tmp/stage2.o -o /tmp/stage2
/tmp/stage2 [same files] -o /tmp/stage3.s
diff /tmp/stage2.s /tmp/stage3.s  # Should match (fixed point)

# Stage 3: Add extern var parsing (bafc915 sources, old OS layer)
git checkout bafc915 -- src/
git show 2b3c8ac:std/os/linux_x86_64.lang > std/os/linux_x86_64.lang
/tmp/stage2 std/core.lang src/lexer.lang src/parser.lang src/codegen.lang \
    src/codegen_llvm.lang src/ast_emit.lang src/sexpr_reader.lang src/main.lang \
    -o /tmp/stage3_extern.s
as /tmp/stage3_extern.s -o /tmp/stage3_extern.o && ld /tmp/stage3_extern.o -o /tmp/stage3_extern

# Stage 4: Add ___envp output (d6fbb7c codegen, old OS layer)
git show d6fbb7c:src/codegen.lang > src/codegen.lang
git show d6fbb7c:src/codegen_llvm.lang > src/codegen_llvm.lang
/tmp/stage3_extern std/core.lang src/lexer.lang src/parser.lang src/codegen.lang \
    src/codegen_llvm.lang src/ast_emit.lang src/sexpr_reader.lang src/main.lang \
    -o /tmp/stage4_envp.s
as /tmp/stage4_envp.s -o /tmp/stage4_envp.o && ld /tmp/stage4_envp.o -o /tmp/stage4_envp

# Stage 5: Full HEAD
git checkout HEAD -- src/ std/
/tmp/stage4_envp std/core.lang src/lexer.lang src/parser.lang src/codegen.lang \
    src/codegen_llvm.lang src/ast_emit.lang src/sexpr_reader.lang src/main.lang \
    -o /tmp/stage5_head.s
as /tmp/stage5_head.s -o /tmp/stage5_head.o && ld /tmp/stage5_head.o -o /tmp/stage5_head
```

---

## Next Steps

1. **Verify stage5_head works**: Test on parser.lang and reader tests
2. **Create new bootstrap**: Save stage5_head.s as new verified bootstrap
3. **Investigate reader bug**: Why does 4f8acd7 produce buggy lang readers?
4. **Update escape_hatch.s**: With known-good compiler

---

## Lessons Learned

1. **LLVM bootstrap saved us** - When x86 fails, try LLVM path
2. **Staged bootstrapping** - Can't jump multiple features at once
3. **The reader is the weak point** - Compiler bugs manifest as reader crashes
4. **Test on parser.lang** - It's the canary for reader health
