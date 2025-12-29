# Compiler Layers: Bootstrap, Composition, and Emission

## The Core Equation

```
lang_compiler = kernel + lang_reader
```

This is not a new architecture - it's what we already have. The split makes it explicit:

- **kernel**: `src/codegen.lang` + `src/sexpr_reader.lang` + glue
- **lang_reader**: `src/parser.lang` + `src/ast_emit.lang` + glue

The `--emit-ast` flag IS the lang_reader. The `--from-ast` flag IS the kernel entry point.
We're not building new things - we're extracting what exists.

---

## Current Bootstrap Architecture

### What We Have Now

```
bootstrap/
├── current.s          # symlink → latest verified .s
├── v0.1.0.s           # release checkpoints
├── 2411534.s          # commit-based checkpoints
├── 3bc135d.s
└── ...
```

**Makefile targets:**
- `make bootstrap` - Assemble `bootstrap/current.s` → `out/lang_bootstrap`, symlink `out/lang`
- `make build` - `out/lang` compiles `src/*.lang` → `out/lang_next`
- `make verify` - `out/lang_next` compiles `src/*.lang`, diff against itself (fixed point)
- `make promote` - `out/lang_next` → `out/lang`, save new `bootstrap/<commit>.s`

**The invariant:** `bootstrap/current.s` can always rebuild the compiler from nothing.

### What's Actually In bootstrap/current.s

It's the **entire compiler** as x86 assembly: lexer, parser, codegen, ast_emit, sexpr_reader, main.
All of `src/*.lang` compiled to a single .s file.

This is `kernel + lang_reader` already - just monolithic.

---

## The New Bootstrap Architecture

### Directory Structure

```
bootstrap/
├── current → ./2411534/              # symlink to latest verified snapshot
├── escape_hatch.s                    # assembly for emergency (rare)
│
├── 2411534/                          # snapshot by commit hash
│   ├── kernel/
│   │   ├── source.ast                # kernel as S-expr AST
│   │   └── PROVENANCE                # what built this, from what
│   └── lang_reader/
│       ├── source.ast                # lang_reader as S-expr AST
│       └── PROVENANCE
│
├── 3bc135d/                          # previous snapshot
│   ├── kernel/
│   │   ├── source.ast
│   │   └── PROVENANCE
│   └── lang_reader/
│       ├── source.ast
│       └── PROVENANCE
│
├── 16fa7a7/                          # even older
│   └── ...
│
└── v0.1.0/                           # release tags too
    └── ...
```

### The Chain is Preserved

Every snapshot records what built it:

```
# bootstrap/2411534/kernel/PROVENANCE
artifact: source.ast
sha256: a1b2c3d4...
built_by: bootstrap/3bc135d            # ← points to previous snapshot
built_at: 2025-01-15T10:30:00Z
source_commit: 2411534
source_files:
  - src/codegen.lang @ sha256:...
  - src/sexpr_reader.lang @ sha256:...
verified_fixed_point: true
```

```
# bootstrap/2411534/lang_reader/PROVENANCE
artifact: source.ast
sha256: e5f6g7h8...
built_by: bootstrap/3bc135d            # ← same: built by previous
built_at: 2025-01-15T10:30:00Z
source_commit: 2411534
source_files:
  - src/lexer.lang @ sha256:...
  - src/parser.lang @ sha256:...
  - src/ast_emit.lang @ sha256:...
verified_fixed_point: true
```

### Walking the Chain

```
bootstrap/current → bootstrap/2411534
    built_by: bootstrap/3bc135d
        built_by: bootstrap/16fa7a7
            built_by: bootstrap/v0.1.0
                built_by: escape_hatch.s   # the root of trust
```

You can always trace any bootstrap artifact back to the assembly escape hatch.

### Why Separate Folders?

Kernel and lang_reader evolve independently:

```
bootstrap/2411534/
├── kernel/           # unchanged from 3bc135d (kernel didn't change)
│   └── PROVENANCE: "copied from bootstrap/3bc135d/kernel"
└── lang_reader/      # rebuilt (parser changed)
    └── PROVENANCE: "built by bootstrap/3bc135d"
```

