# Multi-Backend Kernel Design

**Status**: Design
**Goal**: Cross-platform compiler (not just x86 generator)

---

## Dev Plan

This design covers two related but independent tracks. Each can be done separately; together they enable full cross-platform support.

### Track A: Cross-OS Support (First Target: macOS)

Add syscall abstraction layer so stdlib works on multiple OSes.

| Step | Task | Files | Status |
|------|------|-------|--------|
| A1 | Create `std/os/linux_x86_64.lang` with `os_*` wrappers | new | TODO |
| A2 | Update `std/core.lang` to use `os_*` instead of raw syscall() | std/core.lang | TODO |
| A3 | Verify fixed point still works (Linux x86_64) | make verify | TODO |
| A4 | Create `std/os/macos_arm64.lang` with macOS syscall numbers | new | TODO |
| A5 | Add target selection to build system | Makefile | TODO |
| A6 | Test on Mac (cross-compile or native) | - | TODO |

**Deliverable**: Same lang source compiles on Linux x86_64 and macOS ARM64 via direct backends.

### Track B: LLVM Backend (New Compiler Target)

Add LLVM IR as alternative codegen output.

| Step | Task | Files | Status |
|------|------|-------|--------|
| B1 | Create `std/os/libc.lang` with extern declarations (write, read, exit, malloc) | new | TODO |
| B2 | Add `LANGBE=llvm` env var support to compiler | src/main.lang | TODO |
| B3 | Implement LLVM IR emitter (text output, like current x86 asm) | src/codegen.lang or new | TODO |
| B4 | Test: compile hello world → .ll → manual clang → binary | test/ | TODO |
| B5 | Handle all AST node types in LLVM backend | - | TODO |
| B6 | Test full bootstrap through LLVM path | make verify | TODO |

**Deliverable**: `LANGBE=llvm ./out/lang program.lang -o program.ll` produces valid LLVM IR that clang can compile.

### Track C: Toolchain Integration (Lang = Full Compiler)

Make lang invoke toolchains automatically so users get binaries, not intermediate files.

| Step | Task | Files | Status |
|------|------|-------|--------|
| C1 | Add `exec()` / `fork()` syscall wrappers to stdlib | std/os.lang | TODO |
| C2 | Implement `find_tool(name)` - PATH search + common locations | src/toolchain.lang | TODO |
| C3 | Auto-invoke `as` + `ld` after x86 codegen | src/main.lang | TODO |
| C4 | Auto-invoke `clang` after LLVM codegen | src/main.lang | TODO |
| C5 | Infer intent from output extension (`.ll` = stop at IR) | src/main.lang | TODO |
| C6 | Implement `lang env` command | src/main.lang | TODO |

**Deliverable**: `./out/lang program.lang -o program` produces a runnable binary. No user knowledge of clang/as/ld required.

### Why Three Tracks?

```
Track A (OS abstraction):     Same backend, different OS syscalls
Track B (LLVM backend):       Different backend, portable codegen
Track C (Toolchain integration): Lang produces binaries, not intermediates
```

They compose:
- Track A alone: Direct x86/ARM64 backends work on multiple OSes
- Track B alone: LLVM backend works (user manually invokes clang)
- Track C alone: Current x86 backend auto-invokes as+ld
- All three: `lang foo.lang -o foo` just works on any platform

### Recommended Order

1. **Track A first** (simpler) - proves the OS abstraction works
2. **Track B second** - LLVM IR is more work but unlocks portability
3. **Track C third** - polish, but can be done incrementally alongside B

Track C can start early (C1-C3 for x86) while B is in progress.

---

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

### Target Selection (Environment Variables)

