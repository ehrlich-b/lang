# Current capability profiles

These profiles describe present behavior. They are not a C11 conformance claim, a Lua build receipt, or a promise that every core program works on every target. A fixed point proves repeatability; runtime fixtures provide independent evidence.

| Backend and target | Contract | Verification |
|---|---|---|
| LLVM, Linux x86-64 | [llvm-linux-x86_64](profiles/llvm-linux-x86_64.md) | Native baseline |
| LLVM, macOS arm64 | [llvm-macos-arm64](profiles/llvm-macos-arm64.md) | Native baseline required on a Mac; Linux object cross-check alone is insufficient |
| LLVM, wasm32 | [llvm-wasm32](profiles/llvm-wasm32.md) | LLVM-to-Wasm suite |
| Direct binary, wasm32 | [direct-wasm32](profiles/direct-wasm32.md) | Direct emitter and compiler-host suites |
| Assembly, Linux x86-64 | [x86-linux-legacy](profiles/x86-linux-legacy.md) | Frozen, legacy/internal |

Run `nice -n 10 python3 test/run_baseline.py --output out/baseline` from a clean checkout with clang, lli, wasm-ld, Node, Python and (on Linux) ld.lld. It preserves the input bootstrap hashes, records the exact commit, dirty status, host and tool versions, runs non-promoting make verify, LLVM/effects/Wasm/profile checks, and writes logs plus receipt.json. Each run needs a new output directory. Required missing tools, unexpected skips or nonzero gates fail the command. Run it on each native host; the receipt's host field must match the claimed platform. The receipt requires identical seed hashes before and after. The separate promotion gate must run in a disposable checkout with PUBLISH_BOOTSTRAP=0. No upload is performed.

The historical integration receipt at 480e61e reported LLVM 239 passed / 0 failed / 6 skipped and LLVM-to-Wasm 177 passed / 0 failed / 21 skipped. Those are historical counts, not a fresh native arm64 receipt. The checked-in skip inventories retain the exact baseline exclusions; a new exclusion fails verification. Additional safety checks may increase passes.

The shipped [C reader](C_SUBSET.md) uses legacy/internal ABI v1 and rejects incomplete parses at the first unparsed token. Struct return syntax fails in that reader; struct return signatures in core/lang input fail in the emitters. Optimized native effects retain their refusal, including full LTO. Known unsupported behavior must be named as such; a coincidentally correct example does not expand a profile.

`designs/ast_as_language.md`, `designs/kernel_reader_split.md` and older bootstrap prose contain proposals and historical implementation descriptions. They do not override these profiles. In particular, escaping continuations, automatic GC roots, standard-C signed overflow, complete C support and a fully independent parser/kernel split are not established by those designs. Runtime policies and surface-language rules belong outside the kernel.

The [core/wire and audited storage contract](CORE_WIRE.md) freezes the boundary for future staging. Run `nice -n 10 test/run_staging.sh P0` for calculator, admission, confinement and manifest checks. Run `nice -n 10 make verify` and `nice -n 10 make test-direct-wasm` after every implementation change; select `COMPILER=out/bootstrap_verify/kernel2` for the freshly verified compiler. Native confinement remains unavailable until its full attack matrix qualifies; supported Wasm never authorizes trusted-native.
