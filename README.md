# lang

A self-hosted compiler where syntax is a plugin.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   .lang file    │     │   .lisp file    │     │   .whatever     │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │ lang reader           │ lisp reader           │ your reader
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                              AST                                │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 │ kernel
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│            LLVM IR (native) or direct WebAssembly             │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                     native exe or browser module
```

The compiler has two parts: a kernel (AST to native code) and readers (syntax to AST). The lang reader - the one that parses `func`, `if`, `while` - is just one reader. You can swap it for anything.

**Cross-platform**: Linux x86-64 and macOS ARM64 via LLVM.

## It's a language

```lang
func factorial(n i64) i64 {
    if n < 2 { return 1; }
    return n * factorial(n - 1);
}

func main() void {
    print_int(factorial(10));
}
```

Functions, structs, pointers, algebraic effects. See [LANG.md](./LANG.md).

## First run: local SDK archive

Start with the versioned archive produced by
`python3 scripts/package_sdk.py --output ../release`. There is no public download
yet; use the local `../release/lang-<version>-x86_64-linux.tar.xz` path.
You need Linux x86-64 with compatible glibc, `/bin/sh`, XZ-capable tar, Clang and
the system C development toolchain, including `ld` on PATH (Debian/Ubuntu:
`clang build-essential binutils xz-utils`).
See [SDK prerequisites and receipts](docs/SDK.md) for versions and host requirements.

```bash
tar -xJf ../release/lang-<version>-x86_64-linux.tar.xz
export SDK="$PWD/lang-<version>-x86_64-linux"
export PATH="$SDK/bin:$PATH"
mkdir my-language
cd my-language
lang new reader tiny
lang compiler tiny tiny.lang -o tinyc
./tinyc answer.tiny -o answer.ll
clang -O2 answer.ll -o answer
./answer
echo $?  # 42
```

### Second path: build from source

For compiler development, install Git, make, Python 3 and Clang, then:

```bash
git clone https://gitlab.com/ehrlich-b/lang
cd lang
make build
./out/lang_next new reader tiny
./out/lang_next run tiny.lang answer.tiny
echo $?  # 42
```

## It outputs compilers

That makes lang a **compiler compiler**: you write one reader function—source
text in, shared AST out—and lang turns it into a native compiler:

```bash
./out/lang new reader tiny
./out/lang run tiny.lang answer.tiny
./out/lang read tiny.lang answer.tiny -o answer.ast
./out/lang compiler tiny tiny.lang -o tinyc
```

`read` formats the shared AST for review and snapshots. Add `--compact` when a
host needs the reader's byte-for-byte protocol output.

Now `tinyc` is a native compiler for `.tiny` files:

```bash
./tinyc answer.tiny -o answer.ll
```

Same AST means same calling convention. Functions call each other directly at the machine level, no wrappers or runtime glue.

Use the lower-level `-c tiny ... -o tinyc.ll` form when you want compiler IR
for inspection or cross-compilation.

If emitted programs need a Lang runtime, embed it when the compiler is built:

```bash
./out/lang compiler minilisp example/minilisp/minilisp.lang \
  --runtime example/minilisp/lisp_runtime.lang -o minilispc
```

The runtime is expanded once and carried inside `minilispc`; `.minilisp` files
are still parsed only by the minilisp reader.

Start with the copyable [reader guide](./docs/READERS.md), grow into the small
[precedence parser](./example/calc/calc.lang), then steal from the shipped
examples below.

For AI-assisted reader work, use the [AI authoring guide](./docs/AI.md) and its
executable task pack. To diagnose a failure or report a wrong result, use the
[support guide](./docs/SUPPORT.md).

Or [write and run a generated reader in the browser](https://lang.ehrlich.dev/lab.html).
Edit its `#parser{}` grammar and lowering; the reader, AST, compiler, and output
program all stay in the tab. Choose **named capture tree** to inspect the
reader's `pnode_dump` output beside the grammar: node kinds, named captures,
and byte spans appear in the collapsible **reader diagnostics / tree** panel.
Edit the grammar and lowering, then build again; editing only the source
reuses the compiled reader. AST downloads still contain only the lowered AST.

