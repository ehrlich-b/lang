# Phase 3: Reader Macros

## The Big Picture

**Phase 2 (AST macros)**: Transform AST → AST. The parser already did its job.

**Phase 3 (Reader macros)**: Transform text → AST. You control how text is parsed.

```
Source Text
    │
    ▼
┌─────────────────┐
│  READER MACROS  │  ← Phase 3: Custom parsing
└─────────────────┘
    │
    ▼
┌─────────────────┐
│     Parser      │  ← Normal parsing
└─────────────────┘
    │
    ▼
┌─────────────────┐
│   AST MACROS    │  ← Phase 2: AST transformation
└─────────────────┘
    │
    ▼
┌─────────────────┐
│    Codegen      │
└─────────────────┘
```

They're **complementary**, not competing. Reader macros produce AST that can then be further transformed by AST macros.

---

## Why Reader Macros?

AST macros are powerful, but they're stuck with the language's syntax:

```lang
macro double(x) { return ${ $x + $x }; }

var n i64 = double(5);  // Still looks like a function call
```

What if you want:
- S-expression syntax: `(+ 1 (* 2 3))`
- SQL literals: `SELECT * FROM users WHERE id = 5`
- Regex literals: `/[a-z]+/`
- Custom DSLs that look nothing like the host language

You can't do this with AST macros because the parser would choke before the macro ever runs.

---

## Design Space

### Question 1: How is a reader macro triggered?

| Approach | Example | Pros | Cons |
|----------|---------|------|------|
| **Prefix sigil** | `#lisp(...)` | Clear, unambiguous | Uses up `#` namespace |
| **Keyword block** | `reader lisp { ... }` | Readable | Verbose |
| **Backtick block** | `` `lisp ... ` `` | Familiar (markdown) | Backtick conflicts |
| **Comment pragma** | `//! lang: lisp` | Non-invasive | Weird |
| **File extension** | `.lisp.lang` | Simple | One syntax per file |

**Recommendation**: Start with **prefix sigil** `#name(...)` or `#name{...}`.

### Question 2: What does the reader macro receive?

| Option | What macro sees | Pros | Cons |
|--------|-----------------|------|------|
| **Raw text** | `"(+ 1 2)"` | Full control | Must handle everything |
| **Token stream** | `[LPAREN, PLUS, INT(1), INT(2), RPAREN]` | Structured | Limited to our tokens |
| **Balanced delimiters only** | Text between `(...)` or `{...}` | Predictable end | Less flexible |

**Recommendation**: **Balanced delimiters with raw text**. The sigil specifies which delimiter: `#lisp(...)` captures everything between balanced parens as a string.

### Question 3: What does the reader macro return?

| Option | Returns | Pros | Cons |
|--------|---------|------|------|
| **AST node** | `*u8` (our AST) | Direct, efficient | Must know AST internals |
| **Quoted expression** | `${ ... }` | Reuses Phase 2 | May be limiting |
| **Source text** | `*u8` (code string) | Simple | Requires re-parsing |

**Recommendation**: **AST node**. Reader macros are already advanced; let them build AST directly.

### Question 4: When is the reader macro defined?

This is the tricky one.

**The Bootstrap Problem**: To use a reader macro, it must be compiled first. But how do you compile it if it's in the same file?

| Approach | How it works | Pros | Cons |
|----------|--------------|------|------|
| **Built-in only** | Reader macros are part of compiler | Simple | Not extensible |
| **Separate file** | `import "lisp_reader.lang"` | Clear | Separate compilation |
| **Two-pass** | First pass finds reader macros, second uses them | Single file | Complex |
| **Interpreter** | Reader macros run interpreted | Flexible | Performance |

**Recommendation**: Start with **built-in** reader macros (like `#lisp`), then add **separate file** imports.

---

## Concrete Proposal

### Syntax

```lang
#name(content)   // Parens: reader macro "name" receives content between ()
#name{content}   // Braces: reader macro "name" receives content between {}
#name[content]   // Brackets: reader macro "name" receives content between []
```

The content is **raw text** with balanced delimiters. Nested matching delimiters are included.

### Defining Reader Macros (Built-in First)

Initially, reader macros are implemented in the compiler itself. We ship with:

- `#lisp(...)` - S-expression syntax
- `#raw(...)` - Raw string (no escapes)

Later, we can add a way to define them in user code.

### User-Defined Reader Macros (Future)

```lang
reader lisp(text *u8) *u8 {
    // text contains the raw content between delimiters
    // returns AST node
    var sexpr *u8 = parse_sexpr(text);
    return sexpr_to_ast(sexpr);
}
```

**Challenge**: The functions `parse_sexpr` and `sexpr_to_ast` need to run at compile time. They'd need to be interpreted or pre-compiled.

---

## Example: Lisp-lite

### Usage

```lang
var result i64 = #lisp(+ 1 (* 2 3));  // Compiles to: 1 + (2 * 3)

// More complex
var answer i64 = #lisp(
    (let ((x 10)
          (y 32))
      (+ x y))
);
// Compiles to: { var x = 10; var y = 32; x + y; }
```

### Implementation (in compiler)

