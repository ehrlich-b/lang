# Composition Dependencies

## Status: DESIGN NEEDED

**To future Claude:** This is a brain dump. Read the code, understand the current state, then transform this into a proper design doc with solutions.

## The Problem

Even with a perfect kernel/reader split, composition breaks when readers share dependencies.

```
bare_kernel (includes std/core.lang)
+ lisp_reader (includes std/core.lang)
+ json_reader (includes std/core.lang)
= THREE copies of std/core.lang = duplicate definition errors
```

**Current flow:**
1. `--emit-expanded-ast` fully expands ALL includes recursively
2. Each emitted AST is self-contained (good for standalone compilation)
3. Composition via `-r` combines self-contained ASTs
4. Duplicates! clang errors on redefinition

**Why this happens:**
- Normal compilation deduplicates includes at parse time
- AST emission happens AFTER deduplication
- But each AST is emitted independently
- No cross-AST deduplication

## This is SEPARATE from Kernel/Reader Split

| Issue | Question |
|-------|----------|
| Kernel/Reader Split | What code belongs in kernel vs readers? |
| This issue | How do shared includes work across AST boundaries? |

Even if kernel has zero overlap with readers, readers can overlap with EACH OTHER.

## Possible Solutions (brainstorm, not vetted)

### 1. Deduplicate at composition time
`-r` mode checks each definition, skips if already exists.
- Pro: Works with current AST format
- Con: Band-aid, doesn't solve root cause
- Con: What if definitions differ? Silent skip or error?

### 2. `include` vs `requires`
New keyword: `requires "std/core.lang"` declares dependency without expanding.
```lang
requires "std/core.lang"  // Dependency, not expanded
include "my_lexer.lang"   // Expanded into AST
```
- Pro: Explicit, clean model
- Con: Language change, migration needed

### 3. Dependency manifest in AST
AST header lists what's included:
```
(program
  (meta (included "std/core.lang" "src/foo.lang"))
  (func main ...))
```
Composition checks manifest, skips already-included.
- Pro: No language change
- Con: AST format change

### 4. Convention: readers don't include stdlib
Readers assume stdlib exists, never include it.
- Pro: Simple
- Con: Fragile, easy to break

### 5. Content-addressed dedup
Hash each definition. Skip if hash matches existing.
- Pro: Handles identical code regardless of source
- Con: Complex, what about minor differences?

## Questions to Investigate

1. How does normal compilation deduplicate includes? Look at parser.lang or wherever include handling lives.

2. What does the AST look like for an include? Is there an `(include ...)` node or is it fully inlined?

3. Could we emit unexpanded includes and resolve at composition time? What would that require?

4. What's the minimal shared dependency set? Just std/core.lang or more?

5. Look at how other self-hosting compilers handle this (if you have examples).

## Files to Read

- `src/parser.lang` - include handling, deduplication logic
- `src/ast_emit.lang` - how includes are emitted
- `src/main.lang` - the `-r` composition logic
- `src/sexpr_reader.lang` - how AST is read back

## The Real Question

Is `--emit-expanded-ast` the right model for composition?

Maybe we need `--emit-reader-ast` that:
- Only emits the reader's NEW code
- Lists dependencies as references, not expanded content
- Composition resolves dependencies against kernel

## Related

See also: `designs/kernel_reader_split.md` - the kernel/reader entanglement (separate issue, fix first)
