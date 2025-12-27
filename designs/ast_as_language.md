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

The AST is a typed language expressed as S-expressions. This is NOT meant to be written by humans - it's the interchange format. The kernel understands this format; readers produce it.

### Core Forms (2.0 Complete Specification)

```lisp
;; ═══════════════════════════════════════════════════════════════════════════
;; PROGRAM STRUCTURE
;; ═══════════════════════════════════════════════════════════════════════════

(program <decl>*)

;; ═══════════════════════════════════════════════════════════════════════════
;; DECLARATIONS
;; ═══════════════════════════════════════════════════════════════════════════

;; Functions - with optional effect annotations (2.0)
(func <name> (<param>*) (<effect>*)? <ret-type> <body>)

;; Variables
(var <name> <type> <init>?)

;; Structs (product types)
(struct <name> (<field-decl>*))

;; Enums (sum types) ← NEW in 2.0
(enum <name> (<variant-decl>*))

;; Effect declarations ← NEW in 2.0
(effect <name> (<param-type>*) <resume-type>)

;; ═══════════════════════════════════════════════════════════════════════════
;; STATEMENTS
;; ═══════════════════════════════════════════════════════════════════════════

(block <stmt>*)
(if <cond> <then> <else>?)
(while <cond> <body>)
(return <expr>?)
(break <label>?)
(continue <label>?)
(expr-stmt <expr>)
(assign <target> <value>)              ; ← explicit assignment (2.0)
(let <name> <type>? <init> <body>)     ; ← lexical binding (2.0)

;; ═══════════════════════════════════════════════════════════════════════════
;; EXPRESSIONS
;; ═══════════════════════════════════════════════════════════════════════════

;; Literals & Identifiers
(ident <name>)
(number <value>)
(string <value>)
(bool <value>)
(nil)

;; Operations
(binop <op> <left> <right>)            ; + - * / % == != < > <= >= && || & | ^
(unop <op> <expr>)                     ; - ! * &
(call <func> <arg>*)
(field <expr> <name>)
(index <expr> <index>)

;; First-class functions ← NEW in 2.0
(lambda (<param>*) (<effect>*)? <ret-type> <body>)
(closure <lambda> (<capture>*))        ; lambda + captured environment

;; Sum types ← NEW in 2.0
(variant <enum-name> <variant-name> <value>?)   ; construct: Some(42)
(match <expr> (<case>*))                         ; match x { ... }
(case <pattern> <body>)                          ; pattern => body

;; Algebraic effects ← NEW in 2.0
(perform <effect-name> <arg>*)                   ; raise effect
(handle <expr> <return-case> (<effect-case>*))   ; wrap and intercept
(resume <k> <value>?)                            ; resume continuation

;; ═══════════════════════════════════════════════════════════════════════════
;; PATTERNS (for match expressions) ← NEW in 2.0
;; ═══════════════════════════════════════════════════════════════════════════

(pattern-variant <name> <binding>?)    ; Some(x), None
(pattern-wildcard)                      ; _
(pattern-literal <value>)              ; 42, "hello", true

;; ═══════════════════════════════════════════════════════════════════════════
;; TYPES
;; ═══════════════════════════════════════════════════════════════════════════

(type-base <name>)                     ; i64, u8, bool, void
(type-ptr <elem>)                      ; *T
(type-array <size> <elem>)             ; [N]T
(type-func (<param-type>*) (<effect>*)? <ret-type>)  ; fn(i64) -> i64 ← NEW
(type-enum <name>)                     ; Option, Result ← NEW
(type-continuation <arg-type> <ret-type>)            ; k's type ← NEW

;; ═══════════════════════════════════════════════════════════════════════════
;; SUPPORTING NODES
;; ═══════════════════════════════════════════════════════════════════════════

;; Parameters and Fields
(param <name> <type>)
(field-decl <name> <type>)
(variant-decl <name> <type>?)          ; enum variant ← NEW
(capture <name> <type>)                ; closure capture ← NEW

;; Effect handling
(return-case (<binding>) <body>)       ; normal return path ← NEW
(effect-case <name> (<param>*) <k> <body>)  ; handler case ← NEW
```

