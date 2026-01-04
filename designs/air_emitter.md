# AIR Emitter Design: Capturing Zig Through Its Own Compiler

## Overview

The AIR emitter is a new Zig codegen backend that emits lang AST (S-expressions) instead of machine code. This allows us to compile Zig programs through lang's LLVM backend, and ultimately bootstrap the Zig compiler itself on lang.

## Repository Strategy

### Decision: Patches (No Fork)

We use a **patches-based approach** - no fork repository, no submodule, no drama.

**Why patches:**

| Option | Vibes | Practical | Chosen |
|--------|-------|-----------|--------|
| Fork on GitHub | Bad - undermines their Codeberg move | Works | No |
| Fork on Codeberg | Okay | Works | No |
| Submodule | Neutral | 500MB pollution | No |
| **Patches** | **Best** | **Clean, transferable** | **Yes** |

The patches approach:
- Zero confusion with upstream
- Full responsibility is ours
- Transferable pattern for capturing other languages
- Explicit upstream reference in manifest
- No fork relationship to maintain

### Directory Structure

```
patches/
├── README.md                    # How this system works
├── zig/
│   ├── manifest.yaml            # Repo, commit, build instructions
│   ├── 001-add-lang-ast-objectformat.patch
│   ├── 002-add-backend-dispatch.patch
│   ├── 003-lang-ast-codegen.patch
│   └── src/
│       └── codegen/
│           └── lang_ast.zig     # New file (not a patch, just add)
├── rust/                        # Future
│   ├── manifest.yaml
│   └── ...
└── go/                          # Future
    ├── manifest.yaml
    └── ...
```

### Manifest Format

`patches/zig/manifest.yaml`:

```yaml
# Zig compiler with lang-ast backend
name: zig
description: Zig compiler patched to emit lang AST

upstream:
  repo: https://codeberg.org/zig/zig.git
  commit: a1b2c3d4e5f6...    # Pin to specific commit
  version: 0.14.0            # Human-readable version

patches:
  - 001-add-lang-ast-objectformat.patch
  - 002-add-backend-dispatch.patch
  - 003-lang-ast-codegen.patch

# Files to copy (new files, not patches)
copy:
  - src: src/codegen/lang_ast.zig
    dst: src/codegen/lang_ast.zig

build:
  command: zig build -Doptimize=Debug
  output: zig-out/bin/zig

# What we extract after build
artifacts:
  - zig-out/bin/zig -> lang/tools/zig-lang-ast
```

### Makefile Targets

```makefile
# Build patched Zig compiler
patch-zig:
	@./scripts/apply-patches.sh zig

# Rebuild after patch changes
rebuild-zig:
	@./scripts/rebuild-patches.sh zig

# Update to new upstream commit (generates new patches)
update-zig:
	@./scripts/update-upstream.sh zig

# Clean up
clean-patches:
	rm -rf /tmp/lang-patches-*
```

### Workflow Scripts

`scripts/apply-patches.sh`:

```bash
#!/bin/bash
set -euo pipefail

TARGET="$1"
MANIFEST="patches/$TARGET/manifest.yaml"

# Parse manifest (simplified - real impl uses yq or similar)
REPO=$(grep 'repo:' "$MANIFEST" | awk '{print $2}')
COMMIT=$(grep 'commit:' "$MANIFEST" | awk '{print $2}')

WORKDIR="/tmp/lang-patches-$TARGET-$$"
echo "==> Cloning $TARGET to $WORKDIR"
git clone --depth=1 "$REPO" "$WORKDIR"
cd "$WORKDIR"
git fetch --depth=1 origin "$COMMIT"
git checkout "$COMMIT"

echo "==> Applying patches"
for patch in ../patches/$TARGET/*.patch; do
    [ -f "$patch" ] || continue
    echo "    Applying $(basename "$patch")"
    git apply "$patch"
done

echo "==> Copying new files"
# Copy files listed in manifest copy: section
cp -r "../patches/$TARGET/src/" "src/" 2>/dev/null || true

echo "==> Building"
zig build -Doptimize=Debug

echo "==> Done! Binary at $WORKDIR/zig-out/bin/zig"
```

### Updating to New Upstream

When Zig releases a new version:

```bash
# 1. Clone fresh upstream
git clone https://codeberg.org/zig/zig.git /tmp/zig-new
cd /tmp/zig-new
git checkout v0.15.0  # new version

# 2. Apply our changes manually (may need conflict resolution)
# ... edit files ...

# 3. Generate new patches
git diff HEAD~3 > patches/zig/001-new.patch  # etc

# 4. Update manifest.yaml with new commit hash

# 5. Test
make patch-zig
```

