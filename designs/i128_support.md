# i128/u128 Support Design

**Status:** Planned
**Blocker for:** Zig Capture (see `designs/zig_ast_compatibility.md`)

## Summary

Add `i128` and `u128` 128-bit integer types to lang. Required for Zig capture because Zig's compiler-rt uses 128-bit integers extensively (753 occurrences in AIR).

## Motivation

From analyzing Zig compiler self-compile AIR:

| Type | Occurrences | Usage |
|------|-------------|-------|
| u128 | 549 | Division routines, overflow detection |
| i128 | 204 | Signed arithmetic, compiler-rt |

The `compiler_rt` library (Zig's runtime support) implements software division, multiplication overflow detection, and other operations that require 128-bit integers. Without i128/u128, we cannot compile Zig's runtime library through lang.

## Design Goals

1. **LLVM-native** - LLVM has native i128 support, trivial to emit
2. **Minimal changes** - Just add type recognition, most codegen works unchanged
3. **No special operations** - Regular arithmetic ops work via LLVM
4. **ABI compatible** - Match Zig/C calling convention for i128

## Implementation Plan

### Phase 1: Lexer

**Add token recognition** (`src/lexer.lang`):

The lexer already handles type keywords. Add i128/u128 to keyword checking:

```lang
// In check_keyword() or equivalent
if lexeme_eq("i128") { return TOKEN_I128; }
if lexeme_eq("u128") { return TOKEN_U128; }
```

**Or simpler:** Since types are parsed as identifiers and checked in the parser/codegen, we may not need new tokens. The string "i128" flows through as an identifier and is recognized as a type name.

### Phase 2: Type System

**Type recognition** (`src/codegen_llvm.lang`):

Update `llvm_emit_type()` to handle i128/u128:

```lang
func llvm_emit_type(t *u8) void {
    // ... existing code ...

    } else if len == 4 && memcmp(name, "i128", 4) == 0 {
        llvm_emit_str("i128");
    } else if len == 4 && memcmp(name, "u128", 4) == 0 {
        llvm_emit_str("i128");  // LLVM uses i128 for both signed/unsigned
    }

    // ... rest of function ...
}
```

**Type size calculation**:

```lang
func type_size_bits(name *u8) i64 {
    // ... existing cases ...
    if streq(name, "i128") || streq(name, "u128") { return 128; }
    // ...
}
```

### Phase 3: Literal Support

128-bit literals are rare in source code but may appear in AST from Zig AIR.

**LLVM literal format:**
```llvm
; 128-bit constant
%x = add i128 340282366920938463463374607431768211455, 1
```

The number can be written as a decimal integer in LLVM IR.

**For now:** Defer full literal support. Zig AIR will produce constants inline; we just need to emit them.

### Phase 4: Operations

All standard operations work automatically because LLVM handles i128 natively:

```llvm
; Arithmetic
%sum = add i128 %a, %b
%diff = sub i128 %a, %b
%prod = mul i128 %a, %b
%quot = sdiv i128 %a, %b   ; signed division
%uquot = udiv i128 %a, %b  ; unsigned division

; Bitwise
%and = and i128 %a, %b
%or = or i128 %a, %b
%xor = xor i128 %a, %b
%shl = shl i128 %a, %b
%shr = ashr i128 %a, %b    ; arithmetic shift right
%ushr = lshr i128 %a, %b   ; logical shift right

; Comparisons
%eq = icmp eq i128 %a, %b
%lt = icmp slt i128 %a, %b  ; signed less than
%ult = icmp ult i128 %a, %b ; unsigned less than
```

**No codegen changes needed** for operations - LLVM handles everything.

### Phase 5: ABI Considerations

**System V AMD64 ABI** (Linux, macOS):
- i128 passed in register pair (RDI:RSI or RSI:RDX)
- i128 returned in RAX:RDX

**LLVM handles this automatically** when you declare functions with i128 parameters/returns.

```llvm
define i128 @add128(i128 %a, i128 %b) {
  %sum = add i128 %a, %b
  ret i128 %sum
}
```

### Phase 6: Bootstrap

Run `make bootstrap` to bake in i128 type recognition.

## File Changes Summary

| File | Changes |
|------|---------|
| `src/codegen_llvm.lang` | Add i128 to `llvm_emit_type()`, update size calculations |
| `src/lexer.lang` | (Maybe) Add TOKEN_I128, TOKEN_U128 |
| `src/parser.lang` | (Minimal) Types already parsed as identifiers |
| `src/sexpr_reader.lang` | (None) type_base already handles any name |

## Test Cases

### 270_i128_basic.lang
```lang
// expect: 111
// i128/u128: declaration, arithmetic, casting, function params

func add128(a i128, b i128) i128 {
    return a + b;
}

func sub128(a i128, b i128) i128 {
    return a - b;
}

func identity128(x i128) i128 {
    return x;
}

func main() i64 {
    var result i64 = 0;

    // Basic declaration
    var a i128 = 42;
    var b u128 = 100;
    if cast(i64, a) == 42 {
        result = result + 10;
    }

    // Addition
    var c i128 = 100;
    var d i128 = 200;
    var e i128 = add128(c, d);
    if cast(i64, e) == 300 {
        result = result + 20;
    }

    // Subtraction
    var f i128 = sub128(d, c);
    if cast(i64, f) == 100 {
        result = result + 30;
    }

    // Cast i64 → i128 → i64 roundtrip
    var g i64 = 12345;
    var h i128 = cast(i128, g);
    var i i64 = cast(i64, h);
    if i == 12345 {
        result = result + 40;
    }

    // Function parameter/return (ABI test)
    var j i128 = 999;
    var k i128 = identity128(j);
    if cast(i64, k) == 999 {
        result = result + 11;
    }

    // All pass: 10+20+30+40+11 = 111
    return result;
}
```

## Zig Compiler-RT Functions

These functions from Zig's compiler-rt use i128 and must work:

```zig
// Division
pub fn __divti3(a: i128, b: i128) i128
pub fn __udivti3(a: u128, b: u128) u128
pub fn __modti3(a: i128, b: i128) i128
pub fn __umodti3(a: u128, b: u128) u128

// Multiplication
pub fn __multi3(a: i128, b: i128) i128

// Shifts
pub fn __ashlti3(a: i128, b: i32) i128
pub fn __ashrti3(a: i128, b: i32) i128
pub fn __lshrti3(a: u128, b: i32) u128
```

When we emit Zig AIR that calls these functions, they must be callable from lang.

## Success Criteria

1. `var x i128 = 0;` compiles without error
2. i128 arithmetic operations emit correct LLVM
3. i128 function parameters and returns work
4. Cast between i64 and i128 works
5. 170/170 existing tests still pass
6. Zig compiler-rt functions can be declared and called

## Limitations (acceptable for now)

1. **No literal parsing** - Can't write `var x i128 = 12345...;` with huge numbers in lang source
2. **No printf support** - Can't easily print i128 values (need custom function)
3. **No overflow checking** - LLVM wraps on overflow

These limitations are fine because:
- Zig AIR emits constants directly, not parsed from source
- Debugging can use smaller types or custom print functions
- Overflow behavior matches Zig's wrapping semantics

## Future Extensions (not in scope)

- Arbitrary-width integers (i256, i512)
- Saturating arithmetic
- Checked arithmetic with overflow detection
- BigInt type for unlimited precision
