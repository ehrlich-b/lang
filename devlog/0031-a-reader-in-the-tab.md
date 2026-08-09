# A reader in the tab

The direct backend became useful when it stopped being an arithmetic demo.
Writable data segments and i64-canonical pointers enabled string scanners;
globals made literal pointers stable; a separate `lang` import namespace kept
the direct backend's all-i64 host ABI from colliding with LLVM's wasm32 pointer
ABI. Heap-backed struct fields then unlocked the existing tokenizer and AST
builder libraries.

One backend policy mattered more than another opcode: emit only functions
reachable from `main`. A tiny reader includes the whole standard library, but
does not use its floating-point printer, filesystem search, or process tools.
Rejecting an unused `printf(f64)` made the backend feel arbitrarily broken.
Reachability pruning both removes that false failure and produces tiny modules.

Lexical shadowing was the next honest failure. Flattening every local by name
worked for demos but failed in `tok_next`, where separate branches reuse a
temporary named `next`. Locals now have stable wasm slots while a scoped binding
stack resolves each identifier at its actual point in the source.

Those pieces close the compiler-compiler loop without browser subprocesses:

1. compiler.wasm compiles the editable reader to a reader wasm module.
2. That module reads editable custom source and returns shared AST text.
3. compiler.wasm consumes the AST and emits the program wasm module directly.
4. The tab runs `main()` and shows a short AST preview.

The end-to-end test uses the real tiny reader and gets 42 from the second
module. The lab now has two bounded columns—reader on the left, source and
result on the right—so generated output never turns the page into a scroll.

The next boundary is generated readers. `#parser{}` still assumes the native
compile-time execution path, and the direct backend deliberately rejects its
remaining array/function-pointer/aggregate features instead of emitting a
module that happens to validate but lies about the language.
