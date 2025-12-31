# Bootstrap Crisis - Forensic Analysis

## Current State (2024-12-31 ~17:00)

**STATUS**: Partial recovery. Kernel fixed point works. Reader fixed point works. But 2 tests fail (235, 237) and the verify/promote incorrectly says "ALL PASSED" even with failures.

**Current bootstrap**: `8f83802` (fb0caaa is latest commit)

```
Passed: 163 / 165
FAIL 235_ast_literals (expected 0, got 3)
FAIL 237_ast_calls (expected 0, got 6)
```

## The Core Design Flaw

**The entire codebase passes string values WITH quotes embedded in memory.**

```
Source:     var s = "hello";
Tokenizer:  captures "hello" (7 chars, including quotes)
Parser:     stores "hello" in string_expr_value
Codegen:    expects "hello" with quotes to emit .ascii "hello\000"
```

This is a fundamental design decision that permeates:
- `std/tok.lang` - tokenizer includes quotes in token
- `src/parser.lang` - stores token text directly
- `src/codegen.lang` - expects quotes for write_ascii_string
- `src/ast_emit.lang` - double-escapes: "hello" → "\"hello\""
- `src/sexpr_reader.lang` - must handle the escaping

## What I Fixed (and broke)

### Fix 1: standalone.lang paren counting ✓
The standalone strips `(program ...)` wrapper using naive paren counting that didn't skip quoted strings:
```lang
// OLD - broken
while *end != 0 && depth > 0 {
    if *end == 40 { depth = depth + 1; }
    if *end == 41 { depth = depth - 1; }
    end = end + 1;
}

// NEW - fixed
while *end != 0 && depth > 0 {
    if *end == 34 {  // '"' - skip quoted strings
        end = end + 1;
        while *end != 0 && *end != 34 {
            if *end == 92 { end = end + 1; }
            if *end != 0 { end = end + 1; }
        }
        if *end == 34 { end = end + 1; }
    } else {
        if *end == 40 { depth = depth + 1; }
        if *end == 41 { depth = depth - 1; }
        end = end + 1;
    }
}
```

### Fix 2: standalone.lang ___main params ✓
Standalone used 2-param ___main, kernel uses 3-param. Fixed to match.

### Fix 3: sexpr_reader.lang string handling ✗ PROBLEMATIC
Changed from storing raw token text to using sexpr_parse_string:
```lang
// OLD
string_expr_set_value(n, val_node.text);

// NEW
var val *u8 = sexpr_parse_string(val_node.text);
string_expr_set_value(n, val);
```

**The problem**: This works for the PARSER path but breaks the AST BUILDER path.

## The Two Paths

### Parser Path (works with my fix)
```
Source: "hello"
Parser stores: "hello" (7 chars with quotes)
ast_emit outputs: (string "\"hello\"")  -- escaped quotes
sexpr_reader token: "\"hello\"" (11 chars)
sexpr_parse_string: "hello" (7 chars) ✓ matches parser
```

### AST Builder Path (BROKEN with my fix)
```
User calls: ast_string("hello") with value "hello" (5 chars, NO quotes)
ast_quote_string wraps: "hello" (7 chars)
S-expr output: (string "hello")
sexpr_reader token: "hello" (7 chars)
sexpr_parse_string: hello (5 chars) ✗ NO QUOTES - codegen fails!
```

## The Architectural Problem

There are TWO different conventions in the codebase:

1. **Parser convention**: String values include source quotes
   - `"hello"` in source → `"hello"` in memory (7 chars)

2. **AST builder convention**: String values are raw content
   - `ast_string("hello")` → value is `hello` (5 chars)
   - `ast_quote_string` adds quotes for S-expr format

These conventions COLLIDE at sexpr_reader. My fix assumed parser convention everywhere, but std/ast.lang uses a different convention.

## Why Tests 235 and 237 Fail

These tests use `std/ast.lang` to build AST programmatically:
```lang
reader hello(text *u8) *u8 {
    return ast_string("hello");  // passes "hello" without quotes
}
```

With my sexpr_reader fix:
1. ast_string produces `(string "hello")`
2. sexpr_parse_string strips quotes → `hello`
3. codegen expects `"hello"` → FAILS

