# Kernel/Reader Split

## Status: DESIGN COMPLETE

This document describes the architectural problem of kernel/reader entanglement and the solution to cleanly separate them.

## The Problem

The current "kernel" is NOT a bare AST-processing kernel. It includes:
- `src/lexer.lang` - lang tokenizer
- `src/parser.lang` - lang syntax parser

From the Makefile:
```makefile
KERNEL_CORE := std/core.lang src/lexer.lang src/parser.lang src/codegen.lang src/sexpr_reader.lang
```

This means the kernel already knows how to parse `.lang` files. When we compose `kernel + lang_reader`, we get duplicate definitions because both include lexer/parser.

## Why Codegen Needs the Parser (Currently)

Investigation of `src/codegen.lang` and `src/codegen_llvm.lang` reveals:

### 1. Include Statement Handling (codegen.lang:1820-1867, codegen_llvm.lang:5635-5660)

```lang
// When codegen hits an include:
var prog *u8 = parse_program_from_string(buf);  // Uses parser!
```

Codegen reads the included file, **parses it as lang source**, and processes the declarations.

### 2. Reader Macro Expansion (codegen.lang:5237-5279, codegen_llvm.lang:5750-5804)

```lang
// When codegen hits #reader{content}:
var prog *u8 = parse_program_from_string(output);  // Uses parser!
```

Reader output is AST, but codegen uses `parse_program_from_string` to convert it back to internal nodes.

### 3. Reader Compilation (codegen.lang:1118-1257)

When compiling a reader declaration, codegen:
- Generates wrapper source code (lang syntax)
- Forks self and calls `parser_tokenize` + `parse_program` on it

## The Wrong Mental Model

The current design has codegen doing work that belongs in readers:

```
Current: SOURCE → parser → AST → codegen → CODE
                                   ↑
                         (codegen handles includes!)
                         (codegen handles reader macros!)
```

## The Correct Architecture

### What the Kernel Should Be

A bare kernel ONLY reads S-expression AST and generates code:

```
Correct: AST → kernel → CODE
         ↑
         (sexpr_reader parses S-expr input)
         (NO lang parser!)
```

**Kernel files** (AST → x86/LLVM):
- `std/core.lang` - runtime support
- `src/sexpr_reader.lang` - S-expression parser ONLY
- `src/codegen.lang` - AST → x86 (after refactor)
- `src/codegen_llvm.lang` - AST → LLVM IR (after refactor)
- `src/kernel_main.lang` - CLI that only accepts .ast files

**NO lexer.lang, NO parser.lang!**

### What Readers Should Be

Readers transform their syntax to S-expression AST:

**Lang Reader files** (lang source → AST):
- `src/lexer.lang` - tokenizer
- `src/parser.lang` - lang syntax parser
- `src/ast_emit.lang` - AST serialization
- `src/lang_reader.lang` - reader entry point

### Key Insight: Readers Handle Everything

> "A bare kernel can only read AST. If you pass it a code.lang file, it should emit 'I don't know how to parse this type of code, please provide a reader for `lang`'"

- **Includes?** The READER expands them before emitting AST
- **Macros?** The READER expands them before emitting AST
- **Reader macros?** The READER invokes nested readers before emitting AST
- The kernel just sees FINAL, EXPANDED AST

## The Refactoring Required

### 1. Remove Include Handling from Codegen

Currently codegen reads files and parses lang source at codegen time. Instead:
- Readers MUST expand all includes before emitting AST
- The `--emit-expanded-ast` flag in main.lang already does this
- Codegen should error if it sees an include node (or just skip it)

### 2. Change Reader Macro Output Handling

Currently:
```lang
// codegen calls parse_program_from_string(reader_output)
```

The issue is that `parse_program_from_string` parses LANG SOURCE. But readers output AST!

Actually wait - looking more carefully at the code:
```lang
var prog *u8 = parse_ast_from_string(output);  // Line 5278
```

Some paths use `parse_ast_from_string` (sexpr_reader) and some use `parse_program_from_string` (parser). The ones using the wrong function need fixing.

**Key insight:** `parse_ast_from_string` is in `sexpr_reader.lang` which the kernel SHOULD have. `parse_program_from_string` is in `parser.lang` which the kernel should NOT have.

