# Multi-Backend Kernel Design

**Status**: Design
**Goal**: Cross-platform compiler (not just x86 generator)

## Current State

```
AST → kernel → x86 assembly → as → native binary
```

Single target, single toolchain. Works on Linux x86_64.

## The Question

Should the architecture be:

**A) Many direct backends**
```
        ┌→ x86 asm  → as     → Linux binary
AST → kernel ─┼→ ARM asm  → as     → Mac binary
        ├→ WASM     → (browser interprets)
        └→ LLVM IR  → clang  → any native
```

**B) LLVM as universal backend**
```
AST → kernel → LLVM IR → clang/llc → {x86, ARM, WASM, RISC-V, ...}
```

## Comparative Analysis

### Option A: Direct Backends

| Backend | Effort | Value | Dependencies |
|---------|--------|-------|--------------|
| x86 asm | Done | High (current) | `as`, `ld` (ubiquitous) |
| ARM asm | Medium | Medium | `as` (Xcode CLT) |
| WASM | Medium | High (browser) | None (browser native) |
| LLVM IR | Medium | High (portability) | `clang` or `llc` |

**Pros:**
- Educational (we understand every instruction)
- Fast compilation (no LLVM overhead)
- Minimal dependencies (just assembler/linker)
- Full control over output

**Cons:**
- Each backend is ~2000 LOC
- No optimizations
- Platform-specific bugs multiply

### Option B: LLVM-Only

| Aspect | Assessment |
|--------|------------|
| Effort | One backend (~2000 LOC) |
| Targets | All LLVM targets (x86, ARM, WASM, RISC-V, ...) |
| Optimization | -O2 comes free |
| Dependencies | LLVM/Clang (~500MB) |

**Pros:**
- One backend → many targets
- World-class optimizations
- Battle-tested codegen
- WASM via `--target=wasm32`

**Cons:**
- Huge dependency
- Compile time overhead
- Less educational
- "Magic" we don't control

## The Honest Assessment

### ARM Direct: Is It Worth It?

**Effort**: ARM64 codegen is ~90% similar to x86_64:
- Same register calling convention style
- Similar instruction patterns
- Different register names, syntax

Estimate: 1-2 days to port x86 backend to ARM.

**Value**: Native Mac binaries without LLVM.

**Verdict**: Low effort, moderate value. Worth doing if we want Mac support without LLVM dependency.

### WASM Direct: Is It Worth It?

**Effort**: WASM is a stack machine, fundamentally different:
- No registers (stack-based)
- Different memory model
- Different function call ABI

Estimate: 1-2 weeks, significant restructuring.

**Value**: High - browser deployment, sandboxed execution.

**Verdict**: Medium effort, high value. But LLVM also outputs WASM...

### LLVM IR: The Pragmatic Choice?

**Effort**: LLVM IR is well-documented, straightforward:
- SSA form (we already think in SSA-ish patterns)
- Text format (just emit strings like we do for asm)
- One backend serves all targets

Estimate: 1 week for basic LLVM IR output.

**Value**: Extremely high - all platforms, optimizations, WASM.

**Verdict**: This is probably the "smart" engineering choice.

## Recommended Architecture

**Hybrid approach**: Keep direct backends for education/speed, add LLVM for production.

```
        ┌→ x86 asm  → as     → Linux binary (fast, educational)
AST → kernel ─┼→ LLVM IR  → clang  → {anything} (portable, optimized)
        └→ WASM     → (direct) → browser (no deps)
```

### Phase 1: Add LLVM IR Backend (recommended first)
- One backend → immediate Mac/Windows/WASM support
- Text output like current x86 (just different syntax)
- Use `clang` to compile (already on most systems)

### Phase 2: Direct WASM (optional)
- Browser deployment without toolchain
- Educational value (stack machine is different)
- Skip if LLVM WASM output is sufficient

### Phase 3: Direct ARM (optional)
- Native Mac without LLVM
- Mostly a port of x86 backend
- Skip if LLVM is acceptable

## Toolchain Dependencies

