# Translation-unit size audit

Limits count bytes, not Unicode characters. The shared compiler host uses `LANG_HOST_MAX_BYTES` (16 MiB by default, payload bytes excluding the sentinel); see [PHASE_HOST.md](PHASE_HOST.md). Legacy backend buffers still count their sentinel in the allocation capacity. Text capacities include one NUL terminator; an input exactly at capacity minus one is valid only when the next read proves EOF. Read loops handle short reads. Oversized input never succeeds with a valid prefix. Diagnostics identify the path or stage and capacity; writes loop until complete or fail loudly. Limits bound resources, not language semantics.

| Path | Capacity | Behavior at exhaustion |
|---|---:|---|
| Main CLI, includes/requires, combined source, serialized AST input/output | Configured host payload budget | Versioned host error, nonzero |
| Generated reader stdin/stdout and dependency closure | Configured host payload budget | Complete read or versioned host error |
| AST-to-source renderer | 64 KiB initially, grows to host payload budget | ast-byte-limit at maximum |
| Split kernel / split reader input | 4 MiB / 1 MiB | Path diagnostic, nonzero |
| Legacy fixed-destination capture | Caller capacity minus sentinel | output-limit, never a successful prefix |
| LLVM output | 8 MiB | Existing LLVM overflow diagnostic |
| Legacy assembly / per-function output | 4 MiB / 512 KiB | Existing fatal overflow diagnostics |
| Direct Wasm module/section/body | 8 MiB each | Existing Wasm overflow error; no successful module |
| Direct Wasm static string data | 1 MiB | Existing direct Wasm data diagnostic |

The direct Wasm include loader reserves one additional byte in its 1 MiB allocation (maximum content: 1 MiB minus two bytes). Counts for declarations, locals, parameters and parser structures are separately bounded in src/limits.lang; this audit addresses text/binary transport, not unlimited AST complexity or allocation.

`test/run_profile_checks.py` exercises real file/AST/reader paths and instrumented small-capacity emitter probes. Host transport probes explicitly configure the payload budget; the former fixed 1/4/8 MiB capacities are boundary test sizes, not current host limits. `test/run_phase_host.py` also checks growth past the old capacities, worker duplex transport, and source identity failures. It verifies success at the boundary, a valid-prefix adversary beyond it, intended diagnostics and nonzero status. Negative output artifacts are retained for inspection, never renamed or deleted to turn a failure into success. LLVM and legacy streaming outputs can leave partial files on failure; a nonzero compiler exit always invalidates them.
