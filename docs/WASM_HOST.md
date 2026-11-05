# Browser program host contract

The reader lab runs direct Wasm through `web/program_host.js` (`runLangProgram`).
The example page runs LLVM/wasm32 programs through `web/host.js` (`runLangWasm`).
Both validate `WebAssembly.Module.imports` before instantiation against the
functions actually supplied by that host. No third-party browser library is used.

Direct Wasm imports functions from **lang**; LLVM/wasm32 imports them from **env**.
These are the concrete supported function names in both hosts:

```
read write open close stat unlink mkdir rmdir getcwd
mmap munmap malloc calloc free memcpy memmove memset
getenv getpid getppid fork execve waitpid pipe dup2 exit _exit printf
```

Names and namespaces are case sensitive. Tables, globals, memories and other
import kinds are unsupported, including an import with a supported function name
and a different kind. WASI and arbitrary native externs are unsupported.

Programs must export `main` as a function and `memory` as a memory. Memory is
module-owned, unshared wasm32. Its initial minimum must be at most **4096 pages
(256 MiB)**. A larger declared maximum alone is allowed: this is an initial
allocation limit, not a runtime growth quota or a sandbox resource guarantee.
An optional `__heap_base` global supplies the allocator's starting address.
The LLVM host also invokes an optional `__wasm_call_ctors` function before main.

Unsupported requirements throw `LangWasmTargetLimitError`, with code
`LANG_WASM_TARGET_LIMIT` and a message starting `Wasm target limit:`. Its `limits`
array lists all unsupported module/name/kind combinations, missing exports and
unsupported memory requirements. These errors also inherit `WebAssembly.LinkError`
for existing callers. Validation compiles the binary first: malformed modules
remain `WebAssembly.CompileError`, and guest execution traps remain runtime errors.
The engine still checks function signatures when linking/calling; the reflection
API does not expose those signatures. Neither compiler backend is changed.

The supported functions provide a deliberately small environment:

- `write` sends fd 2 to stderr and other fds to stdout. Direct `read` consumes
  supplied UTF-8 stdin on fd 0; other fds return EOF. LLVM `read` always returns EOF.
- `malloc`, `calloc` and `mmap` bump-allocate; `free` does nothing and `munmap`
  returns 0. The byte copy/set functions operate on exported linear memory.
- `open`, `stat`, `unlink`, `mkdir`, `rmdir`, `fork`, `execve`, `waitpid`, `pipe`
  and `dup2` return -1. `close` returns 0. `getcwd` and `getenv` return null.
  `getpid` returns 1 and `getppid` returns 0. No filesystem or process is created.
- `exit` and `_exit` stop the run with the low eight bits of their argument.
  Direct `printf` returns 0 without output; LLVM `printf` supports `%d`, `%f`,
  `%g` and their optional `l` forms through its varargs buffer.

Direct imports use the compiler's canonical i64 ABI, including pointers. LLVM
imports retain the existing mixed i64/pointer ABI described in `web/host.js`.
The host does not make an unsupported native operation portable by accepting its
name: the failure/null stubs above are their concrete browser behavior.

With a fresh compiler built by `make build`, run the six focused cases with
`node test/wasm_host_contract.js` (or `node --test test/wasm_host_contract.js`).
They verify the build receipt, generate a tiny stdin reader and its output
program, and execute that pair after every rejected module. `TMPDIR` selects
where generated test artifacts are retained; `COMPILER` and `COMPILER_RECEIPT`
can select another freshly built compiler and matching receipt.
