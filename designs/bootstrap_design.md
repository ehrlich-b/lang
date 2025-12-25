# Bootstrap System Design

## Problem

The current `lang1/lang2/lang3` naming scheme has issues:

1. **Conflates stage with version** - "lang2" means "second stage of bootstrap" not "version 2"
2. **No git connection** - Can't tell which source produced which binary
3. **Confusing after fixed point** - lang2.s == lang3.s but different names
4. **No release story** - How do we preserve/restore known-good states?

## Goals

1. **Version-centric naming** - Binaries named by git commit/tag, not stage number
2. **Clear trust chain** - Obvious which compiler is "trusted" vs "candidate"
3. **Git tag integration** - Each release tag has a preserved fixed-point artifact
4. **Reproducible bootstrap** - Can rebuild from any tagged version
5. **Simple verification** - Easy to check fixed-point property

## Design

### Directory Structure

```
bootstrap/
  v0.1.0.s              # Fixed-point assembly for each release
  v0.2.0.s
  ...

out/
  lang                  # symlink -> current trusted compiler
  lang_next             # symlink -> candidate being verified
  lang_v0.1.0           # binary from bootstrap/v0.1.0.s
  lang_a3f2c1d          # binary from src/ at commit a3f2c1d
```

### Naming Convention

| Artifact | Name | Example |
|----------|------|---------|
| Tagged release binary | `lang_<tag>` | `lang_v0.1.0` |
| Development binary | `lang_<short-hash>` | `lang_a3f2c1d` |
| Current trusted | `lang` symlink | `lang -> lang_v0.1.0` |
| Candidate | `lang_next` symlink | `lang_next -> lang_a3f2c1d` |

### Makefile Targets

```make
bootstrap       # Assemble from latest bootstrap/*.s, create lang symlink
build           # Compile src/*.lang using lang -> lang_next
verify          # lang_next compiles src/*.lang, check fixed point
promote         # Update lang symlink to point to lang_next target
release TAG=x   # Save .s to bootstrap/, git tag, update symlinks
clean           # Remove non-tagged binaries
```

### Workflows

#### Fresh Clone
```bash
git clone ...
make bootstrap    # Assembles bootstrap/v0.1.0.s -> out/lang_v0.1.0
                  # Creates symlink: lang -> lang_v0.1.0
```

#### Development Cycle
```bash
# Edit src/*.lang
make build        # lang compiles src/ -> out/lang_<commit>.s
                  # Assembles -> out/lang_<commit>
                  # Creates symlink: lang_next -> lang_<commit>

make verify       # lang_next compiles src/ -> out/verify.s
                  # Checks: lang_<commit>.s == verify.s (fixed point)

make promote      # Updates: lang -> lang_<commit>
                  # Removes lang_next symlink
```

#### Release
```bash
make release TAG=v0.2.0
# 1. Verifies current state is a fixed point
# 2. Copies out/lang_<commit>.s -> bootstrap/v0.2.0.s
# 3. Creates git tag v0.2.0
# 4. Updates lang symlink
```

### Verification Logic

The fixed-point property: a compiler that compiles its own source produces identical output.

```
lang (trusted)  ──compile──>  candidate.s  ──assemble──>  lang_next
lang_next       ──compile──>  verify.s

assert: candidate.s == verify.s
```

If they match, `lang_next` is a valid fixed point and can be trusted.

### Why This Design

**Git-centric**: Every binary traces to a specific commit. No ambiguity.

**Trust is explicit**: The `lang` symlink is the trust anchor. You always know what you're trusting.

**History preserved**: bootstrap/ directory contains every release's fixed point. Can rebuild any version.

**Stages are transient**: "lang_next" exists only during verification. After promote, it's just "lang".

**Clean rollback**: If verification fails, lang symlink still points to last known-good. No damage.

### Migration

1. Rename `stage1-bootstrap.s` -> `bootstrap/v0.1.0.s`
2. Create initial git tag `v0.1.0`
3. Update Makefile with new targets
4. Update .gitignore for out/ binaries

### Edge Cases

**Dirty working tree**: `make build` uses current HEAD commit hash. If tree is dirty, appends `-dirty` suffix: `lang_a3f2c1d-dirty`.

**No tags yet**: `make bootstrap` finds latest .s file alphabetically or errors with instructions.

**Multiple developers**: Each works from same bootstrap/*.s. Candidates are local until release.
