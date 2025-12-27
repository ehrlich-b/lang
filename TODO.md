# language - TODO

## Vision

**A self-hosted compiler compiler.**

Lang + reader macro = native compiler for any syntax. No runtime, no VM, just x86.

---

## Milestones

1. ✓ Self-hosting compiler (x86 fixed point)
2. ✓ Self-hosted compiler compiler (reader infrastructure in lang)
3. ✓ `#parser{}` reader (parser generator as reader macro!)
4. ✓ `#lisp{}` reader with defun (cross-file function interop!)
5. → Language polish (bugs, missing features)
6. → `lang_reader.lang` (lang syntax defined in lang)
7. → Language forge (file extension dispatch, trivial compiler creation)

---

## Current Focus: Language Polish

We keep tripping over missing features and bugs. Fix these before pushing forward.

### Bugs (Breaking)

| Bug | Severity | Status |
|-----|----------|--------|
| ~~>6 parameters generates broken assembly~~ | High | FIXED |
| ~~`*(struct.ptr_field)` reads 8 bytes~~ | High | FIXED |
| ~~No argument count checking~~ | Medium | FIXED |
| ~~Duplicate includes fail~~ | Medium | FIXED |

### Missing Features (Annoying)

| Feature | Pain Level | Status |
|---------|-----------|--------|
| ~~Character literals `'A'`~~ | High - use 65 everywhere | FIXED |
| ~~Bitwise operators `& \| ^ << >>`~~ | High - can't do bit manipulation | FIXED |
| ~~Compound assignment `+= -= *= /= %=`~~ | Medium - verbose | FIXED |
| ~~`break` / `continue` / labeled break~~ | Medium - awkward loops | FIXED |
| `for` loop sugar | Low - while works | TODO |

### Works Fine (I Was Wrong!)

These features already work - don't waste time on them:
- ✓ Forward function references (call before definition)
- ✓ Mutual recursion (is_even/is_odd)
- ✓ `else if` chains
- ✓ Nested struct field access

---

## Code Quality (from REVIEW.md)

| Issue | Priority | Status |
|-------|----------|--------|
| Magic PNODE numbers in lisp.lang | Low | TODO |
| Fixed 4KB stack frames | Low | TODO |
| Reader cache not invalidated | Low | TODO |

---

## Next Up: File Extension Dispatch

Two modes:

```bash
# Build-time compilation
# .lisp gets wrapped in #lisp{ contents }, finds reader in provided .lang files
lang reader_lisp.lang program.lisp -o program

# Standalone compiler generation
# -c lisp means "make a compiler for the 'lisp' reader"
lang -c lisp reader_lisp.lang -o lisp_compiler
./lisp_compiler program.lisp -o program
```

The file extension *is* the reader name. Mix `.lang` and `.whatever` files freely - one needs a main.

- [x] Detect non-.lang extensions, wrap in `#ext{ contents }`
- [x] `-c <reader>` flag to generate standalone compiler
- [x] Readers also generate callable functions (no .lang-cache needed at runtime)

---

## Future: AST as Language

The big architectural vision: **AST is the language, syntax is just a skin.**

See `designs/ast_as_language.md` for the full design:
- S-expression AST format as the "root language"
- Readers output AST via typed constructors (never write S-exprs by hand)
- Kernel compiles AST → x86 (or WASM, LLVM IR)
- `lang` becomes just one syntax among many

This is what "compiler compiler" really means - syntax is a plugin, not a property.

### Implementation Path

**1.0: lang as a lang_reader**
1. [ ] `std/ast.lang` - AST node constructors + `ast_emit()`
2. [ ] S-expression parser in kernel
3. [ ] `lang_reader.lang` - lang syntax as a reader
4. [ ] Verify fixed point (kernel + lang_reader compiles itself)
5. [ ] Delete hardcoded parser from current compiler

**Post-1.0: Multiple backends**
6. [ ] WASM backend (portability, browser, WASI)
7. [ ] LLVM IR backend (optimization, more targets)

**2.0: Modern language features** (see `designs/ast_as_language.md`)
8. [ ] First-class functions + closures in AST + lang
9. [ ] Sum types / enums + pattern matching
10. [ ] Generics (monomorphization in kernel)
11. [ ] Exception handling

---

## Stdlib Gaps

- [ ] `memcpy`, `memset`
- [x] `itoa` (number to string)
- [ ] `read_file` (returns contents as string)
- [ ] String builder (have it, needs polish)

---

## Backends

### LLVM IR Output
- [ ] Emit LLVM IR directly (textual .ll files, no libLLVM)
- [ ] Use `llc` to compile to native
- [ ] Enables: optimization, multiple targets

---

## Completed (This Session)

- [x] Deep code review (see REVIEW.md)
- [x] Fixed `vec_new()` ignoring capacity parameter
- [x] Fixed `*(struct.ptr_field)` reading 8 bytes instead of 1
- [x] Added function argument count checking at compile time
- [x] Fixed duplicate includes (idempotent includes)
- [x] Documented `#parser{}` reader macro
- [x] Lisp `defun` with cross-file function interop

## Completed (Previous)

- [x] Self-hosting compiler (x86 fixed point)
- [x] Stdlib (malloc, vec, map)
- [x] Structs with field access
- [x] AST macros (quote/unquote)
- [x] Reader macros V2 (native executables)
- [x] `#parser{}` reader macro
- [x] Reader includes (sibling functions available)
- [x] Parsing toolkit (std/tok.lang, std/emit.lang)

---

## Backlog

- [ ] Floating point types (f32, f64)
- [ ] Struct literals (`Point{x: 1, y: 2}`)
- [ ] Passing/returning structs by value
- [ ] Debug symbols (DWARF)
- [ ] First-class functions (function pointers)
- [ ] Type aliases `type Fd = i64`
- [ ] Multiple backends (x86, ARM, WASM)

---

## Open Questions: Editor Integration

See `designs/source_maps.md` for full analysis.

**Problem**: IDE features (go-to-definition, hover) don't work inside `#lisp{}` blocks because we lose the connection between input positions and generated code.

**Solution**: Mapped emit API. Readers use `reader_emit_from(ctx, start, end)` instead of string concat. Builds source map automatically as a side effect. Readers still output text!

**Syntax highlighting**: Two levels:
1. TextMate embedded languages (regex, no compiler) - works today
2. Semantic highlighting (needs source maps + LSP)

**Key insight**: Readers already tokenize - they have to, to transform. We just ask them to preserve that info when emitting.

**Status**: Design complete, not implemented. Low priority until we want real IDE support.