## The Ugly "Fix" I Tried

I tried making ast_quote_string double-escape like ast_emit:
```lang
// Output "\"hello\"" instead of "hello"
sb_char(sb, '"');   // outer quote
sb_char(sb, '\\');  // escaped
sb_char(sb, '"');   // inner quote
// ... content ...
sb_char(sb, '\\');  // escaped
sb_char(sb, '"');   // inner quote
sb_char(sb, '"');   // outer quote
```

This is INSANE. Now we're passing `"\"hello\""` around in memory.

## The Real Fix Needed

The codebase needs ONE consistent convention. Options:

### Option A: Values WITHOUT quotes (clean)
1. Tokenizer strips quotes when capturing strings
2. Parser stores raw content: `hello`
3. Codegen adds quotes when emitting: `.ascii "hello\000"`
4. ast_emit wraps for S-expr: `(string "hello")`
5. sexpr_reader strips S-expr quotes: `hello`
6. std/ast.lang already works this way!

**Impact**: Change tokenizer, parser string handling, codegen write_ascii_string

### Option B: Values WITH quotes (current mess)
Keep the current parser convention but fix std/ast.lang to match:
1. ast_string("hello") should store `"hello"` (with quotes)
2. But then the API is terrible - users must NOT pass quotes

**Impact**: Confusing API, error-prone

### Option C: Revert sexpr_reader fix, find different solution
Revert my sexpr_parse_string change. Find why the original code worked for 165 tests but failed for standalone paren issue.

## Current Bootstrap State

```
bootstrap/current -> 8f83802
  - Has my sexpr_reader fix baked in
  - Passes 163/165 tests
  - Kernel fixed point: VERIFIED
  - Reader fixed point: VERIFIED
  - But 2 tests fail!
```

## The Escape Hatch

LLVM bootstrap still works and has NONE of these issues:
```bash
clang bootstrap/llvm_libc_compiler.ll -o /tmp/llvm_boot
/tmp/llvm_boot std/core.lang src/*.lang -o /tmp/stage1.s
as /tmp/stage1.s -o /tmp/stage1.o && ld /tmp/stage1.o -o /tmp/stage1
```

This produces a working compiler that:
- Compiles directly (no reader/standalone)
- Reaches fixed point
- Passes all tests

## Makefile Bug

`make promote` says "ALL VERIFICATIONS PASSED" even when tests fail (163/165). The promote should FAIL if any tests fail.

## Files Modified

- `src/standalone.lang` - paren counting fix + ___main fix (COMMITTED in bootstrap)
- `src/sexpr_reader.lang` - string handling fix (COMMITTED in bootstrap - PROBLEMATIC)
- `std/ast.lang` - ugly double-quote fix (UNCOMMITTED - not in bootstrap)
- `bootstrap/8f83802/` - current bootstrap with sexpr_reader issue

## Current Uncommitted State

```
M problem.md     - this file
M std/ast.lang   - ugly double-quote fix (NOT in bootstrap)
```

The bootstrap has the sexpr_reader fix but NOT the ast.lang fix, which is why tests fail.

## Git State

```
fb0caaa Promote 8f83802 - stable bootstrap
8f83802 Promote bootstrap b1da012
b1da012 Full bootstrap recovery with all fixes
a202495 Add fixed bootstrap a4a7821
a4a7821 Fix standalone string handling and paren counting for bootstrap
```

## Next Steps

1. **DO NOT make more changes** - research first
2. Check if std/ast.lang has my ugly double-quote fix or if it was reverted
3. Consider Option A (clean fix) vs Option C (revert)
4. Fix Makefile to fail on test failures
5. Possibly roll back to LLVM bootstrap and rebuild without sexpr_reader change

## Key Insight

The bootstrap is in a weird state where:
- It can compile itself (fixed point works)
- It produces slightly broken output (2 tests fail)
- The brokenness is in how strings are handled between ast_emit and sexpr_reader
- The LLVM bootstrap is clean and can rescue us

We're not "fucked" but we're bootstrapped onto a compiler that has a string handling inconsistency. We need to either:
1. Fix the inconsistency properly (Option A)
2. Revert to a clean state via LLVM bootstrap