### What's New in 2.0 (Summary)

| Category | 1.0 (Current) | 2.0 (Target) |
|----------|---------------|--------------|
| **Functions** | Named only | + Lambda, closures |
| **Data** | Structs only | + Enums (sum types) |
| **Control** | if/while/return | + Pattern matching |
| **Effects** | None | perform/handle/resume |
| **Types** | Base, ptr, array | + Func types, enums |

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

---

## The 2.0 Vision: Algebraic Effects as the Unifying Primitive

After extensive research (see `prompts/universal_ast_research_responses/`), a clear consensus emerged: **algebraic effects + handlers** are the single most important addition for semantic universality. They subsume exceptions, async/await, generators, coroutines, and even dynamic scoping - all as library features rather than kernel primitives.

### What Are Algebraic Effects?

Think of effects as "resumable exceptions." A `perform` operation is like `throw`, but with a superpower: the handler can **resume** execution at the perform site.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  throw   = perform that CANNOT resume    (handler discards continuation) │
│  yield   = perform that RESUMES ONCE     (handler returns to performer)  │
│  async   = perform that RESUMES LATER    (handler saves continuation)    │
│                                                                          │
│  All three are the SAME mechanism with different handler behavior.       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### The perform/handle Model

**perform** raises an effect up the call stack:

```lang
var result i64 = perform Read();  // "I need a Read to happen"
                                   // Suspends here until handler resumes
```

**handle** wraps code and intercepts effects:

```lang
handle {
    var x = do_stuff();           // may perform effects
    return x + 1;
} with {
    return(v) => v,               // normal completion: just return value
    Read(k) => {
        var data = read_file();   // handle the effect
        resume k(data);           // resume with data as perform's result
    }
}
```

The magic is `k` - the **continuation**. It represents "the rest of the computation after the perform." Call `k(value)` to resume with that value. Don't call `k` to abort (like exceptions).

### Concrete Examples

**Exceptions (no resumption):**
```lang
// throw is just perform where handler doesn't resume
func risky() i64 {
    if bad_condition {
        perform Throw("error!");  // k is never called
    }
    return 42;
}

var result = handle {
    risky()
} with {
    return(v) => Ok(v),
    Throw(msg, k) => Err(msg)     // don't call k = abort computation
};
```

**Generators (resume with next input):**
```lang
func count_up() void {
    var i = 0;
    while true {
        perform Yield(i);         // suspend, give value to consumer
        i = i + 1;                // resume here when consumer calls k
    }
}

var gen = handle {
    count_up()
} with {
    return(v) => Done,
    Yield(value, k) => Yielded(value, k)  // return value AND continuation
};

// Consumer:
match gen {
    Yielded(v, k) => {
        print(v);                 // prints 0
        var next = resume k();    // resume generator
        // next is Yielded(1, k')
    }
}
```

**Async/Await (resume later):**
```lang
func fetch_data() *u8 {
    var response = perform Await(http_get("url"));  // suspend
    return response.body;  // resume when future completes
}

var program = handle {
    fetch_data()
} with {
    return(v) => Completed(v),
    Await(future, k) => {
        // Don't resume now - schedule for later
        future.on_complete(|result| resume k(result));
        return Pending
    }
};
```

**State (implicit parameter):**
```lang
func increment() void {
    var current = perform Get();
    perform Set(current + 1);
}

var final_state = handle {
    increment();
    increment();
    perform Get()
} with initial_state = 0 {
    return(v) => v,
    Get(k) => resume k(state),
    Set(new_val, k) => { state = new_val; resume k(()) }
};
// final_state = 2
```

### Why This Matters for Universal Semantics

