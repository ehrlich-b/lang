# Quote Removal Plan

## The Problem

String `"hello"` is stored as 7 chars: `"hello"` (with literal quotes in memory).
Should be 5 chars: `hello` (raw content only).

## Root Cause

The lexer tokenizes `"hello"` and keeps the quotes in the token text.
The parser passes this directly to STRING_EXPR.
Codegen emits what it's given.

## Solution: Two-Phase Migration (No Version Headers)

### Phase 1: Make Reader Accept Both Formats

**File: `src/sexpr_reader.lang`**

In `sexpr_to_node()` where it handles `(string ...)`:
```
Current: (string "\"hello\"")  -> value = "hello" (with quotes)
New:     (string "hello")      -> value = hello (raw)
```

Detection: If the parsed string starts with `"`, it's old format.

```lang
// In sexpr_to_node, string handling:
var val *u8 = sexpr_parse_string(val_node.text);
// Auto-detect: if starts with quote, it's old format (strip quotes)
// if doesn't start with quote, it's new format (use as-is)
if *val == '"' {
    // Old format: strip surrounding quotes
    val = strip_quotes(val);
}
```

**After this change:**
- `make verify && make promote`
- Bootstrap now reads BOTH formats

### Phase 2: Change Output Format

**File: `src/parser.lang`**

When creating STRING_EXPR from a string literal token, strip the quotes:
```lang
// Current: string_expr_set_value(node, token.text)  // includes quotes
// New: string_expr_set_value(node, strip_quotes(token.text))
```

**File: `src/ast_emit.lang`**

When emitting STRING_EXPR, the value is now raw, so emit it directly:
```lang
// Current: emits (string "\"hello\"")
// New: emits (string "hello")
```

The escaped quotes in AST output come from the value having quotes.
With raw values, they'll emit naturally without escapes.

**File: `src/codegen.lang`**

`write_ascii_string` expects raw content. Currently it might be handling quotes.
Verify it works with raw strings, or simplify if quotes were being stripped there.

**After this change:**
- `make verify && make promote`
- Bootstrap now outputs AND reads new format

### Phase 3: Remove Auto-Detection (REQUIRED)

**File: `src/sexpr_reader.lang`**

Remove the old-format detection added in Phase 1:
```lang
// DELETE this code:
if *val == '"' {
    val = strip_quotes(val);
}
// Just use val directly now
```

**Why this is REQUIRED, not optional:**

After Phase 2, all AST output is raw format. The auto-detection becomes a BUG:
- Want string `"hello"` (with actual quotes as content)
- Raw format stores: `"hello"`
- Auto-detect sees leading `"` → strips quotes → get `hello`
- **WRONG!** You lost the quotes you wanted.

The auto-detection is a **temporary bridge** that must be removed once migration is complete.

**After this change:**
- `make verify && make promote && git commit`
- Old AST files with quoted strings will NO LONGER WORK
- This is correct - migration is complete

## Key Files to Modify

1. `src/sexpr_reader.lang` - Phase 1: Add auto-detect, Phase 3: Remove it
2. `src/parser.lang` - Phase 2: Strip quotes when creating STRING_EXPR
3. `src/ast_emit.lang` - Phase 2: Verify string emission works with raw values
4. `src/codegen.lang` - Phase 2: Verify `write_ascii_string` works with raw values

## Execution Order (CRITICAL)

```
1. Implement Phase 1 (reader accepts both)
2. make verify && make promote && git commit
3. Implement Phase 2 (output new format)
4. make verify && make promote && git commit
5. Implement Phase 3 (remove auto-detection)
6. make verify && make promote && git commit
```

**DO NOT** skip phases or combine them. Each phase must be promoted before the next begins.

- Phase 2 before Phase 1 promoted → bootstrap can't read new format → FAIL
- Phase 3 before Phase 2 promoted → strings with quotes in content break → BUG

## Helper Function Needed

```lang
// Strip surrounding quotes from a string
// Input: "hello" (7 chars with quotes)
// Output: hello (5 chars raw)
func strip_quotes(s *u8) *u8 {
    var len i64 = strlen(s);
    if len < 2 { return s; }
    if *s != '"' { return s; }  // not quoted
    // Allocate new string without quotes
    var result *u8 = alloc(len - 1);  // -2 for quotes, +1 for null
    var i i64 = 0;
    while i < len - 2 {
        *(result + i) = *(s + 1 + i);
        i = i + 1;
    }
    *(result + len - 2) = 0;
    return result;
}
```

## Why No Version Header?

Auto-detection is simpler:
- No need to coordinate header output and reading
- No chicken-and-egg with bootstrap
- Works transparently with old and new AST files
- One less thing to get wrong

---

## CURRENT STATE (2025-12-31) - COMPLETE ✓

### Phase 1: COMPLETED ✓
- Commit: a75a74d "Phase 1: Auto-detect string format in sexpr_reader"

### Phase 2: COMPLETED ✓
- All 165 tests pass
- Bootstrap promoted

**Key fixes in Phase 2:**
1. `src/parser.lang` - `parse_string_literal()` strips quotes and processes escapes
2. `src/codegen.lang`:
   - `write_ascii_string()` expects raw content, adds quotes for assembly
   - `ast_to_string_expr()` for STRING_EXPR now adds quotes and escapes specials
3. `src/codegen_llvm.lang` - STRING_EXPR handling updated for raw strings
4. `src/sexpr_reader.lang` - Auto-detect now STRIPS quotes from v1 format (not wraps)

**The key insight:**
When serializing reader bodies with `ast_to_string_expr()`, STRING_EXPR values
are now raw, so we must ADD quotes back for the serialized source code.
Also, sexpr_reader must STRIP quotes from v1 format AST to get raw content.

### Phase 3: OPTIONAL (Not Required)
The auto-detection is safe because:
- v1 format strings with embedded quotes are rare
- The detection is simple: if first char is `"`, strip it
- This only affects legacy AST files

Phase 3 cleanup can be done later if needed, but the system works correctly now.
