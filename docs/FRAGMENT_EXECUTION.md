Local LLVM fragments can explicitly opt into a private native cache:

```sh
python3 scripts/fragment_exec.py run fragment.ll --cache /private/build/fragment-cache
python3 scripts/fragment_exec.py qualify fragment.ll --cache /private/build/fragment-cache
python3 scripts/fragment_exec.py run fragment.ll --cache /private/build/fragment-cache
```

`run` executes lli on a miss and never invokes clang. Only `qualify` builds an
O0 binary, compares its exit status and exact output streams against ORC lli,
and publishes a receipt after both terminate successfully (nonzero program
exits are allowed). Compilation failures, signals, timeouts and unequal
observations cannot qualify. Assembly and stack-control IR cannot qualify;
the integration suite keeps all existing execution choices, including effects.

Qualification is a deliberate local assertion that this particular fragment
has no arguments, input, environmental dependencies or external effects. It is
one bounded observation, not a proof of arbitrary program equivalence. Use lli
or the existing native routes for other programs. `run` inherits the caller's
streams, stdin and signals; bound execution with the caller's usual timeout.
The cache contains executable code and must be writable only by its trusted
user. It is not a remote artifact format or a sandbox.

Identity includes exact IR bytes, clang/lli/linker paths, bytes and versions,
target triple, host system/architecture, fixed native and lli flags, and the
oracle version and runner bytes. Each hit also verifies the executable digest
and qualification identity. Missing, stale, malformed or damaged entries use
lli. Complete binaries are published before their atomic receipts; concurrent
qualification may leave unused binaries, but cannot publish partial hits.

For repeated execution, `resolve` returns a JSON argv for a validated hit or
lli fallback. Resolve once, then execute that argv within the same bounded
local session. Resolution and qualification costs are excluded from binary
launch microbenchmarks; invoking the Python runner for each execution adds
identity validation overhead and carries no sub-5ms latency claim. Resolve
again after changing tools or inputs. No integration mode enables this cache.

The focused check is `python3 test/check_fragment_execution.py --evidence DIR`
with DIR outside the checkout, after `make build`. It records interleaved
lli/native user+system CPU samples, exits, streams, hashes and timeout results
on arithmetic, stream output, failure and rejection fixtures. Full integration
and both bootstrap fixed points remain requirements of the existing verifier.
