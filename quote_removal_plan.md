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

### Phase 3: Clean Up (Optional)

Remove old-format detection from sexpr_reader if desired.
Or keep it for backwards compatibility with old AST files.

## Key Files to Modify

1. `src/sexpr_reader.lang` - Add auto-detect for old/new string format
2. `src/parser.lang` - Strip quotes when creating STRING_EXPR from token
3. `src/ast_emit.lang` - Verify string emission works with raw values
4. `src/codegen.lang` - Verify `write_ascii_string` works with raw values

## Execution Order (CRITICAL)

```
1. Implement Phase 1 (reader accepts both)
2. make verify && make promote && git commit
3. Implement Phase 2 (output new format)
4. make verify && make promote && git commit
```

**DO NOT** do Phase 2 before promoting Phase 1. The bootstrap must understand the new format before you output it.

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
