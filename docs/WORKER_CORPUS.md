# Worker confinement and cancellation corpus

Run `make test-worker-confinement WORKER_EVIDENCE_DIR=/absolute/evidence/directory`.
This runs the corpus and adversarial observer regressions; `make test-all` also
includes that target. The harness currently needs Linux inotify, procfs and
child subreaping; missing observer support fails loudly, with no skip.
The output directory must be outside the checkout. Every invocation retains a
new directory containing receipts and raw bounded stdout/stderr. No external
services, user data or production endpoints are used. The network control
connects only to a disposable loopback listener owned by the harness.

This prepares an execution contract, not an isolation implementation. The
`policy-model` is a cooperative test double: its authority checks are trivially
bypassable by arbitrary native code. Its supervisor and publication state
machine are reference models, not compiler services. The `permissive` fake host
must fail the same independent JSON oracle. `native-unavailable` must exit 1,
report `isolation-unavailable` on every row, launch nothing and publish nothing.
It never skips or selects trusted-native. The default command passes only when
the model passes and both negative controls fail in the expected ways; that
successful harness test does not turn the native admission failure into a pass.
All receipts keep qualification and production admission false.

## C context and grants

`test/confinement/worker_cases.json` freezes the expected outcomes separately
from the worker and host models. `C` is the compiler-owned request context in
this test contract. It contains request/generation identity, named immutable
inputs with SHA-256, and budgets. These are proposed execution-service fields,
not fields claimed to exist in today's `PhaseCompileRequest`. `C_accounts`
and `granted_inputs` on every row give a machine-readable mapping. Frontends
cannot enlarge the accounts or grant ambient authority.

| Cases | C account / granted input | Independent expected outcome | Current implementation boundary |
| --- | --- | --- | --- |
| granted-input | input_bytes=64; source=`granted`, hash verified | complete, 7 copied bytes | `std/buffer.lang`: host byte limits; named execution grants remain future work |
| filesystem-read, filesystem-write, environment, network, process, inherited-descriptor | granted_inputs=[source]; processes=0; no paths, environment, sockets, children or inherited descriptors granted | authority-denied, no publication | `src/stage_worker.lang` remains trusted native with ambient authority |
| infinite-work, silent-infinite-work (both output descriptors closed) | wall_ms=500; fuel=100 reserved | deadline-exceeded, no publication | test supervisor enforces wall time; semantic fuel is unimplemented, not established by this case |
| stdout-overflow, stderr-overflow, combined-output-overflow | output_bytes=1024 shared across both streams | output-limit, no prefix publication | `std/buffer.lang` and `src/stage_worker.lang` bound legacy stdout; this combined account is a future service obligation |
| exact-output | output_bytes=1024 | complete, exactly 1024 bytes | tests the limit's inclusive boundary independently of overflow |
| cancel-before-start, cancel-running | cancellation, wall_ms | cancelled, zero publication, no launch / leader and descendants waited for, process group empty | future service; running case waits for a pipe handshake before cancellation |
| stale-request, superseded-generation | request_id, generation, publication | stale-response, zero publication | deterministic test model; no result publication scheduler exists in production |
| cancel-before-publication | cancellation, publication | cancelled despite successful worker completion | cancellation is checked at commit, not just at launch |
| partial-failure | publication | worker-failed, zero publication despite buffered bytes | legacy adapter already refuses nonzero worker exits; this is a model of the future commit rule |
| current-response | request_id, generation, publication | complete, 7 bytes | positive control proves the publication model can publish |

The allocation_bytes=1 MiB account is reserved context, not a tested worker
memory guarantee. Today's compiler has cumulative `phase_budget_limit` and
`phase_work_limit` in `std/buffer.lang`; they account for host storage/structural
operations, not arbitrary native reader allocation or instructions. This corpus
does not qualify memory containment, instruction fuel, descendant escape,
filesystem race resistance, cross-platform launchers or production admission.
The existing `test/run_confinement.py` remains a separate feasibility spike;
supported Wasm authority imports likewise do not establish cancellation/fuel.

## Bounds and oracle

The outer watchdog is independent of the host double: 3 seconds per live
worker, at most 8192 captured bytes plus one 2048-byte read, a single child for
the process control, and a fresh process group terminated on every completion
or failure. The watchdog remains active after both output streams reach EOF.
Watchdog/output-cap outcomes fail the oracle; they are never
accepted as confinement or host deadlines. Policy deadlines are 500 ms. Total
output counts stdout plus stderr, including diagnostic bytes. Only complete
successful results may publish. Each live worker leader is waited for, even
when cancelled or over budget. The Linux supervisor adopts orphaned descendants,
waits for group children, and checks process-group absence after killing them.
Receipts record the leader exit, observed descendant PIDs, waited-for descendant
PIDs and `group_empty`; rows fail if cleanup leaves a group behind. Model-only
rows use `reaped: null` because no process was launched. The permissive double
deliberately ignores the
host deadline/cancellation and output/publication rules while the independent
harness bounds remain active.

The six authority attacks are live in the permissive control. The harness
creates the private fixture, random environment canary, inherited open file
description and loopback listener. It decides outcomes from these observations,
never from a worker's status text:

| Attack | Harness-owned observation |
| --- | --- |
| filesystem-read | inotify IN_ACCESS events, drained before the harness hashes the fixture |
| filesystem-write | SHA-256 before and after worker cleanup |
| environment | exact random canary echoed as data, compared with the harness value |
| network | connections accepted by the disposable listener |
| process | procfs child PIDs and orphan descendants collected by waitpid |
| inherited-descriptor | offset of the shared open file description after execution |

Observed access fails even if the worker prints `authority-denied` or exits
nonzero. Completed attempts with absent effects are denied, including nonzero
exits from missing filesystem/environment inputs; signals, deadlines and output
limits alone do not prove denial. The cooperative model simply returns without
access; it has no authority to choose the observed status. The environment
probe intentionally echoes any value it obtains: this tests that fixed attack
fixture, not arbitrary code silently inspecting its environment. Likewise these
bounded instruments do not claim to detect restored writes, pread without an
offset change or descendants escaping the process group. A positive model run
is never qualification of arbitrary native code.

`test/check_worker_corpus.py` makes each live attack lie after access and
requires all six independent observers to reject it. It also runs actual
missing-input failures and mutates the oracle under normal Python, `-O` and
`PYTHONOPTIMIZE=1`; all three commands must fail. Safety checks use explicit
exceptions so optimization cannot remove them. The silent-spin corpus row
verifies the deadline after closing both pipes. The process control leaves one
fixed child for the supervisor to adopt, kill and reap. No fork bomb or host
file access is required.

Publication cases use ordered events instead of timing sleeps: deliver a
completed response after cancellation, after switching requests or after
advancing the generation. Every case has its own status and byte-count oracle.

For a future real engine, retain these expected outcomes and replace the
adapter while keeping these harness-owned observations, then add
platform/toolchain escape, allocation/fuel, process-tree and
race qualification. Do not admit agent-generated native readers based on a
passing model receipt. `docs/PHASE_HOST.md` describes the current trusted adapter.
