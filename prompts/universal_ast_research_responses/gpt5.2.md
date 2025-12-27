## 1) Semantic dimensions inventory (and whether one unified AST can carry them)

Key idea: many “semantic dimensions” *can* live in one high-level AST **if** you (a) make evaluation/effects/control *explicit* in the core, and (b) treat most surface features as **desugarings/elaborations** to a small set of orthogonal primitives (very Racket / nanopass). Where things get hard is when a feature’s *operational contract* changes (scheduler, memory model, backtracking/search), not merely its syntax.

### Semantic dimensions table

| Dimension                             | Common variations                                        |                        Can one AST capture it? | How to model it coherently                                                                                                                                                            | “Different IR?” trigger                                                                                                              |
| ------------------------------------- | -------------------------------------------------------- | ---------------------------------------------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| **Evaluation strategy**               | strict (CBV), lazy (CBN/CBNeed), mixed                   |  **Yes**, but not as a single implicit default | Make *thunks/force* explicit **or** elaborate to a calculus that factors eval order (e.g., CBPV) ([Birmingham CS][1])                                                                 | If laziness must be *ambient* and optimized globally without explicit thunks (whole-program demand analysis)                         |
| **Evaluation order**                  | left-to-right, unspecified, parallel                     |                                        **Yes** | Define AST evaluation order precisely (or make it explicit via sequencing/let)                                                                                                        | If you want “unspecified order” semantics for optimization freedom while preserving side effects                                     |
| **Binding & scope**                   | lexical/dynamic, hygiene                                 |                                     **Mostly** | Lexical scope is straightforward; hygiene is a *reader/macro* concern (syntax objects, scopes) ([Racket Documentation][2])                                                            | If you want dynamic scope as a *first-class* ambient mechanism (often best as an effect)                                             |
| **Control flow (local)**              | if/while/for, break/continue                             |                                        **Yes** | Structured control in AST; then lower to CFG/SSA later                                                                                                                                | N/A                                                                                                                                  |
| **Non-local control**                 | exceptions, early return, goto                           |                                        **Yes** | Model as **effects + handlers** (exceptions become one effect) ([Informatics Homepages Server][3])                                                                                    | If you need low-level UB-like “longjmp” behavior interleaving with optimizations                                                     |
| **Continuations / delimited control** | call/cc, shift/reset                                     |                **Yes**, but it’s a “big lever” | Put **delimited control** into the core or treat it as an effect with handler semantics (but type/effect gets subtle) ([Informatyka Wrocław][4])                                      | If backends can’t support stack capture/rewind efficiently (then you CPS/defunctionalize)                                            |
| **Coroutines / generators**           | yield, stackful/stackless                                |                                        **Yes** | Encode via delimited continuations or as an effect whose handler lowers to a state machine                                                                                            | If you require stackful coroutines across FFI in all targets                                                                         |
| **Async/await (“colored functions”)** | sync vs async                                            |                                        **Yes** | Treat “may suspend” as an **effect** (or continuation capability) and compile to state machines; effect polymorphism reduces bifurcation ([Informatics Homepages Server][3])          | If you demand zero-cost interop between blocking and async without an effect boundary                                                |
| **Effects discipline**                | implicit, monads, algebraic effects, effect typing       |                                        **Yes** | Choose a core story: **type-and-effect** + **handlers** is the most “unifying” lever for exceptions/async/nondet/state ([Informatics Homepages Server][3])                            | If you want to preserve a source language’s *specific* effect semantics (e.g., Haskell’s laziness + IO) without explicit elaboration |
| **Memory management**                 | manual, GC, refcount, linear/affine, region              |                                  **Partially** | Put a *single runtime contract* in the kernel (e.g., tracing GC + FFI escape hatches), or make ownership an effect/typing discipline; don’t pretend you can “just mix” w/o boundaries | If two components must share objects but disagree on ownership/collector (needs ABI/runtime boundary)                                |
| **Linearity / ownership**             | unrestricted vs affine vs linear                         |                             **Yes (as types)** | Keep AST mostly unchanged; enforce via type system + borrow/permission analysis; lowering chooses moves/copies/drops ([arXiv][5])                                                     | If you want *runtime-visible* linear resources with guaranteed destruction points across all backends                                |
| **Data types**                        | products, sums/ADTs, objects, traits                     |                                        **Yes** | Add **constructors + match**; encode OO as records + vtables if desired                                                                                                               | If you require open-world dynamic dispatch with runtime method lookup as a primitive                                                 |
| **Polymorphism**                      | parametric (System F), ad-hoc (typeclasses/traits), HKTs |                            **Yes**, but staged | Keep AST generic; elaboration inserts dictionaries/vtables or monomorphizes                                                                                                           | If you need dependent types with computation at type level that must be preserved into runtime IR                                    |
| **Dependent typing**                  | full dependent types, refinement                         |        **Yes in principle**, heavy in practice | Treat as compile-time elaboration + proof erasure; kernel must decide what’s erased vs reified                                                                                        | If you require runtime proof objects / equality reflection widely                                                                    |
| **Pattern matching**                  | ML-style, GADTs, view patterns                           |                                        **Yes** | Core `match` over sum types; elaborate fancy patterns                                                                                                                                 | If your match semantics include Prolog-like unification/backtracking                                                                 |
| **Nondeterminism / logic**            | backtracking search, unification                         | **Can be encoded**, but ergonomics/perf suffer | Algebraic effect `choose/fail` + handler gives semantics; performance may require dedicated engine                                                                                    | When search is *the* core model (indexing, unification vars, occurs check)                                                           |
| **Concurrency model**                 | OS threads, green threads, actors, CSP, dataflow         |                  **Only with a runtime model** | Represent “spawn/send/recv/await” as effects; kernel chooses scheduler + semantics                                                                                                    | If you want Erlang-style “let it crash” + per-process heaps + mailbox ordering as a primitive guarantee everywhere                   |
| **Memory model (concurrency)**        | SC, TSO, relaxed atomics                                 |                                       **Hard** | Needs explicit atomic ops + fences + well-defined compilation mapping                                                                                                                 | If you promise language-level DRF/SC guarantees that targets can’t preserve without fences                                           |
| **Modules / visibility**              | ML modules, packages, namespaces                         |                            **Yes (front-end)** | Usually erased after name resolution + linking metadata                                                                                                                               | If modules carry runtime semantics (dynamic loading with reflection contracts)                                                       |
| **Reflection / runtime meta**         | eval, reflection, reification                            |                         **Yes**, but dangerous | Treat as capability/effect; sandboxing matters                                                                                                                                        | If you require “eval” with full ambient authority in a multi-tenant setting                                                          |
| **Macros / staging**                  | hygienic macros, multi-stage                             |          **Yes**, but mostly *before* AST core | Racket-style: rich syntax objects + expansion to a small core ([Racket Documentation][2])                                                                                             | If macros must run *at runtime* and generate code dynamically (then it’s reflection/eval)                                            |
| **FFI & ABI**                         | C ABI, calling conventions                               |                    **Yes**, but boundary-heavy | Model as primitives with explicit ownership + error + representation rules                                                                                                            | If you want seamless sharing of managed objects with native code without pinning/marshalling costs                                   |
| **Numeric tower / arrays**            | bignums, SIMD, APL arrays                                |          **Yes**, but often best as intrinsics | Keep as library + compiler-recognized intrinsics; lower to vector/loop nests                                                                                                          | If array fusion / rank polymorphism is central (APL/J)—may want specialized IR for optimization                                      |

