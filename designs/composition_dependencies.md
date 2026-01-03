# Composition Dependencies

## Status: DESIGN COMPLETE

This document describes the dependency duplication problem in composition and the solution using extension-less `require` statements.

## The Problem

When composing multiple ASTs (kernel + reader1 + reader2), shared dependencies get duplicated:

```
kernel.ast (includes std/core.lang, expanded)
+ lang_reader.ast (includes std/core.lang, expanded)
+ lisp_reader.ast (includes std/core.lang, expanded)
= THREE copies of std/core definitions = duplicate symbol errors!
```

### Why Current Model Breaks

The `--emit-expanded-ast` flag fully expands ALL includes recursively:

1. Each emitted AST is **self-contained** (good for standalone compilation)
2. Composition via `-r` **concatenates declarations** (lines 823-853 of main.lang)
3. No deduplication at composition time
4. Result: `clang` errors on redefined symbols

### This is Separate from Kernel/Reader Split

| Issue | Question |
|-------|----------|
| Kernel/Reader Split | What code belongs in kernel vs readers? |
| **This issue** | How do shared includes work across AST boundaries? |

Even with a perfect kernel (no lexer/parser), readers overlap with **each other**.

## The Solution: Extension-less `require`

### Key Insight: Syntax-Agnostic Dependencies

```lang
// Current: includes have file extensions
include "std/core.lang"    // I need this .lang file, parse it NOW

// New: requires are extension-less
require "std/core"         // I need the std/core MODULE, as pre-compiled AST
```

The `require` keyword means:
1. "I need the definitions from `std/core`"
2. "I don't care what syntax it was originally written in"
3. "Find me the pre-compiled AST version"
4. "At composition time, deduplicate against other modules"

### Why Extension-less is Critical

A composed compiler might:
- Require `std/core` (originally from `.lang`)
- But **no longer know how to read `.lang`** (kernel without lang reader)

Extension-less requires separate **what I need** from **who can provide it**:

```
require "std/core"   →  Look for: std/core.ast
                         (Already compiled, syntax doesn't matter)

include "foo.lang"   →  Parse NOW with lang reader
                         (Reader must be available)
```

### The Build Model

```
Source files (various syntaxes):       AST cache (syntax-agnostic):
  std/core.lang                          .lang-cache/std/core.ast
  my_lib.lisp                            .lang-cache/my_lib.ast
  util.json                              .lang-cache/util.ast

Compilation:
  lang std/core.lang --emit-ast -o .lang-cache/std/core.ast
  lisp my_lib.lisp --emit-ast -o .lang-cache/my_lib.ast

Later, any compiler can require these:
  require "std/core"   →  .lang-cache/std/core.ast  (pre-compiled)
```

## Detailed Design

### 1. New Keyword: `require`

```lang
// Syntax
require "module/path"              // Basic form
require "std/core" sha:a1b2c3d4    // With content hash (optional, future)
```

**Semantics**:
- Does NOT inline the module at parse time
- Emits a `(require "module/path")` node in AST
- Resolved at **codegen/composition time**

### 2. New AST Node: `NODE_REQUIRE`

```lang
var NODE_REQUIRE i64 = 45;  // require "module"

struct RequireDecl {
    kind i64;
    module *u8;       // "std/core" (no extension)
    module_len i64;
    hash *u8;         // Optional: "a1b2c3d4" or nil
    hash_len i64;
}
```

AST emission:
```
(require "std/core")
(require "std/core" :sha "a1b2c3d4")  // With hash
```

### 3. Module Resolution

Codegen and composition resolve requires against a **module search path**:

```lang
// Environment variable or flag
LANG_MODULE_PATH=".lang-cache:~/.lang-modules:/usr/local/lang-modules"

// Resolution algorithm
func resolve_module(name *u8) *u8 {
    // Try each path in LANG_MODULE_PATH
    // Look for: path/name.ast
    // Return first match, or error if not found
}
```

### 4. Deduplication at Composition Time

The `-r` mode changes to:

```lang
// Current: just concatenate
combined = base_decls + reader_decls

// New: deduplicate requires first
var seen_modules *u8 = map_new();

// Walk base AST
for each decl in base_decls {
    if decl is require {
        map_set(seen_modules, decl.module, 1);
        resolved = resolve_module(decl.module);
        append resolved.decls to combined;
    } else {
        append decl to combined;
    }
}

// Walk reader AST - skip already-seen modules
for each decl in reader_decls {
    if decl is require {
        if !map_has(seen_modules, decl.module) {
            map_set(seen_modules, decl.module, 1);
            resolved = resolve_module(decl.module);
            append resolved.decls to combined;
        }
        // else: skip duplicate require
    } else {
        append decl to combined;
    }
}
```

### 5. `include` vs `require` Semantics

| Aspect | `include "file.lang"` | `require "module"` |
|--------|----------------------|-------------------|
| Extension | Required (`.lang`, `.lisp`) | None |
| Resolution | Reader parses source NOW | Lookup pre-compiled AST |
| Inlining | Immediate (at parse time) | Deferred (at codegen/compose) |
| Dedup scope | Single compilation unit | Cross-composition |
| Reader needed | Yes (matching extension) | No (AST only) |

### 6. Migration: Reader Pattern

Readers should use `require` for shared dependencies:

```lang
// OLD: lang_reader.lang
include "std/core.lang"      // Expands everything
include "src/lexer.lang"
include "src/parser.lang"

// NEW: lang_reader.lang
require "std/core"           // Reference only, resolved later
include "src/lexer.lang"     // Still include reader-specific code
include "src/parser.lang"
```

