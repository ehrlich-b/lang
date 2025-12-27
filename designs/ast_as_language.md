# AST as Language: The Root Language Design

## The Insight

We've been thinking about this backwards.

**Current mental model:**
```
lang source → [parser] → AST → [codegen] → x86
                ↑
          "lang is the language"
```

**Correct mental model:**
```
any syntax → [reader] → AST → [codegen] → x86
                          ↑
                 "AST is the language"
```

The AST format IS the programming language. What we call "lang" is just one syntax (one "skin") that maps to that AST. Lisp S-expressions would be another skin. You could invent any syntax you want.

## Why S-Expressions... But Also Not

S-expressions are perfect for AST representation:
- Trivial to parse (one page of code)
- Self-describing (structure is visible)
- Proven for 60+ years
- Homoiconic (code = data)

But you don't WRITE S-expressions by hand. That's the key insight Racket missed (or accepted as a tradeoff). S-expressions are an **interchange format**, not a human interface.

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│   S-expressions: perfect for machines, hard for humans              │
│   C-like syntax: easy for humans, complex to parse                  │
│                                                                      │
│   Solution: humans write C-like, machines exchange S-exprs          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## The Architecture

```
                        SYNTAX LAYER (readers)
                     ┌─────────────────────────────┐
                     │                             │
    lang syntax ───→ │  lang_reader                │───┐
    (C-like)         │  (tokenize + parse → AST)   │   │
                     └─────────────────────────────┘   │
                                                       │
                     ┌─────────────────────────────┐   │
    lisp syntax ───→ │  lisp_reader                │───┤
    (S-exprs)        │  (parse S-exprs → AST)      │   │
                     └─────────────────────────────┘   │
                                                       │
                     ┌─────────────────────────────┐   │
    your syntax ───→ │  your_reader                │───┤
    (whatever!)      │  (your parser → AST)        │   │
                     └─────────────────────────────┘   │
                                                       │
                                                       ▼
                                              ┌───────────────┐
                                              │  AST FORMAT   │
                                              │  (S-exprs)    │
                                              └───────┬───────┘
                                                      │
                        KERNEL LAYER                  │
                     ┌────────────────────────────────┼────────┐
                     │                                │        │
                     │                                ▼        │
                     │                        ┌─────────────┐  │
                     │                        │ AST Loader  │  │
                     │                        └──────┬──────┘  │
                     │                               │         │
                     │                               ▼         │
                     │                        ┌─────────────┐  │
                     │                        │ Type Check  │  │
                     │                        └──────┬──────┘  │
                     │                               │         │
                     │                               ▼         │
                     │                        ┌─────────────┐  │
                     │                        │  Codegen    │  │
                     │                        └──────┬──────┘  │
                     │                               │         │
                     └───────────────────────────────┼─────────┘
                                                     │
                                                     ▼
                                                    x86
```

## The AST Format Specification

The AST is a typed imperative language expressed as S-expressions. This is NOT meant to be written by humans - it's the interchange format.

### Core Forms

```lisp
;; Program structure
(program <decl>*)

;; Declarations
(func <name> (<param>*) <type> <body>)
(var <name> <type> <init>?)
(struct <name> (<field>*))

;; Statements
(block <stmt>*)
(if <cond> <then> <else>?)
(while <cond> <body>)
(return <expr>?)
(break <label>?)
(continue <label>?)
(expr-stmt <expr>)

;; Expressions
(binop <op> <left> <right>)    ; + - * / % == != < > <= >= && ||
(unop <op> <expr>)             ; - ! * &
(call <func> <arg>*)
(field <expr> <name>)
(index <expr> <index>)
(ident <name>)
(number <value>)
(string <value>)
(bool <value>)
(nil)

;; Types
(type-base <name>)             ; i64, u8, bool, void
(type-ptr <elem>)              ; *T
(type-array <size> <elem>)     ; [N]T

;; Parameters and Fields
(param <name> <type>)
(field-decl <name> <type>)
```

### Example: Factorial

