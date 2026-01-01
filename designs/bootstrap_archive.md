# Bootstrap Archive Design

## Problem

The `bootstrap/` directory grows with every `make bootstrap`:
- Each bootstrap: ~4MB (2× 2MB .ll files + ~200KB AST)
- Current: 50+ folders = ~200MB in git history
- Git keeps ALL history - deleting files doesn't shrink the repo

**Key insight:** Compressing or deleting old bootstraps in git does nothing. The `.git/objects/` still contains every version ever committed.

## Solution: GitHub Releases

Store only `bootstrap/current/` in git. Archive historical bootstraps to GitHub Releases.

```
# In git (~4MB forever):
bootstrap/
├── current/                 # Symlink to active commit folder
├── <current-commit>/        # Only the active bootstrap
│   ├── compiler_linux.ll
│   ├── compiler_macos.ll
│   ├── lang_reader/source.ast
│   └── PROVENANCE
└── HISTORY.md               # Documents the chain, links to releases

# In GitHub Releases (grows, but external):
bootstrap-abc1234.tar.gz     # Each historical bootstrap
bootstrap-def5678.tar.gz
...
```

## Goals

1. Git repo stays under 50MB for bootstraps (only current)
2. Full history preserved in GitHub Releases
3. Chain of trust documented and verifiable
4. Easy retrieval of any historical bootstrap
5. Automated via Makefile

## Non-Goals

