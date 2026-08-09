# lang - TODO

## Vision

A **language forge**: write a source reader, compose it with one kernel, and get
a native or wasm compiler for that syntax.

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
6. ✓ Cross-platform + LLVM backend (198/198 checks, Linux + macOS)
7. ✓ Kernel/reader composition (bare kernel + -r reader = compiler)
8. ✓ Reader-authorship proof (C, minilisp, flow, forth, minipy)
9. ✓ WASM program target (`LANGOS=wasm` + suite + precompiled browser demos)
10. ✓ Browser compiler and editable reader lab
11. ✓ Real readers produce real compilers
12. ✓ Exact source spans and reader-driven wasm breadth
13. ✓ Turn the browser proof into a reader workbench
14. ✓ Make reader failures fast to fix
15. ✓ Reuse the compiler the reader just made
16. ✓ Fit the first reader on one screen
17. ✓ Make the textareas behave like code editors
18. ✓ Scaffold a reader outside the browser
19. → **Inspect a reader before codegen** ← current
20. → Capture more languages only when it improves the reader toolkit

---

## Completed: Exact locations and reader-driven wasm breadth

The browser now runs the same compiler-compiler loop as native: edit a
`#parser{}` grammar and lowering, compile the reader, read custom source into
shared AST, then compile and run that AST—all in the tab.

- [x] Split the generated parser runtime from its build-time generator.
- [x] Embed `#parser{}` expansion in `compiler.wasm`; no subprocess or server hop.
- [x] Make the lab starter a generated grammar, not a hand-written recognizer.
- [x] Guard grammar → reader wasm → AST → program wasm → `main()` end to end.
- [x] Add an optional source span to shared AST nodes without breaking old readers.
- [x] Carry reader token spans through `PNode` and the AST builders.
- [x] Report semantic errors at the exact location in custom-language source,
      in minted native compilers and the browser pipeline.
- [x] Grow direct wasm from reader failures, not a feature checklist: structured
      break/continue and narrow integer locals make the shipped Forth reader run
      end to end and the minilisp reader compile and execute in the browser.
- [x] Let browser builds consume ordinary `std/parser_reader.lang` sources while
      keeping the build-time generator out of the reader module.
- [x] Add browser-side target runtimes. `--from-ast --runtime` and the lab's
      collapsed runtime editor now carry helpers emitted by a reader; the gate
      reads, compiles, and runs Minilisp to a boxed 42 entirely in the tab.
- [x] Re-run the shipped-reader inventory. Tiny, Calc, Minilisp, and Forth build
      as reader wasm; C, Flow, and Minipy all stop at address-taken scalar locals.
- [x] Support address-taken locals in direct wasm with per-call spill frames;
      parameters, shadowing, recursion, and pointer mutation retain Lang
      semantics instead of forcing heap-cursor rewrites.
- [x] Run every shipped reader through source → reader wasm → AST →
      program wasm. Minimal C, Flow, and Minipy programs now join Tiny, Calc,
      Forth, and runtime-backed Minilisp in the browser gate.

Do not capture a sixth language yet. First make the next reader faster to write,
debug, compile, and share than the five already shipped.

---

## Completed: Turn the browser proof into a reader workbench

The lab proves the complete compiler-compiler loop, but it still behaves like a
single demo. Make it useful for studying and iterating on readers without making
the runner taller:

- [x] Add a compact preset loader for the starter and shipped readers, clearly
      presented as examples rather than the product.
- [x] Keep reader, source, and optional target runtime together when switching
      presets; preserve in-progress edits locally.
- [x] Make the generated reader Wasm and final program Wasm downloadable.
- [x] Add a size-safe share path: versioned JSON workspace files keep reader,
      source, and runtime together, validate on open, and reject files over
      1 MiB instead of stuffing large shipped readers into fragile URLs.

The primary action remains **write a language**. Presets are scaffolding for
reader authors, not a return to marketing a fixed list of syntaxes.

---

## Completed: Make reader failures fast to fix

The compiler now reports exact custom-source spans. Close the browser feedback
loop so those diagnostics take authors directly back to the failing input:

- [x] Focus and select `reader.lang`, `source.read`, or `runtime.lang` from a
      location-bearing diagnostic; open the collapsed runtime only on demand.
