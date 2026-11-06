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

## Run project fixtures

`lang test --project PROJECT` reads `tests.json` beside the manifest. Use
`--fixture NAME` for one exact fixture; an unknown name fails. `--fixtures FILE`
selects a different suite, with source paths relative to that file. `--evidence DIR`
reserves a fresh directory for receipts; the default is `build/tests-<id>` beside
the project. The caller's working directory continues to resolve reader includes.
The runner requires Python 3 and a Lang source installation, like scaffolding.

```bash
./out/lang_next test --project example/shipping/project.lang-project
./out/lang_next test --project example/shipping/project.lang-project --fixture policy
```

The small format is versioned JSON. Each fixture has a unique `name`, `source`,
and either `runs` or `diagnostic`. Positive fixtures need at least two distinct
argument lists. Every run asserts exact UTF-8 stdout, stderr and process exit:

```json
{"version":1,"fixtures":[{"name":"policy","source":"policy.shipping",
 "runs":[{"args":["99"],"stdout":"10\n","stderr":"","exit":0},
         {"args":["100"],"stdout":"0\n","stderr":"","exit":0}]}]}
```

A negative instead uses `"diagnostic":{"label":"shipping","line":1,"column":21,
"message_contains":"duplicate setting"}`. These are structured assertions against
located reader-toolkit diagnostics (`label:line:column: message`); line/column
are one-based byte positions. They do not require the compiler's separate JSON
transport. Negative fixtures require exit 1 at the reader phase and no AST output.
Toolchain, manifest, validation, LLVM and link failures cannot satisfy negatives.

All fixtures use the invoking compiler's native build driver. On the supported
Linux host, the compiler identifies its running image through `/proc/self/exe`;
procfs must be available. Shell command caches, a changed `PATH`, caller-supplied
`argv[0]` and `LANG_ROOT` cannot select a different compiler for these fixtures.
Positive builds
must publish an ELF executable after reader, shared-AST validation, LLVM emission,
object compilation and native link all succeed. A failed compile or link fails
the fixture. Any wrong output, exit or diagnostic makes the runner exit 1.
Receipts include commands, stdout/stderr, exits, per-phase exits and wall times, runtime
wall/CPU times, compiler/reader/runtime/source SHA-256 identities, the project
input digest (including dependencies), toolchain/linker identities and tool version.
Readers are trusted native code; command timeouts are 120 seconds per fixture
subprocess. Timings measure machine work. `LANG_TEST_TIMINGS=1` enables the native
driver's phase timing records; normal builds keep their existing output.

New language projects include `tests.json`. Change the inclusive threshold
`free_over` or fee `base` in `policy.NAME`, then rerun to see an expected failure;
update expectations when that change is intended. The older `cases.json` and
`check.py` remain available for minted compilers. Project tests do not invoke the
product-wide suite. Replay this fragment with
`python3 -B test/reader_author/project_tests.py --case oracle`, or
`env JOBS=2 VERIFY_CASE=project-tests make verify`. Plain `make verify` retains
integration suites and fixed points.

## Export a local compiler kit

Build the current committed sources with `make init` and `make build`, then run:

```bash
LANGBE=llvm LANGOS=linux ./out/lang_next package --project example/shipping/project.lang-project --metadata example/shipping/package.json -o ../shipping-kit.tar.gz
```

This creates one local archive and refuses an occupied destination. It never
installs, publishes or uploads. Packaging requires the matching standard compiler
build receipt in `out/build-receipt.json`; changed compiler/source hashes fail.
Only the existing Linux x86-64 LLVM profile is supported. Python 3, Clang, the
system linker, `ldd` and `getconf` are required on the packaging host.

The metadata JSON has `schema: 1`, a nonempty `runtime_contract` string, and a
`licenses` list. Each notice has `component` and `file`; compiler, reader and
runtime must each be covered. Notice paths resolve beside the metadata file.
For a language with no runtime, use an explicit contract stating that choice
and a runtime notice explaining it. Missing metadata, empty notices or missing
notice files fail before minting. The shipping example includes a complete
[metadata file](../example/shipping/package.json).

The archive contains `kit/bin/compiler`, the project entry as an example, selected
runtime sources and contract, license notices, `README.md`, `kit.py` and
`receipt.json`. Runtime AST is embedded in the compiler; retained runtime source
is for inspection, with transitive source hashes in the receipt. This export is
a ready compiler, not an editable frontend SDK. The compiler's existing trusted
native reader contract applies. OS/architecture, libc, actual `ldd` observations,
shared-library hashes, tool paths/hashes/versions, resolved project input hashes,
compiler build receipt and exact mint/build commands are recorded. It describes
a dynamically linked compiler and target runtime, with no static/runtime-free
claim and no cross-host ABI compatibility promise. System libraries are not
bundled; the recipient supplies the recorded host profile, Python 3 for the
verifier and, for native mode, Clang/linker and libc development files.

After extracting under a fresh directory, from inside `kit/`:

```bash
python3 kit.py verify
mkdir ../kit-output
PATH=/nonexistent /usr/bin/python3 kit.py llvm --output ../kit-output/policy.ll
python3 kit.py native --clang /absolute/path/to/clang --output ../kit-output/shipping
../kit-output/shipping 99
../kit-output/shipping 100
```

The shipping example prints `10` and `0`. The kit README records the packaging
host's exact Clang path; select a suitable absolute path on the recipient host.
Outputs must be outside the kit so its inventory stays immutable. `kit.py` checks
all bundled hashes, required runtime metadata and notices before invoking the
compiler. A changed or missing artifact fails; this integrity receipt is not a
signature against a malicious distributor. Direct binary invocation bypasses
the verifier. IR emission uses no toolchain or original source roots; native
mode requires explicit `--clang`, the system linker on `PATH`, and uses the shared
`-O0` native host driver.

Run only `python3 -B test/reader_author/package.py --case relocated`, or
`env JOBS=2 VERIFY_CASE=package make verify`. This fragment uses bubblewrap to
mount the extracted kit and system tools/libraries while excluding both original
source roots and caches. It compares IR bytes and runtime results with the
unbundled shipping fixture, and exercises missing metadata, every bundled hash,
explicit Clang selection and an input changed during packaging. Commands, input
and tool hashes, stdout, stderr, exits, archive and receipt stay outside the
checkout under `../evidence/`. All expectations fail the runner on mismatch.
