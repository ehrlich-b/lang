# Reader Macros V2: Lang as a Language Forge

**Vision**: Racket-style power with Zig-style minimalism. For fun.

---

## The Two Inspirations

### Racket: Maximum Power

[Racket](https://racket-lang.org/) is the gold standard for language-oriented programming:
- `#lang` invokes arbitrary parsers
- Reader extensions via `#reader`
- Syntax objects preserve source locations and lexical context
- Full language semantics can be overridden
- [Beautiful Racket](https://beautifulracket.com/) shows what's possible

**Tradeoff**: Substantial runtime. Every binary includes Racket's VM.

### Zig: Maximum Minimalism

[Zig](https://ziglang.org/) achieves metaprogramming through `comptime`:
- Same language at compile-time and runtime
- Types are first-class values
- No runtime, no GC
- [Hermetic and reproducible](https://kristoff.it/blog/what-is-zig-comptime/) - no I/O at comptime

**Tradeoff**: Limited metaprogramming. Can't define new syntax. No reader macros.

### Lang: Both

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│   Racket-style reader macros  +  Zig-style bare-metal output    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## The Design

### The Pipeline

```
Input Text
    ↓
┌─────────────────┐
│   TOKENIZER     │  lang_tokenize() or custom
└────────┬────────┘
         ↓
┌─────────────────┐
│     PARSER      │  combinators, BNF, or custom
└────────┬────────┘
         ↓
┌─────────────────┐
│   CODE GEN      │  emit_*() helpers or custom
└────────┬────────┘
         ↓
Lang source text → compiler → native
```

Every stage has a happy path. Every stage is replaceable.

### How Readers Work

1. **Readers are full lang programs** - compiled to native executables
2. **Readers output lang source text** - simple, debuggable
3. **Compiler parses the output** - reuses existing parser

```lang
reader lisp(text *u8) *u8 {
    var tokens *TokenStream = lang_tokenize(text);  // Lang's tokenizer!
    var result ParseResult = parse(sexp_parser(), tokens);
    return result.value;  // Lang source: "(1 + (2 * 3))"
}
```

### The Toolkit (std/)

**std/tok.lang** - Tokenizer
```lang
func lang_tokenize(text *u8) *TokenStream;  // Use lang's own lexer
func tok_next(t *Tokenizer) Token;
func tok_peek(t *Tokenizer) Token;
```

**std/parse.lang** - Parser Combinators
```lang
func p_token(kind i64) Parser;
func p_or(a Parser, b Parser) Parser;
func p_many(p Parser) Parser;
func p_seq(parsers *Vec) Parser;
func p_map(p Parser, f func(*u8) *u8) Parser;
```

**std/emit.lang** - Code Generation
```lang
func emit_number(n i64) *u8;           // "42"
func emit_binop(l *u8, op *u8, r *u8) *u8;  // "(l op r)"
func emit_call(fn *u8, args *Vec) *u8; // "fn(a, b)"
```

### Build Model

```
1. Compiler sees `reader lisp` declaration
   → Compiles to .lang-cache/readers/lisp

2. Compiler hits #lisp{(+ 1 2)}
   → Runs: .lang-cache/readers/lisp <<< "(+ 1 2)"
   → Gets: "(1 + 2)"
   → Parses as lang expression
   → Continues compilation
```

---

## Example: Lisp Reader

```lang
include "std/tok.lang"
include "std/parse.lang"
include "std/emit.lang"

reader lisp(text *u8) *u8 {
    var tokens *TokenStream = lang_tokenize(text);
    return parse(sexp(), tokens).value;
}

func sexp() Parser {
    return p_or(
        p_map(p_number(), emit_number_from_tok),
        p_map(
            p_delimited(p_lparen(), p_many(sexp()), p_rparen()),
            emit_sexp
        )
    );
}

func emit_sexp(items *Vec) *u8 {
    var op *u8 = vec_get(items, 0);
    var left *u8 = vec_get(items, 1);
    var right *u8 = vec_get(items, 2);
    return emit_binop(left, op, right);
}
```

Usage:
```lang
func main() i64 {
    return #lisp{(+ 1 (* 2 3))};  // Returns 7
}
```

---

## What We Looked At

- **Common Lisp**: Reader macros via `set-macro-character`. Full Lisp power. Heavy runtime.
- **Rust proc macros**: TokenStream interchange. Separate compilation. Via LLVM.
- **Terra**: Lua meta-language, Terra object language. Multi-stage. Via LLVM.
- **MetaOCaml**: Type-safe staging. Well-typed generators → well-typed code.
- **Nim**: Macros transform AST. Compiles to C.
- **PreScheme**: Scheme subset → C. Manual memory. No GC.
- **Language workbenches** (Spoofax, MPS, Xtext): Grammar-driven, IDE generation.

All informed the design. Racket and Zig are the north stars.

---

## Implementation Plan

### Phase 1: Core Infrastructure
- Reader declarations compile to separate executables
- `#reader{...}` invokes executable, captures output
- Output parsed as lang expression

### Phase 2: std/tok.lang
- Expose lang's lexer as `lang_tokenize()`
- Token and TokenStream types

### Phase 3: std/parse.lang
- Parser combinator primitives
- p_or, p_seq, p_many, p_map, etc.

### Phase 4: std/emit.lang
- Code generation helpers
- emit_number, emit_binop, emit_call, etc.

### Phase 5: Caching
- Cache compiled readers in .lang-cache/
- Invalidate on source change

---

## The Value Proposition

**Educational**: See custom syntax → machine code in one readable codebase.

**Hackable**: Want to add a feature? You can.

**Minimal**: No runtime. No dependencies. Just your code.

**Fun**: Build languages because you can.

---

## References

- [Racket](https://racket-lang.org/) / [Beautiful Racket](https://beautifulracket.com/)
- [Zig comptime](https://kristoff.it/blog/what-is-zig-comptime/)
- [Racket Manifesto](https://felleisen.org/matthias/manifesto/sec_pl-pl.html)
