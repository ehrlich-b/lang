# Validation vNext: Rigorous Multi-Generation Verification

## Executive Summary

The current `make verify` has critical gaps:
1. **Single-generation kernel check** - doesn't verify multi-generation stability
2. **Toy reader test** - "does test42 return 42" is not a fixed point
3. **No standalone self-compilation** - never verifies standalone can recreate itself
4. **Mixed concern phases** - tests run before full fixed point

This document proposes a mathematically rigorous verification chain.

## Current Verification Analysis

### What `make verify` Does Now

```
Phase 1: ctrusted = assemble(bootstrap/current/compiler.s)
Phase 2: candidate = ctrusted.compile(sources)
Phase 3: candidate_v2 = candidate.compile(sources)
         VERIFY: candidate.s === candidate_v2.s  ← "Kernel fixed point"
Phase 4: standalone = candidate.compile(-c lang, lang_reader.lang)
Phase 5: test42 = standalone.compile(test42.lang)
         VERIFY: test42.run() === 42  ← "Reader fixed point" (NOT A FIXED POINT!)
Phase 6: Run x86 test suite with candidate
Phase 7: llvm_compiler = candidate.compile(sources, LANGBE=llvm)
Phase 8: Run LLVM test suite with llvm_compiler
```

### Critical Gaps

| Gap | Current | Problem |
|-----|---------|---------|
| Multi-gen stability | 1 generation | Could have drift that only manifests in gen 3+ |
| Reader fixed point | Functionality test | "test42 returns 42" proves nothing about self-consistency |
| Standalone self-compilation | Not tested | Never verifies standalone can recreate itself |
| LLVM fixed point | Not tested | LLVM compiler never compiles itself |

### The "Reader Fixed Point" Fallacy

Current Phase 5 tests:
```bash
./out/lang_standalone /tmp/test42.lang -o /tmp/test42.s
# run test42, verify exit code 42
```

This proves the standalone compiler **works**, not that it's a **fixed point**. A fixed point would be:
```
standalone -c lang lang_reader.lang === (standalone -c lang lang_reader.lang) -c lang lang_reader.lang
```

## Proposed Verification Chain

