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
      flow streams primes (asking C, which asks forth about each divisor),
      collects them into a Lisp list, Lisp folds it, forth folds the digits of
      the result. Four paradigms in one native binary, calling each other at the
      i64 ABI. See devlog 0023, 0024.
- [x] **forth - a fourth language, and the first non-brace one** - postfix, with
      no expression grammar at all: a flat stream of words over a data stack. The
      stack is the READER's, holding AST nodes at read time, so it is erased
      before codegen (`: square ( n -- n2 ) dup * ;` optimizes to one `mul`).
      The stack effect comment is load-bearing - it names the params and counts
      the results, which is what makes a word an ordinary i64 function. Body
      words are flat and `if`/`else`/`then` are given meaning by the converter,
      exactly as Forth's immediate words do, which also dodges the weak
      no-backtrack parser entirely. Reader-only. Guarded by `reader_forth_e2e`.
      Bounds: recursion but no loops/`variable` yet, names are lang identifiers
      plus an optional `?`, negative literals must be `0 5 -` (the tokenizer
      splits `-5`). In the polyglot, C's trial-division loop calls Forth's
      `divides?` and Forth folds the digits of what Lisp computes.
- [x] **minipy - a fifth language, and the first layout-delimited one** - a
      Python subset whose block structure lives in the whitespace to the LEFT of
      each line, which is the part every other reader throws away. Layout needed
      NO change to the shared tokenizer: a token carries its byte offset, so the
      two facts the offside rule needs ("first token on this line?" and "at what
      column?") are recoverable in the reader, which then synthesizes the
      NEWLINE/INDENT/DEDENT stream itself. Reader-only - no bootstrap. Bracket
      depth makes newlines inside `( )` continuations, and a comment-only line
      contributes no tokens so it can't affect indentation. Python's
      function-scoped names are reconciled with lang's block-scoped `var` by
      hoisting every assigned name to the top of the function; `for`'s step goes
      at the TOP of the loop body so `continue` still advances it. `print` is
      variadic and polymorphic, lowered per-argument at read time. Guarded by
      `reader_minipy_e2e`; in the polyglot it is the reporting layer, which is
      the job a scripting language actually has. See devlog 0025.
- [ ] **Pick the next direction** - loops + `variable`/`!`/`@` for forth (which
      needs the stack model to survive mutation), more flow (a 2nd effect, piped
      generators), finish C typedef, minipy round 2 (lists, on minilisp's boxed
      runtime), or milestone 9 (WASM - but flow's effects use inline-asm stack
      switching that WASM can't express).

### Reader toolkit (the thing to invest in)

Effort that would otherwise go into lang ergonomics goes here instead — making
readers easier to write is the product.

**A reader can now use the whole language in its own source** (2026-08-01). A
reader's source is regenerated by unparsing its AST back to lang text before
being compiled in a forked child, so a reader was only ever as expressive as
that unparser. It rendered 10 expression kinds and 2 type shapes; everything
else became the literal text `<expr>` (a syntax error surfacing as an
unexplained "reader compilation failed") or, for an array/fn/closure type, read
a garbage pointer and **segfaulted the compiler**. Now added: array/fn/closure
types, indexing, array literals, cast/bitcast, lambdas, block expressions,
`let`, `match` + patterns, and `perform`/`handle`/`resume` — plus module-level
`var` globals, `enum` and `effect` declarations in the reader's own file.

That last one retires a long-standing trap: **a global declared in a reader's
own file used to be dropped**, so readers derived unique names from node
addresses and threaded context through parameters instead. Those workarounds
still work and don't need unwinding, but new readers don't need them.
Guarded by `test/suite/155_reader_full_language.lang`.

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

The code is gone (`patches/`, `zig_reader/`, the capture scripts). Analysis is kept
in `designs/path_b_zig_reader.md` / `designs/air_emitter.md`; the last commit that
still contained the emitter is `ff8813d`.

---

## Foundation Status

**Solid (184/184 tests passing):**
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

## Broken windows

### Fixed 2026-08-01

Three silent-miscompile bugs found while testing the reader unparser (none were
unparser bugs — each reproduced in a plain lang program). All three now have
regression tests that fail on the pre-fix compiler.

- **Local array-literal initializers were silently wrong.** `var a [3]i64 =
  [1,2,3]` stored one scalar into slot 0 and left the rest as stack garbage,
  while the global form built a proper constant aggregate. Locals now store
  element-wise, zero-filling past the end of the literal and narrowing i64
  expressions back to the element type (`inttoptr` for pointers, `trunc` for
  small ints) — the mirror of what the index-read path does.
  Test `156_local_array_literal` (segfaulted before).
- **Struct/enum parameters were read as their own incoming pointer.** An
  aggregate param slot held a pointer to the caller's value, but every reader of
  an aggregate identifier takes the ADDRESS of its slot, so `match o` read the
  pointer as the tag and fell off the arm chain into an uninitialized result.
  Params now get real aggregate storage and are copied into it, which also gives
  them by-value semantics (writing through a param no longer risks the caller's
  copy). Test `157_aggregate_params`.
- **`cast()` of an untyped operand emitted `add void 11, 0`.** Integer literals
  and call results have no type node; they now default to i64. This hid behind a
  second bug: `llvm_is_float_literal` scanned the number token to the next NUL
  instead of respecting its length, so a `.` anywhere later in the file marked
  every integer literal as a float. Test `158_cast_literal`.

The root cause of the whole category was `llvm_emit_expr`'s fallback, which
silently emitted `0` for any expression kind it didn't handle. It is now a hard
error. Probing every suite file, example, and the compiler's own source found
only `nil` legitimately reaching it (now an explicit case), so nothing else was
relying on the silence.

### Still open

- **Narrowing integer casts produce a non-i64 value.** `cast(i32, x)` emits a
  `trunc` and hands back an i32, which then fails LLVM verification at any i64
  use site. Pre-existing and acknowledged in `265_cast_basic`'s own comment
  ("integer sizes not yet fully supported"). Fails loudly, so it's not in the
  silent-wrong-answer category. The fix that fits lang's all-i64 model is to
  `trunc` then `sext`/`zext` straight back to i64.
- **Returning a struct by value returns a pointer to the callee's dead frame.**
  It works today because the caller copies out of it immediately, but the value
  is only valid until something else uses that stack. Not reachable from any
  shipped code.
- **`break`/`continue` outside a loop emit nothing** on the LLVM backend when
  `llvm_find_loop` returns nil (`src/codegen_llvm.lang`), where the x86 backend
  errors and exits.

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

### Reader cache goes stale on reader-source edits

`should_recompile_reader` (`src/codegen.lang:1087`) invalidates the cached reader
executable on the mtime of `out/lang`, `out/lang_next`, and `std/core.lang` — but
**not** on the reader's own source file. Edit `example/c/c.lang` alone and recompile
without rebuilding the compiler, and you silently run the OLD reader. Masked in
normal development because `make build` bumps `out/lang_next`. Workaround: delete
`.lang-cache/readers/<name>`. Fix: hash or mtime-check the defining source file.

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
