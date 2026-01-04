# Float Support Design

**Status:** ✅ Implemented
**Implemented:** 2025-01-04

## Summary

`f32` and `f64` floating-point types in lang. LLVM backend only (x86 backend frozen).

## What Works

- **Types:** `f32`, `f64` in declarations, parameters, return types
- **Literals:** `3.14`, `2.5` (inferred as f64)
- **Arithmetic:** `+`, `-`, `*`, `/` → `fadd`, `fsub`, `fmul`, `fdiv`
- **Comparisons:** `==`, `!=`, `<`, `>`, `<=`, `>=` → `fcmp` with ordered predicates
- **Function params/returns:** Full f64 ABI support
- **Test:** `test/suite/260_float_basic.lang` (170/170 tests pass)

## Design Goals

1. **Minimal viable floats** - Just `f32` and `f64`, basic operations, no fancy math
2. **LLVM-first** - LLVM backend trivially supports floats; x86 backend can defer
3. **Explicit conversions** - No implicit int↔float coercion (matches Zig philosophy)
4. **IEEE 754 semantics** - Standard float behavior, no fast-math by default

## Implementation Plan

### Phase 1: Type System (lexer + parser)

**Lexer changes** (`src/lexer.lang`):

1. Add token types for f32/f64 keywords:
```lang
var TOKEN_F32 i64 = 86;  // After TOKEN_PUB
var TOKEN_F64 i64 = 87;
```

2. Add float literal token:
```lang
var TOKEN_FLOAT i64 = 88;  // Distinguished from TOKEN_NUMBER
```

3. Extend `scan_number()` to handle decimal points:
```lang
func scan_number() *u8 {
    while is_digit(lex_peek()) {
        lex_advance();
    }

    // Check for decimal point (float literal)
    if lex_peek() == 46 {  // '.'
        if is_digit(lex_peek_next()) {
            lex_advance();  // consume '.'
            while is_digit(lex_peek()) {
                lex_advance();
            }
            return make_token(TOKEN_FLOAT);
        }
    }

    return make_token(TOKEN_NUMBER);
}
```

4. Add keyword recognition in `check_keyword()`:
```lang
if lexeme_eq("f32") { return TOKEN_F32; }
if lexeme_eq("f64") { return TOKEN_F64; }
```

**Parser changes** (`src/parser.lang`):

1. Add f32/f64 to type parsing (in `parse_type()`):
```lang
if tt == TOKEN_F32 || tt == TOKEN_F64 {
    // Create TYPE_BASE node with "f32" or "f64"
    ...
}
```

2. Handle TOKEN_FLOAT in `parse_primary()`:
```lang
if tt == TOKEN_FLOAT {
    // Create NODE_FLOAT_EXPR (new node type)
    // OR: reuse NODE_NUMBER_EXPR with type hint
    ...
}
```

**Decision: Separate float expression node vs reusing number node**

Option A: New `NODE_FLOAT_EXPR` node
- Pro: Explicit, no ambiguity
- Con: More parser changes, AST emit changes

Option B: Reuse `NODE_NUMBER_EXPR`, distinguish by lexeme content
- Pro: Minimal parser changes
- Con: Codegen must check for '.' in lexeme

**Recommendation:** Option B. The lexeme already contains "3.14" vs "314", codegen can distinguish easily.

### Phase 2: LLVM Backend

**Type emission** (`src/codegen_llvm.lang`, line ~116):

Add float type mapping in `llvm_emit_type()`:
```lang
} else if len == 3 && memcmp(name, "f32", 3) {
    llvm_emit_str("float");
} else if len == 3 && memcmp(name, "f64", 3) {
    llvm_emit_str("double");
```

**Float literals**:

LLVM accepts float literals directly:
```llvm
%t1 = fadd float 3.14, 2.71
%t2 = fadd double 3.14159265359, 2.71828182846
```

The lexeme "3.14" can be emitted verbatim for f32/f64 contexts.

**Arithmetic operations** (`src/codegen_llvm.lang`, line ~2009):

Current integer ops:
```lang
if op == 25 {  // TOKEN_PLUS
    llvm_emit_str("add");
} else if op == 26 {  // TOKEN_MINUS
    llvm_emit_str("sub");
```

Need to dispatch based on operand type:
```lang
if is_float_type(expr_type) {
    if op == 25 { llvm_emit_str("fadd"); }
    else if op == 26 { llvm_emit_str("fsub"); }
    else if op == 27 { llvm_emit_str("fmul"); }
    else if op == 28 { llvm_emit_str("fdiv"); }
    // etc.
} else {
    // existing integer logic
}
```

**Float LLVM instructions needed:**

| Operation | f32 | f64 |
|-----------|-----|-----|
| Add | `fadd float` | `fadd double` |
| Sub | `fsub float` | `fsub double` |
| Mul | `fmul float` | `fmul double` |
| Div | `fdiv float` | `fdiv double` |
| Negate | `fneg float` | `fneg double` |
| Compare | `fcmp olt float` | `fcmp olt double` |

**Comparison predicates** for `fcmp`:
- `oeq` - ordered equal (both operands not NaN, and equal)
- `one` - ordered not equal
- `olt` - ordered less than
- `ogt` - ordered greater than
- `ole` - ordered less or equal
- `oge` - ordered greater or equal
- `ord` - ordered (neither operand is NaN)
- `uno` - unordered (either operand is NaN)

For simplicity, use "ordered" variants initially (fail on NaN comparisons).

**Conversions:**

