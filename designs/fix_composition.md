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

**Option A: ___main hook (x86 backend)**
```lang
// Generated composed source
var EMBEDDED_LISP_SRC *u8 = "...reader source...";

func ___main(argc i64, argv **u8, envp **u8) i64 {
    init_environ(envp);
    add_embedded_reader("lisp", 4, EMBEDDED_LISP_SRC, strlen(EMBEDDED_LISP_SRC));
    return main(argc, argv);
}

include "std/core.lang"
... all compiler includes ...
include "src/main.lang"  // Uses our ___main, not its own
```

Problem: main.lang already appends its own ___main in some modes.

**Option B: Lazy initialization in find_reader()**
```lang
var cg_embedded_init_done i64 = 0;

func find_reader(...) {
    if cg_embedded_init_done == 0 {
        init_embedded_readers();  // Call generated init function
        cg_embedded_init_done = 1;
    }
    ...
}
```

Problem: How to call a function that may or may not exist?

**Option C: Generate source, not assembly**
```bash
# Step 1: Generate composed source
./out/lang -c lisp reader.lang -o composed_lisp.lang

# Step 2: User compiles the source
./out/lang composed_lisp.lang -o lang_lisp.ll
clang lang_lisp.ll -o lang_lisp
```

The composed_lisp.lang contains everything needed. User compiles it.

**Option D: Function pointer hook**
```lang
// In codegen.lang
var cg_init_embedded_fn fn() void = nil;

// In find_reader() or early in main()
if cg_init_embedded_fn != nil {
    cg_init_embedded_fn();
    cg_init_embedded_fn = nil;  // Only call once
}

// Generated composed source sets this:
func my_init() void {
    add_embedded_reader(...);
}
var cg_init_embedded_fn fn() void = &my_init;
```

Problem: Include order - can't set variable before it's defined.

### Recommended Approach

**Option A (___main hook) seems most viable:**

1. Remove ___main generation from the normal `-c` path in main.lang
2. The generated composed source provides its own ___main that:
   - Calls init_environ(envp)
   - Calls add_embedded_reader() for each embedded reader
   - Calls main(argc, argv)
3. Include all compiler sources INCLUDING main.lang (but main.lang doesn't define ___main in this case)

For LLVM backend (which doesn't use ___main):
- Could add an `__attribute__((constructor))` equivalent
- Or add init call at very start of main()

### Next Steps

1. Refactor main.lang's ___main generation to be conditional
2. Update `-c` mode to:
   - Read reader source files
   - Extract reader declarations (just the `reader foo(...) { ... }` part + dependencies)
   - Generate source with embedded reader strings
   - Generate custom ___main that initializes them
   - Include all compiler sources
   - Compile to output
3. Test with example/minilisp/lisp.lang

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
