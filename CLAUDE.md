# lang

*"There are many like it but this one is mine."*

**Vision**: A self-hosted compiler compiler. For fun.

Lang + reader macro = native compiler for any syntax. Outputs LLVM IR → native binary.

## Anchor Documents

**Always re-read during reanchor:**
- `README.md` - Project overview and vision
- `CLAUDE.md` - This file (Claude Code guidance)
- `TODO.md` - Current tasks and roadmap
- `LANG.md` - Language reference (what works NOW)
- `designs/ast_as_language.md` - **The big vision**: AST as root language, syntax as plugin

## Project Structure

```
lang/
├── src/            # Compiler (written in lang)
│   ├── codegen.lang      # x86-64 backend (FROZEN - emergency bootstrap only)
│   └── codegen_llvm.lang # LLVM IR backend (PRIMARY - all new features)
├── std/            # Standard library
├── test/           # Test programs (186 suite files + reader/composition checks)
├── bootstrap/      # LLVM IR bootstrap (primary) + x86 assembly (frozen)
├── example/        # Example programs
├── designs/        # Design documents
├── devlog/         # Development journal
└── out/            # Build artifacts
```

## Build Commands

### Default
```bash
make build          # Build compiler → out/lang_next
make bootstrap      # THE ONE COMMAND: verify + promote (see below)
make run FILE=...   # Compile and run
make init           # Recover from the preserved platform LLVM IR
```

### LLVM Backend
```bash
LANGBE=llvm make dev-run FILE=test.lang    # Compile via LLVM
LANGBE=llvm ./out/lang_next src.lang -o out.ll  # Generate LLVM IR
clang -O2 out.ll -o binary                 # Use clang to compile
```

**After compiler changes:** Always `make bootstrap`.

## Bootstrap

**Primary**: `bootstrap/current/compiler_{linux,macos}.ll` - LLVM IR roots

**Frozen**: x86-64 assembly artifacts in history/archives (emergency fallback only)

The x86 backend is frozen - no new features (floats, calling conventions) will be added. LLVM is the sole target for Language Forge development.

## Testing

### Test suites
```bash
# LLVM backend (all features, cross-platform)
./test/run_llvm_suite.sh

# wasm target (165 tests under node; effects tests skip - no stack switching)
./test/run_wasm_suite.sh

# x86 backend (Linux only, frozen - no new tests)
./test/run_lang1_suite.sh
```

### Development Workflow
```bash
# Run single test with dev compiler + stdlib
make dev-stdlib-run FILE=test/suite/195_effect_in_loop.lang

# Cache full suite results (SLOW - only run once)
COMPILER=./out/lang_next ./test/run_llvm_suite.sh > /tmp/suite.txt 2>&1
grep "FAIL" /tmp/suite.txt  # Query cached results
```

**Key insight**: Use `make dev-run` for testing new features until promoted.

## Milestones

1. ✓ Self-hosting compiler (x86 fixed point)
2. ✓ Reader macro infrastructure (`#parser{}`, `#lisp{}`)
3. ✓ Language polish (break/continue, bitwise ops, char literals)
4. ✓ AST 2.0: closures, algebraic effects, sum types
5. ✓ Kernel/reader split (lang as a reader, bootstrap verified)
6. ✓ **Cross-platform + LLVM backend** (198/198 checks, Linux + macOS)
7. ✓ Kernel/reader composition (bare kernel + -r reader = compiler)
8. → **Reader authorship: ship many readers** ← current
9. → WASM backend (via LLVM)
10. → Capture more languages

## Code Style

- Hack freely, this is for fun
- Comments explain "why", not "what"
- Memory can leak in the compiler (short-lived)
- **Just include stdlib when needed** - Tests that need `alloc` should include `std/core.lang`

## Git Commit Style

- **Single sentence commits only** - No multi-line messages, no bullet points
- **No co-author tags** - Never add "Co-Authored-By" or similar
- **No emoji prefixes** - No 🤖 or other decorations
- Example: `git commit -m "Fix malloc symbol conflict in libc bootstrap"`

## Language Gotchas (READ THIS)