**Takeaway:** a single AST can “cover” most dimensions if the *kernel’s core calculus* is chosen to make evaluation/effects/control explicit and orthogonal; otherwise you’ll get semantic corner explosions.

---

## 2) The “colored functions” family: making bifurcations compositional

### The pattern behind “coloring”

Async, laziness, purity/effects, linearity: each introduces a *capability* that some functions have and others don’t. Coloring becomes painful when that capability is **not abstractable**.

### A unifying design move: “capabilities as effects”

If your AST has a first-class notion of **effects** and **handlers**, then:

* **Exceptions** are an effect (`raise`) handled by `try/catch`.
* **Async suspension** is an effect (`suspend/await`) handled by an async runtime that lowers to a state machine.
* **Nondeterminism** is an effect (`choose/fail`) handled by backtracking or search.
* Even **dynamic scoping** can be an effect (`get/set` for implicit parameters).

This is exactly what algebraic effects + handlers are designed for. ([Informatics Homepages Server][3])
It doesn’t make every interop “free,” but it makes the *semantic distinctions explicit and typeable*, so you can push boundaries into a small number of well-defined constructs instead of infecting the whole language.

### Strict vs lazy interop

You can interop in one AST by:

* Representing lazy values as explicit thunks and forcing at boundaries, **or**
* Choosing a core calculus (CBPV) where “values” vs “computations” are distinct and CBV/CBN become embeddings. ([Birmingham CS][1])

