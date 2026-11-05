# Scoped CPS effects

`LANG_EFFECTS=cps` selects the native LLVM state-machine lowering. The default
continues to emit the legacy O0 implementation. This is an opt-in implementation
of the initial tail-resuming profile in `designs/effects_lowering.md`; it does
not enable escaping, non-tail, multi-shot or cross-thread continuations.

The pass runs after declaration registration and reader expansion, before LLVM
output is opened. It closes a direct call graph over perform/handle/resume and
rewrites only the affected functions and executable reader bodies. Effect-free
functions keep their ordinary native ABI and emitter. Calling an effectful
function through a function value is refused, including passing it through a
foreign callback. Its native entry wrapper starts a synchronous dispatcher;
transformed callers enter its frame constructor directly instead.

Each activation contains a step function, next PC, caller, typed result cell,
handler chain, lexical environment and source-function owner. Expressions with
suspension are split in evaluation order; temporaries and live scalar locals
reside in the activation. Each step returns normally. Reentry starts at the
step's entry and dispatches its saved integer PC. No native stack, machine
register, block address, assembly transfer or stack switch is captured.

A handle creates a separate body activation and a prompt record. Clauses receive
fresh activations outside the matching prompt's dispatch chain. Their lexical
environments reference the owner's cells. A perform searches the current chain
by resolved declaration ID every time; a missing match fails with `E_UNHANDLED`.
A tail resume checks active-clause authority and one-shot state, consumes the
clause, and selects its captured activation and reply cell. Continuations may
only occur as their own clause's tail resume operand; copying, storing or
forwarding one is refused before publishing IR.

Normal body completion runs the return clause once outside the prompt.
Clause completion abandons the capture and bypasses the return clause. Source
return retains its real function owner. Break and continue retain their lexical
loop owner, including labels across synthetic body/clause boundaries. These
exits abandon the intervening paths before selecting their target. The runtime
owns explicit records through a per-invocation list: completed calls, consumed
clauses, closed prompts and abandoned paths are reclaimed as they finish; the
driver disposes any remaining records at its synchronous boundary. Language
resource destructors and asynchronous cleanup are outside this profile.

Current supported values are integer/pointer scalar function cells and
zero/one-argument effects with i64 payload/reply. Aggregate and closure locals
can remain in a native region if no reference leaves that region across a
suspension. Aggregate parameters/returns, floating CPS cells, suspending
aggregate initializers, suspending assignment targets, and unsupported
suspending expression forms are diagnosed. Taking a frame local's address is
conservatively refused because the pass does not prove escaping alias lifetimes.
This includes addresses derived through aggregate indexing/fields and aggregate
values that could decay into pointers; reading an aggregate element within its
native region remains supported. Split expressions retain their integer/pointer
types, including nested arithmetic, dereferences, fields and indexing.
Return clauses must be effect-free. Direct Wasm effects remain unsupported.
Private generated runtime symbols are reserved and have no external token ABI.

The pass constructs ordinary core AST nodes; its embedded runtime is parsed
into ordinary core before emission. LLVM sees calls, returns, loads, stores and
branches. Typed pointer casts in generated functions use the compiler's existing
i64 address representation. Neither the preserved seed nor generated web
artifacts need updating to build the implementation.

Run the focused checks after `make build`:

```
COMPILER=out/lang_next LANG_EFFECTS=cps python3 -B test/run_effects_safety.py
COMPILER=out/lang_next python3 -B test/effects_cps/run.py
```

The first runner exercises all existing safety inputs at O0/O1/O2/full LTO.
The second has independent answers for state, normal return, abandonment,
unhandled entry, nested dispatch, reentry, recursive calls, lexical exits and
reader-generated flow. It also compares native IR with the flag on and off.
`test/effects_cps/compare_legacy.py` accepts `BASE_COMPILER` and compares unflagged
IR bytes from both compilers on the same complete source graph. Each runner
writes its IR, logs and results outside the checkout, configurable through its
`EFFECTS_*_EVIDENCE_DIR` environment variable.