**Human writes (lang syntax):**
```lang
func factorial(n i64) i64 {
    if n <= 1 {
        return 1;
    }
    return n * factorial(n - 1);
}
```

**Reader outputs (AST S-expression):**
```lisp
(func factorial ((param n (type-base i64))) (type-base i64)
  (block
    (if (binop <= (ident n) (number 1))
      (block (return (number 1))))
    (return (binop *
              (ident n)
              (call factorial (binop - (ident n) (number 1)))))))
```

**Same program, lisp syntax:**
```lisp
(defun factorial (n)
  (if (<= n 1)
      1
      (* n (factorial (- n 1)))))
```

**Same AST output** - both syntaxes produce identical AST S-expressions.

## The Kernel

The kernel is the irreducible core. It cannot be reader-defined.

```
Kernel responsibilities:
├── AST Parser       (parse S-expression AST format)
├── Type Checker     (validate types, compute sizes)
├── Codegen          (AST → x86 assembly)
├── Reader Dispatch  (#name{} detection, fork/exec)
└── OS Interface     (syscall wrappers)
```

The kernel is **syntax-agnostic**. It only understands the AST format. All syntax is defined by readers.

## Reader Protocol

A reader is a native executable that:
1. Reads source text from stdin
2. Writes AST S-expressions to stdout
3. Writes errors to stderr

```bash
# Reader invocation
echo "func main() i64 { return 42; }" | ./lang_reader
# Output: (program (func main () (type-base i64) (block (return (number 42)))))
```

Readers are compiled by the kernel (using whatever reader was used to write them). This is the bootstrap loop.

## Reader Author Experience

Reader authors should NEVER write S-expression strings manually. We provide abstraction layers so they work with typed AST constructors.

### The Core Principle

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  Reader author's ONLY job: parse their syntax, build AST nodes.     │
│                                                                      │
│  They should NEVER:                                                  │
│  - Write S-expression strings manually                              │
│  - Know AST node memory layout                                       │
│  - Think about serialization                                         │
│  - Care about x86                                                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Abstraction Layers

```
Level 4: Lang Variants          "fn" → "func", done
         ──────────────────────────────────────────
Level 3: Domain Helpers         expr_lang_parse(text)
         ──────────────────────────────────────────
Level 2: Parser Combinators     p_seq(p_token(...), ...)
         ──────────────────────────────────────────
Level 1: AST Constructors       ast_binop("+", left, right)
         ──────────────────────────────────────────
Level 0: Raw S-exprs            "(binop + ...)"  ← NEVER DO THIS
```

### Level 1: AST Constructors (std/ast.lang)

The core abstraction. Typed constructors for every AST node:

```lang
include "std/ast.lang"

// Expressions
func ast_number(value i64) *AST;
func ast_ident(name *u8) *AST;
func ast_string(value *u8) *AST;
func ast_binop(op *u8, left *AST, right *AST) *AST;
func ast_unop(op *u8, expr *AST) *AST;
func ast_call(fn *AST, args *Vec) *AST;
func ast_field(expr *AST, name *u8) *AST;

// Statements
func ast_block(stmts *Vec) *AST;
func ast_if(cond *AST, then *AST, else_ *AST) *AST;
func ast_while(cond *AST, body *AST) *AST;
func ast_return(value *AST) *AST;
func ast_var(name *u8, type *AST, init *AST) *AST;

// Declarations
func ast_func(name *u8, params *Vec, ret *AST, body *AST) *AST;
func ast_param(name *u8, type *AST) *AST;
func ast_struct(name *u8, fields *Vec) *AST;

// Types
func ast_type(name *u8) *AST;           // i64, u8, bool, MyStruct
func ast_type_ptr(elem *AST) *AST;      // *T

// The magic function - serialize to S-expr
func ast_emit(node *AST) *u8;
```

**Example: Minimal calculator reader**

