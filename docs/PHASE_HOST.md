# Compiler host foundation

The compiler host owns bytes, source identities, origin grants, dependency
identities and resource accounts. Frontends own language semantics. The host
request boundary lives in `src/phase_host.lang`; `stage_buffer`, `stage_digest`,
`stage_origin`, `stage_node_origin`, `stage_wire`, `stage_worker`, `stage_dependencies` and
`stage_legacy` implement separate mechanisms using bootstrap-compatible syntax.

`phase_compile_hook` accepts a `PhaseCompileRequest` and returns an exit status.
The legacy adapter renders the existing source wrapper, compiles in a fork with
fresh backend state and links an executable. `phase_worker_hook` accepts an
executable and exact input bytes, returning owned output or a separate failure
status. Future execution engines replace these hooks without changing parsers,
emitters, codegen or the standard core. Artifact construction is in
`stage_legacy.lang`; dependency discovery is in `stage_dependencies.lang`.
A hook must set `phase_worker_status` on failure. Neither hook may publish
partial output. The existing fixed-destination `exec_capture` adapter rejects
output that does not fit; it never returns a successful prefix.

The opt-in [copied-value call adapter](WORKER_CALLS.md) adds fresh compile/run
contexts, binary copied values and atomic result publication for controlled,
explicitly trusted wrappers. It does not change the legacy reader cache.

## Bytes and budgets

`PhaseBuffer` stores data, payload length, allocated capacity, payload limit and
source name. Capacity includes the NUL sentinel; limits exclude it. Reserve
checks subtraction before addition. Reads loop through EOF, including a probe
past an exact limit. Embedded NUL in the legacy text protocol is rejected.
File, combined source, AST emitter, AST source renderer, pretty-printer and
reader stdin/stdout paths use the same bounded storage rules.

`LANG_HOST_MAX_BYTES` sets the process's payload limit (default 16 MiB, valid
range 1 through 1 GiB). Sources and AST may grow past the former 4 MiB boundary.
The default allocation account is 1 GiB, conservatively cumulative including
replaced buffers; the work account is 16,777,216 structural operations. These
are host-owned fields, not values trusted from a worker. AST publication allows
at most 512 nested lists by default and 4,194,304 list/atom nodes.
`LANG_HOST_MAX_NODES` configures the structural limit (1 through 16,777,216).
It also bounds source tokens, emitted AST nodes and indexed node origins;
these representations count different units and whichever bound is reached
first refuses. The former fixed 1,048,576 quota protected wire parsing and
provenance storage from runaway expansion, but the Tariff scale program needs
2,999,939 textual elements, including span metadata. The new default admits
that program while preserving independent byte, depth, memory and work bounds.
Structural refusals retain their error codes and name the source, effective
limit and configuration variable. Invalid or overflowing settings refuse.
`LANG_HOST_MAX_DEPTH` configures source/AST parsing and emission together
(valid range 1 through 1024); the hard ceiling bounds recursive stack use.
Structural validation runs before recursive wire parsing. Backend semantic verification remains a
separate obligation. LLVM output now grows within the same payload/allocation
accounts instead of failing at a separate fixed 8 MiB buffer. Reader span
line/column lookup uses the immutable line index rather than rescanning every
source prefix; columns remain one-based UTF-8 byte columns.

A failure emits a versioned `(host-error ...)` record on stderr with code,
source and phase; it exits nonzero. AST stdout contains only AST. Existing
reader diagnostics keep their established byte-based line/column display.

## Sources and origins

The shared byte storage lives in `std/buffer.lang`; standard-library clients
never import a compiler-internal module. `src/stage_buffer.lang` is a compatibility
import for host clients.

The registry copies source names and UTF-8 bytes, records SHA-256 and mints
immutable source IDs. IDs are scoped to a host instance; content digests are
persistent identities. Spans are half-open UTF-8 byte ranges. Invalid UTF-8,
mid-codepoint offsets, reversed/out-of-range spans, missing sources and forged
parents are rejected. An origin stores source ID, span, include parent and
expansion parent. Parents must already exist, so provenance cannot form cycles.
Invalid UTF-8 is intentionally a hard error, including bytes in comments that
older compilers accepted. Nested source parsing restores the source binding.
Identical name/byte pairs reuse immutable records and line indexes; changed
bytes mint a fresh ID. File snapshots are indexed separately from reader slices
that share a diagnostic filename. Root inputs are captured once before wrapping, and
includes and dependency discovery share those snapshots through worker forks.
Copying node diagnostics preserves the original source ID even after the same filename is reread.

