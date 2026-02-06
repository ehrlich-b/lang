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

## Captured Languages

| Language | Status | Notes |
|----------|--------|-------|
| Zig | In progress | AIR -> lang AST emitter |
| Rust | Future | MIR -> lang AST |
| Go | Future | SSA -> lang AST |

## Adding a New Language

1. Create `patches/<lang>/manifest.yaml`
2. Create patches for integration points
3. Add new codegen files to `patches/<lang>/src/`
4. Add `patch-<lang>` target to Makefile
5. Document in this README