### Forward Declarations: NOT NEEDED

Lang's parser collects ALL function declarations first. Functions can call functions defined later:

```lang
func foo() void { bar(); }  // Works! bar is defined below
func bar() void { foo(); }
```

**INVALID**: `func baz() void;` (signature only) - this is a syntax error.

### Identifiers Cannot Contain `-`

Use underscores: `my_var`, not `my-var`. The tokenizer sees `-` as minus.

## Error Handling Policy

**Broken windows rule**: Segfaults and crashes are top priority. Fix them before moving on.

## Testing Policy

**Tests check the compiler, not vice versa.** When a test fails:
1. Assume the compiler is wrong
2. Fix the compiler
3. Original test passes

**Never change a test** just because the compiler rejects it. Weird edge cases are valuable.

## Bootstrap Safety Rules (CRITICAL)

The bootstrap chain is the compiler's lifeline. Corruption = days of recovery.

### ONE Command: `make bootstrap`

```bash
make bootstrap    # Does EVERYTHING: verify, archive, stage, and promote
```

**That's it.** One command. Can't fuck it up.

### What `make bootstrap` Does (7 stages)

1. **Root of trust**: compile the platform's preserved LLVM IR with clang
2. **Generation 1**: trusted compiler builds kernel1 and reader_ast1
3. **Generations 2 + 3**: verify kernel2.ll === kernel3.ll
4. **Reader fixed point**: verify reader_ast1 === reader_ast2
5. **Cross-platform roots**: generate and clang-check Linux + macOS LLVM IR
6. **Validation**: run the LLVM suite on the final platform binary
7. **Archive + promote**: release/archive the old root, update
   `bootstrap/current/`, then install the tested binary as `out/lang`

Validation and archival finish before promotion begins. Root files are staged
as complete files, the identity marker moves last, and `out/lang` is replaced
only after the root promotion succeeds.

### NEVER Do These Things

1. **NEVER bypass tests** - If tests hang or are slow, WAIT or diagnose
2. **NEVER manually copy generated IR into `bootstrap/current/`**
3. **NEVER edit preserved bootstrap IR directly**
4. **NEVER run partial verification** - Always full `make bootstrap`

### Incremental Development (CRITICAL)

**Always think about bootstrap.** Every change must be bootstrappable before moving on.

- Make ONE small change
- Run `make bootstrap`
- Only proceed if it passes
- Commit after each successful bootstrap

Don't build features that depend on other features you haven't bootstrapped yet.
For example, you can't build a standalone kernel without `-r` support if that
kernel needs readers - bootstrap it with readers first, then split later.

### Feature Development Workflow (CRITICAL)

When adding new features that change the AST format, readers, or any compiler capability:

1. **Add the feature** (e.g., v2 AST support for READING)
2. **IMMEDIATELY run `make bootstrap`** - Bake it into bootstrap
3. **ONLY THEN** can you write code that USES the new feature

**WHY**: The bootstrap compiler must understand any new format before you can use it.
If you write v2 AST before the bootstrap knows v2, you create a bootstrap crisis.

**Example - Adding AST v2**:
```
WRONG:
1. Add v2 reading support
2. Write test that outputs v2 format  <- BROKEN! Bootstrap can't read v2 yet
3. Try to compile <- crash/fail

RIGHT:
1. Add v2 reading support
2. make bootstrap  <- Now bootstrap knows v2
3. Write test that outputs v2 format  <- Works!
```

### Recovery: LLVM Bootstrap Path

If `out/lang` is missing or corrupted:
```bash
make init
make build
```

`make init` chooses `bootstrap/current/compiler_linux.ll` or
`compiler_macos.ll` and rebuilds the root with clang.

## Key Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Bootstrap | Go (deleted) | Fast to write, goal was to delete it |
| x86 Backend | **FROZEN** | Served its purpose (self-hosting proof), too much work for new features |
| LLVM Backend | LLVM IR text | Portable, optimizable, cross-platform - sole target going forward |
| Reader output | AST S-expressions | Universal format, debuggable |
| Effects | Algebraic (resumable) | Powerful, composable |
