# Mac Bootstrap Handoff

Bootstrap the lang compiler on Mac ARM64. Delete after successful setup.

## Quick Start

```bash
# 1. Compile the libc-based bootstrap (macOS version)
clang bootstrap/llvm_libc_macos.ll -o lang

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

`bootstrap/llvm_libc_macos.ll` - LLVM IR that uses libc for OS interface:
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
LANGBE=llvm LANGLIBC=libc ./out/lang std/core.lang src/*.lang -o bootstrap/llvm_libc_macos.ll
```

**getenv returns nil**: The current bootstrap stores envp from main's hidden third parameter. If tests that use `getenv()` fail, the issue is likely in how clang calls main().

**Binary crashes immediately**: Check that you're using `LANGBE=llvm`. The default x86 output won't run on ARM Mac.

---

## BLOCKER: 2024-12-31 Attempt #3 - mmap flags

**Symptom**: mmap returns MAP_FAILED (-1), crash in append_str
```
frame #0: lang`append_str + 68  (writing to 0xffffffffffffffff)
```

**Root cause**: `std/core.lang` hardcodes Linux mmap flags:
```lang
// std/core.lang:18
heap_pos = os_mmap(nil, SIZE_HEAP, 3, 34, 0-1, 0);
//                                    ^^-- Linux MAP_PRIVATE|MAP_ANONYMOUS = 34
```

macOS uses different flag values:
| Flag | Linux | macOS |
|------|-------|-------|
| MAP_PRIVATE | 0x02 | 0x02 |
| MAP_ANONYMOUS | 0x20 | 0x1000 (MAP_ANON) |
| Combined | 34 | 4098 |

**Fix options**:

1. **Define flags in OS layer** - each `std/os/*.lang` exports constants:
   ```lang
   // std/os/libc.lang (or per-platform)
   var MMAP_FLAGS_ANON i64 = 4098;  // macOS value
   ```
   Then std/core.lang uses `MMAP_FLAGS_ANON` instead of hardcoded 34.

2. **Use libc malloc entirely** - when using libc layer, don't implement our own bump allocator. Just use libc's malloc/free everywhere.

---

## Deep Dive: All Platform-Specific Code (2024-12-31)

### Issue 1: mmap flags in std/core.lang (BLOCKING)
```lang
// std/core.lang:18
heap_pos = os_mmap(nil, SIZE_HEAP, 3, 34, 0-1, 0);
//                                    ^^-- Linux only
```
- Linux: MAP_PRIVATE|MAP_ANONYMOUS = 34
- macOS: MAP_PRIVATE|MAP_ANON = 4098

### Issue 2: File open flags (will break file writing)
```lang
// Multiple places use 577 for O_WRONLY|O_CREAT|O_TRUNC
file_open(output_file, 577);
```
- Linux: O_CREAT=64, O_TRUNC=512 → 577
- macOS: O_CREAT=512, O_TRUNC=1024 → 1537

**Affected files:**
- src/main.lang:382, 399
- src/codegen_llvm.lang:29
- src/codegen.lang:1164, 5831
- src/reader_main.lang:126

### Issue 3: Direct syscalls in codegen.lang (reader execution)
The reader macro system uses raw Linux syscalls:
```lang
// codegen.lang - reader subprocess execution
syscall(57);           // fork
syscall(59, ...);      // execve
syscall(61, ...);      // wait4
syscall(22, ...);      // pipe
syscall(33, ...);      // dup2
syscall(2, path, 577, 420);  // open
syscall(0, fd, ...);   // read
syscall(1, fd, ...);   // write
syscall(3, fd);        // close
```

These are **not abstracted** through the OS layer. The libc layer would need:
```lang
extern func fork() i64;
extern func execve(path *u8, argv **u8, envp **u8) i64;
extern func waitpid(pid i64, status *i64, options i64) i64;
extern func pipe(pipefd *i64) i64;
extern func dup2(oldfd i64, newfd i64) i64;
```

### Issue 4: codegen.lang:5831 bypasses OS layer
```lang
cg_out_fd = syscall(2, out_path, 577, 420);
```
Direct syscall instead of using `file_open()`.

### Summary Table

| Issue | Location | Linux Value | macOS Value | Severity |
|-------|----------|-------------|-------------|----------|
| mmap flags | std/core.lang:18 | 34 | 4098 | BLOCKING |
| open flags | multiple | 577 | 1537 | BLOCKING |
| fork syscall | codegen.lang | 57 | N/A (use libc) | Reader macros break |
| execve syscall | codegen.lang | 59 | N/A | Reader macros break |
| wait4 syscall | codegen.lang | 61 | N/A | Reader macros break |
| pipe syscall | codegen.lang | 22 | N/A | Reader macros break |
| dup2 syscall | codegen.lang | 33 | N/A | Reader macros break |

### Recommended Fix Strategy

1. **Define constants in OS layer**:
   ```lang
   // std/os/libc.lang
   var OPEN_FLAGS_WRITE_CREATE_TRUNC i64 = 1537;  // macOS
   var MMAP_FLAGS_ANON i64 = 4098;                // macOS
   ```

2. **Add process functions to OS layer**:
   ```lang
   extern func fork() i64;
   extern func execve(path *u8, argv **u8, envp **u8) i64;
   extern func waitpid(pid i64, status *i64, options i64) i64;
   extern func pipe(pipefd *i64) i64;
   extern func dup2(oldfd i64, newfd i64) i64;

   func os_fork() i64 { return fork(); }
   func os_exec(...) i64 { return execve(...); }
   // etc.
   ```

3. **Update codegen.lang** to use OS layer functions instead of direct syscalls.

4. **Alternative**: For libc bootstrap, just use libc malloc everywhere and skip our custom allocator.
