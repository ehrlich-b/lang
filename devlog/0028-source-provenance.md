# Errors point back to owned source

Parser errors used to say only `Error at line:column`, even when the compiler
was parsing a named include. Reader build failures were worse: the useful error
could mention only generated code under `.lang-cache/readers/`, and semantic
errors in a reader's emitted AST lost the input file entirely.

Nested parser state now carries a source name, producing conventional
`path:line:column: error:` diagnostics without leaking one include's name into
the next. Generated reader wrappers use their cache path for exact wrapper
syntax locations, while the parent diagnostic points back to the original
reader declaration and keeps the wrapper path as a debugging hint.

Top-level AST declarations also have a provenance side table. It deliberately
does not change the stable AST layout or S-expression format. Declarations
emitted by a reader inherit the reader invocation's input file, so kernel
semantic errors name user-owned source instead of an anonymous generated tree.
The current granularity is the invocation (`line 1, column 1` for a custom input
file); exact semantic spans inside a custom language remain an optional future
AST extension. Readers already have exact syntax locations through `std/tok`.

The failure matrix now guards all three boundaries: malformed included Lang,
bad code in a generated reader wrapper, and an undefined call emitted by a
custom reader.
