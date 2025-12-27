# 0011 - Language Polish

## Summary

With the reader macro system working, we shifted focus to polishing the base language. Several quality-of-life features that kept causing friction in real code.

## Features Added

### Character Literals ('A')
- Tokenizer recognizes `'c'` syntax
- Parser creates literal nodes with character code
- No more magic numbers: `'A'` instead of `65`

### Bitwise Operators (& | ^ << >>)
- All five operators with correct precedence
- Essential for bit manipulation (flags, masks, etc.)
- Parser handles both `|` (bitwise OR) and `||` (logical OR) correctly

### Compound Assignment (+= -= *= /= %=)
- Transforms `x += y` into `x = x + y` at parse time
- Works with any lvalue (variables, pointer dereferences, struct fields)
- Makes accumulator loops much cleaner

### Break / Continue (including labeled)
- Basic `break` and `continue` for while loops
- Labeled loops: `outer: while ... { break outer; }`
- Loop stack tracks active loops with their labels and target labels
- Fixed a subtle bug: pending label was captured AFTER parsing body, so nested loops stole the outer loop's label

### >6 Parameters Bug Fix
- Function calls with 7+ parameters were generating broken assembly
- x86-64 calling convention: first 6 args in registers, rest on stack
- Stack parameters were being read at wrong offsets

## Bootstrap System Overhaul

Discovered that `make promote` wasn't saving checkpoints - all working compilers were only in `out/` as binaries. Emergency backup followed by redesign:

- `bootstrap/` now contains working compiler assembly snapshots
- `current.s` symlink points to latest stable version
- `make bootstrap` creates compiler from assembly (no dependencies!)
- Git history preserves all checkpoints

## Test Suite

102 tests now (up from 100):
- 185_labeled_break
- 186_labeled_continue

## Stats

- Fixed point verified
- All tests pass
- Bootstrap system robust
