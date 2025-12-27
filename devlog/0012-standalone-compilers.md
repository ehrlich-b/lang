# Devlog 0012: Standalone Compilers

**Date**: 2024-12-26

## The Vision

Generate truly standalone compilers from reader macros:

```bash
# Generate a lisp compiler
./out/lang -c lisp std/core.lang example/lisp/lisp.lang -o lisp_compiler.s

# Use it (no dependencies!)
./lisp_compiler program.lisp -o program.s
```

The generated compiler is a single binary. No `.lang-cache`, no external reader executables.

## The Key Insight

A reader like `reader lisp(text *u8) *u8 { body }` is just a function. We were compiling it to an external executable for `#lisp{}` macro invocation, but the body is valid lang code.

**Solution**: Make readers generate BOTH:
1. External executable (for compile-time macro expansion)
2. Callable function (for standalone compilers to call directly)

Now standalone compilers can call `lisp(content)` directly - no subprocess exec needed.

## Implementation

### codegen.lang
Added `gen_reader_func()` - generates reader body as a callable function:

```lang
func gen_reader_func(reader_node *u8) void {
    // Emit .globl <name>
    // Emit function prologue
    // Add parameter as local variable
    // Generate body (same as reader)
}
```

### main.lang
The `-c <reader>` flag generates:
```lang
include "reader_source.lang"   // Provides reader declaration
func reader_transform(t *u8) *u8 { return lisp(t); }  // Glue
include "src/standalone.lang"  // Compiler infrastructure
```

### standalone.lang
Template that provides:
- Compiler infrastructure (lexer, parser, codegen)
- Main that reads files, calls `reader_transform()`, compiles result

## The Result

```bash
# Remove .lang-cache to prove we don't need it
rm -rf .lang-cache

# Standalone compiler still works!
./lisp_compiler /tmp/test.lisp -o /tmp/test.s
as /tmp/test.s -o /tmp/test.o
ld /tmp/test.o -o /tmp/test
./test  # Exit code 42
```

## What This Enables

**Language distribution**: Ship a single binary. Users don't need the lang toolchain.

**Nested readers**: A standalone compiler can have readers that use OTHER readers, all inlined.

**The forge vision**: `lang -c lisp reader.lang` produces a native lisp compiler. The reader IS the compiler.

## Files Changed

- `src/codegen.lang`: `gen_reader_func()` to emit readers as callable functions
- `src/main.lang`: `-c <reader>` flag, generates glue code
- `src/standalone.lang`: Template for standalone compilers
- `test/standalone_compiler_test.sh`: Test script

## Next Steps

The file extension dispatch is now complete:
- [x] `.lisp` files wrapped in `#lisp{}`
- [x] `-c <reader>` generates standalone compiler
- [x] Readers callable without external exec

Next: `lang_reader.lang` - define lang's syntax as a reader macro.
