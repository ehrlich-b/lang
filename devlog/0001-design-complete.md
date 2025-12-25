# 0001: Design Complete

**Date**: 2024-12-25

## What happened

Finalized the language design after exploring the space of C-like languages. Looked at:
- Jai, Odin, C3, Hare, D, V, Go

Key decision: **types after names** (Go-style). This eliminates C's famous parsing ambiguities where you can't tell `foo * bar` is multiplication or pointer declaration without knowing if `foo` is a type.

The language is basically "Go syntax with C simplicity" - no GC, no interfaces, no goroutines.

## Stdlib insight

Realized the Phase 0 Go compiler should compile a stdlib written in `language`. This:
1. Tests the compiler more thoroughly than hello world
2. Gives Phase 1 compiler ready-made file I/O, memory allocation, etc.
3. Only needs 6 syscalls: read, write, open, close, mmap, exit

The stdlib is ~60 lines. A bump allocator that never frees (compiler is short-lived, who cares).

## Current state

- INITIAL_DESIGN.md has the full spec
- EBNF grammar done
- Stdlib sketched out
- Ready to start coding

## Mood

Still excited. Haven't hit a wall yet. The design phase was actually fun - learned a lot about why languages make the choices they do.

## Next

Lexer time.
