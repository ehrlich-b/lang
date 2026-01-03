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
# 1. Build kernel
./out/lang --emit-expanded-ast std/core.lang src/*.lang -o /tmp/full.ast
./out/lang /tmp/full.ast --embed-self -o /tmp/kernel.ll
clang -O2 /tmp/kernel.ll -o /tmp/kernel

# 2. Add lang reader
/tmp/kernel -r lang lang_reader.ast -o /tmp/lang1.ll
clang -O2 /tmp/lang1.ll -o /tmp/lang1

# 3. Compile standalone program (no external files needed!)
echo 'require "std/core" func main() i64 { println("Hi"); return 0; }' > hello.lang
/tmp/lang1 hello.lang -o hello.ll
clang hello.ll -o hello && ./hello  # Prints "Hi"
```

---

## History (Completed Work)

- **Limit overflow** (2025-01-03): LIMIT_TOP_DECLS 1000→4000, LIMIT_FUNCS 1000→3000, etc. - was causing heap corruption
- **Function name mismatch**: -r mode built `reader_lang` but emitted as `@lang` - fixed to use name directly
- **Embedded readers not invoked**: Code always used exec_capture() - fixed to check find_embedded_reader_func() first
- **AST parsing**: parse_program_from_string → parse_ast_from_string for reader output
- **is_ast flag**: Added to sexpr_reader.lang to skip external compilation for embedded readers
- **Small reader composition**: Verified working with #answer{} returning 42