For a local lab, run `make build`, `./web/build_compiler.sh`, then
`python3 -m http.server 8000 --directory web` and open
`http://127.0.0.1:8000/lab.html`. The software Chromium contract is
`node test/lab_tree_browser.mjs` after installing Playwright (`npm install
--no-save playwright`); set `CHROMIUM_PATH` to use an existing browser and
`LAB_EVIDENCE_DIR` to save screenshots and a JSON receipt.

To try source diagnostics locally, serve `web/` with
`python3 -m http.server 8080 --bind 127.0.0.1 --directory web`, open
`http://127.0.0.1:8080/lab.html`, and choose any of the five **find an error**
workspaces. **Build + run** selects the offending source token; **jump to error**
returns to it after you inspect the reader. The examples include comments,
blank lines, accents and emoji. Locations use 1-based UTF-8 byte columns, which
the editor converts to its own text offsets.

`node test/reader_locations.js` checks native rejections.
`node test/reader_locations_browser.mjs` compares native and browser diagnostics,
checks focus and click selection, runs the five valid examples, and saves PNGs
and a JSON receipt under `out/reader-locations/`. The browser check needs
Playwright and Chromium; `PLAYWRIGHT_MODULE` may name Playwright's `index.mjs`,
`CHROMIUM_PATH` may name an existing Chromium executable, and `EVIDENCE_DIR`
chooses the artifact directory.

## Shipped readers, one binary

A reader parses its own surface syntax and emits lang AST. The kernel compiles whatever any reader emits, so several readers can share one program — and because they all lower to the same AST, they share one calling convention. They call each other directly at the machine level. No FFI, no interpreter, no glue.

[`example/polyglot.lang`](./example/polyglot.lang) puts five real languages in one native binary:

```lang
#forth{ : divides? ( d x -- f ) swap mod 0 = ; }             // postfix, no grammar

#c{ int c_is_prime(int x) {                                  // imperative C,
        ... if (divides_p(d, x)) { return 0; } ...           //   calling Forth
} }

#minilisp{ (defun ml_sum (xs)                                // a real Lisp:
    (if (eq xs nil) 0 (+ (car xs) (ml_sum (cdr xs))))) }     // closures, quote, lists

#flow{                                                       // a coroutine DSL:
    gen primes(n) { ... if c_is_prime(x) { yield x; } ... }  //   suspend / resume
    func collect_primes(n) {
        var lst = lisp_nil();
        for p in primes(n) { lst = lisp_cons(lisp_int(p), lst); }
        return lst;
    }
}

#minipy{                                    // layout: no block delimiters at all
def report(n):
    lst = collect_primes(n)                 # flow's coroutine -> C -> forth
    total = lisp_to_int(ml_sum(lst))        # minilisp, folding a cons list
    print("primes <=", n, "sum", total, "digitsum", digit_sum(total))
    return total                            #                       ^ forth
}
```

flow's `primes` coroutine streams primes — asking C about each candidate and suspending between hits; C's trial-division loop asks Forth about each divisor; flow's driver conses each prime onto a Lisp list; Lisp folds the list; minipy loops over the whole pipeline and formats the answer. Five paradigms — stack, imperative, coroutine-effectful, functional, scripting — each doing its idiomatic job, meeting at the i64 ABI.

No two of the five agree on so much as where a block ends: parens, braces, `;`, `then`, and — in minipy — nothing but the column the line starts in.

