# LLVM / macOS arm64

Profile: `llvm-macos-arm64`, version 1 (current implementation boundary).

Select with `LANGBE=llvm LANGOS=macos`.

The bootstrap cross-check builds an arm64 Mach-O object on Linux. That is not native execution. Native bootstrap/suite receipts must be produced on an arm64 Mac with the baseline command; no local Mac receipt is claimed by this document.

64-bit pointers; internal i64 arguments and implemented scalar returns. System libc is mandatory. No general AAPCS64 aggregate or variadic ABI claim.

Experimental native effects at -O0 only; the same optimization refusals are required. Cross-compilation cannot prove continuation lifetime or native correctness.

All existing readers/examples retain [legacy/internal ABI v1](../C_SUBSET.md). Struct value returns are rejected because the old lowering can return a dead local address; explicit output pointers are the supported replacement. Existing enum-return fixtures remain internal compatibility evidence, not proof of a general external aggregate-return ABI. Narrow-field layout, aggregate calls and arbitrary C interop are unverified.

[Size limits](../SIZE_LIMITS.md) apply to the compiler host. See the [profile index](../PROFILES.md) for reproducible checks and proposal status.