| Target | Direct Backend | LLVM Backend |
|--------|---------------|--------------|
| Linux x86 | `as`, `ld` | `clang` |
| Mac ARM | `as` (Xcode) | `clang` (Xcode) |
| Windows | MinGW `as` | `clang` |
| WASM | None | `clang --target=wasm32` |
| RISC-V | N/A | `clang --target=riscv64` |

Note: Mac requires Xcode Command Line Tools regardless (for `as`, `ld`, or `clang`).

## Implementation Sketch

### LLVM IR Backend

```
; Current x86 output:
main:
    pushq %rbp
    movq %rsp, %rbp
    movl $42, %eax
    popq %rbp
    ret

; Equivalent LLVM IR:
define i64 @main() {
    ret i64 42
}
```

The kernel already walks AST and emits text. LLVM IR is just different text:
- `movq` → `store`
- `addq` → `add`
- Labels → basic blocks
- Stack slots → `alloca`

### Backend Selection

```bash
# Current (x86 default)
./out/lang program.lang -o program.s

# With backend flag
./out/lang program.lang -o program.ll --backend=llvm
./out/lang program.lang -o program.wasm --backend=wasm

# Or infer from extension
./out/lang program.lang -o program.ll    # → LLVM
./out/lang program.lang -o program.wasm  # → WASM
./out/lang program.lang -o program.s     # → x86 (default)
```

## Decision Matrix

| If you want... | Use... |
|----------------|--------|
| Fast iteration, understanding codegen | Direct x86 |
| Mac support today | LLVM IR → clang |
| Browser deployment | LLVM IR → wasm32 (or direct WASM later) |
| Maximum portability | LLVM IR |
| Minimal dependencies | Direct backends |
| Best optimization | LLVM IR with -O2 |

## Recommendation

1. **Keep x86 direct backend** - It works, it's educational, it's fast
2. **Add LLVM IR backend next** - Maximum leverage for effort
3. **Direct WASM later if needed** - Only if LLVM WASM isn't good enough
4. **Direct ARM optional** - Nice to have, low effort, but LLVM covers it

The kernel's job is "AST → runnable code". LLVM IR is "runnable code" in the sense that every platform has clang. Direct x86 remains valuable for:
- Fast edit-compile-run cycle (no LLVM overhead)
- Educational purposes (we know every instruction)
- Environments without LLVM

## Cross-Platform Syscalls

**Critical Issue**: The stdlib uses Linux x86_64 syscall numbers directly. These differ across platforms.

### Current Syscall Usage

**std/core.lang** (essential):
| Function | Syscall | Linux x86_64 | Linux ARM64 | macOS |
|----------|---------|--------------|-------------|-------|
| read | 0 | 0 | 63 | 0x2000003 |
| write | 1 | 1 | 64 | 0x2000004 |
| open | 2 | 2 | 56 (openat) | 0x2000005 |
| close | 3 | 3 | 57 | 0x2000006 |
| mmap | 9 | 9 | 222 | 0x20000C5 |
| exit | 60 | 60 | 93 | 0x2000001 |

**std/os.lang** (extended):
| Function | Syscall | Linux x86_64 | Linux ARM64 | macOS |
|----------|---------|--------------|-------------|-------|
| stat | 4 | 4 | 79 (fstatat) | 0x2000152 |
| getpid | 39 | 39 | 172 | 0x2000014 |
| getcwd | 79 | 79 | 17 | - |
| mkdir | 83 | 83 | 34 (mkdirat) | 0x2000088 |
| rmdir | 84 | 84 | 35 (unlinkat) | 0x2000089 |
| unlink | 87 | 87 | 35 (unlinkat) | 0x200000A |
| getppid | 110 | 110 | 173 | 0x2000027 |

**Note**: Linux ARM64 uses *at variants (openat, mkdirat) - no direct equivalents.
**Note**: macOS uses BSD numbers with 0x2000000 class prefix.
**Note**: Windows has NO stable syscall interface - must use DLL functions.

### The libc Question

Same stance as LLVM: **both options should exist**.

| Approach | Analogy | Pros | Cons |
|----------|---------|------|------|
| Raw syscalls | Direct x86 backend | No deps, educational, full control | Platform-specific |
| System libc | LLVM backend | Portable, battle-tested | External dependency |

