# Explicit effects machine witness

From the repository root, run `python3 -B test/effects_witness/run.py` on native
Linux x86-64 or macOS arm64 with matching clang/opt/llvm-as. Linux needs lld;
macOS needs matching libLTO. All commands run under `nice -n 10`.

The runner writes `evidence/witness.json`, `commands.json`, `summary.tsv` and
`work-emitted.txt` in the repository's sibling `evidence/` directory; builds
remain in sibling `scratch/effects-witness/`. Override `EFFECTS_EVIDENCE_DIR` and
`EFFECTS_BUILD_DIR` to select other external directories. Neither may be inside
the checkout. The JSON receipt records native host, tools, HEAD, input hashes,
per-case results and exit codes; the command log includes compiler/linker output.

`machine.c` dispatches hand-lowered frames from `fixtures.c` and `control.c`.
`foreign.c` is a separate translation unit for calls, callbacks and descriptor
selection. `contract.ll` and `ir_driver.c` form a smaller direct IR witness.
These implement the contract in [effects_lowering.md](../../designs/effects_lowering.md),
not a production compiler transformation. The source and phase plan preserve
all original semantics and diagnostics; no production feature is enabled.

There are 219 checks: 33 semantic cases across six profiles, minimal IR across
seven, and two outward-clause cases across seven. Required profiles are O0/O1/O2,
full LTO, ASan with UBSan, and explicit opt O2 with verification after each pass.
The original O2-sanitized outward regression is also preserved. All four main
translation units enter full LTO as checked bitcode, and a generated native
object must exist. The explicit optimizer pipeline covers those four units and
minimal IR; the outward auxiliary probe in that profile uses clang O2.

Checks include exact answers/errors, handler side effects, complete disposal,
exact source-exit/abandonment cleanup traces, token retirement, six independent
indirect-call seeds, by-reference owner capture and nested native dispatchers.
`control-sources.lang` and `flow-exits.lang` are specification fixtures paired
with `control.c`; this runner does not compile them with lang. E1/E4 require
actual compiler output, including flow 10/88/5/6/10 and suites 190–198.

The arena is bounded and retains records until context disposal. Production
steady-state memory, token generation/authority, partial lexical cleanup and
actual source lowering remain explicit phase gates. Independent design
qualification is pending; finite witness success does not admit implementation.

`sources.spec.cjs` and `playwright.config.cjs` preserve an optional LLVM
reference snapshot tool, separate from native execution. With an existing
Playwright setup and bundled headless Chromium, select external output paths:

```sh
EFFECTS_SOURCES_FILE=../evidence/sources.json \
EFFECTS_BROWSER_RESULTS=../scratch/browser-results \
PLAYWRIGHT_BROWSERS_PATH=/path/to/shared/browser-cache \
npx --no-install playwright test --config=test/effects_witness/playwright.config.cjs
```

No browser or package installation is part of the native witness run.