### The Full Chain

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 1: ROOT OF TRUST                                          │
├─────────────────────────────────────────────────────────────────┤
│ ctrusted = assemble(bootstrap/current/compiler.s)               │
│   - This is our axiom, the one thing we trust                   │
│   - Everything flows from this                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 2: GENERATION 1 (Built by Trusted)                        │
├─────────────────────────────────────────────────────────────────┤
│ candidate_kernel1 = ctrusted.compile(kernel + compiler sources) │
│ candidate_reader_ast1 = ctrusted.emit_ast(lang_reader.lang)     │
│ candidate_lang1 = {candidate_kernel1 -r candidate_reader_ast1}  │
│   - First compiler built from sources                           │
│   - Potentially has bugs in output but not in parsing           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 3: GENERATION 2 (Built by Gen1) - THE CRITICAL LOOP       │
├─────────────────────────────────────────────────────────────────┤
│ candidate_kernel2 = candidate_lang1.compile(kernel + compiler)  │
│ candidate_reader_ast2 = candidate_lang1.emit_ast(lang_reader)   │
│ candidate_lang2 = {candidate_kernel2 -r candidate_reader_ast2}  │
│                                                                 │
│ VERIFY: candidate_kernel1.s === candidate_kernel2.s             │
│ VERIFY: candidate_reader_ast1 === candidate_reader_ast2         │
│   - If these match, we have KERNEL FIXED POINT                  │
│   - The compiler's output is stable across generations          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 4: STANDALONE FIXED POINT                                  │
├─────────────────────────────────────────────────────────────────┤
│ candidate_standalone1 = candidate_lang2.compile(-c lang,        │
│                                                 lang_reader)    │
│ candidate_standalone2 = candidate_standalone1.compile(-c lang,  │
│                                                 lang_reader)    │
│                                                                 │
│ candidate_standalone3 = candidate_standalone2.compile(-c lang,  │
│                                                 lang_reader)    │
│                                                                 │
│ VERIFY: candidate_standalone2.s === candidate_standalone3.s     │
│   - Standalone compiler can recreate itself                     │
│   - This is TRUE SELF-HOSTING                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 5: VALIDATION (Only After Fixed Points Proven)            │
├─────────────────────────────────────────────────────────────────┤
│ Using candidate_standalone2 (the proven fixed point):           │
│   - Run x86 test suite (43 tests)                               │
│   - Generate LLVM IR: llvm_compiler = compile(sources, llvm)    │
│   - Run LLVM test suite (165 tests)                             │
│                                                                 │
│ ALL MUST PASS before promotion                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 6: PROMOTION                                               │
├─────────────────────────────────────────────────────────────────┤
│ Save to bootstrap/COMMIT/:                                      │
│   - compiler.s (candidate_standalone2.s - THE fixed point)      │
│   - llvm_libc_compiler.ll                                       │
│   - lang_reader/source.ast (for emergency recovery)             │
│   - PROVENANCE (hashes, dates, chain of trust)                  │
└─────────────────────────────────────────────────────────────────┘
```

## Key Decision: What To Walk Away With

### The Candidates

| Artifact | What It Is | How To Use |
|----------|------------|------------|
| `candidate_lang2` | kernel + reader AST composition | `kernel -r reader.ast file.lang` |
| `candidate_standalone2` | standalone compiler, proven fixed point | `standalone file.lang` |

### Recommendation: `candidate_standalone2`

Why `standalone2` specifically (not `standalone1`):
- `standalone1` was built by `lang2` (a composed compiler)
- `standalone2` was built by `standalone1` (a standalone compiler)
- `standalone3` was built by `standalone2` (another standalone)
- We verified `standalone2 === standalone3`
- Therefore `standalone2` is the **proven self-hosting fixed point**

Reasons to choose standalone format over composed:
1. **Self-contained** - No external reader AST needed
2. **True fixed point proven** - `standalone2 === standalone3`
3. **Matches current bootstrap** - bootstrap/current/compiler.s is standalone
4. **Simpler usage** - Just `./compiler file.lang`

However, we should ALSO save:
- **Reader AST** - For emergency kernel-only recovery
- **LLVM IR** - For cross-platform bootstrap

## Comparison: Current vs Proposed

| Aspect | Current | Proposed |
|--------|---------|----------|
| Generations verified | 1 (candidate vs candidate_v2) | 2 (trusted→gen1→gen2) |
| Kernel fixed point | Yes (asm diff) | Yes (asm diff) |
| AST fixed point | No | Yes (ast diff) |
| Standalone fixed point | No (only functionality) | Yes (asm diff) |
| LLVM fixed point | No | No (future work) |
| Tests run when | Before all fixed points | After all fixed points |
| Artifacts saved | standalone + llvm | standalone + llvm + ast |

## Implementation

### Pseudocode for New Verify

```makefile
verify:
    # Stage 1: Root of trust
    ctrusted = assemble(bootstrap/current/compiler.s)

    # Stage 2: Generation 1
    kernel1.s = ctrusted.compile(KERNEL_SOURCES)
    kernel1 = assemble + link(kernel1.s)
    reader_ast1 = ctrusted.emit_ast(lang_reader.lang)
    lang1 = kernel1 -r reader_ast1  # composed compiler

    # Stage 3: Generation 2 + Kernel Fixed Point
    kernel2.s = lang1.compile(KERNEL_SOURCES)
    reader_ast2 = lang1.emit_ast(lang_reader.lang)

    ASSERT: kernel1.s === kernel2.s          # KERNEL FIXED POINT
    ASSERT: reader_ast1 === reader_ast2      # AST FIXED POINT

    kernel2 = assemble + link(kernel2.s)
    lang2 = kernel2 -r reader_ast2

    # Stage 4: Standalone Fixed Point
    standalone1.s = lang2.compile(-c lang, lang_reader.lang)
    standalone1 = assemble + link(standalone1.s)

    standalone2.s = standalone1.compile(-c lang, lang_reader.lang)
    standalone2 = assemble + link(standalone2.s)

    standalone3.s = standalone2.compile(-c lang, lang_reader.lang)

    ASSERT: standalone2.s === standalone3.s  # STANDALONE FIXED POINT

    # Stage 5: Validation (ONLY after fixed points)
    run_test_suite(standalone2)  # Use the fixed-point compiler

    llvm.ll = standalone2.compile(sources, LANGBE=llvm)
    run_llvm_test_suite(llvm.ll)

    # Stage 6: Ready for promote
    echo "All verifications passed"
