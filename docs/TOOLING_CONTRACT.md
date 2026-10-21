# Q0 reader facts, version 1

Q0 freezes a shared interchange boundary. The compiler host checks reader facts
before `tooling_program` hands syntax to the AST parser. Readers own names and
scope policy; the host contains no Lang or minilisp syntax rules. Q0 does not
resolve names, expand phases, infer types, index references, or implement rename.
Those are Q1–Q4 and `tooling_require` rejects them as `tooling-unimplemented`.

H (`phase_host`) owns immutable source snapshots and origin IDs. Sources carry
SHA-256 of exact UTF-8 bytes. Sites use half-open **byte** offsets, never codepoint
indices, pointers, or line/column guesses. An envelope grants an explicit set of
source IDs and digests, plus a root origin. All origin ancestors must refer to
those sources. Source IDs must match the current captured file snapshot; a
reader slice with the same display name does not supersede a captured file.
Without a file snapshot, the latest registered source is current. IDs are local
to a host session: a persisted worker frame cannot grant itself source authority.

Scopes and bindings use dense IDs starting at 1 within the envelope. Scope 0 is
no parent. Parents must precede children, ruling out cycles. Each scope has a
nonnegative phase number. A binding has a scope, H origin, and UTF-8 name. Repeated
names in different scopes represent shadowing; duplicate names in one scope are
conflicting facts. A site names its source, span, scope, binding, H origin and role
(1 declaration, 2 reference). Its origin must contain its span in that same source.
Bindings must be visible through the supplied scope ancestry and in the same
phase. These are consistency checks on supplied facts, not a name resolver.
Closure names use ordinary binding records; capture uses reference sites to an
ancestor binding. Generated bindings may have no editable declaration site.

## W transport

`tooling_wire_encode` and `tooling_wire_decode` reuse W's 16-byte header: four
little-endian u32 words for protocol version (1), payload byte length, granted
H root origin ID, and discriminator. Discriminator **1** selects Q0; **0** remains
the existing AST protocol. Existing W AST decoders reject Q0 frames. No existing
reader ABI or AST grammar changes. The Q0 payload is this ordered sequence:

| Field | Representation |
| --- | --- |
| schema version, mapped | u32, u32 (version 1; mapped 0 or 1) |
| syntax | u32 byte length, exact legacy AST bytes |
| sources | u32 count; each: u32 ID, 64 ASCII SHA-256 hex bytes |
| scopes | u32 count; each: u32 ID, parent, phase |
| bindings | u32 count; each: u32 ID, scope, origin; length-prefixed UTF-8 name |
| sites | u32 count; each: u32 source, start, end, scope, binding, origin, role |

All lengths, counts, enum values, IDs and byte boundaries are checked. Trailing
bytes, embedded NUL, unknown schema/discriminator, wrong granted origin, stale
digests and oversized counts fail closed. Host byte, work and memory budgets
apply. Syntax and names use NUL-free strings; no native pointers enter the wire.
Nested reader sites stay in the enclosing source's absolute byte coordinates;
a separately registered slice can have its own source and expansion-parent
origin without changing those coordinates. The fixtures also pin slice-relative
site projections to the same binding IDs through that expansion origin.

## Capabilities and clients

`tooling_capabilities` reports `compile,Q0` only for a validated mapped envelope.
A legacy adapter uses `tooling_new(text, origin, 0)` and grants its H sources;
it supplies no scope, binding or site records and advertises
`compile,limited-tooling`. `tooling_require(legacy, 4)` rejects unmapped rename.
Existing source readers continue compiling through their unchanged string ABI.
The CLI `lang tooling capabilities` describes that legacy path. `lang tooling
Q1` through `Q4` fail explicitly as unimplemented, and `lang tooling rename`
fails because that path has no binding map. CLI Q0 requests require an envelope;
the host API is the Q0 entry point. No general reader gains mapping automatically.

`test/tooling/lang_client.py` and `minilisp_client.py` are two independent fixture
clients sharing only the W encoder and fact construction helpers. Their frozen
JSON fixtures pin identities, scope/phase structure, closure names, captures,
shadowing sites and UTF-8 byte offsets. Both drive the real reader to produce
core AST, compile and execute their enclosing source, and exchange frames with
the production Lang host decoder. They deliberately supply known fixture facts;
they are not general-purpose tooling implementations. The minilisp invocation
is nested inside Lang, with separate host and guest source identities and an
include/expansion origin chain. Mutation controls pass corrupted frames to the
pre-analysis boundary and require nonzero status, a specific diagnostic and no
handoff marker. A valid neighboring control must still pass.

Run `python3 test/run_tooling_contract.py` with a compiler built from these sources
(`COMPILER=out/lang_next` after `make build`). `--acceptance A1`, `A2`, or `A3`
selects a group. `TOOLING_EVIDENCE` keeps frames, facts, compiler output and receipts
outside the checkout. `test/check_bootstrap.py` runs the full promoting bootstrap
in a retained clone of committed HEAD; it never substitutes an older compiler
for the fixed-point check.
