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

### Phase 3: Closures ✓ (MVP)

| Task | File | Status |
|------|------|--------|
| Closure struct generation | codegen.lang:2872+ | DONE |
| Capture analysis pass | codegen.lang:375-505 | DONE |
| Environment passing convention | codegen.lang:3528+ | DONE |
| Compile-time safety check | codegen.lang:3246+ | DONE |
| Automatic closure calls | codegen.lang | DEFERRED |

**Status**: Closures work! Lambdas can capture outer scope variables. Requires manual calling convention (pass closure ptr as first arg via helper function). See `test/suite/139_closure.lang` and `test/stdlib/144_closure_basic.lang`.

**Safety Check**: Compiler now errors if you assign a capturing lambda to a `fn(T) R` variable. This prevents a crash where the closure struct would be executed as code. Non-capturing lambdas are still allowed with `fn(T) R`.

### Phase 3b: Closure Type ✓

Implemented type-level distinction between plain function pointers and closures:

```lang
// Plain function pointer - no captures allowed
var f fn(i64) i64 = &add;                    // OK
var f fn(i64) i64 = fn(x i64) { x + 1 };     // OK (no captures)
var f fn(i64) i64 = fn(x i64) { x + n };     // COMPILE ERROR

// Closure type - allows captures, automatic calling
var g closure(i64) i64 = fn(x i64) { x + n };  // OK
g(42);  // Compiler auto-passes closure struct as first arg
```

| Task | File | Status |
|------|------|--------|
| Parse `closure(T) R` type syntax | parser.lang | DONE |
| Add TYPE_CLOSURE kind | parser.lang | DONE |
| Closure type codegen | codegen.lang | DONE |
| Auto-wrap non-capturing lambda for closure type | codegen.lang | DONE |
| Test closure type | test/suite/189_closure_type.lang | DONE |

**Closure struct layout**: `[tag:8][fn_ptr:8][captures...]`
- tag=0: non-capturing (call fn_ptr directly)
- tag=1: capturing (pass struct as hidden first arg)

### Phase 4: Sum Types ✓

| Task | File | Status |
|------|------|--------|
| Parse `enum Name { V1, V2(T) }` | parser.lang | DONE |
| Enum registry | codegen.lang:400+ | DONE |
| Tagged union layout `[tag:8][payload:N]` | codegen.lang | DONE |
| Variant construction `Enum.Variant(x)` | codegen.lang:2028+ | DONE |
| Parse `match expr { ... }` | parser.lang | DONE |
| Match → if/else tree compilation | codegen.lang | DONE |

### Phase 5: Algebraic Effects (Exceptions MVP)

| Task | File | Status |
|------|------|--------|
| Parse `effect` declarations | parser.lang | DONE |
| Parse `perform Effect(args)` | parser.lang | DONE |
| Parse `handle { } with { }` | parser.lang | DONE |
| **Exceptions (no resume)** | codegen.lang | DONE |
| State machine transform | codegen.lang | TODO |
| `resume k(value)` support | codegen.lang | TODO |

**Status**: Basic exceptions work! `perform` jumps to handler, handler receives effect argument. No resume support yet (perform is a one-way jump). See `test/suite/188_effect_exception.lang`.

**Current Limitations**:
- Single handler at a time (no handler stack for nesting)
- No resume support (exceptions only, not full delimited continuations)
- Effects are not type-checked (any perform goes to active handler)

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
| ~~**POINTER ARITHMETIC BUG**~~ | ~~CRITICAL~~ | DONE |
| **TEST SUITE GAPS** | **HIGH** | TODO |
| Add `const` keyword for compile-time constants | Medium | TODO |
| Magic PNODE numbers in lisp.lang | Low | TODO |
| Reader cache invalidation | Low | TODO |

### HIGH: Test Suite Gaps

**Problem**: The test suite (test/suite/*.lang) is mostly happy-path tests. Edge cases, error conditions, and corner cases are underrepresented.

**Examples of missing test categories:**
- Integer overflow behavior
- Deeply nested expressions
- Large structs / arrays
- Boundary conditions (empty arrays, zero-length strings)
- Error recovery / malformed input
- Stress tests (many locals, deep recursion, large functions)
- Interaction tests (structs containing arrays containing pointers, etc.)

**Action**: Add 30-50 more targeted tests covering edge cases and interactions. Each bug found should spawn a regression test.

### ~~CRITICAL: Pointer Arithmetic Bug~~ (FIXED)

**Fixed**: Pointer arithmetic now correctly scales by element size. `*i64 + 1` adds 8 bytes.

- **Test**: `test/suite/143_ptr_arithmetic.lang`
- **Fix location**: `codegen.lang:1972-1997` (NODE_BINARY_EXPR for +/-)
- **Bootstrap note**: Existing code using `*u8` with manual byte offsets still works correctly

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
- [x] Phase 4 Sum Types complete (enum, match, pattern matching)
- [x] Pointer arithmetic fix (`*i64 + 1` now adds 8 bytes)
- [x] Pointer arithmetic test (143_ptr_arithmetic.lang)
- [x] Phase 3 Closures MVP (capture analysis, closure structs, env passing)
- [x] Closure test (test/stdlib/144_closure_basic.lang)
- [x] Phase 5 Exceptions MVP (effect/perform/handle, setjmp/longjmp style)
- [x] Exception test (test/suite/188_effect_exception.lang)
- [x] Phase 3b Closure Type (closure(T) R type, automatic calling)
- [x] Closure type test (test/suite/189_closure_type.lang)

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