- [x] Keep phase context (reader build, reader run, AST compile, program run)
      visible in failures without adding permanent UI.
- [x] Offer the complete emitted AST for inspection without making the result
      pane taller by default.

---

## Completed: Reuse the compiler the reader just made

The lab currently recompiles a reader when only custom-language source changed.
Make the generated artifact real and make the common edit/run loop faster:

- [x] Give reader Wasm source over stdin instead of embedding one source string.
- [x] Reuse that module until reader code changes; source-only runs skip the
      reader-build phase.
- [x] Prove one downloaded reader module can read two different inputs and
      document its tiny host contract.

---

## Completed: Fit the first reader on one screen

The generated-grammar starter is honest but still makes a one-rule language
spell out parse-tree indexing and a complete `main` declaration. Remove that
incidental work without hiding the reader/AST boundary:

- [x] Add small, general helpers for a parse-tree child and an i64 `main`.
- [x] Use them in the lab starter and Tiny where they improve readability.
- [x] Keep the entire starter visible without scrolling its editor at the
      default desktop height; guard the helper path end to end.

---

## Completed: Make the textareas behave like code editors

The workbench deliberately stays dependency-free, but reader authors should not
lose basic editor mechanics:

- [x] Insert/indent with Tab and outdent with Shift-Tab instead of moving focus.
- [x] Preserve current indentation on Enter, with one extra level after `{` or
      `:` for Lang and layout-language source.
- [x] Apply the behavior to reader, custom source, and runtime while preserving
      Cmd/Ctrl-Enter build-and-run.

---

## Completed: Scaffold a reader outside the browser

The workbench now gives browser authors a tight loop. Native authors should get
the same clean starting point without copying from documentation:

- [x] Add one discoverable command that creates a named reader and sample input.
- [x] Refuse to overwrite either file and leave no partial scaffold on failure.
- [x] Find the checkout's `std/` beside `out/lang`, so the printed commands work
      from a clean directory; expose and override that root with `lang tools`
      and `LANG_ROOT` when the binary moves.
- [x] Compile and run the fresh scaffold from another directory in an end-to-end
      CLI gate; the same gate covers reruns, both pre-existing-file directions,
      invalid names, missing toolkit files, and help discovery.

---

## Current: Inspect a reader before codegen

The browser exposes the AST a reader returned. Native reader authors should not
need a complete target compile just to inspect that frontend boundary:

- [ ] Add a concise `lang read` command that runs reader source on custom source
      and writes the returned shared AST to stdout or `-o`.
- [ ] Preserve reader and custom-source diagnostics without also reporting a
      misleading codegen failure.
- [ ] Feed a scaffold's saved AST back through `--from-ast` and run it in an
      end-to-end gate, proving the inspection path is lossless.

---

## Completed: Real readers produce real compilers

`lang` is a compiler compiler: give it a reader, and it mints a standalone
compiler for that syntax. This now works for generated grammars and readers
with runtimes, not only the small hand-written examples.

Ship the artifact boundary before adding another language:

- [x] A minimal `#parser{}` reader mints a standalone compiler and compiles a program.
- [x] Native artifacts retain generated parsers but dead-strip the parser generator and Lang frontend.
- [x] The shipped C reader mints a standalone `cc` and passes an end-to-end test.
- [x] `--runtime file.lang` expands and embeds runtime AST at compiler-build time.
- [x] The shipped minilisp reader mints a self-contained compiler with its runtime.
- [x] Generated compilers have a small, honest CLI (`--help`, output defaults, diagnostics).
- [x] Bootstrap and release gates exercise the real generated-reader path.

Then return to reader authoring and browser parity. The product is not the set
of syntaxes in `example/`; it is how quickly someone can add the next one. The
working learning path is:

1. `example/tiny/` — a 20-line recognizer and AST emitter
2. `example/calc/` — a 78-line precedence parser with useful errors
3. `#parser{}` — transactional generated parsers with furthest-failure context
4. shipped frontends — lowering, runtimes, layout, effects, and interop

