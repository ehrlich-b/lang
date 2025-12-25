# 0003: Test Suite

**Date**: 2024-12-25

## What happened

Added a comprehensive test suite with 67 tests covering all language features. Inspired by [nlsandler/writing-a-c-compiler-tests](https://github.com/nlsandler/writing-a-c-compiler-tests) and [chibicc](https://github.com/rui314/chibicc).

## Test categories

| Category | Tests | What's tested |
|----------|-------|---------------|
| Return values | 3 | Basic return statements |
| Arithmetic | 10 | +, -, *, /, %, precedence, parens, negation |
| Comparisons | 6 | ==, !=, <, >, <=, >= |
| Logical ops | 10 | &&, \|\|, !, short-circuit behavior |
| Variables | 5 | Declaration, assignment, expressions |
| Control flow | 11 | if/else, else-if chains, while loops, nesting |
| Functions | 7 | Args, recursion, fibonacci, call chains |
| Pointers | 7 | &, *, assign through pointer, swap pattern |
| Expressions | 3 | Assignment as expression, chaining |
| Edge cases | 5 | Zero, negatives, associativity |

**Total: 67 tests, all passing.**

## How to run

```bash
make test-suite
```

## Why this matters

Before writing a compiler in an unproven language, we need confidence that language works correctly. These tests caught zero bugs (which is either very good or means I'm not testing hard enough).

Next step: start the self-hosting compiler. The test suite will help catch regressions as we build.

## Mood

Feeling solid. Having a real test suite is a psychological safety net.
