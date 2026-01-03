# Composition Dependencies

## Status: DESIGN COMPLETE (blocked by visibility.md)

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

Module resolution follows a **freshness-first** order: source files are always freshest,
cache is for dependencies without local source, and the compiler itself is a portable
fallback of last resort.

#### Resolution Order for `require "x/y"`

```
Step 1: SOURCE (freshest - you're actively developing)
────────────────────────────────────────────────────────
  For each registered reader (lang, lisp, json, ...):
    Try ./x/y.{ext}  (e.g., ./x/y.lang, ./x/y.lisp)
    If found:
      → Compile source to AST using that reader
      → Write AST to module cache (.lang-cache/x/y.ast)
      → DONE (using fresh source)

Step 2: CACHE (pre-compiled dependencies)
────────────────────────────────────────────────────────
  Try .lang-cache/x/y.ast
  Try LANG_MODULE_PATH/x/y.ast
  If found:
    → Load cached AST
    → DONE (using cached version)

Step 3: SELF (compiler as portable repository)
────────────────────────────────────────────────────────
  Check kernel_modules array (what's embedded in this compiler)
  If "x/y" in kernel_modules:
    → Extract AST from self_kernel string
    → Write AST to module cache (.lang-cache/x/y.ast)
    → DONE (using embedded version, now cached for next time)

Step 4: ERROR
────────────────────────────────────────────────────────
  Cannot resolve module "x/y"
  (No source, no cache, not embedded)
```

#### Why This Order Matters

| Scenario | Resolution | Why |
|----------|------------|-----|
| Active development | Step 1 (source) | You edited std/core.lang, get fresh version |
| Using installed lib | Step 2 (cache) | Pre-compiled, no source available |
| Portable compiler | Step 3 (self) | Composed compiler carries its deps |
| Missing dependency | Step 4 (error) | Clear error message |

#### Cache Population

The module cache is populated automatically:
- **From source**: When Step 1 succeeds, AST is written to cache
- **From self**: When Step 3 succeeds, embedded AST is extracted to cache

This means:
1. First compilation of fresh source → cache miss → compile → cache populated
2. Second compilation → cache hit (but Step 1 still checks source first!)
3. Source modified → Step 1 finds newer source → recompile → cache updated

#### Reader Registration

For Step 1 to work, the compiler needs to know what readers are available:

```lang
// Reader registry (built-in + composed)
var registered_readers [64]*u8 = [];      // ["lang", "lisp", nil, ...]
var registered_extensions [64]*u8 = [];   // [".lang", ".lisp", nil, ...]

// Check each registered reader's extension
func find_source_file(module *u8, module_len i64) *u8 {
    var i i64 = 0;
    while registered_readers[i] != nil {
        var ext *u8 = registered_extensions[i];
        var path *u8 = concat(module, ext);  // "x/y" + ".lang" = "x/y.lang"
        if file_exists(path) {
            return path;
        }
        i = i + 1;
    }
    return nil;  // No source found
}
```

For a fresh compiler, only `lang` is registered. Composed compilers have additional readers.

#### Environment Variables

