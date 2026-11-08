# Rebuilding a composed Rill compiler

The test composition in `test/reader_author/fixtures/rill/bootstrap-compiler.lang`
uses the complete compiler root list from `compiler-closure.json`. It replaces
`compiler_readers_none.lang` with a test composition that registers the Rill
reader through the existing embedded-reader interface. No dialect rule is added
to the compiler core. Rill remains a keyword dialect of Lang with shared
semantics; this is not an independent compiler implementation.

Run the local fragment from a committed repository root:

```sh
JOBS=2 python3 -B test/reader_author/rill_bootstrap.py --case module
JOBS=2 VERIFY_CASE=rill-bootstrap make verify
```

The runner clones the committed candidate, builds the initial Lang host and
builds the seed composition from its explicitly recorded Lang sources. The source exporter packages the compiler and
Rill reader as ordinary Rill modules with dependency boundaries. The seed
compiles that package to `compiler-stage1.ll`; Clang links `rill-stage1`.
Stage 1 compiles that exact same package to `compiler-stage2.ll`; Clang links
`rill-stage2`. Then stage 1 and stage 2 each compile the same package containing
`src/limits.lang` and a tiny observation harness. Their complete module IR must
be byte identical and each native executable must exit 16. A semantic edit
changes `LIMIT_CALL_ARGS` to 17, must change the IR, and must exit 17. A child
process exercises the actual byte-comparison assertion and must fail on that
edit. Frontend, backend and incomplete-package failures must have the expected
attribution, exit 1, and produce no LLVM output.

The local check builds and exercises complete compiler stage 2, then compares
two generations of the smallest compiler module. The module executables are
observation harnesses. A successful local run leaves compiler stage 3, the
complete compiler LLVM fixed point, reader AST fixed point and
shipping-through-both obligations pending.

Compiler rebuilds run from a separate directory containing compiler binaries
and exported Rill packages, with `PATH=/nonexistent`, no `LANG_ROOT`, and a new
cache. Original source files are never copied there. Rill packages validate all
dependency edges before publication; missing package sources cannot fall back
to Lang files. Clang is an explicit separate backend at every native link.

The shared host transports complete foreign files with byte-counted reader
bodies, preserving comments, unmatched delimiters and quotes without interpreting
them. Balanced inline reader bodies preserve slash bytes, including URLs; comments
are interpreted only by the selected reader. The boundary probe checks both forms,
malformed counts, UTF-8 byte lengths and following-token positions. The host also
terminates reader input strings and registers generated declarations through the
active backend. Logical expressions join values with LLVM phi nodes
instead of allocating a fresh stack slot on each loop iteration. The small
unoptimized probe checks nested short-circuit side effects, bounded scanning
and snapshot comparisons, and parser input boundaries. The module fragment
also verifies that expanded AST output contains actual declarations rather
than an unexpanded source-reader invocation. Missing variable names are rejected
without dereferencing a missing parser token.
All processes are sequential and inherit two-CPU affinity, JOBS=2 and a 2 GiB
address-space ceiling. No root access, OS kernel operations, bootstrap promotion,
web generation or full unchanged suites are involved.

## Complete integration recipe (pending until executed)

On a suitable integration host, from the committed repository root:

```sh
JOBS=2 python3 -B test/reader_author/rill_bootstrap.py --case integration --evidence ../evidence/rill-integration
```

The evidence directory must be new. This executes the module fragment first,
then the following additional obligations, failing on any mismatch:

1. Using compiler stage 2 from the local check, compile the same exported
   compiler/reader package to compiler stage 3, and link it with Clang. Compare complete `compiler-stage2.ll` and
   `compiler-stage3.ll` byte for byte, without normalization or omitted functions.
2. Stage 2 and stage 3 each expand the complete exported Rill reader package
   using `--emit-expanded-ast`. Compare the entire `reader-stage2.ast` and
   `reader-stage3.ast`, using the standard AST serialization. An entry-only AST or raw reader invocation is insufficient.
3. Each full compiler stage explicitly builds the actual shipping reader with
   its runtime from `example/shipping/`. This application step uses the recorded
   authored Lang reader, runtime and toolkit sources in the cloned checkout;
   it is separate from the source-free Rill compiler rebuild. Each generated
   shipping compiler compiles `policy.shipping` in isolation. Link and execute
   each program: totals 99, 100 and 120 must print 10, 0 and 0 respectively.
4. Each shipping compiler also compiles a deliberate policy edit, changing
   `free_over` from 100 to 101. The LLVM must change and total 100 must print 10.
   The original-output comparison must reject this semantic input change with
   a failing child process, rather than marking it as equivalent.

The runner retains commands, stdout, stderr, exits, CPU/wall times,
source/tool hashes, a stage manifest with compiler/input/output hashes,
isolation assumptions and machine-readable obligation status outside the
checkout. `sources-and-stages.tar.xz` retains complete source snapshots, exported
packages, manifests and LLVM/AST outputs with stable archive metadata. Native
binaries are reproducible from the recorded Clang commands and hashed inputs.
`result.json` records compiler stage 2 as passed in module mode; full fixed
points and shipping are marked passed only after integration executes successfully.

Byte equality demonstrates repeatability under this seed and Clang backend.
Both paths share compiler algorithms, parser, semantics and native backend.
This is not diverse double compilation, an independent correctness proof, or
proof that compiler stages are free of a shared trusting-trust defect. Shipping
execution and changed-input rejection add behavioral checks without changing
that limitation. Other platforms and unchanged full suites remain separate
integration work.
