# Array Support

## Status: Not Started

## Motivation

While implementing multi-reader composition (`-r` flag), we discovered that lang has no array support. The `TYPE_ARRAY` constant exists but is never used - `parse_type()` only handles pointers, functions, closures, and base types.

We need arrays to store N embedded readers in a self-aware kernel. Currently limited to a single reader slot.

## Design Philosophy

Lang's collection story has three levels, matching the C-like low-level vibes:

| Level | What | Length Knowledge | Bounds Checking | Status |
|-------|------|------------------|-----------------|--------|
| **Pointers** | `*T` | None - you track it | None | **Have now** |
| **Arrays** | `[N]T` | Compile-time (in type) | Compile-time for constants | **Adding** |
| **Slices** | `struct { ptr, len }` | Runtime (in struct) | Runtime (library function) | **Future std** |

**Key principle**: No hidden machinery. Arrays are just storage allocation with sugar. Slices are user-defined structs, not language magic.

## What We Have Now (Level 0: Pointers)

```lang
var p *u8 = alloc(160);      // 20 * 8 bytes
*(p + 24) = something;       // Manual pointer arithmetic
// Length? What length? You track it yourself.
```

With a raw pointer, you **cannot** know where allocated memory ends. You either:
1. Track length separately (like Vec does with a header)
2. Use sentinel value (like C strings use `\0`)
3. Bake length into the type (arrays - what we're adding)

## What We're Adding (Level 1: Arrays)

### Core Semantics

```lang
var arr [20]i64;             // Allocates 160 bytes, type is [20]i64
arr[3] = 42;                 // Sugar for *(arr + 24)
var x = arr[i];              // No runtime bounds check
```

**Arrays are storage with compile-time known size.** The size N is part of the type.

### Compile-Time Bounds Checking

For constant indices, the compiler catches out-of-bounds access:

```lang
var arr [20]i64;
arr[0] = 1;      // OK: 0 < 20
arr[19] = 1;     // OK: 19 < 20
arr[i] = 1;      // OK: runtime index, no check
arr[20] = 1;     // COMPILE ERROR: index 20 out of bounds for [20]i64
arr[100] = 1;    // COMPILE ERROR: index 100 out of bounds for [20]i64
```

**No runtime bounds checking** - that's not the vibe. If you want safety, use a checked accessor or the future Slice type.

### Array Decay to Pointer

When passed to functions or assigned to pointers, arrays decay to pointers (C-style):

```lang
func sum(p *i64, len i64) i64 { ... }

var arr [20]i64 = [...];
sum(arr, 20);                // arr decays to *i64, length lost
// OR explicit:
sum(&arr[0], 20);            // Same thing
```

**We are NOT adding `*[N]T` (pointer-to-array-with-length).** Too complex for the benefit. You want the length? Track it yourself.

### Global Array Literals

Array literals are supported for global variable initialization:

```lang
var names [3]*u8 = ["alice", "bob", "charlie"];
var counts [5]i64 = [0, 0, 0, 0, 0];
var funcs [20]*u8 = [nil, nil, nil, ...];  // For composition
```

### Local Arrays

Local arrays allocate on the stack:

```lang
func foo() i64 {
    var arr [10]i64;         // 80 bytes on stack
    arr[0] = 1;
    return arr[0];
}
```

Local array literals are a stretch goal - can use element-by-element init:

```lang
func foo() i64 {
    var arr [3]i64;
    arr[0] = 1; arr[1] = 2; arr[2] = 3;
    return arr[1];
}
```

## Future: Slices (Level 2: std library)

Slices will be a **library feature**, not language magic:

```lang
// std/slice.lang (future)
struct Slice {
    ptr *u8,
    len i64
}

func slice_new(ptr *u8, len i64) Slice {
    var s Slice;
    s.ptr = ptr;
    s.len = len;
    return s;
}

func slice_get(s *Slice, i i64) *u8 {
    if i < 0 { panic("negative index"); }
    if i >= s.len { panic("index out of bounds"); }
    return s.ptr + i * 8;
}

func slice_set(s *Slice, i i64, val *u8) void {
    if i < 0 { panic("negative index"); }
    if i >= s.len { panic("index out of bounds"); }
    var p **u8 = s.ptr + i * 8;
    *p = val;
}

// Usage:
var arr [20]i64 = [...];
var s Slice = slice_new(arr, 20);
slice_set(&s, 3, 42);  // Bounds checked!
```

**No fat pointers, no hidden control flow.** Just a struct with explicit accessors.
User chooses: raw speed (arrays) or safety (slices).

## Syntax

### Array Types

```lang
var arr [20]i64;             // Array of 20 i64s
var ptrs [10]*u8;            // Array of 10 pointers
var nested [5][3]i64;        // 2D array (stretch goal)
```

### Array Literals

```lang
var arr [3]i64 = [1, 2, 3];
var ptrs [2]*u8 = [nil, nil];
var mixed [3]*u8 = ["hello", nil, "world"];
```

### Array Access

```lang
arr[0] = 42;                 // Write
var x i64 = arr[i];          // Read
```

## AST Representation

### Type: TYPE_ARRAY (already defined = 3)

Layout: `[kind:8][size:8][elem:8]` = 24 bytes

```lang
func array_type_alloc() *u8;
func array_type_size(t *u8) i64;
func array_type_set_size(t *u8, size i64) void;
func array_type_elem(t *u8) *u8;
func array_type_set_elem(t *u8, elem *u8) void;
```

### Expression: NODE_ARRAY_LITERAL (new, = 42)

Layout: `[kind:8][elems:8][count:8]` = 24 bytes

```lang
func array_literal_alloc() *u8;
func array_literal_elems(node *u8) *u8;    // Pointer to array of expr pointers
func array_literal_set_elems(node *u8, elems *u8) void;
func array_literal_count(node *u8) i64;
func array_literal_set_count(node *u8, count i64) void;
```

### S-Expression Format

```lisp
; Array type
(type_array 20 (type_base i64))
(type_array 10 (type_ptr (type_base u8)))

; Array literal expression
(array_literal (number 1) (number 2) (number 3))
(array_literal (nil) (nil) (ident reader_lang))

; Variable with array type and initializer
(var names (type_array 3 (type_ptr (type_base u8)))
  (array_literal (string "alice") (string "bob") (string "charlie")))

; For composition - function pointers in array
(var embedded_reader_funcs (type_array 20 (type_ptr (type_base u8)))
  (array_literal (nil) (ident reader_lang) (nil) ...))
```

## Implementation Plan

### Phase 1: Parser

**1a. Array type syntax in `parse_type()`:**
```lang
// Add at start of parse_type():
if parse_check(TOKEN_LBRACKET) {
    parse_advance();  // consume '['
    var size_tok *u8 = parse_expect(TOKEN_NUMBER, "expected array size");
    var size i64 = token_to_int(size_tok);
    parse_expect(TOKEN_RBRACKET, "expected ']' after array size");

    var elem *u8 = parse_type();

    var t *u8 = array_type_alloc();
    array_type_set_size(t, size);
    array_type_set_elem(t, elem);
    return t;
}
```

**1b. Array literal syntax in `parse_primary()`:**
```lang
// Add case for '[' that's not followed by number (index expr handled elsewhere)
if parse_check(TOKEN_LBRACKET) {
    // Peek ahead to distinguish [N]T (type) from [e1, e2] (literal)
    // If next is number followed by ']', it's a type context
    // Otherwise it's a literal
    parse_advance();  // consume '['

    var elems *u8 = vec_new(8);
    if !parse_check(TOKEN_RBRACKET) {
        vec_push(elems, parse_expression());
        while parse_match(TOKEN_COMMA) {
            vec_push(elems, parse_expression());
        }
    }
    parse_expect(TOKEN_RBRACKET, "expected ']'");

    var node *u8 = array_literal_alloc();
    array_literal_set_elems(node, vec_data(elems));
    array_literal_set_count(node, vec_len(elems));
    return node;
}
```

### Phase 2: AST Accessors

Add to `src/parser.lang`:

```lang
// TYPE_ARRAY = 3 (already defined)
// ArrayType: [kind:8][size:8][elem:8] = 24 bytes

func array_type_alloc() *u8 {
    var t *u8 = alloc(24);
    type_set_kind(t, TYPE_ARRAY);
    return t;
}

func array_type_size(t *u8) i64 {
    var p *i64 = t + 8;
    return *p;
}

func array_type_set_size(t *u8, size i64) void {
    var p *i64 = t + 8;
    *p = size;
}

func array_type_elem(t *u8) *u8 {
    var p **u8 = t + 16;
    return *p;
}

func array_type_set_elem(t *u8, elem *u8) void {
    var p **u8 = t + 16;
    *p = elem;
}

// NODE_ARRAY_LITERAL = 42
// ArrayLiteral: [kind:8][elems:8][count:8] = 24 bytes

var NODE_ARRAY_LITERAL i64 = 42;

func array_literal_alloc() *u8 {
    var node *u8 = alloc(24);
    node_set_kind(node, NODE_ARRAY_LITERAL);
    return node;
}

func array_literal_elems(node *u8) *u8 {
    var p **u8 = node + 8;
    return *p;
}

func array_literal_set_elems(node *u8, elems *u8) void {
    var p **u8 = node + 8;
    *p = elems;
}

func array_literal_count(node *u8) i64 {
    var p *i64 = node + 16;
    return *p;
}

func array_literal_set_count(node *u8, count i64) void {
    var p *i64 = node + 16;
    *p = count;
}
```

### Phase 3: AST Emit

Add to `src/ast_emit.lang`:

```lang
// In ast_emit_type():
if kind == TYPE_ARRAY {
    ast_emit_str("(type_array ");
    ast_emit_int(array_type_size(t));
    ast_emit_str(" ");
    ast_emit_type(array_type_elem(t));
    ast_emit_str(")");
    return;
}

// In ast_emit_expr() or ast_emit_node():
if kind == NODE_ARRAY_LITERAL {
    ast_emit_str("(array_literal");
    var elems *u8 = array_literal_elems(node);
    var count i64 = array_literal_count(node);
    var i i64 = 0;
    while i < count {
        ast_emit_str(" ");
        var elem *u8 = get_ptr_at(elems, i);
        ast_emit_expr(elem);
        i = i + 1;
    }
    ast_emit_str(")");
    return;
}
```

### Phase 4: S-Expression Reader

Add to `src/sexpr_reader.lang`:

```lang
// In parse_sexpr_type():
if streq_n(head, head_len, "type_array", 10) {
    var size_sexpr *u8 = sexpr_child(sexpr, 1);
    var size i64 = sexpr_to_int(size_sexpr);
    var elem_sexpr *u8 = sexpr_child(sexpr, 2);
    var elem *u8 = parse_sexpr_type(elem_sexpr);

    var t *u8 = array_type_alloc();
    array_type_set_size(t, size);
    array_type_set_elem(t, elem);
    return t;
}

// In parse_sexpr_expr():
if streq_n(head, head_len, "array_literal", 13) {
    var node *u8 = array_literal_alloc();
    var count i64 = sexpr_child_count(sexpr) - 1;  // Minus head
    var elems *u8 = alloc(count * 8);

    var i i64 = 0;
    while i < count {
        var child *u8 = sexpr_child(sexpr, i + 1);
        var elem *u8 = parse_sexpr_expr(child);
        set_ptr_at(elems, i, elem);
        i = i + 1;
    }

    array_literal_set_elems(node, elems);
    array_literal_set_count(node, count);
    return node;
}
```

### Phase 5: Index Expression Codegen

**Critical**: `NODE_INDEX_EXPR` is parsed but not codegen'd! Need to implement.

```lang
// In codegen.lang emit_expr():
if kind == NODE_INDEX_EXPR {
    // IndexExpr: [kind:8][expr:8][index:8]
    var base_expr *u8 = index_expr_base(node);
    var index_expr *u8 = index_expr_index(node);
    var base_type *u8 = expr_type(base_expr);

    // Get element type and size
    var elem_type *u8;
    var elem_size i64;
    if type_kind(base_type) == TYPE_ARRAY {
        elem_type = array_type_elem(base_type);
    } else if type_kind(base_type) == TYPE_PTR {
        elem_type = ptr_type_elem(base_type);
    }
    elem_size = type_size(elem_type);

    // Emit: base + index * elem_size
    emit_expr(base_expr);           // Result in rax
    emit_line("    push %rax");
    emit_expr(index_expr);          // Index in rax
    emit_line("    imul $", elem_size, ", %rax");
    emit_line("    pop %rcx");
    emit_line("    add %rcx, %rax"); // Address in rax

    // Load value (for rvalue) or leave address (for lvalue)
    // ... context-dependent
}
```

### Phase 6: Codegen - Global Arrays

```lang
// x86: emit in .data section
// For: var arr [3]i64 = [1, 2, 3];
.data
arr:
    .quad 1
    .quad 2
    .quad 3

// For: var arr [20]i64;  (uninitialized)
.bss
arr:
    .zero 160

// LLVM:
@arr = global [3 x i64] [i64 1, i64 2, i64 3]
@arr_zero = global [20 x i64] zeroinitializer
```

### Phase 7: Codegen - Local Arrays

```lang
// x86: allocate on stack
// For: var arr [3]i64;
sub $24, %rsp        // 3 * 8 bytes
// arr is at %rbp - offset

// LLVM:
%arr = alloca [3 x i64]
```

### Phase 8: Compile-Time Bounds Check

In semantic analysis or codegen, when emitting index expression:

```lang
// If index is a constant (NODE_NUMBER_EXPR) and base is array type:
if node_kind(index_expr) == NODE_NUMBER_EXPR {
    var idx i64 = number_expr_value(index_expr);
    var arr_size i64 = array_type_size(base_type);
    if idx < 0 {
        error("negative array index");
    }
    if idx >= arr_size {
        error("array index ", idx, " out of bounds for [", arr_size, "]T");
    }
}
```

## Decisions

| Question | Decision | Rationale |
|----------|----------|-----------|
| Syntax | `[N]T` | Matches C, familiar |
| Array decay | Yes, to `*T` | C compatibility, simple |
| `*[N]T` pointer-to-array | **No** | Too complex, just use `*T` + length |
| Runtime bounds check | **No** | Not the vibe, use Slice for safety |
| Compile-time bounds check | **Yes** | Catches obvious bugs, zero cost |
| `.len` property | **No** | You know the size, you wrote it |
| Local array literals | Stretch goal | Can init element-by-element |
| 2D arrays | Stretch goal | `[M][N]T` |
| Zero-size arrays | Error | No use case |
| Mismatched literal size | Error | `[3]i64 = [1, 2]` is error |
| Array assignment | Pointer copy | `arr2 = arr1` copies address, not values |
| Slices | Future std library | Not language feature |

## Test Cases

### Core Tests (test/suite/)

**200_array_basic.lang** - Declaration and access:
```lang
func main() i64 {
    var arr [3]i64;
    arr[0] = 10;
    arr[1] = 20;
    arr[2] = 30;
    return arr[0] + arr[1] + arr[2];  // 60
}
```

**201_array_literal.lang** - Literal initialization:
```lang
var arr [3]i64 = [100, 200, 300];

func main() i64 {
    return arr[1];  // 200
}
```

**202_array_pointer.lang** - Array of pointers:
```lang
var names [3]*u8 = ["alice", "bob", "charlie"];

func main() i64 {
    if *names[0] == 'a' {
        if *names[2] == 'c' {
            return 1;
        }
    }
    return 0;  // 1
}
```

**203_array_loop.lang** - Iteration:
```lang
var arr [5]i64 = [1, 2, 3, 4, 5];

func main() i64 {
    var sum i64 = 0;
    var i i64 = 0;
    while i < 5 {
        sum = sum + arr[i];
        i = i + 1;
    }
    return sum;  // 15
}
```

**204_array_param.lang** - Array decay to pointer:
```lang
func sum_first_two(p *i64) i64 {
    var a i64 = *p;
    var b i64 = *(p + 8);
    return a + b;
}

var arr [3]i64 = [10, 20, 30];

func main() i64 {
    return sum_first_two(arr);  // 30 (array decays to pointer)
}
```

**205_array_global.lang** - Mutable global array:
```lang
var counts [10]i64;

func increment(i i64) void {
    counts[i] = counts[i] + 1;
}

func main() i64 {
    increment(3);
    increment(3);
    increment(7);
    return counts[3] + counts[7];  // 3
}
```

**206_array_local.lang** - Stack-allocated array:
```lang
func test() i64 {
    var arr [4]i64;
    arr[0] = 1;
    arr[1] = 2;
    arr[2] = 3;
    arr[3] = 4;
    return arr[0] + arr[3];  // 5
}

func main() i64 {
    return test();
}
```

**207_array_nested_access.lang** - Index with expression:
```lang
var arr [10]i64 = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90];

func main() i64 {
    var i i64 = 3;
    return arr[i] + arr[i + 1];  // 30 + 40 = 70
}
```

**208_array_funcptr.lang** - Array of function pointers (for composition):
```lang
func add(a i64, b i64) i64 { return a + b; }
func mul(a i64, b i64) i64 { return a * b; }

var ops [2]*u8 = [nil, nil];

func main() i64 {
    ops[0] = add;
    ops[1] = mul;

    var f0 fn(i64, i64) i64 = ops[0];
    var f1 fn(i64, i64) i64 = ops[1];

    return f0(2, 3) + f1(2, 3);  // 5 + 6 = 11
}
```

### Stretch Tests

**209_array_2d.lang** - 2D arrays:
```lang
func main() i64 {
    var matrix [2][3]i64;
    matrix[0][0] = 1;
    matrix[1][2] = 6;
    return matrix[0][0] + matrix[1][2];  // 7
}
```

**210_array_struct.lang** - Array in struct:
```lang
struct Point { x i64, y i64 }

func main() i64 {
    var points [2]Point;
    points[0].x = 10;
    points[1].y = 40;
    return points[0].x + points[1].y;  // 50
}
```

## Implementation Order

1. **AST accessors** - array_type_*, array_literal_* functions
2. **Parser: type** - `[N]T` syntax in parse_type()
3. **Parser: literal** - `[e1, e2, ...]` in parse_primary()
4. **AST emit** - Round-trip support for type_array, array_literal
5. **Sexpr reader** - Parse array types and literals from AST
6. **Codegen: index expr** - Implement NODE_INDEX_EXPR (currently "not implemented")
7. **Codegen: global arrays** - .data section with initializers
8. **Codegen: local arrays** - Stack allocation
9. **Bounds check** - Compile-time check for constant indices
10. **Bootstrap** - Verify self-hosting
11. **Tests** - All test cases

## Related

- `designs/fix_composition.md` - Blocked on array support for multi-reader
- `src/limits.lang` - LIMIT_EMBEDDED_READERS = 20
- `std/core.lang` - Vec implementation (runtime dynamic array)