```lang
include "std/ast.lang"

reader calc(text *u8) *u8 {
    var expr *AST = parse_expr(text);
    return ast_emit(expr);
}

func parse_expr(text *u8) *AST {
    // Reader author focuses on THEIR syntax
    var left *AST = ast_number(1);
    var right *AST = ast_binop("*", ast_number(2), ast_number(3));
    return ast_binop("+", left, right);
}
```

Reader author thinks in terms of **AST nodes**, not strings. `ast_emit` handles serialization.

### Level 2: Parser Combinators (std/parse.lang)

For more complex parsing with tokenization support:

```lang
include "std/ast.lang"
include "std/parse.lang"

reader lisp(text *u8) *u8 {
    var p *Parser = parser_new(text);
    var expr *AST = parse_sexpr(p);
    return ast_emit(expr);
}

func parse_sexpr(p *Parser) *AST {
    if parser_match(p, TOKEN_NUMBER) {
        return ast_number(parser_prev_number(p));
    }
    if parser_match(p, TOKEN_LPAREN) {
        var op *u8 = parser_expect_ident(p);
        var left *AST = parse_sexpr(p);
        var right *AST = parse_sexpr(p);
        parser_expect(p, TOKEN_RPAREN);
        return ast_binop(op, left, right);
    }
    parser_error(p, "expected number or (");
}
```

### Level 3: Domain Helpers

Pre-built parsers for common patterns:

```lang
include "std/expr_lang.lang"

// For expression-only languages (calculators, formula DSLs)
reader calc(text *u8) *u8 {
    return expr_lang_infix(text);  // Handles precedence, parens, etc.
}
```

```lang
include "std/stmt_lang.lang"

// For imperative languages with standard control flow
reader mini(text *u8) *u8 {
    var cfg *StmtLangConfig = stmt_lang_config();
    cfg.fn_keyword = "def";
    cfg.var_keyword = "let";
    return stmt_lang_parse(text, cfg);
}
```

### Level 4: Lang Variants

For "lang with different keywords" - near-zero effort:

```lang
include "std/lang_variant.lang"

reader rustlike(text *u8) *u8 {
    var v *LangVariant = lang_variant_new();
    lang_variant_keyword(v, "fn", "func");
    lang_variant_keyword(v, "let", "var");
    lang_variant_keyword(v, "i32", "i64");
    return lang_variant_parse(v, text);
}
```

Now `fn add(a: i32, b: i32) { a + b }` just works.

### The AST Vocabulary (Cheat Sheet)

What reader authors need to memorize:

```
EXPRESSIONS (things that have values)
├── ast_number(42)                    →  42
├── ast_ident("x")                    →  x
├── ast_string("hello")               →  "hello"
├── ast_binop("+", left, right)       →  left + right
├── ast_unop("-", expr)               →  -expr
├── ast_unop("*", expr)               →  *expr (deref)
├── ast_unop("&", expr)               →  &expr (address-of)
├── ast_call(fn, args_vec)            →  fn(a, b, c)
└── ast_field(expr, "name")           →  expr.name

STATEMENTS (things that do stuff)
├── ast_block(stmts_vec)              →  { stmt1; stmt2; }
├── ast_if(cond, then, else_)         →  if cond { then } else { else_ }
├── ast_while(cond, body)             →  while cond { body }
├── ast_return(expr)                  →  return expr;
├── ast_break()                       →  break;
└── ast_continue()                    →  continue;

DECLARATIONS (things that define stuff)
├── ast_var(name, type, init)         →  var name type = init;
├── ast_func(name, params, ret, body) →  func name(params) ret { body }
├── ast_param(name, type)             →  name type
└── ast_struct(name, fields)          →  struct name { fields }

TYPES
├── ast_type("i64")                   →  i64
├── ast_type("bool")                  →  bool
└── ast_type_ptr(elem)                →  *elem
```

### Complete Example: Lisp Reader

~100 lines for a working Lisp-to-native compiler:

```lang
include "std/ast.lang"
include "std/tok.lang"

reader lisp(text *u8) *u8 {
    var t *Tokenizer = tok_new(text);
    var program *Vec = vec_new(16);

    while !tok_eof(t) {
        vec_push(program, parse_toplevel(t));
    }

    return ast_emit(ast_program(program));
}

func parse_toplevel(t *Tokenizer) *AST {
    tok_expect(t, TOKEN_LPAREN);
    var form *u8 = tok_ident(t);

    if streq(form, "defun") {
        return parse_defun(t);
    }
    tok_error(t, "unknown form");
}

func parse_defun(t *Tokenizer) *AST {
    var name *u8 = tok_ident(t);

    // Parse parameter list
    tok_expect(t, TOKEN_LPAREN);
    var params *Vec = vec_new(8);
    while !tok_check(t, TOKEN_RPAREN) {
        var pname *u8 = tok_ident(t);
        vec_push(params, ast_param(pname, ast_type("i64")));
    }
    tok_expect(t, TOKEN_RPAREN);

    // Parse body expression
    var body *AST = parse_expr(t);
    tok_expect(t, TOKEN_RPAREN);

    return ast_func(name, params, ast_type("i64"),
                    ast_block(vec_of(ast_return(body))));
}

func parse_expr(t *Tokenizer) *AST {
    if tok_check(t, TOKEN_NUMBER) {
        return ast_number(tok_number(t));
    }
    if tok_check(t, TOKEN_IDENT) {
        return ast_ident(tok_ident(t));
    }
    if tok_check(t, TOKEN_LPAREN) {
        tok_advance(t);
        var op *u8 = tok_ident(t);

        // Binary operators
        if streq(op, "+") || streq(op, "-") || streq(op, "*") {
            var left *AST = parse_expr(t);
            var right *AST = parse_expr(t);
            tok_expect(t, TOKEN_RPAREN);
            return ast_binop(op, left, right);
        }

        // Function call
        var args *Vec = vec_new(8);
        while !tok_check(t, TOKEN_RPAREN) {
            vec_push(args, parse_expr(t));
        }
        tok_expect(t, TOKEN_RPAREN);
        return ast_call(ast_ident(op), args);
    }
    tok_error(t, "expected expression");
}
```

### What Reader Authors Know vs Don't Know

```
┌──────────────────────────────────────┬──────────────────────────────────┐
│  MUST KNOW                           │  DON'T NEED TO KNOW              │
├──────────────────────────────────────┼──────────────────────────────────┤
│  1. The AST vocabulary:              │  1. S-expression syntax          │
│     - What nodes exist               │  2. AST memory layout            │
│     - What each node means           │  3. How kernel compiles          │
│                                      │  4. x86 assembly                 │
│  2. AST constructors:                │  5. Type system internals        │
│     - ast_binop, ast_func, etc.      │  6. Codegen details              │
│                                      │                                  │
│  3. Their own syntax:                │                                  │
│     - How to tokenize it             │                                  │
│     - How to parse it                │                                  │
└──────────────────────────────────────┴──────────────────────────────────┘
```

### The Key Insight

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  ast_binop("+", ast_number(1), ast_number(2))                       │
│       ↓                                                              │
│  ast_emit()                                                          │
│       ↓                                                              │
│  "(binop + (number 1) (number 2))"  ← Reader never sees this        │
│       ↓                                                              │
│  kernel                                                              │
│       ↓                                                              │
│  add $1, $2, %rax                   ← Reader never sees this        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

The S-expression format is an **implementation detail**. Reader authors build AST trees using constructors, and `ast_emit` serializes it. They never write or read S-expressions directly.

## Why This is Powerful

### 1. True Syntax Freedom

Want Python-like syntax? Write a reader. Want APL? Write a reader. The kernel doesn't care.

```python
# python_reader could accept:
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
```

And output the same AST as the lang and lisp versions.

### 2. Syntax is Versioned Separately

`lang_v1_reader` and `lang_v2_reader` can coexist. Old syntax keeps working. New features can be added without breaking anything.

### 3. Cross-Language Interop is Free

Since all readers output the same AST, mixing syntaxes is trivial:

```bash
./kernel lang_reader:main.lang lisp_reader:lib.lisp python_reader:utils.py -o program
```

