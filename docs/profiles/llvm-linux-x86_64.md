# LLVM / Linux x86-64

Profile: `llvm-linux-x86_64`, version 1 (current implementation boundary).

Select with `LANGBE=llvm LANGOS=linux`.

Native libc build, bootstrap LLVM/AST fixed points, LLVM suite and effects matrix run on Linux x86-64.

64-bit pointers; scalar/internal i64 arguments, u8/bool and floating returns where implemented. Struct parameters use the internal address/copy convention, not the platform aggregate ABI.

Effects are experimental at -O0 within live native frames. -O1/-O2 and full LTO at -O2 must fail with the effects diagnostic. No escaping, multi-shot, foreign-frame suspension or thread migration contract.

All existing readers/examples retain [legacy/internal ABI v1](../C_SUBSET.md). Struct value returns are rejected because the old lowering can return a dead local address; explicit output pointers are the supported replacement. Existing enum-return fixtures remain internal compatibility evidence, not proof of a general external aggregate-return ABI. Narrow-field layout, aggregate calls and arbitrary C interop are unverified.

[Size limits](../SIZE_LIMITS.md) apply to the compiler host. See the [profile index](../PROFILES.md) for reproducible checks and proposal status.
