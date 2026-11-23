# The LLVM Kaleidoscope tutorial in Lang

The [Kaleidoscope reader](../example/kaleidoscope/README.md) targets the
Chapter 7 language and uses shared native source spans for the Chapter 9
line-table goal.

| LLVM tutorial chapter | Reader implementation |
| --- | --- |
| 1. Language and lexer | [Token boundaries and comments](../example/kaleidoscope/lex.lang#L10), [binary64 constants](../example/kaleidoscope/kaleidoscope.lang#L14) |
| 2. Parser and AST | [Primary expressions and calls](../example/kaleidoscope/kaleidoscope.lang#L141), [precedence climbing](../example/kaleidoscope/kaleidoscope.lang#L174), [prototypes](../example/kaleidoscope/kaleidoscope.lang#L196) |
| 3. LLVM IR generation | [Binary operations](../example/kaleidoscope/kaleidoscope.lang#L37), [function AST and foreign calls](../example/kaleidoscope/kaleidoscope.lang#L97), [shared LLVM backend](../src/codegen_llvm.lang) |
| 4. JIT and optimization | [Source-ordered top-level execution](../example/kaleidoscope/kaleidoscope.lang#L226), [Clang optimization and reference comparison](../test/kaleidoscope/check.py#L111) |
| 5. Control flow | [If expressions](../example/kaleidoscope/kaleidoscope.lang#L84) and [post-test loops](../example/kaleidoscope/kaleidoscope.lang#L54) |
| 6. User-defined operators | [Unary applications](../example/kaleidoscope/kaleidoscope.lang#L161), [binary applications](../example/kaleidoscope/kaleidoscope.lang#L37), [precedence registration](../example/kaleidoscope/kaleidoscope.lang#L224) and [Mandelbrot differential case](../test/kaleidoscope/check.py#L42) |
| 7. Mutable variables | [Variable scopes](../example/kaleidoscope/kaleidoscope.lang#L64), [assignment returning its value](../example/kaleidoscope/kaleidoscope.lang#L37), [mutable and uniqued arguments](../example/kaleidoscope/kaleidoscope.lang#L97) |
| 8. Object code | [Building a linked native binary](../example/kaleidoscope/README.md#build-and-run) |
| 9. Debug information | [Expression spans](../example/kaleidoscope/kaleidoscope.lang#L77), [declaration spans](../example/kaleidoscope/kaleidoscope.lang#L223), [shared LLVM debug emission](../src/codegen_llvm.lang#L141), [linked DWARF checks](../test/kaleidoscope/check.py#L128) |
| 10. Conclusion | [End-to-end build and verification](../example/kaleidoscope/README.md) |

The same [count script](../test/kaleidoscope/count.py) strips comments and
counts nonblank physical lines on both sides. The tutorial's original C++
file has 1,294 physical lines.

| Source | Counted lines |
| --- | ---: |
| Reader lexical profile | 66 |
| Reader grammar | 138 |
| Reader lowering | 114 |
| Reader runtime | 24 |
| Reader grammar, lowering and runtime | 276 |
| Reader total with lexical profile | 342 |
| LLVM 19.1.7 Chapter 7 `toy.cpp` | 828 |

Grammar, lowering and runtime together are exactly one third of the tutorial
implementation by this measure. The lexical profile is shown separately
because it adapts the shared tokenizer to Kaleidoscope's spelling. The
[friction notes](../example/kaleidoscope/FRICTION.md) list the reader-local
adapters and shared interfaces they exercise.
