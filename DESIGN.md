# Reader sites and tooling contract

Status: **Q0 design**, tooling schema `reader-tooling-v1`. This specifies future
implementation requirements, not shipped compiler or LSP support. Q0 checks
contract examples; Q1–Q4 deliberately fail until their implementations exist.
The current host foundation is described in [PHASE_HOST](docs/PHASE_HOST.md).

## 1. Boundary, versions and identities

A reader returns core plus evidence about its surface language. The host owns
immutable bytes, IDs, origin grants and budgets; a frontend owns parsing,
namespaces, lookup, visibility, phases, captures and the legality of a rename.
The kernel consumes validated core and opaque identity links. It must never
learn Lang block rules, minilisp's Lisp-2 lookup, `let` ordering or name syntax.
No general language server, editor UI, formatter, sandbox, scheduler or source
type-system refactor is part of Q0.

Reuse H (the shared compiler host), rather than creating a second source store:

| Identity | Existing authority | Tooling use |
| --- | --- | --- |
| source | `PhaseSource`, `phase_source_register` | immutable exact bytes, SHA-256, host-local ID |
| origin | `PhaseOrigin`, `phase_origin_new` | include and expansion ancestry, host-granted handle |
| artifact | `phase_cache_identity` | compiler, dependencies, phase, execution target/profile, protocol/core versions |
| node origin | `stage_node_origin` | local address index only; never serialize an address |

Source/origin integers are session-local handles, not persistent semantic IDs.
A request supplies a host session token, monotonically increasing document
revision and an allowlist of source handles with exact digests. A changed file
mints a new source; an old source remains valid history but is **stale** for the
new request. Neither a path nor equal text grants cross-session authority.
Binding/scope/site/core IDs are opaque nonempty strings, unique within the
result, qualified externally by `(artifact digest, request, phase, local ID)`.
No pointer-derived spelling such as minilisp's current `__lt<address>` is an ID.
Cache keys additionally include tooling schema, frontend digest, source digest,
phase, target/ABI/options and every imported binding interface digest. Mtime,
URI and worker addresses cannot establish a hit.

### Transport

Do not change the legacy AST bytes or overload staging wire v1's reserved word.
The existing v1 frame is exactly four little-endian u32 fields `(1, ast_bytes,
granted_origin, 0)` followed by the complete AST. `phase_wire_decode` continues
to reject trailing bytes; JSON cannot be appended to that frame.

Tooling is a negotiated sidecar in the staging request/response artifact list
reserved in [CORE_WIRE](docs/CORE_WIRE.md). Its record is `u32le schema=1,
u32le json_bytes, json_bytes of UTF-8 JSON`, with no trailing bytes. AST remains
a separately length-framed v1 artifact. A response binds both artifact SHA-256s
to the same request, granted origin, core version and frontend identity; accept
both atomically. These sidecar and request APIs are proposed, not implemented
in `stage_wire.lang`. Reject unknown versions, duplicate JSON keys, missing or
unknown mandatory fields and unsigned integer overflow. Optional future
extensions require explicit capability negotiation. Do not sniff formats.

JSON is an inspectable encoding, not an alternative identity authority. Worker
source aliases are remapped to host-granted H handles after validation; workers
cannot register arbitrary files or forge origin parents. Fixture handles are
symbolic test grants. Goldens are decoded sidecars, not production wire frames.

## 2. Source, site, scope, binding and origin envelopes

All records live under `{schema:1, session, request, revision, phase, source,
core_sha256, sources, origins, scopes, bindings, sites, core, capabilities}`.
`source` is the primary input; a result may contain several phase roots. JSON
integers are nonnegative exact integers (never bool/float), bounded by u32 for
wire lengths/handles and by the host's smaller configured limits for offsets.
`null` represents an absent parent, binding or exact surface span.

| Record | Required fields and meaning |
| --- | --- |
| source | `id, path, sha256, bytes, slice` where slice is null or `{source,start,end}` in its immediate parent's byte space |
| origin | `id, source, start, end, include_parent, expansion_parent`; these are existing H origins |
| scope | `id, parent, phase, origin`; parent is null or an earlier scope at the same phase |
| binding | `id, name, namespace, scope, phase, declaration, generated`; declaration is a site ID or null for generated names |
| site | `id, source, start, end, name, role, binding, namespace, scope, phase, origin, core`; exact name span, role is declaration/reference/generated |
| core | `id, path, binding, origin, generated`; path is an index path in the decoded AST child tree, including list heads (index zero) |
| capabilities | `diagnostics, navigation, references, rename, reason`; booleans plus a nonempty explanation when limited |

A site uses a name-token span, never a whole call span. Start is inclusive, end
exclusive, measured in UTF-8 bytes of that immutable source, including trivia.
Both endpoints must be codepoint boundaries and `0 <= start <= end <= bytes`.
Exact named sites are nonempty and their decoded bytes equal `name`; the
surrounding expression's origin can be wider. Generated sites have null
start/end/name, no editable range, and an origin leading to their invocation.
All sites map to one or more core IDs. Many surface sites may map to one core
node; one surface name may lower to many nodes. Core paths must resolve against
the AST whose digest is bound by the envelope; no synthetic guessed paths.

