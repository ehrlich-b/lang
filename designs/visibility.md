# Visibility: The `pub` Keyword

## Status: STAGE 3 COMPLETE, STAGE 4 BLOCKED

**Last Updated**: 2025-01-03

### Implementation Progress

| Stage | Description | Status | Commit |
|-------|-------------|--------|--------|
| 1 | Add `pub` syntax (lexer, parser, AST emit, sexpr reader) | ✅ DONE | Previous session |
| 2 | Add visibility tracking arrays in codegen | ✅ DONE | e52184e |
| 3 | Annotate stdlib with `pub` | ✅ DONE | 88f335a |
| 4 | Enable enforcement at require boundaries | ⏸️ BLOCKED | - |

### What's Done

1. **Syntax**: `pub` keyword works on func, var, struct, enum, reader declarations
2. **AST**: `pub` emits as `(func pub name ...)` in S-expressions
3. **Tracking**: `cg_func_is_pub`, `cg_global_is_pub`, `cg_struct_is_pub`, `cg_enum_is_pub`, `cg_effect_is_pub`, `cg_reader_is_pub` arrays populated
4. **Stdlib**: All public API functions in std/core.lang and std/os/*.lang marked `pub`

### Why Stage 4 is Blocked

**`require` is not implemented.** It parses to `NODE_REQUIRE_DECL` but codegen ignores it completely. Test:

```lang
require "std/core"
func main() i64 {
    println("hello");  // Compiles but println is never defined!
    return 0;
}
```

This generates a call to `@println` that doesn't exist. The code compiles but would fail at link time.

**Visibility enforcement requires require to work first.** The enforcement logic is:
1. When looking up a symbol from a `require`d module
2. Check if it's marked `pub`
3. If not, emit error

But since require doesn't actually import anything, there's nothing to enforce.

### Dependency

Stage 4 is blocked on **Phase 2 of fix_composition.md**:

> ### Phase 2: Add `require` keyword (composition_dependencies.md)
> 1. Add `TOKEN_REQUIRE` to lexer, `NODE_REQUIRE` to parser  ← DONE
> 2. Add `kernel_modules [256]*u8` tracking to codegen
> 3. Update `--embed-self` to populate `kernel_modules`
> 4. Update `-r` mode to resolve requires against `kernel_modules`
> 5. Add `LANG_MODULE_PATH` for external module resolution

### Next Steps

1. **Return to fix_composition.md** - implement require resolution
2. Once require works, return here to implement enforcement
3. Enforcement implementation:
   - Track `cg_func_from_require[]` (or similar) to know which symbols came from require
   - In `find_func()`, `find_global()`, etc: if symbol is from require and not pub, error

### Files Modified (Stages 1-3)

**Stage 1 (syntax)**:
- src/lexer.lang - TOKEN_PUB
- src/parser.lang - parse pub prefix, is_pub fields
- src/ast_emit.lang - emit pub in S-expressions
- src/sexpr_reader.lang - read pub from S-expressions

**Stage 2 (tracking)**:
- src/codegen.lang - visibility tracking arrays, add_* functions track is_pub
- src/codegen_llvm.lang - same for LLVM backend

**Stage 3 (stdlib)**:
- std/core.lang - pub on vec_*, map_*, file_*, str*, print*, itoa, etc.
- std/os/libc_macos.lang - pub on O_*, malloc, free, alloc, exit, getenv, etc.
- std/os/libc.lang - same
- std/os/linux_x86_64.lang - same
- std/os/macos_arm64.lang - same
- std/tools.lang - pub on find_in_path, find_clang, find_as, find_ld, find_lli

### Bootstrap Status

All stages bootstrapped successfully:
- 169/169 LLVM tests pass
- Fixed points verified
- Committed and pushed

---

## Original Design (Reference)

[Rest of original design document follows...]

## Motivation

### The Problem: One Massive Global Namespace

Currently, all symbols are globally visible. When you `include` or `require` a module, you get **everything**:

```lang
// std/alloc.lang
func align_up(x i64) i64 { ... }        // Implementation detail
func find_bucket(size i64) i64 { ... }  // Implementation detail
func alloc(size i64) *u8 { ... }        // Actual API

// user.lang
require "std/alloc"

func main() i64 {
    alloc(100);        // Intended use
    align_up(50);      // Oops, using internal function
    find_bucket(10);   // Fragile dependency on implementation
    return 0;
}
```

Problems:
1. **Namespace pollution** - Hundreds of internal helpers in global scope
2. **Fragile dependencies** - Users accidentally depend on internals
3. **No encapsulation** - Can't refactor internals without breaking users
4. **Name conflicts** - Internal names from different modules can clash

### The Solution: Visibility Boundaries

```lang
// std/alloc.lang
func align_up(x i64) i64 { ... }        // Private (default)
func find_bucket(size i64) i64 { ... }  // Private

pub func alloc(size i64) *u8 { ... }    // Public - part of API
pub func free(ptr *u8) void { ... }     // Public

// user.lang
require "std/alloc"

func main() i64 {
    alloc(100);        // Works - alloc is pub
    align_up(50);      // Error: 'align_up' is not public
    return 0;
}
```

## Design Principles

1. **Private by default** - Symbols are private unless marked `pub`
2. **Simple syntax** - Just one keyword, no `private`/`protected`/etc.
3. **Module boundary = require** - `include` ignores visibility (textual paste)
4. **No field-level visibility** - If struct is pub, all fields are pub

## Syntax

### Functions

```lang
func private_helper() void { ... }      // Private (no keyword)
pub func public_api() void { ... }      // Public
```

### Globals

```lang
var internal_state i64 = 0;             // Private
pub var config_value i64 = 100;         // Public
```

### Constants

```lang
const INTERNAL_MAGIC i64 = 0xDEAD;      // Private
pub const API_VERSION i64 = 1;          // Public
```

### Structs

```lang
struct InternalNode { ... }             // Private
pub struct PublicConfig { ... }         // Public (all fields accessible)
```

### Sum Types

```lang
sum InternalState { ... }               // Private
pub sum Result { Ok(i64), Err(*u8) }    // Public (variants accessible)
```

### Type Aliases

```lang
type InternalPtr = *u8;                 // Private
pub type Handle = i64;                  // Public
```

### Readers

```lang
reader internal_helper(t *u8) *u8 { }   // Private
pub reader lang(text *u8) *u8 { ... }   // Public (needed for composition)
```

## Semantics

### Visibility Boundary: `require`

The `require` keyword creates a visibility boundary:

```lang
// module_a.lang
func helper() void { }
pub func api() void { helper(); }

// module_b.lang
require "module_a"

func main() i64 {
    api();      // OK - api is pub
    helper();   // ERROR - helper is not pub in module_a
    return 0;
}
```

### No Boundary: `include`

The `include` keyword is textual paste - no visibility checking:

```lang
// internal/helpers.lang
func helper() void { }  // No pub needed

// module.lang
include "internal/helpers.lang"

pub func api() void {
    helper();  // OK - helper is now part of this module
}
```

This means:
- Use `include` for private implementation files
- Use `require` for public module dependencies
- Visibility only checked at `require` boundaries

### Composition (`-r` mode)

Composition is like `include` - all symbols are combined:

```bash
kernel_self -r lang lang_reader.ast
```

The reader's private symbols are included in the composed binary. They're callable by the reader's own code. Visibility doesn't apply because composition creates one program, not separate modules.

### Within-Module Visibility

All symbols within the same module (same file + includes) can see each other:

```lang
// my_module.lang
include "internal/impl.lang"  // All symbols from impl.lang visible here

func private_func() void { }

pub func public_func() void {
    private_func();           // OK - same module
    internal_helper();        // OK - from included file
}
```

## AST Representation

### Option A: Flag on Nodes (Chosen)

Each declaration node gets an `is_pub` field:

```lang
struct FuncDecl {
    kind i64;
    name *u8;
    name_len i64;
    is_pub i64;       // 0 = private, 1 = public
    // ... rest of fields
}
```

AST S-expression format:
```
(func pub name (args) ret_type body)     // Public
(func name (args) ret_type body)         // Private (no pub)

(global pub name type init)              // Public
(global name type init)                  // Private

(struct pub Name fields)                 // Public
(struct Name fields)                     // Private
```

The `pub` keyword appears right after the declaration type.

### Why Not a Wrapper Node?

A wrapper like `(pub (func ...))` is cleaner but:
- Adds nesting complexity
- Every declaration handler needs unwrap logic
- Flag is simpler to implement

## Bootstrap Plan

This requires careful staging to avoid breaking the bootstrap chain.

### Stage 1: Add Syntax (No Enforcement) ✅

1. Add `TOKEN_PUB` to lexer
2. Add `pub` parsing to parser (sets is_pub flag)
3. Add `pub` to AST emit
4. Add `pub` parsing to sexpr_reader
5. Codegen: Record is_pub but DON'T enforce
6. **Bootstrap** - Compiler can parse `pub` but ignores it

### Stage 2: Add Visibility Tracking (No Enforcement) ✅

1. Add `func_is_pub[]`, `func_module[]` arrays
2. Populate during require resolution
3. Still allow all name lookups (no errors)
4. **Bootstrap** - Tracking works but not enforced

### Stage 3: Annotate Standard Library ✅

1. Add `pub` to all stdlib API functions
2. Keep internal helpers without `pub`
3. **Bootstrap** - stdlib now has visibility annotations

### Stage 4: Enable Enforcement ⏸️ BLOCKED

1. Change `lookup_func` to check visibility
2. Same for globals, structs, etc.
3. **Bootstrap** - Visibility now enforced

**BLOCKED**: Requires `require` to actually work first.

At each stage, if something breaks, we know exactly what changed.

## Standard Library Visibility

### std/core.lang (The Root)

```lang
// Public API
pub func alloc(size i64) *u8 { ... }
pub func free(ptr *u8) void { ... }
pub func realloc(ptr *u8, size i64) *u8 { ... }
pub func print(s *u8) void { ... }
pub func println(s *u8) void { ... }
pub func strlen(s *u8) i64 { ... }
pub func strcmp(a *u8, b *u8) i64 { ... }
pub func memcpy(dst *u8, src *u8, n i64) void { ... }
// ... other core functions

// Private implementation
func align_size(size i64) i64 { ... }
func syscall_write(fd i64, buf *u8, len i64) i64 { ... }
func mmap_alloc(size i64) *u8 { ... }
```

### Compiler Sources

Compiler internal files don't need `pub` because they're combined via `include`:

```lang
// src/main.lang
include "src/lexer.lang"    // All symbols visible (same compilation)
include "src/parser.lang"
include "src/codegen.lang"
```

The compiler is one program, not separate modules requiring each other.

## Success Criteria

1. ✅ `pub` keyword parses and emits correctly
2. ⏸️ Visibility enforced at `require` boundaries (blocked)
3. ✅ `include` ignores visibility (textual paste)
4. ⏸️ Good error messages for visibility violations (blocked)
5. ✅ stdlib properly annotated
6. ✅ All tests pass
7. ✅ Bootstrap succeeds at each stage (1-3)
