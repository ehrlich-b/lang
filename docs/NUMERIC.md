# Exact integers: N1

N1 is an explicit core AST tranche for integer comparisons and conversions on
LLVM/native and direct Wasm. Readers may emit these forms without applying a
surface language's promotion rules in the kernel. Existing `binop`, `cast`,
function signatures, storage and readers retain legacy/internal ABI v1; this
tranche does not reinterpret them as exact typed arithmetic. In particular,
legacy direct Wasm `cast` is still outside this contract.

## Core forms

```lisp
(int_compare lt (type_base u64) (ident a) (ident b))
(int_convert extend (type_base i8) (type_base u64) (ident a))
(int_convert truncate (type_base u64) (type_base i16) (ident a))
(int_convert reinterpret (type_base i32) (type_base u32) (ident a))
```

Types are exactly `i8/u8/i16/u16/i32/u32/i64/u64`. Comparison operations are
`eq/ne/lt/le/gt/ge`. Both operands are interpreted at the single declared common
width and signedness, then compared as mathematical integers. Results are
canonical 0 or 1. There is no implicit common-type calculation or promotion.
Readers must choose the common type and insert explicit conversions themselves.

An operand carries a 64-bit pattern. To interpret it as a declared source type,
take its residue modulo 2^width; signed types then subtract 2^width if the high
bit is set. Operands may be integer literals, bindings, calls and composed
integer expressions. Floating and pointer operands are rejected. Host-level
signatures remain the existing i64 carrier convention, including the direct
Wasm `lang` import namespace. This specifies expression semantics, not a public
C ABI or a storage layout. Decimal literals can express all 64 bits.

`extend` requires a larger destination width, `truncate` a smaller width, and
`reinterpret` equal widths. Conversion first interprets the source as above,
then takes that mathematical value modulo 2^destination-width and interprets
the destination's signedness. Thus signed widening sign-extends, unsigned
widening zero-extends, narrowing keeps low bits, and equal-width sign changes
retain bits. A signed i8 -1 extended to u64 is 18446744073709551615. Results
are carried as i64 bit patterns, sign-extended or zero-extended from narrow
destination types. No saturation, checked cast, arithmetic, float, i128 or
overflow mode is accepted by these forms. Unsupported names, widths, directions
and non-integer operands fail before any target output is written. The legacy
x86 backend rejects both new nodes.

Node kinds 47 and 48 use six bootstrap slots: kind, operation string, source
type, destination type (nil for comparisons), left operand, right operand (nil
for conversions). This internal node representation is not a wire ABI.
Emission retains operation, both type spellings and explicit `span` ranges;
parse with the same `--ast-source` to retain source identity and coordinates.
`--from-ast --emit-ast` supports canonical interchange without target lowering.
Origins use the existing source registry and span validation.

## Independent acceptance

Build with `make build`. Run `python3 test/run_numeric.py oracle --output DIR`
and `python3 test/run_numeric.py roundtrip --output DIR`, with DIR outside the
checkout. `COMPILER` can select a verified candidate. The Python model uses
arbitrary-precision modulo and mathematical comparisons; it consumes no emitted
IR or backend results when constructing expectations. Fixtures cover every type,
all six predicates, all source/destination conversions, high bits, signed extrema,
out-of-width inputs, deterministic random patterns and composition. Native O0/O2
results are read through ctypes and direct Wasm results through BigInt, retaining
all 64 bits. Rejections must be loud, preserve origin coordinates and leave no
partial target output. Round trips compare complete AST tokens and executable
results on both backends, plus diagnostic origins after re-emission. A second fixture executes the
parser/emitter and inspects type, operation and origin metadata inside native
and direct Wasm programs for all 112 type/operation combinations.

`python3 test/run_numeric_mutations.py --output DIR` builds isolated compiler
copies with an inverted LLVM signedness predicate and a missing direct Wasm
destination normalization. Each must fail the unchanged independent oracle;
compiler/build errors do not count as mutation detection.

## Remaining N obligations; L is blocked

Full N acceptance has not passed. Remaining obligations are exact arithmetic
(add/subtract/multiply/divide/remainder, including divide-by-zero and min/-1),
bitwise and shift semantics (including out-of-range shifts), signed/unsigned
overflow policies and rejection, checked/saturating conversion modes, i128,
floating-point widths/rounding/NaNs/infinities/signed zero, integer/float
conversion boundaries, and integration of exact values with every storage,
parameter, result and foreign ABI boundary. These need independent oracles on
each supported target. Existing float/cast examples do not discharge them.
Layout phase L remains blocked until full N acceptance passes. N1 alone does
not qualify layout, a Lua/native endpoint or C conformance.
