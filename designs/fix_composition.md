# Fix Composition (compose command)

## Status: In Progress

**Current state**: Basic `-r` and `--embed-self` modes exist but use single variables instead of arrays. Need to migrate to array-based storage for multiple readers.

## The Core Insight: Pure AST Manipulation

**This is ALL just AST manipulation.** No lang parsing. No source code. Just:
1. Read AST (S-expressions)
2. Combine AST nodes
3. Poke values into AST nodes
4. Re-serialize AST
5. Generate code from AST

The compiler never needs to understand lang syntax to compose readers. It only manipulates S-expression AST.

## The Three Steps

### Step 1: Compile bare kernel to executable

```
[some compiler] compiles bare_kernel.ast → .ll → exe
```

This bare kernel:
- Understands S-expression AST
- Can generate LLVM IR / x86
- Has `var self_kernel *u8 = ""` (empty)
- Has `var embedded_reader_names [1024]*u8 = []` (empty array literal)
- Has `var embedded_reader_funcs [1024]*u8 = []` (empty array literal)

### Step 2: Create self-aware kernel (`--embed-self`)

```
bare_kernel --embed-self bare_kernel.ast → kernel_self exe
```

This is just AST manipulation:
1. Read `bare_kernel.ast` file
2. Parse it as S-expressions → AST nodes
3. Find `self_kernel` variable in AST
4. Poke the entire AST string (from file) into `self_kernel`'s initializer
5. Generate code from modified AST → .ll → exe

Result: `kernel_self` exe contains a string with its own AST.

### Step 3: Add reader (`-r`)

```
kernel_self -r lang lang_reader.ast → lang1 exe
```

This is nearly identical to `--embed-self`:
1. Read `self_kernel` string (which contains `bare_kernel.ast`)
2. Parse it as S-expressions → base AST nodes
3. Read `lang_reader.ast` file
4. Parse it as S-expressions → reader AST nodes
5. **Combine**: append reader declarations to base declarations
6. Find `embedded_reader_names`, append `(string "lang")` to its `array_literal`
7. Find `embedded_reader_funcs`, append `(ident reader_lang)` to its `array_literal`
8. **Re-serialize** the entire combined AST to string
9. Find `self_kernel`, poke the combined AST string into it
10. Generate code from combined AST → .ll → exe

Result: `lang1` exe contains:
- All kernel code
- All reader code (the `reader_lang` function from `lang_reader.ast`)
- `self_kernel` = combined AST (for future `-r` operations!)
- `embedded_reader_funcs[0]` pointing to `reader_lang`

## Data Structures (Target Design)

```lang
// In kernel source - these get poked by -r mode
var self_kernel *u8 = "";                    // Full program AST (quine)
var embedded_reader_names [1024]*u8 = [];    // ["lang", "lisp", nil, nil, ...]
var embedded_reader_funcs [1024]*u8 = [];    // [reader_lang, reader_lisp, nil, nil, ...]
// No count needed - loop until nil!
```

Array support was added specifically for this purpose - to store multiple reader function pointers.

### Array Literals for Poking

The `-r` mode pokes into the `array_literal` nodes:

```lisp
; Before -r:
(var embedded_reader_names (type_array 1024 (type_ptr (type_base u8)))
  (array_literal))

; After -r lang:
(var embedded_reader_names (type_array 1024 (type_ptr (type_base u8)))
  (array_literal (string "lang")))

; After -r lang, then -r lisp:
(var embedded_reader_names (type_array 1024 (type_ptr (type_base u8)))
  (array_literal (string "lang") (string "lisp")))
```

The AST infrastructure exists:
- ✅ Parser: `[e1, e2]` → `NODE_ARRAY_LITERAL`
- ✅ sexpr_reader: parses `(array_literal ...)`
- ✅ ast_emit: emits `(array_literal ...)`
- ❌ codegen_llvm: **TODO** - emit LLVM array initializers

Codegen needs to emit:
```llvm
@embedded_reader_names = global [1024 x i64] [
  i64 ptrtoint (i8* @.str_lang to i64),
  i64 ptrtoint (i8* @.str_lisp to i64),
  i64 0, i64 0, ...  ; rest zero-filled
]
```

