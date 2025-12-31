# Mac Bootstrap Handoff

Bootstrap the lang compiler on Mac ARM64. Delete after successful setup.

## Quick Start

```bash
# 1. Compile the libc-based bootstrap
clang bootstrap/llvm_libc_compiler.ll -o lang

# 2. Verify it works
./lang test/suite/002_return_42.lang -o test.s
echo "Wrote test.s: OK"

# 3. Test LLVM backend (produces runnable Mac binary)
LANGBE=llvm ./lang std/core.lang test/suite/002_return_42.lang -o test.ll
clang test.ll -o test
./test; echo "Exit: $?"
# Expected: Exit: 42

# 4. Full self-host
LANGBE=llvm ./lang std/core.lang src/lexer.lang src/parser.lang \
    src/codegen.lang src/codegen_llvm.lang src/ast_emit.lang \
    src/sexpr_reader.lang src/main.lang -o compiler.ll
clang compiler.ll -o lang_v2

# 5. Verify self-hosted compiler
LANGBE=llvm ./lang_v2 std/core.lang test/suite/002_return_42.lang -o test2.ll
clang test2.ll -o test2
./test2; echo "Exit: $?"
# Expected: Exit: 42
```

## What's in the Bootstrap

`bootstrap/llvm_libc_compiler.ll` - LLVM IR that uses libc for OS interface:
- Uses `read()`, `write()`, `open()`, `close()` from libc
- Uses `malloc()`, `free()` from libc
- Uses `getenv()` from our stdlib (reads from envp passed to main)
- Portable across Linux/Mac since libc abstracts OS differences

## Expected Behavior

| Command | Result |
|---------|--------|
| `./lang file.lang -o out.s` | Writes x86-64 assembly (won't run on Mac) |
| `LANGBE=llvm ./lang file.lang -o out.ll` | Writes LLVM IR (compile with clang) |

The x86 backend outputs Linux x86-64 assembly. Use `LANGBE=llvm` for Mac-runnable binaries.

## Test Suite

```bash
# Run LLVM test suite (should pass 165/165)
COMPILER=./lang ./test/run_llvm_suite.sh
```

## Troubleshooting

**clang errors about malloc/free redefinition**: The bootstrap should only have `declare` (not `define`) for libc functions. If you see conflicts, regenerate on the dev machine:
```bash
LANGBE=llvm LANGLIBC=libc ./out/lang std/core.lang src/*.lang -o bootstrap/llvm_libc_compiler.ll
```

**getenv returns nil**: The current bootstrap stores envp from main's hidden third parameter. If tests that use `getenv()` fail, the issue is likely in how clang calls main().

**Binary crashes immediately**: Check that you're using `LANGBE=llvm`. The default x86 output won't run on ARM Mac.

---

## BLOCKER: 2024-12-31 Attempt #2

**Symptom**: Segfault in malloc during startup
```
frame #0: lang`malloc + 908
frame #1: lang`vec_new + 28
frame #2: lang`main + 200
```

**Root cause**: `os_mmap` still calls Linux syscall, not libc:
```llvm
; Current (BROKEN on Mac):
define i8* @os_mmap(...) {
    %result = call i64 @syscall(i64 9, ...)  ; <-- Linux syscall number!
}
```

The bootstrap declares `@syscall` as extern but macOS doesn't have a `syscall()` function that works like Linux's.

**Fix needed in `std/os/libc.lang`**:
```lang
// Add extern declarations for libc functions:
extern func mmap(addr *u8, len i64, prot i64, flags i64, fd i64, offset i64) *u8;

// Then os_mmap should call libc's mmap, not syscall:
func os_mmap(addr i64, len i64, prot i64, flags i64, fd i64, offset i64) *u8 {
    return mmap(addr, len, prot, flags, fd, offset);
}
```

**All os_* functions need this treatment** - they should call libc wrappers, not raw syscall.
