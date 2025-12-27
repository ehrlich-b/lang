# Self-Defining Syntax: `lang_reader.lang`

## Overview

Define lang's syntax as a lang reader macro. Like the x86 fixed point proved self-hosting works, `lang_reader.lang` proves the compiler compiler can define any syntax - including its own.

## The Three Loops

### Loop 1: x86 Self-Hosting (Complete)

```
lang source → [lang compiler] → x86 asm → [lang compiler executable]
```

The compiler compiles itself. This is traditional self-hosting - a loop in machine code space. Every step is bound to x86: the parser generates x86, the codegen emits x86, the output runs on x86.

**Status**: Done. Fixed point reached.

### Loop 2: Language Forge (In Progress)

```
lang + lisp_reader.lang → [runtime lisp-to-x86 compiler]
```

A reader macro defines a new syntax. The combination of our compiler + that reader macro IS a compiler for the new language. At runtime, `lang lisp_reader.lang main.lisp` produces a native executable from Lisp source.

**Key insight**: We're not interpreting Lisp. We're not transpiling to an intermediate. The reader macro transforms Lisp syntax directly into lang AST, which compiles to x86. The result is a **native Lisp compiler** that exists only at compile time.

**Emit as standalone exe**: We should be able to emit the combined compiler as a standalone executable:
```bash
lang --emit-compiler lisp_reader.lang -o lisp_compiler
./lisp_compiler main.lisp -o main
```

**Status**: Blocked on reader includes. The infrastructure works but readers can't include helper files.

### Loop 3: Self-Defining Syntax (The Vision)

```
lang + lang_reader.lang → [lang compiler with lang-defined syntax]
```

This is the philosophical breakthrough: **lang's own syntax defined as a lang reader macro**.

Currently, lang's syntax is hardcoded in `src/parser.lang`. The tokenizer knows what `func` means, what `{` means, what operators exist. This is arbitrary - it's just what we chose to implement.

With `lang_reader.lang`, the syntax becomes **data**. The reader macro defines:
- What tokens exist
- What expressions look like
- What statements are valid
- How they map to the underlying AST

The compiler no longer "knows" lang syntax. It only knows:
1. How to execute reader macros
2. How to compile AST to assembly

Everything else is defined in the reader.

## Abstract vs Concrete

The x86 self-hosting loop is concrete - every instruction is a real x86 opcode running on real silicon.

Self-defining syntax only touches reality at two points:

```
┌─────────────────────────────────────────────────────────┐
│                   ABSTRACT LAYER                         │
│                                                          │
│   Tokenization → Parsing → AST → Codegen Logic          │
│                                                          │
│   (defined in lang, portable, abstract)                  │
│                                                          │
└──────────────┬────────────────────────────┬─────────────┘
               │                            │
               ▼                            ▼
        ┌──────────┐                 ┌──────────────┐
        │  alloc   │                 │   emit asm   │
        │ syscall  │                 │   (backend)  │
        └──────────┘                 └──────────────┘
             │                              │
             ▼                              ▼
        ┌─────────────────────────────────────────┐
        │              REALITY (x86)               │
        └─────────────────────────────────────────┘
```

The **touch points** to reality:
- `alloc` / `syscall` - OS interface for memory and I/O
- Assembly emission - translation to machine code

Everything in the abstract layer is pure semantics. It's not x86-specific. Swap the backend to LLVM IR, ARM, or WASM, and `lang_reader.lang` works unchanged. The syntax definition is truly portable.

## The Syntax Bootstrap

Here's where it gets wild:

```bash
# Traditional bootstrap (x86 space)
./boot/lang0 src/*.lang -o out/lang1
./out/lang1 src/*.lang -o out/lang2
# lang1 == lang2 (fixed point in x86)

# Syntax bootstrap
lang lang_reader.lang src/compiler.lang -o out/lang_v2
```

The `lang_v2` compiler:
1. Uses `lang_reader.lang` to parse lang syntax
2. Compiles that to x86
3. Can compile any `.lang` file

But wait - what compiled `lang_reader.lang` in the first place? The original hardcoded parser.

**The syntax fixed point**:
```bash
# Step 1: Use hardcoded parser to compile the reader
lang std/core.lang lang_reader.lang src/compiler.lang -o out/lang_p1

# Step 2: Use lang_p1 (with reader-defined syntax) to compile itself
./out/lang_p1 lang_reader.lang src/compiler.lang -o out/lang_p2

# Step 3: Verify fixed point
diff out/lang_p1 out/lang_p2  # Should be identical!
```

If `lang_p1 == lang_p2`, we've achieved a syntax fixed point. The syntax definition is self-consistent.

## The Bootstrap Chain

Once we have self-defining syntax, we can bootstrap NEW languages from it:

```
lang_reader.lang          # lang syntax in lang
    │
    ├── lisp_reader.lang  # lisp syntax in lang
    │
    └── lisp_reader.lisp  # lisp syntax in lisp (!)
            │
            └── ???_reader.lisp  # new syntax in lisp
```

