# Shape Types: Structural Typing for Multi-Language Compilation

> "If the shape fits, it works."

## The Goal

Compile any language (Zig, Scheme, TypeScript, whatever) through lang's infrastructure.

```
Zig source    ──→ Zig Reader    ──→ ┐
Lang source   ──→ Lang Reader   ──→ ├──→ Kernel ──→ Binary
Scheme source ──→ Scheme Reader ──→ ┘
```

Each reader is a full frontend. The kernel verifies and compiles.

---

## The Core Idea: Types Are Shapes

A shape is a memory layout:

```
Shape = (size, alignment, structure)

Primitives:
  i64 = (size: 8, align: 8, primitive: signed-int)
  f64 = (size: 8, align: 8, primitive: float)
  *T  = (size: 8, align: 8, primitive: pointer)

Composites:
  struct Point { x i64; y i64; }
  = (size: 16, align: 8, product: [
      (name: "x", shape: i64, offset: 0),
      (name: "y", shape: i64, offset: 8)
    ])
```

**Type equality = shape equality.** Names don't matter at the kernel level.

```lang
struct Point { x i64; y i64; }
struct Vec2 { x i64; y i64; }
// Same shape → same type (at kernel level)
```

---

## Architecture

### Current

```
Source ──→ Reader ──→ AST ──→ Kernel ──→ Binary
                              ↑
                        Type checks
                        Infers types
                        Resolves names
```

The kernel is smart. It understands lang's type system.

### Proposed

```
Source ──→ Reader ──→ Lowered AST ──→ Kernel ──→ Binary
              ↑                          ↑
        Full frontend              Skeptical backend
        - Parse                    - Verifies AST
        - Type check               - Then codegen
        - Lower to shapes          - No type CHECKING
                                   - But does VERIFY
```

The kernel is skeptical. It doesn't type-check (language-specific), but it verifies (universal).

---

## The Lowered AST

### High-Level (Current)

```scheme
(func add (params (a i64) (b i64)) (ret i64)
  (body
    (return (+ a b))))
```

The kernel must figure out:
- What does `+` mean? (i64 add? f64 add?)
- What are the sizes of a, b?
- How to call this function?

### Lowered (Proposed)

```scheme
(func add
  (params
    (a (shape i64 8 8))
    (b (shape i64 8 8)))
  (ret (shape i64 8 8))
  (body
    (return
      (add-i64
        (load (shape i64 8 8) (local-ref a))
        (load (shape i64 8 8) (local-ref b))))))
```

Everything is explicit:
- Shapes on all declarations
- Explicit operations (`add-i64` not `+`)
- Explicit loads

The kernel just translates to assembly. No thinking required.

### Shape Representation

```scheme
;; Primitives
(shape i8 1 1)
(shape i64 8 8)
(shape f64 8 8)
(shape ptr 8 8)  ;; All pointers are the same shape

;; Struct
(shape struct 16 8
  (field x (shape i64 8 8) 0)
  (field y (shape i64 8 8) 8))

;; Array
(shape array 80 8
  (element (shape i64 8 8))
  (count 10))

;; Function (for function pointers)
(shape func 8 8
  (params (shape i64 8 8) (shape i64 8 8))
  (ret (shape i64 8 8)))
```

---

## Verification vs Type Checking

Readers can be buggy. We can't blindly trust them. But the kernel also shouldn't impose a language-specific type system.

**Solution**: The kernel VERIFIES but doesn't TYPE CHECK.

| Type Checking (Reader's Job) | Verification (Kernel's Job) |
|------------------------------|----------------------------|
| "Is this valid Zig code?" | "Is this AST internally consistent?" |
| Language-specific rules | Universal rules |
| Inference, generics, compatibility | Shape matching on operations |
| Nominal vs structural decisions | Just: do the pieces fit? |

### What the Verifier Checks

```scheme
;; Buggy reader emits this:
(add-i64
  (load (shape f64 8 8) (local-ref x))   ;; f64, not i64!
  (load (shape i64 8 8) (local-ref y)))

;; Verifier: ERROR - add-i64 requires (shape i64 8 8) operands
;;           got (shape f64 8 8) and (shape i64 8 8)
```

The verifier is mechanical and simple:

1. **Operation shapes**: `add-i64` requires i64 operands
2. **Load/store consistency**: Load shape matches target shape
3. **Reference validity**: All `local-ref`, `func-ref` exist and have shapes
4. **Call shapes**: Argument shapes match parameter shapes
5. **Return shapes**: Returned value shape matches declared return shape
6. **Control flow**: Returns in all paths, breaks inside loops

### What the Verifier Does NOT Check