When only the reader changes, the kernel PROVENANCE just says "copied" - no rebuild needed.
When only the kernel changes, the reader PROVENANCE says "copied".
This makes it clear what actually changed.

### What Changes

| Old | New |
|-----|-----|
| One bootstrap artifact (full compiler .s) | Two artifacts: kernel.ast + lang_reader.ast |
| Bootstrap = assemble from .s | Bootstrap = kernel processes lang_reader.ast |
| Fixed point = .s matches .s | Fixed point = .ast matches .ast |

### The Key Files

**kernel source** (what we're extracting):
```
src/codegen.lang      # AST → x86
src/sexpr_reader.lang # S-expr → internal AST nodes
src/limits.lang       # shared constants
std/core.lang         # runtime (malloc, etc.)
src/kernel_main.lang  # NEW: entry point for kernel-only binary
```

**lang_reader source** (what we're extracting):
```
src/lexer.lang        # tokens
src/parser.lang       # lang syntax → internal AST
src/ast_emit.lang     # internal AST → S-expr text
src/reader_main.lang  # NEW: entry point for reader-only binary
```

---

## Bootstrap Flows

### Normal Development (No Bootstrap Needed)

```
src/*.lang  ──[out/lang]──►  out/lang_next
                                  │
                                  ▼
                            make verify
                                  │
                                  ▼
                            make promote
                                  │
                                  ▼
                         out/lang updated
```

This doesn't change. `out/lang` = `kernel + lang_reader` as a single binary.

### Kernel-Only Bootstrap (From Assembly)

When: Kernel codegen changes, kernel has bugs, emergency recovery.

```
bootstrap/kernel/current.s  ──[as + ld]──►  out/kernel
                                                │
out/kernel + bootstrap/lang_reader/current.ast  │
                                                ▼
                                          out/lang
```

The assembly escape hatch. Rare. Only for kernel changes.

### Normal Bootstrap (From AST)

When: Starting fresh, lang_reader changes, normal rebuild.

```
out/kernel + bootstrap/lang_reader/current.ast ──► out/lang_reader
out/kernel + bootstrap/kernel/current.ast      ──► out/kernel_new

Verify: kernel_new + lang_reader can rebuild themselves (fixed point)
```

Key insight: **If you have a working kernel, you never need assembly.**

### The Bootstrap Ladder

```
Level 0: Assembly
    bootstrap/kernel/current.s → out/kernel (via assembler)
    This is the escape hatch. Everything else can be rebuilt from here.

Level 1: Kernel + lang_reader.ast
    out/kernel + lang_reader.ast → out/lang_reader
    out/kernel + kernel.ast → out/kernel (verify fixed point)

Level 2: Full compiler
    out/lang_reader | out/kernel = out/lang (conceptually)
    In practice, we emit a single binary that does both.

Level 3+: Additional readers
    out/lang + lisp_reader.lang → out/lang_lisp
    out/lang_lisp + sql_reader.lang → out/lang_lisp_sql
    ...
```

---

## Provenance Tracking

### Why It Matters

The bootstrap is only trustworthy if we know what built it. If `bootstrap/kernel/current.ast` was generated by a buggy compiler, we could be propagating bugs.

### PROVENANCE Files

```
# bootstrap/kernel/PROVENANCE
kernel_ast: current.ast
kernel_sha256: a1b2c3d4...
built_by: out/lang @ commit 2411534
built_at: 2025-01-15T10:30:00Z
source_files:
  - src/codegen.lang @ sha256:...
  - src/sexpr_reader.lang @ sha256:...
  - src/limits.lang @ sha256:...
verified_fixed_point: true
```

```
# bootstrap/lang_reader/PROVENANCE
reader_ast: current.ast
reader_sha256: e5f6g7h8...
built_by: out/lang @ commit 2411534
built_at: 2025-01-15T10:30:00Z
source_files:
  - src/lexer.lang @ sha256:...
  - src/parser.lang @ sha256:...
  - src/ast_emit.lang @ sha256:...
verified_fixed_point: true
```

### The Trust Chain

```
bootstrap/kernel/current.s    ← Emergency escape hatch (auditable assembly)
         │
         ▼
    out/kernel               ← Built from assembly
         │
         ├── bootstrap/kernel/current.ast       ← Built by out/kernel
         │         (verified: rebuilds identical kernel)
         │
         └── bootstrap/lang_reader/current.ast  ← Built by out/kernel + lang_reader
                   (verified: rebuilds identical lang_reader)
```

If you trust the assembly, you can verify everything else.

---

## The Two Fixed Points

There are two distinct fixed points with different shapes:

### Lang Reader Fixed Point (Common Path)

**When:** You change `src/parser.lang`, `src/lexer.lang`, or `src/ast_emit.lang`.

**What stays fixed:** The kernel (unchanged).

**What rebuilds:** The lang_reader.

```
┌─────────────────────────────────────────────────────────────────┐
│  LANG READER FIXED POINT                                        │
│                                                                  │
│  1. {kernel + lang_reader_v1} compiles lang_reader_v2.lang       │
│                                    ↓                             │
│                              lang_reader_v2                      │
│                                                                  │
│  2. {kernel + lang_reader_v2} compiles lang_reader_v2.lang       │
│                                    ↓                             │
│                              lang_reader_v2  ← must match!       │
└─────────────────────────────────────────────────────────────────┘
```

```bash
# Build new reader with current compiler
./out/lang -c lang_reader_v2 -o out/lang_next    # = {kernel + lang_reader_v2}

# Verify: new compiler rebuilds its reader identically
./out/lang_next -c lang_reader_v2 -o out/verify  # = {kernel + lang_reader_v2}
diff out/lang_next out/verify                    # ✓ fixed point
```

**PROVENANCE records:**
```yaml
lang_reader:
  parsed_by: snapshot/prev/lang_reader   # v1 parsed the v2 source
  compiled_by: snapshot/prev/kernel      # kernel compiled the AST
  fixed_point: verified                  # v2 can rebuild itself
```

### Kernel Fixed Point (Rare Path)

**When:** You change `src/codegen.lang` or `src/sexpr_reader.lang`.

**What stays fixed:** The lang_reader (unchanged).

**What rebuilds:** The kernel.

```
┌─────────────────────────────────────────────────────────────────┐
│  KERNEL FIXED POINT                                             │
│                                                                  │
│  1. {kernel_v1 + lang_reader} compiles kernel_v2.lang            │
│                                    ↓                             │
│                               kernel_v2                          │
│                                                                  │
│  2. {kernel_v2 + lang_reader} compiles kernel_v2.lang            │
│                                    ↓                             │
│                               kernel_v2  ← must match!           │
└─────────────────────────────────────────────────────────────────┘
```

```bash
# Build new kernel with current compiler
./out/lang -c kernel_v2 -o out/lang_next    # = {kernel_v2 + lang_reader}

# Verify: new compiler rebuilds its kernel identically
./out/lang_next -c kernel_v2 -o out/verify  # = {kernel_v2 + lang_reader}
diff out/lang_next out/verify               # ✓ fixed point
```

**PROVENANCE records:**
```yaml
kernel:
  parsed_by: snapshot/prev/lang_reader   # reader parsed the kernel source
  compiled_by: snapshot/prev/kernel      # v1 compiled the AST
  fixed_point: verified                  # v2 can rebuild itself
```

**Critical:** The `parsed_by` field records WHICH lang_reader was trusted to parse the kernel source. This is the provenance chain.

### Escape Hatch (Emergency Only)

**When:** Both kernel AND lang_reader are untrusted/corrupted, or you're starting from scratch.

**What's different:** The escape hatch is the **full compiler** as assembly, not just the kernel. Because:
- To build a lang_reader, you need a kernel
- To build a kernel from lang source, you need a lang_reader
- Chicken and egg → the escape hatch breaks the cycle

```
┌─────────────────────────────────────────────────────────────────┐
│  ESCAPE HATCH BOOTSTRAP                                         │
│                                                                  │
│  escape_hatch.s ──[assemble]──► full_compiler_bootstrap         │
│                                        │                         │
│         ┌──────────────────────────────┼──────────────────┐      │
│         ↓                              ↓                  ↓      │
│    kernel.lang                  lang_reader.lang    (verify)     │
│         ↓                              ↓                         │
│    kernel_v1                    lang_reader_v1                   │
│         └──────────────┬───────────────┘                         │
│                        ↓                                         │
│              {kernel_v1 + lang_reader_v1}                        │
│                        ↓                                         │
│              First snapshot (PROVENANCE: escape_hatch.s)         │
└─────────────────────────────────────────────────────────────────┘
```

The escape hatch is **auditable assembly** - a human can read it and verify it does what it claims. Everything else is derived from it.

### Full Compiler Fixed Point (Monolithic Path - Current Behavior)

The existing `make verify` continues to work. It's conceptually:

```bash
# Build full compiler (kernel + lang_reader together)
./out/lang src/*.lang -o out/lang_next.s

# Full compiler rebuilds itself
./out/lang_next src/*.lang -o out/verify.s

# Fixed point check
diff out/lang_next.s out/verify.s  # must match
```

This is equivalent to doing both fixed points simultaneously. The split just makes the pieces visible.

---

## Makefile Changes

### Target Naming Philosophy

The targets are named to make the workflow clear:

| Target | When to use |
|--------|-------------|
| `verify-lang-reader-fixed-point` | After changing parser/lexer/ast_emit |
| `verify-kernel-fixed-point` | After changing codegen/sexpr_reader |
| `promote-lang-reader` | Save new lang_reader snapshot |
| `promote-kernel` | Save new kernel snapshot |
| `bootstrap-from-snapshot` | Normal rebuild from bootstrap/current |
| `bootstrap-from-escape-hatch` | Emergency rebuild from assembly |

### New Targets

```makefile
# Current commit for snapshot naming
GIT_COMMIT := $(shell git rev-parse --short HEAD)
BOOTSTRAP_DIR := bootstrap/$(GIT_COMMIT)
PREV_SNAPSHOT := $(shell readlink bootstrap/current 2>/dev/null)

# ============================================================
# BUILD TARGETS
# ============================================================

# Build kernel-only binary (for split mode)
build-kernel:
    $(LANG) std/core.lang src/limits.lang src/codegen.lang src/sexpr_reader.lang \
            src/kernel_main.lang -o out/kernel.s
    as out/kernel.s -o out/kernel.o
    ld out/kernel.o -o out/kernel

# Build lang_reader-only binary (for split mode)
build-lang-reader:
    $(LANG) std/core.lang src/limits.lang src/lexer.lang src/parser.lang \
            src/ast_emit.lang src/reader_main.lang -o out/lang_reader.s
    as out/lang_reader.s -o out/lang_reader.o
    ld out/lang_reader.o -o out/lang_reader

# ============================================================
# FIXED POINT VERIFICATION
# ============================================================

# Lang reader fixed point: {kernel + reader_v2} rebuilds reader_v2 identically
verify-lang-reader-fixed-point: build
    @echo "=== LANG READER FIXED POINT ==="
    @echo "Testing: {kernel + lang_reader_new} can rebuild lang_reader_new"
    $(LANG_NEXT) std/core.lang src/limits.lang src/lexer.lang src/parser.lang \
            src/ast_emit.lang src/reader_main.lang --emit-ast > /tmp/reader_v2.ast
    $(LANG_NEXT) std/core.lang src/limits.lang src/lexer.lang src/parser.lang \
            src/ast_emit.lang src/reader_main.lang -o /tmp/reader_v2.s
    # Rebuild with new compiler
    # (conceptually: kernel compiles the AST that reader_v2 just emitted)
    diff /tmp/reader_v2.ast <($(LANG_NEXT) ... --emit-ast)  # simplified
    @echo "✓ Lang reader fixed point verified"

# Kernel fixed point: {kernel_v2 + reader} rebuilds kernel_v2 identically
verify-kernel-fixed-point: build
    @echo "=== KERNEL FIXED POINT ==="
    @echo "Testing: {kernel_new + lang_reader} can rebuild kernel_new"
    $(LANG_NEXT) std/core.lang src/limits.lang src/codegen.lang src/sexpr_reader.lang \
            src/kernel_main.lang -o /tmp/kernel_v2.s
    # The new compiler should produce identical kernel assembly
    diff out/lang_$(VERSION).s /tmp/kernel_v2.s  # kernel portion
    @echo "✓ Kernel fixed point verified"

# Full fixed point (current behavior - both at once)
verify: build
    @echo "=== FULL COMPILER FIXED POINT ==="
    $(LANG_NEXT) src/*.lang -o out/verify.s
    diff out/lang_$(VERSION).s out/verify.s
    @echo "✓ Full compiler fixed point verified"
    @./test/run_lang1_suite.sh

# ============================================================
# SNAPSHOT / PROMOTE
# ============================================================

# Promote lang_reader: save AST, mark kernel as "copied"
promote-lang-reader: verify-lang-reader-fixed-point
    @mkdir -p $(BOOTSTRAP_DIR)/kernel $(BOOTSTRAP_DIR)/lang_reader
    # Emit new lang_reader AST
    $(LANG_NEXT) std/core.lang src/limits.lang src/lexer.lang src/parser.lang \
            src/ast_emit.lang src/reader_main.lang --emit-ast \
            > $(BOOTSTRAP_DIR)/lang_reader/source.ast
    # Copy kernel from previous (unchanged)
    cp bootstrap/current/kernel/source.ast $(BOOTSTRAP_DIR)/kernel/source.ast
    # Generate PROVENANCE
    ./scripts/gen_provenance.sh $(BOOTSTRAP_DIR) lang_reader $(PREV_SNAPSHOT)
    # Update symlink
    ln -sfn $(GIT_COMMIT) bootstrap/current
    @echo "✓ Promoted lang_reader: bootstrap/$(GIT_COMMIT)"

# Promote kernel: save AST, mark lang_reader as "copied"
promote-kernel: verify-kernel-fixed-point
    @mkdir -p $(BOOTSTRAP_DIR)/kernel $(BOOTSTRAP_DIR)/lang_reader
    # Emit new kernel AST
    $(LANG_NEXT) std/core.lang src/limits.lang src/codegen.lang src/sexpr_reader.lang \
            src/kernel_main.lang --emit-ast \
            > $(BOOTSTRAP_DIR)/kernel/source.ast
    # Copy lang_reader from previous (unchanged)
    cp bootstrap/current/lang_reader/source.ast $(BOOTSTRAP_DIR)/lang_reader/source.ast
    # Generate PROVENANCE
    ./scripts/gen_provenance.sh $(BOOTSTRAP_DIR) kernel $(PREV_SNAPSHOT)
    # Update symlink
    ln -sfn $(GIT_COMMIT) bootstrap/current
    @echo "✓ Promoted kernel: bootstrap/$(GIT_COMMIT)"

# Promote both (when both changed - rare)
promote-both: verify
    @mkdir -p $(BOOTSTRAP_DIR)/kernel $(BOOTSTRAP_DIR)/lang_reader
    $(LANG_NEXT) ... --emit-ast > $(BOOTSTRAP_DIR)/kernel/source.ast
    $(LANG_NEXT) ... --emit-ast > $(BOOTSTRAP_DIR)/lang_reader/source.ast
    ./scripts/gen_provenance.sh $(BOOTSTRAP_DIR) both $(PREV_SNAPSHOT)
    ln -sfn $(GIT_COMMIT) bootstrap/current
    @echo "✓ Promoted both: bootstrap/$(GIT_COMMIT)"

# ============================================================
# BOOTSTRAP
# ============================================================

# Normal bootstrap: rebuild from snapshot/current
bootstrap-from-snapshot:
    @if [ ! -L bootstrap/current ]; then \
        echo "ERROR: No bootstrap/current. Use bootstrap-from-escape-hatch."; \
        exit 1; \
    fi
    @echo "=== BOOTSTRAP FROM SNAPSHOT ==="
    @echo "Using: bootstrap/current -> $$(readlink bootstrap/current)"
    # First, assemble escape hatch to get a kernel that can process AST
    # (or use existing out/kernel if trusted)
    ./out/kernel --from-ast bootstrap/current/kernel/source.ast -o out/kernel.s
    as out/kernel.s -o out/kernel.o && ld out/kernel.o -o out/kernel
    ./out/kernel --from-ast bootstrap/current/lang_reader/source.ast -o out/lang_reader.s
    as out/lang_reader.s -o out/lang_reader.o && ld out/lang_reader.o -o out/lang_reader
    @echo "✓ Bootstrapped from snapshot"

# Emergency bootstrap: rebuild from auditable assembly
bootstrap-from-escape-hatch:
    @echo "=== EMERGENCY BOOTSTRAP FROM ESCAPE HATCH ==="
    @echo "WARNING: This is the nuclear option. Using escape_hatch.s"
    as bootstrap/escape_hatch.s -o out/lang_escape.o
    ld out/lang_escape.o -o out/lang_escape
    # Now use escape hatch compiler to rebuild everything
    ./out/lang_escape src/*.lang -o out/lang_rebuilt.s
    as out/lang_rebuilt.s -o out/lang_rebuilt.o
    ld out/lang_rebuilt.o -o out/lang_rebuilt
    # Verify fixed point
    ./out/lang_rebuilt src/*.lang -o /tmp/verify.s
    diff out/lang_rebuilt.s /tmp/verify.s
    ln -sf lang_rebuilt out/lang
    @echo "✓ Bootstrapped from escape hatch"
    @echo "Now run: make promote-both  (to create first snapshot)"

# ============================================================
# SPLIT VERIFICATION (optional, for debugging)
# ============================================================

verify-split-matches-monolithic:
    ./out/lang test.lang -o /tmp/mono.s
    ./out/lang_reader test.lang | ./out/kernel -o /tmp/split.s
    diff /tmp/mono.s /tmp/split.s
    @echo "✓ Split matches monolithic"
```

### Typical Workflows

**Lang reader change (common):**
```bash
vim src/parser.lang                    # make your change
make build                             # build out/lang_next
make verify-lang-reader-fixed-point    # verify reader can rebuild itself
make promote-lang-reader               # save snapshot, kernel marked "copied"
```

**Kernel change (rare):**
```bash
vim src/codegen.lang                   # make your change
make build                             # build out/lang_next
make verify-kernel-fixed-point         # verify kernel can rebuild itself
make promote-kernel                    # save snapshot, reader marked "copied"
```

**Emergency recovery:**
```bash
make bootstrap-from-escape-hatch       # rebuild from assembly
make promote-both                      # create first snapshot from escape hatch
```

### Backward Compatibility

The existing `make build`, `make verify`, `make promote` continue to work as before.
They operate on the full monolithic compiler. The new split targets are additive.

---

## What Needs to Be Created

### 1. Entry Point Files (Small)

**src/kernel_main.lang** (~50 lines):
```lang
// Kernel entry point: S-expr AST → x86 assembly
// Reads AST from file or stdin, writes assembly to stdout or -o file

func main(argc i64, argv **u8) i64 {
    // Parse args: input file, -o output
    // Read S-expr AST
    // Call codegen
    // Write assembly
}
```

**src/reader_main.lang** (~50 lines):
```lang
// Lang reader entry point: lang source → S-expr AST
// Reads lang from file or stdin, writes AST to stdout

func main(argc i64, argv **u8) i64 {
    // Parse args: input files
    // For each file: lex, parse, emit AST
    // Write to stdout
}
```

### 2. Initial Bootstrap Snapshot

```bash
# Create the first snapshot using current monolithic compiler
mkdir -p bootstrap/$(git rev-parse --short HEAD)/{kernel,lang_reader}

# Emit kernel AST
./out/lang src/kernel_files... --emit-ast > bootstrap/<commit>/kernel/source.ast

# Emit lang_reader AST
./out/lang src/reader_files... --emit-ast > bootstrap/<commit>/lang_reader/source.ast

# Create PROVENANCE (first one points to escape_hatch.s)
# Set current symlink
ln -s <commit> bootstrap/current
```

This becomes the "seed" - after that, each snapshot builds on the previous.

### 3. PROVENANCE Generation Script

**scripts/gen_provenance.sh**:
```bash
#!/bin/bash
# Usage: gen_provenance.sh <new_snapshot_dir> <previous_snapshot>

SNAPSHOT=$1
PREVIOUS=$2
COMMIT=$(basename $SNAPSHOT)
TIMESTAMP=$(date -Iseconds)

for component in kernel lang_reader; do
    cat > $SNAPSHOT/$component/PROVENANCE << EOF
artifact: source.ast
sha256: $(sha256sum $SNAPSHOT/$component/source.ast | cut -d' ' -f1)
built_by: ${PREVIOUS:-escape_hatch.s}
built_at: $TIMESTAMP
source_commit: $COMMIT
verified_fixed_point: pending
EOF
done
```

### 4. The Escape Hatch: We Already Have It

**We don't need to create anything new.** The current `bootstrap/current.s` IS the escape hatch.
It's a tested, working compiler that can compile `kernel.lang` and `lang_reader.lang`.

The transition is just reorganization:

```bash
# What we have today
bootstrap/
├── current.s → 2411534.s      # ← THIS is our escape hatch
├── 2411534.s                  # full compiler, tested, working
├── 3bc135d.s
├── 16fa7a7.s
├── v0.1.0.s
└── ...

# This is already a provenance chain!
# Each .s file was built by the previous one.
```

### 5. Migration: Archive + Seed

```bash
# Step 1: Archive the existing provenance chain
mkdir -p archive/assembly-era
mv bootstrap/*.s archive/assembly-era/
# Keep the Go bootstrap too if you have it
mv bootstrap-go/ archive/go-era/  # if it exists

# Step 2: Create escape hatch from last known good
cp archive/assembly-era/current.s bootstrap/escape_hatch.s

# Step 3: Bootstrap into the new structure
make bootstrap-from-escape-hatch

# Step 4: Create first snapshot (this IS the seed)
make promote-both
# Creates: bootstrap/<commit>/{kernel,lang_reader}/
# PROVENANCE: built_by: escape_hatch.s

# Step 5: Update current symlink
# bootstrap/current → ./<commit>/
```

**After migration:**

```
bootstrap/
├── current → ./abc1234/              # symlink to latest
├── escape_hatch.s                    # the "keystone" - last assembly-era compiler
│
├── abc1234/                          # FIRST snapshot (seed)
│   ├── kernel/
│   │   ├── source.ast
│   │   └── PROVENANCE               # built_by: escape_hatch.s
│   └── lang_reader/
│       ├── source.ast
│       └── PROVENANCE               # built_by: escape_hatch.s
│
└── ... future snapshots ...

archive/
├── assembly-era/                     # preserved history
│   ├── current.s → 2411534.s
│   ├── 2411534.s
│   ├── 3bc135d.s
│   ├── v0.1.0.s
│   └── ...
└── go-era/                           # the original bootstrap
    └── ... go compiler if preserved ...
```

### 6. The Full Provenance Chain

After migration, you can trace the complete history:

```
bootstrap/current → bootstrap/abc1234
    PROVENANCE: built_by: escape_hatch.s
        ↓
    escape_hatch.s = archive/assembly-era/2411534.s
        built_by: archive/assembly-era/3bc135d.s
            built_by: archive/assembly-era/16fa7a7.s
                built_by: ...
                    built_by: archive/assembly-era/v0.1.0.s
                        built_by: archive/go-era/bootstrap.go
                            built_by: Go compiler
                                built_by: ... (it's turtles all the way down)
```

The assembly era is archived, not deleted. The escape hatch is the bridge between eras.

---

## Compiler Composition (`-c` Flag)

### The Upsert Semantics

```
compiler -c reader.lang → new_compiler

Where:
  compiler     = kernel + [r₁, r₂, r₃, ...]
  new_compiler = kernel + [r₁', r₂, r₃, ...]  // r₁ replaced if same name
```

**Key insight: `-c` is UPSERT, not APPEND.**

- If `reader.lang` defines a reader named "foo" and compiler already has "foo": **REPLACE**
- If compiler doesn't have "foo": **ADD**
- All other readers: **PRESERVED**

### Examples

```bash
# Start with kernel + lang
{kernel + lang} -c lisp.lang = {kernel + lang + lisp}      # ADD lisp

# Update lang (lisp preserved!)
{kernel + lang + lisp} -c lang_v2.lang = {kernel + lang_v2 + lisp}

# Update lisp (lang preserved!)
{kernel + lang_v2 + lisp} -c lisp_v2.lang = {kernel + lang_v2 + lisp_v2}

# Add sql (everything preserved!)
{kernel + lang_v2 + lisp_v2} -c sql.lang = {kernel + lang_v2 + lisp_v2 + sql}
```

### Why This Matters for Bootstrap

This is exactly how lang bootstrapping works:

```bash
# out/lang is {kernel + lang_reader_v1}
# You edit src/parser.lang (part of lang_reader)

out/lang -c lang_reader_v2 → out/lang_next    # = {kernel + lang_reader_v2}

# Verify: lang_next can rebuild itself
out/lang_next -c lang_reader_v2 → out/verify  # = {kernel + lang_reader_v2}

diff out/lang_next out/verify  # fixed point!
```

The fixed point check is: "can the new compiler rebuild its own reader identically?"

### Reader Registry

```lang
struct ReaderEntry {
    name *u8;
    name_len i64;
    handler fn(*u8) *u8;  // text → AST (or text → text for current model)
}

var readers Vec<ReaderEntry>;

// Upsert: replace if exists, add if new
func register_reader(name *u8, handler fn(*u8) *u8) void {
    var i i64 = 0;
    while i < readers.len {
        if streq(readers[i].name, name) {
            readers[i].handler = handler;  // REPLACE
            return;
        }
        i = i + 1;
    }
    readers.push(ReaderEntry{name, strlen(name), handler});  // ADD
}
```

### What `-c` Emits

When `-c` emits a new compiler:
1. Copy kernel code (unchanged)
2. Copy ALL existing readers (serialized)
3. Compile new reader
4. Upsert into reader table
5. Emit combined binary with updated dispatch table

---

## The Vision: Layered Compilers

```bash
# Start with kernel
./kernel -c lang_reader.ast -o lang

# Add lisp
./lang -c lisp_reader.lang -o lang_lisp

# Add sql
./lang_lisp -c sql_reader.lang -o polyglot

# The polyglot can compile any mix of lang, lisp, sql
./polyglot my_app.lang  # uses #lisp{} and #sql{} freely
```

Each compiler knows its lineage:
```
polyglot.readers = [lang_reader, lisp_reader, sql_reader]
polyglot.kernel = kernel_v1
```

### Introspection

```bash
./polyglot --list-readers
# Output:
# lang (default)
# lisp
# sql

./polyglot --kernel-version
# Output: kernel_v1 @ commit abc123
```

---

## Migration Path

### Phase 1: Extract Without Changing Bootstrap

1. Create `src/kernel_main.lang` and `src/reader_main.lang`
2. Add `make kernel` and `make lang-reader` targets
3. Add `make verify-split` to confirm split matches monolithic
4. Keep existing bootstrap unchanged

### Phase 2: Add AST Bootstrap

1. Generate initial `bootstrap/kernel/current.ast` and `bootstrap/lang_reader/current.ast`
2. Add `make bootstrap-from-ast` target
3. Add PROVENANCE tracking
4. Verify fixed points work through AST path

### Phase 3: Make AST Primary

1. Default bootstrap uses AST path
2. Assembly becomes emergency-only
3. Update `make promote` to save both .ast and .s

### Phase 4: Composition

1. Implement reader registry
2. Implement `-c` with accumulation
3. Enable layered compiler emission

---

## Summary

**What we have:** A monolithic compiler that already contains kernel + lang_reader.

**What we're doing:** Extracting them into separately-bootstrappable components.

**Why it matters:**
- Kernel changes are rare → assembly bootstrap is rare
- Reader changes are common → AST bootstrap is fast
- Composition becomes natural → compiler compiler vision realized

**The equation:**
```
out/lang = kernel + lang_reader

bootstrap/kernel/current.ast   ← built by {kernel + lang_reader}
bootstrap/lang_reader/current.ast ← built by {kernel + lang_reader}

Fixed point: {kernel + lang_reader} can rebuild both .ast files identically.
```

This is the compiler compiler.
