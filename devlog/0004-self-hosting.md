# 0004 - Self-Hosting Complete

The compiler bootstraps itself. Fixed point reached.

## What Happened

Rewrote the entire compiler in the language itself:
- `src/lexer.lang` - 550 lines
- `src/parser.lang` - 1285 lines
- `src/codegen.lang` - 1402 lines
- `src/main.lang` - 118 lines

Total: ~3355 lines of self-hosted code.

## The Bootstrap Chain

```
lang0 (Go) → compiles src/*.lang → lang1 (binary)
lang1      → compiles src/*.lang → lang2.s
lang2      → compiles src/*.lang → lang3.s

lang2.s == lang3.s  ← FIXED POINT
```

Preserved as `stage1-bootstrap.s` - can rebuild from scratch without Go.

## The Bug

Spent hours debugging why lang2 crashed on certain inputs. The symptom: `1 * 24` returned `1` instead of `24`.

Root cause: `find_local()` searched the locals array from index 0 forward, returning the *first* match. When variables were shadowed (e.g., `var op` declared in multiple if-branches), it found the wrong one.

Fix: Search from the end (most recent) backward.

## Pain Points

Writing a compiler without structs is brutal:
```lang
var p **u8 = node + 16;
var name *u8 = *p;
var len_p *i64 = node + 24;
```

This is everywhere. ~100 accessor functions just to read/write fields.

## What's Next

Before adding more features, need stdlib additions (malloc, vectors, maps) to make the code less painful. Then structs.

The Go compiler is now just a historical artifact. We bootstrap from `stage1-bootstrap.s`.

## Mood

This is the moment the project becomes real. The snake eats its tail.
