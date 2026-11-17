# Copied-value worker calls

`src/stage_call.lang` supplies `phase_host_call`, an opt-in native libc adapter
for controlled, trusted executable wrappers. It uses H's `phase_compile_hook`
and `phase_worker_buffer_hook`. `phase_legacy_worker_compile` implements the
compile/link hook for the existing frontend. The ordinary reader adapter and
its text protocol retain their existing behavior.

A `PhaseCallRequest` contains a host-owned compile request, copied arguments,
the exact `copied-values-v1` entry signature, the explicit `trusted-native`
profile, output target descriptor, workspace, publication path and result tag.
The compile request's target is the execution OS, checked against the host.
The output target describes what the generated module is for; it does not
select where the worker runs. The controlled tests execute native workers and
compile their generated core AST for both native and wasm32 output.

The entry ABI is an executable reading exactly one copied value through stdin
and writing exactly one copied value through stdout before exiting successfully.
The frontend wrapper owns the actual entry function and checks its argument
and return signature. Missing imports and incorrect calls fail compilation or
linking. The host validates the wire signature before emission and the result
tag before publication. There is no native function-address calling API.
Wrappers are explicit closed source, not implicit capture of a caller's scope;
this trusted adapter still permits explicit includes and ambient resources.

Values use little-endian u32 tag and u32 payload length, followed by exact
payload bytes. Tags 1/2, 3/4, 5/6, 7/8 denote signed/unsigned 8-, 16-, 32-,
64-bit integers respectively. Tag 9 is a one-byte canonical bool, 10 arbitrary
bytes (including NUL), 11 UTF-8 (including U+0000), 12 an immutable positional
record (u32 field count followed by complete child values), 13 AST using H's
v1 frame and host-granted origin. A positional record's field order is its
schema; this tranche supplies no nominal record/type identity system.
All lengths must match exactly. Widths, bool range, UTF-8, AST shape/origin,
record lengths/count/depth, byte and work budgets are checked before returning
an owned copy. No pointers are serialized. Host and worker share no mutable
value storage; callers must treat returned record bytes as immutable values.
Unknown tags, pointers, closures, floats, lists, mutable objects, descriptors
and nominal symbol/type IDs are refused, never passed through opaquely.

Each call creates an exclusive attempt directory beneath an existing private
workspace, forks the compile hook, and execs the resulting unique executable.
The parent never accumulates backend or worker globals across calls. No artifact
cache hit or fallback can execute a prior attempt after a failed rebuild.
A successful worker's entire stdout is captured with exact byte length; stderr
stays on stderr. The host validates and copies the result, writes a pending file,
checks writes/close and atomically renames it to the requested publication path.
The workspace and publication destination must share a filesystem. Two processes
can publish there: readers see one complete response, and the last completed
rename wins. Invocation results remain request-local. Failed attempts do not
replace an earlier successful publication. All attempt artifacts are retained
for inspection; publication guarantees visibility, not power-loss durability.
This interface serializes calls per host process; native threads are unsupported.

## Remaining W and C obligations

This is an explicit trusted-native primitive. Fork/exec isolation is not
confinement. Every other profile, including untrusted, is refused before a
compile hook runs. The host-owned profile field is an authorization decision,
not an untrusted wire field. C confinement remains a separate prerequisite
before admitting untrusted native execution. No sandbox claim follows from
this adapter or the generated wasm output tests.

Remaining W obligations include closed validated core admission and full entry
schema checks independent of a trusted frontend wrapper, semantic AST checking
before publishing (currently shape/origin are checked and the consuming compiler
checks semantics), resource/import digest admission, nominal IDs, canonical
argument/result caching, target/ABI capability descriptors, phase scheduling,
deadlines, cancellation, fuel, allocation/output supervision across the process
tree, and bounded diagnostics. Compiler/linker tools and explicit includes are
not hermetic. A trusted worker can hang or exercise ambient authority. These
limits must be implemented and qualified before introducing an untrusted profile.

Run `COMPILER=out/lang_next python3 test/run_worker_calls.py`. Use
`WORKER_EVIDENCE` to select a parent directory for retained artifacts. Each run
creates a fresh subdirectory, including failure artifacts and an atomic
publication observer receipt. `--acceptance A1` through `A4` select focused
checks; compiling the real H test host is always part of each selected check.

## Reader evaluation

`include "std/stage.lang"` exposes `stage_run(ast, args)`. `ast` is a closed,
serialized `(program ...)` core AST exporting
`stage_entry(args *PhaseBuffer) *PhaseBuffer`; `args` and the return use the
copied-values-v1 ABI above, including integer, bytes, text and positional record
constructors in `src/stage_values.lang`. This is separate from the legacy STG1
reader text protocol. Includes are explicit dependencies, and there is no
implicit capture of the reader's locals. The same compiler executable that
launched the reader compiles the fragment in a fresh process, with LLVM and the
native host OS selected even when the consuming program targets Wasm.
`std/stage_entry.lang` supplies the process entry and copied-byte transport.

The host passes the compiler identity and the reader invocation's source byte
span out of band. The selected source path travels separately from its logical
name, so an included file found through the resource root can be reopened by
staging without changing diagnostic names or project-local input precedence.
`LANG_STAGE_WORKSPACE` selects an existing private workspace
(or `LANG_CACHE` supplies it). Each call gets a unique compilation directory;
validated results are atomically published to a reader-process-specific file.
The returned buffer owns a copy. A failed call leaves any prior publication
intact, reports the reader's source span, and terminates that reader.

`LANG_STAGE_MAX_MS` (default 10000, maximum 3600000) bounds the entire call,
including compile, link and transport, using a monotonic clock.
`LANG_STAGE_MAX_BYTES` (default 16777216, at most `LANG_HOST_MAX_BYTES`) bounds
each AST input, copied argument and copied result. Oversized stdout is rejected
while reading, before publication. The supervisor kills the call's process
group on timeout, failure or completion, including ordinary descendants holding
pipes open. The legacy text adapter retains its previous execution behavior.

These limits apply to trusted native fragments. They do not confine ambient
filesystem/network authority, memory allocation, stderr, compiler artifacts, or
processes that deliberately escape the process group. They do not provide fuel,
cancellation by the caller, caching or untrusted admission. The broader W/C
obligations listed above still apply; reader evaluation supplies deadlines and
copied-byte supervision for this trusted API only.

`example/tiny/stage.lang` stages `answer 42`; `example/minilisp` accepts
`(stage (+ 10 32))`. Both evaluate through the shared API and emit constants.
Run `COMPILER=out/lang_next python3 -B test/stage_reader/run.py` for the three
reader clients, the 256-entry zlib CRC proof and the timeout/overrun checks.
