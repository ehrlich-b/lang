# language

"There are many like it but this one is mine."

A self-bootstrapping language with extreme metaprogramming aspirations. Started as a blog project.

## Anchor Documents

- `README.md` - Project overview
- `CLAUDE.md` - This file (Claude Code guidance)
- `TODO.md` - Current tasks and roadmap
- `LANG.md` - **Language reference** (what actually works NOW, not aspirational)
- `INITIAL_DESIGN.md` - Original syntax design, grammar (EBNF)

## Project Structure

```
language/
├── boot/           # Phase 0 compiler (Go) - temporary, delete after bootstrap
├── src/            # Phase 1+ compiler (language) - the real one
├── std/            # Standard library
├── test/           # Test programs
├── devlog/         # Development log (milestone reflections)
└── out/            # Build artifacts
```

## Build Commands

```bash
# Build compiler from source (uses out/lang to compile src/*.lang)
make build

# Verify fixed point (compiler compiles itself to identical output)
make verify

# Promote verified build to be the active compiler
make promote

# Compile and run a test file
make run FILE=test/hello.lang

# Compile with stdlib
make stdlib-run FILE=test/vec_test.lang

# Bootstrap from scratch (only if out/lang is broken)
make bootstrap
```

**After making compiler changes:** Always run `make verify` to ensure fixed point.

## Development Phases

- [x] Phase 0: Bootstrap compiler in Go → emits x86-64 assembly
- [x] Phase 1: Self-hosting (compiler written in language)
- [x] Phase 1.5: Stdlib additions (malloc, vec, map)
- [~] Phase 1.6: Structs (working, compiler uses them, incremental adoption)
- [ ] Phase 2: Macro system (AST-based)
- [ ] Phase 3: Syntax extensions (reader macros)
- [ ] Phase 4: GC and runtime niceties

## Devlog Instructions

The `devlog/` folder tracks the journey. **Light touch** - only log at milestones:

- When a major feature lands (not every commit)
- Format: `NNNN-short-title.md` (e.g., `0001-hello-world.md`)
- Content: How'd it go? What am I thinking? Is Bryan frustrated yet?
- If you forget, reconstruct from recent commits when you notice

## Code Style

- Hack freely, this is a learning project
- Comments explain "why", not "what"
- If it works, it works
- Memory can leak in the compiler (it's short-lived)

## Development Philosophy

**Incremental modernization, not big-bang refactoring:**

1. When implementing a new language feature, prove it works in one meaningful part of the compiler (e.g., convert Token to a real struct), then move on
2. Don't exhaustively refactor all 30 uses of a pattern - that's tedious and error-prone
3. As you touch compiler code for new features, "bring it up to code" using all available language features
4. Check `LANG.md` to see what language features are available - use the best ones for the job

This keeps momentum high and ensures the compiler gradually modernizes as it evolves.

## Key Decisions Log

| Decision | Choice | Why |
|----------|--------|-----|
| Phase 0 language | Go | Fast to write, goal is to delete it |
| x86 output | Text assembly (GNU as) | Debuggable, educational |
| Target | x86-64 Linux (System V ABI) | Most common, well-documented |