```c
// Pseudo-code for built-in #lisp reader macro
AST* reader_lisp(char* text) {
    SExpr* sexpr = parse_sexpr(text);
    return sexpr_to_ast(sexpr);
}

AST* sexpr_to_ast(SExpr* s) {
    if (is_number(s)) {
        return make_number_expr(s->value);
    }
    if (is_symbol(s)) {
        return make_ident_expr(s->name);
    }
    if (is_list(s)) {
        char* op = s->head->name;
        if (streq(op, "+")) {
            return make_binary(OP_ADD,
                sexpr_to_ast(s->args[0]),
                sexpr_to_ast(s->args[1]));
        }
        // ... etc
    }
}
```

---

## Example: Raw Strings

No escape processing:

```lang
var path *u8 = #raw(C:\Users\Name\Documents);
// Equivalent to: "C:\\Users\\Name\\Documents"

var regex *u8 = #raw([a-z]+\d{3});
// Equivalent to: "[a-z]+\\d{3}"
```

---

## Example: SQL (Future)

```lang
var query *u8 = #sql(
    SELECT name, email
    FROM users
    WHERE id = $user_id
);
// Compiles to: "SELECT name, email FROM users WHERE id = " + itoa(user_id)
// With $user_id being unquoted from surrounding scope
```

This shows reader macros combining with unquote syntax for interpolation.

---

## How It Fits With Phase 2 Macros

Reader macros and AST macros compose:

```lang
macro twice(x) {
    return ${ $x + $x };
}

// Reader macro produces AST, then AST macro transforms it
var n i64 = twice(#lisp(* 3 4));
// Reader: #lisp(* 3 4) → AST for (3 * 4)
// AST macro: twice(...) → AST for ((3 * 4) + (3 * 4))
// Result: n = 24
```

The reader macro runs first (during parsing), then the AST macro runs (during expansion).

---

## Implementation Plan

### Step 1: Lexer Changes

- Recognize `#` followed by identifier as `TOKEN_READER_MACRO`
- After reader macro name, capture balanced delimiter content as raw text

```lang
#lisp(+ 1 2)
      ↑     ↑
      start end (balanced parens)
```

### Step 2: Parser Changes

- When seeing `TOKEN_READER_MACRO`, look up the reader macro by name
- Call the reader macro with the raw text
- Insert returned AST node into the parse tree

### Step 3: Built-in Reader Macros

Implement directly in the compiler:
- `#lisp` - S-expression parser + transformer
- `#raw` - Raw string (trivial: just wrap in string node)

### Step 4: User-Defined (Future)

- Add `reader name(text) { }` syntax
- Reader macro bodies run in the compile-time interpreter
- Need to expose AST construction functions to the interpreter

---

## Open Questions

### 1. Unquoting in Reader Macros

Should reader macros support unquoting from the surrounding scope?

```lang
var x i64 = 10;
var result i64 = #lisp(+ $x 5);  // Should $x work?
```

**Options**:
- **No unquoting**: Reader macros are pure text transformers
- **Explicit syntax**: Use `$x` inside reader macro content
- **Reader decides**: Each reader macro defines its own interpolation syntax

**Recommendation**: Let each reader macro define its own. `#lisp` might use `,x` (like real Lisp unquote).

### 2. Multi-Expression Results

Can a reader macro produce multiple top-level declarations?

```lang
#define_enum(
    Color: Red Green Blue
)
// Expands to:
// var Color_Red i64 = 0;
// var Color_Green i64 = 1;
// var Color_Blue i64 = 2;
```

**Answer**: Probably need a "splice multiple" mechanism. Or reader macros only produce expressions/statements, not declarations.

### 3. Error Reporting

When a reader macro fails, how do we report useful errors?

```lang
#lisp(+ 1 2 3 4)  // Lisp + is binary, this is wrong
```

**Options**:
- Reader macro returns error node with message
- Reader macro calls `reader_error("message")`
- Crash with generic "reader macro failed"

### 4. Nesting

Can reader macros nest?

```lang
#lisp(+ 1 #sql(SELECT max(x) FROM t))
```

**Answer**: Probably not initially. Keep it simple. One reader macro per expression.

---

## What This Enables

With reader macros, you could:

1. **Embed DSLs**: SQL, regex, HTML templates
2. **Create entire sublanguages**: Lisp-like, APL-like, logic programming
3. **Literal syntax**: JSON, XML, data formats
4. **Compile-time computation**: Calculator syntax, matrix notation

The language becomes a platform for other languages.

---

## Summary

| Concept | Phase 2 (AST Macros) | Phase 3 (Reader Macros) |
|---------|---------------------|------------------------|
| Input | Parsed AST | Raw text |
| Output | Transformed AST | New AST |
| Runs when | After parsing | During parsing |
| Trigger | Function call syntax | `#name(...)` sigil |
| Can change | What code means | How code looks |

Reader macros don't replace AST macros—they enable entirely new syntaxes that AST macros can then transform.

---

## Minimal First Version

For a first implementation:

1. Add `#raw(...)` - trivial, proves the mechanism works
2. Add `#lisp(...)` - S-expressions for arithmetic only
3. Built-in only, no user-defined reader macros yet

This gets us:
- Proof of concept for syntax extension
- A working Lisp-lite embedded in the language
- Foundation for more ambitious reader macros later