This is manual but infrequent (Zig releases ~2x/year).

### patches/README.md Content

```markdown
# Language Capture Patches

This directory contains patches for capturing languages through their own compilers.

## Philosophy

We don't fork. We don't submodule. We patch.

Each language gets a directory with:
- `manifest.yaml` - Upstream repo, commit, build instructions
- `*.patch` - Modifications to existing files
- `src/` - New files to add (not patches)

## Usage

```bash
# Build a patched compiler
make patch-zig

# Use the result
/tmp/lang-patches-zig-XXXX/zig-out/bin/zig build-obj foo.zig -ofmt=lang-ast
```

## Why Patches?

1. **Respect upstream** - No fork confusion, no GitHub vs Codeberg drama
2. **Transparency** - Patches show exactly what we changed
3. **Portability** - Works with any git host
4. **Responsibility** - We maintain the patches, not a parallel universe

## Adding a New Language

1. Create `patches/<lang>/manifest.yaml`
2. Create patches for integration points
3. Add new codegen files to `patches/<lang>/src/`
4. Add `patch-<lang>` target to Makefile
5. Document in this README
```

---

## Integration Points

### 1. ObjectFormat Enum

**File:** `lib/std/Target.zig` (line ~955)

```zig
pub const ObjectFormat = enum {
    c,       // existing
    coff,    // existing
    elf,     // existing
    // ...
    lang_ast,  // NEW: lang AST S-expressions
    // ...
};
```

### 2. CompilerBackend Enum

**File:** `lib/std/builtin.zig`

```zig
pub const CompilerBackend = enum {
    // ... existing ...
    stage2_lang_ast,  // NEW
};
```

### 3. Backend Selection

**File:** `src/target.zig` (zigBackend function, line ~842)

```zig
pub fn zigBackend(target: *const std.Target, use_llvm: bool) std.builtin.CompilerBackend {
    if (use_llvm) return .stage2_llvm;
    if (target.ofmt == .c) return .stage2_c;
    if (target.ofmt == .lang_ast) return .stage2_lang_ast;  // NEW
    // ...
}
```

### 4. Codegen Dispatch

**File:** `src/codegen.zig`

```zig
fn importBackend(comptime backend: std.builtin.CompilerBackend) type {
    return switch (backend) {
        // ... existing ...
        .stage2_c => @import("codegen/c.zig"),
        .stage2_lang_ast => @import("codegen/lang_ast.zig"),  // NEW
        // ...
    };
}

fn devFeatureForBackend(backend: std.builtin.CompilerBackend) dev.Feature {
    return switch (backend) {
        // ... existing ...
        .stage2_lang_ast => .lang_ast_backend,  // NEW
        // ...
    };
}
```

Also update `AnyMir` union and `generateFunction` switch.

### 5. Dev Features

**File:** `src/dev.zig`

```zig
pub const Feature = enum {
    // ... existing ...
    lang_ast_backend,  // NEW
};
```

---

## CLI Interface

### End-to-End Workflow

```bash
# 1. Build patched Zig (one-time, or after patch updates)
make patch-zig
# Output: /tmp/lang-patches-zig-XXXX/zig-out/bin/zig
ZIG_PATCHED="/tmp/lang-patches-zig-XXXX/zig-out/bin/zig"

# 2. Emit the Zig COMPILER ITSELF as lang AST
#    (This is the capture - we're yoinking Zig's entire frontend!)
$ZIG_PATCHED build-obj /path/to/zig/src/main.zig -ofmt=lang-ast -femit-bin=zig_compiler.ast

# 3. Compose Zig compiler into lang kernel as a reader
./out/lang -r zig zig_compiler.ast -o lang_zig

# 4. Now lang_zig IS a Zig compiler! Use it directly:
./lang_zig hello_world.zig -o hello.ll
clang hello.ll -o hello
./hello
```

**The key insight:** We don't translate individual `.zig` files through lang AST. We capture the *entire Zig compiler* as a reader, then `.zig` files go through natively.

### Flag Details

The `-ofmt=lang-ast` flag triggers `target.ofmt == .lang_ast`, which routes to our backend.

```bash
# Explicit format
zig build-obj source.zig -ofmt=lang-ast -femit-bin=output.ast

# Can also use target triple (alternative)
zig build-obj source.zig -target lang_ast-unknown-unknown -femit-bin=output.ast
```

### Output

Single file containing all functions as lang AST S-expressions:

```lisp
;; Generated by zig (lang-ast backend)
;; Source: source.zig

(func factorial ((n i64)) i64
  (if (<= n 1)
    (return 1)
    (return (* n (call factorial (- n 1))))))

(func main () i64
  (var result i64 (call factorial 5))
  (return result))
```

---

## Backend Implementation

### File Structure

```
src/codegen/lang_ast.zig    # Main backend (~2000-3000 lines estimated)
```

Unlike the C backend (which has `c/Type.zig`), we don't need a separate type file because lang AST types map directly to strings.

### Core Data Structures

```zig
const std = @import("std");
const Air = @import("../Air.zig");
const Zcu = @import("../Zcu.zig");
const InternPool = @import("../InternPool.zig");

pub const Mir = struct {
    /// Generated S-expression code for this function
    code: []u8,

    pub fn deinit(mir: *Mir, gpa: std.mem.Allocator) void {
        gpa.free(mir.code);
    }
};

const Function = struct {
    air: *const Air,
    zcu: *const Zcu,
    writer: std.ArrayList(u8).Writer,
    indent: u32,

    /// Maps AIR instruction index to generated variable name
    value_map: std.AutoHashMap(Air.Inst.Index, []const u8),
};

pub fn generate(
    lf: *link.File,
    pt: Zcu.PerThread,
    src_loc: Zcu.LazySrcLoc,
    func_index: InternPool.Index,
    air: *const Air,
    liveness: *const ?Air.Liveness,
) !Mir {
    // ... implementation
}
```

### Instruction Mapping

**Priority 1: Core Operations (MVP)**

| AIR Instruction | Lang AST | Implementation |
|-----------------|----------|----------------|
| `arg` | `(param name type)` | `airArg` |
| `add`, `sub`, `mul` | `(+ a b)`, etc. | `airBinOp` |
| `div_trunc` | `(/ a b)` | `airBinOp` |
| `rem` | `(% a b)` | `airBinOp` |
| `bit_and`, `bit_or`, `xor` | `(& a b)`, etc. | `airBinOp` |
| `shl`, `shr` | `(<< a b)`, `(>> a b)` | `airBinOp` |
| `cmp_eq`, `cmp_neq`, etc. | `(== a b)`, etc. | `airCmpOp` |
| `not` | `(! a)` | `airUnaryOp` |
| `alloc` | `(var name type)` | `airAlloc` |
| `load` | `(deref ptr)` | `airLoad` |
| `store` | `(store ptr val)` | `airStore` |
| `ret` | `(return val)` | `airRet` |
| `call` | `(call func args...)` | `airCall` |
| `block` | implicit in structure | `airBlock` |
| `cond_br` | `(if cond then else)` | `airCondBr` |
| `br` | implicit (block exit) | `airBr` |

**Priority 2: Type Conversions**

| AIR Instruction | Lang AST | Notes |
|-----------------|----------|-------|
| `intcast` | `(cast type val)` | sign/zero extend or truncate |
| `bitcast` | `(bitcast type val)` | reinterpret bits |
| `trunc` | `(cast type val)` | truncate to smaller int |
| `float_from_int` | `(cast f64 val)` | sitofp |
| `int_from_float` | `(cast i64 val)` | fptosi |

**Priority 3: Memory and Structs**

| AIR Instruction | Lang AST | Notes |
|-----------------|----------|-------|
| `struct_field_ptr` | `(field_ptr expr n)` | pointer to field n |
| `struct_field_val` | `(field expr n)` | value of field n |
| `ptr_add` | `(+ ptr n)` | pointer arithmetic |
| `memset` | `(call memset ptr val len)` | extern call |
| `memcpy` | `(call memcpy dst src len)` | extern call |

**Priority 4: Control Flow**

| AIR Instruction | Lang AST | Notes |
|-----------------|----------|-------|
| `loop` | `(while true body)` | infinite loop with breaks |
| `switch_br` | `(match expr cases...)` | switch statement |
| `unreach` | `(call os_exit 1)` | unreachable code |

**Skip (Debug):**
- `dbg_stmt`, `dbg_var_val`, `dbg_var_ptr`, `dbg_inline_block`, `dbg_arg_inline`, `dbg_empty_stmt`

### Example Transformation

**Zig source:**
```zig
fn add(a: i64, b: i64) i64 {
    return a + b;
}
```

**AIR (simplified):**
```
# Begin Function AIR: test.add
  %0 = arg(i64, 0)
  %1 = arg(i64, 1)
  %2 = add(%0, %1)
  %3 = ret(%2)
# End Function AIR
```

