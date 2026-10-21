# Zig M0 boundary

This is an oracle and measurement harness, with no Zig frontend or candidate
semantics. `oracle.lock.json` pins the source and Linux compiler archives from
the 0.17.0 distribution manifest. Extract both archives without editing them.
Initialize Lang with `make bootstrap PUBLISH_BOOTSTRAP=0`, then run:

```sh
nice -n 10 ./conformance/zig-demo M0 --zig-version 0.17.0 \
  --target x86_64-linux \
  --source /absolute/path/zig-0.17.0 \
  --source-archive /absolute/path/zig-0.17.0.tar.xz \
  --compiler /absolute/path/zig-x86_64-linux-0.17.0/zig \
  --compiler-archive /absolute/path/zig-x86_64-linux-0.17.0.tar.xz \
  --work /absolute/path/m0-output --receipt /absolute/path/M0.json
```

All compiler caches, temporary inputs, logs, native reader wrappers, LLVM IR,
and per-instance receipts live below `--work`. `--lang` selects the Lang
compiler (default `out/lang`); its executable digest is in the receipt. For
non-promoting verification, run `make verify` and pass
`--lang out/bootstrap_verify/kernel2` explicitly. No
upstream program is ever compiled as a candidate by the reference compiler.

The profile is x86_64 Linux, baseline CPU, ELF, little endian, 64-bit pointers,
the compiler's musl ABI without libc linkage, and `-fllvm`. The pinned CLI
spells the modes `debug`, `safe`, `fast`, and `small`; the first three form this
profile. Debug/safe enable safety checks; fast is unchecked. Each mode compiles
a separate assertion of `builtin.zig_backend == .stage2_llvm`. A candidate must
select that same compatibility branch and corresponding safety mode. Native
Lang boundary fixtures additionally run with clang `-O0` and `-O2`.

`baseline.json` publishes zero candidate credit, with reference denominators.
Full reruns produce `reference.json` and these subsidiary artifacts:

| Artifact | Meaning |
|---|---|
| `reference/identity.json` | Archive, compiler and extracted-file hashes; conservative complete source/library input closure |
| `reference/cli.txt` | Mode spellings from the pinned executable |
| `reference/declarations.json` | 2,137 direct declarations and 2,239 recursive declarations, with byte offsets |
| `reference/discovered-*.json` | Names and order returned by upstream runner discovery |
| `reference/coverage.json` | Every lexical declaration, its discovered instances and reference outcomes by mode |
| `reference/{debug,safe,fast}.json` | Compile commands, binary/IR hashes, per-instance results, timings and P |
| `reference/{debug,safe,fast}/global-cache/b/*/builtin.zig` | Compiler-generated resolved targets/modes, hashed in the reference receipt |
| `reference/negative-safety.json` | Unmodified selected upstream rejection and safety cases in checked modes |
| `harness.json` | Fault-detection controls; all receive zero upstream credit |
| `readers.json` | Native recursive reader, guest-origin, output-budget and limit measurements |

The entire archives are hashed and every extracted regular file is verified
before compilation. `std/testing.zig` and `compiler/test_runner.zig` additionally
must match between the compiler distribution and source archive. The original
`test/behavior.zig` imports discover the tests. There is no generated test
entrypoint, custom upstream runner, replaced testing helper, edited body, filter,
or candidate-specific skip list. The Python client speaks the unmodified
runner's little-endian metadata/run-test protocol and records skip, assertion,
runtime failure, timeout and compiler failure separately. Stalled processes are
killed as process groups; stderr is a file, so diagnostics cannot block a pipe.

IDs are `(source archive SHA-256, relative file, UTF-8 byte offset, full discovered
instance name plus occurrence)`. Byte offsets identify declarations, including
duplicate string names and declaration-named tests. LLVM debug locations join
fully qualified runner names to declarations. Optimization removes some debug
locations: optimized discovery must match the complete debug discovery list
exactly before its canonical source identities can be reused. Missing or
ambiguous origins fail the freeze. LLVM output is identity evidence only.