- [x] `lang help reader` explains the compiler-compiler model and gives runnable commands.
- [x] Reader and AST-builder quick references, plus an honest `#parser{}` boundary guide.
- [x] Reader parse/build/link failures are fatal, remove partial output, and identify bad helpers.
- [x] Reader subprocesses inherit the environment and accept source/AST beyond the old 64 KiB cap.
- [x] Tiny and calculator readers are guarded end to end.
- [x] `lang compiler <reader> ... -o <binary>` produces a named native compiler in one command.
- [x] Reader imports, grammars, types, globals, and transitive helpers can appear after the reader; wrappers omit unrelated host functions.
- [x] Preserve source provenance through includes, reader wrappers, and reader-emitted top-level AST.
- [x] `#parser{}` rewinds failed alternatives/sequences, guards empty repetitions, and exposes furthest-token parse errors.
- [x] Compile and run editable Lang entirely in the browser: `compiler.wasm` now emits a direct wasm binary.
- [x] Put an editable reader beside editable source in the browser; compile reader → AST → program wasm entirely in the tab.
- [x] Generate a reader from editable `#parser{}` grammar in the browser and run
      its custom source end to end.

---

## Archive: Ship Readers (Reader-Authorship Proof)

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
      exactly as Forth's immediate words do. Reader-only. Guarded by
      `reader_forth_e2e`.
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
- [x] **Direction picked: milestone 9, WASM** - the endgame is a browser
      playground at lang.ehrlich.dev: the compiler itself compiled to wasm,
      compiling the polyglot languages client-side. Stage A landed (below);
      remaining stages tracked under Milestone 9.

### Milestone 9: WASM (in progress)

- [x] **Stage A: wasm as a program target** - `LANGOS=wasm` emits a
      wasm32-unknown-unknown triple; `test/run_wasm_suite.sh` runs the suite
      under node via `test/wasm_host.js` (a ~100-line host providing the libc
      surface): **168 passed, 0 failed, 21 skipped**. Effects are a clean
      compile error on this target (their lowering is target-specific inline
      asm; core wasm has no stack switching), and the suite skips on that
      diagnostic. Landing this surfaced a real ABI bug: closure signatures
      mismatched at every indirect call (`i8*` env in the definition, `i64` at
      the call, plus hand-rolled `fn(i64)` callers) - native targets tolerate
      that, wasm traps. The env param is now uniformly i64. Reader executables
      are now forced to target the build host (they run at compile time), so
      cross-targeting cannot produce unrunnable readers.
- [x] **Stage B: compiler.wasm** - the 478 KiB self-hosted compiler runs behind
      a JS virtual filesystem and real argv/environment shim. Its e2e test asks
      compiler.wasm to compile an in-memory source file to LLVM, links that IR
      to wasm, and runs the result. The live lab exposes editable Lang -> LLVM.
      wasm32 pointer relocations required pointer globals to use i32 storage and
      widen on load; `278_wasm_global_pointer` guards initialization + assignment.
- [x] **Stage C1: executable direct wasm** - `codegen_wasm.lang` emits binary
      modules itself: functions, i64/bool locals, arithmetic, calls, `if`,
      and `while`. The browser lab now does source → wasm → `main()` with no
      LLVM or server hop; the first e2e result is a 133-byte module.
- [x] **Stage C2: reader-capable direct wasm** - writable strings, pointer
      loads/stores, globals, host imports, structs, lexical shadowing, and
      reachability pruning are enough to run `std/tok.lang` + `std/ast.lang`.
      The browser lab compiles an editable reader to wasm, runs it to obtain
      shared AST, compiles that AST to a second wasm module, then runs `main()`.
- [ ] **Stage C3: reader-driven backend breadth** - generated `#parser{}` readers
      now run in the browser, and Forth drove nested/labeled loop control plus
      narrow integer locals. Add arrays, function pointers, aggregates by value,
      and floats only as useful readers demand them. Keep every unsupported
      construct diagnostic rather than emitting invalid modules.
- [x] **Demo site LIVE: https://ehrlich.dev/lang/** - `web/`: compiler.wasm lab, fib, ASCII
      mandelbrot, and the FOUR-language polyglot (`example/polyglot_wasm.lang`,
      flow sits out) precompiled to wasm, run client-side by `web/host.js`.
      `web/deploy.sh` deploys (pareto-pattern VPS); the `lang.ehrlich.dev`
      vhost and Cloudflare DNS are live. Stage C2 is the editable reader +
      source → runnable wasm lab.