**Lang AST output:**
```lisp
(func add ((a i64) (b i64)) i64
  (return (+ a b)))
```

### SSA to Named Variables

AIR uses SSA (Static Single Assignment) form with numbered registers (`%0`, `%1`, etc.). We need to convert to named variables for readable lang AST.

**Strategy:**
1. Function parameters get names from debug info (or `arg0`, `arg1`)
2. Allocations become named variables
3. Intermediate values become temporaries (`t0`, `t1`, etc.) or get inlined

```zig
fn resolveOperand(f: *Function, operand: Air.Inst.Ref) ![]const u8 {
    if (Air.refToIndex(operand)) |inst_index| {
        // Look up in value_map
        if (f.value_map.get(inst_index)) |name| {
            return name;
        }
        // Generate temporary
        const name = try std.fmt.allocPrint(f.gpa, "t{d}", .{inst_index});
        return name;
    } else {
        // Constant - emit inline
        return try emitConstant(f, operand);
    }
}
```

---

## Type Mapping

### Primitive Types

| Zig Type | Lang Type |
|----------|-----------|
| `i8`, `i16`, `i32`, `i64` | `i8`, `i16`, `i32`, `i64` |
| `u8`, `u16`, `u32`, `u64` | `u8`, `u16`, `u32`, `u64` |
| `i128`, `u128` | `i128`, `u128` |
| `isize`, `usize` | `i64`, `u64` (platform-dependent) |
| `f32`, `f64` | `f32`, `f64` |
| `bool` | `bool` |
| `void` | `void` |
| `noreturn` | `void` |

### Arbitrary-Width Integers

Zig uses types like `u5`, `u6` for shift amounts. Strategy: round up to next power of 2.

```zig
fn mapIntType(bits: u16, signed: bool) []const u8 {
    const rounded = std.math.ceilPowerOfTwo(u16, bits) catch bits;
    return switch (rounded) {
        1...8 => if (signed) "i8" else "u8",
        9...16 => if (signed) "i16" else "u16",
        17...32 => if (signed) "i32" else "u32",
        33...64 => if (signed) "i64" else "u64",
        65...128 => if (signed) "i128" else "u128",
        else => "i64", // fallback
    };
}
```

### Composite Types

**Slices:** Emit as anonymous struct with ptr and len fields.

```lisp
;; []const u8 becomes:
(struct __slice_u8
  ((field_decl ptr (type_ptr (type_base u8)))
   (field_decl len (type_base i64))))
```

**Optionals:** Emit as sum type.

```lisp
;; ?i64 becomes:
(enum __optional_i64
  ((variant_decl None)
   (variant_decl Some (type_base i64))))
```

**Error unions:** Emit as sum type with error code.

```lisp
;; error{OutOfMemory}!i64 becomes:
(enum __result_i64
  ((variant_decl Ok (type_base i64))
   (variant_decl Err (type_base i64))))  ;; error code
```

---

## Implementation Plan

### Phase 0: Patches Infrastructure

1. Create `patches/` directory structure
2. Create `patches/README.md` explaining the system
3. Create `patches/zig/manifest.yaml` pinned to Zig 0.14.0
4. Create `scripts/apply-patches.sh`
5. Add `patch-zig` target to Makefile
6. Test: `make patch-zig` clones and builds vanilla Zig

### Phase 1: Skeleton

1. Create `patches/zig/src/codegen/lang_ast.zig` with minimal structure
2. Create patch: Add `lang_ast` to `ObjectFormat` enum
3. Create patch: Add `stage2_lang_ast` to `CompilerBackend` enum
4. Create patch: Wire into `codegen.zig` dispatch
5. Test: `make patch-zig && $ZIG build-obj empty.zig -ofmt=lang-ast` produces empty output

### Phase 2: Hello World (Days 2-3)

1. Implement `airArg` - function parameters
2. Implement `airRet` - return statement
3. Implement `airBinOp` - arithmetic operations
4. Implement `airAlloc`, `airLoad`, `airStore` - basic memory
5. Test: Simple arithmetic function compiles

### Phase 3: Control Flow (Days 4-5)

1. Implement `airCondBr` - if/else
2. Implement `airBlock`, `airBr` - blocks and jumps
3. Implement `airCmpOp` - comparisons
4. Test: Factorial function compiles

### Phase 4: Types (Days 6-7)

1. Implement `airIntCast`, `airBitcast`, `airTrunc` - type conversions
2. Implement `airStructFieldPtr`, `airStructFieldVal` - struct access
3. Implement slice handling (as structs)
4. Test: String operations compile

