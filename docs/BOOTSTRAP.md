# Bootstrap Process

This document explains how lang's bootstrap chain works and how to get a working compiler from scratch.

## Toolchain Requirements

### Linux (x86-64)

**Required:**
- `as` - GNU assembler (part of binutils)
- `ld` - GNU linker (part of binutils)
- `make` - GNU make

**Optional (for LLVM backend):**
- `clang` - LLVM C compiler (for linking LLVM IR)

Install on Debian/Ubuntu:
```bash
sudo apt install build-essential
```

### macOS (ARM64)

**Required:**
- Xcode Command Line Tools (provides `clang`, `as`, `ld`)
- `make`

Install:
```bash
xcode-select --install
```

## What is Bootstrap?

Lang is a self-hosting compiler: the compiler is written in lang itself. This creates a chicken-and-egg problem: how do you compile the compiler if you need the compiler to compile it?

The solution is **bootstrap artifacts** - pre-compiled versions of the compiler stored in the repository:

```
bootstrap/
├── current -> 1654aca/              # Symlink to active bootstrap
├── escape_hatch.s                   # Emergency recovery (x86 assembly)
├── llvm_libc_macos.ll              # Emergency recovery (LLVM IR for macOS)
└── 1654aca/                         # Bootstrap for commit 1654aca
    ├── compiler.s                   # x86-64 assembly (Linux)
    ├── llvm_libc_macos.ll          # LLVM IR (macOS, any arch)
    ├── lang_reader/source.ast       # Expanded AST of lang reader
    └── PROVENANCE                   # Build metadata and checksums
```

## Bootstrap Chain Overview

```
                    TRUST CHAIN
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 1: Root of Trust                                      │
│  ─────────────────────                                       │
│  bootstrap/current/compiler.s → as → ld → ctrusted          │
│                                                              │
│  ctrusted is the foundation - we trust it because it        │
│  was verified by previous bootstrap cycles.                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 2: Generation 1                                       │
│  ────────────────────                                        │
│  ctrusted compiles src/*.lang → kernel1                      │
│  kernel1 compiles src/lang_reader.lang → lang1               │
│                                                              │
│  lang1 is a standalone compiler (kernel + reader combined)   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 3: Generation 2 + Fixed Point                         │
│  ──────────────────────────────────                          │
│  lang1 compiles src/*.lang → kernel2                         │
│                                                              │
│  VERIFY: kernel1.s === kernel2.s (KERNEL FIXED POINT)        │
│                                                              │
│  kernel2 compiles src/lang_reader.lang → lang2               │
│                                                              │
│  VERIFY: reader_ast1 === reader_ast2 (AST FIXED POINT)       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 4: Validation                                         │
│  ──────────────────                                          │
│  Run x86 test suite (167 tests) with lang2                   │
│  Build LLVM+libc compilers (Linux + macOS)                   │
│  Run LLVM test suite (167 tests)                             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 5: Promote                                            │
│  ───────────────                                             │
│  Copy kernel2.s → bootstrap/<commit>/compiler.s              │
│  Copy LLVM IR → bootstrap/<commit>/llvm_libc_macos.ll        │
│  Update bootstrap/current symlink                            │
│  Update escape_hatch.s                                       │
└─────────────────────────────────────────────────────────────┘
```

## Fixed Point Verification

The key insight of lang's bootstrap is **fixed point verification**. A fixed point means:

> When the compiler compiles itself, the output is identical.

This proves the compiler is stable and not introducing subtle changes each generation.

### Kernel Fixed Point

```
kernel1.s === kernel2.s
```

Both assembly files must be byte-for-byte identical. This proves:
- The compiler produces deterministic output
- No hidden bugs are changing behavior between generations

### AST Fixed Point

```
reader_ast1 === reader_ast2
```

The expanded AST (after processing includes and reader macros) must be identical. This proves:
- The reader macro system produces stable output
- Include resolution is deterministic

## Quick Start

### First Time Setup (Linux)

