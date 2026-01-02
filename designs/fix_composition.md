# Fix Composition (compose command)

## Status: Design Finalized, Implementation TBD

## The Architecture

### Core Components

```
Kernel = AST parser + codegen
         ONLY understands: S-expression AST → platform code

Reader = text → AST transformer
         DEFINED as AST (S-expressions)
         COMPILED to platform code when needed

Compiler = Kernel + Reader(s)
         e.g., lang compiler = kernel + lang_reader
```

### The Fundamental Principle

**Readers always resolve to AST.** Regardless of where a reader comes from, the flow is:

| Source | Flow |
|--------|------|
| Embedded in binary | load AST from data section → compile → function |
| CLI `-r reader.lang` | parse source → AST → compile → function |
| Cache `.lang-cache/` | load AST from file → compile → function |

This is the key insight: **composition just means storing AST in the binary's data section**.

The runtime behavior is identical regardless of source. `find_reader()` returns AST, which gets compiled to a function pointer.

## Reader Resolution Flow

### Example: Compiling a .lisp file

```
./lang1 lisp_reader.lang prog.lisp

1. lang1 sees prog.lisp, needs "lisp" reader
2. find_reader("lisp"):
   a. Check embedded AST in binary → miss
   b. Check CLI-provided readers → found lisp_reader.lang
   c. Parse lisp_reader.lang using lang reader → lisp_reader.ast
3. Compile lisp_reader.ast → reader function (platform code, in memory)
4. Call reader function on prog.lisp → prog.ast
5. Compile prog.ast → output
```

### With Composed Binary

```
./lang1_lisp prog.lisp

1. lang1_lisp sees prog.lisp, needs "lisp" reader
2. find_reader("lisp"):
   a. Check embedded AST in binary → HIT! Returns lisp.ast
3. Compile lisp.ast → reader function
4. Call reader function on prog.lisp → prog.ast
5. Compile prog.ast → output
```

Same flow, different AST source.

## The Two Flags: -r and -c

### -r (raw/reader): Embed AST directly

```bash
kernel -r lisp lisp_reader.ast -o kernel_lisp
```

- Takes **AST** (S-expressions)
- Kernel needs ZERO syntax knowledge
- Just: "embed this AST with this name"
- **The primitive operation**

### -c (compile): Compile source, then embed AST

```bash
lang -c lisp lisp_reader.lang -o lang_lisp
```

- Takes **source code** (in whatever syntax the compiler knows)
- Uses existing reader to parse source → AST
- Then embeds that AST (equivalent to -r)
- **Sugar on top of -r**

### The Relationship

```
-c lisp reader.lang  =  [parse reader.lang → AST]  +  [-r lisp AST]
```

### Language Forgetting

The syntax used to DEFINE a reader doesn't have to match the syntax it PARSES:

```bash
# Start with bare kernel (only knows AST)
kernel -r lisp lisp_reader.ast -o kernel_lisp

# Define lang's syntax... in lisp!
# lang_reader.lisp: lang syntax defined using lisp

kernel_lisp -c lang lang_reader.lisp -o kernel_lang

# Result: kernel_lang knows lang syntax
# But lang was DEFINED in lisp
# The final binary has "forgotten" lisp entirely
```

This enables the vision: define any syntax using any other syntax.

## Composition: The "What"

### Commands

```bash
# Primitive (AST only):
kernel -r lisp lisp.ast -o kernel_lisp

# Convenience (compile first):
lang compose -c lisp lisp_reader.lang -o lang_lisp
```

### What It Produces

A new compiler binary containing:
1. All of the original compiler's code
2. Embedded AST for each composed reader
3. Registration data: `"lisp" → pointer to embedded AST`

### Data Layout (Conceptual)

```
Binary:
  .text
    [kernel code]
    [find_reader code - checks embedded AST table]

  .rodata
    _embedded_lisp_ast:      "(program (reader lisp ..."
    _embedded_lisp_name:     "lisp"
    _embedded_reader_table:
      entry[0]: { name_ptr, name_len, ast_ptr, ast_len }
      ...
```

### The Kernel's Role

The kernel must be able to:
1. **Read AST** (S-expressions) - already has this
2. **Compile AST → platform code** - already has this
3. **Embed AST data in output binary** - for composition
4. **Access its own AST** - for self-composition

### Kernel Self-Knowledge

For `compose` to produce a complete compiler, the kernel needs access to its own AST. Options:

1. **Kernel AST stored in bootstrap** - `bootstrap/kernel.ast`
2. **Kernel AST embedded in kernel binary** - self-contained
3. **Explicit flag** - `--kernel-ast path`

## Bootstrap Chain

```
bootstrap/
  kernel.ll              # Kernel binary (LLVM IR) - root of trust
  kernel.ast             # Kernel's own AST (for self-composition)
  lang_reader/
    source.ast           # Lang reader as AST

# Bootstrap process:
clang kernel.ll -o kernel

# Build lang compiler (option A - runtime reader):
kernel lang_reader.ast program.ast -o program

# Build lang compiler (option B - compose):
kernel compose -r lang lang_reader.ast -o lang1
# Now lang1 has lang reader baked in
```

## Implementation: The "How"

### The Key Insight

**Kernel must know its own AST.** When composing, the kernel:

1. Reads its own AST (from bootstrap file)
2. Adds reader data declarations to it
3. Generates combined binary

This is the core mechanism: **AST-level combination with reader data as string constants**.

### What Compose Generates

