# Fix Composition

## The Goal

Build composed compilers: `kernel -r lang reader.ast → lang1`

A language-agnostic kernel that plugins (readers) give syntax abilities to.

## Architecture

### Language-Agnostic Kernel

The kernel ONLY knows AST. It cannot read any source syntax.

```
Fresh kernel:       → only processes .ast files
After -r lang:      → can read .lang files
After -r lang,lisp: → can read .lang AND .lisp files
```

### Self-Contained Distribution

The kernel is a **complete compiler distribution**. It must compile programs
that `require` built-in modules WITHOUT needing external files.

```lang
// User has ONLY the compiler binary and this file:
require "std/core"
func main() i64 { println("Hello"); return 0; }
```

The kernel must provide std/core from internal storage → fat exe's.

## Data Structures

```lang
// Readers embedded via -r (gives syntax abilities)
// Order matters - first reader matching an extension wins
var embedded_reader_names [1024]*u8;  // ["lang", "lisp", ...]
var embedded_reader_funcs [1024]*u8;  // [fn ptr, fn ptr, ...]

// Modules built into kernel (extension-less names + their full AST)
var kernel_builtin_modules [256]*u8;  // ["std/core", "src/lexer", ...]
var kernel_builtin_asts [256]*u8;     // ["(program ...)", "(program ...)", ...]
```

**Critical**: Module names are extension-less (`"std/core"` not `"std/core.lang"`).

## Require Resolution Algorithm

For `require "x/y"`:

```
1. LOOK FOR LOCAL SOURCE (./x/y.{ext})
   For each reader in embedded_reader_names (in order):
     Found → compile with cache → include → DONE

2. CHECK KERNEL BUILT-INS (distribution fallback)
   If "x/y" in kernel_builtin_modules[]:
     -r mode: SKIP (links against kernel)
     normal: include from kernel_builtin_asts[] → DONE

3. ERROR: module "x/y" not found
```

**That's it. Two steps.** No LANG_MODULE_PATH. No separate cache search.

### Caching = Existing Plumbing

Uses the existing `LANG_CACHE` infrastructure with mtime-based invalidation:

```lang
// Already exists in codegen.lang!
func get_cache_base() *u8;           // LANG_CACHE or ".lang-cache"
func should_recompile_reader(...);   // mtime-based invalidation

// New: same pattern for modules
// Cache path: {LANG_CACHE}/modules/x/y.ast (next to /readers/)
func should_recompile_module(source_path *u8, cache_path *u8) i64 {
    var cache_mtime = file_mtime(cache_path);
    if cache_mtime == 0 { return 1; }
    if file_mtime(source_path) > cache_mtime { return 1; }
    if file_mtime("./out/lang") > cache_mtime { return 1; }
    return 0;
}
```

### Why kernel_builtin_asts Is Still Needed

Distribution scenario: user has ONLY the compiler binary, writes:
```lang
require "std/core"
func main() { println("Hi"); }
```

No `./std/core.lang` exists. The AST must come from the kernel.

### -r Mode vs Normal Mode

**-r mode** (composing reader into kernel):
- `require "std/core"` → found in kernel → **SKIP**
- Reader links against kernel's existing functions
- No duplicate symbols

**Normal mode** (building standalone binary):
- `require "std/core"` → found in kernel → **INCLUDE AST**
- Output binary needs all the code to be self-contained

## Implementation Status

### Done
- `require` keyword (TOKEN_REQUIRE, NODE_REQUIRE_DECL)
- `is_ast` flag for embedded readers in sexpr_reader.lang
- embedded_reader_names/funcs arrays and lookup
- -r mode AST combination and poking
- --embed-self mode
- All 169/169 tests pass

### TODO
1. Add `kernel_builtin_modules [256]*u8` (extension-less names)
2. Add `kernel_builtin_asts [256]*u8` (AST strings)
3. Update `--embed-self` to populate both arrays
4. Implement `resolve_require()`:
   - Search local source (./x/y.{ext}) with cache
   - Fallback to kernel_builtin_* arrays
   - Handle -r mode (skip) vs normal mode (include)

### Key Code Locations

**src/codegen.lang** (existing cache infrastructure):
- `get_cache_base()` - LANG_CACHE or ".lang-cache"
- `should_recompile_reader()` - mtime pattern to copy
- `embedded_reader_names/funcs` arrays

**src/main.lang** (new require resolution):
- Add `kernel_builtin_modules` + `kernel_builtin_asts` arrays
- Add `resolve_require()` function
- Update `--embed-self` to populate arrays

## Acceptance Test

```bash
# 1. Build kernel (use --emit-exe-ast for standalone with ___main)
./out/lang --emit-exe-ast std/core.lang src/version_info.lang src/lexer.lang \
    src/parser.lang src/codegen.lang src/codegen_llvm.lang src/ast_emit.lang \
    src/sexpr_reader.lang src/main.lang -o /tmp/full.ast
./out/lang /tmp/full.ast --embed-self -o /tmp/kernel.ll
clang -O2 /tmp/kernel.ll -o /tmp/kernel

# 2. Build reader AST (use --emit-expanded-ast for composition, NO ___main)
./out/lang --emit-expanded-ast src/lang_reader.lang -o /tmp/lang_reader.ast

# 3. Compose kernel + reader
/tmp/kernel -r lang /tmp/lang_reader.ast -o /tmp/lang1.ll
clang -O2 /tmp/lang1.ll -o /tmp/lang1

# 4. Compile standalone program (no external files needed!)
echo 'require "std/core" func main() i64 { println("Hi"); return 0; }' > hello.lang
/tmp/lang1 hello.lang -o hello.ll
clang hello.ll -o hello && ./hello  # Prints "Hi"
```

