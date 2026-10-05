# Portable effects draft checkpoint

This is an **unhooked research draft**. Local effects integration has resumed
from the preserved checkpoint after the native Hamiltonian work. It is not the
default compiler implementation, has not received a full bootstrap, and is not
deployed. The new source repairs below have not yet been built or verified;
the recorded 44 executions describe the earlier pinned draft.
The Hamiltonian checkpoint `006944f` remains independent of this work.

`src/effects_lower.lang` lowers one-shot deep effects to lexical heap cells,
generated step functions, and an ordinary call/return trampoline. No native
stack is captured and no runtime source AST is interpreted. This addresses the
architectural cause of the preserved optimization/Wasm problem rather than
renaming assembly labels or disabling LLVM optimization.

The draft handles known direct effectful calls and their callers, recursion,
argument evaluation order, short-circuit operands, loops, labeled loop control,
shared outer-local cells, deep handler forwarding/shadowing, return clauses,
non-tail resume, and escaped one-shot continuations. Effect dispatch uses full
compile-time identities rather than name length. Continuations are checked
against a registry before dereferencing; invalid/reused continuations and
unhandled effects fail explicitly with exit status 3.

The initial admitted slice uses integral and pointer values with Lang's existing
i64 word ABI. Declared pointer payloads preserve their type. Floating payloads
are rejected. Compiler-owned `__eff_` and `__Eff` names are reserved when the
module uses effects. Bounds are 8192 control states per transformed function,
65536 bytes of lexical frame storage, and 32 nested frame-layout types.

## Evidence retained locally

`out/effects-portability/draft-final-matrix.json` contains exact commands,
outputs, exit codes and timings for the preserved minimal repro and all ten
original scalar effects tests (`188`, `190`–`198`). All **44 executions** passed:
native `-O0`, native `-O2`, LLVM-to-Wasm `-O2`, and direct Wasm under Node.
The minimal repro returns 42 on each route. No effects tests were skipped in
this focused matrix.

`out/browser-science/effects-review/review-summary.json` records independent
handwritten probes across those four routes. They verify transformed return
clauses, code after resume, nested forwarding, handler shadowing, recursion,
evaluation order, short-circuit behavior, stable local addresses, shared pointer
aliases, zero-argument and void effects, outward effects from clauses/return
clauses, and sequential escaped continuations. The reviewer identified and
rechecked repairs for namespace collision, pointer payload typing, invalid
continuation pointers, and unsupported declared float payloads.

The isolated harness source and binary are retained at
`out/effects-portability/lower.lang` and `out/effects-portability/lower`.
It reads an expanded AST, applies the draft pass, saves the lowered AST, and
invokes either backend. A basic reproduction is:

```sh
./out/lang test/suite/194_effect_deep_resume.lang --emit-expanded-ast -o /tmp/input.ast
./out/effects-portability/lower /tmp/input.ast /tmp/program.ll /tmp/lowered.ast
clang -O2 /tmp/program.ll -o /tmp/program
/tmp/program

./out/effects-portability/lower /tmp/input.ast /tmp/program.wasm /tmp/lowered.ast wasm
node test/wasm_host.js /tmp/program.wasm
```

The LLVM-to-Wasm runs use the installed Homebrew LLVM clang, because Apple's
clang lacks that target. Harness compilation and these bounded checks do not
establish bootstrap fixed points or aggregate compiler acceptance.

## Remaining integration and correctness gates

- Unverified source repairs add checked, aligned aggregate frame layout,
  aggregate copies and stable addresses, actual parameter offsets, enum
  construction and match lowering, and pure native closure snapshots. The
  original `155_reader_full_language` reader helper and real bidirectional
  Flow reader-to-program compilation remain mandatory gates. No acceptance
  or bootstrap claim follows from these source changes.
- Unverified source repairs infer pointer-valued return-clause bindings and
  handler results, reject first-class references to known effectful functions,
  and respect lexical shadowing in call-graph marking. The independent
  pointer-return, indirect-bridge, and shadowed-name probes remain pending.
- Unverified source repairs route explicit returns across synthetic handler
  boundaries to their active lexical function, with an explicit failure for
  returns into an already completed lexical function. Active and escaped
  return probes remain pending.
- Pure lambda assignment to an explicit `fn` declaration still needs its
  original boxing convention. Actual aggregate captures need explicit
  rejection before closure construction: existing LLVM closure boxing stores
  one word per capture and an aggregate local's address could outlive the
  generated step's stack. Integral and pointer capture probes remain pending.
- Floating/aggregate effect payloads and general effectful closures remain
  outside the admitted slice. Native and direct-Wasm pure closure support are
  separate backend gates, with direct function-table support still pending.
- Runtime allocations are retained. There is no reclamation or long-run
  performance claim. The registry has linear lookup for older continuations.
- The reviewed harness predates subsequent direct-Wasm array work. A reachable
  `print_int` exposed incorrect lowering of a nil/void return into a heap-cell
  assignment. A source repair now emits such calls as expression statements;
  fresh direct-module validation and printed-output checks remain pending.
- Neither backend uses the pass by default. Native registration/emission
  reparses includes, so integration needs cached replacements consistently in
  both phases. Expression-level reader expansion also needs consideration.
  No compiler hooks, effects-suite skip changes, or bootstrap promotion were
  performed by this lane.

Proposed API: `effects_init()`, `effects_add_decl(decl)`, `effects_prepare()`,
`effects_replacement(decl)`, `effects_extra_decls()` (Vec), and
`effects_had_error`. Both backends need the same collected declaration set,
and must apply the pass before code emission/reachability/type scans.

The current default raw-assembly effects implementation remains unresolved.
This draft supplies concrete portability evidence and identified next gates;
it does not establish a completed general effects repair.
