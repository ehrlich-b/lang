# Fix Composition (compose command)

## Status: BLOCKED → DESIGNED (2025-01-03)

Composition works for small readers. Full composition is **blocked on architecture issues** but now has complete designs.

### Blockers (Now Designed)

| Blocker | Design Doc | Status | Solution |
|---------|------------|--------|----------|
| Kernel/Reader Split | `kernel_reader_split.md` | DESIGNED | Remove parser deps from codegen |
| Composition Dependencies | `composition_dependencies.md` | DESIGNED | Extension-less `require` keyword |

### The Integration: How They Fit Together

**The Core Insight**: The kernel IS the dependency library.

When we build `kernel_self` from the full compiler, it already contains everything (std/core, lexer, parser, codegen). Readers that `require "std/core"` will find it already present.

**New Infrastructure Needed**:

1. **`require` keyword** - Declares dependency without inlining
2. **`kernel_modules` array** - Tracks what modules kernel has
3. **Module resolution** - `LANG_MODULE_PATH` for external modules
4. **Updated `-r` mode** - Skips satisfied requires, loads missing ones

**The Flow**:

```
1. Build kernel (full compiler) with --embed-self
   → kernel_modules = ["std/core", "src/lexer", "src/parser", ...]

2. Build reader with requires (not expanded)
   → reader.ast has: (require "std/core"), (reader lang ...)

3. Compose: kernel_self -r lang reader.ast
   → Check require "std/core" against kernel_modules
   → Found! Skip (no duplication)
   → Add reader's new code only

4. Result: Composed compiler with no duplicates
```

See `composition_dependencies.md` for full details.

### Completed Work

1. ✅ **Function name mismatch**: Fixed - `-r` mode now pokes `lang` (not `reader_lang`)
2. ✅ **Embedded readers not invoked**: Fixed - code now checks for embedded function first
3. ✅ **Limits increased**: LIMIT_TOP_DECLS=4000, LIMIT_FUNCS=3000, etc.
4. ✅ **Bootstrap with new limits**: 169/169 tests pass

### What Works Now

Small reader composition works! See "Testing (Verified)" section below for the `#answer{}` example.

## The Design (How It Works)

### Core Insight: Pure AST Manipulation

Composition is ALL AST manipulation. No lang parsing. No source code. Just:
1. Read AST (S-expressions)
2. Combine AST nodes
3. Poke values into AST nodes
4. Re-serialize AST
5. Generate code from AST

### Data Structures

```lang
// In codegen.lang - these get poked by -r mode
var self_kernel *u8 = "";                    // Full program AST (quine)
var embedded_reader_names [1024]*u8 = [];    // ["lang", "lisp", nil, ...]
var embedded_reader_funcs [1024]*u8 = [];    // [lang, lisp, nil, ...]
// Nil-terminated, no count needed
```

### The Three Phases

```
Phase 1: Build composed compiler
──────────────────────────────────────────────────────────────
  kernel_self -r lang lang_reader.ast -o lang1

  This is BUILD TIME for lang1.
  kernel_self is RUNNING.

Phase 2: Composed compiler compiles user code
──────────────────────────────────────────────────────────────
  lang1 user.lang -o user

  This is lang1's RUNTIME = user code's COMPILE TIME.
  When lang1 hits #lang{...}, it must INVOKE the embedded reader.
  The reader function EXISTS inside lang1's binary.
  lang1 should CALL this function, not spawn a subprocess.

Phase 3: User program runs
──────────────────────────────────────────────────────────────
  ./user

  This is user code's RUNTIME.
```

### What Readers Are

Readers are functions that transform strings to AST:

```lang
reader lang(text *u8) *u8 {
    // Parse text, return S-expression AST string
    return ast_emit_program(parse_program());
}
```

**Signature**: `func name(text *u8) *u8`
- Takes: input text string
- Returns: S-expression AST string (e.g., `"(number 42)"`)

When you declare a reader, TWO things happen:
1. `compile_reader_to_executable()` creates external binary for compile-time use
2. `llvm_emit_reader()` emits the reader AS A FUNCTION `@name` in output binary

The function exists so composed compilers can invoke readers at their runtime.

## The Two Bugs (Fixed)

### Bug 1: Function Name Mismatch ✅

**Location**: `src/main.lang:862-865`

**Was**: `-r` mode built `reader_lang` but function emitted as `@lang`.
**Fix**: Use reader name directly without prefix.