Like Go's `GOOS`/`GOARCH`, we use environment variables for cross-compilation:

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `LANGOS` | `linux`, `macos`, `windows` | (current OS) | Target operating system |
| `LANGBE` | `x86`, `arm64`, `llvm`, `wasm` | `llvm` | Backend (codegen target) |
| `LANGLIBC` | `none`, `libc` | `none` | Link against system libc (`none` = lang's own)

```bash
# Current behavior (all defaults: LANGOS=<current>, LANGBE=llvm, LANGLIBC=none)
./out/lang program.lang -o program.ll
clang program.ll -o program

# Cross-compile for Mac (still LLVM, just different OS layer)
LANGOS=macos ./out/lang program.lang -o program.ll
clang -target arm64-apple-macos program.ll -o program

# Use direct x86 backend (fast iteration, educational)
LANGBE=x86 ./out/lang program.lang -o program.s
as program.s -o program.o && ld program.o -o program

# LLVM with system libc
LANGLIBC=libc ./out/lang program.lang -o program.ll
clang program.ll -lc -o program
```

**Why env vars over flags?**
- Composable with make (just set vars, don't change commands)
- Matches Go convention developers know
- Can be set once in shell profile for consistent target
- Build scripts don't need to thread flags through

### Lang is a Compiler, Not a Transpiler

**Principle**: `lang foo.lang -o foo` should produce a runnable binary. Users shouldn't need to know about LLVM IR, clang, assemblers, or linkers.

```bash
# This is what users type:
./out/lang program.lang -o program
./program

# NOT this (implementation detail leakage):
./out/lang program.lang -o program.ll
clang program.ll -o program  # user has to know this!
```

Lang handles the full pipeline internally:
1. Parse source → AST
2. Generate backend output (LLVM IR, x86 asm, etc.)
3. **Invoke toolchain** (clang, as+ld) to produce final binary
4. Clean up intermediates (unless `--keep-temps`)

### Toolchain Detection

Lang must detect and invoke platform toolchains. Like Go's toolchain management:

**Linux:**
- LLVM backend: `clang` (from package manager or llvm.org)
- x86 backend: `as`, `ld` (binutils, always present)

**macOS:**
- LLVM backend: `clang` (Xcode CLT)
- arm64 backend: `as`, `ld` (Xcode CLT)
- Detection: `xcode-select -p` or check `/usr/bin/clang`

**Windows:**
- LLVM backend: `clang` (LLVM installer or Visual Studio)
- Detection: Check PATH, Program Files, VS installation

### `lang env` Command

Show detected toolchain and configuration:

```bash
$ lang env
LANGOS=linux        # detected from uname
LANGBE=llvm         # default
LANGLIBC=none       # default

Toolchain:
  clang:    /usr/bin/clang (version 17.0.1)
  as:       /usr/bin/as (GNU assembler)
  ld:       /usr/bin/ld (GNU ld)

Status: Ready (all required tools found)

$ LANGBE=x86 lang env
LANGOS=linux
LANGBE=x86
LANGLIBC=none

Toolchain:
  as:       /usr/bin/as (GNU assembler)
  ld:       /usr/bin/ld (GNU ld)

Status: Ready
```

If tools are missing:
```bash
$ lang env
LANGOS=linux
LANGBE=llvm
LANGLIBC=none

Toolchain:
  clang:    NOT FOUND

Status: INCOMPLETE
  Install clang: sudo apt install clang
  Or use x86 backend: LANGBE=x86 lang ...
```

### Implementation

```lang
func find_clang() *u8 {
    // Try common locations
    var paths []*u8 = [
        "/usr/bin/clang",
        "/usr/local/bin/clang",
        "/opt/homebrew/bin/clang",  // macOS ARM homebrew
        // ... platform-specific paths
    ];
    // Also check PATH via which/where
    return first_existing(paths);
}

func compile_to_binary(ll_file *u8, output *u8) i64 {
    var clang *u8 = find_clang();
    if clang == nil {
        eprintln("Error: clang not found. Install LLVM or use LANGBE=x86");
        return 1;
    }
    // Fork/exec: clang -o output ll_file
    return exec(clang, ["-o", output, ll_file]);
}
```

### Output Extension Inference

Like Go, infer what user wants from output name:

| Output | Behavior |
|--------|----------|
| `-o program` | Full compile → binary |
| `-o program.ll` | Stop at LLVM IR |
| `-o program.s` | Stop at assembly |
| `-o program.o` | Stop at object file |
| `-S` (no -o) | Emit asm to stdout |
| `--emit=ast` | Emit AST (existing) |

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

**Option 2: Environment Variable Overrides Include Path**

The compiler reads `LANGOS` and `LANGLIBC` env vars to redirect includes:

```bash
LANGOS=linux ./out/lang program.lang    # include "std/os.lang" → "std/os/linux_x86_64.lang"
LANGLIBC=libc ./out/lang program.lang   # include "std/os.lang" → "std/os/libc.lang"
```

Implementation in compiler:
```lang
func resolve_include(path *u8) *u8 {
    if streq(path, "std/os.lang") {
        var os *u8 = getenv("LANGOS");
        var libc *u8 = getenv("LANGLIBC");
        if libc != nil && streq(libc, "libc") {
            return "std/os/libc.lang";
        }
        // Build path from LANGOS + LANGBE
        return str_concat3("std/os/", os, "_", arch, ".lang");
    }
    return path;
}
```

**Pros**: Clean, explicit, no generated files, composable with make
**Cons**: Requires compiler modification, needs getenv() support

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
Phase 2: Add `LANGOS`/`LANGLIBC` env var support to compiler for cleaner UX

The generated file approach is how many real build systems work (autoconf generates config.h, CMake generates headers, etc.). It's pragmatic.

### The Full Picture

```
┌─────────────────────────────────────────────────────────────────┐
│ User Program                                                     │
│   include "std/core.lang"                                       │
│     └─> include "std/os.lang"  ← SELECTED BY LANGOS/LANGLIBC    │
│           └─> std/os/linux_x86_64.lang  (raw syscalls)          │
│               OR std/os/libc.lang       (extern to libc)        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Compiler (reads environment variables)                          │
│   LANGBE=x86        → emit x86 assembly                         │
│   LANGBE=llvm       → emit LLVM IR                              │
│   LANGOS=linux      → select linux syscalls                     │
│   LANGLIBC=libc     → link against system libc                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Assembler/Linker                                                │
│   as + ld           (for LANGBE=x86)                            │
│   clang             (for LANGBE=llvm, handles linking)          │
│   -lc               (if LANGLIBC=libc, link against libc)       │
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

See [Target Selection (Environment Variables)](#target-selection-environment-variables) above for the full spec.

```bash
# Current (implicit Linux x86_64)
./out/lang program.lang -o program.s

# Explicit target selection via env vars
LANGOS=linux LANGBE=x86 ./out/lang program.lang -o program.s
LANGOS=linux LANGBE=arm64 ./out/lang program.lang -o program.s
LANGOS=macos LANGBE=arm64 ./out/lang program.lang -o program.s
LANGBE=wasm ./out/lang program.lang -o program.wasm
```

The environment variables:
1. `LANGOS` - Selects the correct OS layer (syscall implementation)
2. `LANGBE` - Selects the backend (x86, arm64, llvm, wasm)
3. `LANGLIBC` - Whether to link against system libc

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
