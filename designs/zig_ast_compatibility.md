# Yoink & Bootstrap: Capturing Languages Through Their Own Compilers

## The Insight

Don't write frontends. **Capture compilers.**

Every mature language has a bootstrapping compiler - a compiler written in itself that compiles itself. This compiler already solves all the hard problems:
- Lexing, parsing
- Type checking, semantic analysis
- Generics/templates (monomorphization)
- Compile-time evaluation
- Platform-specific codegen

The insight: **Patch the backend to emit lang AST instead of native code.**

```
Traditional approach (hard):
  Zig source → [NEW Zig frontend we write] → lang AST → LLVM → binary

Yoink & Bootstrap (elegant):
  Zig source → [Zig's own compiler, patched] → lang AST → LLVM → binary
```

The Zig team spent years building their frontend. We spend weeks patching their backend.

---

## The Methodology

### Phase 1: Yoink

1. Clone the target language's compiler source
2. Build it on your system (using their bootstrap)
3. Study their internal IR (the representation between frontend and backend)
4. Write a new backend that emits lang AST S-expressions

### Phase 2: Bootstrap

1. Use patched compiler to compile itself → `compiler.ast`
2. Use lang kernel to compile the AST → `compiler_gen1`
3. Use `compiler_gen1` to compile source again → `compiler.ast` (should be identical)
4. **Fixed point achieved** - language is captured

### Phase 3: Captured

The language now exists as lang AST. You can:
- Compile it through any lang backend (x86, LLVM, future WASM)
- Compose it with other lang programs
- Apply lang's tooling (analysis, transformation)
- The original compiler becomes optional - lang IS the compiler now

---

## The Language Forge Value Proposition

**The killer feature isn't "Zig through lang" - it's ONE COMPILER, ONE COMMAND:**

```bash
lang hello.zig world.lang whats.lisp up.my_dsl -o program
```

All syntaxes compose at AST level, compile through one pipeline, produce one binary.

**This is different from LLVM interop:**
- LLVM requires separate frontends for each language
- Each frontend is a massive undertaking (Clang: millions of lines)
- "Interop" means linking, not composition
- DSLs require building an entire compiler

**With lang:**
- Frontends are readers (50-500 lines for a DSL)
- Languages share the same AST before codegen
- Cross-language inlining at AST level
- Create a DSL in 50 lines of `#parser{}` that interops with Zig

**The real value:** A junior dev can create a domain-specific language in an afternoon that compiles to native code and interoperates with production Zig/Rust libraries.

---

## Case Study: Capturing Zig

### Why Zig?

Zig is the credibility move. If lang can capture Zig, it proves the AST is powerful enough for real languages.

