# Fix Composition (-c flag)

## Status: In Progress

## Problem Statement

The current `-c` flag tries to build a standalone compiler by including `src/standalone.lang`, which is a broken mini-compiler. This approach:
1. Duplicates compiler infrastructure
2. Has AST round-trip corruption issues
3. Is overly complex

## The Core Insight

**Readers are NOT compilers. Readers are text transformers: source text → AST text.**

The kernel is the compiler. The kernel takes AST and emits native code.

A composed compiler should just be "the regular compiler with some reader source strings embedded."

## Current Broken Flow

```
lang -c lisp reader.lang -o lang_lisp.s

1. Build source string:
   - include reader.lang
   - func reader_transform(t) { return lisp(t); }
   - include "src/standalone.lang"  <- BROKEN: mini-compiler, not real compiler
   - func ___main(...) { ... }
2. Compile this generated source
3. Output assembly
```

Problems:
- standalone.lang is incomplete (missing features)
- Tries to build a NEW compiler from scratch
- Include expansion causes duplication (everything includes std/core.lang)

## Correct Model

A composed compiler is:
1. The kernel (AST → native code) - the regular compiler
2. Embedded reader sources as string constants
3. When a reader is needed, compile it on-demand from embedded source

```
lang -c lisp reader.lang -o lang_lisp

Result: The normal compiler binary, but with:
- String constant: EMBEDDED_LISP_SOURCE = "reader lisp(...) { ... }"
- find_reader() checks embedded sources
- Compiles embedded reader on first use
```

## Implementation Done So Far

### 1. Added embedded reader storage (codegen.lang)
```lang
// Embedded reader registry: AST strings for readers baked into composed compilers
// Each entry: [name_ptr:8][name_len:8][ast_ptr:8][ast_len:8] = 32 bytes
var cg_embedded_readers *u8 = nil;
var cg_embedded_reader_count i64 = 0;
```

### 2. Added LIMIT_EMBEDDED_READERS (limits.lang)
```lang
var LIMIT_EMBEDDED_READERS i64 = 20;
```

### 3. Added embedded reader functions (codegen.lang)
- `add_embedded_reader(name, name_len, src, src_len)` - register an embedded reader
- `find_embedded_reader(name, name_len)` - find embedded reader, returns source or nil
- `compile_from_embedded_ast(name, name_len, src)` - compile embedded source to executable

### 4. Modified find_reader() (codegen.lang)
```lang
func find_reader(name, name_len) {
    // 1. Check registered readers (from current compilation)
    ...

    // 2. Check embedded readers (for composed compilers)
    var embedded_src = find_embedded_reader(name, name_len);
    if embedded_src != nil {
        return compile_from_embedded_ast(name, name_len, embedded_src);
    }

    // 3. Check cached readers in .lang-cache/
    ...
}
```

### 5. Created std/tools.lang
Tool detection utilities to avoid hardcoded paths:
- `find_in_path(tool)` - search PATH for tool
- `find_clang()` - find clang with fallbacks
- `find_as()` - find assembler
- `find_ld()` - find linker
- `find_lli()` - find LLVM interpreter

### 6. Updated codegen.lang to use tool detection
Replaced hardcoded `/usr/bin/clang`, `/usr/bin/as`, `/usr/bin/ld` with dynamic detection.

## Remaining Work

### The Initialization Problem

The key challenge: How do we initialize embedded readers at startup?

**x86 vs LLVM entry point differences:**

```
x86 backend:
  _start (codegen emits)
    → ___main(argc, argv, envp)  [user code provides]
        → main(argc, argv)       [user's main]

LLVM backend:
  clang's _start (libc)
    → main(argc, argv, envp)     [user's main, always gets C ABI signature]
  (no ___main exists!)
```

Key insight: **LLVM has no ___main hook!** clang calls main() directly.

### Options Analyzed

**Option A: ___main hook (x86 only)**
```lang
func ___main(argc i64, argv **u8, envp **u8) i64 {
    init_environ(envp);
    add_embedded_reader("lisp", 4, EMBEDDED_LISP_SRC, strlen(EMBEDDED_LISP_SRC));
    return main(argc, argv);
}
```
- Works for x86
- **Doesn't work for LLVM** - no ___main exists

**Option B: Inject into main() body**
- Modify AST after parsing to add init calls at start of main()
- Complex, invasive

**Option C: Generate source, not assembly**
```bash
./out/lang -c lisp reader.lang -o composed_lisp.lang
./out/lang composed_lisp.lang -o lang_lisp.ll
```
- Two-step process for user
- Clean but less magical

**Option D: Function pointer hook**
```lang
var cg_init_embedded_fn fn() void = nil;
```
- Problem: Include order - can't set before defined

**Option E: Lazy initialization (RECOMMENDED)**
```lang
var cg_embedded_init_done i64 = 0;
var cg_embedded_init_fn fn() void = nil;

func find_reader(name, len) {
    // Lazy init on first reader lookup
    if cg_embedded_init_done == 0 && cg_embedded_init_fn != nil {
        cg_embedded_init_fn();
        cg_embedded_init_done = 1;
    }
    // ... rest of find_reader
}
```
- **Works for BOTH backends!**
- Init happens on first reader lookup (which is during compilation)
- Generated code sets `cg_embedded_init_fn` before including compiler