All three files compile to the same AST, link together seamlessly.

### 4. The Kernel is Tiny

The kernel only needs to:
- Parse S-expressions (trivial)
- Type check AST (already have this)
- Generate x86 (already have this)

Maybe 2000 lines total, vs the current ~5000 line compiler.

## Bootstrap Process

```
Phase 1: Build the kernel
─────────────────────────
Use current lang compiler to build kernel.lang
The kernel can now compile AST S-expressions to x86

Phase 2: Build lang_reader
─────────────────────────
Write lang_reader.lang (a reader that parses lang syntax)
Compile with current compiler to get lang_reader executable
lang_reader outputs AST S-expressions

Phase 3: Self-hosting
─────────────────────────
kernel + lang_reader can compile any .lang file
Use them to recompile kernel.lang and lang_reader.lang
Verify fixed point

Phase 4: Delete hardcoded parser
─────────────────────────
The current parser in src/parser.lang becomes unnecessary
All parsing is done by readers
```

## Comparison to Racket

| Aspect | Racket | Lang |
|--------|--------|------|
| Core language | `racket/base` (large) | AST format (small) |
| Reader output | Syntax objects | S-expression AST |
| Expansion | Multi-phase macros | Readers do all transformation |
| Runtime | VM + JIT | None (native code) |
| Syntax freedom | High | Total |

Racket's `#lang` is more powerful in some ways (hygiene, phases, syntax-case) but requires a substantial runtime. Lang's approach is more minimal: readers are native executables, there's no runtime, and the kernel is tiny.

## Comparison to WASM

```
                        ABSTRACTION LEVEL
                              ↑
    ┌─────────────────────────┼─────────────────────────┐
    │  OUR AST               │  ← High-level           │
    │  (func, if, while,     │    Named variables      │
    │   expressions, types)  │    Structured control   │
    ├─────────────────────────┼─────────────────────────┤
    │  WASM                   │  ← Low-level            │
    │  (local.get, i32.add,  │    Stack-based          │
    │   br_if, call)         │    Explicit operations  │
    ├─────────────────────────┼─────────────────────────┤
    │  x86                    │  ← Machine              │
    │  (mov, add, jmp, call) │                         │
    └─────────────────────────┴─────────────────────────┘
```

| Aspect | WASM | Our System |
|--------|------|------------|
| **Solves** | Portable, safe execution | Universal syntax |
| **Focus** | Backend | Frontend |
| **Level** | Low (stack machine) | High (typed AST) |
| **Runtime** | Required | None |

**Key insight**: They're orthogonal! WASM solves the backend problem (run anywhere), we solve the frontend problem (write in any syntax). They compose:

```
any syntax → reader → AST → kernel → WASM → browser/WASI/anywhere
```

The kernel will have multiple backends: x86 (current), then WASM and LLVM IR. The AST format and all readers stay the same - backend is just a flag.

## The S-Expression Question

"Why S-expressions for AST if I find them hard to read?"

Because **you never read them**. They're like assembly language - an intermediate representation that humans don't touch directly.

```
Human writes:     func add(a i64, b i64) i64 { return a + b; }
                                    ↓
                             lang_reader
                                    ↓
Machine exchanges: (func add ((param a (type-base i64)) (param b (type-base i64)))
                     (type-base i64) (block (return (binop + (ident a) (ident b)))))
                                    ↓
                               kernel
                                    ↓
Machine executes:  mov %rsi, %rax; add %rdi, %rax; ret
```

S-expressions are the "assembly of syntax" - universal, simple, machine-friendly.

## Alternative: Binary AST Format

We could use a binary format instead of S-expressions:

```
Pros:
- Faster to parse
- Smaller files
- No parsing ambiguity

Cons:
- Not human-debuggable
- Versioning is harder
- Tooling is harder
```

S-expressions are probably better for now. Binary could be an optimization later.

## AST Expressiveness: What's Missing

Our current AST is a **C-level IR**. It can express C-family languages well, but has fundamental limitations for other paradigms.

