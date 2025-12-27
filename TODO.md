# language - TODO

## Vision

**A self-hosted compiler compiler with universal semantics.**

The AST is the language. Syntax is a plugin. Effects unify control flow.

---

## Milestones

1. ✓ Self-hosting compiler (x86 fixed point)
2. ✓ Reader macro infrastructure (`#parser{}`, `#lisp{}`)
3. ✓ Language polish (break/continue, bitwise ops, char literals)
4. → **AST 2.0: Universal Semantics** ← CURRENT
5. → Kernel/reader split (lang as a reader)
6. → Multiple backends (WASM, LLVM IR)

---

## Current Focus: AST 2.0 Implementation

See `designs/ast_as_language.md` for the complete design.

### Phase 1: Foundation (Current → Layer 1 stable)

| Task | File | Status |
|------|------|--------|
| Add `let` expression binding | parser.lang, codegen.lang | DONE |
| Add explicit `assign` node | parser.lang, codegen.lang | DONE |
| Add `TYPE_FUNC` to type system | parser.lang, codegen.lang | DONE |
| Parse `fn(T) R` type syntax | parser.lang | DONE |
| Verify indirect calls work | codegen.lang:1800+ | DONE |
| Test function pointers (`&func`) | test/ | DONE |

### Phase 2: First-Class Functions

| Task | File | Status |
|------|------|--------|
| `NODE_LAMBDA_EXPR` node type | parser.lang:32 | DONE |
| Parse lambda `fn(x i64) i64 { body }` | parser.lang:1980+ | DONE |
| Lambda codegen (no captures) | codegen.lang:2684+ | DONE |

### Phase 3: Closures

| Task | File | Status |
|------|------|--------|
| Closure struct generation | codegen.lang | TODO |
| Capture analysis pass | codegen.lang | TODO |
| Environment passing convention | codegen.lang:2287+ | TODO |

### Phase 4: Sum Types

| Task | File | Status |
|------|------|--------|
| Parse `enum Name { V1, V2(T) }` | parser.lang | TODO |
| Enum registry | codegen.lang:315+ | TODO |
| Tagged union layout `[tag:8][payload:N]` | codegen.lang | TODO |
| Parse `match expr { ... }` | parser.lang | TODO |
| Match → if/else tree compilation | codegen.lang | TODO |

### Phase 5: Algebraic Effects

| Task | File | Status |
|------|------|--------|
| Parse `effect` declarations | parser.lang | TODO |
| Parse `perform Effect(args)` | parser.lang | TODO |
| Parse `handle { } with { }` | parser.lang | TODO |
| **Exceptions (no resume)** | codegen.lang | TODO |
| State machine transform | codegen.lang | TODO |
| `resume k(value)` support | codegen.lang | TODO |

### Phase 6: Kernel Split

| Task | File | Status |
|------|------|--------|
| S-expression parser | kernel/sexpr.lang | TODO |
| AST validation | kernel/ast.lang | TODO |
| Extract lang_reader | readers/lang/ | TODO |
| Verify fixed point | Makefile | TODO |

**Open Question: Parser Unification**

Should `parser.lang` (handwritten recursive descent) unify with `#parser{}` (parser generator)?

The vision: lang's syntax defined in parser DSL, not handwritten. This would mean:
- `lang.grammar` defines lang syntax using `#parser{}` grammar notation
- Parser generator produces `lang_reader.lang` (or equivalent)
- Handwritten `src/parser.lang` becomes generated/obsolete
- True "syntax as data" - grammar IS the specification

Implications:
- Parser generator must be powerful enough (precedence, error recovery)
- Bootstrap: need handwritten parser to compile first parser generator
- See `designs/self_defining_syntax.md` for the full vision

---

## Pre-Flight Checks (Before Phase 1)

- [x] Verify stack frames can exceed 4KB (dynamic stack sizing)
- [x] Test nested structs `struct A { b B; }`
- [x] Test storing function address `var f = &myfunc` (function registry)
- [x] Test indirect call via pointer

---

## Code Quality Debt

| Issue | Priority | Status |
|-------|----------|--------|
| Add `const` keyword for compile-time constants | Medium | TODO |
| Magic PNODE numbers in lisp.lang | Low | TODO |
| Reader cache invalidation | Low | TODO |

---

## Stdlib Gaps

| Item | Status |
|------|--------|
| `memcpy`, `memset` | TODO |
| `read_file` (returns string) | TODO |
| String builder polish | TODO |

---

## Backlog (Post 2.0)

- [ ] Floating point (f32, f64)
- [ ] Struct literals `Point{x: 1, y: 2}`
- [ ] Pass/return structs by value
- [ ] Debug symbols (DWARF)
- [ ] Type aliases `type Fd = i64`
- [ ] `for` loop sugar
- [ ] Generics (monomorphization)

---

## Completed

### This Session
- [x] Pre-flight checks all passing
- [x] Dynamic stack sizing (deferred prologue generation)
- [x] Function registry for `&funcname` support
- [x] Centralized limits in `src/limits.lang`
- [x] `let` expression binding (`let x = val in body`)
- [x] Explicit `assign` node (AST 2.0: separates assignment statement from expression)
- [x] Function pointer calls via variables (indirect call codegen)
- [x] `TYPE_FUNC` type kind and `fn(T) R` type syntax
- [x] Comprehensive function pointer tests (133-137)
- [x] Lambda expressions `fn(x i64) i64 { body }` (Phase 2 complete)
- [x] Lambda test (138_lambda.lang)

### Previous Session
- [x] Comprehensive AST 2.0 design with algebraic effects
- [x] Research: LLM comparative analysis (Gemini, Claude, GPT)
- [x] Layer cake architecture design
- [x] Pluggable memory model design

### Previous
- [x] Self-hosting compiler (x86 fixed point)
- [x] Stdlib (malloc, vec, map)
- [x] Structs with field access
- [x] AST macros (quote/unquote)
- [x] Reader macros V2 (native executables)
- [x] `#parser{}` reader macro
- [x] `#lisp{}` with defun
- [x] Parsing toolkit (std/tok.lang, std/emit.lang)
- [x] Character literals `'A'`
- [x] Bitwise operators `& | ^ << >>`
- [x] Compound assignment `+= -= *= /=`
- [x] `break` / `continue` / labeled loops
- [x] >6 parameter support
- [x] Duplicate include handling
- [x] Argument count checking
- [x] Standalone compiler generation (`-c` flag)
