# Code Review: Language Compiler

**Date**: 2025-12-26
**Reviewer**: Claude (Deep line-by-line review)

## Executive Summary

The compiler is in good shape overall - self-hosting works, all 81 tests pass, and the reader macro system is impressive. However, there are several issues ranging from bugs to documentation gaps that should be addressed before moving forward.

## Critical Issues

### 1. ~~`vec_new()` Ignores Capacity Argument (BUG)~~ FIXED

**Status**: FIXED - `vec_new(cap i64)` now accepts and uses capacity parameter.

**Files changed**:
- std/core.lang - Added `cap` parameter to `vec_new(cap i64)`
- src/parser.lang - Updated calls to `vec_new(8)`
- test/vec_test.lang - Updated calls to `vec_new(8)`
- test/emit_test.lang - Updated call to `vec_new(4)`
- LANG.md - Updated documentation

---

### 2. Language Limitation: `*(struct.ptr_field)` Is Buggy

**Files**: std/tok.lang
**Severity**: Low (documented workaround exists)

Multiple comments document this:
```lang
// std/tok.lang:101-102
// Workaround: *(struct.ptr_field) is buggy, use temp variable
var inp *u8 = t.input;
return *(inp + t.pos);
```

**Impact**: Can't directly write `*(t.input + t.pos)` - must use temp variable.

**Fix**: This is a language limitation that should be tracked in TODO.md or fixed in the parser/codegen.

---

## Code Quality Issues

### 3. Fixed 4KB Stack Frame

**File**: src/codegen.lang:2074-2077
**Severity**: Low (wastes stack space but safe)

```lang
// SAFETY: Use 4KB stack frame to avoid silent overflow corruption
// The compiler itself has functions with 50+ local variables (gen_expr)
// TODO: calculate actual size from cg_stack_size after generating body
emit_line("    sub $4096, %rsp");
```

All functions allocate 4KB regardless of actual local variable usage. This is safe but wasteful.

**Fix**: Calculate actual stack size after generating the function body and patch it in.

---

### 4. Magic Numbers in Generated Code

**File**: std/rdgen.lang:108
**Severity**: Low (works but hard to understand)

```lang
rdgen_line(rd, "    var n *PNode = pnode_new(4);");  // PNODE_LIST = 4
```

Generated code uses magic numbers instead of symbolic constants.

**Fix**: Generate code that uses `PNODE_LIST` constant instead of `4`.

---

### 5. Duplicated Operator Mapping

**Files**: src/codegen.lang, std/rdgen.lang
**Severity**: Low (maintenance burden)

Token-to-symbol mappings exist in multiple places:
- `src/codegen.lang:3097-3110` - print_expr_ast
- `src/codegen.lang:2811-2823` - ast_to_string_expr
- `std/rdgen.lang:166-181` - literal token matching

Any changes to operators require updates in multiple places.

---

## Documentation Gaps

### 6. ~~`#parser{}` Reader Undocumented (CRITICAL)~~ FIXED

**Status**: FIXED - Comprehensive documentation added to std/parser_reader.lang

**Documentation now includes**:
- Quick start example
- Complete grammar syntax reference
- All supported literals and token types
- Generated code structure (PNode struct, helper functions)
- PNode kind constants
- AST structure examples
- Pattern for building readers with #parser{}
- Dependency information

---

### 7. Missing Type Annotations on Return Statements

**Files**: Various
**Severity**: Low

Some functions that return void don't have explicit return type:
```lang
func free(ptr *u8) {  // Missing `: void` or return type
```

Not a bug, but inconsistent style.

---

## Potential Future Issues

### 8. No Argument Count Checking

**Severity**: Medium

The language allows calling functions with wrong number of arguments:
- `vec_new(8)` when signature is `vec_new()`
- Extra arguments silently pushed to stack and ignored

This is how the vec_new bug went unnoticed. Should add compile-time check.

---

### 9. Reader Cache Not Invalidated

**File**: src/codegen.lang (compile_reader_to_executable)
**Severity**: Low

Reader executables in `.lang-cache/readers/` are not rebuilt when source changes. Must manually delete cache.

---

## Good Patterns Worth Noting

1. **Stack-based Expression Generator** (std/rdgen.lang:122-452): Avoids mutual recursion by using explicit work stack - elegant solution.

2. **AST Serialization** (src/codegen.lang:2748-2975): Clean separation between AST walking and string building.

3. **Reader Architecture** (std/parser_reader.lang): Readers building readers is beautiful - #lisp uses #parser, all compile to native.

---

## Recommended Priority

1. **Fix vec_new() bug** - Silent bug, easy fix
2. **Document #parser{}** - Critical for users
3. **Track *(struct.ptr) bug** - Language limitation to fix eventually
4. **Add argument count checking** - Prevents future bugs

---

## Files Reviewed

| File | Lines | Issues |
|------|-------|--------|
| src/codegen.lang | ~3500 | Stack frame size, operator duplication |
| src/parser.lang | ~2000 | Clean, well-structured |
| src/lexer.lang | ~500 | Clean |
| std/core.lang | ~640 | vec_new signature |
| std/tok.lang | ~345 | Workaround comments |
| std/emit.lang | ~198 | Clean |
| std/grammar.lang | ~317 | vec_new call bug |
| std/rdgen.lang | ~492 | vec_new call bug, magic numbers |
| std/parser_reader.lang | 31 | Needs docs |
| example/lisp/lisp.lang | ~130 | Well documented |

**Total**: ~8000+ lines reviewed