```llvm
; int to float
%f = sitofp i64 %i to float
%d = sitofp i64 %i to double

; float to int (truncation)
%i = fptosi float %f to i64
%i = fptosi double %d to i64

; float widening/narrowing
%d = fpext float %f to double
%f = fptrunc double %d to float
```

### Phase 3: Type Tracking

**The challenge:** Current codegen doesn't track expression types through operations. It just emits i64 everywhere.

**Options:**

1. **Infer from context** - If a binop has a float literal operand, assume float
2. **Propagate types** - Track type through expression evaluation
3. **Require explicit casts** - `f32(42)` syntax

**Recommendation:** Start with option 1 (infer from literals), evolve to option 2 as needed.

Simple heuristic:
```lang
func is_float_expr(expr *u8) i64 {
    var k i64 = node_kind(expr);
    if k == NODE_NUMBER_EXPR {
        var lexeme *u8 = number_expr_value(expr);
        // Check if lexeme contains '.'
        return strchr(lexeme, 46) != nil;
    }
    // For binops, check operands recursively
    if k == NODE_BINOP {
        var left *u8 = binop_left(expr);
        var right *u8 = binop_right(expr);
        return is_float_expr(left) || is_float_expr(right);
    }
    // etc.
}
```

### x86 Backend: NOT IMPLEMENTED

The x86 backend is **frozen** - no new features will be added.

Float support will only be implemented in the LLVM backend. The x86 backend served its purpose (self-hosting proof, educational value) but requires too much effort for each new feature (SSE2 registers, calling conventions, etc.).

See `designs/multi_backend.md` for the full rationale.

### Phase 5: Standard Library

**Float printing** - The tricky part. Options:

1. **Defer to libc** - `printf("%f", val)` via extern
2. **Basic implementation** - Integer + decimal parts separately
3. **Full implementation** - Dragon4 or similar algorithm (complex)

**Recommendation:** Start with libc, add basic impl later.

```lang
extern func printf(fmt *u8, ...) i64;

func print_f64(val f64) void {
    printf("%f\n", val);
}
```

**Math functions** (all defer to libc initially):

```lang
extern func sin(x f64) f64;
extern func cos(x f64) f64;
extern func sqrt(x f64) f64;
extern func pow(x f64, y f64) f64;
extern func floor(x f64) f64;
extern func ceil(x f64) f64;
extern func fabs(x f64) f64;
```

### Phase 6: AST Emit

For readers/AST interchange, floats need representation:

```lisp
; Float literal (reuse number with type annotation)
(number_expr "3.14" (type_base "f64"))

; Or explicit float node
(float_expr "3.14" (type_base "f64"))
```

The AST reader needs to handle this format.

## File Changes Summary

| File | Changes |
|------|---------|
| `src/lexer.lang` | Add TOKEN_F32, TOKEN_F64, TOKEN_FLOAT; extend scan_number() |
| `src/parser.lang` | Handle TOKEN_FLOAT in parse_primary(); add f32/f64 to parse_type() |
| `src/codegen_llvm.lang` | Add float/double type mapping; add fadd/fsub/fmul/fdiv ops |
| `src/codegen.lang` | (Deferred) SSE2 instructions |
| `src/ast_emit.lang` | (Minimal) TYPE_BASE already handles "f32"/"f64" |
| `std/core.lang` | Add print_f64() and math functions via libc |

## Test Cases

### Basic float literals
```lang
func main() i64 {
    var x f64 = 3.14;
    var y f32 = 2.71;
    return 0;
}
```

### Float arithmetic
```lang
func add_f64(a f64, b f64) f64 {
    return a + b;
}

func main() i64 {
    var result f64 = add_f64(1.5, 2.5);
    // result should be 4.0
    return 0;
}
```

### Float comparisons
```lang
func main() i64 {
    var x f64 = 3.14;
    if x > 3.0 {
        return 1;
    }
    return 0;
}
```

### Mixed int/float (with explicit cast)
```lang
func main() i64 {
    var x f64 = 3.5;
    var y i64 = i64(x);  // truncates to 3
    return y;
}
```

## Open Questions

1. **Scientific notation?** `1.5e10` - defer initially, add later
2. **Hex float literals?** `0x1.fp3` - defer, complex to parse
3. **Float suffix syntax?** `3.14f` vs `f32(3.14)` - use type inference from context
4. **Default float type?** When `3.14` appears untyped, assume f64 (like Go, Rust)
5. **NaN/Infinity literals?** Defer, use function calls

## Implementation Order

1. **Lexer** - TOKEN_F32, TOKEN_F64, TOKEN_FLOAT, scan_number() changes
2. **Parser** - parse_type() and parse_primary() for float tokens
3. **Bootstrap** - Run `make bootstrap` to bake in reading support
4. **LLVM type emission** - float/double in llvm_emit_type()
5. **Float literals in codegen** - Emit float constants
6. **Float arithmetic** - fadd/fsub/fmul/fdiv
7. **Float comparisons** - fcmp
8. **Bootstrap again** - Compiler can now use floats
9. **Tests** - Add float test suite
10. **Stdlib** - print_f64, math functions

## Success Criteria

1. `var x f64 = 3.14;` compiles and stores correct IEEE 754 value
2. Float arithmetic produces correct results
3. Float comparisons work
4. Float function args/returns work (System V ABI)
5. 169/169 existing tests still pass (no regressions)

## Future Extensions (not in scope)

- SIMD vector types (`v4f32`, etc.)
- Fast-math mode
- 128-bit floats
- Decimal floats
- Complex numbers
