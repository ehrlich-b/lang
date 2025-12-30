# Reader AST Interchange

## The Problem

Currently there are TWO reader systems that use DIFFERENT interchange formats:

### 1. Standalone Compilation (kernel/reader split)
```
lang source → lang_reader → S-expr AST text → kernel → x86
```
The lang reader outputs S-expr AST:
```lisp
(program
  (func main () (type_base i64)
    (block (return (number 42)))))
```

### 2. Inline Reader Macros (#name{...})
```
reader output → parse_expression_from_string() → AST nodes → codegen
```
Inline readers output LANG TEXT:
```lang
(1 + 2)
```
Which gets re-parsed as lang syntax.

## Why This Is Wrong

1. **Readers tied to lang syntax**: A lisp reader can't emit `(+ 1 2)` - it must emit `(1 + 2)`. The reader is forced to know lang syntax.

2. **No AST-level interop**: Readers can't emit AST constructs that don't exist in lang syntax (macros, etc).

3. **Two code paths**: Standalone readers use `parse_ast_from_string()`, inline readers use `parse_expression_from_string()`. Unnecessary complexity.

4. **The paradigm is broken**: The whole point is "reader outputs AST, codegen consumes AST". Having readers output lang text defeats this.

## The Solution

Change inline readers to also use S-expr AST interchange.

### Current Flow (codegen.lang)
```lang
// Expression-level reader
var output *u8 = exec_capture(exe_path, content, ...);
var expanded *u8 = parse_expression_from_string(output);  // parses as LANG
gen_expr(expanded);

// Declaration-level reader
var output *u8 = exec_capture(exe_path, content, ...);
var prog *u8 = parse_program_from_string(output);  // parses as LANG
```

### Fixed Flow
```lang
// Expression-level reader
var output *u8 = exec_capture(exe_path, content, ...);
var expanded *u8 = parse_ast_expression_from_string(output);  // parses as S-expr AST
gen_expr(expanded);

// Declaration-level reader
var output *u8 = exec_capture(exe_path, content, ...);
var prog *u8 = parse_ast_from_string(output);  // parses as S-expr AST
```

## What Already Exists

The infrastructure is already there in `src/sexpr_reader.lang`:

```lang
// Converts S-expr text → internal AST node
func sexpr_to_node(node *PNode) *u8

// Converts S-expr text → program (multiple declarations)
func parse_ast_from_string(source *u8) *u8
```

Missing: a function to parse a single expression (not wrapped in `(program ...)`):
```lang
// NEW: needed for expression-level readers
func parse_ast_expression_from_string(source *u8) *u8
```

## What Readers Need

For readers to emit S-expr AST, they need AST constructors. Two options:

### Option A: String-based (simple, current approach)
Reader builds AST text directly:
```lang
reader minilisp(text *u8) *u8 {
    // ... parse ...
    sb_str(sb, "(binop + ");
    sb_str(sb, "(number 1) ");
    sb_str(sb, "(number 2))");
    return sb_finish(sb);
}
```

### Option B: AST constructors + emit (future)
Reader builds AST nodes, then emits:
```lang
reader minilisp(text *u8) *u8 {
    var left *u8 = number_expr(1);
    var right *u8 = number_expr(2);
    var expr *u8 = binary_expr(TOKEN_PLUS, left, right);
    return ast_emit_expr(expr);  // NEW: emit single expression
}
```

Option A works today. Option B requires exposing AST constructors in a clean API.

## Implementation Plan

### Phase 1: Minimal Fix
1. Add `parse_ast_expression_from_string()` to sexpr_reader.lang
2. Change codegen.lang to use it for inline readers
3. Update minilisp.lang to emit S-expr AST

### Phase 2: Clean API (optional)
1. Create `std/ast.lang` with clean AST constructor API
2. Add `ast_emit_expr()` for single expression emission
3. Document the reader protocol

## Breaking Change

This is a BREAKING CHANGE for existing readers. They must switch from emitting lang text to emitting S-expr AST.

Affected:
- `std/sexpr_reader.lang` - already uses string-based approach
- `example/minilisp/minilisp.lang` - needs update

## Example: minilisp Before/After

### Before (emits lang text)
```lang
// (+ 1 2) → "(1 + 2)"
func emit(sb *StringBuilder, node *PNode) void {
    // ...
    sb_str(sb, "(");
    emit(sb, left);
    sb_str(sb, " + ");
    emit(sb, right);
    sb_str(sb, ")");
}
```

### After (emits S-expr AST)
```lang
// (+ 1 2) → "(binop + (number 1) (number 2))"
func emit(sb *StringBuilder, node *PNode) void {
    // ...
    sb_str(sb, "(binop + ");
    emit(sb, left);
    sb_str(sb, " ");
    emit(sb, right);
    sb_str(sb, ")");
}
```

## Compatibility Mode?

Could detect format by checking if output starts with `(`:
- Starts with `(` + known AST head (binop, call, number, etc): treat as S-expr AST
- Otherwise: treat as lang text (legacy)

But this adds complexity. Better to just break and fix.
