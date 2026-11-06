The supplied runtime file defines the artifact's explicit export root set with
`pub func`. Visibility on functions in transitively included modules serves
module lookup and does not export those functions from the artifact. To export
an imported helper, add a public wrapper to a supplied runtime file.

The roots fixture links an independent C caller against otherwise uncalled
exports and an initialized function pointer. The indirect fixture calls a local
callback and must keep the complete runtime. The foreign fixture's unknown ABI
implementation calls an otherwise unreferenced runtime helper from C, proving
that foreign dependencies cannot be pruned by callee name.

Pruning removes only runtime functions. Every global, initializer, type, and
guest declaration is retained. All matching overload declarations are marked.
Unrecognized syntax, unresolved or indirect calls, casts, and reachable foreign
imports retain the whole runtime unless an explicit `--runtime-leaf` contract
asserts no hidden runtime dependencies for that linked symbol. No libc names or
ABIs receive implicit exemptions. The interposed fixture provides the ordinary
`write` ABI from C but calls `dead_helper`, and must work through both a minted
compiler and `--from-ast --runtime` without any contract.
This pass does not narrow the language or reject previously supported programs.
