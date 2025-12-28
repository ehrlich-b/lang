# AST Interchange Format Design

## The Change

**Current:** Reader macros are TEXT → TEXT
```
#lisp{ (+ 1 2) }  →  lisp_reader  →  "(1 + 2)"  →  parse again  →  AST
```

**Target:** Reader macros are TEXT → AST
```
#lisp{ (+ 1 2) }  →  lisp_reader  →  AST  →  compile
```

This is a fundamental architectural shift. Readers become first-class AST producers, not text preprocessors.

## Why This Matters

1. **No re-parsing** - Reader output goes directly to codegen
2. **More expressive** - Readers can produce AST that has no lang syntax equivalent
3. **Cleaner architecture** - Readers and kernel have a contract (the AST spec)
4. **Enables kernel split** - Kernel accepts AST, readers produce AST

## The Decision: What Format?

### Option 1: S-Expressions (Text)

```lisp
(func add ((param x (type-base i64)) (param y (type-base i64)))
  (type-base i64)
  (block (return (binop + (ident x) (ident y)))))
```

**Pros:**
- Human readable - can `cat` output and understand it
- Easy to debug - when reader produces wrong output, you can see it
- Simple to implement - just string concatenation in readers
- Proven - Lisp/Racket have used this for 60+ years
- Easy to test - write expected output as literal strings
- Version-tolerant - adding new node types doesn't break old parsers
- Cross-platform - no endianness issues

**Cons:**
- Parsing overhead (but at compile time, not runtime)
- String escaping complexity (strings inside strings)
- Verbose (larger intermediate files)

### Option 2: Binary Format

```
[node_type:u8][payload_len:u16][payload...]

Example for (binop + (number 1) (number 2)):
0x09 0x12 0x00  // NODE_BINARY_EXPR, len=18
  0x2B          // op = '+'
  0x0F 0x09 0x00 0x01 0x00 0x00 0x00 0x00 0x00 0x00  // number 1
  0x0F 0x09 0x00 0x02 0x00 0x00 0x00 0x00 0x00 0x00  // number 2
```

**Pros:**
- Fast to read/write - no parsing, just memcpy
- Compact - smaller intermediate files
- No escaping issues - bytes are bytes
- Can memory-map directly

**Cons:**
- Not human readable - debugging is hard
- Versioning is tricky - field order matters
- Endianness - need to specify byte order
- Harder to write readers - need to emit exact bytes
- No partial validity - corrupt byte corrupts everything

### Option 3: In-Memory Structs (Pointers)

Readers linked into compiler, share address space, pass AST node pointers directly.

**Pros:**
- Zero serialization cost
- Direct manipulation
- Type-safe (in theory)

**Cons:**
- Only works for in-process readers
- Can't cache to disk
- Can't run readers in sandbox
- Memory layout must match exactly
- No isolation - reader bug corrupts compiler

## Recommendation: S-Expressions

For this project, **S-expressions are the right choice**. Here's why:

### 1. Debuggability Trumps Performance

This is a hobby/learning project. When something goes wrong (and it will), being able to:
```bash
./lisp_reader < test.lisp > /tmp/ast.sexpr
cat /tmp/ast.sexpr  # Actually readable!
```
...is invaluable. With binary, you'd need hex dumps and manual decoding.

### 2. Compile-Time Cost is Acceptable

Reader macros run at compile time. The user waits anyway. Parsing a few KB of S-expressions takes microseconds on modern CPUs. The real work is codegen.

Rough math:
- Parse 10KB of S-expressions: ~1ms
- Compile 10KB of code to x86: ~100ms

The S-expression overhead is noise.

### 3. Readers Are Easier to Write

With S-expressions, a reader author writes:
```lang
func emit_binop(op *u8, left *u8, right *u8) *u8 {
    return str_concat("(binop ", op, " ", left, " ", right, ")");
}
```

With binary, they'd need to carefully emit exact bytes in exact order. More error-prone, harder to debug.

### 4. Proven Technology

Lisp has used S-expressions for code-as-data for 60+ years. Racket's `#lang` produces S-expression syntax objects. This isn't novel - it's battle-tested.

### 5. Future Optimization Path

If S-expression parsing ever becomes a bottleneck (unlikely), we can add binary as an **optional optimization**:
- S-expressions remain the canonical format
- `--fast-ast` flag enables binary
- Binary is defined as "the obvious encoding of S-expressions"

This gives us debuggability now, performance later if needed.

## S-Expression AST Specification

### Grammar

```
ast        ::= atom | list
atom       ::= number | string | symbol
list       ::= '(' ast* ')'
number     ::= '-'? [0-9]+
string     ::= '"' (escape | [^"\\])* '"'
symbol     ::= [a-zA-Z_][a-zA-Z0-9_-]*
escape     ::= '\\' [nrt"\\0]
whitespace ::= [ \t\n\r]+  (ignored between tokens)
comment    ::= ';' [^\n]* '\n'  (ignored)
```

### Node Types

Each AST node is a list starting with a symbol (the node type):

