# Scalar and fixed-array storage

`src/layout.lang` exposes `layout_query(type, profile, out)`: status zero
means that `StorageLayout` contains byte size, alignment and stride (the
spacing between adjacent values of the queried type). Failure clears all three
fields. Statuses distinguish an unsupported profile, unsupported storage type,
relocation storage, negative count, and size overflow. No ambient target or
backend state is read by the API.

The supported storage profiles are `llvm-linux-x86_64` and `llvm-wasm32`.
Scalars are i/u8/16/32/64, f32/f64 and bool. Their byte size, alignment and stride
are respectively 1, 2, 4 or 8. Fixed arrays, including nested arrays, retain
the element alignment and have size/stride equal to count times element stride.
Zero-length arrays are valid storage types: size and stride zero, with the
alignment of their element. Invalid element forms remain invalid inside empty
arrays. There is no dereferenceable element in an empty array.

Counts must be nonnegative. Multiplication is checked before it happens.
The x86-64 object size ceiling is the signed 64-bit offset limit; wasm32's is
the unsigned 32-bit address limit. Counts also obey that ceiling, including
arrays with zero-sized elements. These are representational limits, not a
promise that an allocation fits available stack, memory or a host allocator.
The Lang reader rejects decimal counts that exceed signed 64-bit storage
before they can wrap. Other readers' type nodes pass through the same query.

The LLVM compiler's scalar-array allocation/type emission and literal-store
element widths consume this API.
Its accepted fixtures emit byte-identical LLVM to the prior compiler, including
empty arrays. Legacy arrays of aggregates, pointers and functions, and macOS
cross-target output, keep their existing internal lowering. They do not pass
through shared layout admission. Other legacy size calculators are unchanged;
in particular their historical float/aggregate rules are not this contract.

Calling the shared API for structs, enums, unknown names or void returns an
unsupported-type error. Pointers, function values and closures return the
relocation-storage error. This does not implement constant relocations, general
aggregate layout, aggregate packing, C ABI, argument/return classification or
an ABI migration. Layout work remains incomplete for those forms.

`test/run_storage_layout.py` links the production API to an independent C11
sizeof/_Alignof/array-stride oracle on the actual Linux x86-64 executor at O0
and O2. Separate wasm32 rows check target arithmetic and limits; the LLVM-Wasm
suite independently executes existing programs in Node. Neither test qualifies
native arm64 execution or the direct Wasm emitter's unsupported array lowering.