### Recommended Approach: Lazy Init + Function Pointer

1. Add to codegen.lang:
```lang
var cg_embedded_init_fn fn() void = nil;
var cg_embedded_init_done i64 = 0;
```

2. Modify find_reader() to call init lazily

3. Generated composed source:
```lang
// Embedded reader source
var EMBEDDED_LISP_SRC *u8 = "...reader source...";

// Init function
func init_embedded_readers() void {
    add_embedded_reader("lisp", 4, EMBEDDED_LISP_SRC, strlen(EMBEDDED_LISP_SRC));
}

// Set the hook BEFORE including codegen.lang
// Wait - this doesn't work! cg_embedded_init_fn isn't defined yet!
```

**The include order problem:**
- `cg_embedded_init_fn` is defined in codegen.lang
- We can't assign to it before including codegen.lang
- We can't include codegen.lang first because it needs our init function

### Alternative: Pre-populated Data Approach

Instead of a function pointer, use **data-driven initialization**:

1. Add to codegen.lang:
```lang
// External embedded reader data (set by composed compilers)
var cg_embedded_reader_data *u8 = nil;
var cg_embedded_reader_data_count i64 = 0;
```

2. In find_reader(), check this data and initialize:
```lang
func ensure_embedded_readers_loaded() void {
    if cg_embedded_reader_data == nil { return; }
    if cg_embedded_reader_count > 0 { return; }  // Already loaded

    var i i64 = 0;
    while i < cg_embedded_reader_data_count {
        var entry *u8 = cg_embedded_reader_data + (i * 32);
        // ... read name, src from entry ...
        add_embedded_reader(name, name_len, src, src_len);
        i = i + 1;
    }
}
```

3. Generated composed source:
```lang
// Embedded data - these are globals defined BEFORE includes
var EMBEDDED_NAME_0 *u8 = "lisp";
var EMBEDDED_SRC_0 *u8 = "...reader source...";

// Data array pointing to the above
// BUT: Can't call alloc() at global scope to build array!
```

**Problem:** Can't build the data array at global initialization time.

### Simplest Working Solution: Two-Step Compilation

For now, `-c` outputs SOURCE CODE, not assembly:

```bash
# Step 1: Generate composed source
./out/lang -c lisp reader.lang -o composed_lisp.lang

# Step 2: Compile to binary
LANGBE=llvm ./out/lang composed_lisp.lang -o lang_lisp.ll
clang lang_lisp.ll -o lang_lisp
```

The generated `composed_lisp.lang`:
```lang
// Embedded reader source
var EMBEDDED_LISP_SRC *u8 = "...reader source...";

// Override main to init then delegate
func main(argc i64, argv **u8) i64 {
    add_embedded_reader("lisp", 4, EMBEDDED_LISP_SRC, strlen(EMBEDDED_LISP_SRC));
    return compiler_main(argc, argv);
}

// Include compiler with renamed main
// (requires refactoring main.lang to export compiler_main)
include "src/compiler_core.lang"
```

This requires:
1. Refactoring main.lang to have `compiler_main()` callable
2. Or using a preprocessor-style approach

### Next Steps

**Phase 1: Refactor main.lang**
1. Extract compilation logic from `main()` into `compiler_main(argc, argv)`
2. Have `main()` just call `compiler_main()`
3. This allows composed compilers to define their own `main()` that wraps `compiler_main()`

**Phase 2: Update -c mode**
1. Parse reader source files
2. Extract reader source (the `reader foo(...) { ... }` + any dependencies before it)
3. Generate composed source that:
   - Defines embedded reader source as string literal
   - Defines `main()` that calls `add_embedded_reader()` then `compiler_main()`
   - Includes all compiler sources (which now export `compiler_main`)
4. Either:
   - Output as `.lang` source for user to compile (simpler)
   - Or compile directly to assembly (more magical)

**Phase 3: Test**
1. Test with example/minilisp/lisp.lang
2. Verify composed compiler can compile .lisp files

## Questions to Resolve

1. Should embedded readers store SOURCE or AST?
   - SOURCE is simpler (no AST round-trip issues)
   - AST would avoid re-parsing but has complexity
   - **Current choice: SOURCE**

2. What dependencies does a reader need?
   - std/core.lang (always)
   - Helper functions defined before the reader
   - #parser{} expansions
   - Current compile_reader_to_executable() handles this

3. How to handle multiple embedded readers?
   - Just loop through and call add_embedded_reader() for each
   - Order shouldn't matter

## Related Files

- `src/codegen.lang` - embedded reader storage and compilation
- `src/main.lang` - `-c` flag handling, ___main generation
- `src/standalone.lang` - DEPRECATED, should be removed after fix
- `std/tools.lang` - NEW, tool detection utilities
- `std/core.lang` - includes std/tools.lang now
