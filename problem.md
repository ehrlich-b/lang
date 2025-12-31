# Bootstrap Crisis - Forensic Analysis

## Current State (2024-12-31 ~14:45)

**CRITICAL**: The x86 bootstrap chain is broken. All attempts to `make verify` fail with:
```
Error: expected ')' in S-expression
Error: failed to parse S-expression
Error: failed to parse reader output
```

## The Bug

### Root Cause
Commit `ad6014d` ("Split architecture: lang-reader is now default verify/promote") introduced a bug in `src/ast_emit.lang`:

**Before (correct):**
```lang
if kind == NODE_STRING_EXPR {
    ast_emit_str("(string ");
    ast_emit_quoted_string(string_expr_value(node), string_expr_value_len(node));
    ast_emit_str(")");
    return;
}
```

**After (broken):**
```lang
if kind == NODE_STRING_EXPR {
    ast_emit_str("(string ");
    // String value already includes quotes from source, emit directly
    ast_emit_strn(string_expr_value(node), string_expr_value_len(node));  // BUG!
    ast_emit_str(")");
    return;
}
```

### Why It Breaks
When a string contains `)`, like `"expected ')' after binding"`, the S-expression output becomes:
```
(string "expected ')' after binding")
```

The S-expression parser's tokenizer SHOULD handle this (the `)` is inside quotes). But somewhere in the pipeline, the paren counting goes wrong and the parser fails.

### I Fixed ast_emit.lang
The fix is in place - line 611 now uses `ast_emit_quoted_string`. Verified in source.

## The Deeper Problem

Even with the fix in `src/ast_emit.lang`, the **standalone compiler** still fails.

### Architecture Understanding

1. **LLVM Bootstrap** (`bootstrap/llvm_libc_compiler.ll`)
   - Self-contained LLVM IR
   - Compiles .lang files directly (lexer → parser → codegen)
   - Does NOT use ast_emit at runtime
   - WORKS to compile all sources

2. **Stage1** (built from LLVM bootstrap)
   - x86 compiler built by: `clang llvm_libc_compiler.ll -o boot; boot [sources] -o stage1.s`
   - Also compiles .lang files directly
   - Has fixed ast_emit compiled in
   - WORKS: can compile parser.lang, can emit valid AST

3. **Standalone** (built from stage1 with `-c lang`)
   - Built by: `stage1 -c lang src/lang_reader.lang -o standalone.s`
   - Contains:
     - `lang_reader.lang` (includes lexer, parser, ast_emit)
     - `standalone.lang` (includes sexpr_reader)
   - When it runs:
     1. Reads .lang file
     2. Calls `reader_transform()` → invokes lang_reader
     3. lang_reader outputs S-expression AST (uses ast_emit)
     4. sexpr_reader parses that AST
   - FAILS on parser.lang with "expected ')' in S-expression"

### The Mystery

**Stage1 (fixed) can:**
- Compile parser.lang directly ✓
- Emit valid AST for parser.lang with `--emit-expanded-ast` ✓
- Parse that AST back with `--from-ast` ✓

**Standalone (built from fixed stage1) cannot:**
- Compile parser.lang ✗
- Even compile a simple test file with `)` in a string ✗

**Verified the standalone HAS the fix:**
- Checked `.lang-cache/readers/lang.s` assembly
- `ast_emit_quoted_string` IS being called for NODE_STRING_EXPR
- The assembly shows the correct escaping logic

### Hypotheses

1. **sexpr_reader bug in standalone** - The standalone includes `src/sexpr_reader.lang`. Maybe there's a bug in how it tokenizes strings that only manifests in the standalone context.

2. **Different code paths** - Stage1's `--from-ast` and standalone's internal sexpr_reader might use different code paths.

3. **Compilation issue** - Something about how stage1 compiles the standalone causes the sexpr_reader to be broken, even though the source is correct.

4. **Memory/buffer issue** - The standalone allocates buffers differently and something is getting corrupted.

## Working Recovery Path

