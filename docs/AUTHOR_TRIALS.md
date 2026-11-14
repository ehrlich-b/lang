# Language author trials, protocol 2

Human authoring success is **not measured**. The executable fragment below is
an **automated replay of supplied shipping code**, not an authoring session.
Its elapsed time, zero new authored lines and successful native output say
nothing about human usability or which tool is best.

The [frozen prompts](../test/reader_author/fixtures/trial_protocol/tasks.v2.json)
specify five tasks: create a language, add syntax, change semantics, repair a
semantic error, and export a native compiler. Requirements are identical for
lang, Bison, ANTLR, Ohm and tree-sitter. Each has a public example and an explicit
[facilitator oracle](../test/reader_author/fixtures/trial_protocol/heldout/oracles.v2.json).
Positive cases specify exact stdout, stderr and exit; negative cases specify
exit, diagnostic, source location and absence of an output artifact. Inherited
cases remain mandatory, except T3 replaces the inclusive positive semantics
with exclusive ones. T5 starts from an independent correct T1 starter, so an
earlier failure does not make native export impossible to attempt.

The participant contract's `compile_diagnostics` map publishes every required
diagnostic substring and its error category; only the inputs are held out.
The fragment checks that no compile-rejection oracle requires unpublished
wording and rejects a deliberately undisclosed phrase. Protocol 2 refreezes
these clarified instructions and binds replay observations to their commands;
the task behavior and expected outputs are unchanged.

The future bar for **each tool** is four of five unfamiliar users finishing T5
within 15 elapsed minutes, at most 100 authored lines and zero compiler-core
edits. Elapsed time includes active work, waiting, docs and installation during
the task. Passing a replay never counts toward that bar. No participants have
been recruited, no human sessions exist and no comparator outcomes are claimed.

## Before any real sessions

Use five separate matched cohorts, five unfamiliar participants per tool (25
people total). Unfamiliar means fewer than two lifetime hours using the assigned
tool and no prior exposure to the study code or exact task before enrollment.
Record lifetime tool hours, language-authoring hours and prior exposure before
showing a task. Balance cohorts on language-authoring experience and general
programming experience; retain both rather than calling experienced authors
novices. Randomize tool assignment within these strata with a recorded seed.
This is a small descriptive study, not adequate evidence of a universal best tool.

Run T5 first, with its independent T1 starter, to avoid practice from T1–T4.
Then run T1–T4 in order, each with a fresh 15-minute budget. Supply a correct
previous-stage starter when a participant fails a dependency; record that help
and report these later tasks separately from uninterrupted progress. For T4
use the [same seeded duplicate-overwrite defect](../test/reader_author/fixtures/trial_protocol/repair-seed.txt)
in every tool's independently verified T3 frontend. Preserve a pre-repair
failure receipt as well as the repaired result.

Pin each tool version, dependencies, compiler/linker, machine image, starter,
repair patch and documentation snapshot by hash **before recruitment**. Preflight
all five idiomatic tool adapters against the complete shared oracle, including
the required failing T4 seed. These comparator adapters and their preflights are
future work; this fragment validates only lang's recorder and shipping path.
If a tool cannot provide the required native compiler, record a capability
failure; do not silently replace it with an interpreter or omit the native task.
ANTLR/Ohm/tree-sitter may use native packaging or an embedded runtime, but those
steps and dependencies count under exactly the same requirements as lang/Bison.
Tool-specific syntax and glue are allowed; core modifications are not.

Give each participant the complete public contract (including
`compile_diagnostics`), prompts, training examples, pinned public docs and
the appropriate starter. Keep held-out inputs, repair-seed instructions and
reference solutions in a separate evaluator workspace. Public fixture files
are reproducible test inputs, not secrets: separate workspaces are required
for a real study. An evaluator, not the author, runs the oracle. Revisions
require a new protocol version and freeze; never update a golden output to
make a submission pass. No model assistants or hidden facilitator coding in
the human cohort. Any assisted/agent study is a separately labeled cohort.

Preinstall the declared baseline toolchains equally, retaining their install
commands, versions and time as setup cost. Record extra installation during
each task as part of its elapsed time and as installation subtotals. The native
evaluation environment provides only the submitted ELF compiler, unseen source,
declared Clang/linker/libc and system libraries, without the original source
checkout, parser generator, Node, Java or Python. Run guest executables without
compiler tools in PATH. Freeze these conditions for every tool before starting.

## Record a session

