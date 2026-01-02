# Array Support

## Status: Not Started

## Motivation

While implementing multi-reader composition (`-r` flag), we discovered that lang has no array support. The `TYPE_ARRAY` constant exists but is never used - `parse_type()` only handles pointers, functions, closures, and base types.

We need arrays to store N embedded readers in a self-aware kernel. Currently limited to a single reader slot.

## Syntax

### Array Types

```lang
var arr [20]i64;           // Array of 20 i64s
var ptrs [10]*u8;          // Array of 10 pointers
var nested [5][3]i64;      // 2D array (5 arrays of 3 i64s) - stretch goal
```

### Array Literals

```lang
var arr [3]i64 = [1, 2, 3];
var ptrs [2]*u8 = [nil, nil];
var partial [5]i64 = [1, 2];  // Rest zero-initialized? Or error?
```

### Array Access

Already works via `NODE_INDEX_EXPR`:
```lang
arr[0] = 42;
var x i64 = arr[i];
```

## AST Representation

### Type: TYPE_ARRAY (already defined = 3)

Layout: `[kind:8][size:8][elem:8]` = 24 bytes

```lang
// Accessors needed:
func array_type_alloc() *u8;
func array_type_size(t *u8) i64;
func array_type_set_size(t *u8, size i64) void;
func array_type_elem(t *u8) *u8;
func array_type_set_elem(t *u8, elem *u8) void;
```

### Expression: NODE_ARRAY_LITERAL (new)

Layout: `[kind:8][elems:8][elem_count:8][elem_type:8]` = 32 bytes

```lang
// elems is array of expression pointers
func array_literal_alloc() *u8;
func array_literal_elems(node *u8) *u8;
func array_literal_set_elems(node *u8, elems *u8) void;
func array_literal_count(node *u8) i64;
func array_literal_set_count(node *u8, count i64) void;
func array_literal_type(node *u8) *u8;  // Inferred element type
func array_literal_set_type(node *u8, t *u8) void;
```

### S-Expression Format

```lisp
; Array type
(type_array 20 (type_base i64))
(type_array 10 (type_ptr (type_base u8)))

; Array literal expression
(array_literal (number 1) (number 2) (number 3))

; Variable with array type and initializer
(var arr (type_array 3 (type_base i64)) (array_literal (number 1) (number 2) (number 3)))
```

## Implementation Plan

### 1. Parser (src/parser.lang)

**parse_type() changes:**
```lang
// Add before base type handling:
if parse_match(TOKEN_LBRACKET) {
    // Parse size
    var size_tok *u8 = parse_expect(TOKEN_NUMBER, "expected array size");
    var size i64 = parse_number(size_tok);
    parse_expect(TOKEN_RBRACKET, "expected ']' after array size");

    // Parse element type
    var elem *u8 = parse_type();

    var t *u8 = array_type_alloc();
    array_type_set_size(t, size);
    array_type_set_elem(t, elem);
    return t;
}
```

**parse_primary() changes for array literals:**
```lang
// Add case for TOKEN_LBRACKET:
if parse_match(TOKEN_LBRACKET) {
    var elems *u8 = vec_new(16);
    if !parse_check(TOKEN_RBRACKET) {
        vec_push(elems, parse_expression());
        while parse_match(TOKEN_COMMA) {
            vec_push(elems, parse_expression());
        }
    }
    parse_expect(TOKEN_RBRACKET, "expected ']' after array elements");

    var node *u8 = array_literal_alloc();
    array_literal_set_elems(node, elems);
    array_literal_set_count(node, vec_len(elems));
    return node;
}
```

### 2. AST Accessors (src/parser.lang)

Add after existing type accessors:

```lang
// ArrayType accessors
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
```

Add NODE_ARRAY_LITERAL constant and accessors:

```lang
var NODE_ARRAY_LITERAL i64 = 42;  // Next available

// ArrayLiteral: [kind:8][elems:8][count:8][type:8] = 32 bytes

func array_literal_alloc() *u8 {
    var node *u8 = alloc(32);
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

func array_literal_type(node *u8) *u8 {
    var p **u8 = node + 24;
    return *p;
}

func array_literal_set_type(node *u8, t *u8) void {
    var p **u8 = node + 24;
    *p = t;
}
```

### 3. AST Emit (src/ast_emit.lang)

**ast_emit_type() - add TYPE_ARRAY case:**
```lang
if kind == TYPE_ARRAY {
    ast_emit_str("(type_array ");
    ast_emit_int(array_type_size(t));
    ast_emit_str(" ");
    ast_emit_type(array_type_elem(t));
    ast_emit_str(")");
    return;
}
```

**ast_emit_node() - add NODE_ARRAY_LITERAL case:**
```lang
if kind == NODE_ARRAY_LITERAL {
    ast_emit_str("(array_literal");
    var elems *u8 = array_literal_elems(node);
    var count i64 = array_literal_count(node);
    var i i64 = 0;
    while i < count {
        ast_emit_str(" ");
        ast_emit_node(get_ptr_at(elems, i));
        i = i + 1;
    }
    ast_emit_str(")");
    return;
}
```

### 4. S-Expression Reader (src/sexpr_reader.lang)

**parse_sexpr_type() - add type_array case:**
```lang
if streq(head, "type_array") {
    // (type_array SIZE ELEM_TYPE)
    var size_sexpr *u8 = sexpr_get(sexpr, 1);
    var size i64 = sexpr_to_int(size_sexpr);
    var elem_sexpr *u8 = sexpr_get(sexpr, 2);
    var elem *u8 = parse_sexpr_type(elem_sexpr);

    var t *u8 = array_type_alloc();
    array_type_set_size(t, size);
    array_type_set_elem(t, elem);
    return t;
}
```