A slice is itself a registered immutable H source with its own digest/ID.
Its bytes must equal `parent[start:end]`. Nested translation composes offsets:
`root_start = outer_start + inner_start + local_start`, with checked addition
at every boundary. Never flatten a relative offset using a diagnostic filename.
An origin uses the slice's own coordinates and points through expansion parents
to the invocation; includes and expansions are distinct edges. H's already
minted parent ordering prevents cycles. The host remints fixture-style aliases
into H origin handles; an envelope never authorizes its own parent graph.

A binding's declaration and every reference must agree on binding ID, namespace,
phase and spelling. Shadowing is distinct IDs, even for equal names. A scope's
parent is a containment edge, not a frontend-independent lookup algorithm.
Explicit imported interfaces carry their phase and identity; moving between
phases requires a reader-provided import mapping, never name matching. Core
captures reference the original binding; closure storage/argument temporaries
have generated bindings and cannot be offered as editable surface names.

### Admission before analysis

Validate in this order, before resolving names, analyzing core, publishing a
cache result or answering any tooling request. Failure produces a structured
host diagnostic with code, phase, request and granted origin; no partial result.

1. Bound transport/frame/payload size before allocation, reject malformed,
   truncated or trailing lengths and unsupported schemas. Reuse H's configured
   byte, allocation, work, node and depth accounts for **combined** AST/metadata.
   Defaults remain 16 MiB payload, 1 GiB allocation, 1,048,576 nodes, depth 512;
   negotiated metadata cannot increase host limits. Probe beyond exact limits;
   an oversized result with a valid AST prefix must fail.
2. Verify session/request/revision, source grants, immutable digests and AST
   digest; unknown source is `unknown-source`, history outside the request's
   current snapshot is `stale-source`. Validate UTF-8, byte counts and all slice
   relations. Split codepoint, negative, reversed or out-of-bounds spans fail
   `invalid-span`, even in unused records.
3. Check unique IDs, registered origins and authorized acyclic parent chains.
   Validate scope parents, phase consistency and uniqueness of a binding's
   declaration. Conflicting scope records fail `conflicting-scope`; cycles,
   missing parents and inconsistent site membership fail `invalid-scope`.
4. Check every site/binding/core reference, declaration/reference reciprocity,
   exact names and AST paths. Missing binding is `dangling-binding`; mismatched
   mapping or digest is `invalid-mapping`. Generated identity cannot masquerade
   as an editable declaration. Duplicate names in a scope are a reader semantic
   question; duplicate/conflicting IDs are host structural errors.
5. Only then invoke the frontend's semantic checks and kernel core verifier.
   Reject any claimed capability lacking complete required evidence. A worker
   capability bit alone never grants rename.

`test/lsp/invalid.json` lists mutations and expected rejection codes. The Q0
model exercises these generic admission rules on examples. It does not replace
production H validation, frontend binding resolution or core verification.

## 3. Frontend adapters and compatibility

The Lang adapter instruments token consumption and lowering: keep declaration
and reference name-token spans separately from expression diagnostics; mint
scope/binding IDs during the reader's own binding walk; retain phase-1 reader
bodies separately from phase-0 program code. Quoted/generated core must preserve
surface origins and explicit phase/import edges. Lowering returns core IDs and
paths while constructing nodes, including synthetic names. Byte spans must be
captured before combining files or rendering wrappers. The proposed adapter
lives beside `src/lang_reader.lang`, lexer/parser and AST emission, outside the
kernel. Q0's Lang golden covers function parameters, block shadowing, writes,
references, UTF-8 trivia and a reader body at phase 1; it does not add Unicode
identifiers to Lang's currently ASCII identifier grammar.

The minilisp adapter extends its parse/lower/emit layers beside
`example/minilisp/minilisp.lang`. `PNode.start/end` delimit syntax; a symbol
node's range is the exact name. Reader-owned binding walks distinguish function
and value namespaces (Lisp-2); `let` initializers see earlier bindings but not
the binding being initialized, matching the existing sequential lowering.
`lambda` introduces value parameters and captures outer binding IDs. Lowering
records the `lisp_*` runtime calls, parameter-destructuring lets, `__args` and
closure-holder temporary names as generated nodes, with origins at the lambda.
Do not expose runtime helpers or an address-based temporary as rename targets.
Unicode trivia in the fixture tests byte coordinates without claiming a new
identifier grammar. The nested fixture preserves two slice offsets before the
minilisp input; a local offset alone must not reach the host file.

Goldens in `test/lsp` specify desired metadata, **not output already emitted by
these adapters**. The Q0 fixtures use stable representative temporary spellings;
a future adapter compares generated identities/paths and alpha-normalizes only
unstable temporary spelling, preserving all surface names and byte ranges.

