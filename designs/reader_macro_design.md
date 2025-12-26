# Phase 3: Reader Macros

**Status**: DESIGN FINALIZED - Ready for implementation

## Design Decisions

| Question | Decision | Rationale |
|----------|----------|-----------|
| Trigger syntax | `#name{...}` | Braces are visually distinct, familiar from other langs |
| Macro input | Raw text | Full control; tokenizer provided but optional |
| Macro output | AST nodes | Direct, efficient, no re-parsing |
| Definition location | Separate file import | Clean separation, avoids bootstrap issues |

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
#name{content}   // Reader macro "name" receives content between balanced {}
```

The content is **raw text** with balanced braces. Nested `{...}` are included in the content.

### Import Syntax

```lang
import "readers/lisp.lang"   // Import reader macro definitions

var x i64 = #lisp{+ 1 (* 2 3)};
```

The import must appear before usage. Reader macro files are parsed and run through the compile-time interpreter; `reader` declarations become available.

### Reader Definition Syntax

```lang
// In readers/lisp.lang
reader lisp(text *u8) *u8 {
    // text contains the raw content between braces
    // returns AST node pointer
    var sexpr *u8 = parse_sexpr(text);
    return sexpr_to_ast(sexpr);
}
```

Reader macros run in the **compile-time interpreter** (same as AST macros). They have access to:
- Standard library functions (vec, map, str operations)
- Compiler-provided AST construction functions
- Optionally, the host language's tokenizer

### Compiler-Provided Functions

For building AST nodes:
```lang
func lang_number_expr(value i64) *u8;
func lang_ident_expr(name *u8) *u8;
func lang_string_expr(value *u8) *u8;
func lang_binary_expr(op i64, left *u8, right *u8) *u8;
func lang_unary_expr(op i64, operand *u8) *u8;
func lang_call_expr(func *u8, args *u8, arg_count i64) *u8;
func lang_if_stmt(cond *u8, then_block *u8, else_block *u8) *u8;
func lang_while_stmt(cond *u8, body *u8) *u8;
func lang_var_decl(name *u8, typ *u8, init *u8) *u8;
func lang_block_stmt(stmts *u8, count i64) *u8;
func lang_return_stmt(value *u8) *u8;
// ... more as needed
```

For optional tokenizer access:
```lang
func lang_tokenize(text *u8) *u8;     // returns vec of tokens
func lang_tok_type(tok *u8) i64;
func lang_tok_lexeme(tok *u8) *u8;
func lang_tok_lexeme_len(tok *u8) i64;
```

Operator constants:
```lang
var OP_ADD i64 = 1;
var OP_SUB i64 = 2;
var OP_MUL i64 = 3;
// ... etc
```

---

## Example: Lisp-lite (Flagship Example)

This is the core demonstration of "lang lang" - you can write other languages in it.

### Usage

```lang
import "readers/lisp.lang"

var result i64 = #lisp{+ 1 (* 2 3)};  // Compiles to: 1 + (2 * 3)

// More complex
var answer i64 = #lisp{
    (let ((x 10)
          (y 32))
      (+ x y))
};
// Compiles to block: { var x i64 = 10; var y i64 = 32; return x + y; }
```

### Supported Forms (v1)

| Lisp Form | Compiles To |
|-----------|-------------|
| `42` | `42` (number literal) |
| `foo` | `foo` (identifier) |
| `(+ a b)` | `a + b` |
| `(- a b)` | `a - b` |
| `(* a b)` | `a * b` |
| `(/ a b)` | `a / b` |
| `(% a b)` | `a % b` |
| `(< a b)` | `a < b` |
| `(> a b)` | `a > b` |
| `(<= a b)` | `a <= b` |
| `(>= a b)` | `a >= b` |
| `(== a b)` | `a == b` |
| `(!= a b)` | `a != b` |
| `(if c t e)` | `if c { t } else { e }` |
| `(let ((x v)) body)` | `{ var x = v; body }` |
| `(progn e1 e2 ...)` | `{ e1; e2; ... }` |
| `(while c body)` | `while c { body }` |
| `(set! x v)` | `x = v` |
| `(funcall f args...)` | `f(args...)` |

### Implementation (in readers/lisp.lang)

```lang
// S-expression representation
// Atom: [kind:8][value:8] where kind=0 for number, kind=1 for symbol
// List: [kind:8][elements:8][count:8] where kind=2

reader lisp(text *u8) *u8 {
    var sexpr *u8 = parse_sexpr(text);
    return sexpr_to_ast(sexpr);
}

