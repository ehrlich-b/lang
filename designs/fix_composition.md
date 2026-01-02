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

## Implementation: The "How" (TBD)

### Key Questions

1. **How does codegen emit embedded AST data?**
   - x86: `.section .rodata` with `.ascii` directives
   - LLVM: `@name = private constant [N x i8] c"..."`

2. **How does find_reader() locate embedded data?**
   - Global symbol `_embedded_reader_table`
   - Scanned at first reader lookup (lazy init)

3. **How does kernel access its own AST for self-composition?**
   - External file (bootstrap/kernel.ast)
   - Or embedded in kernel binary

4. **What's the exact compose command flow?**
   - Parse reader sources → reader AST
   - Load kernel AST
   - Combine: kernel AST + reader AST (+ entry point)
   - Generate combined binary

### Partial Implementation (Current State)

The following exists but needs updating:

```lang
// codegen.lang - runtime registry (for CLI readers)
var cg_embedded_readers *u8 = nil;
var cg_embedded_reader_count i64 = 0;

func add_embedded_reader(name, name_len, ast, ast_len) void { ... }
func find_embedded_reader(name, name_len) *u8 { ... }
```

This is runtime-only. For composition, we need codegen to **emit** this data.

### What Needs to Be Built

1. **Codegen support for emitting embedded data**
   - `emit_embedded_reader(name, ast)` - adds to output binary
   - Emit `_embedded_reader_table` symbol

2. **find_reader() checks embedded table**
   - On first call, scan `_embedded_reader_table`
   - Populate `cg_embedded_readers` from binary data

3. **Compose command**
   - Parse reader sources → AST
   - Load kernel AST (from file or embedded)
   - Call codegen with: kernel AST + reader ASTs
   - Output: new binary with readers embedded

4. **Bootstrap restructure**
   - Add `kernel.ast` to bootstrap
   - Separate kernel from lang_reader cleanly

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
| Where does kernel AST live? | **TBD** | Bootstrap file or embedded |

## Non-Goals

- Runtime reader compilation from source strings (that was the old broken approach)
- Standalone.lang (deprecated, will be removed)
- Generating .lang source as intermediate step