The LLVM bootstrap WORKS:
```bash
clang bootstrap/llvm_libc_compiler.ll -o /tmp/llvm_boot
/tmp/llvm_boot [all sources] -o /tmp/stage1.s
as /tmp/stage1.s -o /tmp/stage1.o && ld /tmp/stage1.o -o /tmp/stage1
# stage1 reaches fixed point and works
```

But we CANNOT build a working standalone from stage1.

## Files of Interest

- `src/ast_emit.lang:608-614` - The fix is here (NODE_STRING_EXPR uses ast_emit_quoted_string)
- `src/lang_reader.lang` - Includes ast_emit, outputs AST
- `src/standalone.lang` - Template for standalone, includes sexpr_reader
- `src/sexpr_reader.lang` - Parses S-expression AST
- `std/tok.lang:238-252` - Tokenizer string handling (looks correct)
- `bootstrap/llvm_libc_compiler.ll` - Working LLVM bootstrap
- `/tmp/fixed` - Working stage1 compiler (non-standalone)
- `/tmp/fresh_standalone` - Broken standalone compiler

## Test Cases

**Works:**
```bash
/tmp/fixed std/core.lang src/parser.lang -o /tmp/p.s  # Direct compile
/tmp/fixed --emit-expanded-ast src/parser.lang -o /tmp/p.ast  # Emit AST
/tmp/fixed --from-ast /tmp/p.ast -o /tmp/p.s  # Parse AST
```

**Fails:**
```bash
/tmp/fresh_standalone src/parser.lang -o /tmp/p.s  # Standalone compile
/tmp/fresh_standalone /tmp/test_paren.lang -o /tmp/t.s  # Even simple file with ) in string
```

Where `/tmp/test_paren.lang` is:
```lang
func test() void {
    var msg *u8 = "hello ) world";
}
```

## Next Steps to Investigate

1. Add debug output to standalone to see what AST the lang_reader produces
2. Compare sexpr_reader behavior between stage1 (`--from-ast`) and standalone
3. Check if there's a different tokenizer being used
4. Manually trace through the tokenizer with a string containing `)`
5. Check buffer sizes and memory allocation in standalone vs stage1

## Bootstrap State

- `bootstrap/current` → `bootstrap/8228b82/`
- `bootstrap/8228b82/compiler.s` - Contains a standalone that was built (has the bug baked in)
- The symlink points to broken compiler
- All historical `bootstrap/*/lang_reader/source.ast` files are "corrupted" (contain unescaped parens in strings, but this is actually VALID for proper S-expr parsing)

## Key Insight

The "corrupted" AST files might actually be VALID. The issue isn't that parens in strings break S-expression format - they shouldn't if quoted properly. The issue is that the sexpr_reader in the standalone has a bug that causes it to miscount parens even when they're inside quoted strings.

The same sexpr_reader code works in stage1 (via `--from-ast`) but fails in standalone. This suggests a compilation or linking issue, not a source code bug.

## Quick Recovery Commands

If you need a working compiler quickly:
```bash
# LLVM bootstrap always works
clang bootstrap/llvm_libc_compiler.ll -o /tmp/llvm_boot
/tmp/llvm_boot std/core.lang src/*.lang -o /tmp/stage1.s
as /tmp/stage1.s -o /tmp/stage1.o && ld /tmp/stage1.o -o /tmp/stage1

# stage1 can compile any .lang file
/tmp/stage1 std/core.lang yourfile.lang -o out.s
```

## Git State

- Current commit: 8505460 (includes fix attempt)
- Uncommitted: This problem.md file
- The fix to ast_emit.lang IS committed but doesn't solve the standalone issue

## Timeline

1. Bug introduced in ad6014d (Dec 30)
2. LLVM bootstrap created/updated in 246b9db-60bd5e1 (after bug)
3. Multiple failed recovery attempts today (Dec 31)
4. Discovered the bug, fixed ast_emit.lang
5. Fix works for stage1 but NOT for standalone
6. Currently stuck - standalone fails even with fix compiled in
