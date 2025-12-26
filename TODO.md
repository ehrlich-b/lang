# language - TODO

## Vision

**Racket-style power with Zig-style minimalism. For fun.**

A language forge: full-power reader macros, parsing toolkit, bare-metal output.

**The killer feature**: Trivially create DSLs that compile straight to x86 - no runtime, no VM, just your syntax → machine code.

---

## Current State

**Reader Macros V2 Core: COMPLETE** (but needs polish)

Readers compile to native executables that output lang source text. The infrastructure works.

**Blocking issues:**
- Readers can't include helper files (only reader body is compiled)
- No file extension dispatch yet

---

## Immediate: Reader Architecture Fixes

### Reader Includes
- [ ] Readers must be able to `include` files into their compilation
- [ ] Functions defined in the same file as a reader should be available to it
- [ ] Current bug: only code inside `reader foo() { ... }` braces is compiled

### File Extension Dispatch
- [ ] `lang reader.lang main.lisp` → compile main.lisp using reader, produce exe
- [ ] Flow: detect .lisp extension → find lisp reader → `#lisp{file content}` → compile
- [ ] This completes the "language forge" vision

---

## Future: Parser Generator (Killer Feature)

First-class functions would enable beautiful parser combinators:

```lang
var sexp Parser = p_or(
    p_number(),
    p_seq(p_lparen(), p_many(sexp), p_rparen())
);

reader lisp(text *u8) *u8 {
    return parse(sexp, text);
}
```

This is the dream: define a grammar, get a native parser. No runtime, no interpreter - just x86.

### Requirements
- [ ] First-class functions (function pointers at minimum)
- [ ] Parser combinator library (std/parse.lang)
- [ ] Lazy evaluation or explicit thunks for recursive grammars

---

## Parsing Toolkit (Current)

- [x] std/tok.lang - Tokenizer
- [x] std/emit.lang - Code generation helpers
- [ ] std/sexp.lang - S-expression parser (blocked on reader includes)
- [ ] Beautiful lisp example (blocked on reader includes)

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

- **Phase 0**: Bootstrap compiler (Go) - deleted after bootstrap
- **Phase 1**: Self-hosting - compiler compiles itself, fixed point reached
- **Phase 1.5**: Stdlib (malloc, vec, map)
- **Phase 1.6**: Structs
- **Phase 2**: AST macros (quote/unquote, compile-time interpreter)
- **Phase 3**: Reader macros V1 (toy interpreter)
- **Phase 3.5**: Reader macros V2 core (native executables, include statement, 80 tests)
- **Phase 3.6**: Parsing toolkit (std/tok.lang, std/emit.lang)

---

## Future Ideas

- Swappable GC (written in lang, user-replaceable like Zig allocators)
- LSP / IDE integration
- Multiple backends (x86, ARM, WASM)
