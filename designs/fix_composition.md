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
1. SEARCH SOURCE FILES (relative to cwd)
   For each reader in embedded_reader_names (in order):
     Look for ./x/y.{ext}
     If found → compile with that reader → include in output → DONE

2. SEARCH CACHED AST (in LANG_MODULE_PATH)
   For each dir in LANG_MODULE_PATH:
     Look for {dir}/x/y.ast
     If found → load AST → include in output → DONE

3. CHECK KERNEL BUILT-INS
   If "x/y" in kernel_builtin_modules[]:
     Get AST from kernel_builtin_asts[]
     -r mode: SKIP (no duplicates, links against kernel)
     normal mode: INCLUDE (child binary needs the code)
     → DONE

4. ERROR: module "x/y" not found
```

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
4. Implement source file search (step 1)
5. Implement LANG_MODULE_PATH search (step 2)
6. Implement `resolve_require()` full algorithm
7. Handle -r vs normal mode differently in resolution

### Key Code Locations

**src/main.lang**:
- `kernel_modules` → rename to `kernel_builtin_modules`
- Add `kernel_builtin_asts` parallel array
- `has_kernel_module()` → rewrite as `resolve_require()`

**src/codegen.lang**:
- `embedded_reader_names/funcs` arrays
- `find_reader()` - checks embedded then external

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
