# Wasm without a middleman

The browser compiler used to stop one step early: it emitted LLVM text into a
bounded pane. That proved the self-hosted compiler could run in a tab, but the
tab still could not run what it compiled without an LLVM toolchain.

`codegen_wasm.lang` now writes the wasm binary format directly. The first slice
is intentionally small and executable: i64 and boolean functions, locals,
arithmetic, direct calls, `if`, and `while`. A compiler running as wasm can
compile an in-memory Lang source to a 133-byte module, instantiate it, and get
42 back from `main()`. No server and no native linker participate.

The useful architectural lesson arrived before the first opcode. The CLI wraps
every input path in an `include`, so a backend cannot assume main has handed it
a flat program. Direct wasm now recursively reads and parses included source,
preserving the same source-aware failure boundary as the mature backends.

The lab no longer scrolls through generated IR. It has one bounded editor and
one short result pane: compile + run. Unsupported constructs fail closed with a
diagnostic, which makes the next work explicit rather than pretending this is
already the reader sandbox.

That next slice is memory-shaped: pointers, strings, globals, extern imports,
then aggregates. Those are the pieces a reader and the AST builder library need
before the second editor can truthfully accept a new language.
