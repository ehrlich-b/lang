# 0008: Reader V2 and Parsing Toolkit

**Date**: 2025-12-26

## What We Did

Big session. Completed the V2 reader infrastructure and built the parsing toolkit.

### Reader Macros V2 Complete

Readers now compile to native executables:
1. `reader foo(text *u8) *u8 { ... }` declaration triggers compilation
2. Reader body → wrapper program → `.lang-cache/readers/foo`
3. `#foo{content}` runs executable, captures stdout, parses as expression

Key changes:
- Added `exec_capture()` with fork/pipe/execve syscalls
- Added AST-to-source serialization for reader bodies
- Added `parse_expression_from_string()` to parser
- Deleted V1 interpreter builtins (lang_number, lang_add, etc.)

### Include Statement

Added `include "path"` with circular include detection:
- Tracks include stack to prevent infinite loops
- Works in both first pass (declarations) and second pass (codegen)
- Fixed a segfault where second pass wasn't checking for cycles

### Parsing Toolkit

Created stdlib files for building readers:
- **std/tok.lang** - Tokenizer with TOK_NUMBER, TOK_IDENT, TOK_LPAREN, etc.
- **std/emit.lang** - emit_number(), emit_binop(), emit_string(), emit_call()

Reader executables automatically include core.lang, tok.lang, emit.lang.

### Tests

- 80 tests passing
- Tests now run as part of `make verify`
- Added tests for includes, V2 readers

## Bugs Found

Two compiler bugs discovered and documented:

1. **`*(struct.ptr_field)` reads wrong size** - Dereferencing a pointer field from a struct reads 8 bytes instead of 1. Workaround: use temp variable.

2. **>6 function parameters broken** - Stack-based parameters generate malformed assembly. Workaround: pass struct/array.

## Blocking Issue: Reader Includes

Hit a wall trying to write the lisp reader beautifully. The problem:

**Only code inside the `reader foo() { ... }` braces is compiled into the reader executable.**

This means:
- Can't define helper functions outside the reader
- Can't include reader-specific files
- Readers can only use stdlib functions

This defeats the purpose of "full-power readers". A reader should be able to include its own helper files and define recursive parsers.

## Next Steps

1. **Fix reader includes** - Reader compilation should process include statements, or at minimum include all functions from the same file

2. **File extension dispatch** - `lang reader.lang main.lisp` should compile main.lisp using the lisp reader

3. **Parser generator** - First-class functions would enable beautiful parser combinators. This is the killer feature: define grammar → get native parser.

## Reflection

The V2 infrastructure works. The issue is that readers are too constrained - they're compiled in isolation without access to helper code. The beautiful recursive lisp parser we want to write requires either:
- Reader includes (so helper functions can be in separate files)
- First-class functions (so we can pass parsers around)

Both are significant work. Reader includes is probably the smaller change.

The vision remains compelling: trivially create DSLs that compile to x86 with no runtime. We're close but need to fix the reader architecture first.
