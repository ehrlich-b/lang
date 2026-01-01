# Primary Issue: Bootstrap Hop Strategy (Phase 2 Migration)

## Current State (2025-12-31) - COMPLETE!

All issues have been resolved. The phase2 branch is ready for merge.

**Test Results:**
- Regular compiler (phase2): **165/165 PASS**
- Standalone compiler (-c lang): **165/165 PASS**
- Fixed point: **VERIFIED** (phase2 compiles itself identically)

## Issues Fixed in This Session

### 1. sexpr_reader missing `=` operator (Tests 090, 091)
The `sexpr_op_to_token()` function was missing the `=` operator for assignment expressions.
- **Fix**: Added `if streq(op, "=") { return TOKEN_EQ; }` to sexpr_reader.lang

### 2. ast_emit empty `k` parameter in effect_handler
When effect handlers don't use a continuation (e.g., exception-style handlers), the `k` parameter has length 0.
`ast_emit_strn()` outputs nothing for empty strings, causing malformed AST like:
```
(effect_handler Fail e  (number 0))  // Note double space - k is missing!
```
- **Fix in ast_emit.lang**: Output `_` for empty k, same as empty binding
- **Fix in sexpr_reader.lang**: Handle `_` as empty k

### 3. Parser handle body requires block expression
The handle expression body was parsed using `parse_statement()` which requires semicolons.
This broke `handle { expr }` without semicolon (block expression syntax).
- **Fix in parser.lang**: Parse handle body using block expression logic (like `parse_block_expr()`)
  that allows trailing expression without semicolon.

## The Original Problem (Solved)

Phase 2 of quote removal changed BOTH parser AND codegen simultaneously:
- Parser now strips quotes from string literals → stores raw bytes
- Codegen now expects raw strings → adds quotes for output

When OLD bootstrap compiles NEW sources, there's a mismatch that corrupts strings.

**Solution**: Bootstrap hop - build phase2 using trusted phase1 compiler, achieve fixed point.

## Files Modified on phase2 Branch

1. **src/codegen.lang**:
   - `write_ascii_string`: Clean version, expects raw strings only
   - `ast_to_string_expr` STRING_EXPR: Clean version, expects raw strings only

2. **src/sexpr_reader.lang**:
   - Added `(macro ...)` handler
   - Added `(quote ...)`, `(unquote ...)`, `(unquote_string ...)` handlers
   - Added `=` operator to `sexpr_op_to_token()`
   - Fixed `_` handling for empty k in effect handlers

3. **src/ast_emit.lang**:
   - Fixed empty k output to use `_` instead of empty string

4. **src/parser.lang**:
   - Fixed handle body parsing to use block expression logic

## Compilers in /tmp

- `/tmp/phase1` - a75a74d compiler (trusted, can read both formats)
- `/tmp/phase2_current` - Clean Phase 2 with all fixes
- `/tmp/standalone_current` - Standalone compiler, all tests passing

## Next Steps

1. Run full `make verify` to ensure Makefile works
2. Merge phase2 to main
3. Run `make promote` to update bootstrap