`test/reader_author/trial_recorder.py` writes append-only JSONL events outside
the checkout. Start with a fresh file using `start PATH --kind human
--participant ANON_ID --tool TOOL --experience JSON --task-sha256 HASH`.
Experience JSON has `tool_hours`, `language_author_hours`, and boolean
`seen_task`. Use the SHA-256 of tasks.v2.json. Automated sessions use
`--kind automated`; unknown machine experience may be null.

Use `event PATH TYPE --data JSON` during the session:

| Type | Required data and meaning |
| --- | --- |
| state | `mode`: active/waiting; `activity`: setup/authoring/build/evaluation/installation |
| doc | `uri`, `sha256`: each doc used, including external pages or help snapshots |
| code | `path`, `sha256`, `baseline_sha256`, `authored_lines`, `generated_lines`, `compiler_core_edits`: final submitted snapshot per file |
| installation | `tool`, `status`: preinstalled/attempted/installed/failed; attach version and raw command receipt |
| error | `category`: syntax/semantics/build/runtime/oracle/installation; `message`, with raw receipt reference when available |
| receipt | `path`, `sha256`: raw command result; retain argv, cwd, environment, source/tool hashes, stdout, stderr and exit |
| finish | no data; end the timing interval, including unsuccessful/time-limited attempts |

An observer marks state changes on the same host monotonic clock. Waiting means
the author cannot proceed because a tool or install is running; docs or editing
while a build runs is active time. Do not substitute CPU time for author time.
The summary partitions elapsed time into active/waiting; installation subtotals
are a subset of those intervals and must not be added again. Record interruptions
and abandonment as errors and finish the session; do not discard failed attempts.
The small recorder has one writer per session; no concurrent appends or host
migration. It validates state, ordering, required fields and terminal events.

Count additions and changed lines relative to the frozen starter across grammar,
frontend, runtime, config and scripts. Count pasted code as authored; exclude
unchanged starter lines and separately verified tool-generated lines. Preserve
baseline/submission snapshots, patches, generated commands and hashes for an
independent attribution audit. Code events are observer attribution, not proof
of authorship. Keep deleted/replaced attempts in the raw history and record
their errors. `report PATH` computes time, latest code counts per path, docs,
installations and errors; it does not adjudicate success.

Retain every assigned participant in the denominator. Report per-tool, per-task
completion, all failures/timeouts, elapsed/active/waiting times, installation
cost, code counts, docs, prior experience and any help. Apply the T5 bar only to
independently oracle-verified human submissions whose code audit passes; missing
events or incomplete attribution are unmeasured, not successes. Human reports
remain pending independent adjudication until those checks exist.

## Run the recorder fragment

```bash
python3 -B test/reader_author/trial_protocol.py --case replay
env JOBS=2 make verify VERIFY_CASE=author-trials
```

The selector is required for this narrow fragment; plain `make verify` keeps
the integration suites and fixed points. The runner requires a clean committed
checkout descended from the export-kit base. It builds current sources in a
fresh clone, exports shippingc, compiles an unseen 7/80 policy outside that
clone, checks three runtime boundaries and syntax-independent semantic/runtime
rejections. The frozen oracle specifies the executable and every argument;
the hashed identity supplies the replay directory. Verification checks those
commands, observation names and working directories before outputs and exits.
Negative receipts include a swapped above-threshold observation with the same
stdout as the boundary, changed arguments/executable/directory and incorrect
output with the correct command. Each must fail for its expected reason, even
if the receipt says `claimed_success: true`.

The replay also checks exact synthetic recorder totals and rejects regressing
clocks, events after finish, unfinished sessions, missing human experience and
unknown events. Synthetic fixtures are labeled; measured replay time comes
from the clock and subprocesses. It runs sequentially on two inherited CPUs,
JOBS=2, with a 2 GiB address-space ceiling and a sampled aggregate RSS guard.
Command receipts record the measured peak; the guard conservatively sums shared
pages and checks every 20 ms. Linux x86-64, libc, Python, Git,
Make, Clang and a linker are assumed preinstalled. No installation is attempted.
No operating-system kernel tests, elevated permissions, full suites, fixed
points or web generation are used by this fragment.

Each invocation prints its unique `../evidence/author-trials-*` directory
(`--evidence DIR` overrides it). It contains source/tool identities, command
stdout/stderr/exits, raw and false receipts, event stream, measured session
summary and pass/fail result. The source hash map is checked again at the end.
These are local execution records, not signed adversarial attestations: someone
who rewrites all raw logs and identities can forge them. Their verifier prevents
success flags from overriding retained observations or failed expectations.