func parse_sexpr(text *u8) *u8 {
    // Skip whitespace, then:
    // - If digit: parse number atom
    // - If '(': parse list recursively
    // - Otherwise: parse symbol atom
    // ...
}

func sexpr_to_ast(s *u8) *u8 {
    var kind i64 = sexpr_kind(s);

    if kind == SEXPR_NUMBER {
        return lang_number_expr(sexpr_number_value(s));
    }

    if kind == SEXPR_SYMBOL {
        return lang_ident_expr(sexpr_symbol_name(s));
    }

    if kind == SEXPR_LIST {
        var head *u8 = sexpr_list_head(s);
        var op *u8 = sexpr_symbol_name(head);

        if streq(op, "+") {
            return lang_binary_expr(OP_ADD,
                sexpr_to_ast(sexpr_list_nth(s, 1)),
                sexpr_to_ast(sexpr_list_nth(s, 2)));
        }
        // ... other operators
    }

    return nil;
}
```

### File Structure

```
example/lisp/
├── readers/
│   └── lisp.lang        # The reader macro implementation
├── factorial.lang       # (defun factorial (n) ...)
├── fibonacci.lang       # Recursive fib
├── arithmetic.lang      # Basic math examples
└── README.md
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

### Step 1: Lexer Changes (src/lexer.lang)

Add `#name{...}` recognition:

```lang
// New token type
var TOKEN_READER_MACRO i64 = 45;  // or next available

// In scan_token():
if c == 35 {  // '#'
    return scan_reader_macro();
}

func scan_reader_macro() *u8 {
    // 1. Read identifier (the reader name)
    // 2. Expect '{'
    // 3. Read balanced content (track nesting, handle strings)
    // 4. Return token with name and content
}
```

Token stores: reader name, content start pointer, content length.

### Step 2: Parser Changes (src/parser.lang)

Add `import` statement and reader macro handling:

```lang
// New AST node type
var NODE_IMPORT i64 = 24;

// In parse_declaration():
if parse_match(TOKEN_IMPORT) {
    return parse_import();
}

// In parse_primary():
if parse_check(TOKEN_READER_MACRO) {
    return parse_reader_macro_call();
}

func parse_reader_macro_call() *u8 {
    var tok *u8 = parse_advance();
    var name *u8 = reader_macro_name(tok);
    var content *u8 = reader_macro_content(tok);

    // Look up reader in registry
    var reader_fn *u8 = find_reader_macro(name);
    if reader_fn == nil {
        parse_error("unknown reader macro");
        return nil;
    }

    // Call it via interpreter
    return interp_call_reader(reader_fn, content);
}
```

### Step 3: Reader Registry (src/codegen.lang)

```lang
// Reader macro registry (name -> function AST node)
var reader_macros *u8 = nil;  // map

func register_reader_macro(name *u8, func_node *u8) void;
func find_reader_macro(name *u8) *u8;

// Process imports: parse file, find reader declarations, register them
func process_import(path *u8) void {
    var source *u8 = read_file(path);
    var ast *u8 = parse(source);

    // Find all reader declarations and register
    // Run through interpreter to make functions available
}
```

### Step 4: AST Construction Builtins (src/codegen.lang)

Add to compile-time interpreter:

```lang
// In interp_call(), handle special function names:
if streq(func_name, "lang_number_expr") {
    var value i64 = interp_expr(arg0);
    return number_expr_alloc_with_value(value);
}
if streq(func_name, "lang_binary_expr") {
    var op i64 = interp_expr(arg0);
    var left *u8 = interp_expr(arg1);
    var right *u8 = interp_expr(arg2);
    return binary_expr_alloc_with(op, left, right);
}
// ... etc
```

### Step 5: Reader Declaration Parsing

```lang
// New keyword
var TOKEN_READER i64 = 46;

// In parse_declaration():
if parse_match(TOKEN_READER) {
    return parse_reader_decl();
}

// Similar to parse_func_decl but marks as reader macro
```

### Step 6: Lisp Reader (example/lisp/readers/lisp.lang)

Implement in the language itself:
1. S-expression parser (recursive descent)
2. S-expr to AST transformer
3. Register as `reader lisp`

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

## Implementation Order

1. **Lexer**: `#name{...}` token scanning with balanced braces
2. **Parser**: `import` statement, reader macro invocation
3. **Registry**: Reader macro storage, lookup
4. **Interpreter builtins**: `lang_number_expr`, `lang_binary_expr`, etc.
5. **Reader declaration**: `reader name(text) { }` syntax
6. **Lisp reader**: Full implementation in `example/lisp/`

Each step should be testable independently before moving to the next.