## The Quine Pattern

The critical insight: **`self_kernel` contains AST that contains `self_kernel`**.

Before `-r`:
```
self_kernel = "(program ... (var self_kernel *u8 (string \"\")) ...)"
```

After `-r lang`:
```
self_kernel = "(program ... (var self_kernel *u8 (string \"<THIS ENTIRE STRING>\")) ... (func reader_lang ...))"
```

The AST string inside `self_kernel` must be updated to include the combined AST with the reader. This is what enables chaining: the resulting binary can do another `-r` operation.

## What This Is NOT

- **NOT** parsing lang source code
- **NOT** compiling readers to separate executables
- **NOT** calling `parse_program()` on anything
- **NOT** using the lang tokenizer or parser

Everything is S-expression AST. The only parser used is `parse_ast_from_string()` (the S-expr parser).

## Runtime: find_reader()

At runtime, when code uses `#lang{}`:

```lang
func find_reader(name *u8, len i64) *func {
    var i i64 = 0;
    while i < 1024 {
        var n *u8 = embedded_reader_names[i];
        if n == nil { return nil; }  // Reached end - no more readers
        if strlen(n) == len && memcmp(n, name, len) {
            return embedded_reader_funcs[i];  // Direct function pointer!
        }
        i = i + 1;
    }
    return nil;
}
```

Loop until nil - no count variable needed. The reader function was compiled into the binary. No subprocess, no clang at runtime.

## Bootstrap Chain

```bash
# 1. Use trusted compiler to emit kernel AST
lang_trusted --emit-expanded-ast src/kernel.lang -o bare_kernel.ast

# 2. Compile bare kernel
lang_trusted bare_kernel.ast -o bare_kernel

# 3. Create self-aware kernel (one-time bootstrap)
bare_kernel --embed-self bare_kernel.ast -o kernel_self

# 4. Emit lang reader AST
lang_trusted --emit-expanded-ast src/lang_reader.lang -o lang_reader.ast

# 5. Add lang reader
kernel_self -r lang lang_reader.ast -o lang1

# lang1 can now:
#   - Compile .lang files (has lang reader)
#   - Do further -r operations (has self_kernel with combined AST)
```

## Implementation Checklist

- [x] `--emit-expanded-ast` flag - outputs parsed+expanded AST as S-expressions
- [x] `--embed-self` mode - creates self-aware kernel from bare kernel
- [x] `-r` mode - basic structure (currently uses single variables)
- [x] `parse_ast_from_string()` - S-expression parser (in sexpr_reader.lang)
- [x] `ast_emit_program()` - AST to S-expression serializer
- [x] Array type support in lang (`[N]T` syntax)
- [x] Array literal AST support (`NODE_ARRAY_LITERAL`, sexpr_reader, ast_emit)
- [ ] **TODO**: Array literal codegen in codegen_llvm.lang
- [ ] **TODO**: Migrate embedded_reader vars to arrays with empty `[]` literals
- [ ] **TODO**: Update `-r` mode to append to `array_literal` nodes
- [ ] **TODO**: Skip `compile_reader_to_executable()` for LLVM backend
- [ ] **TODO**: Update `find_reader()` to loop arrays until nil

## The Current Bug

When codegen sees a `(reader lang ...)` node, it calls `add_reader()` which calls `compile_reader_to_executable()`. This tries to parse the reader body as lang source code, which fails.

**The fix**: Reader declarations in embedded AST should NOT trigger `compile_reader_to_executable()`. The reader is emitted as a function by `llvm_emit_reader()`. At runtime, `find_reader()` should return the function pointer from `embedded_reader_funcs[]`.

## Files

- `src/main.lang` - `--embed-self` and `-r` mode implementation
- `src/sexpr_reader.lang` - S-expression parser (`parse_ast_from_string`)
- `src/ast_emit.lang` - AST serializer (`ast_emit_program`)
- `src/codegen.lang` - `add_reader()`, `find_reader()` - needs fix
- `src/codegen_llvm.lang` - `llvm_emit_reader()` - emits reader as function
