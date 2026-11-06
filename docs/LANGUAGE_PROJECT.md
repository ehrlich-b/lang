# One language project

Create a complete editable project with `lang new language parcel`. It creates
a new `parcel/` directory containing a manifest, grammar/reader, semantic checks,
target runtime, positive policy, syntax and semantic negative fixtures, and a
Python runtime comparison. It refuses any existing destination before writing.
A failed write leaves the incomplete new directory for inspection and exits 1;
existing content is never replaced. `lang new reader` keeps its two-file form.

Invoke the compiler by its absolute path from any working directory. For example,
after `make init` and `make build`, `/absolute/path/to/lang/out/lang_next new language parcel`
prints exact, shell-quoted commands using that tool path. Run the printed block
to validate the manifest, inspect shared AST, mint the native compiler with its
embedded runtime, and compare runtime output and negative fixtures. No `LANG_ROOT`
override or compiler source edit is needed. Keep the generated project as the
working directory when editing and checking it.

`reader.lang` separates grammar, semantic validation and lowering. `runtime.lang`
handles target input/output; the emitted cost function compares the runtime total
against the policy threshold. Edit `ast_ge` to `ast_gt`, adjust `cases.json`, and
repeat the printed commands to change the inclusive boundary. The generated
`check.py` exits nonzero on any wrong output, exit code or missing diagnostic.

Replay only this fragment with `python3 -B test/reader_author/scaffold.py --case project`.
Use `env JOBS=2 VERIFY_CASE=project make verify` for its make gate; plain verification
continues to select integration checks. Receipts and source/tool hashes stay
outside the checkout.

A project manifest records the frontend, target runtime and guest entry file
that otherwise need to be coordinated on the command line. Start with
[`example/shipping/project.lang-project`](../example/shipping/project.lang-project):

```text
project {
    version 1;
    reader_source "shipping.lang";
    reader_name "shipping";
    source_suffix ".shipping";
    runtime_files ["runtime.lang"];
    entry "policy.shipping";
    backend "llvm";
    native_profile "llvm-linux-x86_64";
    native_toolchain "clang";
}
```

Every field is required exactly once; order is free. Unknown fields, unknown
versions, duplicate fields and trailing input fail with a manifest line and
UTF-8 byte column. Strings use Lang string escaping. Empty strings and control
bytes are rejected. `runtime_files` is an ordered list of Lang sources; use
`[]` for a language without a runtime. The reader source must declare the named
reader exactly once. The current extension dispatch requires `source_suffix`
to be a dot followed by `reader_name`; `.lang` and `.ast` are reserved.
The entry file must have that suffix. Version 1 has one reader source root;
its existing include/require dependencies supply the rest of the frontend.

Reader, runtime and entry paths resolve relative to the manifest's directory,
including `..`; absolute paths also work. Includes and requires within Lang
sources keep the existing compiler resource resolver: the working directory,
then the compiler's resource root (`LANG_ROOT` when configured). Manifest
paths themselves never fall back to that root. There is no directory change,
implicit include rebasing or new dependency scanner.
Missing reader and runtime dependencies report the manifest location of
`reader_source` or `runtime_files`, together with the resolver's error code
and failing dependency path, including failures in transitive dependencies.

From the repository root, build the current compiler, then validate and use the
shipping project:

```bash
make init
make build
export LANGBE=llvm LANGOS=linux
./out/lang_next project check example/shipping/project.lang-project
./out/lang_next project read example/shipping/project.lang-project -o out/policy.ast
./out/lang_next project compiler example/shipping/project.lang-project -o out/shippingc
./out/shippingc example/shipping/policy.shipping -o out/policy.ll
clang out/policy.ll -o out/shipping
./out/shipping 99
./out/shipping 100
```

The last two commands print `10` and `0`. `entry` names the guest source used by
`project read`; its reader emits the normal native `main` entry point. A minted
compiler accepts other guest files through the existing compiler CLI. Runtime
sources are embedded at compiler-build time, so the minted artifact needs no
runtime source tree when emitting IR. The original editable
[shipping walkthrough](../example/shipping/README.md) remains available.

