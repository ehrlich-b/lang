# Visibility: The `pub` Keyword

## Status: DESIGN

This document describes adding visibility modifiers to lang, enabling proper encapsulation across module boundaries.

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

## Implementation

### Phase 1: Lexer

Add `TOKEN_PUB`:

```lang
// In lexer.lang
var TOKEN_PUB i64 = XX;  // New token

// In tokenize()
if buf_eq_str(start, len, "pub") {
    token_type = TOKEN_PUB;
}
```

Keywords list update:
```lang
var keywords [64]*u8 = [
    "func", "var", "const", "struct", "sum", "type",
    "if", "else", "while", "for", "return", "break", "continue",
    "include", "require", "reader", "match",
    "pub",  // NEW
    nil
];
```

### Phase 2: Parser

Handle `pub` prefix on declarations:

```lang
func parse_top_level_decl() *Decl {
    var is_pub i64 = 0;

    // Check for pub keyword
    if current_token() == TOKEN_PUB {
        is_pub = 1;
        advance();
    }

    if current_token() == TOKEN_FUNC {
        return parse_func_decl(is_pub);
    } else if current_token() == TOKEN_VAR {
        return parse_var_decl(is_pub);
    } else if current_token() == TOKEN_STRUCT {
        return parse_struct_decl(is_pub);
    }
    // ... etc
}

func parse_func_decl(is_pub i64) *FuncDecl {
    var decl *FuncDecl = alloc(sizeof(FuncDecl));
    decl.kind = NODE_FUNC_DECL;
    decl.is_pub = is_pub;
    // ... rest of parsing
}
```

### Phase 3: AST Emit

Emit `pub` in S-expression format:

```lang
func ast_emit_func_decl(decl *FuncDecl) {
    emit_str("(func ");
    if decl.is_pub {
        emit_str("pub ");
    }
    emit_str(decl.name);
    // ... rest
}
```

### Phase 4: S-expr Reader

Parse `pub` from AST:

```lang
func read_func_decl(sexpr *SExpr) *FuncDecl {
    var decl *FuncDecl = alloc(sizeof(FuncDecl));
    decl.kind = NODE_FUNC_DECL;

    var idx i64 = 1;  // After "func"

    // Check for pub
    if sexpr_is_symbol(sexpr.children[idx], "pub") {
        decl.is_pub = 1;
        idx = idx + 1;
    }

    decl.name = sexpr.children[idx].value;
    // ... rest
}
```

### Phase 5: Visibility Tracking in Codegen

Add visibility tracking:

```lang
// Track which symbols are visible in current compilation
var func_is_pub [LIMIT_FUNCS]i64 = [];
var global_is_pub [LIMIT_GLOBALS]i64 = [];
var struct_is_pub [LIMIT_STRUCTS]i64 = [];

// Track which module each symbol came from (for error messages)
var func_module [LIMIT_FUNCS]*u8 = [];
var global_module [LIMIT_GLOBALS]*u8 = [];
var struct_module [LIMIT_STRUCTS]*u8 = [];

// Current module being processed (for requires)
var current_require_module *u8 = nil;
```

### Phase 6: Require Resolution with Visibility

When processing a `require`:

```lang
func process_require(module_name *u8) {
    var ast *u8 = resolve_module(module_name);
    var prog *Program = parse_ast_from_string(ast);

    // Remember which module we're importing from
    var saved_module *u8 = current_require_module;
    current_require_module = module_name;

    // Process declarations
    for each decl in prog.decls {
        if decl.kind == NODE_FUNC_DECL {
            var fd *FuncDecl = decl;

            // Always add to funcs[] (code must be generated)
            var idx i64 = add_func(fd);

            // Track visibility
            func_is_pub[idx] = fd.is_pub;
            func_module[idx] = module_name;

            // Only add to visible names if pub
            if fd.is_pub {
                add_visible_func(fd.name, idx);
            }
        }
        // ... similar for globals, structs
    }

    current_require_module = saved_module;
}
```

### Phase 7: Name Resolution with Visibility Check

When looking up a symbol:

```lang
func lookup_func(name *u8, name_len i64) i64 {
    // First check visible functions
    var idx i64 = find_visible_func(name, name_len);
    if idx >= 0 {
        return idx;
    }

    // Check if it exists but isn't visible
    var hidden_idx i64 = find_any_func(name, name_len);
    if hidden_idx >= 0 {
        var module *u8 = func_module[hidden_idx];
        error_at(current_line,
            "function '%s' is not public in module '%s'",
            name, module);
    }

    // Doesn't exist at all
    error_at(current_line, "unknown function '%s'", name);
    return -1;
}
```

## Bootstrap Plan

This requires careful staging to avoid breaking the bootstrap chain.

### Stage 1: Add Syntax (No Enforcement)

1. Add `TOKEN_PUB` to lexer
2. Add `pub` parsing to parser (sets is_pub flag)
3. Add `pub` to AST emit
4. Add `pub` parsing to sexpr_reader
5. Codegen: Record is_pub but DON'T enforce
6. **Bootstrap** - Compiler can parse `pub` but ignores it

### Stage 2: Add Visibility Tracking (No Enforcement)

1. Add `func_is_pub[]`, `func_module[]` arrays
2. Populate during require resolution
3. Still allow all name lookups (no errors)
4. **Bootstrap** - Tracking works but not enforced

### Stage 3: Annotate Standard Library

1. Add `pub` to all stdlib API functions
2. Keep internal helpers without `pub`
3. **Bootstrap** - stdlib now has visibility annotations

### Stage 4: Enable Enforcement

1. Change `lookup_func` to check visibility
2. Same for globals, structs, etc.
3. **Bootstrap** - Visibility now enforced

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

## Migration Guide

### For Library Authors

Before:
```lang
func helper() void { }
func api() void { helper(); }
```

After:
```lang
func helper() void { }       // Keep private (no change needed)
pub func api() void { helper(); }  // Mark public
```

### For Library Users

If you were depending on internal functions, you'll get errors:
```
error: 'helper' is not public in module 'some_lib'
```

Options:
1. Use the public API instead
2. Ask library author to make it public
3. Fork and modify (not recommended)

## Edge Cases

### Re-exporting

If module A wants to re-export something from module B:

```lang
// module_a.lang
require "module_b"

// Can't directly re-export, but can wrap:
pub func do_thing() void {
    module_b_thing();  // Call the original
}
```

Future: Could add `pub use` syntax for re-export.

### Circular Requires

```lang
// a.lang
require "b"

// b.lang
require "a"  // Circular!
```

Visibility doesn't change cycle detection - it's still an error.

### Visibility in Expressions

Only declarations have visibility. You can't do:
```lang
pub if x > 0 { ... }  // Nonsense
```

## Error Messages

Good error messages are critical:

```
error: function 'internal_helper' is not public
  --> user.lang:15:5
   |
15 |     internal_helper();
   |     ^^^^^^^^^^^^^^^
   |
note: 'internal_helper' is defined in module 'std/core' but not exported
help: did you mean 'public_helper'?
```

Tracking `func_module[]` enables the "defined in module X" note.

## Alternatives Considered

### 1. Underscore Convention

```lang
func _private() void { }  // Convention: underscore = private
func public() void { }
```

Rejected: No enforcement, still pollutes namespace.

### 2. Separate Visibility Keyword

```lang
private func helper() void { }
public func api() void { }
```

Rejected: Two keywords where one suffices. Zig/Rust prove `pub` alone works.

### 3. Export Lists

```lang
module std/core exports (alloc, free, print)

func alloc() { }
func free() { }
func helper() { }  // Not in exports = private
```

Rejected: Separates visibility from definition, harder to maintain.

### 4. File-Level Privacy

```lang
// _internal.lang - underscore prefix = can't be required
```

Rejected: Doesn't solve symbol visibility, only file access.

## Future Extensions

### pub(crate) / pub(module) - Scoped Visibility

```lang
pub(crate) func visible_in_crate() { }  // Like Rust
```

Not needed now. `pub` vs private is sufficient.

### pub use - Re-exports

```lang
pub use other_module.SomeType;  // Re-export from another module
```

Nice to have but not essential.

## Success Criteria

1. `pub` keyword parses and emits correctly
2. Visibility enforced at `require` boundaries
3. `include` ignores visibility (textual paste)
4. Good error messages for visibility violations
5. stdlib properly annotated
6. All tests pass
7. Bootstrap succeeds at each stage

## Related Documents

- `composition_dependencies.md` - How `require` works
- `fix_composition.md` - Composition overview
- `LANG.md` - Language reference (needs update after implementation)
