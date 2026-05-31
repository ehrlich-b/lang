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
- [x] **Guard the `#parser{}` path** - `reader_minilisp_e2e` in `test/run_llvm_suite.sh`
      builds AND runs minilisp's `#parser{}` reader so the crown jewel can't rot again.
- [x] **Fix host-program `#parser{}`-struct field access** - the LLVM first pass now
      expands decl-level reader macros and registers their structs, so `find_struct`
      resolves them during codegen.
- [x] **C-subset reader** - `example/c/c.lang` captures recursive C funcs
      (factorial/fib/add) callable from lang; `#parser{}`-based, guarded by
      `reader_c_e2e`. Required growing `#parser{}` (keyword literals; more
      operator/`;`/`<`/`>` literals). Bounded subset: no typedef/preprocessor/
      structs/assignment/local decls yet.
- [x] **Expand the C subset (round 1)** - local var decls, assignment, `while`
      loops, `if`/`else`, and `//` + `/* */` comments (comments fixed in the shared
      `std/tok.lang`, so every reader benefits). Iterative `factorial` now captured.
- [x] **Multi-char operators** - `== != <= >= && ||` work (the tokenizer already
      lexed them as 2-char tokens; only needed a precedence ladder in the converter).
- [x] **A non-trivial C program** - `example/c/algorithms.lang` (gcd, primality,
      prime counting; nested calls + loops + `%`) runs end to end.
- [x] **Fuller C (round 2)** - unary minus, uninitialized `int x;`, and `for`
      loops (decl- or expr-init; desugared to `{init; while(cond){body; step;}}`).
      Pure reader changes (no compiler source → no bootstrap); guarded by the
      extended `test_c.lang` (triangle/negate/maxof).
- [x] **Fuller C (round 3)** - pointers (`T*`, `&`, `*`), `char*` + string
      literals, structs (`struct N { ... };`), and `.`/`(*p).` member access.
      All reader-only (the kernel already had pointers/structs/field access +
      auto-deref) - NO bootstrap. `(*p).f` is peeled to lang's auto-deref `p.f`
      because the kernel crashes on `(field (unop * p) f)` (loads a struct value);
      that latent kernel sharp-edge is unfixed but no well-behaved reader hits it.
- [x] **Fuller C (round 4)** - bitwise/shift (`& | ^ << >>`), `break`/`continue`,
      arrays + `a[i]` indexing, char literals `'a'`, `->` (lexed as `.`; kernel
      auto-derefs), compound assignment (`+= -= *= /= %=`), `++`/`--` (statement
      and for-step), and global variables (scalar/array/init). `->`, `+=`-family,
      and `++`/`--` are tokenizer changes (`std/tok.lang` is compiler source), so
      they took two `make bootstrap` runs (releases bootstrap-d220c42, -af179c6);
      the rest are reader-only. rdgen literal markers now carry their text so the
      converter can tell `(` from `[`. Sieve-of-Eratosthenes capstone in
      `algorithms.lang`. `++`/`--` are statement/step-only (value-position is a
      no-op, defensively).
- [x] **Polyglot: many readers, one binary** - the headline forge vision. Two
      `#parser{}`-based readers (C + minilisp) in one program collided on the
      generated PNode constructors (`pnode_new/atom/list`), which rdgen emitted
      fresh per grammar. Fixed by defining them once as static funcs in
      `std/parser_reader.lang` (included once per host, deduped) instead of
      generating per-grammar. `example/polyglot.lang` runs C + minilisp + lang in
      one native binary (`c_square(ml_double(3))`); guarded by
      `reader_polyglot_e2e`. Reader-toolkit only - NO bootstrap.
- [x] **C long tail (round 5)** - ternary `?:` and `~` (value-returning
      `block_expr` desugar / `x ^ -1`), `enum` (int-const globals), and `switch`
      (bounded if/else-if desugar, no fall-through) all landed. Needed one
      tokenizer bootstrap (`?`/`~` tokens); the rest reader-only. Remaining C tail:
      typedef (needs a lexer-hack token pre-pass), preprocessor (huge), multiple
      declarators `int a, b;`. C already captures real programs.
- [x] **minilisp -> a real Lisp** - first-class closures (capture), `let`, `quote`
      with interned symbols, cons lists, higher-order `map`. Built on a boxed-value
      runtime (every value is an i64-that's-a-pointer; an all-i64 ABI marshals
      across languages). Reader + runtime only, zero kernel changes.
- [x] **flow - a third language (the effects DSL)** - a generator/coroutine syntax
      (`gen`/`yield`/`for x in g(...)`) lowering to algebraic effects. `yield` is
      bidirectional: its value is what the driver sends back via `send`, so a
      generator's output can depend on its input (a real coroutine, not just a
      generator). Built on the existing effect machinery; zero kernel changes.
- [x] **Polyglot showpiece** - `example/polyglot.lang` is a prime-sieve pipeline:
      flow streams primes (asking C), collects them into a Lisp list, Lisp folds it.
      Three paradigms in one native binary, calling each other at the i64 ABI.
      See devlog 0023.
- [ ] **Pick the next direction** - more flow (a 2nd effect, piped generators),
      finish C typedef, or a non-brace reader (Pascal/Lua-like) to prove the
      toolkit generalizes beyond brace languages.

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

**Solid (177/177 tests passing):**
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