U is successful direct declarations / 2,137; recursive U uses 2,239. A declaration
needs reference discovery and candidate passes for every discovered instance in
every published mode. Unreached declarations, skipped tests, unsupported inputs,
compile/link failures, timeouts and adapted snippets earn zero raw credit. The
two tests in the root wrapper are outside both U denominators. P is reported
separately per mode: candidate passes / reference-discovered instances that pass
on the reference. Every reference skip remains visible with its source identity
and runner flags. A reference failure invalidates the freeze instead of shrinking
P. This harness publishes no candidate executions, hence U and all P numerators
are zero. The six authored fault controls and native reader fixtures are separate
from upstream credit. Any future adapted differential snippets must stay separate
as well. Do not compare undefined bytes, padding, or diagnostic wording as
candidate semantics.

`negative-cases.json` selects two upstream compile errors and two runtime safety
programs, each in debug/safe. The latter contain upstream panic handlers that
exit zero only upon the expected safety failure. Their bodies stay intact; fast
mode is excluded because those programs deliberately trigger checked violations.
These supplementary oracle checks do not establish candidate conformance.

The M0 host harness rejects output exceeding its configured budget. This does
not repair the production capture code. See `CURRENT_LIMITS.md` for existing
native-reader bounds, recursive execution limitations and further qualification.

Whole-mode replay on Linux accepts `--mode-jobs 1|2|3` (default 1), also
forwarded by `zig-demo`. Each worker compiles the same upstream root, performs
its own complete metadata discovery, and executes instances in discovery order.
Only whole modes overlap. Debug/safe/fast receipts are joined in that order;
optimized discovery must still match debug exactly before canonical origins are
reused. Each mode owns its local/global caches, temporary directory, binaries,
IR and logs under `reference/{debug,safe,fast}`. An existing reference work
directory can be reused: caches remain warm and current receipts and outputs
are overwritten. Use a new directory for cold-cache measurements. Do not run
multiple replays in the same work directory at once. Workers read the parent
declaration inventory rather than rebuilding it.

Serial replay (`--mode-jobs 1`) keeps the original compile/instance timeout
contract without a whole-mode deadline or CPU/resource restrictions. Pass
`--bounded` to apply supervision to serial replay, as the benchmark does.
Parallel replay always uses supervision.

The supervisor requires Linux `/proc`, child subreaping and CPU affinity. Defaults
are four shared CPU cores, 12 GiB aggregate descendant RSS, 128 descendant
processes, the existing 240-second compilation budget, and a 600-second whole-mode deadline. `--cpus`, `--memory-mib`,
`--process-limit` and `--mode-timeout` tune these bounds. RSS and process count
are sampled every 20 ms, so these are termination thresholds rather than kernel
hard quotas. CPU affinity is inherited by compiler/test descendants and checked
at each sample; a descendant can change it between samples. Timeout,
cancellation, worker failure and normal completion all reap descendants, including
orphans and children that start new sessions. Repeated cancellation is ignored
during the bounded cleanup sweep. SIGKILL or an OOM kill of the supervisor
cannot be handled and may leave descendants; this is not a sandbox. `resources.json` records limits,
measured aggregate peak RSS, elapsed time and cleanup. Compile and instance
failure/skip categories remain distinct. Resource-limit failures invalidate the
replay and never earn conformance credit.

For an equal-work comparison, use a new output directory:

```sh
nice -n 10 python3 -B conformance/zig/benchmark.py \
  --source /absolute/path/zig-0.17.0 \
  --source-archive /absolute/path/zig-0.17.0.tar.xz \
  --compiler /absolute/path/zig-x86_64-linux-0.17.0/zig \
  --compiler-archive /absolute/path/zig-x86_64-linux-0.17.0.tar.xz \
  --work /absolute/path/comparison
```

Two rounds alternate serial/parallel order using equally cold private caches and
identical CPU/resource limits. Every archive and extracted input is reverified.
The comparison requires identical stable declaration/instance IDs, runner flags,
results, failure/skip categories, coverage, frozen discovery counts, U and P.
It reports completed checks/hour and sampled process-tree peak RSS; it records
whether parallel throughput improved. Reference-only work always earns zero
candidate credit. Run `python3 -B conformance/zig/test_mode_jobs.py --work
/absolute/path/supervision-tests` to exercise resource limits and cleanup with
hostile process trees. The existing `oracle.py selftest` remains the independent
bad/clean runner control.
