# language - TODO

## Vision

**A self-hosted compiler compiler.**

Lang + reader macro = native compiler for any syntax. No runtime, no VM, just x86.

```
lang lisp_reader.lang main.lisp  →  native executable
lang sql_reader.lang queries.sql →  native executable
lang your_dsl.lang your_code.x   →  native executable
```

**The milestones:**
1. ✓ Self-hosting compiler (x86 fixed point)
2. ✓ Self-hosted compiler compiler (reader infrastructure in lang)
3. ✓ Reader includes (sibling functions available to readers)
4. → `#parser{}` reader (parser generator as reader macro)
5. → Lisp reader using `#parser{}` (beautiful!)
6. → `lang_reader.lang` (lang syntax defined in lang)
7. → Language forge (trivially spin out compilers)

---

## Current State

**Reader Macros V2 Core: COMPLETE** (but needs polish)

Readers compile to native executables that output lang source text. The infrastructure works.

**Next up:**
- File extension dispatch (`lang reader.lang main.lisp`)
- `#parser{}` reader macro

---

## Immediate: Reader Architecture Fixes

### Reader Includes ✓
- [x] Readers can `include` files into their compilation
- [x] Functions defined in included files are available to readers
- [x] Include statements, struct declarations, and functions are serialized into reader wrapper
- Note: Readers in included files get full sibling access; command-line readers use stdlib via compile args

### File Extension Dispatch
- [ ] `lang reader.lang main.lisp` → compile main.lisp using reader, produce exe
- [ ] Flow: detect .lisp extension → find lisp reader → `#lisp{file content}` → compile
- [ ] This completes the "language forge" vision

---

## Future: `lang_reader.lang` (Self-Defining Syntax)

Define lang's syntax as a lang reader macro. See `designs/self_defining_syntax.md`.

Milestone like x86 fixed point - proves the compiler compiler can define itself.

---

## Future: `#parser{}` Reader (Parser Generator as a Reader Macro!)

Instead of first-class functions, use a reader macro to generate parsers:

```lang
#parser{
    sexp = number | symbol | '(' sexp* ')'
}
```

Emits recursive descent code:
```lang
func parse_sexp(t *Tokenizer) *u8 {
    if tok_kind(t) == TOK_NUMBER { ... }
    if tok_kind(t) == TOK_LPAREN { ... }
}
```

**The killer feature**: Readers invoking readers!

```lang
reader lisp(text *u8) *u8 {
    #parser{
        sexp = number | symbol | '(' sexp* ')'
    }
    return parse_sexp(tok_new(text));
}
```

The `#parser{}` reader runs at compile time, generates the parser, and the lisp reader uses it. DSLs for writing DSLs - every layer compiles to native code.

### Requirements
- [x] Reader includes
- [ ] `#parser{}` reader macro
- [ ] BNF/PEG grammar parser
- [ ] Recursive descent code generator

---

## Parsing Toolkit (Current)

- [x] std/tok.lang - Tokenizer
- [x] std/emit.lang - Code generation helpers
- [ ] std/sexp.lang - S-expression parser
- [ ] Beautiful lisp example

---

## V2 Cleanup

- [x] Delete V1 interpreter builtins
- [ ] File extension dispatch (see above)
- [ ] Meta-include `std:core.lang` for programs outside repo

---

## Bugs

- [ ] **`*(struct.ptr_field)` reads 8 bytes instead of 1** - When dereferencing a pointer field from a struct (e.g., `*(t.input + offset)`), the compiler reads 8 bytes (i64) instead of 1 byte (u8). Workaround: assign to temp variable first (`var p *u8 = t.input; *(p + offset)`). See `test/struct_ptr_debug.lang`.

- [ ] **Functions with >6 parameters generate broken assembly** - The 7th+ parameters (which go on stack per x86_64 ABI) generate malformed assembly like `-56(%rbp)` without a mov instruction. Workaround: pass a struct or array instead of many parameters.

---

## Language Features (Low-Hanging Fruit)

- [ ] Forward declarations (`func foo() void;` - needed for mutual recursion)
- [ ] First-class functions (function pointers)
- [ ] Character literals `'a'` (currently use 97)
- [ ] Bitwise operators `& | ^ << >>`
- [ ] Compound assignment `+= -= *= /=`
- [ ] `for` loop sugar
- [ ] `break` / `continue`
- [ ] Type aliases `type Fd = i64`

---

## Stdlib Gaps

- [ ] `memcpy`, `memset`
- [ ] `itoa` (number to string)
- [ ] String builder
- [ ] `read_file` (returns contents as string)

---

## Backends

### LLVM IR Output
- [ ] Emit LLVM IR directly (textual .ll files, no libLLVM)
- [ ] Use `llc` to compile to native
- [ ] Enables: optimization, multiple targets, easier debugging

---

## Backlog

- [ ] Floating point types (f32, f64)
- [ ] Struct literals (`Point{x: 1, y: 2}`)
- [ ] Passing/returning structs by value
- [ ] Debug symbols (DWARF)
- [ ] Reader caching (invalidate on source change)

---

## Completed

**Milestone 1: Self-Hosting Compiler** (x86 fixed point)
- Phase 0: Bootstrap compiler (Go) - deleted after bootstrap
- Phase 1: Self-hosting - compiler compiles itself, fixed point reached
- Phase 1.5: Stdlib (malloc, vec, map)
- Phase 1.6: Structs

**Milestone 2: Self-Hosted Compiler Compiler** (reader infrastructure)
- Phase 2: AST macros (quote/unquote, compile-time interpreter)
- Phase 3: Reader macros V1 (toy interpreter)
- Phase 3.5: Reader macros V2 core (native executables, include statement, 80 tests)
- Phase 3.6: Parsing toolkit (std/tok.lang, std/emit.lang)
- Phase 3.7: Reader includes (sibling functions available to readers, 81 tests)

---

## Future Ideas

- Swappable GC (written in lang, user-replaceable like Zig allocators)
- LSP / IDE integration
- Multiple backends (x86, ARM, WASM)
