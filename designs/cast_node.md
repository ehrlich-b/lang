# Cast Node Design

**Status:** Planned
**Blocker for:** Zig Capture (see `designs/zig_ast_compatibility.md`)

## Summary

Add `(cast type expr)` and `(bitcast type expr)` AST nodes for explicit type conversions. Required for Zig AIR capture where intcast/bitcast/trunc account for 1074 instruction uses.

## Motivation

Zig's AIR uses three cast instructions extensively:

| Instruction | Occurrences | Purpose |
|-------------|-------------|---------|
| `intcast` | 583 | Sign/zero extend or truncate integers |
| `bitcast` | 458 | Reinterpret bits as different type |
| `trunc` | 33 | Truncate to smaller integer |

Without cast nodes, we cannot represent Zig programs in lang AST.

## Design Goals

1. **Explicit conversions** - No implicit coercion, all casts visible in AST
2. **LLVM-native** - Map directly to LLVM cast instructions
3. **Type-aware** - Codegen picks correct LLVM instruction based on source/dest types
4. **Minimal** - Just what's needed for Zig capture, not a full cast system

## AST Format

```lisp
;; Integer cast (sign/zero extend or truncate)
(cast (type_base i32) (ident x))

;; Bitcast (reinterpret bits)
(bitcast (type_base u64) (ident ptr))

;; Float conversions (reuse cast node)
(cast (type_base f64) (ident int_val))    ;; int → float
(cast (type_base i64) (ident float_val))  ;; float → int
```

## LLVM Mapping

The `cast` node maps to different LLVM instructions based on types:

| Source | Dest | LLVM Instruction |
|--------|------|------------------|
| i32 | i64 | `sext` (sign extend) |
| u32 | u64 | `zext` (zero extend) |
| i64 | i32 | `trunc` (truncate) |
| i64 | f64 | `sitofp` (signed int to float) |
| u64 | f64 | `uitofp` (unsigned int to float) |
| f64 | i64 | `fptosi` (float to signed int) |
| f64 | u64 | `fptoui` (float to unsigned int) |
| f32 | f64 | `fpext` (float extend) |
| f64 | f32 | `fptrunc` (float truncate) |

The `bitcast` node always emits LLVM `bitcast`:

```llvm
%result = bitcast i64 %val to double
%result = bitcast double %val to i64
%result = bitcast i64* %ptr to i8*
```

## Implementation Plan

### Phase 1: AST Infrastructure

**Add NODE_CAST_EXPR constant** (`src/codegen_llvm.lang`):
```lang
var NODE_CAST_EXPR i64 = 28;     // After existing node kinds
var NODE_BITCAST_EXPR i64 = 29;
```

**Add AST accessors**:
```lang
func cast_expr_alloc() *u8;
func cast_expr_type(n *u8) *u8;      // Target type
func cast_expr_expr(n *u8) *u8;      // Source expression
func cast_expr_set_type(n *u8, t *u8) void;
func cast_expr_set_expr(n *u8, e *u8) void;
```

### Phase 2: S-expression Reader

**Update sexpr_reader.lang** to handle cast nodes:

```lang
// (cast type expr)
if streq(head, "cast") {
    var n *u8 = cast_expr_alloc();
    cast_expr_set_type(n, sexpr_to_type(sexpr_get(node, 1)));
    cast_expr_set_expr(n, sexpr_to_node(sexpr_get(node, 2)));
    return n;
}

// (bitcast type expr)
if streq(head, "bitcast") {
    var n *u8 = bitcast_expr_alloc();
    bitcast_expr_set_type(n, sexpr_to_type(sexpr_get(node, 1)));
    bitcast_expr_set_expr(n, sexpr_to_node(sexpr_get(node, 2)));
    return n;
}
```

### Phase 3: LLVM Codegen

**Add cast emission** in `llvm_emit_expr()`:

```lang
if kind == NODE_CAST_EXPR {
    var target_type *u8 = cast_expr_type(expr);
    var src_expr *u8 = cast_expr_expr(expr);

    // Emit source expression
    var src_reg i64 = llvm_emit_expr(src_expr);
    var src_type *u8 = llvm_expr_type(src_expr);

    // Determine cast instruction
    var cast_op *u8 = llvm_pick_cast_op(src_type, target_type);

    // Emit: %rN = <cast_op> <src_type> %rM to <target_type>
    var dst_reg i64 = llvm_next_reg();
    llvm_emit_str("  %r");
    llvm_emit_int(dst_reg);
    llvm_emit_str(" = ");
    llvm_emit_str(cast_op);
    llvm_emit_str(" ");
    llvm_emit_type(src_type);
    llvm_emit_str(" %r");
    llvm_emit_int(src_reg);
    llvm_emit_str(" to ");
    llvm_emit_type(target_type);
    llvm_emit_str("\n");

    return dst_reg;
}
```

**Cast operation picker**:

```lang
func llvm_pick_cast_op(src *u8, dst *u8) *u8 {
    var src_size i64 = type_size(src);
    var dst_size i64 = type_size(dst);
    var src_float i64 = is_float_type(src);
    var dst_float i64 = is_float_type(dst);
    var src_signed i64 = is_signed_type(src);

    // Float conversions
    if src_float && !dst_float {
        if src_signed { return "fptosi"; }
        return "fptoui";
    }
    if !src_float && dst_float {
        if src_signed { return "sitofp"; }
        return "uitofp";
    }
    if src_float && dst_float {
        if dst_size > src_size { return "fpext"; }
        return "fptrunc";
    }

    // Integer conversions
    if dst_size > src_size {
        if src_signed { return "sext"; }
        return "zext";
    }
    if dst_size < src_size {
        return "trunc";
    }

    // Same size - might still need cast for sign change
    return "bitcast";  // or just copy
}
```