The "colored functions" problem (async infects everything) exists because async/sync are **separate mechanisms**. With algebraic effects:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  BEFORE: Different syntax for each "color"                               │
│  ─────────────────────────────────────────                               │
│  throw Exception("x")     try { } catch { }                              │
│  yield value              for x in generator { }                         │
│  await future             async fn foo() { }                             │
│                                                                          │
│  AFTER: One mechanism, different handlers                                │
│  ───────────────────────────────────────────                             │
│  perform Throw("x")       handle { } with { Throw(e,k) => ... }          │
│  perform Yield(value)     handle { } with { Yield(v,k) => ... }          │
│  perform Await(future)    handle { } with { Await(f,k) => ... }          │
│                                                                          │
│  Same AST nodes. Same compilation strategy. Different runtime behavior.  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

A function that `perform`s effects is just a function. The handler decides what those effects mean at runtime. This is **effect polymorphism** - the same code can run synchronously, asynchronously, or in a test harness that mocks effects.

---

## The Revised 2.0 Core AST

Based on research consensus, here's the complete Core AST specification. This is what the kernel understands - everything else elaborates down to this.

### Program Structure

```lisp
(program <decl>*)
```

### Declarations

```lisp
;; Functions (extended with effect annotations)
(func <name> (<param>*) (<effect>*) <ret-type> <body>)

;; Variables (unchanged)
(var <name> <type> <init>?)

;; Structs (product types - unchanged)
(struct <name> (<field-decl>*))

;; Enums (sum types - NEW)
(enum <name> (<variant-decl>*))

;; Effect declarations (NEW)
(effect <name> (<param-type>*) <resume-type>)
```

### Statements

```lisp
;; Existing
(block <stmt>*)
(if <cond> <then> <else>?)
(while <cond> <body>)
(return <expr>?)
(break <label>?)
(continue <label>?)
(expr-stmt <expr>)
(assign <target> <value>)              ; explicit assignment (NEW)

;; NEW: Let binding (expression-as-statement)
(let <name> <type>? <init> <body>)     ; lexical binding
```

### Expressions

```lisp
;; Existing (unchanged)
(binop <op> <left> <right>)
(unop <op> <expr>)
(call <func> <arg>*)
(field <expr> <name>)
(index <expr> <index>)
(ident <name>)
(number <value>)
(string <value>)
(bool <value>)
(nil)

;; First-class functions (NEW)
(lambda (<param>*) (<effect>*) <ret-type> <body>)
(closure <lambda> (<capture>*))        ; lambda + captured environment

;; Sum types (NEW)
(variant <enum-name> <variant-name> <value>?)   ; construct variant
(match <expr> (<case>*))                         ; pattern match
(case <pattern> <body>)                          ; match arm

;; Patterns for match (NEW)
(pattern-variant <name> <binding>?)    ; Some(x)
(pattern-wildcard)                      ; _
(pattern-literal <value>)              ; 42, "hello", true

;; Algebraic effects (NEW)
(perform <effect-name> <arg>*)         ; raise effect, may suspend
(handle <expr> <return-case> (<effect-case>*))
(return-case (<binding>) <body>)       ; what to do on normal return
(effect-case <effect-name> (<param>*) <k> <body>)  ; k is continuation
(resume <k> <value>?)                  ; resume continuation
```

### Types

```lisp
;; Existing
(type-base <name>)                     ; i64, u8, bool, void
(type-ptr <elem>)                      ; *T
(type-array <size> <elem>)             ; [N]T

;; NEW
(type-func (<param-type>*) (<effect>*) <ret-type>)  ; fn(i64) -> i64
(type-enum <name>)                     ; Option, Result
(type-continuation <arg-type> <ret-type>)  ; k's type
```

### Parameters and Fields

```lisp
(param <name> <type>)                  ; function parameter
(field-decl <name> <type>)             ; struct field
(variant-decl <name> <type>?)          ; enum variant (type optional for unit)
(capture <name> <type>)                ; closure capture
```

### AST Constructors (std/ast.lang additions)

