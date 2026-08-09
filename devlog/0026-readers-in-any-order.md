# Readers in any order

A reader used to carry a hidden layout rule: every import, `#parser{}` grammar,
type, global, and helper it needed had to appear before the `reader` declaration.
The compiler regenerated a standalone reader executable from only those earlier
siblings. Moving a helper below the reader turned ordinary forward declaration
style into an unexplained reader compilation failure.

Reader wrappers now start from the reader body and compute a transitive closure
over named declarations in that source file. Imports and declaration generators
are emitted first, so a cold cache can build a later `#parser{}` grammar before
compiling the reader function. The current-file boundary and dependency closure
keep unrelated host functions out of the executable.

`test/suite/276_reader_declaration_order.lang` declares the reader first, then
its parser import, AST import, grammar, and lowering helper. It passes from an
empty reader cache and checks the result through the full compile/run path.