```

### File Layout After Promote

```
bootstrap/
  COMMIT/
    compiler.s              # candidate_standalone2.s (THE FIXED-POINT ARTIFACT)
    llvm_libc_compiler.ll   # LLVM IR for cross-platform
    lang_reader/
      source.ast            # For emergency recovery
    PROVENANCE              # Chain of trust documentation
  current -> COMMIT/
  escape_hatch.s            # Copy of compiler.s for emergency
```

## LLVM Fixed Point (Future Work)

The full chain would also verify:
```
llvm1 = standalone.compile(sources, LANGBE=llvm)
llvm2 = llvm1.compile(sources, LANGBE=llvm)
ASSERT: llvm1.ll === llvm2.ll
```

This is not currently implemented because:
1. LLVM output may have non-deterministic ordering
2. Would significantly slow down verification
3. x86 fixed point is sufficient for correctness

## Deep Analysis: Why Two Generations?

### The Subtle Bug We're Catching

Consider a compiler with a bug in its string escaping:
```
Gen 0 (trusted bootstrap): Correctly escapes "\n" as 0x0a
Gen 1 (built by Gen 0):    Bug: outputs "\n" as literal backslash-n
Gen 2 (built by Gen 1):    Bug manifests: string data is wrong
```

Single-generation verification (current):
- Gen 0 builds Gen 1
- Gen 1 builds Gen 1' (itself)
- Compare Gen 1.s === Gen 1'.s
- **PASSES** because both have the same bug

Two-generation verification (proposed):
- Gen 0 builds Gen 1
- Gen 1 builds Gen 2
- Gen 2 builds Gen 3
- Compare Gen 2.s === Gen 3.s
- **FAILS** because the bug causes drift

### Why Standalone Fixed Point is Separate

The kernel fixed point proves:
```
kernel(kernel_sources) = kernel.s  // stable
```

But standalone combines kernel + embedded reader. The embedding could have bugs:
```
standalone = kernel(kernel_sources + reader_embedding)
```

Even if the kernel is stable, the embedding might not be. So we need:
```
standalone2 = standalone1(-c lang, lang_reader)
standalone3 = standalone2(-c lang, lang_reader)
VERIFY: standalone2 === standalone3
```

Note: We verify `standalone2 === standalone3`, NOT `standalone1 === standalone2`.

Why? Because standalone1 was built by `lang2` (a composed kernel+reader), while standalone2 and standalone3 are both built by standalones. The standalone format might have different characteristics than the composed format.

By verifying `standalone2 === standalone3`, we prove:
- Standalone compilers reach their own fixed point
- The standalone format is self-consistent
- Two generations of "standalone builds standalone" converge

### The Full Trust Chain

```
bootstrap.s (axiom - we trust this)
    │
    ▼ assembles to
ctrusted
    │
    ├──▶ compiles kernel sources → kernel1
    │
    └──▶ emits reader AST → reader_ast1
              │
              ▼ compose
         lang1 = kernel1 -r reader_ast1
              │
              ├──▶ compiles kernel sources → kernel2
              │         │
              │         └──▶ VERIFY: kernel1.s === kernel2.s ✓
              │
              └──▶ emits reader AST → reader_ast2
                        │
                        └──▶ VERIFY: reader_ast1 === reader_ast2 ✓
                                  │
                                  ▼ compose
                             lang2 = kernel2 -r reader_ast2
                                  │
                                  └──▶ builds standalone → standalone1
                                            │
                                            └──▶ builds standalone → standalone2
                                                      │
                                                      └──▶ builds standalone → standalone3
                                                                │
                                                                └──▶ VERIFY: standalone2 === standalone3 ✓