```bash
# Module cache location (default: .lang-cache/)
LANG_CACHE=".lang-cache"

# Additional search paths for cached modules
LANG_MODULE_PATH="~/.lang-modules:/usr/local/lang-modules"
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
| Extension | Required (`.lang`, `.lisp`) | None (syntax-agnostic) |
| Resolution | Parse source file NOW | Source → Cache → Self (freshness-first) |
| When resolved | Parse time | Codegen time |
| Caching | None | Auto-populates .lang-cache/ |
| Dedup scope | Single compilation unit | Cross-composition |
| Portability | Needs source file | Can use embedded fallback |

**Key difference**: `include` is a parse-time directive that requires the source file to exist.
`require` is a codegen-time reference that tries source first (fresh), then cache, then embedded (portable).

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

### Phase 1: Add `require` Keyword ✅ DONE

1. Add `TOKEN_REQUIRE` to lexer
2. Add `NODE_REQUIRE_DECL` and `RequireDecl` to parser
3. Parser emits `(require ...)` node
4. AST emit handles `NODE_REQUIRE_DECL`
5. sexpr_reader parses `(require ...)` node
6. Bootstrap

### Phase 2: Reader Registration

1. Add `registered_readers [64]*u8` array to codegen
2. Initialize with `["lang", nil, ...]` (reader name = extension name)
3. When composing readers, add their names to the array
4. Bootstrap

### Phase 3: Kernel Module Storage

**Critical**: This must be done BEFORE require resolution can work for child programs.

1. Add to codegen:
   ```lang
   var kernel_modules [256]*u8 = [];       // Module names
   var kernel_module_asts [256]*u8 = [];   // Per-module AST strings
   ```

2. Update `--embed-self` in main.lang:
   - For each source file, emit its AST separately
   - Store module name in `kernel_modules[i]`
   - Store module AST in `kernel_module_asts[i]`
   - Continue storing combined `self_kernel` for `-r` mode

3. Bootstrap (kernel now carries per-module ASTs)

### Phase 4: Module Resolution (Source → Cache → Self)

1. Implement `resolve_require()` with three-step resolution:
   ```
   Step 1: SOURCE
     For reader in registered_readers:
       Try ./module.{reader} (e.g., ./std/core.lang)
       If found: compile with reader → cache → return AST

   Step 2: CACHE
     Try .lang-cache/module.ast
     If found: return AST

   Step 3: SELF
     Check kernel_modules for module name
     If found: return kernel_module_asts[i]

   Step 4: ERROR
   ```

2. Add to both x86 and LLVM backends
3. Bootstrap

### Phase 5: Composition Updates

1. In `-r` mode, when reader has `require`:
   - Check if module in `kernel_modules` → skip (already in base_prog)
   - Otherwise resolve normally
2. When adding reader, update `kernel_modules` and `kernel_module_asts`
3. Bootstrap

### Phase 6: Replace Includes with Requires

1. Replace `include "std/core.lang"` with `require "std/core"` in source files
2. Verify: In repo, Step 1 finds source → works
3. Verify: Copy binary elsewhere, Step 3 uses embedded → works
4. Bootstrap

### Phase 7: Content Hashing (Future)

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

## Integration with Composition Flow

This section describes how `require` integrates with the composition process in `fix_composition.md`.

### The Key Insight: Kernel IS the Dependency Library

When building `kernel_self` from the full compiler:

```bash
./out/lang --emit-expanded-ast std/core.lang src/*.lang -o full_compiler.ast
./out/lang full_compiler.ast --embed-self -o kernel_self.ll
```

The kernel already contains:
- All of `std/core`
- All of `src/lexer`, `src/parser`, `src/codegen`
- Everything!

**The kernel IS the primary dependency library.** Readers that `require "std/core"` will find it already present.

### New Data Structures: `kernel_modules` and `kernel_module_asts`

The compiler needs to carry its dependencies in two forms:
1. **Names**: To check "do I have this module?"
2. **ASTs**: To provide the module to child programs

Add to `codegen.lang`:

```lang
// Module tracking - which modules are baked into this compiler
var kernel_modules [256]*u8 = [];       // ["std/core", "src/lexer", nil, ...]
var kernel_module_asts [256]*u8 = [];   // [AST string, AST string, nil, ...]
```

**Why we need both:**

| Data | Purpose |
|------|---------|
| `kernel_modules` | Fast lookup: "Do I have module X?" |
| `kernel_module_asts` | Provide AST to child programs that `require` the module |

**Critical insight**: The compiler's embedded modules serve TWO different purposes:

```
                    ┌─────────────────────────────────────────────────────┐
                    │  lang1 (compiler with std/core embedded)            │
                    │                                                     │
                    │  kernel_modules = ["std/core", ...]                 │
                    │  kernel_module_asts = ["(program (func alloc...))", │
                    │                        ...]                         │
                    └─────────────────────────────────────────────────────┘
                                          │
              ┌───────────────────────────┴───────────────────────────┐
              │                                                       │
              ▼                                                       ▼
   ┌─────────────────────┐                             ┌─────────────────────┐
   │ Composition (-r)    │                             │ Normal compilation  │
   │                     │                             │                     │
   │ reader requires     │                             │ user.lang requires  │
   │ "std/core"          │                             │ "std/core"          │
   │                     │                             │                     │
   │ → Check kernel_     │                             │ → Check kernel_     │
   │   modules           │                             │   modules           │
   │ → SKIP (already in  │                             │ → INJECT AST from   │
   │   base_prog)        │                             │   kernel_module_asts│
   │                     │                             │   into child program│
   └─────────────────────┘                             └─────────────────────┘
```

**Composition**: Skip duplicates (module already in kernel's declarations)
**Normal compilation**: Provide AST to child (child needs its own copy)

### Why `self_kernel` Isn't Enough

The existing `self_kernel` string contains a flattened `(program ...)` with all declarations mixed:

```
self_kernel = "(program
  (func alloc ...)      ; from std/core
  (func print ...)      ; from std/core
  (func tok_type ...)   ; from src/lexer
  (func parse ...)      ; from src/parser
  (func main ...)       ; from src/main
  ...)"
```

We can't extract "just std/core" from this. The module boundaries are lost.

`kernel_module_asts` preserves module boundaries:

```
kernel_modules[0] = "std/core"
kernel_module_asts[0] = "(program (func alloc ...) (func print ...) ...)"

kernel_modules[1] = "src/lexer"
kernel_module_asts[1] = "(program (func tok_type ...) (func tokenize ...) ...)"
```

### Updated `--embed-self` Behavior

When building with `--embed-self`:

```lang
// In main.lang --embed-self handling
var module_count i64 = 0;

for each source_file in input_files {
    // 1. Convert path to module name
    var module_name *u8 = path_to_module(source_file);
    //    "std/core.lang" → "std/core"
    //    "src/lexer.lang" → "src/lexer"

    // 2. Get this module's AST (before flattening with others)
    var module_ast *u8 = emit_module_ast(source_file);

    // 3. Store both
    kernel_modules[module_count] = module_name;
    kernel_module_asts[module_count] = module_ast;
    module_count = module_count + 1;
}
kernel_modules[module_count] = nil;  // Nil-terminate

// Also store combined self_kernel for -r mode compatibility
self_kernel = emit_combined_ast(all_files);
```

### How Step 3 (SELF) Uses These

**During normal compilation** (user.lang requires "std/core"):

```lang
func resolve_from_kernel(module *u8, module_len i64) *u8 {
    var i i64 = 0;
    while kernel_modules[i] != nil {
        if buf_eq_str(module, module_len, kernel_modules[i]) {
            // Found! Return the AST to inject into child program
            return kernel_module_asts[i];
        }
        i = i + 1;
    }
    return nil;  // Not in kernel
}

// In require resolution:
var ast *u8 = resolve_from_kernel(module, module_len);
if ast != nil {
    var prog *u8 = parse_ast_from_string(ast);
    // Add declarations to current compilation
    process_declarations(prog);
    // Optionally write to cache
    write_to_cache(module, ast);
    return;
}
```

**During composition** (`-r` mode):

```lang
// When processing reader's require:
if is_in_kernel_modules(module, module_len) {
    // Skip! The kernel's base_prog already has these declarations
    // (from parsing self_kernel)
    return;
}
// Otherwise resolve normally (source → cache → error)
```

### Updated `-r` Composition Flow

When composing with `-r reader_name reader.ast`:

```
1. Parse self_kernel → base_prog
2. Parse reader.ast → reader_prog
3. For each decl in reader_prog:
   a. If decl is (require "module"):
      - Use standard resolution: Source → Cache → Self
      - Step 1: Try source files (x/y.lang, x/y.lisp, ...)
        → If found: compile, cache, add to combined
      - Step 2: Try cache (.lang-cache/x/y.ast)
        → If found: load, add to combined
      - Step 3: Check kernel_modules
        → If found: already in base_prog, skip (no duplication!)
      - Step 4: Error if not found anywhere
   b. Else: add decl to combined
4. Update kernel_modules to include newly resolved modules
5. Re-serialize combined → new self_kernel
6. Generate code
```

**Key insight**: The kernel check is Step 3 (last fallback), not Step 1. This means:
- If you have local source, you get your local version (development)
- If you have cached AST, you get that (installed dependency)
- Only if neither exists do you use the kernel's embedded version (portability)

### When Kernel Doesn't Have a Module

If a reader requires something the kernel doesn't have:

```bash
# Kernel has: std/core, src/codegen
# Reader requires: std/core, external/json_parser

kernel_self -r json json_reader.ast -o json_compiler.ll
```

Resolution for `require "std/core"`:
1. Step 1: Try `./std/core.lang` → found! → compile, cache, add
   (Even though kernel has it, we use fresh source if available)

Resolution for `require "external/json_parser"`:
1. Step 1: Try `./external/json_parser.lang` → not found
2. Step 2: Try `.lang-cache/external/json_parser.ast` → found! → load, add
3. (If Step 2 failed: Step 3 would check kernel, but it's not there either → error)

### The Module Cache

The module cache (`.lang-cache/`) is **auto-populated** during require resolution:

```
require "std/core"
  → Step 1: Found ./std/core.lang
  → Compile to AST
  → Write to .lang-cache/std/core.ast  ← Cache populated automatically!
  → Done

Next compilation:
require "std/core"
  → Step 1: Found ./std/core.lang (still checked first for freshness)
  → Source unchanged? Use cached AST
  → Source changed? Recompile and update cache
```

**Manual cache population** is only needed for dependencies without local source:

```bash
# For external dependencies you don't have source for:
# Someone gives you pre-compiled .ast files
cp /path/to/external/json_parser.ast .lang-cache/external/json_parser.ast
```

**Kernel extraction**: When Step 3 (self) provides a module, it's also written to cache:

```
require "rare/module"  (no source, not in cache)
  → Step 3: Found in kernel_modules
  → Extract AST from self_kernel
  → Write to .lang-cache/rare/module.ast  ← Now cached for next time
  → Done
```

This means a portable composed compiler can "seed" the cache with its embedded modules.

### Two Composition Scenarios

**Scenario A: Development (source files present)**

```
./std/core.lang exists on disk
./src/lexer.lang exists on disk

kernel_self -r lang lang_reader.ast
  require "std/core"
    → Step 1: ./std/core.lang found → compile fresh → cache → add
  require "src/lexer"
    → Step 1: ./src/lexer.lang found → compile fresh → cache → add

Result: Uses YOUR local source files (fresh, for development)
```

**Scenario B: Distribution (no source, use embedded)**

```
Compiled kernel_self binary shipped to user
User has NO source files (no ./std/ or ./src/ directories)

kernel_self -r lang lang_reader.ast
  require "std/core"
    → Step 1: No source found
    → Step 2: No cache
    → Step 3: kernel has "std/core" → extract → cache → skip (already in kernel)
  require "src/lexer"
    → Step 1: No source found
    → Step 2: No cache
    → Step 3: kernel has "src/lexer" → extract → cache → skip (already in kernel)

Result: Uses EMBEDDED versions (portable, for distribution)
```

**Key insight**: Same binary, different behavior based on environment.
- Developer with source → uses fresh local files
- End user without source → uses portable embedded versions

### Updated Acceptance Criteria

The composition feature is complete when:

```bash
# 1. Build self-aware kernel (tracks its modules)
LANGBE=llvm LANGOS=macos ./out/lang --emit-expanded-ast \
    std/core.lang src/*.lang -o /tmp/full_compiler.ast
LANGBE=llvm LANGOS=macos ./out/lang /tmp/full_compiler.ast \
    --embed-self -o /tmp/kernel_self.ll
clang -O2 /tmp/kernel_self.ll -o /tmp/kernel_self

# 2. Build reader with requires
cat > /tmp/lang_reader.lang << 'EOF'
require "std/core"        // Will resolve: source → cache → kernel
require "src/lexer"
require "src/parser"

reader lang(text *u8) *u8 {
    parser_tokenize(text);
    var prog *u8 = parse_program();
    return ast_emit_program(prog);
}
EOF

./out/lang /tmp/lang_reader.lang --emit-expanded-ast -o /tmp/lang_reader.ast

# 3. Compose (WITH source files present - development mode)
/tmp/kernel_self -r lang /tmp/lang_reader.ast -o /tmp/lang1.ll

# Resolution (source files exist on disk):
# - require "std/core" → Step 1: ./std/core.lang found → compile → cache → add
# - require "src/lexer" → Step 1: ./src/lexer.lang found → compile → cache → add
# - reader lang(...) → NEW, add to combined
# Result: Fresh source used, .lang-cache/ populated

clang -O2 /tmp/lang1.ll -o /tmp/lang1

# 4. Test the composed compiler
/tmp/lang1 test.lang -o test.ll  # Should work!

# 5. Test portability (simulate distribution - no source)
mkdir /tmp/portable_test
cp /tmp/kernel_self /tmp/portable_test/
cd /tmp/portable_test

# No ./std/ or ./src/ directories here!
./kernel_self -r lang /tmp/lang_reader.ast -o lang1.ll

# Resolution (no source files):
# - require "std/core" → Step 1: not found → Step 2: not found → Step 3: kernel has it → skip
# - require "src/lexer" → Step 1: not found → Step 2: not found → Step 3: kernel has it → skip
# Result: Embedded versions used, portable!

clang -O2 lang1.ll -o lang1
./lang1 /tmp/test.lang -o test.ll  # Should also work!
```

## Related Documents

- `designs/kernel_reader_split.md` - Kernel should be AST-only
- `designs/fix_composition.md` - Parent tracking doc
- `designs/ast_as_language.md` - Vision for AST as root language
