# Source Maps for Reader Macros

**Status**: Design draft. Low priority - opt-in feature for IDE support.

## Problem

IDE features (go-to-definition, hover, find-references) don't work inside reader macro blocks:

```lang
#lisp{ (add 1 2) }
        ^^^ cursor here - "go to definition" should find the `add` function
```

Broken because readers output text with no connection to input positions.

## Key Insight: PNode Already Has Position Info

The `#parser{}` macro generates PNode structs. When parsing `(add 1 2)`:

```lang
node.text = "add"  // ← pointer INTO the input buffer
node.kind = ATOM
```

The position info EXISTS - `node.text` points to the original input. We just don't preserve it through to output.

## Solution: PNode Stores Offsets

Add `.start` and `.len` to PNode:

```lang
struct PNode {
    kind i64;
    text *u8;
    start i64;   // offset from input start
    len i64;     // token length
    children *PNode;
    // ...
}
```

The `#parser{}` macro sets these when creating nodes:

```lang
node.text = t.token_text;
node.start = t.pos - t.start;  // offset from input
node.len = t.token_len;
```

Now position info travels WITH the node - no need to thread input pointers.

## Reader Changes

Readers that want source maps use a position-aware emit:

```lang
// Before (no source maps)
func lisp_emit(sb *StringBuilder, node *PNode) {
    if node.kind == ATOM {
        sb_str(sb, node.text);
    }
}

// After (with source maps)
func lisp_emit(ctx *ReaderContext, node *PNode) {
    if node.kind == ATOM {
        reader_emit(ctx, node.text, node.start, node.len);
    }
}
```

One function change per emit. Opt-in - readers that don't care keep using `sb_str`.

## Output Protocol

Readers output code + optional source map:

```
add(1, 2)
<<SOURCEMAP>>
0,3,1,3
4,1,5,1
6,1,7,1
```

Format: `output_start,output_len,input_start,input_len`

Readers that don't emit a source map just output code. The compiler handles both.

## Compiler Flags

Source map collection adds overhead. Disable in production:

```bash
# Development (source maps enabled)
lang --source-maps program.lang -o program

# Production (source maps disabled, faster)
lang program.lang -o program
```

When disabled:
- `reader_emit()` acts like `sb_str()` (no tracking)
- Compiler skips source map parsing from reader output
- No runtime overhead

## API

```lang
// std/reader.lang

struct ReaderContext {
    output *StringBuilder;
    map_enabled i64;      // 0 = disabled, 1 = enabled
    map *SourceMap;       // nil if disabled
}

func reader_new(input *u8) *ReaderContext;
func reader_emit(ctx *ReaderContext, text *u8, start i64, len i64);
func reader_emit_lit(ctx *ReaderContext, text *u8);  // literal, no mapping
func reader_finish(ctx *ReaderContext) *u8;          // prints code + map
```

## Implementation Phases

### Phase 1: PNode positions
- Modify `#parser{}` to generate `.start` and `.len` fields
- Tokenizer exposes offset computation

### Phase 2: Reader infrastructure
- Add `std/reader.lang` with ReaderContext
- Compiler flag `--source-maps`

### Phase 3: Update example readers
- Modify `example/lisp/lisp.lang` to demonstrate

### Phase 4: Compiler integration
- Parse source maps from reader output
- Attach to AST for error messages

### Phase 5: LSP (future)
- Use source maps for IDE features
- Go-to-definition, hover, etc.

## Syntax Highlighting (Separate Concern)

TextMate grammars work today without source maps:

```json
{
  "begin": "#lisp\\{",
  "end": "\\}",
  "patterns": [{ "include": "source.lisp" }]
}
```

Semantic highlighting (function vs variable coloring) needs source maps + LSP.

## Summary

| Aspect | Approach |
|--------|----------|
| Position storage | PNode.start, PNode.len |
| Reader output | Still text |
| Source maps | Opt-in via `reader_emit()` |
| Production | `--source-maps` flag to disable |
| Priority | Low - nice to have for IDE support |