Each layer can define new syntaxes. The only fixed point is the underlying AST and the backend.

## Implementation Requirements

### For Loop 2 (Language Forge)

1. **Reader includes** - Readers must be able to include helper files
2. **File extension dispatch** - `lang reader.lang main.ext` detects extension, uses reader
3. **Emit standalone compiler** - `lang --emit-compiler reader.lang -o compiler`

### For Loop 3 (Self-Defining Syntax)

1. **Complete Loop 2** - Need working reader infrastructure first
2. **lang_reader.lang** - Define lang's syntax as a reader macro
3. **Minimal bootstrap kernel** - The irreducible core that can't be defined in lang:
   - Reader macro execution
   - AST node types
   - Assembly emission
   - `alloc` / `syscall`

### The Minimal Kernel

What MUST be hardcoded (can't be in a reader)?

```
Irreducible core:
├── Reader execution     (fork/exec, capture output)
├── AST types           (NODE_NUMBER, NODE_BINOP, etc.)
├── Type system         (i64, *u8, structs)
├── Backend             (x86 asm emission)
└── OS interface        (alloc, syscall wrappers)

Everything else can be reader-defined:
├── Syntax              (lang_reader.lang)
├── Parsing             (tokenizer, parser combinators)
├── Sugar               (for loops, compound assignment)
└── Macros              (quote/unquote, AST manipulation)
```

## Example: lang_reader.lang (Sketch)

```lang
include "std/tok.lang"
include "std/emit.lang"
include "lang_parser.lang"  // recursive descent parser for lang

reader lang(text *u8) *u8 {
    var t *Tokenizer = tok_new(text);
    return parse_program(t);  // returns lang source (identity for bootstrap)
}
```

Wait - for the syntax bootstrap, the reader returns... lang source. That seems circular.

**Key insight**: The reader's job is to transform syntax to AST. For `lang_reader.lang`, input and output are both lang syntax, so the reader is nearly an identity function. But it PROVES that the syntax is well-defined - if the reader can parse it, it's valid.

The real power comes when we MODIFY the syntax:

```lang
// lang_extended_reader.lang - add for loops!
reader lang_ext(text *u8) *u8 {
    // ... parse including for loops ...
    // ... desugar for → while ...
    return emit_program(ast);
}
```

Now `lang lang_extended_reader.lang program_with_for.lang` works, even though the base compiler doesn't know `for`.

## Why This Matters

1. **Syntax is Data** - No longer hardcoded, can be inspected/modified/versioned
2. **True Portability** - Abstract layer is backend-independent
3. **Infinite Extensibility** - New syntax without modifying the compiler
4. **Beautiful Bootstrap** - Syntax fixed point, not just machine code fixed point
5. **Language Laboratory** - Trivially experiment with syntax changes

## Comparison to Other Systems

| System | Syntax Definition | Extensibility |
|--------|-------------------|---------------|
| C | Hardcoded in compiler | Preprocessor only |
| Lisp | Hardcoded S-exprs, reader macros for sugar | Reader macros (limited) |
| Racket | #lang mechanism | Full, but interpreted |
| **lang** | Reader macros → native code | Full, compiled to x86 |

Racket is the closest comparison. The difference: Racket's `#lang` dispatches to an interpreter/JIT. Lang's reader macros compile to native executables. No runtime, no VM, just machine code.

## Milestones

1. [ ] **Reader includes** - Fix the blocking issue
2. [ ] **Lisp reader** - Prove the language forge concept
3. [ ] **File extension dispatch** - `lang reader.lang main.ext`
4. [ ] **Emit standalone compiler** - `lang --emit-compiler`
5. [ ] **lang_reader.lang** - Self-defining syntax
6. [ ] **Syntax fixed point** - Bootstrap from lang_reader.lang

## Readers Invoking Readers

The real power: reader macros can invoke other reader macros.

```lang
// parser_reader.lang - defines #parser{}
reader parser(grammar *u8) *u8 {
    // parse BNF, emit recursive descent code
}

// lisp_reader.lang - USES #parser{}
reader lisp(text *u8) *u8 {
    #parser{
        sexp = number | symbol | '(' sexp* ')'
    }
    return parse_sexp(tok_new(text));
}
```

**The compilation cascade**:
```
#parser{} ──► parser generator exe
    │
    └──► #lisp{} reader ──► lisp compiler exe
                                │
                                └──► main.lang ──► x86 binary
```

Each layer compiles to native code. You don't just write DSLs - you write DSLs for writing DSLs.

## Conclusion

Self-defining syntax is the completion of the project. We started with "self-hosting compiler" (x86 fixed point) and end with "self-defining syntax" (syntax fixed point).

The only concrete parts are the touch points to reality: memory allocation, system calls, and assembly emission. Everything else is defined in lang itself.

This is what "compiler compiler" really means.