### Phase 5: Full Coverage (Week 2+)

1. Handle remaining instructions as encountered
2. Run against Zig compiler self-compile
3. Fix edge cases
4. Document unsupported features

---

## Testing Strategy

### Unit Tests (During Development)

Test individual instruction handlers with minimal Zig programs:

```bash
# Build patched Zig once
make patch-zig
ZIG="/tmp/lang-patches-zig-*/zig-out/bin/zig"

# Create minimal Zig that uses specific instruction
echo 'export fn add(a: i64, b: i64) i64 { return a + b; }' > /tmp/test.zig

# Compile to lang AST
$ZIG build-obj /tmp/test.zig -ofmt=lang-ast -femit-bin=/tmp/test.ast

# Verify output structure
cat /tmp/test.ast
# Expected: (func add ((a i64) (b i64)) i64 (return (+ a b)))

# Compile through lang kernel (not composed, just raw AST)
./out/lang /tmp/test.ast -o /tmp/test.ll
clang /tmp/test.ll -o /tmp/test
```

### Integration Tests (Reader Composition)

Test the full capture flow with a simple Zig program:

```bash
ZIG="/tmp/lang-patches-zig-*/zig-out/bin/zig"

# Emit a mini "compiler" (really just a hello world for now)
echo 'pub fn main() void { @import("std").debug.print("Hello\n", .{}); }' > /tmp/hello.zig
$ZIG build-obj /tmp/hello.zig -ofmt=lang-ast -femit-bin=/tmp/hello.ast

# Compose as reader (once we have enough instructions working)
./out/lang -r zig /tmp/hello.ast -o /tmp/lang_zig

# Test the composed compiler
./lang_zig /tmp/other.zig -o /tmp/other.ll
```

### Full Capture Validation

The ultimate test - capture Zig's own compiler:

```bash
ZIG="/tmp/lang-patches-zig-*/zig-out/bin/zig"

# 1. Emit Zig compiler as lang AST
$ZIG build-obj /path/to/zig/src/main.zig -ofmt=lang-ast -femit-bin=/tmp/zig_compiler.ast

# 2. Compose into lang
./out/lang -r zig /tmp/zig_compiler.ast -o /tmp/lang_zig

# 3. Use lang_zig to compile a test program
./lang_zig test.zig -o test_via_lang.ll
clang test_via_lang.ll -o test_via_lang

# 4. Compare with native Zig
zig build-exe test.zig -o test_native
diff <(./test_native) <(./test_via_lang)

# 5. Fixed-point: use lang_zig to emit itself
./lang_zig build-obj /path/to/zig/src/main.zig -ofmt=lang-ast -femit-bin=/tmp/zig_compiler2.ast
diff /tmp/zig_compiler.ast /tmp/zig_compiler2.ast  # Should match!
```

---

## Open Questions

### 1. Debug Info

Should we emit source locations as comments?

```lisp
;; source.zig:10
(var x i64 42)
```

**Decision:** Skip initially. Add later if useful for debugging.

### 2. Extern Declarations

How to handle extern functions referenced by Zig code?

**Decision:** Emit `(extern func name type)` declarations. Lang already supports this.

### 3. Global Variables

How to handle Zig globals?

**Decision:** Emit as `(global name type init)`. May need to add this node to lang.

### 4. Calling Conventions

Should we preserve Zig's calling convention annotations?

**Decision:** Ignore initially. All calls use default C convention. Add annotation support if ABI issues arise.

---

## Success Criteria

### MVP

- [ ] Patches infrastructure working (`make patch-zig` builds patched Zig)
- [ ] Simple functions emit valid lang AST
- [ ] AST compiles through lang kernel (not composed, just `./out/lang foo.ast`)
- [ ] Arithmetic, comparisons, control flow work

### Composition

- [ ] `./out/lang -r zig compiler.ast -o lang_zig` produces working binary
- [ ] `./lang_zig hello.zig` compiles hello world
- [ ] Reader composition doesn't conflict with kernel symbols

### Full Capture

- [ ] Zig compiler self-compiles to lang AST
- [ ] `./lang_zig` can compile real Zig programs (not just toy examples)
- [ ] Fixed-point: `lang_zig` emits itself, AST matches original
- [ ] Zig stdlib functions work through the capture

---

## References

- `src/codegen/c.zig` - C backend implementation (8700 lines, our reference)
- `src/Air.zig` - AIR instruction definitions
- `designs/zig_ast_compatibility.md` - AIR analysis and instruction mapping
- `zig/AIR_MAPPING.md` - Detailed per-instruction notes
