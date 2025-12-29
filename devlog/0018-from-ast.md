# 0018: Parsing S-expression AST

**Date**: 2024-12-28

## Goal

Close the loop: `--emit-ast` outputs S-expressions, now `--from-ast` reads them back. Round-trip verification proves the AST format is complete.

## Implementation

### src/sexpr_reader.lang

Dogfooded the `#parser{}` reader macro to build the S-expression parser:

```lang
#parser{
    sexpr = number | symbol | string | operator | list
    list = '(' sexpr* ')'
}
```

Then 400 lines of tree-walking to convert parse nodes back to AST nodes. Each S-expression form maps to an AST constructor.

### The Operator Problem

First attempt failed. The tokenizer sees `-` as minus, not part of an identifier. So `(binary-expr ...)` tokenizes as `(binary` `-` `expr ...)`.

Fix: AST node names use underscores. `binary_expr`, `func_decl`, `type_ptr`. Updated both ast_emit.lang and sexpr_reader.lang.

### Round-Trip Test

```bash
# Emit AST from source
./out/lang test.lang --emit-ast -o /tmp/test.ast

# Compile from AST
./out/lang /tmp/test.ast --from-ast -o /tmp/test.s

# Compare to direct compilation
./out/lang test.lang -o /tmp/direct.s

diff /tmp/test.s /tmp/direct.s  # identical
```

Works for the full compiler source. 159 tests pass.

## Limits Bump

Compiling from AST uses more memory (the S-expression parse tree plus the AST). Bumped limits:
- Heap: 64MB → 256MB
- Code buffer: 2MB → 4MB
- Functions: 500 → 1000
- Strings: 2000 → 3000

Centralized all limits in `src/limits.lang`.

## What This Enables

Readers can now output S-expression AST instead of lang text. The kernel doesn't need to know lang syntax at all. Next step: split the compiler into kernel (AST → x86) and readers (syntax → AST).
