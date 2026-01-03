# Kernel/Reader Split

## Status: DESIGN NEEDED

**To future Claude:** This is a brain dump. Read the code, understand the current state, then transform this into a proper design doc with solutions.

## The Problem

The current "kernel" is NOT a bare AST-reading kernel. It includes:
- `src/lexer.lang` - lang tokenizer
- `src/parser.lang` - lang syntax parser

This means the kernel already knows how to parse `.lang` files. The `lang_reader.lang` is just a thin wrapper (~30 lines) that exposes the same parsing through the reader interface.

When we try to compose `kernel + lang_reader`, we get duplicate definitions because both include lexer/parser.

## The Correct Architecture

**Bare Kernel should be:**
- `std/core.lang` - runtime support
- `src/sexpr_reader.lang` - ONLY parser (reads S-expressions)
- `src/codegen.lang` - AST → x86
- `src/codegen_llvm.lang` - AST → LLVM IR
- `src/kernel_main.lang` - CLI that only accepts .ast files
- NO lexer.lang, NO parser.lang!

**Lang Reader should be:**
- `src/lexer.lang` - tokenizer
- `src/parser.lang` - lang syntax parser
- `src/ast_emit.lang` - AST serialization
- `src/lang_reader.lang` - reader entry point

**Key insight:** The kernel is BUILT from AST. At runtime it only READS AST. It never parses `.lang` files.

- Includes? The READER expands them before emitting AST
- Macros? The READER expands them before emitting AST
- The kernel just sees final, expanded AST

If you pass a `.lang` file to a bare kernel, it should error: "I don't know how to parse .lang files, add a reader"

## Questions to Investigate

1. Does `codegen.lang` have hidden dependencies on lexer/parser? Check imports/function calls.

2. What does `src/main.lang` vs `src/kernel_main.lang` look like? Is there already a split attempted?

3. How do macros currently work? Do they require parsing at codegen time or are they fully expanded by the reader?

4. What about error messages? Does codegen reference lang syntax in errors?

5. Look at the bootstrap process - does it already have a concept of kernel vs full compiler?

## Files to Read

- `src/main.lang` - current CLI, see what it includes
- `src/kernel_main.lang` - might be the kernel entrypoint already
- `src/codegen.lang` - check for lexer/parser dependencies
- `src/lang_reader.lang` - the thin wrapper
- `Makefile` - bootstrap process, what files go where

## The Fix (high level)

1. Audit codegen.lang for lexer/parser deps, remove them
2. Create clean kernel file list (no lexer/parser)
3. Create clean lang_reader file list (has lexer/parser)
4. Update build process
5. Composition works because no shared parsing deps

## Related

See also: `designs/composition_dependencies.md` - the include deduplication problem (separate issue)
