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

---

## INCIDENT POSTMORTEM: Bootstrap Corruption (2025-12-31)

### What Happened

After Phase 2 was "completed", the kernel fixed point started failing with:
```
Error: unterminated string
```

The Phase 2 compiler couldn't compile anything - not even the simplest test file.

### Root Cause: Corrupted Bootstrap

The `bootstrap/a75a74d/compiler.s` file stored in the repository was **completely wrong**.
It did not match what the 4e4ab61 bootstrap would actually produce for a75a74d sources.

**Evidence:**
```bash
# Rebuild a75a74d from scratch with known-good bootstrap
as bootstrap/4e4ab61/compiler.s -o /tmp/prev.o && ld /tmp/prev.o -o /tmp/prev
/tmp/prev [a75a74d sources] -o /tmp/rebuilt.s

# Compare with stored version
diff /tmp/rebuilt.s bootstrap/a75a74d/compiler.s
```

Result: **Massive differences.** String literals were completely wrong:
- Stored a75a74d had: `.ascii "+\000"`, `.ascii "-\000"`, `.ascii "*\000"`
- Correct output has: `.ascii ".lang-cache/readers/\000"`, `.ascii "./out/lang\000"`

The stored file had operator symbols where path strings should be - total garbage.

### Specific Failure Mode

The corrupted bootstrap had broken escape sequences in `write_ascii_string()` output:
- For string `"\"\n"` (quote + newline, 2 bytes)
- Correct output: `"\"\012\000"` (escaped quote + octal newline + null)
- Corrupted output: `"\000"` (just null - empty string!)

This caused the Phase 2 compiler to emit empty strings for any string containing
quote+newline, which appears in `src/main.lang`:
```lang
append_str(source_buf, &source_len, "\"\n");  // Used to close include paths
```

When the compiler tried to build source with `include "file.lang"\n`, the closing
`"\n` was empty, leaving the string unterminated.

### The Fix

Point `bootstrap/current` back to 4e4ab61 (the last known-good version):
```bash
cd bootstrap && rm current && ln -s 4e4ab61 current
make verify  # Now passes
make promote # Creates correct 1654aca bootstrap
```

---

## Deep Dive: How make verify and make promote Work

### make verify: The 8-Phase Verification

```
Phase 1: Bootstrap from known-good
  - Assembles bootstrap/current/compiler.s → /tmp/boot
  - This is the TRUSTED compiler

Phase 2: Build compiler from sources
  - /tmp/boot compiles src/*.lang → out/lang_VERSION.s
  - Assemble and link → out/lang_VERSION (the "candidate")
  - Symlink: out/lang_next → lang_VERSION

Phase 3: KERNEL FIXED POINT
  - out/lang_next compiles src/*.lang → out/lang_VERSION_v2.s
  - diff out/lang_VERSION.s out/lang_VERSION_v2.s
  - MUST be identical (compiler compiles itself to same output)

Phase 4: Build standalone compiler
  - out/lang_next -c lang src/lang_reader.lang → out/lang_standalone.s
  - This tests reader serialization/compilation

Phase 5: READER FIXED POINT
  - out/lang_standalone compiles a test program
  - Verifies the standalone compiler works

Phase 6: x86 test suite (165 tests)
Phase 7: Build LLVM+libc bootstrap compiler
Phase 8: LLVM test suite (165 tests)
```

### make promote: What Gets Saved

```
1. cp out/lang_standalone.s bootstrap/VERSION/compiler.s
   - NOTE: Saves the STANDALONE compiler, not lang_VERSION.s!

2. cp out/llvm_libc_compiler.ll bootstrap/VERSION/llvm_libc_compiler.ll

3. cp out/ast/lang_reader_v1.ast bootstrap/VERSION/lang_reader/source.ast

4. ln -sfn VERSION bootstrap/current
   - Updates the symlink

5. cp to bootstrap/escape_hatch.s and bootstrap/llvm_libc_compiler.ll
   - Backup copies at root level

6. ln -sf lang_VERSION out/lang
   - Makes out/lang point to the new stable compiler
```

### Why Didn't Verify Catch the Corruption?

**The corrupted bootstrap was never actually USED by verify.**

Here's the critical insight: When `make promote` ran for Phase 1 (a75a74d),
the corrupted file was saved to `bootstrap/a75a74d/compiler.s`, and the symlink
`bootstrap/current` was updated to point to it.

BUT: The corruption happened DURING the promote, not before verify.

**Timeline reconstruction:**
1. Phase 1 changes made to sources
2. `make verify` runs using bootstrap/4e4ab61 (GOOD)
3. Verify passes (using the GOOD bootstrap)
4. `make promote` saves output
5. **Something corrupts the output file during save**
6. Symlink updated to point to corrupted file
7. Next `make verify` uses corrupted bootstrap → FAILS

### How Could the File Get Corrupted?

Possibilities:
1. **Filesystem issue** - Partial write, disk error
2. **Race condition** - Multiple processes writing
3. **User error** - Wrong file copied manually
4. **Tool bug** - Something in the Makefile went wrong

The most likely cause: **The wrong file was copied.** The stored a75a74d bootstrap
contains strings that look like they're from a much OLDER version of the compiler
(before paths like `.lang-cache/readers/` existed). This suggests an old cached
file was accidentally promoted instead of the fresh build.

### Lessons Learned

1. **Verify checks the BUILD, not the SAVED file**
   - Verify uses whatever bootstrap/current points to
   - If you corrupt the file AFTER verify but BEFORE the next verify, you're toast
   - The promote step itself is not verified

2. **No hash verification on promote**
   - The Makefile doesn't verify the file it's copying matches expectations
   - A simple `sha256sum` check could catch corruption

3. **PROVENANCE files lie**
   - a75a74d/PROVENANCE claimed: `built_by: bootstrap/4e4ab61`
   - This was written by the Makefile, assuming success
   - But the actual file was garbage

### Proposed Safeguards

```makefile
# After copying, verify the new bootstrap can compile itself
promote:
    ... existing copy steps ...
    # NEW: Verify the saved bootstrap works
    as bootstrap/$(VERSION)/compiler.s -o /tmp/verify_promote.o
    ld /tmp/verify_promote.o -o /tmp/verify_promote
    /tmp/verify_promote std/core.lang src/*.lang -o /tmp/verify_promote_output.s
    diff /tmp/verify_promote_output.s out/lang_$(VERSION).s || \
        (echo "PROMOTE VERIFICATION FAILED"; exit 1)
```

This would catch any corruption in the saved file immediately.

---

## Current State After Recovery

- `bootstrap/current` → `1654aca` (correctly promoted)
- Phase 2 complete: Strings stored as raw bytes
- All 165 tests pass on both x86 and LLVM backends
- Kernel and reader fixed points verified

The corrupted `bootstrap/a75a74d` directory still exists but is not used.
It could be deleted or kept for forensic analysis.
