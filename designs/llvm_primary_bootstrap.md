# LLVM as Primary Bootstrap

**Status**: Implementing
**Priority**: #1 (blocks Mac development)

## Summary

Make LLVM IR the primary bootstrap artifact. The x86 assembly becomes a secondary artifact for fast Linux iteration.

## Current State

```
bootstrap/current/
├── compiler.s           # x86-64 assembly (Linux only)
├── llvm_libc_macos.ll   # LLVM IR (cross-platform)
└── lang_reader/source.ast
```

`make bootstrap` on Linux:
1. Assembles `compiler.s` → root of trust
2. Builds generations, verifies fixed point
3. Generates BOTH `.s` and `.ll` artifacts
4. Promotes both

`make llvm-verify` on Mac:
1. Compiles `llvm_libc_macos.ll` → root of trust
2. Builds generations, verifies fixed point
3. (Separate command, doesn't promote)

**Problem**: Two different commands, Mac is second-class.

## Proposed State

```
bootstrap/current/
├── compiler.ll          # LLVM IR (PRIMARY - cross-platform)
├── compiler_linux.ll    # LLVM IR for Linux (libc)
├── compiler_macos.ll    # LLVM IR for macOS (libc_macos)
├── compiler.s           # x86-64 assembly (SECONDARY - Linux fast path)
└── lang_reader/source.ast
```

`make bootstrap` (same command on both platforms):
1. Detects OS
2. Compiles appropriate `.ll` → root of trust
3. Builds generations, verifies fixed point
4. Runs test suite (LLVM on Mac, both on Linux)
5. Generates all artifacts
6. Promotes

## Implementation

### Phase 1: Unified Bootstrap Command

```makefile
# Detect OS and set bootstrap path
UNAME := $(shell uname -s)
ifeq ($(UNAME),Darwin)
    BOOTSTRAP_LL := bootstrap/current/compiler_macos.ll
    SKIP_X86_TESTS := 1
else
    BOOTSTRAP_LL := bootstrap/current/compiler_linux.ll
    SKIP_X86_TESTS := 0
endif

bootstrap:
    # Stage 1: LLVM root of trust
    clang $(BOOTSTRAP_LL) -o /tmp/bootstrap_verify/ctrusted

    # Stage 2-5: Same as before, but using LLVM compiler
    ...
```

### Phase 2: Rename Bootstrap Artifacts

Current:
- `llvm_libc_macos.ll` → for macOS

New:
- `compiler_macos.ll` → LLVM IR targeting macOS (arm64, libc_macos)
- `compiler_linux.ll` → LLVM IR targeting Linux (x86_64, libc)
- `compiler.s` → x86 assembly for Linux (kept for fast path)

### Phase 3: Update Scripts

All scripts need to work on both platforms:

| Script | Current | Change Needed |
|--------|---------|---------------|
| `run_llvm_suite.sh` | ✓ Cross-platform | None |
| `run_lang1_suite.sh` | Linux only | Exit with message on Mac |
| `Makefile` | Linux-centric | Detect OS, use LLVM primary |

### Phase 4: Fast Path for Linux

On Linux, after LLVM bootstrap succeeds, optionally verify x86 too:

```makefile
# After LLVM verification passes...
ifeq ($(SKIP_X86_TESTS),0)
    @echo "Also verifying x86 backend (Linux fast path)..."
    # Build x86 compiler from verified LLVM compiler
    # Run x86 test suite
    # Generate compiler.s artifact
endif
```

## Bootstrap Chain (New)

```
                         TRUST CHAIN
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 1: LLVM Root of Trust                                │
│  ─────────────────────────                                  │
│  clang bootstrap/current/compiler_$(OS).ll → ctrusted       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 2: Generation 1                                      │
│  ─────────────────────                                      │
│  LANGBE=llvm ctrusted src/*.lang → kernel1.ll               │
│  clang kernel1.ll → kernel1                                 │
│  kernel1 builds lang1 (standalone)                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 3: Generation 2 + Fixed Point                        │
│  ───────────────────────────────────                        │
│  LANGBE=llvm lang1 src/*.lang → kernel2.ll                  │
│  VERIFY: kernel1.ll === kernel2.ll (LLVM FIXED POINT)       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 4: Validation                                        │
│  ───────────────────                                        │
│  Run LLVM test suite (both platforms)                       │
│  Run x86 test suite (Linux only)                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 5: Generate All Artifacts                            │
│  ──────────────────────────────                             │
│  Generate compiler_linux.ll (LANGOS=linux LANGBE=llvm)      │
│  Generate compiler_macos.ll (LANGOS=macos LANGBE=llvm)      │
│  Generate compiler.s (Linux only, x86 backend)              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 6: Promote                                           │
│  ───────────────                                            │
│  Copy all artifacts to bootstrap/$(COMMIT)/                 │
│  Update bootstrap/current symlink                           │
└─────────────────────────────────────────────────────────────┘
```

## File Changes

### Makefile

```makefile
# OS detection
UNAME := $(shell uname -s)
ifeq ($(UNAME),Darwin)
    PLATFORM := macos
    CLANG_TARGET := -target arm64-apple-macos11
else
    PLATFORM := linux
    CLANG_TARGET :=
endif

# Bootstrap artifact selection
BOOTSTRAP_LL := bootstrap/current/compiler_$(PLATFORM).ll

bootstrap: generate-os-layer
    @echo "Platform: $(PLATFORM)"
    @echo "Bootstrap: $(BOOTSTRAP_LL)"
    # ... unified bootstrap using LLVM
```

### Bootstrap Directory

Rename:
- `llvm_libc_macos.ll` → `compiler_macos.ll`
- (new) `compiler_linux.ll`
- `compiler.s` stays as-is

### PROVENANCE

Update to track all three artifacts with checksums.

## Rollout

1. **Immediate**: Update Makefile to use LLVM primary
2. **Immediate**: Rename bootstrap artifacts
3. **Immediate**: Test on Linux (should still work)
4. **Then**: Test on Mac (should now work with `make bootstrap`)
5. **Later**: Consider removing x86 from bootstrap chain entirely

## Risks

- **clang version differences**: LLVM IR is mostly stable, but edge cases exist
- **libc differences**: macOS and Linux libc have different symbols
- **Slower bootstrap on Linux**: ~10s instead of ~5s (acceptable)

## Success Criteria

- [ ] `make bootstrap` works on macOS
- [ ] `make bootstrap` works on Linux
- [ ] Same command, same artifacts
- [ ] x86 test suite still runs on Linux
- [ ] Fixed point verification uses LLVM IR (not x86 assembly)
