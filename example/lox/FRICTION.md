# Lox reader friction

| Reader workaround | Toolkit or core boundary | Smallest removal |
| --- | --- | --- |
| [lexical adapter](lox.lang#L15) resegments unsigned decimal fractions and separates `-` from a following number | [Profile modes](../../std/tok.lang#L56) offer signed integer tokens or unsigned integers with fraction rejection | Add an unsigned decimal-fraction token mode. |
| [lexical adapter](lox.lang#L24) scans raw double-quoted strings and rejects single quotes | [String scanner](../../std/tok.lang#L637) treats backslashes as escapes and recognizes both delimiters | Add configurable delimiters and a raw-string flag. |
| [lexical adapter](lox.lang#L36) splits operators and marks reserved words as non-identifiers | [Operator scanner](../../std/tok.lang#L493) folds Lang operators and the [symbol matcher](../../std/rdgen.lang#L245) accepts every identifier | Let profiles specify operator pairs and reserve identifier spellings. |
| [syntax diagnostics](lower.lang#L39) infer context from the expectation set and preceding tokens | [Expectation tracking](../../std/tok.lang#L759) retains spellings at the furthest failure without rule-specific diagnostic labels | Let grammar captures label their terminal expectations. |
| [semantic diagnostics](lower.lang#L20) and [runtime errors](runtime.lang#L22) use the syntax-snippet code. The [runtime entry](lower.lang#L411) embeds the source and takes its path from the runner's argument | [Diagnostic rendering](../../std/reader_diagnostics.lang#L119) selects snippets by code, and the emitted [origin wrapper](../../std/ast.lang#L63) stops at compile-time metadata | Expose snippet rendering independently of diagnostic code and a runtime source-map lookup for embedded spans. |
| [runner](run.sh#L13) reads the structured budget error on a second compile, renders a caret, and maps guest failures to 65 | [Parser budget reporting](../../std/tok.lang#L949) exits through the host. [Standalone compilation](../../src/standalone.lang#L128) uses status 1 for guest errors and prints budget failures without a source excerpt | Route located phase errors through the snippet renderer, with a configurable guest failure exit code. |
| [numeric literals](lower.lang#L125) carry decimal text to `strtod`. [Numeric negation](runtime.lang#L48) flips the sign bit, and [clock](runtime.lang#L255) requests exact integer-to-float conversion | [S-expression numeric atoms](../../src/sexpr_reader.lang#L95) use the integer scanner. [Legacy LLVM negation](../../src/codegen_llvm.lang#L3581) uses `sub i64`, and [legacy local initialization](../../src/codegen_llvm.lang#L5214) expects a typed float value | Support float atoms in AST transport and typed `fneg` in the legacy path. An explicit conversion is required at the clock ABI boundary. |
| [numeric printing](runtime.lang#L268) uses `printf("%g")` plus `fflush` to preserve clox spelling and ordering with the unbuffered standard writes | [Standard float output](../../std/core.lang#L611) uses `%f`. [LLVM variadic lowering](../../src/codegen_llvm.lang#L2729) specializes `printf` | Supply a standard unbuffered shortest-format float writer. |
| [logical lowering](lower.lang#L202) uses a temporary and conditional assignment for operand-valued short circuiting | [Core logic](../../src/codegen_llvm.lang#L1493) returns a boolean | Add a lazy value-select expression to the AST builders and core. |

Non-blank, non-comment Lang lines by part. Includes and grammar delimiters are
excluded from the lexical profile and grammar, respectively. The reader entry
belongs to lowering.

- Lexical profile: 48
- Grammar: 47
- Lowering: 417
- Runtime: 267
