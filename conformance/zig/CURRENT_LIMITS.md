# Native-reader boundary at 480e61e

This section inventories the historical seed. The integrated target-profile
work now checks source, wrapper, AST and capture boundaries; see
[`docs/SIZE_LIMITS.md`](../../docs/SIZE_LIMITS.md) for the current contract.
The M0 reader probe requires exact lengths below 4,194,304 bytes and an empty
stdout, reader-stdin size diagnostic and exit 1 at or above that capacity.
Silent truncation is no longer an accepted integration result. This changes
the boundary expectation only; it adds no Zig frontend or candidate credit.

M0 inventories this boundary and adds external measurement tools. Production
files stay unchanged. Growable buffers belong to H; nested-phase execution and
its stronger qualification belong to P. No Zig-specific kernel rules are added.

| Boundary | Current size or behavior | Source |
|---|---|---|
| Standalone native reader stdin | Allocates 4,194,304 bytes, reads at most 4,194,303, then appends NUL. No overflow probe or input-too-large diagnostic. | `src/codegen.lang`, generated `main_src` in both reader builders |
| External reader stdout capture | At most 4,194,303 bytes plus NUL; closes its pipe at capacity without detecting an additional byte. Depending on write timing, oversized output can be truncated or terminate its writer. | `src/codegen.lang`, `exec_capture`; callers in `src/main.lang` and `src/codegen_llvm.lang` |
| Reader wrapper and dependency source | Separate fixed 1,048,576-byte allocations; raw copying/appending lacks a corresponding capacity protocol. | `compile_reader_to_executable`, `dependency_src`, wrapper builders in `src/codegen.lang` |
| Included files / runtime expansion | Several 1,048,576-byte single reads. `read_file_contents` writes a NUL at `buf+n`, including when n equals the full allocation size. No EOF check. | `src/codegen.lang:read_file_contents`; `src/main.lang:expand_collect_decl` |
| CLI combined source / wrapper assembly | 4,194,304 bytes with unchecked `append_str`. | `src/main.lang`; `src/reader_main.lang` |
| Main `read_file` | Single 8,388,608-byte read using `SIZE_AST_EMIT`; NUL is written at index n, with the same full-capacity problem. | `src/main.lang:read_file` |
| Separate reader executable `read_file` | Single 1,048,576-byte read, with the same NUL/full-capacity problem. | `src/reader_main.lang:read_file` |
| Serialized AST emitter | 8,388,608-byte allocation; `ast_emit_char` silently stops appending at capacity minus one. | `src/ast_emit.lang` |
| LLVM output | 8,388,608 bytes, loud overflow rejection. | `src/codegen_llvm.lang:llvm_emit_char` |
| Other code output | 4,194,304-byte module buffer and 524,288-byte function buffer, loud overflow rejection. | `src/limits.lang`; `src/codegen.lang:emit_char` |
| Declaration tables | 4,000 top-level declarations, 3,000 functions, 100 readers, 20 embedded readers, 32,768 node origins. These are allocation/table limits, not a universal checked-resource contract. | `src/limits.lang`; `src/parser.lang:node_set_span` |
| Other declared bounds | 1,024 statements/block, 16 call arguments and parameters, 1,024 locals, 32 include and loop depth slots; additional fixed arrays exist. `SIZE_HEAP=268435456` is a declared constant, not evidence of a universal enforced heap budget. | `src/limits.lang`; parser and codegen allocations |

`readers.py` records all declared constants and production-source SHA-256 values.
Its native stdin measurements show exact input lengths up to 4,194,303 bytes,
then the same observed length for larger input with a successful reader exit.
This is measured truncation, not a supported maximum that callers can rely on
to fail safely. The separate output-budget control kills a valid 8,192-byte
reader result after observing 1,025 bytes against a 1,024-byte harness budget.
That failure belongs to the external harness; production capture is unchanged.

The recursive fixture's outer reader calls a recursive sibling helper, emits a
`(reader_expr boundary_leaf ...)`, and the leaf calls the same recursive helper
to produce 42. Lang builds and executes ordinary native wrappers. Its emitted
LLVM links and exits 42 at both `-O0` and `-O2`. Serialized spans survive `lang
read`; consuming the AST with `--ast-source` reports the guest file at 1:1 on a
required undefined-symbol rejection. The inline-origin fixture also exposes the
existing fallback to the enclosing function location, so a complete nested
origin stack is not established by the successful file-origin probe.

Recursive reader output expansion is distinct from a reader's implementation
invoking another reader during its own compilation. Named sibling dependencies
are selected transitively, while declaration-level sibling reader uses are
excluded from implementation wrappers. Cache paths use reader names; freshness
checks use mtimes. There is no proven content-addressed transitive phase cache,
cycle-origin stack, fuel/nesting budget, or cancellation contract. Native readers
inherit the environment and execute with ambient process/filesystem authority.
No sandbox or arbitrary-depth phase-safety claim follows from this fixture.

P still needs cold-cache nested-phase tests, cycles, multiple namespaces and
same-name readers, transitive invalidation, dependency/target identities and
origin chains. H still needs checked source, wrapper, dependency, AST and capture
buffers with explicit overflow failures. M0 deliberately does not repair them.