- [x] **Retire the Mandelbrot workarounds** - LLVM expression typing now follows
      literals, casts, groups, calls, and both sides of nested binary trees;
      float reassignment stores through the declared target type; `a[i] = x`
      narrows i64 values to small array elements. Guarded by
      `261_float_composed` and `252_array_narrow_assignment` on native and wasm.

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

**Solid (native and wasm suites passing):**
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
- Error messages (some errors leak to codegen)
- Negative diagnostics beyond the five guarded invalid-source cases
- No struct literals

---

## Broken windows

### Fixed 2026-08-02

- **A compile that reported an error still wrote its output and exited 0.**
  `cg_had_error` was set in fifteen places — reader not found / returned nil /
  returned no output / returned invalid AST, unknown struct field, unknown enum
  variant in a `match` pattern, non-public access, closure/fn type mismatch —
  and **read in none**. Every one of those diagnostics scrolled past and the
  build succeeded with wrong code. Both backends now check it before writing and
  exit 1. The LLVM backend's reader-no-output site wasn't even setting the flag;
  it does now. Found while making minipy refuse to emit a program after a syntax
  error, which surfaced as `error: reader 'minipy' returned no output` followed
  by a successful build. Guarded by `compile_error_is_fatal` in
  `test/run_llvm_suite.sh` — the suite's first negative test.

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

- **Returning a struct by value returns a pointer to the callee's dead frame.**
  It works today because the caller copies out of it immediately, but the value
  is only valid until something else uses that stack. Not reachable from any
  shipped code.

---

## Deferred: Polish

These are nice-to-have but don't block the forge vision.

### Friction log (from an external user, 2026-08-08)

Fixed: platform auto-detection (LANGOS/LANGBE now default from the OS layer
baked into the binary), builds no longer dirty `src/version_info.lang` (now
generated into `out/`), `out/lang` vs `out/lang_next` documented in README,
`// expect:` and defined/undefined behavior documented in LANG.md.

Still open:
- **`--keyword-map`** - retheme keywords without patching the lexer. Niche
  (requested by a language-mutation experiment); the honest answer may be
  "keywords are hardcoded in std/tok.lang, patch it".

### Fixed 2026-08-08

- **Reader authorship now has a copyable front door.** `docs/READERS.md` explains
  the source-text-to-AST contract, recursive expansion, inline and whole-file
  use, and standalone compiler generation. `example/tiny/` is a 20-line reader
  with one input file; the suite builds it both as a macro and as a compiler.
- **Reader caches now notice source edits.** Cache validation compares the
  deterministic generated wrapper by content and checks direct dependency
  mtimes, in addition to compiler/stdlib mtimes. This also works when an edit
  lands in the same one-second timestamp tick. `reader_cache_refresh_e2e`
  compiles, rewrites, and recompiles one reader against the same cache.
- **LLVM standalone compiler generation works again.** Generated compilers now
  provide composition/module stubs, and codegen no longer borrows raw-array
  helpers from `ast_emit`, which is absent from small standalone readers.
  `compiler_compiler_e2e` proves lang → tiny compiler → tiny source → program.
- **The first real negative suite now guards five invalid builds.** LLVM
  codegen diagnoses undefined identifiers and non-void functions that can fall
  through, and now matches x86's rejection of a capturing lambda stored in a
  plain `fn` slot (the calling conventions differ). All three return nonzero.
- **Narrow integer casts are real i64 expressions.** LLVM truncates to the
  requested width, then sign- or zero-extends back to lang's all-i64 value
  representation. Chained casts and arithmetic no longer fail verification.
- **Invalid loop control is a compile error.** LLVM now rejects unlabeled or
  mislabeled `break`/`continue` when no enclosing loop matches, like x86 does.
- **`lang run` closes the first-run loop.** It compiles, links, executes, passes
  through stdout and the program's status, and removes its PID-scoped temporary
  files. `cli_run_e2e` exercises it through the tiny reader.
- **`--dump-tokens` exposes the lexer.** It prints locations, token kinds, and
  lexemes for one or more raw source files without parsing or compiling them;
  float token names are no longer reported as `UNKNOWN`.
- **CLI option errors fail at the option.** Long flags require exact matches;
  unknown options and missing `-o`, `-c`, or `-r` values now explain the
  invocation error instead of being misread as source filenames.

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
- 198/198 checks passing (includes negative, reader, run, and compiler-composition coverage)

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
