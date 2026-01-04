# Yoink & Bootstrap: Capturing Languages Through Their Own Compilers

## Progress Checklist

### Phase 1: Reconnaissance ✅ COMPLETE
- [x] Clone Zig source, build debug version
- [x] Capture AIR from zig self-compile (`zig/ZIG_COMPILER_AIR.txt`)
- [x] Analyze instruction frequency (`zig/AIR_INSTRUCTION_FREQ.txt`)
- [x] Document AIR → lang AST mapping
- [x] Identify required lang extensions

### Phase 2: Lang Extensions (Current)
- [ ] **Add `cast` node** to lang AST
  - [ ] Parser: recognize `(cast type expr)`
  - [ ] Codegen: emit sext/zext/trunc based on types
  - [ ] Bootstrap
- [ ] **Add i128/u128 types** to lang
  - [ ] Lexer: recognize `i128`, `u128`
  - [ ] Codegen: emit LLVM `i128`
  - [ ] Bootstrap

### Phase 3: AIR Emitter
- [ ] Create `lang_ast.zig` in zig source tree
- [ ] Emit program structure (funcs, structs)
- [ ] Handle arithmetic: add, sub, mul, div, rem
- [ ] Handle bitwise: and, or, xor, shl, shr
- [ ] Handle compare: eq, neq, lt, lte, gt, gte
- [ ] Handle memory: load, store, alloc
- [ ] Handle control: block, cond_br, loop, ret, call
- [ ] Handle casts: intcast, bitcast, trunc
- [ ] Handle structs: field_val, field_ptr, union_init
- [ ] Skip debug instructions (dbg_*)

### Phase 4: Integration
- [ ] Compile simple Zig program through lang
- [ ] Test with zig compiler-rt functions
- [ ] Compile zig compiler itself to lang AST
- [ ] Verify fixed point (gen1 == gen2)

---

## The Insight

Don't write frontends. **Capture compilers.**

Every mature language has a bootstrapping compiler - a compiler written in itself that compiles itself. This compiler already solves all the hard problems:
- Lexing, parsing
- Type checking, semantic analysis
- Generics/templates (monomorphization)
- Compile-time evaluation
- Platform-specific codegen

The insight: **Patch the backend to emit lang AST instead of native code.**

```
Traditional approach (hard):
  Zig source → [NEW Zig frontend we write] → lang AST → LLVM → binary

Yoink & Bootstrap (elegant):
  Zig source → [Zig's own compiler, patched] → lang AST → LLVM → binary
```

The Zig team spent years building their frontend. We spend weeks patching their backend.

---

## Case Study: Capturing Zig

### Why Zig?

Zig is the credibility move. If lang can capture Zig, it proves the AST is powerful enough for real languages.