### Phase 4: AST Emit

**Update ast_emit.lang** to emit cast nodes:

```lang
if kind == NODE_CAST_EXPR {
    emit_str("(cast ");
    emit_type(cast_expr_type(node));
    emit_str(" ");
    emit_expr(cast_expr_expr(node));
    emit_str(")");
    return;
}
```

### Phase 5: Bootstrap

Run `make bootstrap` to:
1. Bake cast reading support into bootstrap compiler
2. Verify all tests still pass
3. Compiler can now emit and read cast nodes

## Type System Considerations

### Struct Types

**Not supported for cast.** Structs cannot be cast - they have no meaningful numeric interpretation.

For struct-to-struct conversion, users should:
1. Manually copy fields
2. Use `bitcast` only if structs have identical memory layout (unsafe)

```lisp
;; INVALID - struct cast not allowed
(cast (type_struct Point) (ident other_struct))

;; VALID - bitcast for same-layout structs (unsafe, user responsibility)
(bitcast (type_ptr (type_struct Point)) (ident void_ptr))
```

### Type Aliases

Lang currently has no type alias system (`type Foo = i64`). When/if added:

**For cast:** Resolve alias to underlying type, then cast.
```lang
type Handle = i64;
var h Handle = 42;
var x i32 = cast(i32, h);  // Resolves Handle → i64, then casts i64 → i32
```

**For now:** Not a concern. Zig AIR is fully monomorphized - all types are concrete, no aliases.

### Signed vs Unsigned

Lang currently doesn't distinguish signed/unsigned integers strongly. For cast operations:

- `i8`, `i16`, `i32`, `i64` → signed (use `sext`)
- `u8`, `u16`, `u32`, `u64` → unsigned (use `zext`)

Need helper function:
```lang
func is_signed_type(t *u8) bool {
    var name *u8 = base_type_name(t);
    return *name == 'i';  // i8, i16, i32, i64
}
```

### Type Size

```lang
func type_size(t *u8) i64 {
    var name *u8 = base_type_name(t);
    if streq(name, "i8") || streq(name, "u8") { return 8; }
    if streq(name, "i16") || streq(name, "u16") { return 16; }
    if streq(name, "i32") || streq(name, "u32") { return 32; }
    if streq(name, "i64") || streq(name, "u64") { return 64; }
    if streq(name, "i128") || streq(name, "u128") { return 128; }
    if streq(name, "f32") { return 32; }
    if streq(name, "f64") { return 64; }
    return 64;  // default
}
```

## Test Cases

### 265_cast_basic.lang
```lang
// expect: 136
// Cast: integer widening, truncation, float conversions, bitcast

func main() i64 {
    var result i64 = 0;

    // Integer widening (sext): i32 → i64
    var a i32 = 42;
    var b i64 = cast(i64, a);
    if b == 42 {
        result = result + 10;
    }

    // Integer truncation: i64 → i8 (keeps low byte)
    var c i64 = 258;  // 0x102
    var d i8 = cast(i8, c);
    if d == 2 {
        result = result + 20;
    }

    // Float to int (fptosi): truncates toward zero
    var e f64 = 5.7;
    var f i64 = cast(i64, e);
    if f == 5 {
        result = result + 30;
    }

    // Int to float (sitofp)
    var g i64 = 10;
    var h f64 = cast(f64, g);
    if h > 9.9 {
        if h < 10.1 {
            result = result + 40;
        }
    }

    // Unsigned widening (zext): u8 → u64
    var i u8 = 255;
    var j u64 = cast(u64, i);
    if j == 255 {
        result = result + 5;
    }

    // Bitcast: f64 → u64 (reinterpret IEEE 754 bits)
    var k f64 = 1.0;
    var l u64 = bitcast(u64, k);
    // IEEE 754: 1.0 = 0x3FF0000000000000
    var high u64 = l >> 48;
    if high == 16368 {  // 0x3FF0
        result = result + 31;
    }

    // All pass: 10+20+30+40+5+31 = 136
    return result;
}
```

## File Changes Summary

| File | Changes |
|------|---------|
| `src/codegen_llvm.lang` | Add NODE_CAST_EXPR, NODE_BITCAST_EXPR, cast emission |
| `src/sexpr_reader.lang` | Parse (cast ...) and (bitcast ...) nodes |
| `src/ast_emit.lang` | Emit cast nodes |
| `src/parser.lang` | (Optional) Add cast() syntax for lang source |

## Success Criteria

1. `(cast (type_base i64) (number 42))` parses and emits correct LLVM
2. All integer cast directions work (widen, narrow, sign change)
3. Float↔int conversions work
4. Bitcast works for pointer/int/float reinterpretation
5. 170/170 existing tests still pass
6. Zig AIR intcast/bitcast/trunc can be translated to lang AST

## Future Extensions (not in scope)

- Pointer casts (already work via bitcast)
- Checked casts (overflow detection)
- Safe narrowing (saturating)
- Reinterpret cast for structs