```lang
// Sum types
func ast_enum(name *u8, variants *Vec) *AST;
func ast_variant_decl(name *u8, payload_type *AST) *AST;
func ast_variant(enum_name *u8, variant_name *u8, value *AST) *AST;
func ast_match(expr *AST, cases *Vec) *AST;
func ast_case(pattern *AST, body *AST) *AST;
func ast_pattern_variant(name *u8, binding *u8) *AST;
func ast_pattern_wildcard() *AST;

// First-class functions
func ast_lambda(params *Vec, effects *Vec, ret_type *AST, body *AST) *AST;
func ast_closure(lambda *AST, captures *Vec) *AST;
func ast_type_func(params *Vec, effects *Vec, ret_type *AST) *AST;

// Algebraic effects
func ast_effect_decl(name *u8, param_types *Vec, resume_type *AST) *AST;
func ast_perform(effect_name *u8, args *Vec) *AST;
func ast_handle(expr *AST, return_case *AST, effect_cases *Vec) *AST;
func ast_return_case(binding *u8, body *AST) *AST;
func ast_effect_case(name *u8, params *Vec, k_name *u8, body *AST) *AST;
func ast_resume(k *AST, value *AST) *AST;
```

---

## The Layer Cake Architecture

The kernel doesn't try to be everything. It understands a small **Core** and provides lowering passes.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Layer 3: Extended AST (Reader Output)                                   │
│  ─────────────────────────────────────                                   │
│  - Domain-specific constructs (SQL, regex, shader, etc.)                 │
│  - Syntactic sugar (for loops, list comprehensions)                      │
│  - Elaborates to Layer 2 via reader-provided transforms                  │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 2: High-Level Core (Kernel Input)                                 │
│  ───────────────────────────────────────                                 │
│  - Closures, enums, pattern matching                                     │
│  - Effects (perform/handle)                                              │
│  - THIS is what the kernel type-checks and validates                     │
│  - The stable public API for readers                                     │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 1.5: Elaborated Core (Kernel Internal)                            │
│  ─────────────────────────────────────────────                           │
│  - Closures → structs + function pointers                                │
│  - Pattern match → decision trees                                        │
│  - Effects → CPS or state machines                                       │
│  - Monomorphization happens here                                         │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 1: Low-Level Core (Current AST)                                   │
│  ──────────────────────────────────────                                  │
│  - No closures (only top-level functions)                                │
│  - No effects (only structured control flow)                             │
│  - Explicit memory operations                                            │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 0: Target (x86 / WASM / LLVM IR)                                  │
│  ──────────────────────────────────────                                  │
│  - Register allocation, instruction selection                            │
│  - Backend-specific optimizations                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key insight**: Readers produce Layer 2. The kernel lowers through Layer 1.5 → Layer 1 → Layer 0. This is **nanopass style** internally, but the public API is stable at Layer 2.

---

## Memory Model: Pluggable GC

**Non-negotiable requirement**: Memory management written in `.lang`, swappable at link time.

### The Design

The kernel provides **allocation primitives** but not policy:

```lisp
;; Memory primitives (kernel built-ins)
(mem-alloc <size>)              ; allocate size bytes, return *u8
(mem-free <ptr>)                ; mark memory as freeable
(mem-size <ptr>)                ; get allocation size
(mem-copy <dst> <src> <len>)    ; copy bytes
```

The **memory manager** is a `.lang` library that readers include:

```lang
// std/gc/none.lang - no GC, manual free (current behavior)
func alloc(size i64) *u8 {
    return mem_alloc(size);
}
func free(ptr *u8) void {
    mem_free(ptr);
}

// std/gc/refcount.lang - reference counting
struct RcHeader {
    count i64;
    size i64;
}
func rc_alloc(size i64) *u8 { ... }
func rc_retain(ptr *u8) void { ... }
func rc_release(ptr *u8) void { ... }

// std/gc/tracing.lang - mark-and-sweep
// Written entirely in lang, uses mem_* primitives
func gc_alloc(size i64) *u8 { ... }
func gc_collect() void { ... }

// std/gc/arena.lang - region-based
func arena_new() *Arena { ... }
func arena_alloc(a *Arena, size i64) *u8 { ... }
func arena_free(a *Arena) void { ... }  // free entire arena at once
```

### How It Works

1. **Readers choose memory model** by which stdlib they include
2. **Kernel emits calls to `alloc`/`free`** - doesn't know implementation
3. **Linker resolves** to chosen GC library
4. **Cross-language interop**: at boundaries, use explicit protocol (pin/unpin for GC, explicit ownership transfer for manual)

