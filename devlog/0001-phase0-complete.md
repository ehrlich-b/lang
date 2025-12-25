# 0001: Phase 0 Complete

**Date:** December 2024

## What Happened

Built the entire Phase 0 bootstrap compiler in Go. It's working.

### Components Built
- **Lexer** (`boot/lexer.go`, `boot/token.go`) - Tokenizes the language, handles comments, strings with escapes, all operators
- **Parser** (`boot/parser.go`, `boot/ast.go`) - Recursive descent with precedence climbing for expressions
- **Codegen** (`boot/codegen.go`) - Emits x86-64 assembly for Linux, System V ABI

### Test Suite
Created 67 comprehensive tests covering:
- Return values, arithmetic, comparisons
- Logical operators with short-circuit evaluation
- Variables, if/else, while loops
- Functions (up to 6 args, recursion, fibonacci)
- Pointers (address-of, dereference, swap pattern)
- Edge cases

All pass: `make test-all`

### Standard Library (std/core.lang)
- `alloc()` - bump allocator using mmap (never frees, who cares)
- `print`, `println`, `eprint`, `eprintln` - I/O
- `print_int` - prints integers (handles negatives)
- `strlen`, `streq` - string basics
- `file_open`, `file_read`, `file_write`, `file_close` - file I/O
- `exit` - exit program

### Bug Fixes Along the Way
1. **Type assertion panic** - `f.RetType.(*BaseType).Name` crashed on pointer return types. Fixed with `isVoidType()` helper.
2. **Strings not null-terminated** - strlen was reading garbage. Fixed `formatAscii` to add `\000`.
3. **Wrong pointer dereference size** - `mov (%rax), %rax` loads 8 bytes but `*u8` should load 1 byte. Added full type tracking to codegen with `LocalVar` struct, `getExprType()`, type-aware dereference using `movzbl`/`movzwl`/etc.

## What's Missing (Intentionally)
- Structs (parsed but codegen not implemented)
- Arrays (use pointer arithmetic)
- For loops, break/continue
- Any form of garbage collection

## Thoughts

The language is genuinely usable for systems programming. Pointer arithmetic works, type-aware dereference works, syscalls work. Could write a real program in this.

The codegen is messy - lots of push/pop shuffling, no register allocation. But it works and that's all that matters for bootstrap.

Next: Phase 1 - rewrite this compiler in the language itself. Started sketching out the lexer before this devlog entry. Main challenge will be no structs - need manual memory layout with pointer offsets.

## Files Created
```
boot/token.go, boot/lexer.go, boot/ast.go, boot/parser.go, boot/codegen.go, boot/main.go
std/core.lang
test/suite/*.lang (67 tests)
test/run_suite.sh
Makefile
LANG.md (living language reference)
editor/vscode/* (syntax highlighting)
```
