# lang - TODO

## Vision

A self-hosted compiler compiler. The AST is the language. Syntax is a plugin.

---

## Milestones

1. ✓ Self-hosting compiler (x86 fixed point)
2. ✓ Reader macro infrastructure (`#parser{}`, `#lisp{}`)
3. ✓ Language polish (break/continue, bitwise ops, char literals)
4. ✓ AST 2.0: closures, algebraic effects, sum types
5. ✓ Kernel/reader split (lang as a reader, bootstrap verified)
6. ✓ **Cross-platform + LLVM backend** (167/167 tests, Linux + macOS)
7. → **Architecture hardening** ← current
8. → Bring your own runtime
9. → WASM backend
10. → Language forge (any syntax → any target)

---

## Current: architecture hardening

The compiler works. Now it needs cleanup and decisions about what it actually is.

### The forest view

**What's solid:**
- Self-hosting with fixed-point verification
- Dual backends (x86 + LLVM) both passing 167 tests
- Cross-platform (Linux x86-64, macOS ARM64)
- Reader macro system with recursive expansion
- Algebraic effects with resume

**What's weird:**
- No architecture reference doc (AST format buried in 1500-line design doc)
- ABI not explicitly documented or decided
- Bootstrap still x86-centric despite LLVM being the portable path
- "Bring your own runtime" exists in design but not implementation

### Upcoming priorities

#### ✓ Technical Documentation - Done

Created `docs/` folder with standalone reference documentation:
- [docs/AST.md](docs/AST.md) - All 41 AST node types with S-expression format
- [docs/BOOTSTRAP.md](docs/BOOTSTRAP.md) - Bootstrap chain, trust flow, toolchain requirements
- [docs/BUILDING.md](docs/BUILDING.md) - Build instructions, compilation pipeline, flags

#### ABI and language capture

See **[designs/abi.md](designs/abi.md)** for deep analysis of:
- What calling conventions lang should support
- What it takes to "fully capture" another language (parse it, emit lang AST)
- Why Go can't be captured (fundamentally incompatible ABI)
- How to capture Zig (C-convention code works, exotic conventions need AST extension)

**Key decision:** C ABI is the interop boundary. Languages with exotic conventions (naked functions, interrupt handlers) need AST extension to `func` nodes.

#### Bootstrap: when does LLVM become primary?

**Current:** x86 is fast (5s), LLVM is slow (25-30s). Keep both.

**Mental model shift:** LLVM+libc is "canonical" (works everywhere), x86 is "fast path" (Linux dev). Both produce identical compilers.

**Future:** `make bootstrap` auto-selects based on platform

---

## Code quality debt

| Issue | Priority | Notes |
|-------|----------|-------|
| ~~ARCHITECTURE.md extraction~~ | ~~High~~ | Done: `docs/` folder |
| Composition flow (`-c`) broken | Medium | AST merging produces wrong code |
| Include deduplication for CLI | Medium | CLI files not deduplicated |
| Block expression scopes | Medium | Inline reader vars collide |
| Semantic checks | Low | Undefined vars reach codegen |
| `const` keyword | Low | Compile-time constants |

---

## Bring your own runtime

The `designs/ast_as_language.md` describes this but it's not implemented.

**The idea:**
- Memory allocation via `prim_mem_*` intrinsics
- GC implementations in `.lang` files: none, refcount, tracing, arena
- Readers include their preferred runtime
- Kernel doesn't know or care what allocator is linked

**What exists:**
- `std/core.lang` has bump allocator and malloc/free
- `extern func` works for FFI
- OS abstraction layer (`std/os/*.lang`)

**What's missing:**
- `prim` node type in AST (currently no intrinsics)
- Multiple allocator implementations to choose from
- Documentation of the "runtime interface"

**Priority:** Low. Current allocator works. This becomes important when someone wants GC'd reader output.

---

## Backlog

### Language features
- Platform conditional compilation (Go-style `_linux.lang` suffixes)
- Interfaces / traits
- Variadic parameters (`open()` is special-cased)
- Floating point (f32, f64)
- Struct literals `Point{x: 1, y: 2}`
- Debug symbols (DWARF)
- Type aliases `type Fd = i64`
- `for` loop sugar
- Generics (monomorphization)

### Backends
- WASM (direct or via LLVM)
- Windows (Win64 ABI)

### Runtime
- `prim` intrinsics for pluggable allocation
- `std/gc/refcount.lang`
- `std/gc/arena.lang`

---

## What's done

### Architecture hardening (milestone 7 - in progress)
- Fork-self reader compilation (removes `./out/lang` hardcode)
- Fix LLVM `&func` address-of for void functions
- Documentation: [docs/](docs/) folder with BUILDING.md, BOOTSTRAP.md, AST.md

### Cross-platform (milestone 6)
- OS abstraction layer (`std/os/*.lang`)
- `LANGOS` / `LANGBE` / `LANGLIBC` env vars
- ARM64 inline asm for algebraic effects
- Reader compilation respects LANGBE
- Dual bootstrap: x86 assembly + LLVM IR
- 167/167 tests on Linux x86-64 and macOS ARM64

### LLVM backend
- All language features work
- Target triple selection (x86_64-linux, arm64-apple-macosx)
- `extern func` for FFI
- `open()` variadic ABI workaround

### Test hardening (41 tests added)
- Effects, closures, sum types, stress tests, interaction tests
- 12 bugs fixed during hardening

### Previous milestones
- Self-hosting compiler with fixed-point verification
- Reader macros (`#parser{}`, `#lisp{}`)
- Algebraic effects (perform, handle, resume)
- Closures with capture analysis
- Sum types (enum, match)
- Kernel/reader split architecture

---

## Design documents

| Document | Topic |
|----------|-------|
| [designs/abi.md](designs/abi.md) | Calling conventions, language capture, Zig/Go analysis |
| [designs/ast_as_language.md](designs/ast_as_language.md) | AST format, kernel/reader architecture, effects |
| [designs/multi_backend.md](designs/multi_backend.md) | x86 and LLVM backend design |

---

## Decision log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Interop ABI | C (System V / Win64) | Lingua franca, Zig/Rust/everyone uses it |
| Go interop | Not directly supported | Fundamentally incompatible ABI, use cgo |
| Bootstrap primary | Dual (x86 fast, LLVM portable) | Speed matters for iteration |
| Zig targeting | Emit source or link objects | No Zig AST interchange format exists |
| Runtime model | Bring your own (future) | Kernel stays simple, policy in libraries |
