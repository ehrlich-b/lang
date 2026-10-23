# Staging workers

`test/run_staging.sh P1` builds and calls host AOT executables. The script builds a current compiler unless `COMPILER` is supplied. Set
`STAGING_EVIDENCE` to an output directory. P0 remains
the layout and confinement audit. P1 requires clang and Node for the Wasm test.

H owns compilation and artifact capabilities. `src/stage_host.py` supplies
`compile_hook` and `call_hook`; the baseline engine starts a fresh compiler
process for every compilation and execs a fresh executable for every call.
An accelerator can implement these hooks using the same wire contract. It
must implement the same copying, type checks and per-call state rules.
No compiler process loads native code or calls a generated function pointer.

Native confinement is not qualified. The service refuses to start without
`--controlled-fixtures`, admits only names in `test/staging/fixtures.json`,
and has no source-upload operation. This mode is for trusted test fixtures.
Process separation, deadlines and resource limits do not authorize running
untrusted source. P0 confinement qualification remains a prerequisite for that.

Run the framed service with:

```
python3 src/stage_host.py --controlled-fixtures --compiler out/lang --storage /path/to/scratch
```

stdin/stdout carry frames; diagnostics remain in each process's separate
stderr spool in scratch. Each request is a `record`. A compile request has
`op: text("compile")`, `fixture: text`, `signature: list(text)` (argument wire
types), `result: text`, and `output_target: descriptor`. It returns an opaque
text artifact token. A call has `op: text("call")`, `artifact: text(token)` and
`args: list`. It returns the entry's copied value. Tokens belong to one service
instance; accepting a serialized descriptor never grants an execution token.
A failed compile publishes nothing. Builds use unique private directories,
link to a pending file and atomically publish the finished executable. H checks
its content digest before executing. Scratch is retained for diagnostics.

The 16-byte STG1 header is `<magic[4], payload_bytes:u32, kind:u32, reserved:u32>`
in little endian; kinds are request=1, response=2 and error=3, reserved=0.
Payloads are one `<tag:u8, bytes:u32, payload>` value. Tags 0..11 are null,
bool, i8, i16, i32, i64, bytes, UTF-8 text, list, record, core syntax and
immutable descriptor. Signed integers are exact-width little-endian two's
complement. Lists begin with a u32 count; records/descriptors begin with a u32
pair count, then strictly sorted UTF-8 text keys and values. Syntax carries
UTF-8 core AST text, validated by the core compiler when consumed. Byte and
text lengths are explicit, so embedded NUL survives. Values contain no IDs,
backreferences, addresses or native layouts. Depth is at most 64, total values
at most 100000, and payloads at most 8 MiB. Exact lengths, canonical keys,
UTF-8, signatures and budgets are checked before entry execution. Foreign
objects, pointers, closures and cycles are refused by the encoder.

`std/stage.lang` implements the worker side independently. Its handles own
copied wire storage. A worker reads one frame, checks EOF, invokes its adapter
and writes one response. Record/descriptor bytes are never cast to a target
or host structure. Output-target descriptors travel as values; execution host
selection uses H's host configuration. The baseline only uses audited pointer
and i64 slots, not a proposed C ABI.

For existing reader wrappers, the opt-in `LANG_STAGE_FRESH_COMPILER=1` H hook
requires `LANG_STAGE_CONTROLLED_FIXTURES=1`. The compile hook execs a new compiler in the
existing compilation child, replacing LANGOS/LANGBE with the execution host
settings and disabling recursive hook installation in the fresh compiler.
The call hook wraps legacy text in STG1 values and validates the response before
returning copied text. Generated wrappers use `std/stage.lang`, and link outputs
publish atomically. The default legacy reader engine is unchanged. `test/staging/reader.lang`
exercises this path with Wasm output and a native helper.

`test/run_bootstrap_gate.py --output /path/to/evidence` runs the full promoting
bootstrap on a retained exact-HEAD checkout, preserving candidate cleanliness
and all bootstrap evidence without restoring generated files afterward.
