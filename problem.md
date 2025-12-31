# Bootstrap Status - RESOLVED

## Current State (2024-12-31)

**STATUS**: ✅ STABLE. All 165 tests pass. Fixed point verified.

**Current bootstrap**: `9332344`

## What Was Fixed

### Issue: Two String Conventions Collision

The codebase had two different conventions:
1. **Parser convention**: String values include quotes (e.g., `"hello"` = 7 chars)
2. **AST builder convention**: String values are raw (e.g., `hello` = 5 chars)

These collided at `sexpr_reader.lang` when parsing S-expr AST.

### Solution: Match Parser Convention in AST Builder

Changed `ast_quote_string` in `std/ast.lang` to output escaped quotes:
- Input: `hello` (5 chars raw)
- S-expr output: `"\"hello\""` (11 chars with escaping)
- After `sexpr_parse_string`: `"hello"` (7 chars with quotes)

This matches what `ast_emit.lang` does for the parser path.

### Test Suite Exit Codes

Fixed `test/run_lang1_suite.sh` to return non-zero exit code on failures.
Now `make verify` and `make promote` will fail if any tests fail.

## Known Design Debt

**String values include quotes in memory.** This is weird but consistent:
- `"hello"` in source → `"hello"` in memory (7 chars)
- `ast_string("hello")` → stores `"hello"` (7 chars with quotes added)

### Future: AST v2 with Clean Convention

Plan to add AST versioning so we can migrate to:
- Values WITHOUT quotes in memory
- Tokenizer strips quotes
- Codegen adds quotes when emitting
- Cleaner API: `ast_string("hello")` stores `hello` (5 chars)

## Files Changed

- `std/ast.lang` - ast_quote_string adds quotes to match parser convention
- `test/run_lang1_suite.sh` - Exit with non-zero on test failures
- `bootstrap/9332344/` - New stable bootstrap

## Verification

```bash
make verify   # Must pass before promote
make promote  # Now fails if tests fail
```
