# The compiler enters the browser

The program demos were wasm, but the compiler was still native. Compiling the
self-hosted kernel to wasm exposed one backend boundary immediately: wasm32
cannot relocate a pointer directly into the compiler's uniform i64 global
storage, and current LLVM no longer permits a constant-expression `zext` as a
bridge. Pointer globals now use native i32 storage on wasm and widen to i64 when
loaded. Assignment narrows in the other direction.

With that fixed, the entire compiler links to a 478 KiB wasm module. A small JS
host gives it real argv and environment values plus an in-memory filesystem for
`open`, `read`, `write`, `stat`, and `unlink`. The compiler remains blissfully a
CLI: it reads `input.lang` and writes `output.ll`; only the filesystem happens
to live in the tab.

The proof is deliberately end to end. `test/run_compiler_wasm.sh` builds
compiler.wasm, asks it to compile a program whose global pointer is initialized
and reassigned, links the LLVM it wrote, and runs the resulting wasm. Exit 98 is
the letter `b` read through that global pointer. The same host powers a compact
browser lab with two bounded panes, so neither source nor IR grows the page.

This completes the compiler-in-browser boundary, not the reader lab. An edited
reader is compile-time code and browsers cannot fork its generated executable.
The clean next step is the direct wasm backend: emit a reader module in the tab,
instantiate it, then feed its AST back to the kernel. Shipping LLVM into the
browser or calling a server would dodge the actual architecture.
