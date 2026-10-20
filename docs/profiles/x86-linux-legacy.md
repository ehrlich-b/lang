# Frozen assembly / Linux x86-64

Profile: `x86-linux-legacy`, version 1 (current implementation boundary).

Select with `LANGBE=x86 LANGOS=linux`.

Legacy/internal backend, not the primary LLVM suite target. The baseline does not certify it as equivalent to LLVM. Use only existing examples and explicit fixture checks.

Historical i64/register and stack convention; Linux syscall or selected libc layer. No portable external aggregate ABI.

No new feature promise or optimizing-effects contract. Old effects and reader examples are legacy/internal; use the LLVM profile for current native validation.

All existing readers/examples retain [legacy/internal ABI v1](../C_SUBSET.md). Struct value returns are rejected because the old lowering can return a dead local address; explicit output pointers are the supported replacement. Existing enum-return fixtures remain internal compatibility evidence, not proof of a general external aggregate-return ABI. Narrow-field layout, aggregate calls and arbitrary C interop are unverified.

[Size limits](../SIZE_LIMITS.md) apply to the compiler host. See the [profile index](../PROFILES.md) for reproducible checks and proposal status.
