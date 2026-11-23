# Kaleidoscope reader friction

| Workaround | Reader and shared sources | Smallest shared change |
| --- | --- | --- |
| Scan token boundaries using the shared tokenizer cursor. Operators are single bytes, identifiers use ASCII alphanumerics, number runs use digits and periods, and comments end at CR or LF. | [lex.lang:10](lex.lang#L10), [std/tok.lang:60](../../std/tok.lang#L60), [std/tok.lang:362](../../std/tok.lang#L362), [std/tok.lang:425](../../std/tok.lang#L425) | Add profile controls for identifier spelling, operator width, numeric spelling and line-comment termination. |
| Preserve exact binary64 bits from `strtod` and emit cast and bitcast S-expressions. The shared textual literal route can change the spelling that identifies a floating operand. | [lex.lang:68](lex.lang#L68), [kaleidoscope.lang:13](kaleidoscope.lang#L13), [std/ast.lang:239](../../std/ast.lang#L239), [src/sexpr_reader.lang:1004](../../src/sexpr_reader.lang#L1004) | Supply cast and exact binary64 literal builders. |
| Include the lexer’s libc declarations so a minted reader preserves their extern signatures. | [libc.lang:1](libc.lang#L1), [lex.lang:4](lex.lang#L4), [src/stage_legacy.lang:151](../../src/stage_legacy.lang#L151), [src/codegen.lang:6808](../../src/codegen.lang#L6808) | Preserve the extern marker when serializing a sibling function declaration. |
| Encode operator punctuation and arity in native symbols. Use a mutable binding-power table and build an expression tree before resolving bindings. | [kaleidoscope.lang:15](kaleidoscope.lang#L15), [kaleidoscope.lang:174](kaleidoscope.lang#L174), [std/prec.lang:87](../../std/prec.lang#L87), [std/prec.lang:222](../../std/prec.lang#L222) | Expose a symbol encoder and a precedence parser with mutable binding powers and separately lowered results. |
| Reserve typed slots before control flow. Lower value-producing assignments, branches and post-test loops with statements and block expressions. | [kaleidoscope.lang:17](kaleidoscope.lang#L17), [kaleidoscope.lang:37](kaleidoscope.lang#L37), [kaleidoscope.lang:54](kaleidoscope.lang#L54), [std/ast.lang:727](../../std/ast.lang#L727), [src/codegen_llvm.lang:4790](../../src/codegen_llvm.lang#L4790), [src/codegen_llvm.lang:5073](../../src/codegen_llvm.lang#L5073) | Add value-producing assignment and conditional builders and a post-test loop builder. Allocate fixed-size locals in the entry block. |
| Take the complement of ordered greater-or-equal for unordered less-than and convert the boolean to double. | [kaleidoscope.lang:49](kaleidoscope.lang#L49), [src/codegen_llvm.lang:3062](../../src/codegen_llvm.lang#L3062), [src/numeric_llvm.lang:208](../../src/numeric_llvm.lang#L208) | Expose ordered and unordered comparison predicates in the exact numeric profile. |
| Route double-only externs through libffi using integer-class pointer arguments. Make top-level results addressable for the C printer using a typed slot. | [kaleidoscope.lang:97](kaleidoscope.lang#L97), [runtime.c:16](runtime.c#L16), [src/codegen_llvm.lang:6289](../../src/codegen_llvm.lang#L6289) | Honor declared floating argument types at native extern call sites and declarations. |
| Emit identity calls for constants and variable reads so unoptimized instruction selection carries their source rows. Give an assignment store the target’s span. Build the C runtime as a separate object without debug metadata to keep the linked debug sections on the guest DWARF version. | [kaleidoscope.lang:37](kaleidoscope.lang#L37), [kaleidoscope.lang:78](kaleidoscope.lang#L78), [src/codegen_llvm.lang:141](../../src/codegen_llvm.lang#L141), [check.py](../../test/kaleidoscope/check.py) | Offer a line marker or debug-capable intrinsic that survives unoptimized instruction selection, and let callers choose the guest DWARF version to match native objects. |
| Allocate the temporary syntax node by its declared field layout. | [kaleidoscope.lang:122](kaleidoscope.lang#L122), [src/codegen.lang:2595](../../src/codegen.lang#L2595) | Add a type-size expression for heap allocation. |

Counted by [count.py](../../test/kaleidoscope/count.py), excluding blank and
comment-only lines.

| Part | Lines |
| --- | ---: |
| Lexical profile | 66 |
| Grammar | 138 |
| Lowering | 114 |
| Runtime | 24 |
| Grammar, lowering and runtime | 276 |
| Reader total with lexical profile | 342 |