### 3. Remove Reader Compilation from Codegen

Currently codegen compiles reader declarations to external executables:
- Generates wrapper source
- Forks and compiles with parser

This should NOT be in the kernel. Options:
1. Move to a separate "reader compiler" tool
2. Pre-compile readers before invoking kernel
3. Have readers be functions, not external executables (for embedded case)

For composition, readers are already pre-compiled as `.ast` files. The kernel just needs to:
- Include the reader's AST
- Look up embedded reader functions when encountering reader macros

## Audit: What Uses `parse_program_from_string`?

```
src/codegen.lang:
  1831: parse_program_from_string(buf)         # Include handling - NEEDS REMOVAL

src/codegen_llvm.lang:
  5644: parse_program_from_string(buf)         # Include handling - NEEDS REMOVAL
  5761: parse_program_from_string(output)      # Reader macro - WRONG (should use parse_ast_from_string)
  5793: parse_program_from_string(output)      # Reader macro - WRONG
  5872: parse_program_from_string(buf)         # First pass include - NEEDS REMOVAL
```

### What Uses `parse_ast_from_string`?

This function is in `sexpr_reader.lang` and is the RIGHT way to parse reader output:

```
src/codegen.lang:5278:   parse_ast_from_string(output)  # Correct!
src/main.lang:713:       parse_ast_from_string(ast_source)  # --from-ast mode
src/main.lang:746:       parse_ast_from_string(ast_source)  # --embed-self mode
src/main.lang:806:       parse_ast_from_string(self_kernel) # -r mode
src/main.lang:817:       parse_ast_from_string(reader_source) # -r mode
src/kernel_main.lang:166: parse_ast_from_string(kernel_source)
```

## Migration Path

### Phase 1: Audit Codegen Dependencies
- [ ] List all uses of `parse_program_from_string` in codegen*.lang
- [ ] List all uses of `parser_tokenize` in codegen*.lang
- [ ] Categorize: include handling vs reader compilation vs reader output parsing

### Phase 2: Fix Reader Output Parsing
- [ ] Replace `parse_program_from_string` with `parse_ast_from_string` for reader output
- [ ] Readers already emit S-expressions, this should just work

### Phase 3: Remove Include Handling
- [ ] Add error/skip for include nodes in codegen
- [ ] Ensure `--emit-expanded-ast` is used to pre-expand includes
- [ ] Update composition flow to use expanded ASTs

### Phase 4: Remove Reader Compilation
- [ ] Factor out `compile_reader_to_executable` from codegen
- [ ] Create separate reader-compiler tool OR require pre-compiled readers
- [ ] For embedded readers: already handled by function pointer invocation

### Phase 5: Update Makefile
```makefile
# New kernel (no lexer/parser!)
KERNEL_CORE := std/core.lang src/sexpr_reader.lang src/codegen.lang

# Lang reader (has lexer/parser)
LANG_READER_SOURCES := std/core.lang src/lexer.lang src/parser.lang src/ast_emit.lang src/lang_reader.lang
```

### Phase 6: Verify Composition
- Build kernel.ast (no lexer/parser)
- Build lang_reader.ast (has lexer/parser)
- Compose: kernel.ast + lang_reader.ast → no duplicates!

## Testing Criteria

After refactoring:

```bash
# 1. Kernel rejects .lang files
./kernel file.lang -o out.s
# Error: I don't know how to parse .lang files, add a 'lang' reader

# 2. Kernel accepts .ast files
./kernel file.ast -o out.s
# Works!

# 3. Composition produces working compiler
./kernel_self -r lang lang_reader.ast -o lang1.ll
clang lang1.ll -o lang1
./lang1 test.lang -o test.ll  # Works!
```

## Open Questions

1. **What about error messages?** Does codegen reference lang syntax in errors? Probably needs audit.

2. **What about macro expansion?** Currently in parser.lang. Should stay in reader, but verify no codegen dependency.

3. **What about the standalone template?** `src/standalone.lang` is used for `-c` mode. Needs review.

## Related

- `designs/composition_dependencies.md` - The include deduplication problem (separate issue, but becomes easier after this split)
- `designs/fix_composition.md` - Parent issue tracking composition blockers