"libc written in lang" = our syscall wrappers (linux_x86_64.lang, etc.)
"Bring your own libc" = extern declarations that link against musl/glibc

### Solution: OS Abstraction Layer

```
std/
├── core.lang              # High-level: print, alloc (uses os_*)
├── os.lang                # → GENERATED or SELECTED (see below)
└── os/
    ├── linux_x86_64.lang  # Raw syscalls for Linux x86_64
    ├── linux_arm64.lang   # Raw syscalls for Linux ARM64
    ├── macos_arm64.lang   # Raw syscalls for macOS ARM64
    └── libc.lang          # extern declarations, links -lc
```

### How Include Selection Works (The Mechanical Question)

We don't have conditional compilation or dynamic includes. So how does `std/core.lang` know which OS implementation to use?

**Option 1: Generated std/os.lang (Build System)**

The Makefile generates `std/os.lang` based on target before compilation:

```bash
# In Makefile
build-linux-x86_64:
    echo 'include "std/os/linux_x86_64.lang"' > std/os.lang
    ./out/lang program.lang -o program.s

build-with-libc:
    echo 'include "std/os/libc.lang"' > std/os.lang
    ./out/lang program.lang -o program.s
```

Then `std/core.lang` just does:
```lang
include "std/os.lang"  // Gets the generated file
```

**Pros**: Simple, no compiler changes, works today
**Cons**: std/os.lang is gitignored/generated artifact, slightly ugly

**Option 2: Compiler Flag Overrides Include Path**

The compiler has `--os=<impl>` that redirects includes:

```bash
./out/lang --os=linux-x86_64 program.lang  # include "std/os.lang" → "std/os/linux_x86_64.lang"
./out/lang --os=libc program.lang          # include "std/os.lang" → "std/os/libc.lang"
```

Implementation in compiler:
```lang
func resolve_include(path *u8) *u8 {
    if streq(path, "std/os.lang") && os_override != nil {
        return str_concat("std/os/", os_override);
    }
    return path;
}
```

**Pros**: Clean, explicit, no generated files
**Cons**: Requires compiler modification

