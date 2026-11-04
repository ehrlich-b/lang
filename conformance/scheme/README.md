# Scheme conformance work in progress

`inventory.py` counts syntactic three-element `(test expected expr)` lists in
an input file. It skips comments and quoted data, but is not a Scheme reader or
conformance score: it does not execute tests, resolve their environments, or
handle all datum syntax. The pinned Chibi suite contains tests inside enclosing
bindings and definitions, so evaluating isolated expressions would lose required
context. A scorer must preserve that context and compare actual runtime values.

The shared AST has ordinary calls but no documented guarantee of proper tail
calls. Scheme needs constant-space tail calls across indirect and mutual calls;
reader-generated trampolines or a general core operation could supply this.
`call/cc` additionally needs continuation lifetime and re-entry semantics, not
just an ordinary call. No Scheme reader or located refusal is implemented here.