### Bug 2: Embedded Readers Not Invoked ✅

**Locations**: `src/codegen.lang` at lines 1725, 3598, 5227

**Was**: Code always used `exec_capture()` even when embedded reader exists.
**Fix**: Check `find_embedded_reader_func()` first, call via function pointer:

```lang
var embedded_func *u8 = find_embedded_reader_func(name, name_len);
if embedded_func != nil {
    var reader_fn fn(*u8) *u8 = embedded_func;
    output = reader_fn(content);
} else {
    // ... exec_capture fallback ...
}
```

## What's Working

| Component | Status |
|-----------|--------|
| Array infrastructure (`embedded_reader_names/funcs`) | ✅ |
| `-r` mode AST combination | ✅ |
| `-r` mode array poking | ✅ |
| `--embed-self` mode | ✅ |
| `llvm_emit_reader()` emits function | ✅ |
| `find_embedded_reader_func()` lookup | ✅ |
| Embedded reader invocation via fn pointer | ✅ |
| `is_ast` flag to skip external compilation | ✅ |
| 169/169 LLVM tests | ✅ |

## Files Modified

1. **`src/main.lang:862-865`** - Use reader name directly (no prefix)
2. **`src/codegen.lang:1725`** - Embedded reader invocation (x86 first pass)
3. **`src/codegen.lang:3598`** - Embedded reader invocation (x86 gen_expr)
4. **`src/codegen.lang:5227`** - Embedded reader invocation (LLVM backend)

## Testing (Verified)

```bash
# Build and test - all 169 tests pass
make build
LANGOS=macos COMPILER=./out/lang_next ./test/run_llvm_suite.sh  # 169/169

# Create full compiler AST and self-aware kernel
LANGBE=llvm LANGOS=macos ./out/lang_next --emit-expanded-ast \
    std/core.lang src/*.lang -o /tmp/compose_test/full_compiler.ast
LANGBE=llvm LANGOS=macos ./out/lang_next /tmp/compose_test/full_compiler.ast \
    --embed-self -o /tmp/compose_test/kernel_self.ll
clang -O2 /tmp/compose_test/kernel_self.ll -o /tmp/compose_test/kernel_self

# Add tiny reader (tests pass)
LANGBE=llvm LANGOS=macos /tmp/compose_test/kernel_self \
    -r answer tiny_reader.ast -o /tmp/compose_test/composed.ll
clang -O2 /tmp/compose_test/composed.ll -o /tmp/compose_test/composed

# Verify embedded reader is invoked correctly
echo 'func main() i64 { return #answer{ignored}; }' > /tmp/test.lang
/tmp/compose_test/composed /tmp/test.lang -o /tmp/test.ll
clang /tmp/test.ll -o /tmp/test && /tmp/test  # Returns 42!
```

## Root Cause Found (2025-01-03)

The crash was NOT a buffer issue - it was **limit overflow**:
- `LIMIT_TOP_DECLS = 1000` but full_compiler.ast has **1135 declarations**
- `LIMIT_FUNCS = 1000` but combined kernel + lang_reader has ~1849 declarations
- Heap corruption occurs when writing past allocated arrays

**Fix Applied** in `src/limits.lang`:
- `LIMIT_TOP_DECLS`: 1000 → 4000
- `LIMIT_FUNCS`: 1000 → 3000
- `LIMIT_GLOBALS`: 1000 → 2000
- `LIMIT_STRINGS`: 3000 → 6000
- `LIMIT_STRUCTS`: 100 → 200

**MUST RUN `make bootstrap`** to bake new limits into bootstrap compiler.

## Acceptance Criteria

The composition feature is complete when:

```bash
# 1. Build self-aware kernel from compiler
LANGBE=llvm LANGOS=macos ./out/lang --emit-expanded-ast \
    std/core.lang src/*.lang -o /tmp/full_compiler.ast
LANGBE=llvm LANGOS=macos ./out/lang /tmp/full_compiler.ast \
    --embed-self -o /tmp/kernel_self.ll
clang -O2 /tmp/kernel_self.ll -o /tmp/kernel_self

# 2. Add lang reader
LANGBE=llvm LANGOS=macos ./out/lang --emit-expanded-ast \
    src/lang_reader.lang -o /tmp/lang_reader.ast
LANGBE=llvm LANGOS=macos /tmp/kernel_self \
    -r lang /tmp/lang_reader.ast -o /tmp/lang1.ll
clang -O2 /tmp/lang1.ll -o /tmp/lang1

# 3. Add minilisp reader (can be trivial)
# Create simple lisp reader that returns (number 42) for any input
LANGBE=llvm LANGOS=macos /tmp/lang1 \
    -r lisp /tmp/lisp_reader.ast -o /tmp/lang2.ll
clang -O2 /tmp/lang2.ll -o /tmp/lang2

# 4. Compose program using both readers
cat > /tmp/hello.lang << 'EOF'
func get_hello() *u8 { return "hello "; }
func main() i64 {
    print(get_hello());
    print(#lisp{world});  // lisp reader provides "world\n"
    return 0;
}
EOF
/tmp/lang2 /tmp/hello.lang -o /tmp/hello.ll
clang /tmp/hello.ll -o /tmp/hello
/tmp/hello  # Prints "hello world"
```

## Next Steps (Implementation Order)

### Phase 1: Kernel/Reader Split (kernel_reader_split.md) ← IN PROGRESS

1. ✅ Fix reader output parsing: `parse_program_from_string` → `parse_ast_from_string` (2025-01-03)
2. Remove include handling from codegen (readers expand includes) - FUTURE
3. Factor out reader compilation from codegen - FUTURE
4. Update Makefile: kernel without lexer/parser - FUTURE
5. Bootstrap after each step

**Note:** Steps 2-4 are for when we actually split kernel/reader. Step 1 was a bug fix.

### Phase 2: Add `require` keyword (composition_dependencies.md)

1. Add `TOKEN_REQUIRE` to lexer, `NODE_REQUIRE` to parser
2. Add `kernel_modules [256]*u8` tracking to codegen
3. Update `--embed-self` to populate `kernel_modules`
4. Update `-r` mode to resolve requires against `kernel_modules`
5. Add `LANG_MODULE_PATH` for external module resolution

### Phase 3: Test full composition

1. Build kernel_self with module tracking
2. Build lang_reader with requires
3. Compose and verify no duplicates
4. Run acceptance criteria tests
5. Bootstrap

---

## Require Resolution Design (2025-01-03)

### Core Principle: Language-Agnostic Kernel

The kernel only knows AST. It is completely **language-agnostic**. Readers are plugins
that give the kernel the ability to understand source syntaxes.

- Fresh kernel: knows NO syntax, only processes AST
- After `-r lang reader.ast`: kernel can now read `.lang` files
- After `-r lisp reader.ast`: kernel can now read `.lang` AND `.lisp` files

### Key Insight: Self-Contained Distribution

The kernel is a **self-contained compiler distribution**. It must be able to compile
programs that depend on built-in modules WITHOUT needing any external files.

Consider: `require "std/core" func main() { println("Hello"); }`

If the user only has the compiler binary and this source file:
1. No `./std/core.lang` exists (no source files)
2. No `std/core.ast` in LANG_MODULE_PATH (no cache)
3. The kernel must provide std/core from its built-in storage

This means the kernel must store the **AST** for each built-in module, not just
a list of names. The output binary needs that code!

### Data Structures

```lang
// Readers embedded via -r (gives ability to read syntaxes)
// Stored in ORDER they were added - this determines search priority
var embedded_reader_names [1024]*u8;  // ["lang", "lisp", "sql", ...]
var embedded_reader_funcs [1024]*u8;  // [fn ptrs...]

// Modules built into the kernel (extension-less names + their AST)
var kernel_builtin_modules [256]*u8;  // ["std/core", "src/lexer", ...]
var kernel_builtin_asts [256]*u8;     // [ast_string, ast_string, ...]
```

