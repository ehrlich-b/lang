# Exact numeric core, initial profile

Readers choose explicit operations independently of their source language's
promotions, coercions, or overflow policy. The initial profile supports i8/u8,
i16/u16, i32/u32, i64/u64, f32 and f64. Zero, odd, wide integer widths and other
float formats reject. These operations lower through LLVM on native and wasm
targets. Direct Wasm and the historical x86 emitter diagnose this profile as
unsupported at the invocation.

The reserved name `__core_numeric` cannot be redeclared. The core transport is an intrinsic call with three literal string metadata
arguments followed by zero, one, or two expression operands:

```lisp
(call (ident __core_numeric)
      (string "add_checked") (string "i8") (string "i8")
      (ident left) (ident right))
```

The strings are operation, result type, and operand type. `ast_numeric(op,
result_type, operand_type, operands)` builds this form. Lang can spell it
`__core_numeric("add_checked", "i8", "i8", left, right)`. Emit/parse retains the
intrinsic name, metadata, and operand order. It never maps an unsigned predicate
to a signed predicate. The old ambiguous AIR `ult/ugt/ule/uge` binop spellings
reject; use exact comparisons with an unsigned operand type.

Operands evaluate once, left to right. Integer inputs are bitvector carriers;
the explicit operand type selects their low bits and signed interpretation.
Float inputs must have float representation; integer inputs must have integer
representation. This is explicit normalization, not a source-language promotion.
Unknown metadata, operations, operand representations, arity, and declared types
reject with source provenance. A validation walk checks operation metadata and
declared types even in statements after a return. The kernel does not infer C or Zig rules.

| Operations | Contract |
| --- | --- |
| `add_wrap`, `sub_wrap`, `mul_wrap` | Integer arithmetic modulo 2^N; result and operand types match. |
| `add_checked`, `sub_checked`, `mul_checked` | Exact mathematical integer result, or a deterministic trap if out of range. No LLVM poison. |
| `div`, `rem` | Integer division truncates toward zero; remainder has dividend's sign. Signedness comes from the operand type. Zero divisor and signed MIN/-1 trap for both operations. |
| `shl`, `shr` | The count first normalizes to the operand type's low N bits, like every integer operand, then must be in [0,N), otherwise trap. For example, an i8 count of 256 normalizes to zero. Left shift wraps; right shift is arithmetic for signed types, logical for unsigned. |
| `and`, `or`, `xor` | Integer bitwise operations. |
| `add`, `sub`, `mul`, `div`, `rem` | Float arithmetic at the declared f32/f64 precision, without fast-math or contraction. IEEE signed zeros, infinities, and NaNs; NaN payload propagation is unspecified. Remainder uses truncating quotient. Native remainder may require libm. |
| `eq`, `ne`, `lt`, `le`, `gt`, `ge` | Integer signedness or IEEE comparison at the operand precision; i64 result 0/1. `ne` is true for unordered operands; other float predicates are ordered. |
| `convert` | Integer narrowing keeps low bits; widening uses source signedness. Integer/float conversions use source/destination signedness. Float/integer conversion truncates toward zero and traps on NaN, infinity, or an unrepresentable truncated result. |
| `convert_checked` | Also requires integer/integer conversions to retain the mathematical value. Other conversions follow `convert`. |
| `bitcast` | Equal widths only; preserve bits, with no numerical conversion. |
| `trap`, `unreachable` | No operands; both metadata types are `void`. Executing either traps, including at -O2. Unreachable is a checked failure, not an optimizer assumption. |

Float conversions and arithmetic use the default IEEE round-to-nearest,
ties-to-even environment. Alternate rounding modes and floating exception flags
are outside this profile. Float-to-int validation uses truncation before range
comparison, so e.g. -128.9 to i8 and -0.9 to u8 are valid. Native lowering can
require libm for truncation as well as remainder; link `-lm` when used. LLVM's
wasm target implements the truncation directly.

## Explicit legacy boundary

This is an additive core profile, not a change to every existing reader ABI.
Legacy integer expressions, locals, and ordinary internal calls transport i64
values (pointers are addresses); legacy float expressions ordinarily transport
double, while declared f32 loads and parameters use float SSA values. Existing
`binop` and `cast` forms retain their historical behavior. They are not a promise
of exact narrow arithmetic or checked float conversions. New readers should use
the explicit operations rather than relying on those forms for exact semantics.
Legacy binary operations on native f32 values and implicit double initializers
of f32 locals reject with an origin; use explicit numeric operations/conversions.

Exact integer results sign/zero-extend to i64 carriers; f32 results round at f32
then extend exactly to double carriers. NaN carriers preserve the sign and all
23 payload bits, including the signaling/quiet bit, in the high double payload
bits; normalization restores them without a floating conversion. Thus bitcasts
preserve every bit even through f64 carrier locals. Exact float initializers
also normalize to the declared f32/f64 local representation. Pass carrier values
through the explicit operand type on the next operation.
Use explicit `convert` for arithmetic conversion, or `bitcast` to expose bits.
This profile does not change native aggregate or foreign narrow-call ABI rules.
The C reader still owns promotions, and future Zig readers own coercions.

Unknown declarations now reject instead of becoming an i64 slot. The previous
i128 smoke fixture merely returned 42 without reading the i128 local; it now
requires a diagnostic rather than claiming wide representation support. Both
LLVM and wasm suite runners count that negative fixture as a pass, with no new
skips. Existing struct, enum, function, and closure representations remain named
legacy ABI cases, rather than unknown-type fallback paths.

`test/run_numeric.py` checks runtime boundary inputs against Python exact integer
arithmetic and a separately compiled C float oracle. It runs lang and independent
schema-reader fixtures, plus both emitted-core round-trips, at -O0 and -O2.
Validation cases exercise diagnostics; legacy cases execute the existing C,
Forth, Minipy, and Minilisp readers and cast/float/pointer fixtures.
