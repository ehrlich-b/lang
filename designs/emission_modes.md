# Compiler Emission Modes

## Status: Backlog (captured for future work)

## Problem Statement

The compiler doesn't have clean, explicit modes for different output types. We should be able to:

1. **Emit code files compiled to AST (a fragment)**
   - Input: source file(s)
   - Output: AST S-expressions (just the declarations, not wrapped in `(program ...)`)
   - Use case: Library compilation, reader output

2. **Emit code files expanded to AST with expanded includes**
   - Input: source file(s)
   - Output: Fully expanded AST (all includes inlined, macros expanded)
   - Use case: Debugging, understanding what the compiler sees
   - Current: `--emit-expanded-ast` does this

3. **Emit code programs compiled to a full program, as AST**
   - Input: source file(s)
   - Output: Complete `(program ...)` AST with all declarations
   - Use case: Round-trip testing, AST interchange
   - Current: `--emit-ast` does this

4. **Emit self-as-compiler AST**
   - Input: (none - use compiler sources)
   - Output: The compiler itself as AST
   - Use case: Bootstrap verification, compiler introspection

5. **Emit code-compiled or self-as-compiler as OS-native assembly**
   - Input: source file(s) or self
   - Output: Assembly (.s) or LLVM IR (.ll)
   - Use case: Normal compilation, bootstrap
   - Current: Default mode

6. **Emit self-as-compiler as OS-native executable**
   - Input: (none - use compiler sources)
   - Output: Ready-to-run binary
   - Use case: One-step bootstrap, distribution
   - Not currently implemented - requires invoking assembler/linker

## Proposed CLI

```bash
# Fragment AST (no program wrapper)
lang --emit-ast-fragment file.lang -o file.ast

# Expanded AST (includes inlined)
lang --emit-expanded-ast file.lang -o file.ast   # Already exists

# Full program AST
lang --emit-ast file.lang -o file.ast   # Already exists

# Self as AST
lang --emit-self-ast -o compiler.ast

# Normal compilation (assembly/LLVM IR)
lang file.lang -o out.s   # Already exists

# Self as assembly
lang --emit-self -o compiler.s

# Self as executable (NEW)
lang --emit-self-exe -o lang_new
```

## Implementation Notes

### Fragment vs Program AST
- Fragment: Just declarations, can be combined
- Program: Wrapped in `(program ...)`, standalone

### Self-emission
- Compiler knows its own source files (could be baked in or use a manifest)
- `--emit-self` compiles src/main.lang + dependencies
- `--emit-self-exe` goes further to invoke assembler/linker

### Executable emission
Requires:
1. Compile to assembly/LLVM IR
2. Invoke toolchain:
   - x86: `as` then `ld`
   - LLVM: `clang`
3. Use `std/tools.lang` for tool detection

## Relationship to Composition

The composition feature (`-c`) is related:
- Composed compiler = self + embedded readers
- Could be: `lang --emit-self-exe --embed-reader lisp reader.lang -o lang_lisp`

## Priority

Low - current modes work for bootstrap and development. This is polish/UX improvement.

## Related

- `designs/fix_composition.md` - composition uses similar concepts
- `designs/cli_commands.md` - overall CLI design
