# Shared baseline

Source baseline: 480e61e5331ce9e8c942691d5b65440b2c2c3535. The preserved
bootstrap identity is f532c0d, built from b47e3f4-dirty. The root's PROVENANCE
contains the original hashes; this work deliberately retains the input seed.
The profile, aggregate-return refusal, complete C-parse refusal, transport size
checks and retained full-LTO sentinel reuse the established 47aa77d baseline
work. These source changes are built by the older preserved seed through the
same self-hosted fixed point, rather than assuming a regenerated root is trusted.

Historical integration counts were LLVM 239/0/6 and LLVM-Wasm 177/0/21. They are
expectations only. `test/run_baseline.py --output NEW_DIRECTORY` records fresh
host/tool identities, source status, seed hashes, exact fixed-point hashes,
all gate exits and exact skip lists. Native receipts must say Linux x86_64 or
Darwin arm64; a cross-target object is not native execution. No supplied native
Mac execution receipt is available here. Run the baseline and confinement spike
on a real arm64 Mac before qualifying that native platform.

Known failures and refusals: aggregate returns can refer to dead storage and
are rejected; two-u8 layout is inconsistent; effects have no proven optimized
lowering; the original full-LTO optimizer could discard its refusal sentinel.
Retaining the sentinel with llvm.used closes that observed escape. The effects
matrix now requires the intended diagnostic at O1/O2/full-LTO O2, and correct
answers at O0. Other unsupported optimizer pipelines remain unqualified.
No optimized effects support is advertised.

Backend-specific profiles are indexed in PROFILES.md. CORE_WIRE.md distinguishes
legacy/internal storage from opt-in audited slots and future staging wire.
Conformance manifests in test/conformance freeze independent selections and
source/directive identities. They confer no C implementation or reference-run
passes. Native confinement feasibility records an unavailable result whenever
any attack succeeds or the host/toolchain cannot execute the probe. Wasm's
import boundary is a supported alternative at its explicitly tested scope.