- Type inference (shapes are explicit)
- Type compatibility rules (exact match only)
- Generics/templates (already monomorphized)
- Language-specific semantics (reader's problem)

### Defense in Depth

```
Reader: "Here's my lowered AST"
           ↓
Verifier: "Checking internal consistency..."
          - add-i64 has i64 operands? ✓
          - All references exist? ✓
          - Call shapes match? ✓
          - Return shapes match? ✓
           ↓
Codegen: "Generating code"
```

If verification fails:
```
Verification failed:
  add-i64 at line 42 requires operands of shape (i64 8 8)
  operand 1: got (f64 8 8)
  operand 2: got (i64 8 8)
```

Clear error pointing at the reader's bug. Not a runtime crash.

### Verification is Simple

The verifier is ~500 lines, not ~5000:

```lang
func verify_add_i64(node *Node) bool {
    var left *Node = node_child(node, 0);
    var right *Node = node_child(node, 1);
    return shape_eq(node_shape(left), SHAPE_I64) &&
           shape_eq(node_shape(right), SHAPE_I64);
}

func verify_node(node *Node) bool {
    match node_kind(node) {
        OP_ADD_I64 => verify_add_i64(node),
        OP_LOAD    => verify_load(node),
        OP_STORE   => verify_store(node),
        OP_CALL    => verify_call(node),
        // ... one case per operation
    }
}
```

No inference. No unification. Just pattern matching on explicit shapes.

---

## What Changes

### 1. AST Format

| Current | Lowered |
|---------|---------|
| `(+ a b)` | `(add-i64 a b)` or `(add-f64 a b)` |
| `(var x i64 ...)` | `(local x (shape i64 8 8) ...)` |
| `(field p x)` | `(load (shape i64 8 8) (ptr-add p 0))` |
| `(call f x)` | `(call f (shape ...) x)` |

Operations become explicit. Types become shapes.

### 2. Kernel (codegen.lang)

Remove:
- Type inference
- Type compatibility rules
- Name resolution for types
- Language-specific type checking

Add:
- Shape verification (universal, mechanical)

Keep:
- Shape → size/offset calculations (trivial, just read the shape)
- Codegen for each operation
- Register allocation
- Calling conventions

The kernel changes shape: less type logic, more verification. Net simpler because verification is mechanical.

### 3. Readers

Each reader must:
1. **Parse** its syntax
2. **Type check** (using its own type system)
3. **Lower** to shaped AST

A Zig reader handles Zig's type system (nominal, comptime, anytype).
A Lang reader handles lang's type system.
A Lisp reader might have no type checking (everything is boxed).

### 4. Explicit Operations

The lowered AST needs explicit operations:

```
Arithmetic:     add-i64, sub-i64, mul-i64, div-i64, mod-i64
                add-f64, sub-f64, mul-f64, div-f64
Comparison:     lt-i64, le-i64, eq-i64, gt-i64, ge-i64
                lt-f64, le-f64, eq-f64, gt-f64, ge-f64
Bitwise:        and-i64, or-i64, xor-i64, shl-i64, shr-i64
Memory:         load, store, ptr-add, alloc
Control:        if, loop, break, continue, return
Calls:          call, call-indirect
Casts:          trunc, extend, int-to-float, float-to-int, bitcast
```

---

## Cross-Language Interop

### The Problem

```zig
// file1.zig
pub fn helper(x: i64) i64 { return x + 1; }
```

```lang
// file2.lang
func main() i64 {
    return helper(41);  // How does lang reader know about helper?
}
```

### Solution: Extern Declarations

```lang
// file2.lang
extern helper(x i64) i64;  // Declare shape, trust it exists

func main() i64 {
    return helper(41);  // Reader can type-check against declaration
}
```

Reader emits:
```scheme
(extern helper (shape func 8 8 (params (shape i64 8 8)) (ret (shape i64 8 8))))

(func main ...)
```

### Solution: Interface Files

Better: auto-generate interfaces.

Zig reader produces:
```scheme
;; file1.iface (auto-generated)
(export helper (shape func 8 8 (params (shape i64 8 8)) (ret (shape i64 8 8))))
```

Lang reader consumes:
```lang
include "file1.iface"  // Now knows helper's shape

func main() i64 {
    return helper(41);
}
```

### Link-Time Verification

The kernel (or linker) verifies:
1. Every extern has a matching definition
2. Shapes match

```scheme
;; From Zig reader
(func helper (params (x (shape i64 8 8))) (ret (shape i64 8 8)) ...)

;; From Lang reader
(extern helper (shape func 8 8 (params (shape i64 8 8)) (ret (shape i64 8 8))))

;; Shapes match ✓
```

Shape mismatch → link error.

---

## Build Process

### Single Language (Current)

```
source.lang ──→ lang_reader ──→ AST ──→ kernel ──→ binary
```

### Multi-Language

```
file1.zig   ──→ zig_reader  ──→ file1.ast + file1.iface
file2.lang  ──→ lang_reader ──→ file2.ast          (uses file1.iface)
file3.scm   ──→ scm_reader  ──→ file3.ast          (uses file1.iface)
                                    ↓
                    kernel (link all .ast) ──→ binary
```

Or with lazy resolution:
```
all sources ──→ all readers (parallel) ──→ all .ast
                                              ↓
                              kernel (resolve + link) ──→ binary
```

Readers emit `(call-unresolved "helper" ...)` for unknown functions.
Kernel resolves at link time.

---

## Structural Subtyping

If shapes are types, we get structural subtyping:

```lang
struct Point2D { x i64; y i64; }
struct Point3D { x i64; y i64; z i64; }

func magnitude2d(p { x i64; y i64; }) f64 { ... }

var p3 Point3D = ...;
magnitude2d(p3);  // OK! Point3D has the required fields
```

The function wants shape `{ x: i64@0, y: i64@8 }`.
Point3D has that as a prefix. Match.

### The `distinct` Escape Hatch

If you want nominal typing:

```lang
type UserId = distinct i64;
type PostId = distinct i64;

func get_user(id UserId) *User { ... }

var pid PostId = 123;
get_user(pid);  // ERROR: distinct types, even though same shape
```

Readers handle `distinct` during type checking. By the time it reaches the kernel, they're both just `(shape i64 8 8)`.

---

## Generics = Shape Variables

```lang
func swap[T](a *T, b *T) void {
    var tmp T = *a;
    *a = *b;
    *b = tmp;
}
```

At call site:
```lang
var x i64 = 1;
var y i64 = 2;
swap(&x, &y);
```

Reader:
1. Infers T = i64 (from argument shapes)
2. Substitutes T → i64 in the function body
3. Emits monomorphized version with concrete shapes

No generics in the kernel. Just shape substitution in readers.

---

## What This Enables

### Compile Any Language

Each language gets its own reader (full frontend):
- Parse syntax
- Apply its type system
- Lower to shapes

The kernel doesn't care what language it came from.

### Cross-Language Calls

```zig
// math.zig
pub fn fast_sqrt(x: f64) f64 { ... }
```

```lang
// main.lang
extern fast_sqrt(x f64) f64;

func main() i64 {
    var result f64 = fast_sqrt(2.0);
    ...
}
```

```scheme
;; scheme_stuff.scm
(define (use-sqrt x)
  (fast_sqrt (exact->inexact x)))
```

All calling the same Zig function. All just need matching shapes.

### Duck-Typed Interop

```lang
// I don't care what language defined it
// I just need something with this shape
extern process_point(p { x i64; y i64; }) void;
```

Any language can provide `process_point` as long as the shape matches.

---

## Migration Path

### Phase 1: Define Lowered AST

Document the lowered AST format:
- All operations (add-i64, load, store, etc.)
- Shape representation
- Extern declarations

### Phase 2: Build Verifier

Write the verifier (~500 lines):
- Check each operation has correct operand shapes
- Check all references exist
- Check call/return shapes match

This can be tested independently.

### Phase 3: Update Kernel

Modify codegen.lang to:
- Accept lowered AST
- Run verifier before codegen
- Remove language-specific type checking
- Keep codegen logic

Keep old path working during transition.

### Phase 4: Update Lang Reader

Modify lang reader to:
- Do full type checking
- Emit lowered AST with explicit shapes

### Phase 5: Test Cross-Language

Write a simple "other language" reader (maybe Scheme).
Verify cross-language calls work.

### Phase 6: Interface Files

Add auto-generation of .iface files.
Add include support for interfaces.

---

## Summary

| Concept | Current | Proposed |
|---------|---------|----------|
| Type identity | Name | Shape |
| Type checking | Kernel | Reader |
| Verification | (part of type checking) | Kernel (universal, simple) |
| AST format | High-level | Lowered (explicit ops) |
| Generics | Not supported | Shape substitution |
| Cross-language | Not supported | Shape matching |
| Kernel complexity | High (type system) | Low (verifier only) |
| Reader complexity | Low (parser only) | High (full frontend) |

**The insight**: Move type checking from kernel to readers. Keep verification in kernel.

**The split**:
- **Readers**: Language-specific type checking (Zig rules, Lang rules, etc.)
- **Kernel**: Universal verification (do shapes match operations?)

**The mechanism**: Shapes. Types are shapes. Readers type-check and lower to shapes. Kernel verifies shapes and generates code.

---

*"The kernel doesn't need to understand your language. It just needs to verify the shapes."*
