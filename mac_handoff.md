# Mac Development Handoff

Temporary doc for bootstrapping on Mac. Delete after successful setup.

## Status: BLOCKED - Needs Windows Fix

**Attempted**: 2024-12-31 on ARM64 Mac (macOS 15.6.1, Apple clang 17.0.0)

**Result**: Bootstrap failed due to symbol conflict in `llvm_libc_compiler.ll`

---

## The Problem: malloc Symbol Conflict

When compiling `bootstrap/llvm_libc_compiler.ll` with clang:

```bash
$ clang -target arm64-apple-macos bootstrap/llvm_libc_compiler.ll -o lang
bootstrap/llvm_libc_compiler.ll:271:12: error: invalid redefinition of function 'malloc'
  271 | define i8* @malloc(i64 %size.arg) {
      |            ^
1 error generated.
```

**Root cause**: The file contains BOTH:
- Line 48: `declare i8* @malloc(i64)` — extern declaration (from `std/os/libc.lang`)
- Line 271: `define i8* @malloc(i64 %size.arg) {` — internal implementation (from `std/core.lang`)

This is invalid LLVM IR. You can't both declare something as external AND define it.

**How this happened**: When generating the libc bootstrap, both files were included:
- `std/os/libc.lang` declares `extern func malloc(size i64) *u8;`
- `std/core.lang` defines `func malloc(size i64) *u8 { ... }`

The LLVM backend faithfully emitted both, creating the conflict.

---

## Fix Required on Windows

### Option A: Rename Internal Allocator (Recommended)

In `std/core.lang`, rename `malloc` to `lang_malloc` (and `free` to `lang_free`):

```lang
// Before
func malloc(size i64) *u8 { ... }
func free(ptr *u8) void { ... }

// After
func lang_malloc(size i64) *u8 { ... }
func lang_free(ptr *u8) void { ... }
```

Then update all callers in the compiler to use `lang_malloc`/`lang_free`.

This keeps the internal allocator separate from libc's malloc.

### Option B: Conditional Compilation

Add a flag or detection so that when `LANGLIBC=libc`, the internal malloc/free are NOT defined, and instead the extern declarations are used.

### Option C: Don't Include std/core.lang for libc Bootstrap

Generate the bootstrap without `std/core.lang`, relying entirely on libc for allocation. This might break things that depend on the bump allocator semantics.

---

## Why Other Bootstrap Files Won't Work

### `bootstrap/8a0e999/llvm/compiler.ll` (syscall-based)

This file uses raw Linux syscalls:
```llvm
declare i64 @syscall(i64, ...)

define i64 @os_read(...) {
  %result = call i64 (i64, ...) @syscall(i64 0, ...)  ; SYS_read = 0
  ...
}
```

**Why it fails on Mac:**

1. **No `syscall()` function**: macOS doesn't expose a generic `syscall()` function in the same way. Linux's glibc provides it, but macOS's libSystem doesn't export it for general use.

2. **Different syscall numbers**: Even if we could call syscalls, the numbers are completely different:
   | Syscall | Linux x86_64 | macOS ARM64 |
   |---------|--------------|-------------|
   | read    | 0            | 0x2000003   |
   | write   | 1            | 0x2000004   |
   | open    | 2            | 0x2000005   |
   | mmap    | 9            | 0x20000C5   |
   | exit    | 60           | 0x2000001   |

3. **Different calling convention**: macOS ARM64 uses different registers for syscall arguments than Linux x86_64.

### `bootstrap/current/compiler.s` (x86 assembly)

This is x86-64 Linux assembly with hardcoded Linux syscalls:
```asm
movq $1, %rax    # SYS_write on Linux
syscall
```

**Why it fails on Mac:**

1. **Wrong architecture**: It's x86-64, Mac is ARM64. Even with Rosetta 2, the syscall interface is translated to macOS syscalls, not Linux.

2. **Wrong syscall ABI**: Linux uses `syscall` instruction, macOS x86-64 uses `syscall` but with different numbers, macOS ARM64 uses `svc #0x80`.

3. **No assembler compatibility**: The assembly syntax may have Linux-specific directives.

---

## Fallback: Docker Bootstrap

If the Windows fix isn't possible, we can bootstrap via Docker on Mac:

```bash
# 1. Run Linux container
docker run -it --rm -v $(pwd):/lang -w /lang ubuntu:22.04 bash

# Inside container:
apt-get update && apt-get install -y build-essential

# 2. Assemble the x86 bootstrap
as bootstrap/current/compiler.s -o compiler.o
ld compiler.o -o lang_linux

# 3. Generate clean LLVM IR using the Linux compiler
LANGBE=llvm ./lang_linux [sources...] -o clean_bootstrap.ll

# 4. Exit container, use the .ll file on Mac
exit

# On Mac:
clang clean_bootstrap.ll -o lang_mac
```

This works because:
- Docker provides a real Linux environment with proper syscall support
- The Linux compiler can generate LLVM IR
- LLVM IR is portable and can be compiled by Mac's clang

---

## What Would Work (Once Fixed)

The libc-based approach IS the right idea. Once the malloc conflict is fixed:

```bash
# This SHOULD work:
clang -target arm64-apple-macos bootstrap/llvm_libc_compiler.ll -o lang

# Then we can bootstrap natively:
LANGBE=llvm ./lang [sources...] -o compiler.ll
clang compiler.ll -o lang_native
```

The libc approach abstracts away all the OS differences:
- `read()`, `write()`, `open()`, `close()` — same API everywhere
- `malloc()`, `free()` — same API everywhere
- `mmap()` — libc handles the flag differences
- Entry point — clang provides `_start` → `main` linkage

---

## Quick Reference: What's in Each Bootstrap File

| File | Type | OS Interface | Mac Compatible? |
|------|------|--------------|-----------------|
| `llvm_libc_compiler.ll` | LLVM IR | libc externs | **BLOCKED** (malloc conflict) |
| `8a0e999/llvm/compiler.ll` | LLVM IR | raw syscalls | No (no syscall function) |
| `current/compiler.s` | x86 asm | raw syscalls | No (wrong arch + syscalls) |

---

## Verification Steps After Fix

Once a working bootstrap is generated on Windows:

```bash
# 1. Compile bootstrap
clang -target arm64-apple-macos bootstrap/llvm_libc_compiler.ll -o lang
# Expected: Success, no errors

# 2. Test it runs
./lang --help 2>&1 | head -5
# Expected: Usage info or similar

# 3. Test x86 backend (output only, won't run)
./lang test/suite/002_return_42.lang -o test.s
# Expected: "Wrote test.s"

# 4. Test LLVM backend (should produce runnable binary)
LANGBE=llvm ./lang test/suite/002_return_42.lang -o test.ll
clang test.ll -o test
./test; echo "Exit: $?"
# Expected: Exit: 42

# 5. Full self-hosting
LANGBE=llvm ./lang std/core.lang src/*.lang -o compiler.ll
clang compiler.ll -o lang_v2
LANGBE=llvm ./lang_v2 test/suite/002_return_42.lang -o test2.ll
clang test2.ll -o test2
./test2; echo "Exit: $?"
# Expected: Exit: 42
```

---

## Environment Info (Mac)

```
Platform: darwin arm64
OS: macOS 15.6.1 (Darwin 24.6.0)
Clang: Apple clang 17.0.0 (clang-1700.0.13.5)
Target: arm64-apple-darwin24.6.0
Docker: Available (27.5.1) — fallback option
```
