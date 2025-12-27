# Research Prompt: Universal AST as Semantic Substrate

## Context

We're designing a language system where the AST (Abstract Syntax Tree) is the true "language" and all surface syntaxes are readers that compile to this AST. This is analogous to how WASM provides "compile once, run anywhere" for execution - but we're aiming at "write in any syntax, express any semantics."

The architecture:
```
any syntax → [reader] → AST (S-expressions) → [kernel] → x86/WASM/LLVM
```

## The Core Question

WASM solved portable *execution*. We're trying to solve universal *expression*. But WASM deliberately chose a low abstraction level (stack machine, linear memory, explicit locals). We're choosing a high abstraction level (named variables, structured control, type system).

## Our Current AST (v1.0)

```lisp
;; Declarations
(func name (params...) ret-type body)
(struct name (fields...))
(var name type init?)

;; Statements
(if cond then else?)
(while cond body)
(return expr?)
(block stmts...)

;; Expressions
(binop op left right)    ; + - * / == < && ||
(unop op expr)           ; - ! * &
(call fn args...)
(field expr name)
(ident name)
(number val) (string val) (bool val) (nil)

;; Types
(type-base name)         ; i64 u8 bool void
(type-ptr elem)          ; *T
(type-array size elem)   ; [N]T
```

## What we've identified as missing for v2.0

- First-class functions / closures
- Sum types (enums/ADTs) + pattern matching
- Generics (via monomorphization)
- Exceptions (try/catch/throw)

## What we acknowledge as "probably needs different IR"

- Lazy evaluation (Haskell)
- Logic programming (Prolog)
- Actor concurrency (Erlang)
- Array primitives (APL/J)

---

## Research Questions

### 1. Semantic Dimensions Inventory

What are ALL the fundamental semantic dimensions that programming languages vary on? Consider:
- Evaluation strategy (strict/lazy/call-by-need)
- Memory model (manual/GC/linear/affine/region-based)
- Effect tracking (implicit/monadic/algebraic)
- Type features (polymorphism, variance, dependent types, HKT)
- Control abstraction (exceptions, continuations, coroutines, delimited control)
- Concurrency model (threads/actors/CSP/async-await)
- Module/visibility systems
- Metaprogramming (macros, reflection, staging)

For each dimension, assess: Can it be captured in a single unified AST, or does it fundamentally change the IR's structure?

### 2. The "Colored Functions" Problem

Some features create "bifurcation" - once you add async/await, you have sync and async functions that don't compose easily. Similarly:
- Lazy vs strict: can they interop in one AST?
- Pure vs effectful: does tracking this change the AST structure?
- Linear vs unrestricted: does linear logic require a different IR?

Is there a way to design the AST to gracefully handle these bifurcations, or are they fundamentally incompatible in one IR?

### 3. Comparison to Existing Universal IRs

Compare our approach to:

| System | Abstraction Level | What It Unifies |
|--------|-------------------|-----------------|
| **WASM** | Low (stack machine) | Execution across browsers/runtimes |
| **LLVM IR** | Low (SSA, explicit ops) | Backend optimization across targets |
| **GraalVM Truffle** | High (AST interp + PE) | Language interop via partial evaluation |
| **Racket** | High (syntax objects) | Syntax via macros, but Scheme core |
| **Nanopass** | Meta (IR per pass) | Compiler construction methodology |
| **Our AST** | High (typed AST) | Syntax freedom via readers |

What can we learn from each? What are their limitations that we should avoid?

### 4. The Expression Problem for IRs

The Expression Problem asks: can you add both new data types AND new operations without recompiling existing code?

For a universal AST:
- Can we add new AST node types without kernel changes?
- Can we add new backends without AST changes?
- Can readers define "extended AST" that the kernel doesn't understand natively?

Is there a design that allows the AST to be extensible without becoming incoherent?

### 5. Semantic Interoperability

If we want "cross-language interop is free" (mixing lang + lisp + python-like), what constraints does that impose?

- Must all languages agree on memory model? (GC vs manual)
- Must calling conventions match?
- What about different error handling (exceptions vs Result types)?
- Can a Haskell-style lazy function be called from strict code?

What's the minimal "semantic contract" that allows interop?

### 6. The Layer Cake Question

Is there a natural layering?

```
Layer 3: Domain-specific semantics (SQL, regex, shader)
Layer 2: High-level (closures, ADTs, effects)
Layer 1: C-level (our 1.0)
Layer 0: Machine-ish (WASM/LLVM-level)
```

Should the kernel understand all layers, or should higher layers compile down to lower layers via AST-to-AST transforms? (Nanopass style)

### 7. What WASM Got Right (and Wrong)

WASM succeeded because it:
- Chose a minimal, stable core
- Is verifiable in linear time
- Has clear security properties
- Is truly portable

But WASM also:
- Has no GC (added later, controversially)
- No closures (function references are limited)
- Awkward string handling
- No standard library

For a "universal frontend AST," what are the analogous design principles? What's the minimal stable core that captures the most semantics?

### 8. Theoretical Limits

Is there a theoretical result (perhaps from type theory or denotational semantics) that tells us:
- Can all computable functions be expressed in a finite, fixed AST grammar?
- Are some semantic features fundamentally incompatible in one IR?
- What's the minimal AST that's Turing-complete?
- What's the minimal AST that captures "mainstream language features"?

### 9. Practical Recommendations

Given our goal (universal syntax → one AST → multiple backends), recommend:
1. What should definitely be in the 1.0 AST?
2. What should definitely be deferred to 2.0+?
3. What should probably never be in this AST (needs different IR)?
4. Are there features we haven't considered that are critical?

### 10. Falsifiability

What would prove this approach wrong? What problems might emerge that show "one AST for all semantics" is fundamentally impossible or impractical?

---

## Requested Output Format

1. **Semantic Dimensions Table**: Comprehensive list of dimensions with assessment of AST-compatibility
2. **Comparative Analysis**: How existing systems handle the universal IR problem
3. **Design Recommendations**: Concrete suggestions for AST node additions/changes
4. **Risk Assessment**: What could go wrong, what are the hard limits
5. **References**: Academic papers, language designs, or implementations to study

---

## Meta-note

We're not asking "is this a good idea" - we're committed to the architecture. We're asking "given this architecture, how do we maximize semantic coverage while maintaining coherence?" Think of it as: if WASM is the "universal bytecode," we're trying to design the "universal AST" - one layer up in abstraction.