**Critical design constraints**:
- Module names are **extension-less** (e.g., `"std/core"` not `"std/core.lang"`)
- Each module has its AST stored as a string literal
- Future optimization: binary AST format + compression (fat exe's for now)

### Require Resolution Algorithm

For `require "x/y"` (extension-less, always):

```
1. SEARCH FOR SOURCE FILES (relative to cwd)
   For each reader in embedded_reader_names (in -r order):
     - Look for "./x/y.{ext}" (e.g., ./x/y.lang, ./x/y.lisp)
     - If found → compile with that reader → include in output
     - STOP on first match (reader order = priority)

2. SEARCH FOR CACHED AST (in LANG_MODULE_PATH)
   - For each directory in LANG_MODULE_PATH:
     - Look for "x/y.ast"
     - If found → load pre-compiled AST → include in output
     - STOP on first match

3. CHECK KERNEL BUILT-INS
   - If "x/y" is in kernel_builtin_modules[]:
     - Get corresponding AST from kernel_builtin_asts[]
     - IN -r MODE: Skip (already compiled into kernel, no duplicates)
     - IN NORMAL MODE: Include AST in output (child binary needs the code)

4. ERROR: module "x/y" not found
```

### Why Reader Order Matters

If you have both `./std/core.lang` and `./std/core.lisp`, and:
- `-r lang` was added first, then `-r lisp`
- `require "std/core"` will use `std/core.lang`

First embedded reader wins. This is intentional - if you want lisp priority, add it first.

### -r Mode vs Normal Compilation

**-r mode** (composing a reader into kernel):
```
Reader source: require "std/core"
               reader answer(text) { ... }

Resolution:
  - "std/core" found in kernel_builtin_modules
  - SKIP including AST (kernel already has this code compiled)
  - Reader's code links against kernel's existing functions
  - No duplicate symbols
```

**Normal compilation** (building standalone binary):
```
User source: require "std/core"
             func main() { println("Hello"); }

Resolution:
  - "std/core" found in kernel_builtin_modules
  - GET AST from kernel_builtin_asts
  - INCLUDE AST in output (child binary needs println, alloc, etc.)
  - Output binary is self-contained
```

The difference: -r mode adds code TO the kernel (links against existing functions),
normal mode creates a NEW binary (must include all dependencies).

### Example Flow

```bash
# 1. Build kernel (language-agnostic, only knows AST)
./out/lang_next --emit-expanded-ast std/core.lang src/*.lang -o /tmp/full.ast
./out/lang_next /tmp/full.ast --embed-self -o /tmp/kernel.ll
clang -O2 /tmp/kernel.ll -o /tmp/kernel

# kernel now has:
#   embedded_reader_names = []  (no readers yet)
#   kernel_builtin_modules = ["std/core", "src/lexer", ...]
#   kernel_builtin_asts = ["(program (func alloc ...)...)", ...]

# 2. Add lang reader
/tmp/kernel -r lang lang_reader.ast -o /tmp/lang1.ll
clang -O2 /tmp/lang1.ll -o /tmp/lang1

# lang1 now has:
#   embedded_reader_names = ["lang"]
#   kernel_builtin_modules = ["std/core", "src/lexer", ...]
#   kernel_builtin_asts = [...same...]

# 3. Compile standalone program
echo 'require "std/core" func main() i64 { println("Hi"); return 0; }' > hello.lang
/tmp/lang1 hello.lang -o hello.ll
clang hello.ll -o hello
./hello  # Prints "Hi" - works without any external files!

# Resolution for require "std/core":
#   1. Search ./std/core.lang - NOT FOUND
#   2. Search LANG_MODULE_PATH/std/core.ast - NOT FOUND
#   3. Check kernel_builtin_modules - "std/core" FOUND!
#      → Get AST from kernel_builtin_asts
#      → Include in output so hello binary has println
```

### Implementation Status

**Completed**:
1. ✅ `require` keyword - lexer (`TOKEN_REQUIRE`) and parser (`NODE_REQUIRE_DECL`)
2. ✅ `is_ast` flag for embedded readers in `sexpr_reader.lang`

**TODO**:
1. ⬜ Add `kernel_builtin_modules [256]*u8` array (extension-less names)
2. ⬜ Add `kernel_builtin_asts [256]*u8` array (AST strings per module)
3. ⬜ Update `--embed-self` to populate both arrays
4. ⬜ Implement source file search (step 1 of algorithm)
5. ⬜ Implement LANG_MODULE_PATH search (step 2 of algorithm)
6. ⬜ Implement `resolve_require()` with full algorithm
7. ⬜ Handle -r mode (skip) vs normal mode (include) differently

### Key Code Locations

**src/main.lang**:
- `kernel_modules` → rename to `kernel_builtin_modules`
- Add `kernel_builtin_asts` parallel array
- `has_kernel_module()` → rewrite as `resolve_require()`
- `-r` mode AST manipulation

**src/codegen.lang**:
- `embedded_reader_names` and `embedded_reader_funcs` arrays
- `find_reader()` function - checks embedded then external

**src/sexpr_reader.lang**:
- Sets `reader_decl_set_is_ast(n, 1)` for S-expression readers