```

### What Each Verification Proves

| Check | Proves |
|-------|--------|
| kernel1.s === kernel2.s | Kernel codegen is deterministic and self-consistent |
| reader_ast1 === reader_ast2 | AST emission is deterministic |
| standalone2 === standalone3 | Standalone format is self-hosting |

All three must pass. Any failure indicates a compiler bug that would manifest in production use.

## Summary

### What We Gain

1. **Mathematical rigor** - True multi-generation fixed point
2. **Standalone self-hosting** - Compiler can recreate itself
3. **AST stability** - Reader output is consistent
4. **Clear test ordering** - Fixed points first, functionality second

### Migration Path

1. Implement new verify stages incrementally
2. Keep old verify as `verify-legacy` during transition
3. Once stable, remove legacy
4. Update CLAUDE.md with new invariants

### The One Command

```bash
make bootstrap    # All fixed points + all tests + promote (atomic operation)
```

Nothing else. No shortcuts. No partial verification. One command. Can't fuck it up.

## Appendix A: Side-by-Side Command Comparison

### Current `make verify`

```bash
# Phase 1-2: Bootstrap and build
as bootstrap/current/compiler.s -o /tmp/boot.o
ld /tmp/boot.o -o /tmp/boot
/tmp/boot std/core.lang src/*.lang -o out/lang_VERSION.s
as out/lang_VERSION.s -o out/lang_VERSION.o
ld out/lang_VERSION.o -o out/lang_VERSION

# Phase 3: Kernel fixed point (ONE generation)
./out/lang_VERSION std/core.lang src/*.lang -o out/lang_VERSION_v2.s
diff out/lang_VERSION.s out/lang_VERSION_v2.s  # Must match

# Phase 4: Build standalone (NO fixed point check!)
./out/lang_next -c lang src/lang_reader.lang -o out/lang_standalone.s
as out/lang_standalone.s -o out/lang_standalone.o
ld out/lang_standalone.o -o out/lang_standalone

# Phase 5: "Reader fixed point" (actually just a smoke test)
echo 'func main() i64 { return 42; }' > /tmp/test42.lang
./out/lang_standalone /tmp/test42.lang -o /tmp/test42.s
# ... assemble and run, check exit code is 42

# Phase 6-8: Tests
./test/run_lang1_suite.sh
./test/run_llvm_suite.sh
```

### Proposed `make verify`

```bash
# Stage 1: Root of trust
as bootstrap/current/compiler.s -o /tmp/boot.o
ld /tmp/boot.o -o /tmp/ctrusted

# Stage 2: Generation 1 (built by trusted)
/tmp/ctrusted std/core.lang src/*.lang -o /tmp/kernel1.s
as /tmp/kernel1.s -o /tmp/kernel1.o
ld /tmp/kernel1.o -o /tmp/kernel1

/tmp/ctrusted src/lang_reader.lang --emit-expanded-ast -o /tmp/reader_ast1.ast

# Compose lang1
# (kernel1 can run with -r to load reader)
# For now, we use the trusted compiler for composition:
/tmp/ctrusted -c lang src/lang_reader.lang -o /tmp/lang1.s
as /tmp/lang1.s -o /tmp/lang1.o
ld /tmp/lang1.o -o /tmp/lang1

# Stage 3: Generation 2 (built by lang1)
/tmp/lang1 std/core.lang src/*.lang -o /tmp/kernel2.s
/tmp/lang1 src/lang_reader.lang --emit-expanded-ast -o /tmp/reader_ast2.ast

# KERNEL FIXED POINT
diff /tmp/kernel1.s /tmp/kernel2.s  # Must match!

# AST FIXED POINT
diff /tmp/reader_ast1.ast /tmp/reader_ast2.ast  # Must match!

# Build lang2 (using verified kernel2 + reader_ast2)
as /tmp/kernel2.s -o /tmp/kernel2.o
ld /tmp/kernel2.o -o /tmp/kernel2

/tmp/lang1 -c lang src/lang_reader.lang -o /tmp/lang2.s  # Or compose kernel2 + reader_ast2
as /tmp/lang2.s -o /tmp/lang2.o
ld /tmp/lang2.o -o /tmp/lang2

# Stage 4: Standalone fixed point
# standalone1 built by lang2
/tmp/lang2 -c lang src/lang_reader.lang -o /tmp/standalone1.s
as /tmp/standalone1.s -o /tmp/standalone1.o
ld /tmp/standalone1.o -o /tmp/standalone1

# standalone2 built by standalone1
/tmp/standalone1 -c lang src/lang_reader.lang -o /tmp/standalone2.s
as /tmp/standalone2.s -o /tmp/standalone2.o
ld /tmp/standalone2.o -o /tmp/standalone2

# standalone3 built by standalone2
/tmp/standalone2 -c lang src/lang_reader.lang -o /tmp/standalone3.s

# STANDALONE FIXED POINT
diff /tmp/standalone2.s /tmp/standalone3.s  # Must match!

# Stage 5: Validation (using standalone2 as the verified compiler)
COMPILER=/tmp/standalone2 ./test/run_lang1_suite.sh

# Stage 6: LLVM validation
/tmp/standalone2 std/core.lang src/*.lang -o /tmp/llvm_compiler.ll LANGBE=llvm
clang -O2 /tmp/llvm_compiler.ll -o /tmp/llvm_compiler
COMPILER=/tmp/llvm_compiler ./test/run_llvm_suite.sh

# All passed - ready for promote
cp /tmp/standalone2.s out/lang_standalone.s  # The verified artifact
cp /tmp/llvm_compiler.ll out/llvm_libc_compiler.ll
```

## Appendix B: Choosing the Final Artifact

### Why `standalone2` (not `standalone1`)

```
standalone1: Built by lang2 (composed format)
standalone2: Built by standalone1 (standalone format)
standalone3: Built by standalone2 (standalone format)

We verified: standalone2 === standalone3
Therefore: standalone2 is the fixed point
```

The fixed point IS `standalone2` because:
1. It was built by a standalone compiler (standalone1)
2. It produces identical output (standalone3)
3. It's fully self-hosting within its own format

`standalone1` is an intermediate - built by the composed format, not the standalone format. It might have subtle differences that disappear once we're in pure standalone territory.

### Why `standalone2` (not `lang2`)

| Artifact | Pros | Cons |
|----------|------|------|
| lang2 | Kernel + reader separate, more modular | Requires reader AST file, more complex usage |
| standalone2 | Self-contained, simple usage, true fixed point | Larger binary (embedded reader), less modular |

**Decision: `standalone2`** for these reasons:
1. **Usability**: Users just run `./compiler file.lang`
2. **Fixed point proven**: We verified standalone2 === standalone3
3. **Matches current bootstrap**: We already use standalone format
4. **Simpler recovery**: One file to restore, not kernel + AST

BUT we also save the reader AST for emergency kernel-only recovery.

## Appendix C: Time and Complexity Estimates

### Current verify
- Phases: 8
- Compiler builds: 3 (boot→lang, lang→lang_v2, lang→standalone)
- Fixed point checks: 1 (kernel) + 1 fake (test42)
- Estimated time: ~45 seconds

### Proposed verify
- Stages: 6
- Compiler builds: 7 (boot→kernel1, boot→lang1, lang1→kernel2, lang1→lang2, lang2→standalone1, standalone1→standalone2, standalone2→standalone3)
- Fixed point checks: 3 (kernel, AST, standalone)
- Estimated time: ~90 seconds

The extra time is worth it for mathematical certainty.