- **C** ([example/c/](./example/c/)) is a [legacy/internal subset](docs/C_SUBSET.md): `int → i64`, no switch fall-through, and no standard C ABI claim.
- **minilisp** ([example/minilisp/](./example/minilisp/)) is a real (small) Lisp: first-class closures, `let`, `quote`, cons lists. Every value is an i64 that's secretly a pointer, so it marshals across the language boundary.
- **flow** ([example/flow/](./example/flow/)) is a generator/coroutine language built on algebraic effects. `yield` is bidirectional — a generator's output can depend on what the driver sends back.
- **forth** ([example/forth/](./example/forth/)) has no expression grammar at all — just a flat stream of words over a data stack. The stack is the reader's, not the program's: it holds AST nodes at read time and is gone before codegen, so `: square ( n -- n2 ) dup * ;` compiles to a single `mul`.
- **minipy** ([example/minipy/](./example/minipy/)) is layout-delimited: block structure lives in the whitespace every other reader discards. It needed no change to the shared tokenizer — a token carries its byte offset, so the reader recovers the columns and synthesizes INDENT/DEDENT itself. Layout is reader-local.

None of this extended the kernel; readers are syntax plugins, not compiler patches. The honest claim isn't "capture any language" — it's *compose any syntax at the ABI level in one native binary*.

## It compiles itself

Check the language-author path with
`env JOBS=2 VERIFY_CASE=path-receipt make verify`. It measures the shipping
project once and writes a source-bound `matrix.json` and concise `README.md`
under the printed evidence directory. The panel covers grammar, capture tree,
semantics, diagnostics, native output, package relocation, formatting, editor
facts and self-hosting. Missing proof stays **not measured**.
`make release-check PATH_RECEIPTS="/path/to/focused.json ..."` reads focused
receipts and fails until the whole path has current deliverables; a broad gate
pass cannot fill an empty cell. See the [receipt contract](docs/PATH_RECEIPTS.md).

The lang reader is written in lang. The kernel is written in lang. The compiler compiles itself from source, producing identical output. Fixed point.

```bash
make bootstrap    # Verify fixed point, run tests, promote stable compiler
```

## Building

```bash
make build        # Compile from source → out/lang_next
make dev-run FILE=... # Compile and run with that source candidate
```

Or use the source candidate directly: `./out/lang_next run hello.lang`.
`make run` and `./out/lang` use the separately promoted stable compiler.

Reader and tooling authors can inspect the exact lexer stream without parsing
or compiling:

```bash
./out/lang --dump-tokens hello.lang
```

