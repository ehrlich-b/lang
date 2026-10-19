# C reader: legacy/internal ABI v1

`example/c/c.lang` is a C-like subset reader, not a C compiler with a standard platform ABI. Existing reader examples retain this convention until an explicit migration. The same preservation applies to the other example readers; sharing AST nodes does not establish ownership or a foreign ABI.

* `int` and enum values lower to i64, `char` to u8, pointers to the selected backend's internal pointer representation. Standard C `int` is not i64 on either supported native platform.
* `switch` lowers to conditional branches with **no switch fall-through**, even when a case omits `break`. This is intentional legacy subset behavior, not standard C semantics.
* Named structs, pointers, arrays, enums, functions and the tested control/operator slice are supported under that internal convention. Struct field offsets and total size are not one proven external layout model; two narrow fields must not be assumed to match a host C struct.
* Struct value returns can transport a pointer to dead callee storage in the old lowering. The C reader rejects struct-return syntax; the native emitters reject those signatures in core/lang input (including externs and lambdas). Pass an explicit output pointer. Existing enum-return examples are retained internal compatibility fixtures, not an external aggregate ABI promise.
* This grammar does not provide a preprocessor, typedef/declarator completeness, unions, standard promotions/conversions, general varargs/va_list, returns_twice/setjmp, bitfields, atomics or TLS. It cannot compile unmodified Lua. Source accepted by the subset must not be advertised as standard-C-equivalent.

The reader requires a complete translation unit. Unsupported or malformed syntax fails before any AST is emitted, with the first unparsed token's line and byte column (which can be the start of the enclosing declaration). A successfully parsed prefix never counts as a supported file.

The compiler runtime's libc declarations and special cases are implementation dependencies, not a public general-purpose C ABI. A future semantic C frontend must select a new ABI/profile deliberately and verify it against an independent compiler. No C-specific type or switch rules belong in the shared kernel.
