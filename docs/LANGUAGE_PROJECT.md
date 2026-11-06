# One language project

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

For composing the shipping function with a second reader, see
[project export signatures](READER_EXPORTS.md). The frontend-owned catalog
describes representations and ownership; sharing native storage alone does not
make an export compatible.

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