### Effect-Based GC Roots

With effects, we can make GC roots **explicit**:

```lang
// Any allocation during a handle block is tracked
var result = handle {
    var x = gc_alloc(100);  // performs Alloc effect
    var y = gc_alloc(200);
    compute(x, y)
} with gc_context {
    return(v) => { gc_collect(); v },
    Alloc(size, k) => {
        var ptr = do_gc_alloc(size);
        gc_add_root(ptr);     // track until handle exits
        resume k(ptr)
    }
};
```

This is how we get GC without baking it into the kernel.

---

## Concrete Changes Required

Based on analysis of the current codebase (`src/*.lang`), here's what needs to change:

### Phase 1: Foundation (Current → Layer 1 stable)

**Files affected**: `src/parser.lang`, `src/codegen.lang`

| Change | Location | Difficulty |
|--------|----------|------------|
| Add `let` expression | parser.lang:1400+, codegen.lang:1900+ | Easy |
| Add explicit `assign` node | parser.lang:900+, codegen.lang:1650+ | Easy |
| Add `TYPE_FUNC` to type system | codegen.lang:1166+, parser.lang:200+ | Medium |
| Support indirect calls via `call *%rax` | codegen.lang:1800+ | Easy (code exists) |

### Phase 2: First-Class Functions

**Files affected**: `src/parser.lang`, `src/codegen.lang`

| Change | Location | Difficulty |
|--------|----------|------------|
| Parse `fn(T) R` type syntax | parser.lang (new ~50 lines) | Medium |
| Parse lambda `\|x\| { body }` | parser.lang (new ~80 lines) | Medium |
| `NODE_LAMBDA_EXPR` node type | parser.lang:30+ | Easy |
| Lambda codegen (no captures) | codegen.lang (new ~100 lines) | Medium |
| Function pointer load `lea func, %rax` | codegen.lang:1750+ | Easy |

### Phase 3: Closures (Captures)

**Files affected**: `src/codegen.lang`

| Change | Location | Difficulty |
|--------|----------|------------|
| Closure struct generation | codegen.lang (new ~150 lines) | Hard |
| Capture analysis pass | codegen.lang (new ~200 lines) | Hard |
| Environment passing convention | codegen.lang:2287+ | Medium |
| Closure call convention | codegen.lang:1800+ | Medium |

**Implementation strategy**:
```
Lambda with captures:
  |x| { x + captured_y }

Compiles to:
  struct __closure_0 {
      fn *u8;           // pointer to actual function
      captured_y i64;   // captured variables
  }

  func __lambda_0(env *__closure_0, x i64) i64 {
      return x + env.captured_y;
  }
```

### Phase 4: Sum Types / Enums

**Files affected**: `src/parser.lang`, `src/codegen.lang`

| Change | Location | Difficulty |
|--------|----------|------------|
| Parse `enum Name { V1, V2(T) }` | parser.lang (new ~100 lines) | Medium |
| `NODE_ENUM_DECL`, `NODE_VARIANT_EXPR` | parser.lang:30+ | Easy |
| Enum registry (like struct registry) | codegen.lang:315+ | Easy |
| Tagged union memory layout | codegen.lang (new ~80 lines) | Medium |
| Parse `match expr { ... }` | parser.lang (new ~120 lines) | Medium |
| Match compilation to if/else tree | codegen.lang (new ~200 lines) | Hard |

**Memory layout**:
```
enum Option {
    Some(i64),
    None,
}

// Layout: [tag: 8 bytes][payload: max_variant_size bytes]
// Option: [tag: 8][value: 8] = 16 bytes
// tag 0 = Some, tag 1 = None
```

### Phase 5: Algebraic Effects

**Files affected**: `src/parser.lang`, `src/codegen.lang` (major additions)

