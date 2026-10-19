# Core, storage and compiler-host boundary

Baseline source revision: 480e61e5331ce9e8c942691d5b65440b2c2c3535.
The preserved bootstrap has its own COMMIT and PROVENANCE identities. They are
inputs, not evidence that current source equals the seed. The legacy AST reader
protocol remains **legacy-ast-v1**: UTF-8 S-expression source on stdin and a
complete program/expression AST on stdout, diagnostics on stderr. No version
field is present on that existing wire. All existing readers retain
**bootstrap-internal-v1**, including the C reader's i64 int and non-fall-through
switch. A new standard C frontend must opt into another proven ABI.

Core owns explicit operations, widths, storage and target capability checks.
Readers own source typing, promotions, inference and runtime policies. Sharing
an AST does not establish external aggregate calls, ownership, lifetime or a C
ABI. Struct returns are refused; use caller-owned output storage. Current enum
examples are internal compatibility evidence. Effects remain experimental at
O0 inside live native frames; O1/O2/full-LTO O2 must reject with the effects
message. There is no foreign-frame, escaping or multi-shot continuation claim.
Unknown operations must fail; no fallback zero is an admission mechanism.

## Audited storage profile

`LANG_LAYOUT_PROFILE=audited-slots-v1` admits struct fields consisting only of
i64, u64 or pointers. Every slot has size/alignment 8. Pair{i64,i64} therefore
has size 16, alignment 8 and offsets 0,8. Empty structs have size 0 but no
external ABI promise. Arrays, nested value structs, functions, enums, floats,
narrow and unknown types are unaudited fields and fail at registration, even
when unused. Pointers are opaque eight-byte storage slots; their pointee layout
is not thereby certified. This is a conservative admission guard, not a new
layout algorithm or a complete core verifier. It changes no legacy storage.
Omitting the variable or selecting bootstrap-internal-v1 keeps compatibility.

`test/layout_audit.lang` calls both real calculators. Two u8 fields expose the
shared size 8 / offsets 0,8 and direct-Wasm size 16 / offsets 0,8 inconsistency.
The first model can address beyond its allocation. A platform C compiler gives
size 2 / offsets 0,1; neither legacy model is a C ABI. Repair sizes and offsets
together in a later migration, with bootstrap and reader compatibility proof.

Machine address width, language pointer slot size, execution target and output
target are four independent fields. Native execution on Linux x86-64 or macOS
arm64 uses 64-bit machine addresses and eight-byte pointer slots. wasm32 uses
32-bit addresses but eight-byte language pointer slots, for both emitters.
| Output profile | Machine address bits | Pointer storage bytes | Execution target |
| --- | ---: | ---: | --- |
| llvm-linux-x86_64 | 64 | 8 | selected native compiler host |
| llvm-macos-arm64 | 64 | 8 | selected native compiler host |
| llvm-wasm32 | 32 | 8 | selected compiler host, including native |
| direct-wasm32 | 32 | 8 | selected compiler host, including native |
| x86-linux-legacy | 64 | 8 | Linux x86-64 |

A native compiler emitting wasm32 still executes on the native host. Layout
queries describe the output profile, never host sizeof. No foreign-target
program executes merely because it is an output target. Target descriptors must
include backend, OS, architecture, ABI/layout version and capabilities.

## Staging wire v1 contract (reserved; no staging execution API yet)

A future staging service must use a separate, length-framed envelope. Freeze
these obligations before admitting source execution:

* Header: protocol_version=1, core_version, request_id, phase, origin chain,
  execution profile, output target and storage ABI. Unknown versions fail closed.
* Module: closed validated core plus symbol/import digests and an explicit entry
  signature. No textual capture of caller scope. Validation precedes emission.
* Values: width/signedness-tagged integers, bools, bounded UTF-8/bytes, immutable
  lists/records, opaque symbol/type IDs tied to the defining module and target.
  No process addresses, pointers, closures, descriptors or mutable host objects.
* Resources: named immutable byte inputs with content hashes; named output
  artifacts. No ambient files, environment, sockets or subprocess capability.
* Limits: frame bytes, total output, AST nodes/depth, allocation, fuel, wall time,
  phase/dependency depth. Overflow, malformed input and cancellation fail before
  publication. Responses contain copied values, AST, dependency reads or a
  structured diagnostic with source byte spans, phase and target.
* Cache: compiler/frontend/protocol, transitive imports, canonical arguments,
  nominal identities, target/ABI/options and resource digests. No mtimes or host
  addresses. Publish atomically only after successful validation and completion.

The existing reader size checks are a baseline, not these complete quotas.
Native readers still have ambient authority. No whole compilation is hermetic.
`test/run_confinement.py` records feasibility only: unavailable native outcomes
never switch to trusted-native. Explicit trusted-native development execution
is outside this guarantee. The direct-Wasm program host denies file/process
imports and exposes no socket import; its supported authority boundary does not
yet supply production staging fuel, cancellation or bounded output supervision.
