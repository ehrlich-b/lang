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

## Test a change in seconds

Build your candidate once with `make build`, then reuse it:

```bash
make fragment
make fragment FILES='src/parser.lang src/lexer.lang' JOBS=2
make fragment COMPILER=out/lang_next FILES='src/codegen_llvm.lang'
```

With no `FILES`, fragment diffs the working tree (including staged changes and
untracked files) against `git merge-base HEAD origin/main`. Set `FRAGMENT_BASE`
to use another integration ref. Explicit `FILES` names changed paths, separated
by spaces (shell quoting inside the value supports spaces in a path); an empty
value selects nothing. Deleted and renamed paths are included in the diff.
`FRAGMENT_COMMIT=<sha>` selects the paths changed by an existing commit relative
to its first parent, while testing the current compiler and fixtures. It does
not check out or rebuild that historical compiler.

[test/fragment-map.json](../test/fragment-map.json) maps paths to named groups
and individual fixtures. Reader changes exercise tiny/calc reader construction
and parser diagnostics; LLVM changes exercise lexical bindings, calls and
pointers. Changed `test/suite/*.lang` fixtures run directly. Docs and images
run zero tests, without needing a compiler. Every other unmapped path, including
an unknown compiler source, prints a fallback notice and runs the named
`compiler-smoke` set (return value, precedence, recursion). Add focused fixtures
and mappings with each new compiler feature; the fallback is only early feedback.

Fragment never builds the compiler. It chooses `COMPILER`, then `out/lang_next`,
then `out/lang`, resolves that binary once and reports it. Rebuild explicitly
after changing compiler sources: using a stale binary tests stale behavior.
It runs at most four workers (`JOBS=1` for serial execution), uses `clang -O0`
for generated programs whose oracles do not depend on optimization, isolates
each reader cache, and checks exit values or rejection diagnostics. Existing
reader helper construction keeps the compiler's own build policy. Each test
has a timeout; compilation, linking, execution and oracle failures fail the
target. Output includes selected test count, aggregate process/child CPU seconds
and wall seconds. `FRAGMENT_REPORT=/path/report.json` saves machine-readable
results. Use `TMPDIR` to place temporary artifacts outside the checkout.

This is selective feedback, not proof of complete impact coverage. Integration
still runs the unchanged `make verify`, `make bootstrap` and
`test/run_llvm_suite.sh`. Bootstrap must still reach both the LLVM and AST fixed
points. Run full integration verification before promotion or release, for
cross-cutting compiler/runtime/ABI changes, optimization-dependent behavior,
backend portability, and whenever the small mapping or fallback cannot establish
coverage. Fragment does not replace optimization or Wasm oracles.

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

An `out/lang` binary invoked by path also finds the checkout's `std/` from
another working directory. Set `LANG_ROOT=/path/to/lang` only when the compiler
has been moved away from its checkout; `lang tools` shows the resolved resource
root and whether `std/core.lang` is present.

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

## Choose and prove a compiler identity

| Command | Candidate | Stable `out/lang` | Preserved seed | Archive upload |
|---|---|---|---|---|
| `make build` | `out/lang_next` | preserved (initialized if absent) | preserved | none |
| `make verify` | `out/bootstrap_verify/kernel2` | preserved, including symlink | preserved | none |
| `make bootstrap-local` | verified platform compiler | replaced after validation | promoted | none |
| `make bootstrap PUBLISH_BOOTSTRAP=0` | same local promotion | replaced after validation | promoted | none |
| `make bootstrap` | same promotion | replaced after validation | promoted | GitHub release |

`PUBLISH_BOOTSTRAP=0` controls upload only. Use `make verify` for a replay that
must preserve both the seed and stable compiler. Promotion can be tested in a
separate checkout without changing the working checkout's root of trust.

Each successful source build writes `out/build-receipt.json`; verification
writes `out/verify-receipt.json`; promotion writes `out/bootstrap-receipt.json`.
These JSON receipts include the full source revision, dirty-source flag, exact
source input hashes, bootstrap identity and seed hashes, builder hash, resulting
compiler bytes/hash and complete `version` output. Verification also records
both LLVM and reader-AST fixed-point pairs. A revision identifies the selected
commit; input hashes describe the actual working files, including dirty edits.
A failed build does not create a new successful receipt; consumers must validate
the existing receipt against current source and binary bytes before using it.

To test the current source, build it and use the candidate explicitly:

```bash
make build
./out/lang_next run example/tiny/tiny.lang example/tiny/answer.tiny
# The sample returns 42.
python3 test/run_identity.py source --output /absolute/path/to/evidence
python3 test/run_identity.py verify --output /absolute/path/to/evidence
python3 test/run_identity.py promotion --output /absolute/path/to/evidence
```

The source gate builds the selected revision and uses the receipt-bound candidate
for the generated-reader tutorial, AST round trip, and native compiler packing.
The verification gate checks seed hashes, stable binary bytes, version output
and symlink identity before and after two complete verification replays. The
promotion gate exercises `make bootstrap PUBLISH_BOOTSTRAP=0` in another checkout.
Evidence directories must be outside the repository.

`web/build.sh` and `web/build_compiler.sh` build `out/lang_next` by default.
An explicit `COMPILER` requires its matching `COMPILER_RECEIPT` (default
`out/build-receipt.json`); a stale compiler or changed source fails before
artifact generation. For example, after verification:

```bash
COMPILER=./out/bootstrap_verify/kernel2 COMPILER_RECEIPT=out/verify-receipt.json ./web/build.sh
```

Browser metadata is regenerated for `wasm-wasm32` from that receipt instead of
reusing the native version file. `web/compiler-receipt.json` binds the compiler
and library bundle; `web/receipt.json` also binds example source and wasm bytes.
Their source revision is the commit used to generate the artifacts, which can
precede a later artifact-only commit. Every recorded source input must still
match. `node test/browser_identity.js /absolute/path/to/evidence` checks hashes,
byte sizes, browser `version` output, invalid-input refusal, and byte-for-byte
wasm emission plus behavior against a fresh native source compiler.