---

## Current Status (WIP 2025-01-03)

### Completed This Session

1. **Added kernel_builtin_modules/asts arrays** (main.lang:110-111)
   - `kernel_builtin_modules [256]*u8` - extension-less names like "std/core"
   - `kernel_builtin_asts [256]*u8` - full AST strings for each module

2. **Added find_kernel_builtin()** (main.lang:118-134)
   - Looks up module by extension-less name, returns AST string

3. **Updated --embed-self** (main.lang:916-1025)
   - Populates kernel_builtin_modules with extension-less names for std/* modules
   - Populates kernel_builtin_asts by reading/parsing each std/* source file

4. **Updated resolve_require in BOTH backends**:
   - codegen.lang: first pass (lines 1996-2130) and second pass (lines 5515-5594)
   - codegen_llvm.lang: emit pass (lines 5673-5757) and register pass (lines 6000-6085)
   - Algorithm: local file → kernel built-in → error
   - -r mode: skip kernel built-ins (link against kernel)
   - Normal mode: include kernel built-in AST

5. **Fixed lang_reader.lang** to use `require` instead of `include`
   - Changed from: `include "std/core.lang"` etc.
   - Changed to: `require "std/core"` etc.
   - This preserves require statements in AST for -r mode to filter

6. **All 168/168 tests pass** with changes

### Current Blocker: ___main Wrapper in AST

When running the acceptance test:
```bash
/tmp/kernel -r lang /tmp/lang_reader.ast -o /tmp/lang1.ll
clang /tmp/lang1.ll -o /tmp/lang1
# ERROR: redefinition of function '___main'
```

**Root cause**: `--emit-expanded-ast` adds a `___main` wrapper function to make
the output directly compilable as an executable. But for -r mode, we're combining
two ASTs that BOTH have ___main:
1. The kernel AST (from --emit-expanded-ast of the compiler)
2. The reader AST (from --emit-expanded-ast of lang_reader.lang)

The ___main wrapper is added at main.lang:789-793:
```lang
if emit_ast_mode == 0 && is_llvm == 0 {
    append_str(source_buf, &source_len,
        "func ___main(argc i64, argv **u8, envp **u8) i64 { return main(argc, argv); }\n");
}
```

Note: This only checks `emit_ast_mode`, not `emit_expanded_ast_mode`.

---

## NEXT: AST Mode Refactor

### Problem

`--emit-expanded-ast` serves two conflicting purposes:
1. **Composition**: Produce a module AST for -r mode (NO ___main)
2. **Standalone**: Produce a runnable program AST (WITH ___main)

Current behavior adds ___main, breaking composition.

### Solution: Split into Two Modes

**Breaking change to --emit-expanded-ast**: Remove ___main wrapper.
**New --emit-exe-ast mode**: Emit with ___main wrapper for standalone compilation.

| Mode | ___main | Use Case |
|------|---------|----------|
| `--emit-ast` | No | Debug: show AST structure (includes not expanded) |
| `--emit-expanded-ast` | **No** (CHANGE) | Composition: module AST for -r mode |
| `--emit-exe-ast` | Yes | Standalone: directly compilable program |

### Migration Plan

1. **Add --emit-exe-ast flag** (main.lang)
   - New mode: `emit_exe_ast_mode`
   - Behavior: like current --emit-expanded-ast (with ___main)

2. **Update --emit-expanded-ast**
   - Remove ___main wrapper addition
   - Now suitable for composition

3. **Update consumers**:
   - Makefile: If any targets use --emit-expanded-ast for standalone → --emit-exe-ast
   - Bootstrap scripts: Same
   - Tests: Check if any expect ___main in expanded AST

4. **Update acceptance test** (this doc):
   ```bash
   # Kernel: use --emit-exe-ast (needs ___main to run)
   ./out/lang --emit-exe-ast std/core.lang src/... -o /tmp/full.ast

   # Reader: use --emit-expanded-ast (NO ___main, for composition)
   ./out/lang --emit-expanded-ast src/lang_reader.lang -o /tmp/lang_reader.ast
   ```

### Implementation Order

1. Add `emit_exe_ast_mode` flag and `--emit-exe-ast` parsing
2. Move ___main addition to ONLY happen in emit_exe_ast_mode
3. Grep for --emit-expanded-ast consumers, migrate if needed
4. Test acceptance flow
5. Bootstrap

---

## History (Completed Work)

- **Limit overflow** (2025-01-03): LIMIT_TOP_DECLS 1000→4000, LIMIT_FUNCS 1000→3000, etc. - was causing heap corruption
- **Function name mismatch**: -r mode built `reader_lang` but emitted as `@lang` - fixed to use name directly
- **Embedded readers not invoked**: Code always used exec_capture() - fixed to check find_embedded_reader_func() first
- **AST parsing**: parse_program_from_string → parse_ast_from_string for reader output
- **is_ast flag**: Added to sexpr_reader.lang to skip external compilation for embedded readers
- **Small reader composition**: Verified working with #answer{} returning 42