**Result**: When composing kernel + lang_reader, `std/core` appears once.

## Content Hashing (Future Enhancement)

For reproducible builds and safety:

```lang
require "std/core" sha:a1b2c3d4
```

This means:
- Find `std/core.ast`
- Compute hash of its contents
- Error if hash doesn't match

### Hash Computation

```lang
func compute_module_hash(ast_content *u8) *u8 {
    // Use existing hash_str from std/core.lang (djb2)
    // Convert to hex string
    var h i64 = hash_str(ast_content);
    return i64_to_hex(h);
}
```

### Use Cases for Hashing

1. **Lock files**: Record exact versions of dependencies
2. **Distributed builds**: Verify cached ASTs match expectations
3. **Security**: Detect tampering with pre-compiled modules

## Implementation Plan

### Phase 1: Add `require` Keyword

1. Add `TOKEN_REQUIRE` to lexer
2. Add `NODE_REQUIRE` and `RequireDecl` to parser
3. Parser emits `(require ...)` node
4. AST emit handles `NODE_REQUIRE`

### Phase 2: Module Resolution

1. Add `LANG_MODULE_PATH` handling
2. Implement `resolve_module()` function
3. Codegen resolves requires to AST files
4. Error on missing module

### Phase 3: Composition Deduplication

1. Modify `-r` mode to collect modules
2. Deduplicate requires across ASTs
3. Inline each module exactly once
4. Test with kernel + multiple readers

### Phase 4: Update Standard Library

1. Change `std/core.lang` to not include itself (root module)
2. Readers use `require "std/core"` instead of `include`
3. Build script generates `.lang-cache/std/core.ast`

### Phase 5: Content Hashing (Optional)

1. Add optional `sha:` syntax
2. Implement hash verification
3. Add `--verify-modules` flag

## Testing Criteria

After implementation:

```bash
# 1. Build std/core as a module
./lang std/core.lang --emit-ast -o .lang-cache/std/core.ast

# 2. Create reader that requires (not includes) std/core
cat > /tmp/test_reader.lang << 'EOF'
require "std/core"
reader answer(text *u8) *u8 {
    return "(number 42)";
}
EOF

# 3. Compile reader to AST
./lang /tmp/test_reader.lang --emit-ast -o /tmp/answer.ast

# 4. Create another reader with same require
cat > /tmp/test_reader2.lang << 'EOF'
require "std/core"
reader hello(text *u8) *u8 {
    return "(string \"hello\")";
}
EOF
./lang /tmp/test_reader2.lang --emit-ast -o /tmp/hello.ast

# 5. Compose: kernel + both readers
# std/core should appear ONCE, not THREE times
./kernel_self -r answer /tmp/answer.ast -r hello /tmp/hello.ast -o /tmp/multi.ll
clang /tmp/multi.ll -o /tmp/multi

# 6. Use both readers in same program
echo 'func main() i64 { return #answer{} + strlen(#hello{}); }' > /tmp/test.lang
/tmp/multi /tmp/test.lang -o /tmp/test.ll
clang /tmp/test.ll -o /tmp/test
./test  # Should work!
```

## Comparison with Alternatives

### Alternative 1: Deduplicate at Composition Time (by name)

Just check if a function/global already exists before adding.

**Pros**: No language change
**Cons**:
- Fragile (what if signatures differ?)
- O(n²) comparison
- Doesn't handle version conflicts

### Alternative 2: Manifest in AST Header

```
(program
  (meta (provides "my_reader") (depends "std/core" "src/lexer"))
  ...)
```

**Pros**: No new keyword
**Cons**:
- Still needs dedup logic
- Doesn't solve syntax-agnostic resolution
- More complex AST format

### Alternative 3: Convention (readers never include stdlib)

Readers assume stdlib is provided by kernel.

**Pros**: Simple, no changes
**Cons**:
- Fragile, easy to break
- Doesn't scale to multiple shared deps
- Can't have standalone reader tests

### Why `require` Wins

1. **Explicit**: Clear distinction between inline and reference
2. **Syntax-agnostic**: Module name, not file path
3. **Scalable**: Works for any shared dependency
4. **Verifiable**: Hash support for reproducibility
5. **Simple**: Easy to implement, easy to understand

## Open Questions

### 1. Module Naming Convention

Should we use paths or package names?

```lang
require "std/core"       // Path-like (chosen)
require "lang.std.core"  // Package-like
```

Path-like maps naturally to filesystem.

### 2. Circular Dependencies

What if A requires B and B requires A?

**Answer**: Detect cycle, error. Circular deps are generally bad.

### 3. Module Versioning

How to handle multiple versions of same module?

**Future work**: Content hashes provide identity. Could have:
```lang
require "std/core" sha:v1_hash  // Old code
require "std/core" sha:v2_hash  // New code
```

Different hashes = different modules (like Go's module versioning).

### 4. AST Cache Location

Where should `.lang-cache/` live?

Options:
- Project-local (`./.lang-cache/`)
- User-global (`~/.lang-modules/`)
- System-wide (`/usr/local/lang-modules/`)

**Recommendation**: Search path like `LANG_MODULE_PATH`, default to project-local.

## Related Documents

- `designs/kernel_reader_split.md` - Kernel should be AST-only
- `designs/fix_composition.md` - Parent tracking doc
- `designs/ast_as_language.md` - Vision for AST as root language