```bash
# Clone the repository
git clone <repo-url>
cd language

# Initialize from bootstrap
make init      # Assembles bootstrap/current/compiler.s → out/lang

# Verify everything works
make bootstrap  # Full verification + promotion
```

### First Time Setup (macOS)

```bash
# Clone the repository
git clone <repo-url>
cd language

# Build from LLVM bootstrap
clang bootstrap/llvm_libc_macos.ll -o lang

# Verify LLVM fixed point
make llvm-verify
```

### After Code Changes

**Always run `make bootstrap` after modifying compiler sources.**

```bash
# Edit src/*.lang files...

make bootstrap   # Verify and promote
git add -A && git commit -m "Your message"
```

## Emergency Recovery

If the bootstrap gets corrupted (rare but possible), use the escape hatches:

### On Linux
```bash
# Use escape_hatch.s directly
as bootstrap/escape_hatch.s -o /tmp/emergency.o
ld /tmp/emergency.o -o /tmp/emergency
/tmp/emergency src/*.lang -o /tmp/recovered.s
# Continue staged rebuild...
```

### On macOS (or any platform with clang)
```bash
# Build from LLVM IR
clang bootstrap/llvm_libc_macos.ll -o /tmp/emergency
LANGBE=llvm /tmp/emergency src/*.lang -o /tmp/recovered.ll
clang /tmp/recovered.ll -o /tmp/recovered
# Verify fixed point manually...
```

## Dual Backend Strategy

Lang maintains two bootstrap paths:

| Bootstrap | Location | Platform | Speed |
|-----------|----------|----------|-------|
| x86 assembly | `compiler.s` | Linux x86-64 only | Fast (~5s) |
| LLVM IR | `llvm_libc_macos.ll` | Any (via clang) | Slower (~25s) |

**Why both?**
- x86 is fast for development iteration
- LLVM is portable and works everywhere clang runs
- Either can rescue the other if corrupted

## Verification Commands

### Full Bootstrap (Linux)
```bash
make bootstrap
```
This runs all 5 stages, verifies both fixed points, runs both test suites, and promotes if successful.

### LLVM-Only Verification (macOS)
```bash
make llvm-verify
```
Skips x86 tests, verifies LLVM fixed point, runs LLVM test suite.

### Just Build (No Promotion)
```bash
make build
```
Compiles to `out/lang_next` without verification or promotion. Use for quick iteration.

## Environment Variables

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `LANGOS` | `linux`, `macos` | `linux` | Target operating system |
| `LANGBE` | `x86`, `llvm` | `x86` | Backend (x86 assembly or LLVM IR) |
| `LANGLIBC` | `none`, `libc` | `none` | Use system libc or raw syscalls |

Example:
```bash
# Build for macOS with LLVM backend using libc
LANGOS=macos LANGBE=llvm LANGLIBC=libc make build
```

## Provenance Tracking

Each bootstrap version includes a `PROVENANCE` file:

```yaml
compiler.s:
  sha256: abc123...
  built_by: bootstrap/previous_commit/
  built_at: 2024-01-15T10:30:00Z
  source_commit: 1654aca
  verification:
    kernel_fixed_point: true
    ast_fixed_point: true
```

This creates an auditable chain of trust from each bootstrap to its predecessor.

## Troubleshooting

### "Kernel fixed point failed"
The compiler is producing different output. Common causes:
- Non-deterministic string pool ordering (rare bug)
- Debug code left in (remove print statements)
- Undefined behavior in codegen

### "AST fixed point failed"
The reader is producing different output. Common causes:
- Reader macros using timestamps or random values
- Include path resolution differences
- Non-deterministic hash map iteration

### "Test suite failed"
A test is failing. Check:
- Did you run the correct test suite for your platform?
- Is the test expecting x86-specific behavior?
- Check test output in `/tmp/` for details

### "Bootstrap stuck"
If bootstrap hangs, it's usually:
- Infinite loop in codegen (reader macro compilation)
- Memory exhaustion (bump allocator out of space)
- Use `Ctrl+C` and check which test/file was being compiled
