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

**Lisp Reader**: Prove the compiler compiler works by building a real reader.

Blocked on: reader includes (readers can't include helper files yet).

## Milestones

1. ✓ Self-hosting compiler (x86 fixed point)
2. ✓ Self-hosted compiler compiler (reader infrastructure in lang)
3. → **Reader includes** (the blocker) ← current
4. → `#parser{}` reader (parser generator as reader macro!)
5. → Lisp reader using `#parser{}` (beautiful!)
6. → `lang_reader.lang` (lang syntax defined in lang)
7. → Language forge (readers invoking readers, all native)

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
| Reader output | Lang source text | Simple, debuggable, reuses parser |
| Future backend | LLVM IR (text) | Optimization, targets, no libLLVM |