Two compilers live in `out/`: **`out/lang`** is the stable compiler, promoted by
the last successful `make bootstrap`. **`out/lang_next`** is
whatever `make build` just compiled from source; it only matters when you are
testing the selected source before promotion. See the [identity and receipt
contract](docs/BUILDING.md#choose-and-prove-a-compiler-identity): `make verify`
preserves the seed and stable compiler; `make bootstrap PUBLISH_BOOTSTRAP=0`
still promotes locally.

### Compiling programs

See the [current target profiles](docs/PROFILES.md), [size limits](docs/SIZE_LIMITS.md), and reproducible baseline command before selecting a backend or external ABI.

```bash
./out/lang hello.lang -o hello.ll
clang -O2 hello.ll -o hello
```

No environment variables needed: the compiler defaults `LANGBE`/`LANGOS` to the
platform it was built for. Set them only to cross-target (`LANGOS=macos`,
`LANGOS=wasm`; `LANGBE=x86` for the frozen assembly backend on Linux).

The LLVM backend is the primary native target. Its current contract covers the
tested scalar, closure, reader and [scoped effects](docs/EFFECTS_CPS.md) paths.
General external layout and calling conventions remain unverified.

Use the development compiler after `make build` to run native effects with the
default `-O2`:

```bash
./out/lang_next run example/polyglot.lang
```

`COMPILER=out/lang_next python3 -B test/run_effects_safety.py` checks the
suite's effects programs and multiple-perform probes at `-O0`, `-O1`, `-O2`,
and `-O2 -flto`.

### WebAssembly

```bash
LANGOS=wasm LANGBE=llvm ./out/lang hello.lang -o hello.ll
clang --target=wasm32-unknown-unknown -nostdlib -Wl,--no-entry -Wl,--export-all \
      -Wl,--allow-undefined -Wl,-z,stack-size=8388608 hello.ll -o hello.wasm
node test/wasm_host.js hello.wasm
```

`test/wasm_host.js` is a small node host providing the libc surface
(write/alloc/exit). LLVM-to-Wasm uses the scoped CPS lowering for effects.
It stores single-use continuations in explicit frames and resumes them through
a state-machine loop using ordinary Wasm calls. The profile supports `i64`
effect results, zero or one `i64` payload, and tail resumption from the owning
handler clause.

Run `./test/run_wasm_suite.sh` for the suite, or set `TESTS` to a space-separated
list of fixture paths for a fragment.

Flow's synchronous generators can also use `#flow_portable{...}` from
`example/flow/flow.lang`. This reader specializes each `for x in gen(...)`
pair into ordinary structured control flow: statement `yield` runs the driver
body, then continues the generator with its locals intact. The stateful
Fibonacci program in `test/flow_wasm.lang` prints `flow answer: 42` and returns
42 natively, through LLVM-to-Wasm under node, and through direct Wasm under node.
Nested driver bodies can forward yields and return from their lexical generator.

```bash
make build
COMPILER=out/lang_next python3 test/run_flow_wasm.py
make test-direct-wasm COMPILER=out/lang_next
```

Portable generators must be declared in the same reader block and driven by
`for-in`; recursive generator specialization and expression `yield` are refused
with source locations. The existing `#flow` reader retains native effects and
bidirectional `yield`/`send`; those effects still require native `clang -O0`.
See [the Wasm profile](docs/profiles/llvm-wasm32.md) for the boundary.

### Bootstrap

The compiler bootstraps from preserved LLVM IR:

```
bootstrap/current/compiler_linux.ll
bootstrap/current/compiler_macos.ll
```

The legacy x86 assembly backend is frozen. It served the self-hosting proof and
remains a historical recovery path, but LLVM is the future for Language Forge.

## Docs

- [LANG.md](./LANG.md) - Language reference
- [TODO.md](./TODO.md) - Roadmap
- [docs/](./docs/) - Technical documentation
  - [READERS.md](./docs/READERS.md) - Write a syntax reader and mint a compiler
  - [AST_BUILDERS.md](./docs/AST_BUILDERS.md) - Shared AST builder quick reference
  - [PARSER_GENERATOR.md](./docs/PARSER_GENERATOR.md) - `#parser{}` grammar and limits
  - [BUILDING.md](./docs/BUILDING.md) - Build instructions and compilation pipeline
  - [BOOTSTRAP.md](./docs/BOOTSTRAP.md) - Bootstrap process and trust chain
  - [AST.md](./docs/AST.md) - AST node reference (41 node types)
- [designs/ast_as_language.md](./designs/ast_as_language.md) - Architecture vision

## License

[MIT](./LICENSE)

For machine-readable compiler failures, see [compiler diagnostics version 1](docs/compiler-diagnostics.md) and `--diagnostics=json`.

`make init` reuses a native seed cache across checkouts. Set `LANG_NATIVE_CACHE`
(or `XDG_CACHE_HOME`) to choose its location. The key includes the preserved IR
bytes, resolved clang executable bytes and version, effective target, ordered
`INIT_FLAGS` (default `-O2`), and `INIT_ABI` (default `native-v1`). `CLANG` and
`INIT_TARGET` select the tool and target. Entries carry a SHA-256 artifact receipt,
are published atomically under a per-key lock, and are never overwritten.
Invalid entries fail closed before installation. Each checkout receives its own
`out/lang_bootstrap` copy and relative `out/lang` link, so editing local output
cannot alter the shared cache. The cache is for trusted local build inputs;
it does not authenticate artifacts from an untrusted cache writer.