Zig is interesting because:
- Self-hosted (stage2 compiler written in Zig)
- Heavy comptime - would be nightmare to reimplement
- Excellent stdlib - practical programs possible
- C ABI compatible - clean interop story
- Relatively small compiler (~200k lines vs GCC's millions)
- **Already has a C backend** - proves backends can be small (~5600 lines)

### Zig's Compiler Architecture

```
Zig source
    ↓
  Tokenizer
    ↓
  Parser → AST (Zig's AST)
    ↓
  Semantic Analysis (Sema)
    ↓
  AIR (Analyzed Intermediate Representation)  ← WE INTERCEPT HERE
    ↓
  [LLVM Backend | Self-hosted Backend]
    ↓
  Binary
```

**AIR** is the goldmine. By the time code reaches AIR:
- All `comptime` blocks → evaluated to concrete values
- All generics → monomorphized to specific types
- All `@typeInfo`/`@Type` → resolved
- All inline loops → unrolled
- All conditional compilation → resolved
- All `defer`/`errdefer` → control flow already inserted
- All optionals/errors → lowered to tagged unions

AIR is **low-level enough** that most constructs map directly to lang AST.

---

## The Rubric: AIR from Zig Self-Compile

We captured AIR output from the Zig compiler compiling itself using a debug build.

### Tooling

```bash
# Debug zig build (required for --verbose-air output)
zig/bin/zig-debug   # Built from zig 0.15.2 source with -Doptimize=Debug

# Captured data
zig/ZIG_COMPILER_AIR.txt      # 20K+ lines of AIR from zig self-compile
zig/AIR_INSTRUCTION_FREQ.txt  # Instruction frequency analysis
zig/AIR_MAPPING.md            # Detailed instruction mapping
```

### Building the Debug Zig

```bash
# Clone and checkout matching version
git clone https://github.com/ziglang/zig.git /tmp/zig-src
cd /tmp/zig-src && git checkout 0.15.2

# Build debug version (release builds strip --verbose-air output)
zig build -Doptimize=Debug

# Save to lang repo
cp -r zig-out/* /path/to/lang/zig/
mv zig/bin/zig zig/bin/zig-debug
```

### Capturing AIR

```bash
# Simple program
zig/bin/zig-debug build-obj test.zig --verbose-air 2>&1

# Zig compiler self-compile (requires zig build, not build-obj)
cd /tmp/zig-src
/path/to/zig-debug build -Doptimize=Debug --verbose-air 2>&1 | head -50000 > AIR.txt
```

---

## AIR Instruction Analysis

### Frequency from Zig Compiler Self-Compile

88 unique instruction types. Top 50 (covering 99%+ of usage):

```
5651 dbg_stmt           Debug: source location (SKIP)
1432 br                 Control: branch to block
 974 load               Memory: load from pointer
 934 store              Memory: store to pointer
 858 dbg_var_val        Debug: variable value (SKIP)
 583 intcast            Type: integer cast ⚠️ NEED CAST NODE
 534 block              Control: block scope
 493 cond_br            Control: conditional branch
 462 dbg_inline_block   Debug: inline function (SKIP)
 458 bitcast            Type: reinterpret bits ⚠️ NEED CAST NODE
 392 sub                Arith: subtract
 351 shr                Bitwise: shift right
 283 bit_and            Bitwise: and
 242 arg                Func: argument
 230 shl                Bitwise: shift left
 230 alloc              Memory: stack alloc
 205 add                Arith: add
 203 ret                Control: return
 195 bit_or             Bitwise: or
 173 dbg_var_ptr        Debug: variable pointer (SKIP)
 171 dbg_arg_inline     Debug: inline arg (SKIP)
 144 call               Control: function call
 138 struct_field_val   Struct: field access
 127 cmp_eq             Compare: equal
 122 cmp_lt             Compare: less than
  89 cmp_neq            Compare: not equal
  81 slice_len          Slice: get length ⚠️ NEED SLICE TYPE
  80 dbg_empty_stmt     Debug: empty (SKIP)
  79 slice_ptr          Slice: get pointer ⚠️ NEED SLICE TYPE
  79 ptr_add            Pointer: add offset
  71 xor                Bitwise: xor
  70 cmp_gt             Compare: greater than
  63 sub_wrap           Arith: wrapping sub
  56 cmp_gte            Compare: >=
  41 slice              Slice: create slice ⚠️ NEED SLICE TYPE
  40 cmp_lte            Compare: <=
  39 clz                Bit: count leading zeros ⚠️ NEED BUILTIN
  37 not                Logic: not
  36 unreach            Control: unreachable
  33 trunc              Type: truncate ⚠️ NEED CAST NODE
  33 add_wrap           Arith: wrapping add
  29 slice_elem_val     Slice: element value
  29 div_trunc          Arith: truncating div
  28 array_elem_val     Array: element value
  25 int_from_float     Type: float→int ✅ (have floats)
  24 switch_br          Control: switch
  23 ret_safe           Control: checked return
  20 mul_wrap           Arith: wrapping mul
```

### Complete Instruction Categories

**All 88 instructions organized:**

| Category | Instructions | Lang Support |
|----------|--------------|--------------|
| **Arithmetic (13)** | add, sub, mul, div_trunc, rem, abs, min, max + wrap/safe variants | ✅ Direct mapping |
| **Bitwise (7)** | bit_and, bit_or, xor, shl, shr, not, trunc | ✅ Direct mapping |
| **Compare (6)** | cmp_eq, cmp_neq, cmp_lt, cmp_lte, cmp_gt, cmp_gte | ✅ Direct mapping |
| **Memory (6)** | load, store, alloc, memset, memcpy + safe variants | ✅ Direct mapping |
| **Control (10)** | block, br, cond_br, loop, repeat, switch_br, ret, unreach, trap, try | ✅ Direct mapping |
| **Pointer (3)** | ptr_add, ptr_elem_ptr, struct_field_ptr* | ✅ Direct mapping |
| **Struct/Union (5)** | struct_field_val, struct_field_ptr, union_init, get/set_union_tag | ✅ Direct mapping |
| **Type Cast (5)** | intcast, bitcast, trunc, float_from_int, int_from_float | ⚠️ Need cast node |
| **Slice (6)** | slice, slice_ptr, slice_len, slice_elem_val, slice_elem_ptr, array_elem_val | ⚠️ Need slice type |
| **Optional (3)** | is_non_null, optional_payload, wrap_optional | ⚠️ Need optional type |
| **Error Union (6)** | try, unwrap_errunion_*, wrap_errunion_*, is_non_err | ⚠️ Need error union |
| **Bit Ops (2)** | clz, ctz | ⚠️ Need builtins |
| **Debug (6)** | dbg_stmt, dbg_var_val, dbg_var_ptr, dbg_inline_block, dbg_arg_inline, dbg_empty_stmt | ✅ Skip |
| **Misc (3)** | call, arg, array_to_slice, bool_or | ✅ Direct mapping |

---

## Type Requirements

### Types Found in Zig Compiler AIR

| Type | Occurrences | Lang Support |
|------|-------------|--------------|
| u32 | 1013 | ✅ |
| void | 861 | ✅ |
| u64 | 703 | ✅ |
| **u128** | 549 | ❌ **NEED** |
| i32 | 522 | ✅ |
| u8 | 454 | ✅ |
| u16 | 446 | ✅ |
| usize | 408 | ✅ (→ i64) |
| i64 | 223 | ✅ |
| **i128** | 204 | ❌ **NEED** |
| f64 | 52 | ✅ |
| **f80** | 46 | ❌ (defer) |
| f32 | 46 | ✅ |
| bool | 33 | ✅ |
| noreturn | 53 | ✅ (→ void) |
| i16 | 3 | ✅ |

### Arbitrary Bit-Width Integers

AIR uses types like `u5`, `u6`, `u80` for shift amounts and extended precision:
```
%25 = shr(%23, <u5, 16>)   // u5 for shift amount
%52 = bitcast(u80, %0)     // u80 for extended float bits
```

**Strategy:** Emit as next power-of-2 size. `u5` → `u8`, `u80` → `u128`.

### Complex Types

**Optional pointers:**
```
?*u128              // Optional pointer
<?*u128, null>      // Null optional constant
```

**Slices:**
```
[]const u8          // Slice type
"hello"[0..5]       // Slice of string literal
```

**Error unions:**
```
error{OutOfMemory}!void           // Error union type
error{Overflow}!usize             // Error union with payload
```

**Function types with calling convention:**
```
<fn (i128, i128) callconv(.c) i128, (function '__divti3')>
<fn (comptime type, anytype) callconv(.@"inline") i32, (function 'clzXi2')>
```

---

## Required Lang Extensions

### Priority 1: Cast Node (Critical)

**Needed for:** intcast (583), bitcast (458), trunc (33) = 1074 uses

```lisp
;; Proposed AST nodes
(cast type expr)        ;; Integer cast (sext/zext/trunc)
(bitcast type expr)     ;; Reinterpret bits
```

**LLVM codegen:**
- `intcast` → `sext` (sign extend), `zext` (zero extend), or `trunc`
- `bitcast` → `bitcast`
- `trunc` → `trunc`

### Priority 2: 128-bit Integers (Critical for compiler-rt)

**Needed for:** i128 (204 uses), u128 (549 uses) in compiler runtime

The Zig compiler's runtime library (`compiler_rt`) heavily uses 128-bit integers for:
- Division: `__divti3`, `__udivti3`
- Multiplication overflow detection
- Float conversion routines

```lisp
;; Type support
(type_base i128)
(type_base u128)
```

**LLVM:** Native `i128` support, straightforward.

### Priority 3: Slice Type (Medium)

**Needed for:** slice_len (81), slice_ptr (79), slice (41), slice_elem_* (40)

**Option A: Emit as struct**
```lisp
(struct __slice_u8 ((field_decl ptr (type_ptr (type_base u8)))
                    (field_decl len (type_base i64))))
(field_access s 0)  ;; ptr
(field_access s 1)  ;; len
```

**Option B: Native slice type**
```lisp
(type_slice (type_base u8))
(slice_ptr s)
(slice_len s)
```

Recommend Option A initially - requires no kernel changes.

### Priority 4: Bit/Memory Operations (Medium)

**Needed for:** clz (39), ctz (17), abs (11), min (1), max (5), memset (8), memcpy (1)

**Two approaches:**

| Approach | Example | Pros | Cons |
|----------|---------|------|------|
| **extern** | `extern func __clzdi2(x i64) i64;` | Simple, uses compiler-rt | Function call overhead |
| **builtin** | Compiler emits `@llvm.ctlz.i64` | Single instruction | Must wire into codegen |

**Recommendation: Use extern initially.**

Zig's compiler-rt already provides these functions. The AIR emitter just emits calls:
```lisp
;; clz(x) becomes:
(call __clzdi2 x)

;; memset(ptr, val, len) becomes:
(call memset ptr val len)
```

No lang changes needed - these are just regular extern function calls. Add builtins later for performance if needed.

### Priority 5: Optional/Error Types (Deferred)

Can initially emit as tagged unions using existing lang sum types:

```lisp
;; Optional as enum
(enum __optional_i64
  ((variant_decl None)
   (variant_decl Some (type_base i64))))

;; Error union as enum
(enum __result_void_OutOfMemory
  ((variant_decl Ok (type_base void))
   (variant_decl Err (type_base i64))))  ;; error code
```

---

## AIR Syntax Reference

### Instruction Format

```
%N = instruction(args...)
```

### Value References

| Syntax | Meaning |
|--------|---------|
| `%0`, `%1` | SSA register reference |
| `<i64, 42>` | Typed constant |
| `<u32, 0>` | Typed constant |
| `<?*u128, null>` | Null optional |
| `@.void_value` | Void constant |
| `@.bool_true` | Boolean true |

### Example AIR

```
# Begin Function AIR: test.factorial:
  %0 = arg(i64, 0)
  %1 = dbg_stmt(2:9)
  %2 = block(void, {
    %3 = cmp_lte(%0, <i64, 1>)
    %7 = cond_br(%3, poi {
      %4 = dbg_stmt(2:17)
      %5 = ret_safe(<i64, 1>)
    }, poi {
      %6 = br(%2, @.void_value)
    })
  })
  %8 = dbg_stmt(3:28)
  %9 = sub_safe(%0, <i64, 1>)
  %10 = call(<fn (i64) i64, (function 'factorial')>, [%9])
  %11 = mul_safe(%0, %10)
  %12 = ret_safe(%11)
# End Function AIR: test.factorial
```

---

## Direct Mapping Table

| AIR Instruction | Lang AST | Notes |
|-----------------|----------|-------|
| `arg(type, n)` | `(param name type)` | Function parameter |
| `add`, `add_wrap`, `add_safe` | `(binop + a b)` | Addition |
| `sub`, `sub_wrap`, `sub_safe` | `(binop - a b)` | Subtraction |
| `mul`, `mul_wrap`, `mul_safe` | `(binop * a b)` | Multiplication |
| `div_trunc`, `div_exact` | `(binop / a b)` | Division |
| `rem` | `(binop % a b)` | Remainder |
| `bit_and` | `(binop & a b)` | Bitwise and |
| `bit_or` | `(binop \| a b)` | Bitwise or |
| `xor` | `(binop ^ a b)` | Bitwise xor |
| `shl` | `(binop << a b)` | Shift left |
| `shr` | `(binop >> a b)` | Shift right |
| `cmp_eq` | `(binop == a b)` | Equal |
| `cmp_neq` | `(binop != a b)` | Not equal |
| `cmp_lt` | `(binop < a b)` | Less than |
| `cmp_lte` | `(binop <= a b)` | Less or equal |
| `cmp_gt` | `(binop > a b)` | Greater than |
| `cmp_gte` | `(binop >= a b)` | Greater or equal |
| `not` | `(unop ! a)` | Logical not |
| `load` | `(unop * ptr)` | Dereference |
| `store`, `store_safe` | `(assign (unop * ptr) val)` | Store to memory |
| `alloc` | `(var name type)` | Stack allocation |
| `ret`, `ret_safe` | `(return val)` | Return value |
| `call` | `(call func args...)` | Function call |
| `block` | `(block ...)` | Code block |
| `cond_br` | `(if cond then else)` | Conditional |
| `loop`, `repeat` | `(while cond body)` | Loop |
| `br` | N/A | Implicit in block structure |
| `switch_br` | `(match expr ...)` | Switch statement |
| `struct_field_val` | `(field_access expr n)` | Field by index |
| `struct_field_ptr` | `(unop & (field_access ...))` | Field pointer |
| `ptr_add` | `(binop + ptr n)` | Pointer arithmetic |
| `unreach`, `trap` | `(call os_exit 1)` | Abort |
| `union_init` | `(variant Type Name val)` | Union initialization |
| `float_from_int` | `(cast f64 expr)` | Int to float |
| `int_from_float` | `(cast i64 expr)` | Float to int |

---

## Implementation Plan

### Phase 1: Core Extensions (Enables Hello World)

1. **Add `cast` node** to lang AST
   - Parser: `(cast type expr)`
   - Codegen: emit `sext`/`zext`/`trunc`/`bitcast` based on types
   - Bootstrap immediately

2. **Add i128/u128 types**
   - Parser: recognize `i128`, `u128`
   - Codegen: LLVM native `i128`
   - Required for compiler-rt

3. **Write AIR→AST emitter** in Zig
   - New file: `src/codegen/lang_ast.zig`
   - Handle top 30 non-debug instructions
   - Emit S-expression text

### Phase 2: Slices and Arrays

1. Emit slices as anonymous structs (no kernel change)
2. Handle `slice_ptr`, `slice_len`, `slice_elem_*`
3. Handle `array_elem_val`, `array_to_slice`

### Phase 3: Optional/Error (If Needed)

1. Emit as sum types using existing `enum`/`match`
2. Handle `optional_payload`, `is_non_null`
3. Handle `try`, `unwrap_errunion_*`

---

## Gap Summary

| Gap | Severity | Impact | Status |
|-----|----------|--------|--------|
| Cast node | **CRITICAL** | 1074 uses | 🔲 TODO |
| i128/u128 | **CRITICAL** | 753 uses, compiler-rt | 🔲 TODO |
| Slice type | MEDIUM | 230 uses | ✅ Use struct |
| clz/ctz/memset | MEDIUM | 56 uses | ✅ Use extern (compiler-rt) |
| f80 | LOW | 46 uses | Defer |
| Optional | LOW | 17 uses | ✅ Use enum |
| Error union | LOW | 27 uses | ✅ Use enum |
| Calling conv | LOW | Decoration only | ✅ Ignore initially |

**Floats: ✅ DONE** - f32/f64 support added, 170/170 tests passing.

---

## The Bootstrap Sequence

```bash
# 1. Build Zig's compiler with our patched backend
cd zig-source
zig build -Dbackend=lang-ast

# 2. Compile Zig's compiler to lang AST
./zig-with-lang-backend build-exe src/main.zig --emit-ast > zig-compiler.ast

# 3. Compile the AST through lang
lang zig-compiler.ast -o zig-gen1

# 4. Use gen1 to compile Zig again
./zig-gen1 build-exe src/main.zig --emit-ast > zig-compiler2.ast

# 5. Verify fixed point
diff zig-compiler.ast zig-compiler2.ast  # Should be identical!

# 6. Zig is captured. zig-gen1 IS the Zig compiler, running on lang kernel.
```

---

## Success Criteria

**Minimum viable capture:**
- [ ] Cast node implemented
- [ ] i128/u128 types added
- [ ] AIR emitter handles core instructions
- [ ] Simple Zig program compiles through lang
- [ ] Zig compiler compiles through lang

**Full capture:**
- [ ] All 88 AIR instructions mapped
- [ ] Zig stdlib works
- [ ] Fixed point bootstrap achieved
- [ ] Performance parity with native Zig

---

## Appendix: Resources

### Local Tooling

```
zig/bin/zig-debug           # Debug build of zig 0.15.2
zig/ZIG_COMPILER_AIR.txt    # AIR from zig self-compile (20K lines)
zig/AIR_INSTRUCTION_FREQ.txt # Instruction frequency
zig/AIR_MAPPING.md          # Detailed mapping notes
```

### Zig Source References

- `src/Air.zig` - AIR instruction definitions
- `src/codegen.zig` - Backend interface
- `src/codegen/c.zig` - C backend (~5600 lines, good reference)
- `src/codegen/llvm.zig` - LLVM backend

### External

- Mitchell Hashimoto's Zig articles: https://mitchellh.com/zig
- Zig compiler internals documentation