`project check` only loads, parses and hashes inputs. It uses immutable
`PhaseSource` snapshots and the existing dependency resolver for
transitive include/require identities. It never expands a reader, compiles,
looks up a reader artifact or executes a subprocess. The printed digest covers
the manifest bytes/path, reader dependencies, entry bytes/path and runtime
dependencies. It is an input identity, not a compiler build receipt or a sandbox
claim. Reader artifact caching still includes compiler identity through the
existing compiler-host path. Two projects can declare the same reader name;
their source paths and bytes distinguish their inputs.

`read` and `compiler` deliberately execute trusted native frontend code. For
version 1, backend `llvm`, profile `llvm-linux-x86_64` and toolchain `clang` are
the only supported combination. Conflicting `LANGBE`/`LANGOS` selections fail;
execution requires a native Linux x86-64 host. Clang and its native linker are
resolved by the existing tool lookup; the manifest contains no commands, flags,
interpolations or executable shell strings. Other targets require a future
explicit profile contract. Existing reader-only commands are unchanged.

Run `python3 -B test/reader_author/project.py --case manifest` from a clean,
committed checkout. It builds current sources in a fresh clone and records
commands, source/tool hashes, stdout, stderr and exits outside the checkout.
For the narrow make gate, use `env JOBS=2 VERIFY_CASE=manifest make verify`.
Plain `make verify` retains the full integration and fixed-point checks.

## Build a guest directly

Use the shared compiler-host driver to produce a named native executable:

```bash
./out/lang_next build --project example/shipping/project.lang-project example/shipping/policy.shipping -o out/shipping
PATH=/nonexistent ./out/shipping 100
./out/lang_next build --project example/shipping/project.lang-project example/shipping/policy.shipping --emit=ast -o out/policy.ast
./out/lang_next build --project example/shipping/project.lang-project example/shipping/policy.shipping --emit=llvm -o out/policy.ll
```

`SOURCE` is relative to the caller's working directory and may differ from the
manifest's entry; its suffix must match the project reader. Manifest inputs keep
the resolution rules above. The driver resolves the manifest, runs the trusted
reader, validates the shared AST, emits LLVM with the manifest's target runtime,
compiles an object, then links it. `--emit=ast` stops after validation and writes
the formatted reader AST (without the separate target runtime). `--emit=llvm`
includes the runtime and stops before object compilation. Neither alternative
needs the final native toolchain; compiling an uncached reader still needs Clang.

The native default is **`-O0`**, explicitly passed to Clang and recorded on stderr
as `optimization=-O0` along with the profile and selected tool. This follows the
current native effects contract; the driver makes no optimized-effects promise.
Object compilation and linking are separate subprocesses. The manifest selects
the `clang` family; the driver resolves `clang` from `PATH`, or uses the exact
executable path in `LANG_CLANG`. That override can contain spaces. Arguments are
passed directly, without a shell. There is no fallback after a configured tool
fails. Reader compilation retains its existing independent tool lookup.

Reader, shared-AST validation, LLVM emission, optimizer/object compilation and
linker failures retain their original stderr and add the failing stage. Child
exits propagate (signals become `128 + signal`); missing final Clang exits 127.
The final artifact stays private in an exclusively reserved directory beside
`OUTPUT` until every requested stage succeeds, then a same-filesystem rename
publishes it. Temporary artifacts are removed after success or a reported stage
failure. An attempted rebuild invalidates a previous native ELF output before
manifest resolution, so a failure cannot leave that executable looking current.
For safety, an occupied destination must be a regular native ELF file; other
files, symlinks and directories are refused and preserved. Use a fresh path for
AST/LLVM inspection. The source and manifest themselves cannot be output paths.

Replay this fragment with `python3 -B test/reader_author/native_build.py --case shipping`.
It builds the committed compiler in an isolated clone and preserves commands,
source/tool SHA-256 hashes, stdout, stderr and exits under `../evidence/`.
It checks real shipping execution with no compiler or VM on `PATH`, syntax and
shared-AST errors, absent Clang, real Clang rejection of invalid IR, real native
linker rejection of an unresolved symbol, stale-output removal and quoted paths.
Every expectation uses an explicit check, including under optimized Python.
Use `env JOBS=2 VERIFY_CASE=native-shipping make verify` for this fragment's gate.
Plain verification continues to select integration suites and fixed points.
