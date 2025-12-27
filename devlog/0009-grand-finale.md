# 0009: The Grand Finale - Compiler Compiler Complete

**Date**: 2025-12-26

## What We Did

The vision is realized. We now have readers building readers, all compiling to native x86.

### Reader Includes Fixed

The blocker from 0008 is solved. Readers can now include helper files:
- Sibling declarations (includes, structs, functions) before the reader are serialized into the wrapper
- Declaration-level `#reader{}` expressions are expanded and included
- This enables the full tower: `#lisp{}` → `#parser{}` → native code

### Parser Generator (`#parser{}`)

Built a complete parser generator as a reader macro:

```lang
#parser{
    sexp = number | symbol | operator | list
    list = '(' sexp* ')'
}
// Generates: parse_sexp(), parse_list(), struct PNode, etc.
```

Components:
- **std/grammar.lang** - Parses grammar specs into Grammar AST
- **std/rdgen.lang** - Generates recursive descent parser code
- **std/parser_reader.lang** - The `#parser{}` reader macro

Built-in token types: `number`, `symbol`, `string`, `operator`

### The Lisp Reader

The grand finale: `example/lisp/lisp.lang`

```lang
include "std/parser_reader.lang"

#parser{
    sexp = number | symbol | operator | list
    list = '(' sexp* ')'
}

reader lisp(text *u8) *u8 {
    var t *Tokenizer = tok_new(text);
    var node *PNode = parse_sexp(t);
    return lisp_to_lang(node);
}
```

Usage:
```lang
var answer i64 = #lisp{ (* (+ 3 3) (+ 3 4)) };  // = 42
```

All computed at compile time. Zero runtime overhead.

### The Tower

```
#lisp{ (* (+ 3 3) (+ 3 4)) }
         │
         ▼
lisp reader (native executable)
         │
         ├── Uses #parser{} to build parse_sexp()
         │         │
         │         └── parser reader (native executable)
         │                   │
         │                   └── Generates parser code from grammar
         │
         └── Walks AST, outputs: "((3 + 3) * (3 + 4))"
                   │
                   ▼
         Compiler parses as lang expression
                   │
                   ▼
         mov $42, %rax
```

## Fixes Along the Way

- Increased `ast_str` buffer from 1KB to 64KB (was silently truncating)
- Added `operator` token type to grammar (for +, -, *, /)
- Fixed reader helper file includes in test suite
- All 81 tests passing

## Files Added/Changed

| File | Purpose |
|------|---------|
| `std/grammar.lang` | Grammar parser |
| `std/rdgen.lang` | Recursive descent code generator |
| `std/parser_reader.lang` | `#parser{}` reader |
| `std/sexpr_reader.lang` | `#sexpr{}` reader |
| `example/lisp/lisp.lang` | The grand finale `#lisp{}` |
| `test/parser_*.lang` | Parser tests |
| `test/sexpr_reader_test.lang` | Sexpr reader test |

## What This Means

The "compiler compiler" vision works:
1. Define a grammar
2. `#parser{}` generates a native parser
3. Use that parser in your reader
4. Your reader compiles to native x86
5. Users can embed your syntax with `#yoursyntax{...}`

No runtime, no VM, no interpreter. Just x86.

## What's Next

- File extension dispatch: `lang reader.lang main.lisp`
- More sophisticated grammars (precedence, left-recursion)
- The ultimate goal: `lang_reader.lang` - lang's syntax defined in lang itself
