# Building lang

Lang builds on Linux x86-64 and macOS ARM64. LLVM is the primary backend; the
x86 assembly backend is frozen and kept as a recovery path.

## Prerequisites

- `make`
- LLVM's `clang`
- LLVM's `lli` for the fastest test path (optional)
- GNU `timeout` or `gtimeout` for test timeouts (optional)

Check what the compiler can see:

```bash
./out/lang tools
```

## First build

The repository normally includes a working `out/lang`. If it does not:

```bash
make init
```

`make init` compiles the platform-specific preserved LLVM IR in
`bootstrap/current/` with `clang`.

Build the current sources:

```bash
make build
```

Two compiler names are intentional:

- `out/lang` is the stable, bootstrapped compiler.
- `out/lang_next` is the candidate just built from the working tree.

Use `out/lang_next` while developing compiler changes. A successful
`make bootstrap` promotes the verified compiler to `out/lang`.

## Compile a program

```bash
LANGBE=llvm ./out/lang hello.lang -o hello.ll
clang -O2 hello.ll -o hello
./hello
```

For the common case:

```bash
LANGBE=llvm ./out/lang run hello.lang
```

On macOS, LLVM is already the compiler's default. Setting `LANGBE=llvm` keeps
commands portable to Linux, where the legacy x86 backend may still be the
compiled-in default.

Useful target variables:

| Variable | Values | Meaning |
|---|---|---|
| `LANGBE` | `llvm`, `x86` | Code generator; new work belongs in LLVM |
| `LANGOS` | `linux`, `macos`, `wasm` | Target platform |
| `LANGLIBC` | `none`, `system` | Runtime/libc mode |
| `LANG_CACHE` | path | Reader executable cache (default `.lang-cache`) |

For WebAssembly:

```bash
LANGBE=llvm LANGOS=wasm ./out/lang hello.lang -o hello.ll
clang --target=wasm32-unknown-unknown -nostdlib -Wl,--no-entry \
  -Wl,--export-all -Wl,--allow-undefined -Wl,-z,stack-size=8388608 \
  hello.ll -o hello.wasm
node test/wasm_host.js hello.wasm
```

Effects are intentionally rejected for the wasm target because core wasm has
no stack-switching primitive.

## Write a compiler

A reader is a frontend function: source text in, shared AST out. Compose one
with the kernel to produce a compiler for its file syntax:

```bash
./out/lang compiler tiny example/tiny/tiny.lang -o tinyc
./tinyc example/tiny/answer.tiny -o answer.ll
```

Use `./out/lang -c tiny ... -o tinyc.ll` when you specifically want the
intermediate compiler IR.

For a reader whose output calls runtime helpers, embed Lang runtime source when
minting the compiler:

```bash
./out/lang compiler minilisp example/minilisp/minilisp.lang \
  --runtime example/minilisp/lisp_runtime.lang -o minilispc
```

The native compiler carries the expanded runtime AST and can be used away from
the repository. Generated parser functions remain in the artifact; the
build-only parser generator and Lang frontend are removed by dead stripping.

See [READERS.md](./READERS.md) for the copyable 20-line reader and the reader
contract.

## Tests

```bash
./test/run_llvm_suite.sh
./test/run_wasm_suite.sh
./test/run_direct_wasm.sh
```

## Browser compiler

Build the self-hosted compiler as wasm and verify that it can compile a virtual
source file, with no host filesystem access:

```bash
./web/build_compiler.sh
./test/run_compiler_wasm.sh
```

`web/compiler_host.js` supplies argv, environment variables, allocation, and an
in-memory filesystem. The end-to-end test exercises both compiler paths: LLVM
IR for the mature backend and a directly emitted wasm module for the browser
lab. Direct wasm covers the scalar control-flow core plus strings, pointers,
globals, host imports, heap-backed structs, source includes, and dead-function
pruning. That is enough for the browser E2E to run `std/tok.lang` and
`std/ast.lang`: reader source → shared AST → program wasm → `main()`. The web
build also embeds the `#parser{}` generator, while generated reader modules carry
only `std/parser_runtime.lang`; the browser gate exercises grammar → reader wasm
→ AST → program wasm. Unsupported features still fail with compiler diagnostics.
The lab compiles returned AST with `--ast-source source.read`, binding optional
`(span START END NODE)` metadata back to the editable custom source.
Direct wasm also covers nested and labeled `break`/`continue` plus i/u8/16/32/64
locals. Address-taken locals use per-call spill frames, so ordinary cursor code
and `require "module"` sources work unchanged. The browser gate compiles and
runs minimal programs through every shipped reader.
If emitted AST calls Lang helpers, add `--runtime helper.lang` beside
`--from-ast`; the browser lab exposes the same path in a collapsed target-runtime
editor. The browser gate uses it to compile and run Minilisp's boxed integer 42.

Test a candidate compiler without promoting it:

```bash
COMPILER=./out/lang_next ./test/run_llvm_suite.sh
```

The LLVM suite includes ordinary language tests, shipped-reader end-to-end
checks, stale-cache coverage, and a compiler-compiler proof.

## Compiler development

Compiler sources are in `src/`; library code used by readers and programs is in
`std/`. The usual loop is:

```bash
make build
COMPILER=./out/lang_next ./test/run_llvm_suite.sh
make bootstrap
```

After any compiler change, `make bootstrap` is required. It rebuilds multiple
generations, checks LLVM and reader-AST fixed points, validates both platform
artifacts with `clang`, runs the suite on the final binary, archives the old
bootstrap as a GitHub release, stages complete root files before promotion, and
replaces the stable compiler only after every check succeeds. See
[BOOTSTRAP.md](./BOOTSTRAP.md).

Do not copy bootstrap files by hand or promote a partially verified compiler.
