# 0005: Stdlib, Structs, and Macro Design

*December 2024*

## What Happened

Three things landed in quick succession:

### Phase 1.5: Real Stdlib

Added actual data structures to std/core.lang:
- `malloc()` / `free()` - free-list allocator that actually reuses memory
- `vec_*` - dynamic array (push, get, set, len)
- `map_*` - hash map with string keys
- `str_concat()` / `str_dup()` - string utilities

The compiler now uses vec for the token list instead of a fixed buffer. Feels real.

### Phase 1.6: Structs Work

Structs are no longer just syntax - they're functional:
- Field access works: `p.x`
- Pointer-to-struct access works: `ptr.field` (auto-deref)
- Converted Token to a real struct (was manual offset math)

The compiler bootstraps with structs. Fixed point verified.

### Phase 2: Macro Design

Spent a while exploring the metaprogramming design space. Looked at Lisp, Racket, Zig, Rust, Terra, Julia, MetaOCaml, Forth, etc.

Landed on a simple proposal:
- `${ expr }` - quote (capture code as AST)
- `$name` - unquote (splice AST into quote)
- `macro name(args) { }` - compile-time code transformer

The `$` sigil is clean and unused. Reserved backtick for future multi-line strings.

## How It Feels

The language is starting to feel like a real tool. Writing `p.x = 42` instead of `*(p + 8) = 42` is a small thing, but it adds up.

The macro design conversation was fun. Started with too many options, narrowed down to something simple. The user's "language's language" vision (syntax as a swappable module) is ambitious - that's Phase 3 territory. For now, quote/unquote macros are enough.

## What's Next

Implement Phase 2:
1. AST introspection functions
2. Quote/unquote parsing
3. Macro definitions
4. Compile-time interpreter
5. Macro expansion

Then we can write `debug(x + y)` and have it print "x + y = 42". That's the hello world of metaprogramming.