| Change | Location | Difficulty |
|--------|----------|------------|
| Parse `effect` declarations | parser.lang (new ~60 lines) | Medium |
| Parse `perform Effect(args)` | parser.lang (new ~40 lines) | Easy |
| Parse `handle { } with { }` | parser.lang (new ~150 lines) | Hard |
| Effect registry | codegen.lang (new ~50 lines) | Easy |
| **CPS transform** or **state machine** | codegen.lang (new ~500+ lines) | **Very Hard** |
| Handler stack runtime | std/effect_runtime.lang (new file) | Hard |

**Implementation options**:

1. **Full CPS Transform** (most general, hardest)
   - Every function becomes `(args..., k) → never_returns`
   - perform = call handler with current k
   - Very invasive, changes all codegen

2. **State Machine Transform** (practical for single-shot)
   - Only transform functions that perform effects
   - Convert to state machine like Rust async
   - Good for async/generators, not full continuations

3. **Stack Copying** (runtime support)
   - On perform, copy stack frames to heap
   - On resume, restore stack
   - Needs runtime support but less codegen change

**Recommended approach**: Start with **state machine transform** for one-shot effects (exceptions, generators, async). This is what Rust, Kotlin, and C# do. Full CPS can come later if needed.

### Phase 6: The Big Refactor (Kernel Split)

Once effects work, we can cleanly separate kernel from lang_reader:

```
Current structure (monolithic):
  src/lexer.lang      → tokenize lang syntax
  src/parser.lang     → parse lang syntax
  src/codegen.lang    → compile AST
  src/main.lang       → CLI driver

New structure (kernel + reader):
  kernel/
    sexpr.lang        → parse S-expressions
    ast.lang          → AST node types + validation
    typecheck.lang    → type checking
    lower.lang        → Layer 2 → Layer 1 transforms
    codegen.lang      → Layer 1 → x86
    main.lang         → kernel CLI

  readers/
    lang/
      lexer.lang      → tokenize lang syntax
      parser.lang     → parse to AST
      main.lang       → reader CLI (stdin → stdout)
```

---

## Implementation Order

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                           │
│  1. let + assign nodes           (1 day)   ← Foundation                   │
│  2. TYPE_FUNC + indirect calls   (2 days)  ← Enable func pointers         │
│  3. Lambda (no captures)         (2 days)  ← First-class functions        │
│  4. Closures (captures)          (4 days)  ← Real lambdas                 │
│  5. Enum + variant               (3 days)  ← Sum types                    │
│  6. Pattern matching             (3 days)  ← match expressions            │
│  7. Effect declarations          (2 days)  ← Effect signatures            │
│  8. perform (exceptions only)    (3 days)  ← Non-resumable effects        │
│  9. handle + resume              (5 days)  ← Resumable effects            │
│  10. Kernel/reader split         (5 days)  ← Architecture migration       │
│                                                                           │
│  Total: ~30 days of focused work                                          │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

Steps 1-6 can be done incrementally without breaking existing code. Steps 7-9 (effects) are the "parachute" - they need to work together. Step 10 is the architectural payoff.

---

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
| Memory model | Pluggable (manual, refcount, GC - see Memory Model section) |

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

## Pre-Flight Checklist: Are We Ready to Jump?

Before implementing the 2.0 AST, we need to verify these foundations are solid:

### ✅ Things We Have

| Capability | Status | Evidence |
|------------|--------|----------|
| Self-hosting compiler | ✅ Done | Fixed point verified |
| Struct support | ✅ Done | Used throughout stdlib |
| Pointer arithmetic | ✅ Done | Manual memory works |
| Reader macro infrastructure | ✅ Done | `#parser{}`, `#lisp{}` work |
| Indirect function calls | ✅ Done | `call *%rax` in codegen |
| String handling | ✅ Done | String pool in .rodata |

### ⚠️ Things to Verify First

| Capability | Question | How to Test |
|------------|----------|-------------|
| Stack frame size | Can we grow beyond 4KB? | Try 1000 locals in one function |
| Struct-in-struct | Do nested structs work? | `struct A { b B; }` |
| Function pointers | Can we store `&func` in var? | `var f *u8 = &my_func; (*f)();` |
| Computed goto | Can we jump to address? | May need for state machines |

