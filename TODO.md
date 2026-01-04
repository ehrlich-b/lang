# lang - TODO

## Vision

A **language forge**: one compiler that understands any syntax, compiles to any target.

```
lang hello.zig world.lang whats.lisp up.my_dsl -o program
```

Different syntaxes, same compilation pipeline, same ABI, single binary.

---

## Milestones

1. ✓ Self-hosting compiler (x86 fixed point)
2. ✓ Reader macro infrastructure (`#parser{}`, `#lisp{}`)
3. ✓ Language polish (break/continue, bitwise ops, char literals)
4. ✓ AST 2.0: closures, algebraic effects, sum types
5. ✓ Kernel/reader split (lang as a reader, bootstrap verified)
6. ✓ Cross-platform + LLVM backend (169/169 tests, Linux + macOS)
7. ✓ Kernel/reader composition (bare kernel + -r reader = compiler)
8. → **Language forge: Zig capture** ← current
9. → WASM backend
10. → Capture more languages (Rust? OCaml?)

---

## Current: Zig Capture (Language Forge Proof)

**The thesis:** Lang AST can capture any compiled language. Zig is the proof.

**The method:** "Yoink & Bootstrap" - don't write frontends, capture compilers.

```
Traditional (years of work):
  Zig source → [NEW Zig frontend we write] → lang AST → LLVM → binary

Yoink & Bootstrap (weeks of work):
  Zig source → [Zig's own compiler, patched] → lang AST → LLVM → binary
```

See **[designs/zig_ast_compatibility.md](designs/zig_ast_compatibility.md)** for full design.

### Why This Matters

With Zig captured:
- `lang main.lang utility.zig -o program` - true polyglot compilation
- DSLs (50 lines of reader macro) interop with production Zig code
- Proves the forge vision works on a real language

### The Plan

#### Phase 1: Reconnaissance (Day 1-2)
- [ ] Clone Zig source, build from source
- [ ] Study AIR format (`src/Air.zig`, `--verbose-air` output)
- [ ] Document AIR instruction → lang AST mapping
- [ ] Identify required AST extensions

#### Phase 2: AST Extensions (Day 3-4)
- [ ] Implement `callconv` attribute on func nodes (if needed)
- [ ] Implement `inline-asm` node (if needed)
- [ ] Implement `type-aligned` wrapper (if needed)
- [ ] Defer SIMD/packed-struct (not needed for hello world)

#### Phase 3: Backend Implementation (Day 5-7)
- [ ] Write lang-ast backend for Zig compiler (~3-5k lines of Zig)
- [ ] Start with simplest instructions (constants, basic ops)
- [ ] Handle function definitions, calls, control flow
- [ ] Get "hello world" through the pipeline

#### Phase 4: Demo (Day 8+)
- [ ] Compile simple Zig program through lang
- [ ] Compose Zig + lang in same compilation
- [ ] Document limitations (no floats initially)

### Known Gaps

| Gap | Severity | Notes |
|-----|----------|-------|
| Floating point | High | Needed for Zig compiler itself, not hello world |
| SIMD vectors | Low | Skip initially |
| Packed structs | Low | Skip initially |
| Atomics | Low | Skip initially |

**Minimum viable capture:** Integer/string Zig programs compile through lang.

**Full capture (future):** Zig compiler self-hosts through lang. Requires float support.

---

## Foundation Status

**Solid (169/169 tests passing):**
- Self-hosting with fixed-point verification
- LLVM backend (primary, all features)
- Cross-platform (Linux x86-64, macOS ARM64)
- Reader macro system with recursive expansion
- Algebraic effects with resume
- CLI: `help`, `version`, `env`, `tools`

**x86 backend: FROZEN**
- The x86 backend is feature-complete for what it has (integers, basic control flow, effects)
- No new features (floats, calling conventions) will be added
- Kept as emergency bootstrap fallback only
- LLVM is the sole target for Language Forge development

**Spartan (not blocking Zig capture):**
- Platform auto-detection (need `LANGOS=macos LANGBE=llvm` manually)
- Error messages (some errors leak to codegen)
- No negative test suite
- No floats, no struct literals

---

## Deferred: Polish

These are nice-to-have but don't block the forge vision.

### Platform auto-detection

When the compiler finds itself on macOS:
- Default to `llvm` backend (no x86 on ARM)
- Default to `libc` (required on macOS anyway)
- Default to `macos` OS layer

### Negative tests

Suite of "this should fail" tests:
- Undefined variables
- Type mismatches
- Missing returns

### Reader documentation

Explain readers in detail:
- What they are (syntax plugins that emit AST)
- How they work (recursive expansion, S-expression output)
- How to write one (the lang_reader as reference)

---

## Backlog

### Language features (LLVM backend only)
- Floating point (f32, f64) - **needed for full Zig capture** - see `designs/float_support.md`
- Struct literals `Point{x: 1, y: 2}`
- Type aliases `type Fd = i64`
- Generics (monomorphization)
- Debug symbols (DWARF)
- Calling conventions (`extern "C"`, `extern "Zig"`)

### Backends
- WASM (via LLVM)
- Windows (Win64 ABI, via LLVM)

**Note:** The x86 backend is frozen. All new features target LLVM only.

### Forge
- Capture Rust (MIR → lang AST)
- Capture OCaml (Lambda/Cmm → lang AST)
- Capture Go (SSA → lang AST) - hard due to ABI

---

## What's Done

### Milestone 7: Kernel/reader composition
- `--emit-expanded-ast` for reader AST capture
- Bare kernel + `-r` reader = composed compiler
- 169/169 tests passing

### Milestone 6: Cross-platform + LLVM
- OS abstraction layer (`std/os/*.lang`)
- `LANGOS` / `LANGBE` / `LANGLIBC` env vars
- ARM64 inline asm for algebraic effects
- Dual bootstrap: x86 assembly + LLVM IR

### Earlier milestones
- Self-hosting compiler with fixed-point verification
- Reader macros (`#parser{}`, `#lisp{}`)
- Algebraic effects (perform, handle, resume)
- Closures with capture analysis
- Sum types (enum, match)

---

## Design Documents

| Document | Topic |
|----------|-------|
| [designs/zig_ast_compatibility.md](designs/zig_ast_compatibility.md) | **Yoink & Bootstrap**: capturing Zig |
| [designs/abi.md](designs/abi.md) | Calling conventions, language capture analysis |
| [designs/ast_as_language.md](designs/ast_as_language.md) | AST format, kernel/reader architecture |
| [designs/multi_backend.md](designs/multi_backend.md) | x86 and LLVM backend design |
| [designs/cli_commands.md](designs/cli_commands.md) | CLI subcommands design |

---

## Decision Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Forge proof | Zig | Modern, self-hosted, heavy comptime, good test case |
| Capture method | Patch backend | Reuse their frontend, just emit our AST |
| Interop ABI | C (System V) | Lingua franca, Zig/Rust/everyone uses it |
| Initial scope | No floats | Get hello world first, add floats for full capture |
