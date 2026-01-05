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
6. ✓ Cross-platform + LLVM backend (170/170 tests, Linux + macOS)
7. ✓ Kernel/reader composition (bare kernel + -r reader = compiler)
8. → **Language forge: Zig capture** ← current
9. → WASM backend
10. → Capture more languages (Rust? OCaml?)

---

## Current: Zig Capture (Language Forge Proof)

**The thesis:** Lang AST can capture any compiled language. Zig is the proof.

**Design doc:** **[designs/zig_ast_compatibility.md](designs/zig_ast_compatibility.md)** - full analysis and checklist.

### Status

- [x] **Reconnaissance complete** - Built debug zig, captured 20K lines of AIR from zig self-compile
- [x] **Mapping complete** - 88 AIR instructions analyzed, most map directly to lang AST
- [x] **Floats done** - f32/f64 support added, 170/170 tests passing
- [x] **Cast nodes done** - `cast(type, expr)` and `bitcast(type, expr)` syntax, 172/172 tests
- [x] **i128/u128 done** - Types recognized (full allocation requires integer type system work)
- [x] **AIR emitter designed** - See [designs/air_emitter.md](designs/air_emitter.md)

### Next Steps

- [x] **Unsigned comparisons in lang** - Fixed! `codegen_llvm.lang` emits `ult`/`ugt`/`ule`/`uge` for unsigned types
- [ ] **Patches infrastructure** - `patches/` directory, `make patch-zig`, manifest.yaml
- [ ] **Write AIR→AST emitter** - `patches/zig/src/codegen/lang_ast.zig` (~2000 lines)
- [ ] **Simple function through pipeline** - arithmetic function → lang AST → binary
- [ ] **Reader composition** - `./out/lang -r zig compiler.ast -o lang_zig`
- [ ] **Hello world** - `./lang_zig hello.zig` compiles and runs

### What Doesn't Need Lang Changes

| Feature | Workaround |
|---------|------------|
| Slices | Emit as structs |
| clz/ctz/memset | Extern calls to compiler-rt |
| Optionals | Emit as enums |
| Error unions | Emit as enums |
| Calling conventions | Ignore initially |

### Known Gaps

| Gap | Severity | Notes |
|-----|----------|-------|
| Floating point | ✅ Done | f32/f64 types, literals, arithmetic, comparisons |
| Unsigned comparisons | ✅ Done | `ult`/`ugt`/`ule`/`uge` for u8/u16/u32/u64 and pointers |
| Inline ASM | ✅ Mitigated | Use `-lc` flag - routes syscalls through libc |
| compiler_rt ASM | ✅ Mitigated | Pure Zig fallbacks exist; link system libcompiler_rt |
| SIMD vectors | Low | Skip initially |
| Packed structs | Low | Skip initially |
| Atomics | Low | Skip initially |

**Minimum viable capture:** Integer/string Zig programs compile through lang.

**Full capture (future):** Zig compiler self-hosts through lang.

---

## Foundation Status

**Solid (170/170 tests passing):**
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
- No struct literals

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
- ✅ Floating point (f32, f64) - implemented, see `designs/float_support.md`
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
- 170/170 tests passing (includes float support)

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
| [designs/zig_ast_compatibility.md](designs/zig_ast_compatibility.md) | **Yoink & Bootstrap**: capturing Zig (analysis) |
| [designs/air_emitter.md](designs/air_emitter.md) | **AIR Emitter**: patches approach, implementation plan |
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
| Float support | ✅ Done | f32/f64 via LLVM backend |