Zig is interesting because:
- Self-hosted (stage2 compiler written in Zig)
- Heavy comptime - would be nightmare to reimplement
- Excellent stdlib - practical programs possible
- C ABI compatible - clean interop story
- Relatively small compiler (~200k lines vs GCC's millions)
- **Already has a C backend** - proves backends can be small (~5600 lines)

### Zig's Compiler Architecture

```
Zig source
    ↓
  Tokenizer
    ↓
  Parser → AST (Zig's AST)
    ↓
  Semantic Analysis (Sema)
    ↓
  AIR (Analyzed Intermediate Representation)  ← WE INTERCEPT HERE
    ↓
  [LLVM Backend | Self-hosted Backend]
    ↓
  Binary
```

**AIR** is the goldmine. By the time code reaches AIR:
- All `comptime` blocks → evaluated to concrete values
- All generics → monomorphized to specific types
- All `@typeInfo`/`@Type` → resolved
- All inline loops → unrolled
- All conditional compilation → resolved
- All `defer`/`errdefer` → control flow already inserted
- All optionals/errors → lowered to tagged unions

AIR is **low-level enough** that most constructs map directly to lang AST.

### AIR Format Details

AIR has approximately **180 instruction types** organized into categories:

**Arithmetic/Logic (~30 instructions):**
- `add`, `sub`, `mul`, `div_trunc`, `div_floor`, `mod`, `rem`
- `and`, `or`, `xor`, `shl`, `shr`
- `cmp_lt`, `cmp_lte`, `cmp_eq`, `cmp_neq`, `cmp_gte`, `cmp_gt`

**Memory (~20 instructions):**
- `load`, `store`, `memcpy`, `memset`
- `alloc`, `ret_ptr`, `arg`
- `struct_field_ptr`, `slice_ptr`, `array_elem_ptr`

**Control Flow (~15 instructions):**
- `br`, `cond_br`, `switch_br`
- `loop`, `repeat`, `block`
- `call`, `ret`

**Type Operations (~25 instructions):**
- `bitcast`, `intcast`, `trunc`, `fpext`, `fptrunc`
- `int_from_ptr`, `ptr_from_int`
- `aggregate_init`, `union_init`, `array_init`

**Float Operations (~20 instructions):**
- `fadd`, `fsub`, `fmul`, `fdiv`
- `fmax`, `fmin`, `sqrt`, `ceil`, `floor`
- `cmp_eq_optimized`, `cmp_lt_optimized` (float-specific)

**SIMD/Vector (~15 instructions):**
- `splat`, `shuffle`, `reduce`
- `select`, `mask_*`

**Atomics (~10 instructions):**
- `atomic_load`, `atomic_store`
- `atomic_rmw` (with sub-ops: add, sub, xchg, cmpxchg)
- `fence`

**Debug/Trap (~5 instructions):**
- `dbg_stmt`, `dbg_inline_block`
- `trap`, `breakpoint`

Most of these map cleanly to lang AST. Key exceptions:
- Float ops → lang needs f32/f64 support
- SIMD → lang needs vector types
- Atomics → lang needs atomic primitives

### What AIR Looks Like

After Zig's semantic analysis, complex code becomes simple:

```zig
// Original Zig (generic + comptime)
fn max(comptime T: type, a: T, b: T) T {
    return if (a > b) a else b;
}
const x = max(i64, 10, 20);
```

```
// In AIR (after monomorphization + evaluation)
// The generic is gone - just a concrete i64 function
// The comptime call is gone - x is just the value 20
```

**Using `--verbose-air` to see real AIR output:**
```bash
zig build-obj hello.zig --verbose-air
```

Produces output showing the lowered instructions, which is invaluable for understanding the mapping.

This AIR representation is what we emit as lang AST.

### AST Extensions Needed

Lang's AST is already close. These extensions complete the capture:

| Extension | AIR Feature | Difficulty | Implementation |
|-----------|-------------|------------|----------------|
| `callconv` | Calling conventions | Medium | Add attribute to `func` node |
| `inline-asm` | Inline assembly | Medium | Structured asm node with inputs/outputs/clobbers |
| `type-vector` | SIMD types | Medium | `(type-vector 4 (type-base f32))` |
| `packed-struct` | Bit-level layout | Hard | New struct variant with bit fields |
| `type-aligned` | Alignment control | Easy | Wrapper type with alignment annotation |

#### callconv

```lisp
;; Current
(func syscall3 ((param n (type-base i64)) ...) (type-base i64) ...)

;; Extended
(func syscall3 ((param n (type-base i64)) ...) (type-base i64)
  (callconv naked)  ; or: interrupt, c, stdcall, etc.
  ...)
```

Kernel impact: Codegen needs multiple prologue/epilogue patterns.

#### inline-asm

```lisp
(inline-asm "syscall"
  ((output "={rax}" (ident ret)))
  ((input "{rax}" (ident num))
   (input "{rdi}" (ident arg1)))
  ((clobber "rcx")
   (clobber "r11")))
```

Kernel impact: Already have raw asm for effects. This adds structure.

#### type-vector

```lisp
(var v (type-vector 4 (type-base f32))
  (vector-literal (number 1.0) (number 2.0) (number 3.0) (number 4.0)))
(binop + (ident v) (ident v))  ; SIMD add
```

Kernel impact: Need SIMD register allocation, vector operations in codegen.

#### packed-struct

```lisp
(packed-struct Flags
  ((field-decl a (type-bits 1))
   (field-decl b (type-bits 3))
   (field-decl c (type-bits 4))))
;; Total size: 1 byte, not 3 bytes
```

Kernel impact: Bit-level field access. This is the hardest extension.

#### type-aligned

```lisp
(var buffer (type-aligned 16 (type-array 64 (type-base u8))) ...)
```

Kernel impact: Stack allocation respects alignment. Relatively easy.

### The Backend Implementation

The new Zig backend (written in Zig, ~3-5k lines estimated):

```zig
// pseudocode structure
const LangAstBackend = struct {
    output: std.fs.File,

    pub fn emit(self: *@This(), air: Air) !void {
        try self.output.writeAll("(program\n");

        // Emit all struct definitions
        for (air.types) |ty| {
            if (ty.isStruct()) try self.emitStruct(ty);
        }

        // Emit all functions
        for (air.functions) |func| {
            try self.emitFunction(func);
        }

        try self.output.writeAll(")\n");
    }

    fn emitFunction(self: *@This(), func: Air.Function) !void {
        // (func name (params...) ret-type body)
        try self.output.print("(func {s} (", .{func.name});
        for (func.params) |p| try self.emitParam(p);
        try self.output.writeAll(") ");
        try self.emitType(func.return_type);
        try self.output.writeAll("\n");
        try self.emitBody(func.body);
        try self.output.writeAll(")\n");
    }

    fn emitInstruction(self: *@This(), inst: Air.Inst) !void {
        switch (inst.tag) {
            .add => try self.output.print("(binop + {s} {s})", .{...}),
            .call => try self.output.print("(call {s} ...)", .{...}),
            .br => try self.output.print("(if {s} ...)", .{...}),
            // ... ~50 instruction types
        }
    }
};
```

### The Bootstrap Sequence

```bash
# 1. Build Zig's compiler with our patched backend
cd zig-source
zig build -Dbackend=lang-ast

# 2. Compile Zig's compiler to lang AST
./zig-with-lang-backend build-exe src/main.zig --emit-ast > zig-compiler.ast

# 3. Compile the AST through lang
lang zig-compiler.ast -o zig-gen1

# 4. Use gen1 to compile Zig again
./zig-gen1 build-exe src/main.zig --emit-ast > zig-compiler2.ast

# 5. Verify fixed point
diff zig-compiler.ast zig-compiler2.ast  # Should be identical!

# 6. Zig is captured. zig-gen1 IS the Zig compiler, running on lang kernel.
```

### What We Get

Once Zig is captured:

1. **Zig programs compile through lang's LLVM backend**
   - All of Zig's optimizations from their frontend
   - All of LLVM's optimizations from our backend

2. **Zig stdlib available to lang programs**
   - Import Zig modules into lang readers
   - Cross-language composition at AST level

3. **Single toolchain**
   - One compiler binary handles `.lang`, `.zig`, any captured syntax
   - Unified debugging, profiling, analysis

4. **Future backends automatic**
   - When lang gets WASM backend, Zig gets WASM
   - When lang gets new target, Zig gets it free

---

## Generalized: The Capture Protocol

This works for any self-hosted language:

| Language | Compiler | Internal IR | Capture Difficulty |
|----------|----------|-------------|-------------------|
| Zig | stage2 | AIR | Medium - clean IR |
| Rust | rustc | MIR | Hard - complex, huge |
| Go | gc | SSA | Medium - well-documented |
| OCaml | ocamlopt | Lambda/Cmm | Medium |
| Haskell | GHC | Core/STG | Hard - lazy semantics |
| Swift | swiftc | SIL | Hard - ARC complexity |
| D | dmd | ? | Medium |

**The pattern:**
1. Find where frontend ends and codegen begins
2. Insert AST emitter at that boundary
3. Handle any semantic gaps with AST extensions

### Languages That Can't Be Captured

Some languages resist this approach:

**Languages with runtime-dependent semantics:**
- Python, Ruby, JavaScript - semantics depend on runtime behavior
- No clear "compile" phase to intercept
- Would need to capture the interpreter instead

**Languages with exotic execution models:**
- Erlang/BEAM - bytecode for specific VM
- Prolog - unification-based execution
- Would need to emulate their runtime model

**Non-self-hosted languages:**
- If the compiler is written in C, you can't bootstrap through lang
- You'd compile a C compiler first, then the target language

---

## What Makes This Powerful

### The Semantic Funnel

```
     Zig  ───┐
     Rust ───┼───→ lang AST ───→ LLVM IR ───→ native
     Go   ───┤        ↑
     ... ────┘        │
                 single kernel
```

Every captured language funnels through one semantic representation. This is the "language forge" - syntax is a plugin, lang AST is the common core.

### Composition Becomes Natural

```lisp
;; A program mixing syntaxes
(program
  (require "crypto.zig")      ; Zig's crypto library, as AST
  (require "parser.lang")     ; Our parser, native lang
  (require "server.rs")       ; Rust HTTP server, as AST

  (func main () ...)          ; Glue code
)
```

Different languages, same compilation pipeline, same ABI, single binary.

### Optimization Across Languages

Because everything becomes lang AST before LLVM:
- Cross-language inlining possible at AST level
- Unified memory layout analysis
- Whole-program optimization spans languages

---

## The Vision

Lang is not trying to be a better Zig or a better Rust. It's trying to be the **kernel that captures them all**.

```
Traditional world:
  Source → [Language-specific compiler] → Binary

Lang forge world:
  Source → [Language's own frontend, patched] → lang AST → [lang kernel] → Binary
```

The "language forge" endgame:
1. Capture major languages via their own compilers
2. Any syntax compiles to lang AST
3. Lang AST compiles to any target
4. **Syntax is decoupled from execution**

This isn't about replacing languages. It's about **factoring out the kernel** - the part that actually generates code - and letting languages focus on their frontend (parsing, type checking, ergonomics) while lang handles the backend (optimization, codegen, targets).

---

## Immediate Next Steps

### Week 1-2: Zig Deep Dive
- Study Zig's AIR format in detail
- Document AIR instruction → lang AST mapping
- Identify all needed AST extensions

### Week 3-4: AST Extensions
- Implement `callconv` support in kernel
- Implement `inline-asm` node
- Implement `type-aligned`
- Defer packed-struct and SIMD (not needed for bootstrap)

### Week 5-6: Backend Implementation
- Write lang-ast backend for Zig compiler
- Start with subset (no async, no SIMD)
- Get "hello world" through the pipeline

### Week 7-8: Bootstrap Attempt
- Compile Zig compiler to AST
- Fix issues as they arise
- Achieve fixed point

### Success Criteria

**Minimum viable capture:**
- Zig compiler compiles through lang
- Can compile simple Zig programs
- Fixed point bootstrap achieved

**Full capture:**
- Zig stdlib works
- All Zig language features handled
- Performance parity with native Zig

---

## Feasibility Assessment

### Timeline Estimates

| Milestone | Effort | Dependencies |
|-----------|--------|--------------|
| Hello world through lang | 2-3 weeks | Integer/string support only |
| Zig stdlib basics | 1-2 months | Float support critical |
| Zig compiler self-hosts | 3-6 months | Float, many AIR instructions |
| Full capture (all features) | 6-12 months | SIMD, atomics, packed structs |

### Known Gaps in Lang

| Gap | Severity | Impact on Zig Capture |
|-----|----------|----------------------|
| **Floating point (f32, f64)** | **Critical** | Zig compiler uses floats; hello world doesn't |
| SIMD vectors | Medium | Skip initially, needed for perf-sensitive code |
| Atomics | Low | Skip initially, needed for threading |
| Packed structs | Low | Skip initially, Zig can workaround |
| Inline assembly (structured) | Medium | Lang has raw asm; structured needs work |

**Floating point is the gate:** Simple programs can work without floats. The Zig compiler itself uses floats for various calculations. Full capture requires f32/f64 support.

### Reference: Zig's C Backend

Zig already has a C backend in `src/codegen/c.zig` (~5600 lines). This proves:
1. Backends can be small relative to the compiler
2. Text-based output (like AST S-exprs) is viable
3. The AIR → text emission pattern works

Our lang AST backend would be similar in approach.

### Risk Assessment

**Low risk:**
- Basic arithmetic, control flow, function calls
- Struct definitions and field access
- Pointer operations

**Medium risk:**
- Calling convention variations
- Alignment requirements
- Error union lowering

**High risk:**
- Float operations (completely missing in lang)
- SIMD (needs new type system support)
- Async/suspend (complex control flow)

### Recommended Approach

1. **Start with integer-only subset** - Get "hello world" working first
2. **Add floats to lang** - Required for serious Zig programs
3. **Iterate on AIR coverage** - Handle instructions as needed
4. **Defer SIMD/atomics** - Not needed for initial capture

---

## Appendix: Why Not Just Use LLVM IR?

"Zig already emits LLVM IR. Why not capture that?"

1. **LLVM IR is too low-level** - No structs, no types beyond primitives, no functions as values
2. **Lost semantic information** - Can't do lang-level analysis or composition
3. **Lost portability** - LLVM IR is target-specific after lowering
4. **Not the forge vision** - We want to capture languages, not just compile them

Lang AST sits at the right level - high enough to preserve semantics, low enough to compile efficiently.

---

## Summary

| Approach | Effort | Result |
|----------|--------|--------|
| Write Zig frontend | Years | Another Zig implementation |
| Patch Zig backend | Weeks | Zig captured by lang |

The "Yoink & Bootstrap" methodology turns compiler capture from an impossible task into a tractable engineering project. Zig is the proof of concept - if we can capture Zig, we can capture anything self-hosted.

**Lang's thesis: Syntax is arbitrary. Semantics are universal. The kernel captures both.**

---

## Appendix: Resources

### Zig Internals

**Mitchell Hashimoto's articles** (https://mitchellh.com/zig) - Excellent deep dives:
- "Zig Compiler Internals" - Covers tokenizer → AST → Sema → AIR pipeline
- Performance analysis and optimization insights
- Practical experience building with Zig

**DeepWiki Zig C Backend docs** - The C backend implementation:
- `src/codegen/c.zig` structure and approach
- Type emission patterns
- How AIR instructions map to C constructs

**Zig source code reference:**
- `src/Air.zig` - AIR instruction definitions (~180 tags)
- `src/codegen.zig` - Backend interface
- `src/codegen/c.zig` - C backend (~5600 lines, good reference)
- `src/codegen/llvm.zig` - LLVM backend (more complex)

### Using --verbose-air

```bash
# See AIR for a simple program
echo 'pub fn main() void { @import("std").debug.print("hello", .{}); }' > /tmp/test.zig
zig build-obj /tmp/test.zig --verbose-air 2>&1 | head -100
```

This shows the lowered representation we'd be capturing.

### Lang AST Reference

See `docs/AST.md` for the 41 node types lang currently supports. Key mappings:
- AIR `add/sub/mul` → lang `(binop + ...)`, `(binop - ...)`, `(binop * ...)`
- AIR `load/store` → lang `(unop * ...)` (deref), `(assign ...)`
- AIR `call` → lang `(call ...)`
- AIR `br/cond_br` → lang `(if ...)`, `(while ...)`
- AIR `ret` → lang `(return ...)`