### 🚨 Known Risks

**Risk 1: State Machine Transform Complexity**

The effect system relies on transforming effectful functions into state machines. This is non-trivial:

```
func gen() void {
    var x = 1;
    perform Yield(x);   // state 0 → state 1
    x = x + 1;
    perform Yield(x);   // state 1 → state 2
}

// Must transform to:
struct gen_state {
    state i64;
    x i64;
}
func gen_step(s *gen_state) YieldResult {
    if s.state == 0 {
        s.x = 1;
        s.state = 1;
        return Yielded(s.x);
    }
    if s.state == 1 {
        s.x = s.x + 1;
        s.state = 2;
        return Yielded(s.x);
    }
    return Done;
}
```

**Mitigation**: Start with exceptions (no resume needed). Add generators second. Async last.

**Risk 2: Closure Environment Lifetimes**

Closures capture variables. What if the captured variable's stack frame is gone?

```lang
func make_adder(n i64) fn(i64) i64 {
    return |x| { x + n };  // n lives on make_adder's stack
}                          // make_adder returns, stack gone
                           // but closure still references n!
```

**Mitigation**: Copy captured values into closure struct (not reference). This means closures capture by value, not by reference. For mutable captures, box them explicitly.

**Risk 3: Effect Type Checking**

Effects need to be tracked in the type system. A function that `perform`s must declare its effects:

```lang
func risky() i64 performs Throw {  // must declare
    perform Throw("error");
}

func caller() i64 {
    risky();  // ERROR: unhandled effect Throw
}

func safe_caller() i64 {
    handle { risky() } with { Throw(e,k) => 0 }  // OK: handled
}
```

**Mitigation**: Effect checking is a separate pass. Start with unchecked effects (like Go's panics), add checking later.

**Risk 4: Performance Cliff**

If every function becomes a state machine, performance tanks. We need to only transform functions that actually perform effects.

**Mitigation**: Effect inference. Functions that don't perform can stay fast. Only effectful functions get transformed.

### 📋 Minimum Viable Effect System

To validate the architecture without building everything:

1. **Just exceptions first**: `perform Throw(msg)` + `handle { } with { Throw(e,k) => ... }`
2. **No resume**: Handler never calls `k`, so no state machine needed
3. **Setjmp/longjmp style**: Store handler address, jump on perform
4. **Test case**: Rewrite stdlib error handling to use effects

If this works, we know the AST nodes are right. Then add resume.

### 🎯 Success Criteria for 2.0

The 2.0 architecture is "done" when:

1. **lang_reader.lang** compiles to AST S-expressions that the kernel accepts
2. **kernel** compiles those S-expressions to working x86
3. **Fixed point** achieved: kernel + lang_reader can compile themselves
4. **Effects demo**: A generator written with `perform Yield` works
5. **Cross-syntax**: Same program in lang syntax and lisp syntax produces identical output

### 📚 Required Reading Before Implementation

1. **"Effect Handlers in Scope"** (Wu & Schrijvers, 2015) - How effects compose
2. **"Compiling with Continuations"** (Appel, 1992) - CPS transform details
3. **Rust async internals** - How state machines are generated
4. **Koka language** - Cleanest effect implementation to study

---

## Conclusion

The AST format is the true language. "Lang" is just syntax - one of many possible skins on the AST. By formalizing the AST as an S-expression interchange format, we achieve:

1. **Complete syntax freedom** - any reader, any syntax
2. **Minimal kernel** - just AST → x86
3. **Cross-language interop** - everything compiles to the same AST
4. **Clean separation** - readers handle syntax, kernel handles semantics

The 2.0 additions (closures, sum types, algebraic effects) unlock **universal semantics** - the ability to express not just C-like languages, but ML, async, generators, and more. Effects are the "one primitive to rule them all" that subsumes exceptions, async, and control flow.

This is what "compiler compiler" really means. Not a tool that helps you write compilers - a compiler that IS a compiler-writing system.

---

*"The AST is the music. The syntax is just the notation."*

*"Effects are the one ring. Handle wisely."*
