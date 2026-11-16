# Language-author path receipts

Run `python3 -B test/reader_author/path_receipt.py --case shipping` from a clean,
committed checkout. This fragment builds the current sources in a private clone,
reads the shipping project, checks pretty/compact AST and formatting idempotence,
runs the four shipping fixtures once through the native driver, and relocates a
minted compiler with only its binary and guest source and no tools in PATH.
It checks the fixture host's actual command receipts against `tests.json`,
including located negative diagnostics, native artifacts, phase exits and exact
runtime stdout/stderr/exits. Unexpected observations fail the runner.

The printed external evidence directory contains commands, stdout, stderr,
exits, complete tracked source hashes, tool hashes, native outputs and a focused
receipt. `matrix.json` contains all nine capabilities with the exact revision
and source digest on every cell. Its `README.md` panel is rendered from that
matrix. No committed status table or manually entered pass is used. Timings
describe machine work, not authoring time. The runner uses two CPUs, JOBS=2,
MAKEFLAGS=-j2 and a 2 GiB inherited address-space ceiling. It requires Linux
x86-64, libc, Clang, Python, Make and Git, with no services or root operations.

The fragment proves grammar acceptance/rejection and the shared AST. It does
not claim a shipping capture tree or production editor/debug facts from contract
fixtures. Building current sources is not either bootstrap fixed point. These
cells remain `not measured`; release readiness remains false. Full existing
suites, both LLVM and reader-AST fixed points, and the final composed author
route run only in integration. The fragment neither changes bootstrap inputs
nor regenerates browser artifacts.

For a local release decision, supply focused receipts:

```bash
python3 -B test/reader_author/path_receipt.py --case aggregate \
  --receipt /absolute/evidence/focused.json --require-release
# Equivalent local check; this does not call make release or bootstrap:
make release-check PATH_RECEIPTS="/absolute/evidence/focused.json"
```

Aggregation never executes a producer. It rejects stale revisions even when
source bytes happen to match, changed source hashes, changed tools, missing or
altered artifacts, failed command expectations, duplicate claims, unknown proof
types and gate-only receipts. A fragment check may pass while release remains
blocked; `--require-release` exits nonzero for any unmeasured cell, after writing
the matrix and panel. Empty input also writes all cells as unmeasured and blocks
release. Outputs must be outside the checkout in a fresh directory.

Focused receipt schema `lang-author-path/1` has `source` (HEAD, complete tracked
SHA-256 map and its digest), `tools`, `kind`, `producer`, `inventory`, `stages`
and `artifacts`. Artifact records contain relative `path`, `sha256` and `bytes`;
all deliverables and streams must be retained inside the receipt directory.
The whole receipt directory may be copied or moved without rewriting its logs.
Runtime commands must name their recorded native build outputs, and fixed-point
commands must name the exact retained artifact paths under one original receipt
directory. Those original paths are checked lexically; retained bytes and hashes
are checked at the receipt's current location. Relocation does not relax source,
tool, artifact, argument or exit checks.
Stages are real command records with command, cwd, environment, exit,
expected_exit, stdout and stderr. The shipping producer is this fragment, which
wraps genuine `std/project_tests.py` receipts rather than interpreting a gate
summary. Additional focused producers may provide `tree`, `editor facts` or
`self-hosting` proofs using the required roles in `ROLES` in the runner. Capture
trees must bind shipping source bytes, editor facts must bind source and core,
and self-hosting must retain equal nonempty LLVM and reader-AST pairs plus suite
and composed-route logs. Equality alone is insufficient: self-hosting also needs
`source-build` (the clean current revision's complete `make build` receipt),
`compiler-1` (that receipt's compiler, checked by hash and size), and `compiler-2`.
The ordered stages are `build-current-sources` (`make build`),
`llvm-generation-1` (compiler-1 emitting llvm-1), `link-generation-2` (the recorded
Clang tool with `-O2`, linking llvm-1 to compiler-2), and `llvm-generation-2`
(compiler-2 emitting llvm-2). Both compiler commands use `COMPILER_INPUTS` from
the validator, the build's original source directory, LLVM and the same target
environment. `reader-ast-generation-1` and `reader-ast-generation-2` use those
respective compilers on `src/lang_reader.lang --emit-expanded-ast -o` and write
the respective retained reader-AST artifacts. Generation outputs, link inputs,
compiler invocations and comparisons must name the exact retained artifact
paths in their original coordinates; comparisons follow generation. Missing
stages, unrelated equal files and stale or incomplete build inputs are rejected.
These producers still need their own integration
validation; their absence is reported, never inferred from a successful build.

Receipts are local evidence from trusted focused runners, not signatures or a
security boundary against fabricated logs. No publishing or automatic release
or queue action is performed.
