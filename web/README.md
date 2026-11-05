# Build the language-maker site

`web/build.sh` builds the browser artifacts and regenerates the borders,
outside-suite scoreboard, native compiler traces, and first reader tutorial.
It uses the build receipt for the selected `COMPILER`.

For a text-only refresh with an existing native compiler:

```sh
python3 web/generate_borders.py
python3 web/generate_scoreboard.py
python3 web/generate_language_maker.py --compiler ./out/lang_next
```

The scoreboard reads the last `HILLCLIMB.jsonl` clox measurement, checks it
against `SHOWCASE.json`, reads that file's per-target Lua measurements, and
uses `borders.json` to enumerate the remaining readers and targets. Capability
probes do not count toward outside-suite scores. Readers without a wired
outside suite say `not measured`; a measured zero stays zero.

Each trace input lives in `web/trace_inputs/`. The native compiler's `read`
command produces the shared AST; `--from-ast` compiles that exact AST with the
appropriate target runtime. The panel displays every function declared by the
reader AST, excluding runtime definitions. Lox retains its runtime function
model, minilisp retains boxing, and Forth lowers to integer arithmetic.
The tutorial is copied directly from the first Lang block in `docs/READERS.md`.

Focused checks:

```sh
python3 test/site_scoreboard.py
COMPILER=./out/lang_next python3 test/site_language_maker.py
node test/site_browser.mjs "$SITE_EVIDENCE_DIR"
```

The browser check uses `CHROMIUM_PATH` and `PLAYWRIGHT_MODULE`, serves only
local files, and fails on page errors, requests outside the local origin,
missing assets, or page overflow. It captures all three pages at desktop and
phone widths, plus scoreboard empty, single-row, limit and overflow states.
The two generated-content checks also run at the end of `make verify`.

A complete archive must list every shipped file and its SHA-256 in `MANIFEST`.
`web/deploy.sh ship ARCHIVE` verifies that inventory and every hash before any
SSH operation. Rehearse it only with local `ssh` and `scp` stand-ins.