- Keeping history in git (that's the problem)
- Complex tiering (unnecessary with external storage)
- Self-hosted storage (GitHub Releases is free and sufficient)

---

## Directory Structure

### In Git

```
bootstrap/
├── current -> abc1234/
├── abc1234/
│   ├── compiler_linux.ll    # ~2MB
│   ├── compiler_macos.ll    # ~2MB
│   ├── lang_reader/
│   │   └── source.ast       # ~200KB
│   └── PROVENANCE           # Build metadata
├── HISTORY.md               # Chain of trust documentation
└── .gitignore               # Ignore restored archives
```

### .gitignore

```gitignore
# Ignore restored historical bootstraps
# Only current commit folder should be tracked
**/
!current/
!HISTORY.md
!.gitignore
```

Wait, that's tricky with the symlink. Simpler approach:

```
bootstrap/
├── current/                 # Actual directory (not symlink)
│   ├── compiler_linux.ll
│   ├── compiler_macos.ll
│   ├── lang_reader/source.ast
│   ├── PROVENANCE
│   └── COMMIT               # File containing commit hash
└── HISTORY.md
```

### HISTORY.md Format

```markdown
# Bootstrap History

## Current
- Commit: abc1234
- Date: 2026-01-01
- Built by: def5678

## Chain of Trust
| Commit | Date | Built By | Tag | Release |
|--------|------|----------|-----|---------|
| abc1234 | 2026-01-01 | def5678 | | [current] |
| def5678 | 2025-12-28 | 111aaaa | v0.1.0 | [download](releases/tag/bootstrap-def5678) |
| 111aaaa | 2025-12-20 | 222bbbb | | [download](releases/tag/bootstrap-111aaaa) |
| ... | | | | |
| 000init | 2025-01-01 | go-bootstrap | v0.0.0 | [download](releases/tag/bootstrap-founding) |

## Founding Bootstrap
The original bootstrap was created by the Go-based bootstrap compiler
and verified through the initial self-hosting process.
```

---

## Workflow

### make bootstrap (updated)

```bash
# After successful verification...

# 1. Archive current bootstrap to GitHub Release
OLD_COMMIT=$(cat bootstrap/current/COMMIT)
if [ -n "$OLD_COMMIT" ]; then
    tar -czf /tmp/bootstrap-${OLD_COMMIT}.tar.gz -C bootstrap current/
    gh release create bootstrap-${OLD_COMMIT} \
        /tmp/bootstrap-${OLD_COMMIT}.tar.gz \
        --title "Bootstrap ${OLD_COMMIT}" \
        --notes "Archived bootstrap from commit ${OLD_COMMIT}"
    rm /tmp/bootstrap-${OLD_COMMIT}.tar.gz
fi

# 2. Replace current with new
rm -rf bootstrap/current/*
cp -r /tmp/bootstrap_verify/* bootstrap/current/
echo "${GIT_COMMIT}" > bootstrap/current/COMMIT

# 3. Update HISTORY.md
# (prepend new entry to chain table)

# 4. Commit
git add bootstrap/
git commit -m "Bootstrap ${GIT_COMMIT}"
```

### make bootstrap-restore

```bash
# Usage: make bootstrap-restore COMMIT=abc1234

COMMIT ?= $(error COMMIT is required)

bootstrap-restore:
	@echo "Downloading bootstrap $(COMMIT)..."
	gh release download bootstrap-$(COMMIT) -D /tmp/
	tar -xzf /tmp/bootstrap-$(COMMIT).tar.gz -C /tmp/
	@echo "Restored to /tmp/bootstrap-$(COMMIT)/"
	@echo "To use: clang -O2 /tmp/bootstrap-$(COMMIT)/current/compiler_macos.ll -o lang"
```

### make bootstrap-list

```bash
bootstrap-list:
	@echo "Available bootstraps:"
	@gh release list --limit 100 | grep "^bootstrap-" | awk '{print $$1}'
```

---

## Tagging Releases

### Semantic Version Tags

When releasing a version (e.g., v0.1.0):

```bash
# Tag the commit
git tag v0.1.0

# The bootstrap release already exists as bootstrap-<commit>
# Create an alias release for the version
gh release create v0.1.0-bootstrap \
    --notes "Bootstrap for v0.1.0 release" \
    --target $(git rev-parse v0.1.0)

# Or just document in HISTORY.md that bootstrap-abc1234 = v0.1.0
```

### Founding Bootstrap

The initial bootstraps that established self-hosting get a special release:

```bash
gh release create bootstrap-founding \
    founding-bootstraps.tar.gz \
    --title "Founding Bootstraps" \
    --notes "The original bootstrap chain that established self-hosting"
```

---

## Migration Plan

### Phase 1: Archive Existing History

```bash
# For each existing bootstrap folder (except current):
for dir in bootstrap/*/; do
    commit=$(basename "$dir")
    if [ "$commit" != "current" ] && [ -d "$dir" ]; then
        tar -czf /tmp/bootstrap-${commit}.tar.gz -C bootstrap "$commit"
        gh release create bootstrap-${commit} \
            /tmp/bootstrap-${commit}.tar.gz \
            --title "Bootstrap ${commit}" \
            --notes "Historical bootstrap"
    fi
done
```

### Phase 2: Restructure Directory

```bash
# Save current
CURRENT=$(readlink bootstrap/current || ls -t bootstrap/ | head -1)
cp -r bootstrap/$CURRENT /tmp/current-backup

# Clean bootstrap directory
rm -rf bootstrap/*

# Create new structure
mkdir -p bootstrap/current
cp -r /tmp/current-backup/* bootstrap/current/
echo "$CURRENT" > bootstrap/current/COMMIT

# Create HISTORY.md
cat > bootstrap/HISTORY.md << 'EOF'
# Bootstrap History
... (generate from archived releases)
EOF
```

### Phase 3: Update Makefile

Add archive step to `make bootstrap` target.

### Phase 4: Clean Git History (Optional)

If we want to reclaim space from existing history:

```bash
# WARNING: This rewrites history and breaks all clones
# Only do this with team coordination

# Using BFG Repo Cleaner
bfg --delete-folders '{folder1,folder2,...}' --no-blob-protection repo.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

This is optional - we can just let old history exist and prevent future growth.

---

## Size Analysis

### Current State
- Git repo: ~200MB (50+ bootstrap folders in history)
- Each `make bootstrap`: +4MB to history

### After Migration
- Git repo: ~200MB initially (history preserved)
- Each `make bootstrap`: +0MB to git (goes to Releases)
- GitHub Releases: grows at 4MB per bootstrap

### Long Term
- Git repo: ~200MB forever (or less if we rewrite history)
- GitHub Releases: 4MB × N bootstraps
- 1000 bootstraps = 4GB in Releases (GitHub allows 2GB per file, unlimited releases)

---

## Implementation Checklist

- [ ] Create `scripts/archive-bootstrap.sh`
- [ ] Create `scripts/restore-bootstrap.sh`
- [ ] Update Makefile with new targets
- [ ] Archive all existing bootstraps to Releases
- [ ] Restructure `bootstrap/` directory
- [ ] Create HISTORY.md with full chain
- [ ] Update CLAUDE.md with new workflow
- [ ] (Optional) Rewrite git history to reclaim space

---

## GitHub Releases Limits & Pruning

### Storage Limits

| Limit | Value |
|-------|-------|
| File size per release | 2GB max |
| Number of releases | Unlimited |
| Total storage | Unlimited (public repos) |
| Bandwidth | Unlimited downloads |

For private repos, storage counts against your plan's limit. Public repos have no practical limit.

### Size Projection

- Each bootstrap: ~1MB compressed (.tar.gz)
- 100 bootstraps: ~100MB
- 1000 bootstraps: ~1GB
- 10000 bootstraps: ~10GB (decades of development)

**Verdict:** Storage is not a concern. Don't need to prune for space.

### Pruning Strategy

**Should you prune?** Optional, but can improve cleanliness.

**What to keep forever:**
- Tagged releases (v0.1.0, v0.2.0, etc.)
- Founding bootstraps (chain of trust roots)
- Monthly milestones (first bootstrap of each month)

**What can be pruned:**
- Intermediate bootstraps older than 6 months
- Failed experiments (if any got released)

**Pruning command:**
```bash
# List old untagged bootstraps
gh release list --limit 500 | grep "bootstrap-" | while read line; do
    name=$(echo "$line" | awk '{print $1}')
    date=$(echo "$line" | awk '{print $3}')
    # Check if older than 6 months and not tagged
    # ... logic here
done

# Delete a specific release
gh release delete bootstrap-abc1234 --yes
```

**Recommendation:** Don't prune initially. Revisit if you hit 1000+ releases and want cleaner UI. The storage cost is zero.

---

## Open Questions

1. **Rewrite history?**
   - Pro: Reclaim ~150MB
   - Con: Breaks all clones, confuses contributors
   - Recommendation: No, just prevent future growth

2. **Release naming?**
   - `bootstrap-abc1234` (by commit)
   - `bootstrap-2026-01-01-abc1234` (with date)
   - Recommendation: Commit only, date is in release metadata

3. **Founding bundle?**
   - Single release with first N bootstraps?
   - Or individual releases for each?
   - Recommendation: Individual, with `bootstrap-founding` as alias to first