### What We Can Express (1.0)

```
✓ C, Go (minus goroutines), Zig, Odin
✓ Basic Rust (minus borrow checker, traits)
✓ Simple OOP (structs + function pointers as vtables)
✓ Imperative Python/JS subset (with runtime type tags)
```

### What We Cannot Express (Fundamental Gaps)

| Feature | Impact | Why It's Hard |
|---------|--------|---------------|
| **First-class functions** | Can't pass/return functions as values | Need func types in type system |
| **Closures** | Can't capture lexical environment | Frames can outlive invocation |
| **Sum types / Enums** | No Option\<T\>, Result\<T,E\>, safe unions | Need variant types + pattern matching |
| **Generics** | No Vec\<T\>, Map\<K,V\> | Need monomorphization or type erasure |
| **Exceptions** | No try/catch/throw | Need stack unwinding infrastructure |
| **Coroutines/async** | No yield, generators, async/await | Need CPS transform or runtime |

### Languages We Cannot Target

```
Haskell     → lazy evaluation, type classes, HKTs
ML/OCaml    → ADTs, pattern matching, type inference
Erlang      → actors, lightweight processes, hot reload
Prolog      → logic programming, unification, backtracking
APL/J       → array primitives, tacit programming
```

These aren't just missing syntax - they're fundamentally different execution models.

### 2.0: Required AST Extensions

To support ML-family languages and modern language features:

```lisp
;; First-class functions (Tier 1 - critical)
(func-type (<param-type>*) <return-type>)    ; fn(i64, i64) -> i64
(lambda (<param>*) <ret-type> <body>)        ; |x, y| { x + y }
(closure <lambda> (<capture>*))              ; lambda + captured environment

;; Sum types / Enums (Tier 1 - critical)
(enum <name> (<variant>*))                   ; enum Option { Some(T), None }
(variant <name> (<field>*))                  ; Some(value: T)
(match <expr> (<case>*))                     ; match x { ... }
(case <pattern> <body>)                      ; Some(v) => v

;; Generics (Tier 1 - critical)
(type-var <name>)                            ; T
(forall (<type-var>*) <type>)               ; forall T. Vec<T>
(type-apply <generic> (<type-arg>*))        ; Vec<i64>
;; Kernel performs monomorphization at compile time

;; Exceptions (Tier 2 - important)
(try <body> (<handler>*) <finally>?)
(throw <expr>)
(catch <type> <binding> <body>)
```

### 2.0: Required lang Syntax Extensions

The lang reader would need to support:

```lang
// First-class functions
func apply(f fn(i64) i64, x i64) i64 {
    return f(x);
}

var double fn(i64) i64 = |x| { x * 2 };

// Closures
func make_adder(n i64) fn(i64) i64 {
    return |x| { x + n };  // captures n
}

// Sum types
enum Option<T> {
    Some(T),
    None,
}

// Pattern matching
match result {
    Some(value) => println(value),
    None => println("nothing"),
}

// Generics
func identity<T>(x T) T {
    return x;
}

struct Vec<T> {
    data *T;
    len i64;
    cap i64;
}
```

### Implementation Complexity

| Feature | AST Change | Kernel Change | Reader Change |
|---------|------------|---------------|---------------|
| First-class funcs | New node types | Func ptr codegen | New syntax |
| Closures | Capture lists | Env allocation | Lambda syntax |
| Sum types | Enum/variant nodes | Tagged union codegen | Enum/match syntax |
| Pattern matching | Case/pattern nodes | Decision tree codegen | Match syntax |
| Generics | Type params | Monomorphization pass | Generic syntax |

### The Paradigm Boundary

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  1.0 AST: Imperative, monomorphic, strict, manual memory               │
│           → C, Go, Zig, Rust (basic)                                   │
│                                                                         │
│  2.0 AST: + closures, ADTs, generics                                   │
│           → ML, OCaml, Scala, Swift, Kotlin                            │
│                                                                         │
│  3.0 AST: + effects, linear types, laziness (hypothetical)             │
│           → Haskell, Rust (full), Koka                                 │
│                                                                         │
│  Beyond: Actors, logic programming, array languages                    │
│          → Would need different IR entirely                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Decision: Start with 1.0