```lisp
;; ═══════════════════════════════════════════════════════════════
;; PROGRAM
;; ═══════════════════════════════════════════════════════════════

(program <decl>*)

;; ═══════════════════════════════════════════════════════════════
;; DECLARATIONS
;; ═══════════════════════════════════════════════════════════════

(func <name> (<param>*) <ret-type> <body>)
(var <name> <type> <init>?)
(struct <name> (<field>*))
(enum <name> (<variant>*))
(effect <name> (<param-type>*) <resume-type>)
(macro <name> (<param-name>*) <body>)
(reader <name> <param-name> <body>)
(include <path>)

;; ═══════════════════════════════════════════════════════════════
;; STATEMENTS
;; ═══════════════════════════════════════════════════════════════

(block <stmt>*)
(if <cond> <then> <else>?)
(while <cond> <body> <label>?)
(return <expr>?)
(break <label>?)
(continue <label>?)
(expr-stmt <expr>)
(assign <target> <value>)

;; ═══════════════════════════════════════════════════════════════
;; EXPRESSIONS
;; ═══════════════════════════════════════════════════════════════

(ident <name>)
(number <value>)
(string <value>)
(bool <value>)
(nil)

(binop <op> <left> <right>)
(unop <op> <expr>)
(call <func> <arg>*)
(field <expr> <name>)
(index <expr> <index>)

(lambda (<param>*) <ret-type> <body>)
(let <name> <type>? <init> <body>)

(variant <enum> <variant> <value>?)
(match <expr> (<case>*))
(case <pattern> <body>)

(perform <effect> <arg>*)
(handle <expr> <return-handler> (<effect-handler>*))
(resume <k> <value>?)

;; ═══════════════════════════════════════════════════════════════
;; PATTERNS
;; ═══════════════════════════════════════════════════════════════

(pattern-var <name>)
(pattern-wildcard)
(pattern-literal <value>)
(pattern-variant <enum> <variant> (<sub-pattern>*))

;; ═══════════════════════════════════════════════════════════════
;; TYPES
;; ═══════════════════════════════════════════════════════════════

(type-base <name>)           ; i64, u8, bool, void, MyStruct
(type-ptr <elem>)            ; *T
(type-array <size> <elem>)   ; [N]T
(type-func (<param-type>*) <ret-type>)      ; fn(T) R
(type-closure (<param-type>*) <ret-type>)   ; closure(T) R

;; ═══════════════════════════════════════════════════════════════
;; SUPPORTING
;; ═══════════════════════════════════════════════════════════════

(param <name> <type>)
(field-decl <name> <type>)
(variant-decl <name> <payload-type>?)
(return-handler <binding> <body>)
(effect-handler <name> (<param>*) <k> <body>)
```

### Example: Complete Program

**Lang syntax:**
```lang
func factorial(n i64) i64 {
    if n <= 1 {
        return 1;
    }
    return n * factorial(n - 1);
}

func main() i64 {
    return factorial(5);
}
```

**S-expression AST:**
```lisp
(program
  (func factorial ((param n (type-base i64))) (type-base i64)
    (block
      (if (binop <= (ident n) (number 1))
        (block (return (number 1))))
      (return (binop * (ident n)
                (call (ident factorial)
                  (binop - (ident n) (number 1)))))))
  (func main () (type-base i64)
    (block
      (return (call (ident factorial) (number 5))))))
```

## Implementation Plan

### Phase 1: AST Emitter

Add `--emit-ast` flag to compiler:
```bash
./out/lang --emit-ast test/hello.lang -o /tmp/hello.ast
cat /tmp/hello.ast  # S-expression output
```

This proves we can serialize AST to S-expressions.

### Phase 2: AST Reader

Add `--from-ast` flag to compiler:
```bash
./out/lang --from-ast /tmp/hello.ast -o hello.s
```

This proves we can deserialize S-expressions back to AST.

### Phase 3: Round-Trip Verification

```bash
./out/lang --emit-ast test.lang -o /tmp/a.ast
./out/lang --from-ast /tmp/a.ast -o /tmp/a.s
./out/lang test.lang -o /tmp/b.s
diff /tmp/a.s /tmp/b.s  # Should be identical
```

### Phase 4: Reader Protocol Change

Change readers from TEXT → TEXT to TEXT → AST:
- Reader writes S-expression AST to stdout
- Compiler reads S-expression AST from reader output
- Compiler no longer re-parses reader output as lang

### Phase 5: AST Constructor Library

Create `std/ast.lang` for reader authors:
```lang
include "std/ast.lang"

reader my_dsl(text *u8) *u8 {
    var expr *AST = ast_binop("+", ast_number(1), ast_number(2));
    return ast_emit(expr);  // Emits S-expression
}
```

Reader authors never write S-expression strings directly.

## Why Not Both? (Text + Binary)

We could support both formats:
- S-expressions for development/debugging
- Binary for production builds

But this adds complexity:
- Two parsers to maintain
- Two emitters to maintain
- Subtle bugs from format differences

Better to start simple. Add binary only if profiling shows S-expression parsing is a real bottleneck (unlikely).

## Comparison to Other Systems

| System | AST Format | Notes |
|--------|------------|-------|
| Racket | S-expressions | With source locations, scopes |
| GCC | GIMPLE (internal) | Not serialized |
| LLVM | LLVM IR (text/bitcode) | Bitcode for speed |
| Rust | HIR/MIR (internal) | Not exposed |
| Our system | S-expressions | Simple, debuggable |

We're closest to Racket's approach, but simpler (no syntax objects, no hygiene).

## Open Questions

1. **Source locations?** Should AST nodes carry line/column info?
   - Pro: Better error messages
   - Con: More complexity, larger output
   - Decision: Defer. Add later if needed.

2. **Comments?** Should AST preserve comments?
   - Pro: Documentation tools
   - Con: More complexity
   - Decision: No. Comments are stripped.

3. **Whitespace?** Pretty-print S-expressions or single line?
   - Pro (pretty): Readable
   - Con (pretty): Harder to parse (need to handle indentation)
   - Decision: Pretty-print with simple rules (indent nested lists)

## Conclusion

S-expressions are the right choice for AST interchange:
- Debuggable (critical for a learning project)
- Simple to implement
- Proven technology
- Performance is fine for compile-time use
- Binary optimization path exists if ever needed

The key insight: **debuggability during development is worth more than microseconds at compile time.**