**Option 3: Conditional Compilation (#if)**

Add `#if` to the language:
```lang
// std/os.lang
#if TARGET == "linux-x86_64" {
    include "std/os/linux_x86_64.lang"
}
#if TARGET == "libc" {
    include "std/os/libc.lang"
}
```

**Pros**: General solution, useful beyond OS layer
**Cons**: New language feature, more complex

**Option 4: Reader Macro for Target Selection**

Since we have reader macros, add a `#target{}` reader:
```lang
#target{
    linux-x86_64: include "std/os/linux_x86_64.lang",
    linux-arm64:  include "std/os/linux_arm64.lang",
    libc:         include "std/os/libc.lang"
}
```

**Pros**: Uses existing infrastructure, declarative
**Cons**: Reader macro complexity, still needs compiler to set target variable

**Recommendation: Option 1 (Generated) for Now, Option 2 Later**

Phase 1: Use generated `std/os.lang` - works immediately, no compiler changes
Phase 2: Add `--os=` flag to compiler for cleaner UX

The generated file approach is how many real build systems work (autoconf generates config.h, CMake generates headers, etc.). It's pragmatic.

### The Full Picture

```
┌─────────────────────────────────────────────────────────────────┐
│ User Program                                                     │
│   include "std/core.lang"                                       │
│     └─> include "std/os.lang"  ← SELECTED BY BUILD/COMPILER     │
│           └─> std/os/linux_x86_64.lang  (raw syscalls)          │
│               OR std/os/libc.lang       (extern to libc)        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Compiler (--backend, --os flags)                                │
│   --backend=x86     → emit x86 assembly                         │
│   --backend=llvm    → emit LLVM IR                              │
│   --os=linux-x86_64 → raw syscalls                              │
│   --os=libc         → link against system libc                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Assembler/Linker                                                │
│   as + ld           (for x86 backend)                           │
│   clang             (for LLVM backend, handles linking)         │
│   -lc               (if --os=libc, link against libc)           │
└─────────────────────────────────────────────────────────────────┘
```

### Valid Combinations

| Backend | OS Layer | Linker | Result |
|---------|----------|--------|--------|
| x86 | linux-x86_64 | as + ld | Static Linux binary, no deps |
| x86 | libc | as + ld -lc | Linux binary, needs libc |
| llvm | libc | clang | Portable binary for any clang target |
| llvm | linux-x86_64 | clang | ⚠️ Unusual - raw syscalls in LLVM IR |

Note: LLVM + raw syscalls is technically possible but odd - if you're using LLVM you probably want portability, which means libc.

### Abstract Syscall Interface

```lang
// These functions are implemented per-platform:

func os_read(fd i64, buf *u8, count i64) i64;
func os_write(fd i64, buf *u8, count i64) i64;
func os_open(path *u8, flags i64, mode i64) i64;
func os_close(fd i64) i64;
func os_mmap(addr *u8, len i64, prot i64, flags i64, fd i64, offset i64) *u8;
func os_exit(code i64) void;

// Extended (optional)
func os_stat(path *u8, buf *u8) i64;
func os_getpid() i64;
func os_getcwd(buf *u8, size i64) i64;
func os_mkdir(path *u8, mode i64) i64;
func os_unlink(path *u8) i64;
```

### Platform Implementations

**Linux x86_64** (std/os/linux_x86_64.lang):
```lang
func os_write(fd i64, buf *u8, count i64) i64 {
    return syscall(1, fd, buf, count);  // syscall 1 = write
}
func os_exit(code i64) void {
    syscall(60, code);  // syscall 60 = exit
}
```

**Linux ARM64** (std/os/linux_arm64.lang):
```lang
func os_write(fd i64, buf *u8, count i64) i64 {
    return syscall(64, fd, buf, count);  // syscall 64 = write
}
func os_exit(code i64) void {
    syscall(93, code);  // syscall 93 = exit
}
```

**libc-based** (std/os/libc.lang):
```lang
// External declarations - LLVM backend emits these as external calls
extern func write(fd i32, buf *u8, count i64) i64;
extern func read(fd i32, buf *u8, count i64) i64;
extern func mmap(addr *u8, len i64, prot i32, flags i32, fd i32, off i64) *u8;
extern func exit(code i32) void;

func os_write(fd i64, buf *u8, count i64) i64 {
    return write(fd, buf, count);
}
func os_exit(code i64) void {
    exit(code);
}
```

### Backend ↔ OS Layer Relationship

| Backend | Default OS Layer | Reason |
|---------|------------------|--------|
| x86 asm | linux_x86_64.lang | Direct syscalls, no libc |
| ARM asm | linux_arm64.lang or macos.lang | Direct syscalls |
| LLVM IR | libc.lang | Portable, links against libc |
| WASM | libc.lang or custom | Browser has no syscalls |

### Target Selection

```bash
# Current (implicit Linux x86_64)
./out/lang program.lang -o program.s

# Explicit target selection
./out/lang program.lang -o program.s --target=linux-x86_64
./out/lang program.lang -o program.ll --target=linux-arm64
./out/lang program.lang -o program.ll --target=macos-arm64
./out/lang program.lang -o program.ll --target=wasm32
```

The `--target` flag:
1. Selects the correct OS layer (syscall implementation)
2. Selects the backend (asm vs LLVM IR)
3. Sets architecture-specific codegen options

### Migration Path

**Phase 1: Create OS abstraction**
1. Create `std/os/linux_x86_64.lang` with `os_*` functions
2. Update `std/core.lang` to use `os_*` instead of `syscall()` directly
3. Verify fixed point still works

**Phase 2: Add LLVM backend + libc layer**
1. Create `std/os/libc.lang` with extern declarations
2. Implement LLVM IR backend in codegen
3. Test: compile program with LLVM backend, link with clang

**Phase 3: Add more targets**
- linux_arm64.lang
- macos.lang
- wasm.lang (special - no filesystem, different memory model)

### Memory Allocation

Memory allocation has platform-specific considerations too:

**Current implementation** (std/core.lang):
```lang
func alloc(size i64) *u8 {
    if heap_pos == nil {
        // mmap syscall - Linux x86_64 specific!
        heap_pos = syscall(9, 0, SIZE_HEAP, 3, 34, 0-1, 0);
        heap_end = heap_pos + SIZE_HEAP;
    }
    var ptr *u8 = heap_pos;
    heap_pos = heap_pos + size;
    return ptr;
}
```

**Problem**: mmap flags differ across platforms:
- Linux: `MAP_PRIVATE|MAP_ANONYMOUS` = 34
- macOS: `MAP_PRIVATE|MAP_ANON` = 0x1002
- Windows: No mmap (use VirtualAlloc)
- WASM: No mmap (use memory.grow)

**Solution**: Two approaches depending on backend:

**Direct backends** (x86, ARM):
```lang
func alloc(size i64) *u8 {
    if heap_pos == nil {
        heap_pos = os_mmap(nil, SIZE_HEAP, PROT_RW, MAP_ANON, -1, 0);
        heap_end = heap_pos + SIZE_HEAP;
    }
    // ... bump allocator
}
```
Where `os_mmap` is implemented per-platform with correct flags.

**libc backend** (LLVM):
```lang
// Just use libc malloc directly
extern func malloc(size i64) *u8;
extern func free(ptr *u8) void;

func alloc(size i64) *u8 {
    return malloc(size);  // Let libc handle it
}
```

**WASM backend**:
```lang
// Use WASM linear memory
var wasm_heap_ptr i32 = 0;  // Offset into linear memory

func alloc(size i64) *u8 {
    var ptr i32 = wasm_heap_ptr;
    wasm_heap_ptr = wasm_heap_ptr + size;
    // Grow memory if needed
    if wasm_heap_ptr > memory_size() {
        memory_grow(1);  // Add 64KB page
    }
    return ptr;
}
```

**Allocation Strategy Summary**:
| Backend | Strategy | Implementation |
|---------|----------|----------------|
| x86 asm | os_mmap + bump | linux_x86_64.lang |
| LLVM IR | libc malloc | libc.lang |
| WASM | linear memory + bump | wasm.lang |

This means `std/core.lang` needs to be backend-aware OR we split it:
- `std/core.lang` - pure lang (no syscalls), uses os_* functions
- `std/os/*.lang` - platform-specific implementations

### WASM Considerations

WebAssembly is special:
- No filesystem (unless using WASI)
- Memory is a flat array, no mmap
- No process exit (just return from main)
- I/O through imports (JavaScript provides implementations)

```lang
// std/os/wasm.lang
// Memory: WASM linear memory, bump allocator works
func os_mmap(addr *u8, len i64, ...) *u8 {
    // WASM: use memory.grow or pre-allocated heap
    return wasm_heap_alloc(len);
}

// I/O: imports from JavaScript environment
@import("env", "print") func wasm_print(ptr i32, len i32) void;

func os_write(fd i64, buf *u8, count i64) i64 {
    if fd == 1 || fd == 2 {  // stdout/stderr
        wasm_print(buf, count);
        return count;
    }
    return -1;  // No filesystem
}
```

## Open Questions

1. **Should LLVM be the default?** Probably not - direct x86 is faster for development
2. **Bundle LLVM?** No - assume it's installed or installable
3. **Support Windows?** LLVM + libc makes this possible; raw syscalls impossible (unstable ABI)
4. **What about optimization?** Let LLVM handle it; direct backends stay simple
5. **WASI for WASM?** Maybe - WASI provides POSIX-like syscalls for WASM, could use libc.lang

## Conclusion

The answer to "AST → LLVM → native always?" is **no, but LLVM should be an option**.

Direct backends have value:
- Speed (no LLVM startup cost)
- Education (full understanding)
- Minimal deps (just assembler)

LLVM has value:
- Portability (one effort → all platforms)
- Optimization (free -O2)
- WASM (browser deployment)

Both can coexist. The kernel becomes a multi-backend emitter, selected at compile time. Cost is ~2000 LOC per backend, but we only need 2-3 total (x86 direct, LLVM, maybe WASM direct).
