# 0023: Three Languages, One Binary

**Date:** 2026-05-31

## Summary

The forge thesis finally has its artifact. `example/polyglot.lang` compiles **three different real languages into one native binary**, calling each other directly at the machine level — no FFI, no interpreter, no runtime glue:

- **C** (`#c{...}`) — imperative trial division
- **minilisp** (`#minilisp{...}`) — a real Lisp: closures, `let`, `quote`, first-class cons lists
- **flow** (`#flow{...}`) — a coroutine DSL: generators that suspend and resume, lowered to algebraic effects

Each is a *reader* — a syntax plugin that parses its own surface syntax and emits lang AST. The kernel compiles whatever any reader emits. Same AST → same calling convention → they just call each other.

## The showpiece

A prime-sieve pipeline where each language does its idiomatic job:

```
=== prime pipeline: flow -> C -> Lisp ===

primes <= 30 (Lisp list) = (29 23 19 17 13 11 7 5 3 2)
count (Lisp ml_len)      = 10
sum   (Lisp ml_sum)      = 129
count (flow count_primes)= 10

POLYGLOT PASS
```

flow's `gen primes(n)` coroutine streams primes, asking C's `c_is_prime` about each candidate and suspending between hits. Its driver conses each (boxed) prime onto a real Lisp list. minilisp's `ml_sum`/`ml_len` fold that list. Three paradigms — imperative, coroutine-effectful, functional — meeting at the i64 ABI.

## How little the kernel changed

The striking thing: **almost none of this touched the compiler.** The kernel's S-expression vocabulary was already rich enough — `lambda`, `let`, `match`, `perform`/`handle`/`resume`, value-returning `block_expr`. The readers are pure reader-toolkit work: parse with `#parser{}`, emit with `std/ast.lang`.

- **minilisp** (351-line reader + 204-line runtime): zero kernel changes. Every Lisp value is an i64 that's secretly a `*LispObj` pointer; the runtime exposes an all-i64 interface, and cross-language calls just marshal — `lisp_int(x)` in, `lisp_to_int(x)` out. Boxing as an ABI.
- **C** (839-line reader): a large subset — all control flow, every operator, structs, pointers, arrays, enums, switch, ternary. One tiny tokenizer change (to lex `?` and `~`); everything else reader-only.
- **flow** (384-line reader + an 18-line runtime that declares one effect): built entirely on the existing effect machinery. A `gen` lowers to a function that `perform`s `Yield`; a `for x in g(...)` driver lowers to a `handle` that resumes the generator after each value.

## Bidirectional flow

The latest addition: flow's `yield` is now an *expression*. `var add = yield acc;` — the value of `yield` is whatever the driver sends back with `send`. That makes flow a real coroutine, not just a generator: the values it produces depend on what you feed it. A `running_sum` that yields its total and receives the next addend proves it — send 1,2,3 and it emits partial sums 0,1,3,6; send 0 every time and it stays flat. No kernel change: the effect substrate already threads `resume k(v)` back as the result of `perform`.

## Metrics

- **177/177** LLVM tests, including four reader end-to-end guards (minilisp, C, flow, polyglot)
- Kernel changes for the whole reader-authorship era: one tokenizer addition, one effect-label bugfix

## Lessons

1. **The subset was always a subset of effort, not capability.** The kernel could express closures, effects, and sum types long before any reader used them. "Capturing a language" turned out to mean writing a reader, not extending the compiler.

2. **Boxing is an ABI.** Representing every dynamic value as an i64-that's-really-a-pointer lets a functional language with first-class lists call — and be called by — raw imperative C, marshalling at the boundary.

3. **Effects are enough for coroutines.** Generators, suspension, resumption, a bidirectional channel — all of it falls out of `perform`/`handle`/`resume`. flow needed zero new kernel features.

4. **The honest claim is the narrow one.** Not "capture any language" — that oversells. The real, rare property is: *compose any syntax at the ABI level in one native binary.*
