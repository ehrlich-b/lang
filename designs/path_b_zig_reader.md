# Path B: Capturing a Zig Reader

## The Goal

`./out/lang -r zig_reader hello.zig -o hello && ./hello` prints "Hello, World!"

Where `zig_reader` is a captured Zig program — compiled by the patched Zig, through our emitter, through the lang kernel, into a native binary. A Zig program running on the lang runtime that reads Zig source and emits lang AST.

## Base Camp (Current State — Feb 2025)

**What works end-to-end:**
```
test.zig → patched Zig → lang AST → kernel → LLVM IR → clang → binary
```

Proven with `factorial(5)` → exit 120. The pipeline handles:
- Functions with parameters and return types
- Variables, assignments
- While loops (Zig's `loop + cond_br + br` pattern → `while + break`)
- If/else
- Arithmetic (+, -, *, /, %, bitwise, comparisons, unsigned variants)
- Function calls
- Nested blocks
- Type casts and bitcasts
- Struct field access (`field`, `field_ptr`)

**Emitter coverage:** 35/204 AIR tags handled (the important 35).

**Key files:**
- `patches/zig/src/codegen/lang_ast.zig` — the emitter (~630 lines)
- `src/codegen_llvm.lang` — kernel LLVM backend
- `src/sexpr_reader.lang` — kernel AST parser
- `src/kernel_main.lang` — kernel entry point (now with LLVM backend)

**Patched Zig build:** `/tmp/lang-patches-zig-63337/`

**To reproduce base camp from scratch:**
```bash
# 1. Apply patches to Zig 0.15.2
./scripts/apply-patches.sh

# 2. Build patched Zig (from the work dir printed by apply-patches.sh)
cd /tmp/lang-patches-zig-NNNNN && zig build -Doptimize=ReleaseFast

# 3. Compile test through pipeline
LANG_AST=1 /tmp/lang-patches-zig-NNNNN/zig-out/bin/zig build-obj test.zig -ofmt=c -target aarch64-macos -femit-bin=/tmp/test.c -OReleaseFast
# Extract S-expressions from .c output, wrap in (program ...), save as test.ast
LANGBE=llvm LANGOS=macos /tmp/kernel_fresh test.ast -o test.ll
clang -O2 test.ll -o test && ./test

# 4. Build a fresh kernel with LLVM support
LANGBE=llvm LANGOS=macos ./out/lang std/core.lang src/version_info.lang src/lexer.lang src/parser.lang src/codegen.lang src/codegen_llvm.lang src/ast_emit.lang src/sexpr_reader.lang src/kernel_main.lang -o /tmp/kernel_fresh.ll
clang -O2 /tmp/kernel_fresh.ll -o /tmp/kernel_fresh
```

## Empirical Gap Analysis

Tested with `-OReleaseFast` to eliminate safety-check noise:

### Structs — CLOSE
```zig
const Point = struct { x: i64, y: i64 };
export fn f(ax: i64, ay: i64) i64 {
    const p = Point{ .x = ax, .y = ay };
    return p.x +% p.y;
}
```
**Missing:** `aggregate_init` (struct literal construction). Field ACCESS works (`field`/`field_ptr` already handled).

### Enum + Switch — NEEDS WORK
```zig
const Op = enum(i64) { add, sub, mul };
export fn calc(op: i64, a: i64, b: i64) i64 {
    return switch (@as(Op, @enumFromInt(op))) { .add => a+%b, .sub => a-%b, .mul => a*%b };
}
```
**Missing:** `switch_br` (the entire switch dispatch). Can lower to if-else chain in emitter.

### String Literals — NEEDS WORK
```zig
extern fn write(fd: c_int, buf: [*]const u8, count: usize) isize;
export fn hello() i64 {
    const msg = "Hello, World!\n";
    _ = write(1, msg.ptr, msg.len);
    return 0;
}
```
**Missing:** String pointer emits as `nil`. The emitter's `resolve_const` handles `.ptr` as `"nil"`. Need to emit global constant data and reference it. Length works (comptime-folded to `(number 14)`).

### Comptime Folding — FREE
```zig
export fn first_char() i64 {
    const msg: [*]const u8 = "Hello";
    return msg[0];  // folded to (number 72) at compile time
}
```
Zig aggressively folds comptime-known expressions. Simple string indexing disappears entirely.

## The Route

### Camp 1: aggregate_init (struct construction)
**What:** Handle `aggregate_init` AIR instruction — constructs a struct from field values.
**Why:** Every struct-using Zig program needs this.
**Emit as:** Sequence of `field_ptr` stores, or a new `(struct_init ...)` AST node.
**Risk:** Low. The data is straightforward — a list of field values.

### Camp 2: switch_br (switch dispatch)
**What:** Handle `switch_br` AIR instruction — multi-way branch on integer value.
**Why:** Zig enums use switch. The tokenizer IS a giant switch. This is the single most important missing feature for Path B.
**Emit as:** Chain of `(if (binop == val case0) (block ...) (if (binop == val case1) (block ...) ...))`. O(n) but correct.
**Risk:** Medium. The `switch_br` instruction has complex payload encoding (case ranges, else branch). Need to study the AIR extra data format carefully.

### Camp 3: String literal constants
**What:** Emit string data as global constants, resolve string pointers to those globals.
**Why:** Any program that does I/O needs strings.
**Emit as:** `(global msg_0 (type_base *u8) "Hello, World!\n")` or similar. Kernel needs to handle global string data in LLVM IR emission.
**Risk:** Medium. Two changes needed: emitter (resolve `.ptr` on string constants) AND kernel (emit global constant data). The kernel currently doesn't have global string literals.

### Camp 4: Extraction script
**What:** Script to extract S-expressions from `-ofmt=c` output, wrap in `(program ...)`, filter out C noise.
**Why:** Currently manual. Needs to be automated for any real workflow.
**Risk:** Low. Just text processing.

### Camp 5: Capture a self-contained Zig program
**What:** Write a non-trivial Zig program using structs + switch + strings (NO std imports, just extern C), capture it end-to-end.
**Why:** Proves we can capture real Zig beyond factorial. This is the first program where captured Zig does something useful.
**Risk:** Low if camps 1-4 are solid.

### Camp 6: Zig reader (the summit for MVP)
**What:** Write `zig_reader.zig` — a Zig program that tokenizes+parses a tiny Zig subset and emits lang AST S-expressions. Capture it and use as a reader.
**Why:** This IS the goal. A captured Zig program that compiles other Zig programs.
**Emit:** Reads `.zig` from argv, writes AST S-expressions to output file.
**Risk:** Medium. The reader itself needs to work correctly AND be capturable. Two things that can go wrong.

### Camp 7 (stretch): Capture std.zig.Tokenizer
**What:** Import Zig's actual tokenizer from the standard library, capture the monomorphized result.
**Why:** Proves we can capture real Zig standard library code, not just hand-written programs.
**Risk:** High. Pulls in allocators, MultiArrayList, hash maps. Each is a wave of new AIR patterns. This is where the long tail lives.

## MVP Definition

**The MVP is Camp 6.** A self-contained Zig reader (no std imports) that:
1. Reads a `.zig` file using `extern fn read(...)`
2. Tokenizes a subset: `fn`, `return`, `var`, `const`, `while`, `if`, `else`, integers, `+`, `-`, `*`, identifiers, `(`, `)`, `{`, `}`, `;`
3. Parses into lang AST S-expressions
4. Writes output using `extern fn write(...)`
5. Is itself captured through the pipeline and runs on the lang kernel

This requires camps 1-5 to be complete. It does NOT require camp 7 (std.zig).

## What Could Kill Us

1. **AIR instruction we can't decode.** The `switch_br` payload is complex. If we can't parse it correctly, we're stuck. Mitigation: study Zig's own C backend for reference (`c.zig` handles all these cases).

2. **Kernel can't handle a pattern the emitter produces.** New AST nodes might need kernel support. Mitigation: keep the emitter output within the kernel's existing AST vocabulary where possible.

3. **Global data / string constants.** This is new territory for both emitter and kernel. If the kernel's LLVM emission can't handle global constants, we need to add that. Mitigation: LLVM IR global constants are well-understood, just need to wire it up.

4. **The reader is too big to capture.** If the reader uses Zig features we haven't handled, it won't capture. Mitigation: keep the reader minimal — no std imports, no generics, no error unions. Pure C-interop Zig.

## Fallback Plan (Path A — the bunny slope)

If Path B stalls at any camp, we can write the Zig reader in lang directly (`src/zig_reader.lang`). This:
- Doesn't require capture at all
- Uses lang's existing parser infrastructure as a template
- Still enables `./out/lang -r zig_reader hello.zig`
- Doesn't prove the capture thesis, but delivers the UX

Path A is always available as an escape hatch. Camps 1-4 are valuable regardless (they improve the emitter for future capture work).

## Compilation Flags

Always use `-OReleaseFast` for capture. Debug mode pulls in the entire panic/debug/stack-trace infrastructure through safety checks, adding hundreds of functions we don't need. ReleaseFast gives us just the user code.

Target: `-target aarch64-macos` (for local testing) or `-target x86_64-linux` (for CI).