If you try to keep laziness *implicit* while also allowing eager mutation/effects, you’ll be forced into a lot of global reasoning (demand/strictness analysis) and “surprises” at FFI boundaries.

### Linear vs unrestricted interop

Linearity is *primarily* a typing/analysis discipline; you don’t need a different AST so long as:

* Move/copy/drop are explicit (or inserted during elaboration),
* Borrow scopes are representable, and
* FFI boundaries are explicit about ownership transfer.
  Rust’s ownership story is a good reference for the analysis side, even if you don’t copy Rust’s surface rules. ([arXiv][5])

---

## 3) Comparison to existing “universal IR” approaches

### WASM

WASM picked a small, stable, verifiable core with structured control and explicit state; the spec calls out goals like fast/safe/portable semantics and validation. ([W3C][6])
The *design* repo emphasizes structured stack/control to simplify one-pass verification. ([GitHub][7])

**Lesson for a universal AST:** you’ll want analogous properties:

* A minimal core with *fully specified semantics*,
* A fast validator (well-formedness + typing + effect checks),
* A clear security story (what capabilities exist, how they’re bounded).

### LLVM IR

LLVM IR unifies *backends*, not semantics: SSA form, explicit memory ops, and a fairly “machine-ish” model. That’s exactly why it’s good for optimization and retargeting, but it’s hostile to high-level semantic preservation (closures/effects/laziness don’t exist “as such”).

**Lesson:** keep your high-level AST as a **front-end semantic IR**, but expect to lower into more specialized IRs (ANF/CPS/SSA/CFG) for optimization and codegen.

### GraalVM Truffle

Truffle explicitly builds language implementations as **AST interpreters**, and Graal uses partial evaluation/JIT to optimize them. ([GraalVM][8])
Truffle also has a defined interop protocol for cross-language values/objects. ([GraalVM][9])

**Lesson:** “universal AST” alone doesn’t buy you interop; you need:

* A value model (boxing, identity, mutability),
* A capability model (IO, threads, reflection),
* A boundary protocol (errors, ownership, calling).

### Racket

Racket’s macro system expands rich surface forms into a relatively small set of core constructs; syntax objects are central to representing source with scopes. ([Racket Documentation][2])

**Lesson:** treat readers + macro-expansion as a first-class “semantic elaboration” stage. Your kernel should not need to understand every surface feature—only the small core that everything expands into.

### Nanopass

Nanopass is the methodology you’re circling: many small AST-to-AST passes, each simplifying or making one concern explicit; it’s used in serious compilers. ([Andy Keep][10])

**Lesson:** don’t aim for “one AST to rule them all” at the *same abstraction level*. Aim for a **family** of increasingly explicit ASTs, with a stable *core* grammar and disciplined elaborations.

---

## 4) The “expression problem” for IRs (extensibility without incoherence)

Wadler’s framing is still the right mental model: you want to add new “cases” (node forms) and new “operations” (passes/backends) modularly. ([Informatics Homepages Server][11])

In compilers, the pragmatic way to “solve” it is architectural, not magical:

1. **Freeze a small Core AST** that the kernel/backends guarantee to understand.
2. Allow “extended AST” only in *front-end space*, with a requirement: **it must elaborate to Core** (macro-like).
3. Version the Core and keep it boring (like WASM did).

If you want stronger modularity, you can borrow from typed extensibility patterns (tagless-final/object algebras/data-types-à-la-carte), but the *kernel* still must ultimately process a finite set of core constructs—otherwise optimization/codegen becomes unbounded.

**A good rule:**

> *Readers may invent syntax freely; the kernel may only accept semantics that have a deterministic elaboration into the core calculus.*

---

## 5) Semantic interoperability: the minimal contract for “mix any language”

“Interop is free” is only true if languages agree on (or can adapt to) a shared contract:

### Minimal semantic contract

1. **Value representation model**

   * boxed vs unboxed, pointer identity, numeric ranges, string/array layout.
2. **Memory management boundary**

   * who owns what, lifetime rules, GC visibility/pinning, borrowing/aliasing.
3. **Effect/capability model**

   * what IO/threading/reflection is allowed, and how it’s mediated.
4. **Error model**

   * exceptions vs result values: pick *one* at the ABI boundary (or define a universal sum like `Ok(v) | Err(e)`), and provide adapters.
