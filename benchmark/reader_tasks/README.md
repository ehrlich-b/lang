# Reader create/evolve/repair corpus

This is a frozen input for a future paired comparison: 20 original tasks
(7 create, 6 evolve, 7 repair), 360 hidden cases, and matched Lang/Python
specifications and starters. It establishes no productivity or adoption result.
No model trials or user contact have taken place. Executions are unattended
checks of fixed fixtures, starters and deliberately broken responses only.

Inputs, expected outputs and fixed solutions live in an operator-owned archive
**outside this repository**, supplied through `--corpus` or
`READER_TASK_CORPUS`. `SHA256SUMS` records its SHA-256 as
`operator:corpus.json.gz`; that name is a logical identifier, not a repository
path. The archive is plain gzip, protected by access separation, not encryption.
Keep it and all evaluator outputs on the operator machine, outside participant
access. Do not publish them or send them to a model. A clone or published source
contains no answers, including in the candidate's ancestor commits.

The participant receives only an exported packet: R01–R20, public calibration,
a seeded assignment order, this protocol and a self-contained `toolkit/`.
`toolkit.json` pins the Linux x86_64 compiler binary by SHA-256 and the complete
`std/`, compiler resources in `src/`, and documentation to source commit
`8fdb5a13bde1e94c1e81103e5a68b8bdcf007b2b`. Export includes those public trees
without Git history, a copied `out/lang` executable, and the libc OS selection.
No checkout or operator files are needed. Python 3 and clang must be on PATH.
Run each Lang task's build command from that task's directory; it changes into
`../toolkit` to resolve includes. Both arms get fresh sessions with the same
packet/tool allowance. Record host Python/clang versions before a trial.
Existing `example/` packs and PUBLIC-1 are excluded from the held-out count;
`pack_exclusions.json` inventories every pack file at the pinned baseline.

From the repository root, after receiving the operator archive and the pinned
compiler (normally the existing bootstrapped `out/lang`):

```sh
export READER_TASK_CORPUS=/absolute/operator/corpus.json.gz
nice -n 10 python3 benchmark/reader_tasks/evaluate.py audit
nice -n 10 python3 benchmark/reader_tasks/evaluate.py freeze
nice -n 10 python3 benchmark/reader_tasks/evaluate.py starters --output ../starter-check-001
nice -n 10 python3 benchmark/reader_tasks/evaluate.py export --seed study-001 --output ../participant-001
nice -n 10 python3 benchmark/reader_tasks/evaluate.py dry-run --output ../fixture-run-001
nice -n 10 python3 benchmark/reader_tasks/evaluate.py controls --output ../controls-001
nice -n 10 python3 benchmark/reader_tasks/evaluate.py protocol --output ../protocol-001
```

Use `--compiler /absolute/operator/lang` if the pinned binary is stored elsewhere.
Rebuilding a different compiler requires a new toolkit pin and pre-trial freeze.
Use a new output directory for every execution; artifacts stay outside the
checkout. `dry-run.json` contains paired per-case scores, fixture preparation,
build and execution intervals, seeded order and explicit zero human review time.
Both starter and fixture builds use the exported toolkit, proving it works
without the operator checkout. `negative-controls.json` pairs correct fixtures
and wrong-span, accepted-trailing-input, wrong-output, invalid-schema, timeout,
crash, invalid-JSON and abstention controls in both languages, checking identical
per-case statuses and scores. The independent scorer uses stored typed answers;
no submitted parser or fixture generates expected outputs.

`SHA256SUMS` freezes the evaluator, protocol, README, toolkit pin, manifest,
task packets, pack inventory, calibration and external archive digest. `freeze`
checks all public bytes against their Git commit and the external archive
against its committed digest, and refuses answer archives in ancestor commits.
Record that commit ID and seed before any model trial. Changes require a new
corpus version and freeze; never edit cases after observing model results.
Valid cases are a majority, exercise default/custom comments in every task,
include UTF-8 trivia for byte spans and contain `@` inside accepted comments.
Trailing probes include identifiers, numbers and delimiters as well as `@`.

To score submissions, provide a JSON mapping every task to both `Lang` and
`Python` argv arrays, or `null` for abstention, plus a complete interval ledger
as defined in `PROTOCOL.md`. Every argv entry must be an absolute executable or
file path; use an absolute-path wrapper script when flags or inline code are
needed. Relative entries are operator errors, rejected before scoring starts.

```sh
nice -n 10 python3 benchmark/reader_tasks/evaluate.py score \
  --submission ../submission.json --ledger ../time-ledger.json \
  --seed study-001 --output ../scored-001
```

The evaluator is local, not a hostile-submission sandbox. Programs receive only
a source argument per invocation and run under resource/process-group limits.
A completed score command writes `scores.json` even for failing submissions;
read correctness there, rather than inferring it from the command's exit code.
Invalid corpus, assignment, argv or ledger fails the command. Equivalent
responses receive identical scoring in both languages, including invalid input.