**parse_sexpr_expr() - add array_literal case:**
```lang
if streq(head, "array_literal") {
    var node *u8 = array_literal_alloc();
    var elems *u8 = vec_new(16);
    var i i64 = 1;
    while i < sexpr_len(sexpr) {
        var elem_sexpr *u8 = sexpr_get(sexpr, i);
        var elem *u8 = parse_sexpr_expr(elem_sexpr);
        vec_push(elems, elem);
        i = i + 1;
    }
    array_literal_set_elems(node, vec_to_array(elems));
    array_literal_set_count(node, vec_len(elems));
    return node;
}
```

### 5. Codegen x86 (src/codegen.lang)

**Type size calculation:**
```lang
func type_size(t *u8) i64 {
    var kind i64 = type_kind(t);
    // ... existing cases ...
    if kind == TYPE_ARRAY {
        var elem_size i64 = type_size(array_type_elem(t));
        return array_type_size(t) * elem_size;
    }
    // ...
}
```

**Global variable with array type:**
- Emit `.zero N*elem_size` for uninitialized
- Emit `.quad val1, val2, ...` for initialized array literal

**Local variable with array type:**
- Allocate N*elem_size bytes on stack
- Initialize elements if literal provided

**Array literal expression:**
- For globals: emit in .data section
- For locals: store each element

### 6. Codegen LLVM (src/codegen_llvm.lang)

**LLVM array type:**
```llvm
[N x T]           ; e.g., [20 x i64], [10 x i8*]
```

**Global array:**
```llvm
@arr = global [3 x i64] [i64 1, i64 2, i64 3]
@arr_zero = global [20 x i64] zeroinitializer
```

**Local array:**
```llvm
%arr = alloca [3 x i64]
; Initialize elements via getelementptr + store
```

**Array literal:**
```llvm
; Constant array
[3 x i64] [i64 1, i64 2, i64 3]
```

**Array access (already works via index, but verify):**
```llvm
%ptr = getelementptr [N x T], [N x T]* %arr, i64 0, i64 %index
%val = load T, T* %ptr
```

## Test Cases

### Basic Tests (test/suite/)

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
func main() i64 {
    var arr [3]i64 = [100, 200, 300];
    return arr[1];  // 200
}
```

**202_array_pointer.lang** - Array of pointers:
```lang
var global_arr [2]*u8 = [nil, nil];

func main() i64 {
    var s1 *u8 = "hello";
    var s2 *u8 = "world";
    global_arr[0] = s1;
    global_arr[1] = s2;
    if *global_arr[0] == 'h' {
        return 1;  // Success
    }
    return 0;
}
```

**203_array_loop.lang** - Iteration:
```lang
func main() i64 {
    var arr [5]i64 = [1, 2, 3, 4, 5];
    var sum i64 = 0;
    var i i64 = 0;
    while i < 5 {
        sum = sum + arr[i];
        i = i + 1;
    }
    return sum;  // 15
}
```

**204_array_param.lang** - Array as parameter (pointer decay):
```lang
func sum_array(arr *i64, len i64) i64 {
    var sum i64 = 0;
    var i i64 = 0;
    while i < len {
        sum = sum + *(arr + i * 8);
        i = i + 1;
    }
    return sum;
}

func main() i64 {
    var arr [3]i64 = [10, 20, 30];
    // Array decays to pointer when passed
    return sum_array(&arr[0], 3);  // 60
}
```

**205_array_global.lang** - Global arrays:
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

**206_array_struct.lang** - Array in struct (stretch):
```lang
struct Point {
    x i64,
    y i64
}

func main() i64 {
    var points [2]Point;
    points[0].x = 10;
    points[0].y = 20;
    points[1].x = 30;
    points[1].y = 40;
    return points[0].x + points[1].y;  // 50
}
```

**207_array_2d.lang** - 2D arrays (stretch):
```lang
func main() i64 {
    var matrix [2][3]i64;
    matrix[0][0] = 1;
    matrix[0][1] = 2;
    matrix[0][2] = 3;
    matrix[1][0] = 4;
    matrix[1][1] = 5;
    matrix[1][2] = 6;
    return matrix[1][2];  // 6
}
```

## Edge Cases

1. **Zero-size arrays** - Error or allow `[0]T`?
2. **Empty literal** - `[]` - infer type from context?
3. **Mismatched sizes** - `var arr [3]i64 = [1, 2]` - error or zero-fill?
4. **Array bounds** - No runtime checks (C-style)
5. **Array assignment** - `arr1 = arr2` - copy or error?
6. **Array comparison** - `arr1 == arr2` - pointer comparison or element-wise?

## Implementation Order

1. **Parser**: Array type syntax `[N]T`
2. **Parser**: Array literal syntax `[e1, e2, ...]`
3. **AST accessors**: TYPE_ARRAY and NODE_ARRAY_LITERAL
4. **AST emit**: Round-trip support
5. **Sexpr reader**: Parse array types and literals
6. **Codegen x86**: Basic array support
7. **Codegen LLVM**: Basic array support
8. **Bootstrap**: Verify self-hosting
9. **Tests**: All test cases

## Open Questions

1. Should arrays decay to pointers automatically (C-style)?
2. Should we support array slices later?
3. Syntax: `[N]T` vs `[T; N]` (Rust-style)?
4. Should array size be required to be constant?

## Related

- `designs/fix_composition.md` - Blocked on array support for multi-reader
- `src/limits.lang` - LIMIT_EMBEDDED_READERS = 20