Legacy `reader name(text *u8) *u8` and raw S-expression AST remain valid. Neither
tooling negotiation nor a sidecar is required to compile. The compatibility
adapter binds `(span START END NODE)` to the invocation's H source; an unspanned
node keeps H's zero-width generated-here origin. A legacy expression span is
not proof of an exact name token or binding. Never infer bindings by scanning
AST strings or by treating equal spellings as identical.

| Evidence available | Diagnostics | Navigation/references | Rename |
| --- | --- | --- | --- |
| legacy unspanned AST | invocation fallback, marked approximate | unavailable | unavailable |
| legacy spanned AST, no bindings/map | exact expression range where provided | unavailable | unavailable |
| valid name/binding/map sidecar | exact surface names and origin chain | only complete resolved bindings | frontend-approved complete editable closure |
| generated/unmapped/incomplete binding | origin fallback or known surface diagnostics | known subset, explicitly incomplete | unavailable |

Limited responses carry `reason` (e.g. `legacy-unmapped`, `generated-name`,
`incomplete-bindings`) and cannot silently advertise full support. Unknown
capabilities fail negotiation. A legacy compile error still fails loudly.
`test/lsp/legacy.ast` and the existing reader suites guard byte compatibility;
Q4 must prove actual compilation plus these limited feature responses.

## 6. Tooling requests and editing safety

A versioned request contains `{schema, session, request, revision, sources,
phase, method, position}`; position is `(source ID, UTF-8 byte offset)`.
Methods are `capabilities`, `definition`, `references`, `hover`, `rename`.
Responses repeat the snapshot identity and contain either complete results,
explicitly limited results with a reason, or a structured error. The client
converts negotiated LSP UTF-16/UTF-8 positions using the exact H snapshot's
line index. Never reuse legacy byte-column diagnostics as UTF-16 columns.

Definition follows a site binding to its declaration; references collect that
binding's sites, not matching text. Hover text/types are frontend contributions;
unknown type information stays unknown. A generated core node can navigate its
origin chain while still having no editable name. Cross-reader navigation uses
explicit exported/imported binding identities, not a kernel language switch.

Rename asks the frontend to validate the new surface name, keyword/escaping
rules, namespace, phase and capture avoidance at every use. It requires a
complete binding/reference closure, exact surface-to-core maps and writable
current snapshots for every edit. Reject generated, legacy, unmapped,
ambiguous, partial, stale, read-only or capture-inducing requests. Return a
versioned atomic edit set `(source, digest, revision, start, end, replacement)`
sorted by source then start, nonoverlapping, with the new name in each reader's
spelling. Recheck all revisions/digests immediately before applying; a changed
file rejects the whole transaction. Never edit a slice independently: compose
to the root and deduplicate equal edits; conflicting translated edits fail.
The kernel only checks identity/shape invariants; readers decide name legality
and whether a proposed edit changes meaning.

## 7. Phased executable manifest

Every command below is a **future implementation requirement**, not a completed
design-time test. `test/run_lsp.sh` dispatches Q0–Q4; Q0 alone currently runs.
A missing fixture or unsupported/unimplemented phase exits nonzero with its
name. No successful skip, empty test discovery or fallback to Q0 is allowed.
The default phase is Q0; extra arguments and unknown phases fail.

| Phase command | Required implementation evidence |
| --- | --- |
| `test/run_lsp.sh Q0` | schema/identity agreement, validated Lang/minilisp/nested goldens, negative admission vectors and compatibility feature matrix; contract examples only |
| `test/run_lsp.sh Q1` | production envelope decoder: all invalid mutations fail before an analysis sentinel; wire short/trailing/overflow, exact and oversized byte/node/depth limits, stale revisions and cross-session grants |
| `test/run_lsp.sh Q2` | real Lang adapter output equals golden, including shadowing, phase-1 reader bodies, UTF-8 byte/LSP conversion and complete core mappings |
| `test/run_lsp.sh Q3` | real minilisp adapter equals golden, sequential let/Lisp-2 namespaces, two-level nested slices, captures and generated closure names |
| `test/run_lsp.sh Q4` | actual definition/references/hover/atomic rename; capture/stale/partial rejection; legacy AST compile unchanged and limited capability responses; no reader semantics added to kernel |

`test/lsp/phases.json` enumerates fixtures and unmet requirements. Future
implementers replace an unimplemented dispatch with a real driver; marking a
manifest status alone cannot turn a phase green. `python3 test/check_lsp_contract.py`
checks the design examples and verifies fail-fast dispatch, not those future
claims. Q1–Q4 failures are expected evidence of the Q0 boundary. They must not
be reported as completed LSP tests.

Regression requirements remain independent: bootstrap fixed points, LLVM suite
with no new skips, effects O0 correctness and loud optimized rejection, wasm
suite and publish hygiene. Q0 makes no runtime, ABI, optimization or bootstrap
changes. The host's current production wire/origin tests remain in
`test/run_phase_host.py`.
