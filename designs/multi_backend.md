# Multi-Backend Kernel Design

**Goal**: Cross-platform compiler — macOS + LLVM as first +1 targets

---

## TODO (Implementation Checklist)

### Track A: OS Abstraction (do first)
- [ ] **A1**: Create `std/os/linux_x86_64.lang` — wrap syscalls as `os_read()`, `os_write()`, `os_exit()`, `os_mmap()`
- [ ] **A2**: Update `std/core.lang` — replace `syscall(1, ...)` with `os_write(...)` etc
- [ ] **A3**: `make verify` — confirm fixed point still works
- [ ] **A4**: Create `std/os/macos_arm64.lang` — same `os_*` API, macOS syscall numbers
- [ ] **A5**: Makefile target selection — generate `std/os.lang` from `LANGOS` env var
- [ ] **A6**: Test on Mac

### Track B: LLVM Backend (do second)
- [ ] **B1**: Create `std/os/libc.lang` — `extern func write()`, `extern func malloc()`, etc
- [ ] **B2**: Read `LANGBE` env var in `src/main.lang`
- [ ] **B3**: Create `src/codegen_llvm.lang` — emit LLVM IR text (like x86 asm emitter)
- [ ] **B4**: Test: hello.lang → hello.ll → `clang hello.ll -o hello` → runs
- [ ] **B5**: Handle all AST nodes in LLVM backend
- [ ] **B6**: Bootstrap test: compile compiler via LLVM path

### Track C: Toolchain Integration (do third, or incrementally)
- [ ] **C1**: Add `fork()`/`exec()` syscall wrappers
- [ ] **C2**: Implement `find_tool("clang")` — PATH search
- [ ] **C3**: Auto-invoke `as`+`ld` after x86 codegen
- [ ] **C4**: Auto-invoke `clang` after LLVM codegen
- [ ] **C5**: `-S` flag to stop at assembly/IR (current behavior becomes opt-in)
- [ ] **C6**: `lang env` command

### Key Files to Create
```
std/os/linux_x86_64.lang   # os_* wrappers for Linux
std/os/macos_arm64.lang    # os_* wrappers for macOS
std/os/libc.lang           # extern declarations for libc
src/codegen_llvm.lang      # LLVM IR emitter
```

### Environment Variables
| Variable | Values | Default |
|----------|--------|---------|
| `LANGOS` | `linux`, `macos` | current OS |
| `LANGBE` | `x86`, `llvm` | `llvm` |
| `LANGLIBC` | `none`, `libc` | `none` |

---

# Reference Material

*Everything below is design rationale. Read only if you need to understand "why".*

---

## Architecture

```
        ┌→ x86 asm  → as     → Linux binary (current, keep for fast iteration)
AST → kernel ─┤
        └→ LLVM IR  → clang  → {anything} (new, for portability)
```

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

### Compilation Flags (Like GCC)

No extension guessing. Explicit flags control output stage:

| Flag | Output | Notes |
|------|--------|-------|
| (none) | **Binary** | DEFAULT. Full compile, invoke toolchain |
| `-S` | Assembly/IR | Stop at kernel output (current behavior) |
| `-c` | Standalone compiler | Existing meaning (embed reader) |
| `--emit=ast` | AST | Existing meaning |

```bash
# Default: full compile to binary
./out/lang program.lang -o program
./program  # runs!

# Stop at assembly (current behavior, now opt-in)
./out/lang program.lang -S -o program.s
as program.s -o program.o && ld ...  # user's problem

# Stop at LLVM IR
LANGBE=llvm ./out/lang program.lang -S -o program.ll
clang program.ll -o program  # user's problem
```

**Key insight**: What we do TODAY (emit .s) becomes the `-S` behavior. The new DEFAULT is full compilation to binary.

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

### Include Selection: Generated std/os.lang

The Makefile generates `std/os.lang` based on target before compilation:

```bash
# In Makefile
build-linux-x86_64:
    echo 'include "std/os/linux_x86_64.lang"' > std/os.lang
    ./out/lang program.lang -o program.s
```

Then `std/core.lang` just does:
```lang
include "std/os.lang"  // Gets the generated file
```

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

**Allocation Strategy**:
- Direct backends (x86): `os_mmap` + bump allocator
- LLVM backend: libc `malloc`

`std/core.lang` uses `os_*` functions; `std/os/*.lang` provides platform implementations.