Wire v1 starts with four little-endian u32 fields: protocol version, exact AST
payload byte count, host-granted origin ID, and reserved zero. Short headers,
unknown versions, mismatched/oversized lengths, trailing bytes, missing or
ungranted origins and invalid AST structure are rejected before publication.
This is an API foundation exercised by the host probes; production legacy
workers still exchange bounded NUL-terminated text, without a v1 frame or origin
grant. Their AST shape is validated before publication. Frame length and grant
checks apply to callers of this API, not to that legacy transport.
`phase_wire_encode` and `phase_wire_decode` preserve the grant;
`phase_syntax_program` binds all generated nodes to its immutable source and
expansion parent. Registry storage never crosses the boundary as pointers.

Legacy `(span START END NODE)` syntax stays byte-compatible. The adapter binds
it to the invocation's registered source. Unspanned generated nodes get a
zero-width generated-here marker at their invocation, with the explicit parent
chain; this does not claim an exact guest range. Ordinary raw AST serialization
retains its established bytes for bootstrap fixed points; use origin envelopes
when transporting provenance. Raw AST artifacts are not origin grants.
Spanned raw AST requires `--ast-source`; missing-source and malformed raw AST errors name the AST input
file. This intentionally rejects formerly accepted spans with no source bytes.

## Dependencies and scope

SHA-256 covers exact bytes. A deterministic traversal records ordered explicit
include/require paths and their transitive content digests, with embedded
modules identified by the compiler digest. Reader artifact identity includes
wrapper/dependency closure, the executing compiler's bytes, protocol/core/cache
versions, execution target/backend, phase and execution profile. Length-prefixed
fields avoid ambiguous concatenations. Warm hits re-read the closure; mtimes
are not semantic identities. If the executing compiler cannot be identified,
artifact reuse is disabled. An identity receipt is written only after linking
succeeds. Toolchain hermeticity and concurrent atomic artifact publication are
not established by this legacy artifact cache.

## Reader specializations

Use `reader name(type *u8) *u8 cached { ... }` for a native source reader that
generates a module deterministically from the exact type descriptor bytes,
its declared source closure and the output target. The reader chooses the
descriptor format and encodes any type environment it needs in its inputs.
Declare source dependencies with `include` or `require`. A cached reader must
avoid ambient values such as files outside that closure, environment settings,
clocks and side effects. Ordinary readers keep their existing behavior.

For declaration expansions, the host combines the template identity, SHA-256
of the type descriptor bytes and the output target. Template identity includes
the reader wrapper, transitive source digests, executing compiler, native
backend, layout profile and cache protocol. `LANG_CACHE/specializations`
stores checksummed AST bytes after successful expansion and AST validation.
Each build parses the AST again and binds it to the current invocation's
origins. Partial entries and diagnostic-bearing results are excluded from
reuse. Concurrent writers publish complete entries atomically. The native
worker executable is obtained only on a miss. Expression and raw reader
requests still execute the reader normally.

The native execution profile inherits ambient authority and is trusted.
Deadlines, cancellation, confinement, semantic fuel and phase-cycle scheduling
remain separate services. The cache directory is part of the trusted build
environment. `LANG_TRACE_STAGE_WORKERS=1` reports native reader compilation
and execution starts to stderr for inspection.

The [worker attack corpus](WORKER_CORPUS.md) prepares bounded authority,
cancellation and stale-publication cases with independent expected outcomes.
Its cooperative model is test-only; native isolation remains an explicit
failing admission outcome. It does not extend the production hook's guarantees.

Run `COMPILER=out/lang_next python3 test/run_phase_host.py` for the production
boundary tests. `PHASE_HOST_EVIDENCE` selects the artifact directory. The suite
checks multi-megabyte source/emission/AST fidelity, malformed frames and shape,
UTF-8/origins, SHA-256 boundary vectors, budgets, bidirectional pipe progress,
cold/warm/same-mtime transitive dependency invalidation, and multi-megabyte
round trips, hashing and Unicode sources in unoptimized workers.
