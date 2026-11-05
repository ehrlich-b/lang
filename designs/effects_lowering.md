# Effects lowering and activation lifetime (ED)

Decision: use **selective defunctionalized CPS/state machines**, with explicit
activation records, handler records, and a dispatcher. No assembly transfer ABI
has established the required invariants. `callbr` and `indirectbr` remain local
control-flow tools; neither is a continuation representation.

The original design baseline is lang `480e61e`; production sites below are
mapped at `4b93dcaa32c177ed827fb7597b02d8431ace2dec`. This remains an
isolated hand-lowered contract witness, not an enabled compiler feature. The initial production profile is scoped, single-task,
single-use, **tail-resuming deep handlers**. Continuations cannot escape their
handling operation, cross a foreign extent, migrate threads, or be cloned.
Heap allocation in the witness preserves transformed activations across ordinary
native returns; it does not authorize escaping continuations. A later escaping
profile requires a separate ownership and capture design.

## Flagged compiler implementation

`LANG_EFFECTS=cps` now selects a scoped production lowering over registered core
AST. See [the capability profile](../docs/EFFECTS_CPS.md) for its supported values,
refusals, ownership and focused tests. The default path retains the legacy
emitter and optimization refusal. The witness qualifications and replacement
map below record the imported design evidence; they are not an assertion that
the opt-in pass implements every later capability gate.

## Starting evidence and disposition

The inherited adapter qualification remains a FAIL. Its blocking probe called
`work(1)` before installing the handler; both adapters supplied the handler's
answer at O2. Restricting an accepted handler's contents did not prove that all
entries to the worker were handled. The earlier adapter x86-64 two-perform O2 and LTO
success remains historical evidence distinct from this state-machine witness. The prior arm64
results were object verification, not native execution.

| Prior issue | Decision and new evidence |
|---|---|
| Unhandled worker silently handled | Every `PERFORM` searches the current activation's handler chain. No match is `E_UNHANDLED` before allocating a continuation. Case 11 calls the worker before any install, at every tested pipeline. No fixture-specific admission rewrite exists. |
| Handler loads/stores or calls erased by adapter | Handler clauses are real frames executed by the dispatcher. Arithmetic, state changes and nested handled calls remain executable. The two-perform fixture increments a counter four times. No region of handler code is discarded. |
| Global handler state overwrites nesting/reentry | Explicit per-task records, separate dispatch and lifetime parents, with the captured handler chain retained through resume. Cases 4, 6 and 16. |
| Native target evidence | Historical macOS arm64 execution is supplemented by native Linux x86-64 execution from the imported runner. Receipts identify the host and tools. |
| Independent qualification | The independent design assessment (OPUS-REVIEW.md) remains **FAIL** pending fresh assessment of the revised hashes. Author checks do not satisfy that gate. Every finding is mapped below. |
| Baseline ignores nonidentity return clause | The new contract applies it once on normal completion; case 12 yields 33. Abandonment yields 77 without applying that clause. This is a deliberate semantic correction, not agreement with the broken baseline. |

## Production replacement map

At base `4b93dcaa32c177ed827fb7597b02d8431ace2dec`, replace these sites only
when the phase gates pass. This import changes no production emitter.

