# Fixed arrays in the direct WebAssembly backend

The native and browser compilers can emit fixed one-dimensional arrays directly
to WebAssembly. Elements may be integer, boolean, `f32`, `f64`, or pointer values.
The focused acceptance runner uses the same source with LLVM/native at `-O0`
and `-O2`, with the native compiler targeting direct Wasm, and optionally with
the browser compiler targeting direct Wasm:

```sh
python3 test/direct_wasm_arrays.py --browser-compiler web/compiler.wasm
```

The raw commands, compiler fingerprint, diagnostics, timings and generated
artifacts are saved under `out/direct-wasm-arrays/`. A failed run writes a failed
report too; source support is not inferred from a successful compiler build.

```lang
var coupling [3]f64 = [0.3, -1.25];  // final element is zero

func update() f64 {
    var coordinates [2]f64 = [1.0, -2.0];
    var p *f64 = coordinates;
    p[1] = p[1] + coupling[0];
    return coordinates[1];
}
```

Literal initializers convert each element to the declared element type, including
binary32 rounding and integer narrowing. Local elements can be arbitrary scalar
expressions or calls; global elements use the backend's constant subset (numbers,
booleans, nil, strings, grouping and negation; floating constants also permit
floating casts). A missing local initializer or a short literal fills the
remaining storage with zero. Global arrays have distinct mutable storage even
when their initializers are equal. An array expression denotes its first-element
address, including arrays in pointer-accessed struct fields; a typed pointer
binding supports existing pointer arithmetic and pointer parameters.

This slice bounds each array to 1–8192 elements and at most 65536 bytes. Lengths
outside the range, nested/aggregate elements, excessive literal elements,
nonliteral array initializers, whole-array assignment, and noninteger indices
produce located errors. Arrays passed or returned by value remain unsupported;
use an element pointer and an explicit length. The backend does not insert array
index bounds checks. Programs must keep indices inside their declared storage.
The Lang reader rejects decimal, signed, missing or symbolic length syntax and
decimal integers above the signed 64-bit range at the length token. This check
runs before either LLVM or direct-Wasm generation and prevents accidental
normalization or integer wraparound into a different extent.

Mutable globals and strings grow upward below 1 MiB. Addressable local values and
arrays live in aligned frames that grow downward from 1 MiB; host allocations
grow upward from that boundary. Static data is finalized before code emission.
Each frame checks space before subtracting its size and traps before entering
static data or wrapping its stack pointer. The recursive resource probe verifies
the static anchor survives that trap. A trapped instance should be discarded;
unwinding does not restore the frames of callers interrupted by the trap.

The tests also cover older array journeys (`156`, `250`, `251`, `252`), a known
binary32 encoding for decimal `0.3`, pointer elements containing `&local`, calls
inside initializer elements, equal global initializers, short zero-filled tails,
array fields, nested call lifetimes and the maximum accepted extent. Performance
receipts describe these small fixtures, not a large-program benchmark.