5. **Calling convention**

   * arity, varargs, tail calls, stack growth, re-entrancy.

Truffle’s polyglot interop works because it defines a protocol for foreign values and how they’re accessed/called, not because all languages “mean the same thing.” ([GraalVM][9])

### Lazy called from strict?

Yes, if laziness is explicit at the boundary (thunk), or your core calculus factors computations/values (CBPV). ([Birmingham CS][1])
But “transparent” interop is not free: forcing points and exception/effect boundaries must be explicit somewhere.

---

## 6) The layer-cake: what the kernel should understand

Your instinct is right: **layering wins**.

A coherent plan is:

* **Core calculus (Kernel IR):** small, explicit, orthogonal constructs.
* **Elaboration layers:** closures/ADTs/exceptions/async/etc. lower into the core via nanopass-style transforms. ([Andy Keep][10])
* **Optimization-lowering IRs:** ANF/CPS/SSA as needed for backends; ANF is a common bridge that makes evaluation order explicit and simplifies compilation. ([users.soe.ucsc.edu][12])

If you want one “semantic substrate,” make *that* the **Core**, and treat everything else as systematic elaboration.

---

## 7) “What WASM got right” translated to a universal frontend AST

WASM’s success pattern maps surprisingly well:

* **Minimal, stable core**: keep the kernel’s accepted AST small and boring.
* **Fast validation**: define type/effect rules so checking is structural and predictable (WASM’s validation story is central). ([W3C][6])
* **Security/capabilities**: define what “unsafe” means in your world and make it explicit (imports/FFI/eval/IO should be capabilities, not ambient).
* **Portability**: avoid semantics that depend on unspecified evaluation order, UB, or target-specific behavior.

---

## 8) Theoretical limits (what you can and can’t hope for)

* **Turing completeness with a finite grammar:** trivially yes (lambda calculus, SK, etc.). The barrier isn’t expressibility.
* **“All semantics in one fixed IR”:** the hard part is *observational equivalence and cost models*. Felleisen’s work on expressiveness formalizes that some “features” cannot be encoded as mere macros without changing observable behavior under some notion of observation. ([CCS NEU][13])
  Translation: you can encode a lot, but you may not preserve the semantics (or performance/space behavior) that programmers care about.
* **Incompatibility usually appears as runtime contract mismatch:** scheduling, memory model, and nondeterministic search are where “one IR” tends to become either too abstract (inefficient) or too specific (not universal).

---

## 9) Practical recommendations for *your* AST

### (A) What should be in “1.0 Core” (even if readers sugar over it)

Your current 1.0 is missing a few “compiler spine” essentials if it’s meant to be a true substrate:

* **Lexical binding/sequencing**: a `let` / `letrec` (or `var` usable as expression-binding), and a sequencing form (`seq` or block-as-expression).
* **Assignment + memory ops**: if you intend C-like expressivity, you need explicit `set!` and a defined memory model for `*`/`&` (right now you have deref/address-of operators but no store).
* **Function values**: `lambda` as an expression and function types.
* **Sum types + match**: even if surface languages use `switch`, exceptions, etc.
* **A single *effect story*** in the core:

  * Either: built-in exceptions/async/etc.
  * Or (strongly recommended): **algebraic effects + handlers** as the *one* general mechanism; then exceptions/async become libraries + elaborations. ([Informatics Homepages Server][3])

### (B) What should be “2.0 elaborations” (not kernel primitives)

* Generics (monomorphization/dictionaries are elaboration strategies).
* Pattern-matching conveniences (guards, nested patterns, etc.).
* Async/await syntax (lower to effects/handlers + state machine).
* Many OO features (traits/interfaces/dynamic dispatch) as elaborations to records + vtables/dicts.

### (C) What probably should *not* be in the core AST

* Ambient laziness as a default (prefer explicit thunks or CBPV-style factoring).
* Prolog-style unification/search as a primitive (can be an effect, but performance pushes you toward a specialized engine).
* APL/J rank-polymorphic array semantics as a primitive unless arrays are a flagship goal (optimization wants specialized IR).

### (D) One concrete “Core v2” shape that tends to scale

If you want maximum semantic coverage with coherence, a strong candidate core looks like:

* **Typed lambda + letrec**
* **Products + sums + match**
* **Explicit sequencing + mutation primitives**
* **Algebraic effects + handlers** (to unify exceptions/async/nondet/state)
* Optional: **delimited control** if you want a very small *lowering target* for async/coroutines