For 1.0, we ship the C-level AST. This is enough to:
- Prove the architecture works
- Bootstrap lang as a reader
- Add WASM/LLVM backends
- Build useful languages (anything C-like)

2.0 adds the features needed for modern functional/OOP hybrid languages. This is a substantial project but follows the same architecture.

## Kernel Responsibilities (Semantics)

The AST is intentionally high-level. The **kernel** defines the operational semantics:

| Concern | Kernel's Answer |
|---------|-----------------|
| Integer overflow | Wrapping (two's complement, like C) |
| Division by zero | Undefined (crashes) |
| Null pointer (`nil`) | Zero address, dereference crashes |
| Struct layout | Sequential, 8-byte aligned fields |
| Calling convention | System V AMD64 (Linux) |
| Evaluation order | Left-to-right, strict |
| Memory model | Manual (alloc/free), no GC |

These should be documented more formally as the kernel stabilizes.

### Why WASM Backend Helps

Targeting WASM gives us many semantics "for free":
- Defined numeric behavior (wrap, trap options)
- Memory safety (bounds checking)
- Portable calling convention
- Verification built-in

### If We Want Serious Optimization

The kernel should lower AST to SSA/CFG internally before emitting LLVM IR:

```
AST (high-level, structured, what readers emit)
         ↓
    [Kernel internal lowering]
         ↓
    CFG + SSA (for optimization passes)
         ↓
    LLVM IR / WASM / x86
```

The AST stays human-friendly. The kernel handles the gnarly bits.

## Open Questions

1. **Error messages**: When AST has an error, how do we map back to source?
   - Readers could emit source location metadata
   - S-expressions could include span info: `(number 42 :line 5 :col 12)`

2. **Incremental compilation**: Parse once, reuse AST?
   - AST files could be cached
   - Readers only run when source changes

3. **Macros**: Where do AST macros live?
   - Option A: Readers expand macros, kernel never sees them
   - Option B: Kernel understands macro expansion
   - Option A is cleaner but limits macro power

4. **Type inference**: Add to kernel or keep explicit types?
   - Current: explicit types required
   - Could add inference later without changing AST format

## Implementation Plan

### Phase 1: AST Format Spec
- [ ] Define complete AST S-expression grammar
- [ ] Document all node types
- [ ] Write AST examples for all language features

### Phase 2: S-Expression Parser
- [ ] Add `parse_sexpr()` to kernel
- [ ] Test with hand-written AST files

### Phase 3: lang_reader
- [ ] Extract parser from current compiler
- [ ] Modify to output S-expressions instead of internal AST
- [ ] Test: lang source → reader → kernel → x86

### Phase 4: Self-Hosting Redux (1.0)
- [ ] Compile kernel with lang_reader
- [ ] Compile lang_reader with kernel + lang_reader
- [ ] Verify fixed point
- [ ] Delete old hardcoded parser
- **This is 1.0**: lang bootstrapped as a reader on the AST kernel

### Phase 5: Multiple Backends
- [ ] WASM backend (portability, browser, WASI)
- [ ] LLVM IR backend (optimization, more targets)
- Same AST, same readers, different output

### Phase 6: Additional Readers
- [ ] lisp_reader (prove multi-syntax works)
- [ ] Demonstrate cross-language linking

## Conclusion

The AST format is the true language. "Lang" is just syntax - one of many possible skins on the AST. By formalizing the AST as an S-expression interchange format, we achieve:

1. **Complete syntax freedom** - any reader, any syntax
2. **Minimal kernel** - just AST → x86
3. **Cross-language interop** - everything compiles to the same AST
4. **Clean separation** - readers handle syntax, kernel handles semantics

This is what "compiler compiler" really means. Not a tool that helps you write compilers - a compiler that IS a compiler-writing system.

---

*"The AST is the music. The syntax is just the notation."*
