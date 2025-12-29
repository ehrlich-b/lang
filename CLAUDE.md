# lang

*"There are many like it but this one is mine."*

**Vision**: A self-hosted compiler compiler. For fun.

Lang + reader macro = native compiler for any syntax. No runtime, no VM, just x86.

## Anchor Documents

**Always re-read during reanchor:**
- `README.md` - Project overview and vision
- `CLAUDE.md` - This file (Claude Code guidance)
- `TODO.md` - Current tasks and roadmap
- `LANG.md` - Language reference (what works NOW)
- `designs/ast_as_language.md` - **The big vision**: AST as root language, syntax as plugin
- `designs/reader_v2_design.md` - Reader macros V2 design
- `designs/self_defining_syntax.md` - The `lang_reader.lang` vision

## Project Structure

```
lang/
├── src/            # Compiler (written in lang)
├── std/            # Standard library
├── test/           # Test programs
├── example/        # Example programs (lisp reader, etc.)
├── designs/        # Design documents
├── devlog/         # Development journal
└── out/            # Build artifacts
```

## Build Commands

```bash
make build          # Build compiler from source → out/lang_next
make verify         # Verify fixed point + run all tests
make promote        # Promote verified build (lang_next → lang)
make run FILE=...   # Compile and run (uses stable out/lang)
make stdlib-run FILE=...  # With stdlib (uses stable out/lang)
make bootstrap      # Bootstrap from assembly (emergency)
```

**After compiler changes:** Always `make verify`.

## Testing New Features

There are TWO compilers:
- `out/lang` - **Stable compiler** (used by `make run`, `make test-suite`)
- `out/lang_next` - **Development compiler** (built by `make build`)

When developing new language features (like enums, match, etc.), the stable compiler doesn't have them yet. Use these patterns:

```bash
# Run single test with development compiler (PREFERRED)
make dev-run FILE=test/suite/188_effect_exception.lang

# Run single test with dev compiler + stdlib
make dev-stdlib-run FILE=test/suite/189_closure_type.lang

# Run full test suite with development compiler
COMPILER=./out/lang_next ./test/run_lang1_suite.sh

# Filter test suite output for specific test
COMPILER=./out/lang_next ./test/run_lang1_suite.sh 2>&1 | grep "188"
```

**Key insight**: `make run` will FAIL on new syntax because it uses the stable compiler. Always use `make dev-run` or `make dev-stdlib-run` for testing new features until they're promoted.

## Current Focus

**AST as Language**: The big architectural vision. See `designs/ast_as_language.md`.

## Milestones

1. ✓ Self-hosting compiler (x86 fixed point)
2. ✓ Self-hosted compiler compiler (reader infrastructure in lang)
3. ✓ `#parser{}` reader (parser generator as reader macro!)
4. ✓ `#lisp{}` reader with defun (cross-file function interop!)
5. → **1.0: AST as Language** ← current
   - `std/ast.lang` - AST constructors + `ast_emit()`
   - S-expression parser in kernel
   - `lang_reader.lang` - lang syntax as a reader
   - Syntax fixed point (lang bootstrapped on AST kernel)
6. → WASM + LLVM IR backends (same AST, multiple targets)
7. → Language forge (any syntax → any target, trivially)

## Code Style

- Hack freely, this is for fun
- Comments explain "why", not "what"
- Memory can leak in the compiler (short-lived)
- Incremental modernization, not big-bang refactoring
- **Just include stdlib when needed** - Don't try to avoid `std/core.lang` dependencies with clever workarounds. If a feature needs `alloc`, include stdlib. Tests that need stdlib should include it.

## Language Gotchas (READ THIS)

### Forward Declarations: NOT NEEDED, DON'T USE SIGNATURES

**THE BUG**: Writing `func foo() void;` (signature only, no body) is INVALID SYNTAX.

**THE FIX**: Just define functions in any order. Lang's parser collects ALL function declarations first, so functions CAN call functions defined later in the file. No forward declarations needed!

```lang
// THIS WORKS - mutual recursion without forward declarations
func foo() void {
    bar();  // bar is defined BELOW, but this works!
}

func bar() void {
    foo();
}

// THIS IS INVALID - don't do this!
func baz() void;  // ERROR: expected '{'
```

**Why we keep hitting this**: Coming from C, the instinct is to forward-declare mutually recursive functions. In lang, the two-pass parser handles this automatically.

### Identifiers Cannot Contain `-` (Hyphen)

**THE BUG**: Using `-` in identifiers (like `my-var` or `foo-bar`) will fail. The tokenizer sees `-` as the minus operator.

**THE FIX**: Use underscores instead: `my_var`, `foo_bar`.

**Why this matters**: When working with S-expression AST (sexpr_reader), operator symbols like `-`, `+`, `==` must be handled specially. They're parsed as operator tokens, not identifiers. The grammar must include `operator` to match them:

```
#parser{
    sexpr = number | symbol | string | operator | list  // 'operator' required for +, -, etc.
    list = '(' sexpr* ')'
}
```

## Error Handling Policy

**Broken windows rule**: If you see any horrible things like core dumps, segfaults, or crashes - don't just say "but it basically works" and try to move on. That error becomes your **top priority** until you can prove it was a fluke or fix it properly. Ignoring errors leads to compounding problems.

## Testing Policy

**Save every test**: When you write a test to verify something works, save it to the `test/` folder - never leave tests to die in `/tmp`. Every well-formed test is valuable and should be kept forever. Use descriptive names and add to the test suite when appropriate.

### Tests Check the Compiler, Not Vice Versa

**THE RULE**: When a test fails, assume THE COMPILER IS WRONG until proven otherwise.

Tests represent what the language SHOULD do. The compiler is the thing being tested. If you write a reasonable test and the compiler rejects it or produces wrong output, that's a **compiler bug to fix**, not a test to change.

**WRONG approach** (what I must NOT do):
```
1. Write test with zero-arg effect: effect Read() i64
2. Compiler crashes or misbehaves
3. "Oh, let me change the test to use effects with arguments instead"
4. Test passes, bug remains hidden
```

**RIGHT approach**:
```
1. Write test with zero-arg effect: effect Read() i64
2. Compiler crashes or misbehaves
3. "This is a compiler bug. Let me fix the compiler."
4. Fix codegen to handle zero-arg effects correctly
5. Original test now passes, bug is fixed
```

**Only change a test when**:
- The test is semantically wrong (misunderstands what the language should do)
- The test has a typo or logic error in its own verification code
- The expected behavior has intentionally changed (and documented)

**Never change a test because**:
- It does something "weird" or unusual (weird is GOOD - it finds edge cases!)
- The compiler says it's wrong (that's what we're checking!)
- It would be easier to work around than fix

**Weird tests are the best tests.** They expose edges. A test that does something no reasonable user would do is still valuable - it might reveal an assumption the compiler makes that isn't actually guaranteed.

## Key Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Bootstrap | Go (deleted) | Fast to write, goal was to delete it |
| Output | Assembly → native | Direct, educational |
| Reader output | AST S-expressions | Universal format, typed constructors hide details |
| AST format | S-expressions | Trivial to parse, proven, debuggable |
| Future backend | WASM, LLVM IR | Portability, optimization |