Then:

* Elaborate rich syntax → Core
* Normalize Core to ANF (or CPS) before codegen ([users.soe.ucsc.edu][12])

---

## 10) Falsifiability: what would prove “one universal AST” impractical

Things that would force a rethink (or a split into multiple cores):

1. **Interop forces multiple runtimes anyway**
   If you repeatedly hit “this language needs its own scheduler/GC/value model,” then the “one kernel” becomes a thin FFI layer—not a semantic substrate.

2. **Validation becomes non-local**
   If type/effect checking requires whole-program reasoning (e.g., implicit laziness + effects + optimization freedom), you lose the WASM-like “linear-time checkability” advantage.

3. **Optimization collapses under semantic generality**
   If your core keeps too much implicit behavior (evaluation order, aliasing, exceptions), every backend either becomes conservative (slow) or unsound. That’s often the death spiral for “universal high-level IR.”

4. **Semantic extensions become de facto new languages**
   If “extended AST nodes” proliferate and no longer reliably elaborate to a small core, the kernel/backends will fragment.

---

## References to study (high signal)

* **Algebraic effects & handlers:** Plotkin & Pretnar; effect handlers overview ([Informatics Homepages Server][3])
* **CBPV (bridges CBV/CBN; helpful for strict/lazy interop):** Levy ([Birmingham CS][1])
* **ANF as a compilation IR bridging source → low level:** Flanagan et al. ([users.soe.ucsc.edu][12])
* **Nanopass methodology:** Keep & Dybvig ([Andy Keep][10])
* **Racket macro expansion + syntax objects:** Racket guide ([Racket Documentation][2])
* **Truffle (AST interpreters + PE; interop protocol):** GraalVM docs ([GraalVM][8])
* **WASM design/validation principles (analog for your kernel):** W3C spec + design rationale ([W3C][6])
* **Expression problem:** Wadler ([Informatics Homepages Server][11])
* **Expressiveness limits / macro-encodability:** Felleisen ([CCS NEU][13])

If you want, I can sketch an explicit **Core v2 grammar** (S-expr forms + type/effect annotations) that bakes in: `lambda/letrec`, `sum/match`, and `effect/handle`, and show how `try/catch`, `async/await`, and `generators` compile into it.

[1]: https://www.cs.bham.ac.uk/~pbl/papers/hosc05.pdf?utm_source=chatgpt.com "Call-By-Push-Value - School of Computer Science"
[2]: https://docs.racket-lang.org/guide/stx-obj.html?utm_source=chatgpt.com "16.2.1 Syntax Objects"
[3]: https://homepages.inf.ed.ac.uk/gdp/publications/Effect_Handlers.pdf?utm_source=chatgpt.com "Handlers of Algebraic Effects"
[4]: https://ii.uni.wroc.pl/~dabi/publications/ICFP11/materzok-biernacki-icfp11.pdf?utm_source=chatgpt.com "Subtyping Delimited Continuations"
[5]: https://arxiv.org/abs/2309.04134?utm_source=chatgpt.com "A Grounded Conceptual Model for Ownership Types in Rust"
[6]: https://www.w3.org/TR/wasm-core-1/?utm_source=chatgpt.com "WebAssembly Core Specification"
[7]: https://github.com/WebAssembly/design/blob/main/Rationale.md?utm_source=chatgpt.com "design/Rationale.md at main · WebAssembly/design"
[8]: https://www.graalvm.org/latest/graalvm-as-a-platform/language-implementation-framework/?utm_source=chatgpt.com "Truffle Language Implementation Framework"
[9]: https://www.graalvm.org/jdk22/reference-manual/java-on-truffle/interoperability/?utm_source=chatgpt.com "Interoperability with Truffle Languages"
[10]: https://andykeep.com/pubs/np-preprint.pdf?utm_source=chatgpt.com "A Nanopass Framework for Commercial Compiler ..."
[11]: https://homepages.inf.ed.ac.uk/wadler/papers/expression/expression.txt?utm_source=chatgpt.com "Expression Problem Philip Wadler"
[12]: https://users.soe.ucsc.edu/~cormac/papers/pldi93.pdf?utm_source=chatgpt.com "The Essence of Compiling with Continuations Abstract 1 ..."
[13]: https://www2.ccs.neu.edu/racket/pubs/scp91-felleisen.pdf?utm_source=chatgpt.com "On the Expressive Power of Programming Languages"
