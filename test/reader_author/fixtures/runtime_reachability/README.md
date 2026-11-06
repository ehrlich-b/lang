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
Unrecognized syntax, unresolved or indirect calls, casts, and foreign imports
outside the exact read/write/exit/malloc/calloc/free libc leaf ABIs retain the
whole runtime. The libc contracts assume the ordinary system libc implementation.
This pass does not narrow the language or reject previously supported programs.
