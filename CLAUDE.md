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
# Phase 0 (Go bootstrap compiler)
cd boot && go build -o lang0 && cd ..

# Compile a .lang file
./boot/lang0 test/hello.lang -o out/hello.s
as out/hello.s -o out/hello.o
ld out/hello.o -o out/hello
```

## Development Phases

- [ ] Phase 0: Bootstrap compiler in Go → emits x86-64 assembly
- [ ] Phase 1: Self-hosting (compiler written in language)
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

## Key Decisions Log

| Decision | Choice | Why |
|----------|--------|-----|
| Phase 0 language | Go | Fast to write, goal is to delete it |
| x86 output | Text assembly (GNU as) | Debuggable, educational |
| Target | x86-64 Linux (System V ABI) | Most common, well-documented |
