# language

*"There are many like it but this one is mine."*

**Vision**: A self-hosted compiler compiler. For fun.

Lang + reader macro = native compiler for any syntax. No runtime, no VM, just x86.

## Anchor Documents

**Always re-read during reanchor:**
- `README.md` - Project overview and vision
- `CLAUDE.md` - This file (Claude Code guidance)
- `TODO.md` - Current tasks and roadmap
- `LANG.md` - Language reference (what works NOW)
- `designs/ast_as_language.md` - **The big vision**: AST as root language, syntax as plugin
- `designs/reader_v2_design.md` - Reader macros V2 design
- `designs/self_defining_syntax.md` - The `lang_reader.lang` vision

## Project Structure

```
language/
├── src/            # Compiler (written in language)
├── std/            # Standard library
├── test/           # Test programs
├── example/        # Example programs (lisp reader, etc.)
├── designs/        # Design documents
├── devlog/         # Development journal
└── out/            # Build artifacts
```

## Build Commands

```bash
make build          # Build compiler from source
make verify         # Verify fixed point
make promote        # Promote verified build
make run FILE=...   # Compile and run
make stdlib-run FILE=...  # With stdlib
make bootstrap      # Bootstrap from assembly (emergency)
```

**After compiler changes:** Always `make verify`.

## Current Focus

**AST as Language**: The big architectural vision. See `designs/ast_as_language.md`.

## Milestones

1. ✓ Self-hosting compiler (x86 fixed point)
2. ✓ Self-hosted compiler compiler (reader infrastructure in lang)
3. ✓ `#parser{}` reader (parser generator as reader macro!)
4. ✓ `#lisp{}` reader with defun (cross-file function interop!)
5. → **1.0: AST as Language** ← current
   - `std/ast.lang` - AST constructors + `ast_emit()`
   - S-expression parser in kernel
   - `lang_reader.lang` - lang syntax as a reader
   - Syntax fixed point (lang bootstrapped on AST kernel)
6. → WASM + LLVM IR backends (same AST, multiple targets)
7. → Language forge (any syntax → any target, trivially)

## Code Style

- Hack freely, this is for fun
- Comments explain "why", not "what"
- Memory can leak in the compiler (short-lived)
- Incremental modernization, not big-bang refactoring

## Error Handling Policy

**Broken windows rule**: If you see any horrible things like core dumps, segfaults, or crashes - don't just say "but it basically works" and try to move on. That error becomes your **top priority** until you can prove it was a fluke or fix it properly. Ignoring errors leads to compounding problems.

## Testing Policy

**Save every test**: When you write a test to verify something works, save it to the `test/` folder - never leave tests to die in `/tmp`. Every well-formed test is valuable and should be kept forever. Use descriptive names and add to the test suite when appropriate.

## Key Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Bootstrap | Go (deleted) | Fast to write, goal was to delete it |
| Output | Assembly → native | Direct, educational |
| Reader output | AST S-expressions | Universal format, typed constructors hide details |
| AST format | S-expressions | Trivial to parse, proven, debuggable |
| Future backend | WASM, LLVM IR | Portability, optimization |