The output binary contains reader AST as **string constants** in .rodata:

```
.rodata
  _reader_lang_ast:  "(program (reader lang ...))"   ; Full AST as string
  _reader_lang_name: "lang"
```

At runtime, `find_reader()` finds this string and compiles it on-demand.

### Implementation Strategy: Init Function

Instead of modifying codegen to emit special table structures, compose **generates a normal init function**:

```lang
// Generated by compose command
var _reader_lang_name *u8 = "lang";
var _reader_lang_ast *u8 = "(program (reader lang ...full AST...))";

func __init_embedded_readers() void {
    add_embedded_reader(_reader_lang_name, 4, _reader_lang_ast, <ast_len>);
}
```

Then `find_reader()` calls `__init_embedded_readers()` on first use (lazy init).

**Why this works:**
- Uses existing codegen (strings, function calls)
- No special binary format needed
- Reader AST stored as escaped string constant

### Compose Flow (Detailed)

```
kernel compose -r lang lang_reader.ast -o lang1

1. Load kernel.ast from bootstrap/current/kernel.ast
2. Load lang_reader.ast from command line
3. Generate init function AST:
   - var _reader_lang_name = "lang"
   - var _reader_lang_ast = "<escaped AST string>"
   - func __init_embedded_readers() { add_embedded_reader(...) }
4. Combine: kernel.ast + init_function.ast
5. Generate to output
```

### find_reader() Update

```lang
var _embedded_readers_initialized i64 = 0;

func find_reader(name *u8, name_len i64) *u8 {
    // Lazy init: call generated __init_embedded_readers() if exists
    if _embedded_readers_initialized == 0 {
        _embedded_readers_initialized = 1;
        // Call weak symbol (no-op if not linked)
        __init_embedded_readers();
    }

    // Then check registered, embedded, cache as before
    ...
}
```

### Bootstrap Restructure

**Current structure:**
```
bootstrap/current/
  compiler_linux.ll    # Full compiler (LLVM IR)
  compiler_macos.ll    # Full compiler (LLVM IR)
  lang_reader/source.ast
```

**New structure:**
```
bootstrap/current/
  kernel.ast           # Kernel AST (parser + codegen + main)
  lang_reader.ast      # Lang reader AST
  compiler_linux.ll    # Still needed as root of trust
  compiler_macos.ll
```

### Generating kernel.ast

How do we get kernel.ast into bootstrap?

**Option 1: Compiler flag `--emit-ast`**
```bash
./lang --emit-ast src/kernel_main.lang -o kernel.ast
```
Outputs the parsed AST (after reader processing) as S-expressions.

**Option 2: Bootstrapped from current**
The current compiler can emit its own AST when given the right flag.

### String Escaping

Reader AST can be megabytes. Need to escape for string literals:
- `"` → `\"`
- `\` → `\\`
- Newlines → `\n`
- Control chars → `\xNN`

The compose command handles this when generating the init function.

### Partial Implementation (Current State)

The following exists in codegen.lang (runtime registry):

```lang
var cg_embedded_readers *u8 = nil;
var cg_embedded_reader_count i64 = 0;

func add_embedded_reader(name, name_len, ast, ast_len) void { ... }
func find_embedded_reader(name, name_len) *u8 { ... }
```

This already works for the runtime part. We just need:
1. `__init_embedded_readers()` stub (weak symbol) in kernel
2. Compose command that generates real `__init_embedded_readers()`
3. `kernel.ast` in bootstrap

### What Needs to Be Built

1. **`--emit-ast` flag** to output AST as S-expressions
2. **Compose command** that generates init function AST
3. **Weak symbol** for `__init_embedded_readers()` in kernel
4. **Bootstrap restructure** to include `kernel.ast`

## Related Files

- `src/codegen.lang` - needs embedded data emission
- `src/codegen_llvm.lang` - needs embedded data emission (LLVM)
- `src/kernel_main.lang` - existing compose logic (partial)
- `src/main.lang` - compose command entry point
- `bootstrap/` - needs kernel.ast

## Decisions Made

| Question | Decision | Rationale |
|----------|----------|-----------|
| Store source or AST? | **AST** | Consistent with reader resolution model |
| Compile reader at compose time or use time? | **Use time** | Simpler, AST is portable |
| Two-step or one-step compose? | **One-step** | Better UX, kernel handles everything |
| Where does kernel AST live? | **Bootstrap file** | `bootstrap/current/kernel.ast` - simpler than embedding |
| How to embed readers? | **Init function** | Generate AST for `__init_embedded_readers()` |

## Open Question: Weak Symbols

The init function approach requires a way to call `__init_embedded_readers()` when it exists, and no-op when it doesn't.

**Options:**

1. **Weak symbol** (platform-specific)
   - x86/ELF: `.weak __init_embedded_readers`
   - LLVM: `declare extern_weak void @__init_embedded_readers()`
   - Check for null before calling

2. **Function pointer indirection**
   - `var init_readers_fn *func() void = nil;`
   - Compose sets this to real function
   - find_reader() checks if non-nil before calling

3. **Always generate stub**
   - Kernel always has empty `__init_embedded_readers() {}`
   - Compose replaces it (multiple definitions)
   - Simpler but relies on linker behavior

**Recommendation:** Option 2 (function pointer) is most portable and explicit.

## Non-Goals

- Runtime reader compilation from source strings (that was the old broken approach)
- Standalone.lang (deprecated, will be removed)
- Generating .lang source as intermediate step
