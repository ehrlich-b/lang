# ABI Design: Calling Conventions and Language Capture

## The question

What would it take to "fully capture" another language - parse its source, emit lang AST, compile with lang's kernel?

Zig is the interesting test case. It's a systems language with explicit control over calling conventions, memory layout, and low-level details. If we can capture Zig, we can capture most things.

## The direction

```
Zig source → Zig reader → lang AST → lang kernel → x86/LLVM
```

Not the other way around. We're not emitting Zig - we're consuming it.

---

## Current lang ABI

### Base convention: System V AMD64

```
Parameters: rdi, rsi, rdx, rcx, r8, r9, then stack
Return: rax
Callee-saved: rbx, rbp, r12-r15 (but lang doesn't use them)
Stack: 16-byte aligned at call
```

Standard C ABI on Linux x86-64. Nothing special here.

### Closure calling: hidden first argument

When calling through a closure variable, we check a tag and conditionally pass the closure struct as the first argument:

```asm
# Closure struct layout: [tag:8][fn_ptr:8][captures...]
# tag == 0: plain function pointer (no extra arg)
# tag == 1: closure (pass struct as first arg)

    mov closure(%rbp), %r10      # Load closure struct pointer
    mov (%r10), %r11             # Load tag
    test %r11, %r11
    jz plain_call

closure_call:
    # Shift all args right by one register
    mov %r9, %rax; push %rax     # arg6 -> stack (if present)
    mov %r8, %r9                 # arg5 -> arg6
    mov %rcx, %r8                # arg4 -> arg5
    mov %rdx, %rcx               # arg3 -> arg4
    mov %rsi, %rdx               # arg2 -> arg3
    mov %rdi, %rsi               # arg1 -> arg2
    mov %r10, %rdi               # closure -> arg1
    mov 8(%r10), %rax            # Load fn_ptr
    call *%rax
    jmp done

plain_call:
    mov 8(%r10), %rax
    call *%rax

done:
```

**Is this standard?**

