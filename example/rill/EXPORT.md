# Compiler source export

`scripts/rill_export.py` exports the current LLVM/Linux/libc compiler inputs,
the Rill reader plus its standalone host template, and the Lang reader. The
roots and generated build inputs are declared in `compiler-closure.json`.
The fragment checks the compiler root list against the actual Makefile command.

From the repository root:

```sh
export JOBS=2 LANGBE=llvm LANGOS=linux
make init
make build
python3 -B scripts/rill_export.py --output ../compiler-rill
python3 -B test/reader_author/rill_export.py --case compiler-closure
env JOBS=2 VERIFY_CASE=rill-export make verify
```

The output directory must be new. All inputs are validated before it is created.
`modules/` mirrors the source paths with `.rill` extensions. Each module is
genuine Rill source, with keyword tokens translated and identifiers escaped
where necessary. Strings, character spellings, comments and whitespace are
copied exactly. Dependency string values stay unchanged: they identify original
source modules, and the manifest links them to their exported modules.

The three top-level `.rill` files are source packages. Each `source "path" { ... }`
section contains the corresponding complete Rill module, including its `use` and
`needs` directives. An `entry { ... }` section includes the closure roots in their
original order. Module sections are listed deterministically after dependencies;
that listing does not determine registration or emission order.

Compile a package with a minted Rill compiler, from any working directory:

```sh
out/lang_next compiler rill example/rill/rill.lang -o ../rillc
../rillc ../compiler-rill/compiler.rill -o ../compiler-rill/compiler.ll
```

The Rill frontend validates every module and dependency before supplying immutable
source slices and a parser callback to the compiler host. The existing compiler
traverses the original include/require graph, deduplicates paths and enforces
`require` visibility boundaries. Package dependencies cannot fall back to original
Lang files. The generic source-provider interface has no dialect rules. Individual
module files remain suitable for inspection and independent parsing; packages
supply the complete source closure for compilation.

`manifest.json` records source and exported SHA-256 hashes, dependency edges,
closure roots/order and complete half-open UTF-8 byte mappings. Copy spans
coalesce adjacent unchanged tokens and trivia. Keyword, escaped-identifier and
dependency keyword spans are explicit. Package module offsets and generated
section delimiters and entry directives are recorded separately. There are no timestamps or absolute paths.
The generated `std/os.lang` and `out/version_info.lang` are ordinary hashed
source inputs from the selected build, so a version change correctly changes
the export. Identical inputs produce byte-identical manifests and sources.

Rill v2 adds `needs` for `require`, `extern`, and decimal floating-point tokens
to the previous reader subset. For example, a Lang local variable named `local`
exports as `rill__local`; a name starting `rill__` receives another prefix. The
reader strips one prefix from an identifier token without changing its position.
Literal and comment contents never enter this translation.

There are no unsupported source forms in the current declared closures.
Macros/quotes, embedded reader invocations, enums/match, effects, let/in,
closures, import, `:=`, nondecimal numbers, escaped dependency paths and paths
outside the source root are blockers for future inputs. They fail with a source
path and byte offset rather than becoming Lang blocks or stored AST. The
exporter checks lexical forms and balanced delimiters; the actual Rill parser
checks grammar. Successful export alone is not a grammar-validity certificate.

The named fragment limits itself and children to two CPUs, JOBS=2 and 2 GiB.
It starts from a committed clone descended from the required reader candidate,
builds the current host once, compares parsed core for six compiler/reader
modules, and parses all three complete source packages. It lowers the complete
compiler package to LLVM and compares Lang/Rill private-call rejection, public
access and textual includes on small fixtures, with Rill compilation isolated
from original dependency files. It verifies every source-map
span and literal/comment byte, deterministic exports, unsupported-form rejection,
and failed expectations. A change to `src/limits.lang` changes only its exported
module, the affected bundles and generated LLVM, and changes an executable's
stdout from `16` to `17`. The minted Rill compiler emits that LLVM with an empty
tool PATH. Commands, stdout/stderr, exits, resource limits, source/tool hashes,
exported sources, original snapshots, selected ASTs and generated input snapshots
are retained outside the checkout. Bulky reproducible text is compressed in
`closure.tar.xz`; this is an evidence archive, not an input to the frontend.

Assumptions are Linux x86-64, Clang/LLVM/libc, repository-root dependency paths
and a trusted native reader. Source packages preserve dependency edges and
module visibility; this fragment does not certify execution of a whole compiled
compiler. Whole-compiler execution, LLVM and reader-AST
fixed points, other OS profiles and full suites remain integration work.
The fragment selector on `make verify` leaves the default integration gate intact.
