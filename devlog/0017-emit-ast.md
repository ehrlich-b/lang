# 0017: AST Emission as S-expressions

**Date**: 2024-12-28

## Goal

First step toward kernel split: emit parsed AST as S-expressions for debugging and future interchange format.

## Design Decision

Considered three formats for AST interchange:
1. **Binary format** - compact but opaque
2. **In-memory structs** - fast but architecture-dependent
3. **S-expressions** - human-readable, trivial to parse, proven

Chose S-expressions because:
- Already have S-expr readers (lisp macro)
- Can debug AST by reading output directly
- Universal format that works for any future readers
- This is compile-time, not runtime - parsing overhead acceptable

Created `designs/ast_interchange.md` documenting the full format.

## Implementation

### New File: `src/ast_emit.lang`

850 lines that convert internal AST to S-expression text:
- `ast_emit_program()` - entry point
- `ast_emit_node()` - dispatch on node kind
- `ast_emit_type()` - emit type nodes
- Helper functions for output buffer management

### Modified: `src/main.lang`

Added `--emit-ast` flag:
```lang
if emit_ast_mode != 0 {
    var ast_str *u8 = ast_emit_program(prog);
    file_write(fd, ast_str, strlen(ast_str));
}
```

### Bug Fixes

Several `vec_get()` calls were wrong - not all arrays in the parser are Vecs:
- Function params: raw array, 24 bytes each
- Block stmts: raw array, 8 bytes each (pointers)
- Match arms: raw array, 16 bytes each
- Effect cases: raw array, 56 bytes each

Added accessor helpers: `get_param()`, `get_stmt()`, `get_ptr_at()`, `get_effect_case()`

### Bootstrap Issue

Adding ast_emit.lang pushed string count over LIMIT_STRINGS (1000). Required two-phase bootstrap:
1. Build compiler with stub ast_emit (gets new limits)
2. Build full compiler with real ast_emit

Increased LIMIT_STRINGS to 2000.

## Example Output

```bash
./out/lang test.lang --emit-ast -o test.ast
```

```lisp
(program
  (include "test.lang")
  (func ___main ((param argc (type-base i64))
                 (param argv (type-ptr (type-ptr (type-base u8)))))
        (type-base i64)
    (block
      (return (call (ident main) (ident argc) (ident argv))))))
```

Note: includes appear as directives (expanded at codegen time).

## Next Steps

1. `--from-ast` - parse S-expr AST, feed to codegen
2. Round-trip verification: parse -> emit -> parse -> codegen
3. Eventually: readers emit S-expr AST instead of lang text

## Metrics

- Fixed point verified
- All 158 tests pass
- ast_emit.lang: 850 lines