Not quite. The System V AMD64 ABI designates **R10 as the static chain pointer** for nested functions. From [The Old New Thing](https://devblogs.microsoft.com/oldnewthing/20231204-00/?p=109095):

> The static chain pointer points to the stack frame of the lexically enclosing function. Using this environment pointer it is then possible to access the variables stored in the stack frame of the parent function.

GCC uses R10 this way for nested functions. We're using RDI (first argument) instead, which is more like C++ `this` pointer convention.

**Options to make it standard:**
1. **Keep as-is** - Works, well-defined, just not the "static chain" convention
2. **Use R10** - Would match GCC nested functions, but breaks our "tag check" pattern
3. **Document it** - Call it "closure calling convention" and move on

**Recommendation:** Keep as-is, document it. The tag-based dispatch is useful for our closure/plain-function unification.

### Effect continuations: hand-rolled setjmp/longjmp

For algebraic effects, we save/restore execution state manually:

```asm
# On handle { ... } entry:
    movq %rbp, __handler_rbp(%rip)    # Save frame pointer
    movq %rsp, __handler_rsp(%rip)    # Save stack pointer
    leaq handler_label(%rip), %rax
    movq %rax, __handler_addr(%rip)   # Save handler address

# On perform Effect():
    # Save continuation: [rbp:8][rsp:8][return_addr:8]
    # Store in __continuation_ptr
    movq __handler_rbp(%rip), %rbp    # Restore handler's frame
    jmpq *__handler_addr(%rip)        # Jump to handler

# On resume k(value):
    # Load continuation struct
    mov (%r12), %rbp                  # Restore saved rbp
    mov 8(%r12), %rsp                 # Restore saved rsp
    jmpq *16(%r12)                    # Jump to saved return addr
```

**Is this standard?**

No. This is custom. The closest standard things are:

1. **setjmp/longjmp** - C library, but only supports "upward" jumps (unwinding). We need bidirectional (resume can go back down).

2. **[LLVM coroutine intrinsics](https://llvm.org/docs/Coroutines.html)** - `llvm.coro.id.retcon.once` is designed for exactly one-shot continuations:
   > In yield-once returned-continuation lowering, the coroutine must suspend itself exactly once. The ramp function returns a continuation function pointer and yielded values.

   This is exactly what algebraic effects do: suspend once, return continuation + value, resume later.

3. **Stack copying** - Some Scheme implementations copy stack segments. We don't do this.

**Options to make it more standard:**

1. **Use LLVM coroutines in LLVM backend** - Let LLVM handle the state machine transform. More portable, better optimized.

2. **Keep inline asm in x86 backend** - Simple, works, no external deps.

3. **Use actual setjmp/longjmp** - Would require libc, and doesn't support resume (only abort).

**Recommendation:**
- LLVM backend could migrate to `llvm.coro.id.retcon.once` intrinsics
- x86 backend keeps inline asm (simple, no deps)
- Both produce same observable behavior
- This is why we have two backends: x86 for simplicity, LLVM for features

---

## The x86 bootstrap question

**If we add exotic calling conventions (naked, interrupt), do we abandon x86?**

No. The strategy:

| Feature | x86 backend | LLVM backend |
|---------|-------------|--------------|
| C ABI | Yes | Yes |
| Closure calling | Custom (RDI) | Custom (first arg) |
| Effect continuations | Inline asm | Could use llvm.coro |
| Naked functions | No | Yes (via LLVM) |
| Interrupt handlers | No | Yes (via LLVM) |
| Exotic conventions | No | Yes |

The x86 backend stays simple: C ABI + our closure/effect extensions. The LLVM backend can grow to support exotic conventions by passing them through to LLVM.

This is fine. The x86 backend is:
- Fast (5s vs 25-30s bootstrap)
- Auditable (human-readable assembly)
- Minimal deps (just as, ld)
- Good for development iteration

The LLVM backend is:
- Portable (anywhere clang runs)
- Full-featured (all conventions LLVM supports)
- Optimizable (LLVM optimization passes)
- Good for production/distribution

Both produce compilers that pass the same 167 tests. Different tradeoffs.

---

## Zig's calling conventions

From [Zig's std.builtin.CallingConvention](https://github.com/ziglang/zig/blob/master/lib/std/builtin.zig):

**Architecture-specific:**
- `.x86_64_sysv` - System V AMD64 (what lang uses)
- `.x86_64_win` - Windows x64
- `.x86_64_vectorcall` - SIMD-heavy Windows
- `.x86_64_interrupt` - x86 interrupt handlers
- `.aarch64_aapcs` - ARM64 standard
- `.aarch64_aapcs_darwin` - ARM64 Apple variant
- `.arm_aapcs` - ARM32
- `.arm_aapcs_vfp` - ARM32 with VFP
- `.riscv64_interrupt` - RISC-V interrupt
- etc.

**Special:**
- `.C` - Platform's C ABI (what `extern` implies)
- `.Naked` - No prologue/epilogue, raw assembly
- `.Inline` - Force inlining
- `.Async` - Zig's stackless coroutines
- `.Unspecified` - Zig's internal convention

Each convention specifies:
- Which registers hold parameters
- Which registers are callee-saved
- Stack alignment requirements
- How to handle variadic arguments
- Return value location

## The capture problem

If we write a Zig reader that emits lang AST, what happens to calling conventions?

### Case 1: Normal functions

```zig
fn add(a: i64, b: i64) i64 {
    return a + b;
}
```

This uses Zig's internal convention (`.Unspecified`). We can emit:

```lisp
(func add ((param a (type-base i64)) (param b (type-base i64)))
  (type-base i64)
  (block (return (binop + (ident a) (ident b)))))
```

Works fine. Lang's default convention is close enough.

### Case 2: Extern functions

```zig
extern fn write(fd: c_int, buf: [*]const u8, count: usize) isize;
```

This requires C ABI. Lang has `extern func`:

```lisp
(extern write ((type-base i64) (type-ptr (type-base u8)) (type-base i64))
  (type-base i64))
```

Works. Both use System V.

### Case 3: Explicit calling convention

```zig
fn handler() callconv(.x86_64_interrupt) void {
    // interrupt handler
}
```

**Problem.** Lang's AST has no way to express this. The `func` node doesn't have a calling convention field.

```lisp
(func handler () (type-base void) ...)  ; Where does callconv go?
```

Options:
1. **Ignore it** - Emit as normal function, hope for the best (broken)
2. **Reject it** - Zig reader refuses code with non-C conventions (limited)
3. **Extend AST** - Add calling convention to func nodes (invasive)
4. **Inline assembly** - Emit the whole function as asm (escape hatch)

### Case 4: Naked functions

```zig
fn _start() callconv(.Naked) noreturn {
    asm volatile ("mov $60, %rax; xor %rdi, %rdi; syscall");
}
```

Naked means no prologue, no epilogue, no stack frame. The function body IS the assembly.

Lang can't express "don't generate prologue." Every function gets `push %rbp; mov %rsp, %rbp; ...`.

### Case 5: Async functions

```zig
fn fetchData() callconv(.Async) ![]u8 {
    const result = await asyncRead();
    return result;
}
```

Zig's async is stackless coroutines with explicit frame allocation. Completely different from lang's algebraic effects (which use stack manipulation).

Not a calling convention problem per se, but a semantic gap.

## What "fully capturing Zig" would require

### AST extensions

```lisp
;; Current func node
(func <name> (<param>*) <ret-type> <body>)

;; Extended func node with calling convention
(func <name> (<param>*) <ret-type> <calling-conv>? <body>)

;; Calling convention options
(callconv c)           ; C ABI
(callconv naked)       ; No prologue/epilogue
(callconv interrupt)   ; Interrupt handler ABI
(callconv inline)      ; Force inline
```

### Codegen changes

The kernel would need to:

1. **Parse calling convention** from func node
2. **Select register assignment** based on convention
3. **Generate appropriate prologue/epilogue** (or none for naked)
4. **Handle special cases** like interrupt frames

This is substantial. Currently codegen assumes one convention everywhere.

### Feature mapping

| Zig feature | Lang equivalent | Gap |
|-------------|-----------------|-----|
| `callconv(.C)` | `extern func` | Works |
| `callconv(.Naked)` | None | Need AST extension |
| `callconv(.Interrupt)` | None | Need AST extension + codegen |
| `callconv(.Async)` | Effects? | Semantic mismatch |
| `callconv(.Inline)` | None | Optimization hint |
| Comptime | Reader macros | Different phase |
| `!T` error unions | Effects or enum | Encoding difference |
| `?T` optionals | Enum | Direct mapping |
| Slices `[]T` | Struct | Need convention |
| Packed structs | None | Need layout control |
| SIMD vectors | None | Need vector types |
| `@cImport` | `extern func` | Manual declarations |

## The boundary question

Where do we draw the line?

### Option A: C ABI only

Lang only supports C calling convention. Zig code using other conventions can't be captured.

**Implication:** Can capture ~80% of Zig code. Interrupt handlers, naked functions, and exotic ABIs require manual port.

**Pro:** Simple. Clear boundary.
**Con:** Can't be a full Zig replacement.

### Option B: Add calling convention to AST

Extend `func` node with optional calling convention. Kernel learns multiple ABIs.

```lisp
(func _start () (type-base void) (callconv naked)
  (inline-asm "mov $60, %rax; ..."))
```

**Implication:** Can capture most Zig, but need codegen work per convention.

**Pro:** Enables interrupt handlers, OS kernels, etc.
**Con:** Complexity. Each convention needs testing.

### Option C: Escape to inline assembly

For non-C conventions, emit the entire function as inline assembly.

```lisp
(inline-asm-func "_start" "
    .globl _start
    _start:
    mov $60, %rax
    xor %rdi, %rdi
    syscall
")
```

**Implication:** Can emit anything, but loses abstraction benefits.

**Pro:** Complete escape hatch.
**Con:** Not really "capturing" - just passing through.

## Recommendation

**Start with Option A (C ABI only), add B incrementally.**

1. **Phase 1:** Zig reader emits lang AST for C-convention code
   - Normal functions → lang functions
   - Extern functions → extern func
   - Reject explicit non-C callconv

2. **Phase 2:** Add `callconv` to AST, implement in kernel
   - `naked` first (simplest - just skip prologue)
   - `inline` (optimization hint)
   - `interrupt` (if someone needs OS dev)

3. **Phase 3:** Complex conventions
   - Async (requires deep integration with effects)
   - Vectorcall (requires SIMD support)

The key insight: **most Zig code uses default or C convention.** The exotic conventions are for OS kernels, drivers, and embedded. That's a small fraction of code.

## Other languages

### Rust

```rust
extern "C" fn foo() {}           // C ABI - works
extern "system" fn bar() {}      // Platform ABI - works (is C on Unix)
extern "Rust" fn baz() {}        // Rust internal - undefined, don't rely on it
```

Rust's internal ABI is explicitly unstable. For FFI, Rust uses C. We can capture C-convention Rust.

### C

C only has one calling convention per platform. No problem.

### C++

C++ has `extern "C"` for C convention, otherwise uses platform C++ ABI (which varies). Name mangling is the bigger issue. For `extern "C"` functions, no problem.

### Go

Go's ABI is fundamentally incompatible. See below.

## Go: why it can't work

Go's calling convention is unique:

1. **Stack-based parameters** (was, now register-based but still custom)
2. **Multi-value returns** that don't fit in registers
3. **Growable stacks** requiring special prologues
4. **No callee-saved registers** for GC root tracking
5. **Hidden goroutine context** threading through calls

From [Go internal ABI](https://tip.golang.org/src/cmd/compile/abi-internal):

> Go's ABI is intentionally different from C. Goroutines need dynamically-sized stacks. Multi-value returns are common. GC needs to trace roots.

You can't "capture" Go by emitting lang AST because the semantics require runtime support lang doesn't have:
- Goroutine scheduler
- Stack copying on growth
- GC integration

**Verdict:** Go interop goes through cgo. No direct capture possible.

## Implementation notes

### Adding callconv to AST

```lisp
;; Parser change: func can have optional callconv before body
(func name (params) ret-type (callconv CONV)? body)

;; Where CONV is one of:
;;   c        - C ABI (default for extern)
;;   naked    - No prologue/epilogue
;;   inline   - Force inline
;;   interrupt - Interrupt handler (save all, iret)
```

### Codegen for naked

```lang
if callconv == CALLCONV_NAKED {
    // Skip prologue generation
    // Generate body directly
    // Skip epilogue generation
    // User must handle everything
}
```

### Codegen for interrupt

```asm
# Interrupt prologue (save all registers)
push %rax
push %rcx
push %rdx
... (all volatile registers)

# Body

# Interrupt epilogue
pop %rdx
pop %rcx
pop %rax
iretq
```

## Questions to resolve

1. **Which conventions matter?** Survey actual use cases. Naked and interrupt cover OS dev. What else?

2. **LLVM backend help?** LLVM knows all calling conventions. We could emit `define void @foo() #naked` and let LLVM handle it.

3. **Variadic functions?** Currently `open()` is special-cased. Need general variadic support for full C capture.

4. **Struct passing?** C ABI has rules about when structs go in registers vs memory. Lang punts (always pointer). For full capture, need proper ABI-compliant struct passing.

## Summary

"Fully capturing Zig" means:

1. Parse Zig source (write a Zig reader)
2. Emit lang AST
3. Compile with lang kernel

The main blocker is calling conventions. Lang has one implicit convention. Zig has many explicit ones.

**Practical path:**
- Start with C-convention Zig (most code)
- Add `callconv` AST node for explicit conventions
- Implement naked/interrupt for OS dev use cases
- Accept that Go-style runtimes need their own scheduler

The line is: **anything that compiles to standard stack frames with C-like semantics can be captured.** Languages requiring runtime cooperation (Go's goroutines, Erlang's processes) need more than AST translation.