| Operation | Production function and current site | Replacement obligation |
|---|---|---|
| Optimization refusal guard | `llvm_emit_effect_optimization_guard`, [src/codegen_llvm.lang:76](../src/codegen_llvm.lang#L76); called by `generate_llvm` at line 8141 | Keep refusal until B closes optimization/LTO bypasses and E5 qualifies rollout; then select a versioned supported pipeline before emission. |
| Handle installation, dispatch, clause bodies and return | `llvm_emit_expr_inner`, `NODE_HANDLE_EXPR`, [line 4603](../src/codegen_llvm.lang#L4603) through 4910 | Explicit prompt/handler and clause frames; separate lifetime/dispatch parents; lexical exit targets and by-reference owner cells. |
| Perform and continuation capture | `llvm_emit_expr_inner`, `NODE_PERFORM_EXPR`, [line 4913](../src/codegen_llvm.lang#L4913) through 5071 | Replace 24-byte machine-frame capture, saved SP/FP, label address and assembly jump with spilled typed frame state and a PERFORM event returning to the dispatcher. |
| Resume | `llvm_emit_expr_inner`, `NODE_RESUME_EXPR`, [line 5074](../src/codegen_llvm.lang#L5074) | Replace continuation pointer loads, saved-frame restoration and assembly transfer with checked one-shot token consumption and a RESUME event. |
| Effect globals | `generate_llvm`, [lines 8110–8118](../src/codegen_llvm.lang#L8110) | Replace `__handler_set`, `__handler_rbp`, `__handler_rsp`, `__handler_addr`, `__effect_value`, `__continuation_ptr`, `__effect_name_ptr`, `__effect_name_len`, `__resume_value` with per-task/per-dispatcher records and typed inboxes. |

Production effects remain unsupported under optimization. The original baseline
had a reported full-LTO refusal bypass; prototype success does not repair it.
Prerequisite B must close that boundary before production enablement.

## Alternatives

The LLVM factual boundaries below were checked on 2026-10-18 using only `npx
playwright` and Playwright's bundled **headless Chromium**. URLs, browser version
and section hashes are historical provenance. The optional source snapshot tool
is retained beside the witnesses; it is separate from native qualification.

| Alternative | Saved state and LLVM successors | Lifetime, native calls and LTO | Decision |
|---|---|---|---|
| `callbr` / asm-goto | Inputs/outputs/clobbers describe one asm operation. The fallthrough successor means that operation completed normally; each indirect successor is a local destination supplied to that operation. It does not describe a new invocation entering an old function. | An assembly implementation would additionally need a complete stack/register transfer and ownership ABI. LTO can inline, split edges and change register allocation; label-address identity is not an ABI. No proof for nested calls, abandoned frames, arm64 ABI state or foreign crossings. | Reject as the general effect route. Local instruction success from the prior experiment proves a smaller property. |
| Local `blockaddress` + `indirectbr` | The address must derive from a block address; the destination list describes all possible local targets. Crossing functions or omitting a possible destination is undefined. | Does not revive a returned native activation or save SSA values, stack objects or ABI state. Inlining a whole fixture into one function is a specialization requiring complete entry/capture analysis, not general separate compilation. | Optional local dispatch optimization after lowering, never cross-function resumption. Use integer state IDs initially. |
| Specified runtime transfer | A new intrinsic or ABI would need to define suspend/transfer/resume edges and their dataflow, complete machine context, roots and unwind behavior. A normal `noreturn` call only ends the caller's CFG; it creates no resume edge. | Dedicated preserved stacks or explicit transformed frames are necessary. An ordinary call plus hidden SP/FP changes does not suffice. `returns_twice` alone does not support arbitrary continuations. A new ABI needs optimizer, LTO, exception, platform and runtime implementation evidence. | Viable separate future project; no current specification/implementation sufficient to choose it. |
| Selective CPS / state machines | Live state resides in typed explicit frames. Steps return events; the dispatcher uses ordinary calls and local switches. Every reentry begins at function entry and selects a stored PC. | Transformed frames survive step returns. Effect-free native calls retain their ABI and complete before suspension. Effectful call chains and clause bodies are transformed. LTO sees all transfers as calls/returns/stores/branches. | **Choose.** Costs frame allocation, analysis and dispatch; semantics can be tested without target stack manipulation. |

Primary contracts: [LLVM indirectbr](https://llvm.org/docs/LangRef.html#indirectbr-instruction),
[LLVM callbr](https://llvm.org/docs/LangRef.html#callbr-instruction),
[LLVM function attributes](https://llvm.org/docs/LangRef.html#function-attributes).
The chosen lowering and the following ownership rules are our design, not LLVM
guarantees. No assembly transfer implementation is claimed by these witnesses.

## Normative execution contract

An effect has a resolved declaration identity and argument/result types, never
just a string length. A handler has a dispatch parent, a lifetime parent, a
prompt/body boundary, a return clause, and effect clauses. Separating the two
parents matters when a clause installs a nested handler while its own handler
is masked. The task owns its current activation, handler records, token registry,
and error state. There are no process-global handler or resume-value cells.

1. **Ordinary effectful call:** save the caller's next PC and every value needed
   after return; allocate/initialize a callee frame linked to the caller. Return
   `CALL(callee)` to the dispatcher. Normal callee return writes the caller's typed
   inbox and selects it as current. Native machine call frames may return freely.
2. **Enter handle:** save the owner's successor and create a prompt. Execute the
   body under that prompt. The return clause runs exactly once when the body
   completes normally, outside this handler's dispatch scope. Initially it must
   be effect-free; it may have ordinary visible side effects. A clause's abort
   result bypasses the return clause. The witness uses arithmetic return clauses;
   general return-clause emission remains E's implementation obligation.
3. **Perform:** evaluate arguments in source order, spill the complete live
   state, set the next PC, then return `PERFORM(id, payload)`. Look up the nearest
   matching handler in the *current* chain, on every perform. If absent, emit
   `E_UNHANDLED`, clean up, and fail; no ambient/default reply is supplied.
4. **Clause invocation:** capture the activation segment to the matching prompt
   plus its handler chain. Allocate a fresh token. Execute the matching clause as
   a transformed frame under the matching handler's dispatch parent: the matching
   and intervening inner handlers are masked during the clause. Its lifetime
   still belongs to the matched prompt. A clause can make ordinary transformed
   calls and install reentrant handled computations. An unhandled effect in a
   clause can reach an outer handler. Nothing rewrites away its side effects.
5. **Tail resume:** evaluate the reply, validate the token and consume it before
   the transfer. Dispose the clause activation, reinstall the captured activation
   and handler chain, write the performer's inbox and dispatch its saved PC.
   Resume has no successor in that clause; code after it is unreachable *in the
   source semantics*, rather than reachable through a hidden stack jump. Inner
   handlers are reinstated even when the selected clause was in an outer prompt.
6. **Abandonment:** normal clause completion without resume (a clause's result,
   not a source `return` statement) drops the captured
   segment and all pending inner prompt/clause state, runs cleanup, and delivers
   the clause result to the matching handle's owner. Normal return, abort and
   error each invalidate relevant tokens and close prompts exactly once.
7. **Source exits:** source `return`, `break` and `continue` keep their resolved
   lexical function/loop targets when a handle body or clause is extracted into
   a synthetic frame. They are never frame-completion `RETURN` events. If an exit
   crosses a body/clause boundary, lower it to
   `LEAVE(kind, target-owner, target-state, cleanup-boundary, value)` and perform
   **abandon-then-exit** as specified below. Local loop exits that cross no such
   boundary remain ordinary local control flow. A return from a real called
   function still completes that callee, not its caller's source function.

Resolve targets and retain reader source spans **before** extracting synthetic
frames. A source return evaluates its expression exactly once before cleanup,
preserving the typed result across cleanup. Break/continue carry the resolved
loop identity (including labels); continue selects the loop's next iteration
or increment state, and break selects its successor. A synthetic clause/body
does not introduce a source function or loop. In particular, the existing flow
reader puts a user's `for` body in a `Yield` clause and appends a resume
([flow.lang:243](../example/flow/flow.lang:243),
[flow.lang:272](../example/flow/flow.lang:272)). In
`for x in count(n) { if x == 3 { return x; } }`, the return abandons the generator
and returns 3 from the containing function. It never reaches the appended resume
or code after the for/handle. Unreachable appended resumes do not make an
otherwise valid source exit a non-tail-resume diagnostic.

For an exit crossing prompts, the order is normative:

1. Evaluate the return value, then determine the exact lexical scopes/prompts
   crossed, stopping at the target scope. Validate that the target is a live
   compiler-resolved activation in this dispatcher; it cannot name a caller's
   function/loop or cross a native dispatcher host. An unresolved, escaping or
   unsupported target is a source diagnostic before object publication. A
   malformed internal exit event fails checked (`E_EXIT_TARGET` in the witness).
2. Mark crossed prompts closing and invalidate their tokens, including suspended
   nested clauses and bodies, **before** executing any cleanup. No abandoned
   continuation can resume. Prompts outside the exit boundary remain live.
3. Clean up the active clause/body path from inner scope to outer scope, then
   its captured/suspended branches from inner scope to outer scope. For nested
   pending clauses, apply that rule recursively: children before their owning
   prompt/activation, active branch before captured branch. Clean each initialized
   resource once in reverse initialization order. Close crossed prompts after
   their children, skipping their return clauses; abandon is not normal body
   completion. Retain owner storage until all clauses using it have been cleaned.
4. Execute the target activation's own exit: return cleans the remaining source
   function scopes and returns through its ordinary caller destination;
   break/continue clean only scopes left by that exit and select the target
   loop's state. Do not deliver a handle result or execute the handle's normal
   successor. An enclosing prompt not crossed by the source exit still observes
   its body's eventual normal completion in the usual way.

The hand witness's `SOURCE_RETURN/BREAK/CONTINUE` events implement this for exits
from two nested prompts to their shared lexical owner; the target cleanup
boundary is that owner's lifetime scope. Production must encode exact lexical
cleanup boundaries too, including exits that retain an outer prompt and local
block resources. [control-sources.lang](../test/effects_witness/control-sources.lang) and
[flow-exits.lang](../test/effects_witness/flow-exits.lang) preserve source inputs for E1/E4;
the C translations do not claim that the existing compiler implements this rule.

The supported resume position is tail position in the effect clause itself
(branches may end with it). Forwarding `k` to another function, invoking it inside
a non-tail expression, continuing clause code after resume, or storing it in a
closure/aggregate/global/return value is refused at the originating span. This
initial restriction is intentional and must be documented in the capability
profile. Non-tail resumption needs an additional explicit continuation for the
clause; it cannot be smuggled in through an ordinary native call.

## Saved state, ownership, and lifetime

| Object | Required preserved state / owner |
|---|---|
| Function activation | Typed next-PC, caller/return destination, current dispatch and lifetime scopes, all live locals/temporaries, parameters still live, loop state, closure captures, aggregate storage and initialized-resource cleanup state. Values used after a yield are loaded from the frame, never assumed to survive in an LLVM SSA register from a previous invocation. |
| Address-taken local | Stable frame-resident storage for the whole scoped activation. No pointer into a returning native step's `alloca` may survive. Promote derived aliases to the owning frame or refuse when the compiler cannot establish the lifetime. |
| Handler activation | Resolved effect IDs, transformed clause environment, prompt boundary, dispatch/lifetime parents, return continuation and initialized cleanup entries. Clause references to owner locals point to stable cells in the **owner's frame**, by reference; no copy on entry, perform, resume or abandonment. All body/clause/alias accesses see the same cell. |
| Continuation handle | Opaque task ID, slot/generation, prompt ownership, captured top frame and handler chain, clause authority and state. No exposed code pointer, SP, FP or caller stack address. |
| Native machine state | Nothing captured. Ordinary ABI calls save what their ABI requires while they execute. Suspension occurs only after a step has returned normally. No PAC/BTI, vector-register, stack-alignment, TLS or exception-unwind context is forged. |

By-reference owner-local capture is required even when a local's address was not
explicitly taken in source. `example/flow/test_flow.lang`'s `sum_count` updates the
enclosing `total` in its Yield clause; `sum_count(5)` must return 10, never the 0
that a by-value environment would leave in the owner. Captured cells live through
all pending clauses, with no pointer into a step's returning native alloca.
Mode 25 reads/writes the actual owner cell from both clause and resumed body.

Static affine checking limits `k` to its clause and prevents escape/copy/resume
misuse. A runtime check remains mandatory for generated code and ABI boundaries.
The permitted transitions are `fresh -> used` on resume and `fresh -> abandoned`
on abort; prompt completion retires every associated handle. While a prompt is
live, using a consumed token is `E_USED`. Using one after prompt closure is
`E_ESCAPE`. Wrong task/generation/index is `E_TOKEN`; wrong clause authority is
`E_TOKEN_SCOPE`. Check identity, bounds, generation and prompt validity **before**
dereferencing captured frame state. Reused slots require generations with checked
exhaustion. No unchecked pointer-to-freed-continuation API is allowed.

The witness's registry never reuses slots within a context. It retains tombstones
and arena records until the synchronous root computation finishes, bounds-checks
all allocations and reports `E_LIMIT`; that is sufficient for its token checks.
Task IDs are supplied explicitly. Production must supply noncolliding task IDs,
generation management, a safe context lifetime and deterministic allocation
failure. The prototype is not a secure public handle service or allocator.
In particular, it does not reclaim consumed records during a long-lived prompt.
E2 must reclaim consumed clause/top-frame records and bound steady-state memory
for at least 10^6 performs in one prompt; passing these finite arena tests is not
that gate.

The supported lifetime ends at the synchronous handle/driver operation. A token
is usable only by its currently active matching clause; it cannot be returned
for later resumption even though the activation has heap storage. No thread
migration, multi-shot copies, foreign retention, serialization, async scheduling,
or indefinite suspended-root ownership is in this profile.

Cleanup walks inner activations/resources before outer ones, once each, on normal
completion, abandonment and failure. A successful resume consumes the clause but
keeps suspended-body resources live. Generated cleanup uses per-frame initialized
bits and reverse initialization order; cleanups must be effect-free and cannot
resume. The core introduces no C++ destructor/unwind semantics. The witness
checks per-frame finalization uniqueness and an exact abort trace `4,3,2,1`;
resource-level initialization masks and cleanup code generation are future gates,
not established by an integer counter.

## Calls, selection, and foreign boundaries

Effect analysis is a fixed point over direct calls, recursion/SCCs, handler and
return-clause bodies, closures and address-taking. A caller that can propagate
an effect is transformed through the handling delimiter. Merely checking the
lexical handled region repeats the inherited bug. A worker may be called in an
unhandled region: it still performs a real dynamic search and fails explicitly.
If analysis can prove no handler exists, an earlier diagnostic is also valid.

**Dispatcher hosts and nesting:** a native-ABI lang function that contains
handled effects but is effect-free to its callers (for example suite 196's
`run_with_handler`) hosts its own synchronous dispatcher. Its native entry wrapper
creates explicit root state, runs the dispatcher, and returns the source result
normally. A top-level effectful entry likewise needs a host. Effect-propagating
calls use `CALL` in the current dispatcher instead; they cannot pass through a
native function with an outward effect summary. Unknown closure/indirect/import
summaries fail closed before selecting a native entry.

Hosts nest on the native stack when a step or native function calls another
effect-closed hosted function. Each dispatcher owns its current frame, root
boundary, and completion destination. Task identity, token registry/generations,
allocation bookkeeping, error state and `foreign_depth` are **per task**, shared
by nested dispatchers, never reset by an inner host. Native entry establishes a
task if none exists; reentry uses the current task context (an explicit context
parameter in the witness; its production accessor is an A/E2 ABI gate).
An inner root has no handler dispatch parent in the outer dispatcher. An inner
dispatcher never receives an outward perform as a supported input: analysis must
prove the host is effect-closed. If this invariant is violated at runtime, lookup
fails with `E_UNHANDLED` inside the inner root; it cannot search an outer native
host's prompts. Effects that need outer handlers must stay in one transformed
call chain and one dispatcher.

Inner completion cleans only its own records before returning normally to the
outer native caller. An inner failure unwinds through checked ordinary returns
and lets each host clean its own records; no native stack jump is introduced.
A token cannot be resumed or a lexical exit targeted across host boundaries.
Nested callbacks retain the task's nonzero foreign depth: even an inner locally
handled perform/resume is `E_FOREIGN_SUSPEND`. Native dispatcher nesting alone
does not add foreign depth. Modes 26-28 exercise successful nesting, isolated
lookup with an outer handler present, and foreign-depth inheritance.

An effectful callable uses an explicit versioned descriptor: initializer/entry,
step function, frame layout/destructor and parameter/result signature identity.
Caller and callee agree on this convention before the indirect call. Mixed
ordinary/effectful function-pointer sets require a statically typed adapter or a
diagnostic, never a pointer cast or an optimistic ordinary call. Unknown effect
summaries in separate compilation fail closed; summaries and ABI identity travel
with exports, imports and LTO inputs. A runtime descriptor check supplements
static typing; it cannot make an arbitrary forged C pointer safe. The witness
selects between two valid descriptors in a separate C translation unit, and
rejects a well-formed descriptor object with an unsupported ABI version.

Proven effect-free lang functions and cooperative foreign leaf functions use
ordinary native calls. The wrapper increments the task's foreign depth before
calling foreign code and restores it on normal return; a perform after the call
is supported. **Any** attempt to suspend or resume while foreign depth is nonzero
is `E_FOREIGN_SUSPEND`, even under a callback-local handler in this first profile.
Exported callback shims always enter this barrier; a foreign caller cannot evade
it by entering through a public effectful symbol. Effectful step ABI entries are
internal/private to cooperating generated modules. A synchronous callback that
does not suspend remains possible.

An arbitrary foreign routine, foreign frame, `lua_pcall`, libc callback, C++
exception, `longjmp` across a wrapper, signal-handler reentry or uncooperative
coroutine cannot preserve this barrier automatically. Such crossings are outside
the profile and must be refused by the declared import/export contract; the
runtime check handles cooperative entry, not adversarial stack introspection.
The witness has a real C callback while the barrier is active and a separate
native-leaf-then-perform case. It does not implement Lua interop or a production
callback shim generator.

C `setjmp` is a separate C ABI obligation in A. It needs an appropriate
`returns_twice` declaration/call model, correct `longjmp` semantics, restrictions
on modified nonvolatile automatic locals, and dedicated optimized/LTO tests.
Neither the state-machine dispatcher nor the legacy effects assembly supplies
that contract. Lua's errors/coroutines do not become lang effects.

## Every LLVM successor

[contract.ll](../test/effects_witness/contract.ll) is the minimal hand-written IR witness.
`two_ticks` returns PERFORM twice and DONE once. The caller calls it again each
time; it never branches into an activation that returned.

| Lowered operation | LLVM control/data-flow meaning |
|---|---|
| Step entry switch | State 0 is initial execution; each other case is a specific saved continuation PC for **this frame**. Default returns a checked invalid-state error. All destinations belong to this invocation of the same step function. |
| Perform event | Frame stores and payload stores precede an ordinary `ret` to the dispatcher. There is no local fallthrough into the post-perform state. Reentry later starts at step entry through an ordinary call. |
| Dispatcher event switch | CALL selects a new callee; ENTER creates a prompt; PERFORM selects a clause or error; RESUME restores explicit state; RETURN selects caller/prompt completion or finishes. Every arm rejoins the local dispatch loop or returns normally. |
| Clause tail resume | Returns a RESUME event. Only the dispatcher mutates token state and selects the captured frame. There is no native backedge into a different LLVM function. |
| Source return / break / continue | Returns a LEAVE event carrying a resolved target and saved value. Checked local dispatcher branches abandon/clean crossed scopes, then complete the owner or select its loop PC. No branch enters a returned native activation; no normal clause-completion edge substitutes for the source exit. |
| Native/indirect step call | Returns once to its ordinary local successor. The step's returned event determines subsequent dispatch. The call result and frame writes carry state across that edge. |
| Error/cleanup | Normal checked branches into cleanup and failure return. The witness does not mark malformed PCs, unhandled effects, stale tokens or unsupported descriptors as LLVM `unreachable`. A production process-exit helper may end with `unreachable` only after an actual specified `noreturn` call. |

The emitted C witness uses ABI aggregate returns for events, which clang may
lower with `sret`; this is an implementation detail of this C prototype. E should
use the shared core's resolved layout/call contract from A, preferably an explicit
output pointer plus a status code until aggregate ABI work is qualified.

## Optimization, targets, and exact evidence scope

Run `python3 -B test/effects_witness/run.py` from the repository root on native
Linux x86-64 (clang/opt/llvm-as and lld) or macOS arm64 (matching LLVM and libLTO). Every command runs under `nice -n 10`. Output defaults to the repository's
sibling `evidence/` directory, with build artifacts in sibling
`scratch/effects-witness/`; both must be outside the checkout. Override these
with `EFFECTS_EVIDENCE_DIR` and `EFFECTS_BUILD_DIR` when necessary.

`evidence/witness.json`, `evidence/commands.json` and `evidence/summary.tsv`
contain per-case outputs/exit codes, tool versions, source hashes, committed
HEAD and build commands. Linux uses LLVM 19.1.7 with lld full LTO: all four
translation units are checked as bitcode, and the retained linker-generated
object must be native ELF. macOS uses matching libLTO and retains its native
LTO object. Neither route falls back to ordinary native linkage.

The original 204 native checks are preserved. The imported runner expands the
minimal IR and outward-clause checks across the required profiles, giving 219
checks: 33 semantic cases in six profiles (198), minimal IR in seven (7), and
two outward-clause cases in seven (14). Profiles are O0/O1/O2, full-LTO O2,
explicit `opt -passes=default<O2> -verify-each`, and ASan/UBSan O1; the original
O2-sanitized auxiliary checks are retained too. The explicit optimizer pipeline
checks all four main translation units and minimal IR; the auxiliary outward
probe in that profile is compiled by clang O2. The pipeline emits input without
`optnone`, verifies every optimizer pass, and rejects hidden assembly,
blockaddress/indirectbr/callbr, returns-twice or optnone in selected-route IR.
The target-neutral `contract.ll` receives native clang data layout before
explicit optimization; optimizing it without that layout folds i64 field
offsets using incompatible generic alignment. No global optimization
suppression or volatile fake edge is used.

| Fixture family | Required observation in this witness |
|---|---|
| Two performs, changed inputs | 500491 and 621238; four real clause side effects each. Arithmetic agrees with the inherited fixture, without using the broken baseline as the sole oracle. |
| Two sequential handlers | First result 2268; second distinct reply bias gives 2676, encoded as 22682676. Eight clause side effects. |
| Nested / reentrant | 254 for nested return transformation; 129 when a clause handles a fresh nested computation before resuming its captured body. |
| Captured inner handler reinstatement | Effect 1 crosses an inner Effect 2 prompt, resumes under it, then Effect 2 is handled there; result 330. |
| Multiple effectful functions | 1016 across explicit caller frames; no native frame revival. |
| Indirect calls | Separate-unit selection of both WORK and STEP, six additional positive/negative/zero seeds with independent arithmetic expectations, plus unsupported ABI refusal. |
| Escape / reuse / unhandled | `E_ESCAPE`, `E_USED` while the prompt is still live, and `E_UNHANDLED` before handler installation. |
| Abandon / normal return | Exact drop trace 4,3,2,1, result 77 on abort; nonidentity normal return clause gives 33. |
| Native / foreign | Native call completes, then effect returns 24; actual callback suspension attempt returns `E_FOREIGN_SUSPEND`. |
| Source exits across two prompts | Clause/body return both yield 41, break yields 101, continue yields 410; no 9000 fallthrough sentinel or crossed return clause runs. Exact drop traces and token retirement checked. |
| Flow reader and owner capture | For-body return yields 3 after four yields and abandons its token; `sum_count(5)` yields 10 from a shared owner cell, visible on each generator resume. Direct Python loop/sum oracles are independent of frame dispatch. |
| Native dispatcher hosting | Native inner hosted handler returns normally, preserving the outer prompt (165); a missing inner handler is `E_UNHANDLED` despite an outer match; foreign depth remains active in an inner hosted handler. |

These are **hand-lowered** C and LLVM witnesses, not automatically translated lang
programs. They establish a runnable contract on the recorded native host, not soundness of an
effect-analysis pass, a complete ABI, unbounded memory management, destructor
generation, all lang effects syntax, a bootstrap fixed point, or production runtime
qualification. No bootstrap or full compiler suite was needed for unchanged
production code, and none is reported as run. The inherited suite receipts retain
their historical status. E must test the actual compiler path on both platforms.
Author checks are historical evidence; independent design qualification remains
FAIL pending a fresh assessment of the corrected artifacts.

Wasm can encode explicit frames, integer states and dispatch in linear memory
using structured blocks/loops; it requires no native stack switching. This is an
architectural consequence of the chosen representation, **not Wasm evidence**.
The current Wasm effects refusal stays. A separate experimental implementation
must pass direct-Wasm and LLVM-to-Wasm runtime/cleanup/ABI tests before enablement.
The frozen assembly backend remains unsupported for the new effects profile.

Only the listed pipelines are qualified by this witness. ThinLTO, custom pass
lists, other clang/LLVM releases, sanitizers outside ASan/UBSan, thread migration,
exceptions through FFI and different native targets are unqualified. Production
must reject unsupported mode combinations in compiler/driver preflight before
publishing an object; an assembly optimization detector is insufficient.

## Implementation boundary

[effects_phases.json](effects_phases.json) defines the handoff to
`lang-shared-effects-lowering`. ED review and A's resolved native call/layout
contract are prerequisites. B's refusal repair remains a prerequisite for any
safe optimization rollout. Feature-off code and the preserved bootstrap seed
remain unchanged until the appropriate gate. Never promote new bootstrap roots
or relax refusal merely because these prototypes pass. The final native rollout
requires real compiler-generated fixtures, fresh LLVM/AST fixed points, existing
LLVM/direct-Wasm/Wasm suites, diagnostic tests and independent review on both
native architectures.

## Design assessment findings and resolution

This table covers the blocking finding and all eight non-blocking findings in
OPUS-REVIEW.md. “Deferred” names an explicit production gate, not a passing
witness claim. Independent qualification remains pending.

| Finding | Resolution / implementation boundary | Proving witness or mandatory gate |
|---|---|---|
| Blocking 1: source return/break/continue became synthetic frame completion | Resolved in the normative abandon-then-exit contract: retain lexical targets, evaluate once, invalidate tokens before cleanup, clean active then captured branches, skip crossed return clauses and normal successors. | `control.c` / `control-sources.lang`, modes 18–23: 41/41/101/410/101/410 and exact cleanup traces; `flow-exits.lang`, mode 24: early return 3. Actual source compilation and partial-prompt/lexical-resource cleanup remain E0/E1/E2/E4 gates. |
| Non-blocking 1: author checks mislabeled independent PASS | Corrected qualification status to FAIL/pending; no independent PASS is claimed. | `effects_phases.json` dependency ED and `independent_review.implementation_admitted=false`; no runtime witness can establish independence. |
| Non-blocking 2: owner-local capture unspecified | Owner locals used by clauses reside in stable owner-frame cells accessed by reference, including locals without explicit address-taking. | `control.c`, mode 25 (`flow_sum_count_by_reference`) yields 10; E1/E4 require real flow 10/88/5/6/10 and suites 190–198. |
| Non-blocking 3: native dispatcher hosts/nesting implicit | Effect-closed native entries host synchronous dispatchers. Registry/task/error/foreign depth are shared; roots/lookup/completion are isolated. Inner unhandled effects never reach outer native prompts. | `control.c`, modes 26–28: 165, E_UNHANDLED, E_FOREIGN_SUSPEND; E0/E2/E4 retain production entry/ABI obligations. |
| Non-blocking 4: arena memory grows with performs | Deliberately finite witness arena is not the production allocator. Production must reclaim consumed/completed frames and reuse generation-checked token slots. | Deferred E2: bounded live and allocated memory for N≥1000000 performs in one prompt. The 219 finite checks do not prove steady-state memory. |
| Non-blocking 5: wrong-task/index and clause-authority errors untested | Keep E_TOKEN and E_TOKEN_SCOPE distinct and explicitly outside current witness coverage; no implied coverage from reuse/escape cases. | Deferred E2 distinct wrong-task/index, wrong-clause, generation and cross-host token tests; existing modes 9/10 prove only escape/used paths. |
| Non-blocking 6: dead matching handler ends lookup | A dead match in an active chain violates the lifetime invariant; production must fail an internal invariant before frame access rather than silently treating it as no match. | Deferred E2 dead-handler-in-chain negative test; current prototype lifetime paths (modes 4/6/16/18–28) do not manufacture an invalid chain. |
| Non-blocking 7: return-clause correction changes O0 semantics | Documented intentional correction: apply once on normal completion; skip on abort/source exit. Release documentation is a rollout requirement. | Mode 12 gives 33; mode 8 abort gives 77; source-exit modes skip crossed return clauses. E5 requires release notes. |
| Non-blocking 8: real compiler work deferred | Scope retained: hand-lowered witnesses establish a contract, not effect-analysis soundness, descriptor ABI, resource cleanup generation, bootstrap or Wasm support. | E0–E6 are ordered, reversible production gates; ED/A/B are explicit prerequisites; `implementation_admitted=false`. |
