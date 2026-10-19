# Translation-unit size audit

Limits count bytes, not Unicode characters. Text capacities include one NUL terminator; an input exactly at capacity minus one is valid only when the next read proves EOF. Read loops handle short reads. Oversized input never succeeds with a valid prefix. Diagnostics identify the path or stage and capacity; writes loop until complete or fail loudly. Limits bound resources, not language semantics.

| Path | Capacity | Behavior at exhaustion |
|---|---:|---|
| Main CLI file / serialized AST input | 8 MiB | Path diagnostic, nonzero |
| Includes/requires, expanded AST includes | 1 MiB | Path diagnostic, nonzero |
| Main/reader combined source wrapper | 4 MiB | combined source diagnostic |
| Split compiler/kernel input | 4 MiB | Path diagnostic |
| Standalone compiler / split reader input | 1 MiB | Path diagnostic |
| Generated reader stdin | 4 MiB | EOF probe, drain excess, reader stdin diagnostic and exit 1 |
| External reader stdout capture | 4 MiB | Drain excess, wait, reader stdout diagnostic |
| Reader wrapper / dependency closure source | 1 MiB each | Checked before stores/copies |
| AST-to-source renderer | 64 KiB initially, grows to 8 MiB | AST source output diagnostic at maximum |
| Serialized AST output | 8 MiB | AST output diagnostic; no prefix returned as success |
| LLVM output | 8 MiB | Existing LLVM overflow diagnostic |
| Legacy assembly / per-function output | 4 MiB / 512 KiB | Existing fatal overflow diagnostics |
| Direct Wasm module/section/body | 8 MiB each | Existing Wasm overflow error; no successful module |
| Direct Wasm static string data | 1 MiB | Existing direct Wasm data diagnostic |

The direct Wasm include loader reserves one additional byte in its 1 MiB allocation (maximum content: 1 MiB minus two bytes). Counts for declarations, locals, parameters and parser structures are separately bounded in src/limits.lang; this audit addresses text/binary transport, not unlimited AST complexity or allocation.

`test/run_profile_checks.py` exercises real file/AST/reader paths and instrumented small-capacity emitter probes. It verifies success at the boundary, a valid-prefix adversary beyond it, intended diagnostics and nonzero status. Negative output artifacts are retained for inspection, never renamed or deleted to turn a failure into success. LLVM and legacy streaming outputs can leave partial files on failure; a nonzero compiler exit always invalidates them.
