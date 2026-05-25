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
8. → **Reader authorship: ship many readers** ← current
9. → WASM backend
10. → Capture more languages (Rust? OCaml?)

---

## Current: Ship Readers (Reader-Authorship Proof)

**The thesis:** lang is the easiest possible reader-maker. A reader is a syntax
plugin that emits lang AST; the kernel compiles any reader's output to native
code. Proving this means **building readers**, not improving lang-the-language —
lang is a throwaway bootstrap substrate (see Decision Log), and the endgame is a
polyglot stdlib written in reader-authored *better* languages.

### Status

- [x] **minilisp end-to-end** - `example/minilisp/` reads s-expr syntax, emits AST,
      compiles to native via LLVM. Arithmetic + recursive `defun` both run. The
      `#parser{}`-generated parser path works end to end (it had silently rotted —
      reader-build dumped AST as source; now parses + unparses).
- [ ] **Guard the `#parser{}` path** - add a build-and-run reader test to the LLVM
      suite so the crown-jewel parser generator can't break unnoticed again.
- [ ] **Fix host-program `#parser{}`-struct field access** - see Known Bugs.
- [ ] **Pick the next real reader** - selection criterion (Decision Log): a language
      we'd actually want to rewrite stdlib components in, not a toy demo.

### Reader toolkit (the thing to invest in)

Effort that would otherwise go into lang ergonomics goes here instead — making
readers easier to write is the product.

| Layer | What | File |
|-------|------|------|
| Parser generator | `#parser{ grammar }` → recursive descent parser | `std/parser_reader.lang` |
| AST constructors | `ast_binop`, `ast_func`, ... + `ast_emit` | `std/ast.lang` |
| Parser combinators | `p_seq`, `p_token`, ... | `std/parse.lang` |

See [designs/ast_as_language.md](designs/ast_as_language.md) for the full layer cake
(Level 0 raw S-exprs → Level 5 lang variants).

### Known Bugs

- **Host-program `#parser{}`-struct field access bails to `(number 0)`.** A struct
  defined by `#parser{}` *expansion* in the including program (not in the reader
  exe) isn't found by `find_struct` during LLVM codegen, because it's registered
  via `process_decl_first_pass`. Plain `struct` decls and the unparsed reader-exe
  copy work. Currently dead code in minilisp's host binary, so it links and runs.

### Abandoned: Zig-via-AIR

Capturing Zig by patching its compiler to emit lang AST from AIR is abandoned. AIR
is monomorphized, comptime-lowered, fully-typed Zig — "capturing" it means
reproducing Zig's entire memory model (slices, optionals, error unions, alignment,
calling conventions) in lang's AST. Infinite long tail, and the captured subset was
near-circular (a hand-written Zig subset hobbled to `u8` arrays).

The IR-reuse *method* was the dead end, not the idea of reading Zig syntax: a
**reader** for a Zig *subset* is still an easy target — low-level runtime semantics
(pointers, manual memory, value structs, fixed-width ints) map directly onto lang's
C-like AST. High-level dynamic languages are the *hard* targets (they need a shipped
runtime), so "I can only capture scripting languages" is backwards.

History preserved in `git log` and `designs/path_b_zig_reader.md` /
`designs/air_emitter.md`.

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

**Spartan (not blocking reader work):**
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
| [designs/ast_as_language.md](designs/ast_as_language.md) | **The vision**: AST as root language, syntax as plugin |
| [designs/zig_ast_compatibility.md](designs/zig_ast_compatibility.md) | _(historical)_ capturing Zig via AIR — abandoned |
| [designs/air_emitter.md](designs/air_emitter.md) | _(historical)_ AIR emitter patches — abandoned |
| [designs/abi.md](designs/abi.md) | Calling conventions, language capture analysis |
| [designs/multi_backend.md](designs/multi_backend.md) | x86 and LLVM backend design |
| [designs/cli_commands.md](designs/cli_commands.md) | CLI subcommands design |

---

## Decision Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Forge proof | Zig-via-AIR (abandoned) | IR-reuse tar pit; reader-authorship is the real proof |
| Capture method | Write a reader | Patch-the-backend (AIR reuse) abandoned; readers emit AST from surface syntax |
| Interop ABI | C (System V) | Lingua franca, Zig/Rust/everyone uses it |
| Float support | ✅ Done | f32/f64 via LLVM backend |
