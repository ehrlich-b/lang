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

### The Key Insight: Self-Aware Kernel

The kernel carries its own AST as a string constant:

```lang
// In kernel source:
var self_kernel *u8 = _;                    // Placeholder, filled at bootstrap
var embedded_readers []*u8 = [];            // Reader AST strings
var embedded_reader_names []*u8 = [];       // Reader names
```

**Critical detail:** `self_kernel` contains AST where `self_kernel = _` (placeholder).
Every operation must re-poke the complete AST back into self_kernel!

### The Two Operations

Both are **pure AST manipulation + compile**:

#### `--embed-self kernel.ast` (Bootstrap, one-time)

Creates a self-aware kernel from a naive one:

```
1. Read kernel.ast file (contains self_kernel = _)
2. Stringify entire kernel.ast
3. Parse kernel.ast to AST nodes
4. Find self_kernel variable, replace _ with stringified AST
5. Compile modified AST → kernel binary
```

Result: kernel binary that contains its own AST in self_kernel.

#### `-r name reader.ast` (Normal operation)

Adds a reader to the kernel:

```
1. Parse self_kernel → get AST (contains self_kernel = _)
2. Find embedded_readers array, append reader.ast content
3. Find embedded_reader_names array, append "name"
4. Re-stringify the ENTIRE modified AST
5. Poke that back into self_kernel  ← CRITICAL!
6. Compile modified AST → new kernel binary
```

Result: new kernel with:
- The new reader in embedded_readers
- Complete self-knowledge (including the new reader) in self_kernel
- Can do more `-r` operations itself!

**It's a self-replicating quine with cargo.**

### Bootstrap Chain

```bash
# Step 1: Compile naive kernel (no self-awareness)
lang_trusted kernel.lang -o kernel_naive

# Step 2: Emit kernel AST
lang_trusted --emit-ast kernel.lang -o kernel.ast

# Step 3: Create self-aware kernel (THE one-time bootstrap step)
kernel_naive --embed-self kernel.ast -o kernel

# Step 4: Add lang reader
kernel -r lang lang_reader.ast -o lang1

# lang1 now has:
#   - lang reader in embedded_readers
#   - complete AST (with lang reader) in self_kernel
#   - can do: lang1 -r lisp lisp_reader.ast -o lang1_lisp
```

### Why This Works

Both operations are the same pattern:
1. Parse self_kernel (or file for --embed-self)
2. Walk AST, find target (variable or array)
3. Modify (replace or append)
4. Re-poke complete AST into self_kernel
5. Compile

The kernel already knows:
- AST parsing ✓
- AST walking ✓
- Compilation ✓

We just need:
- Find variable/array by name in AST
- Replace initializer / append to array
- Stringify AST back to text

### Runtime: find_reader()

At runtime, `find_reader("lang")`:
1. Scan `embedded_reader_names` for "lang"
2. Get corresponding entry from `embedded_readers`
3. Compile that AST on-demand → reader function
4. Cache and return

No changes to the fundamental resolution model.

### What Needs to Be Built

1. **`--emit-ast` flag** - output parsed AST as S-expressions
2. **`--embed-self` mode** - the one-time bootstrap operation
3. **`-r` mode** - add reader to kernel (AST manipulation)
4. **AST helpers**:
   - `find_var_in_ast(ast, name)` - find variable declaration
   - `find_array_in_ast(ast, name)` - find array declaration
   - `replace_initializer(var_decl, new_value)` - modify variable
   - `append_to_array(array_decl, value)` - add array element
   - `stringify_ast(ast)` - convert AST back to S-expression text
5. **Bootstrap update** - run --embed-self to create self-aware kernel

## Related Files

- `src/kernel_main.lang` - add self_kernel, embedded_readers, --embed-self, -r modes
- `src/ast.lang` - add AST manipulation helpers (find_var, replace_init, stringify)
- `src/main.lang` - add --emit-ast flag
- `bootstrap/` - will store kernel.ast (for initial --embed-self)

## Bootstrap Structure (New)

```
bootstrap/current/
  compiler_linux.ll     # Root of trust (LLVM IR)
  compiler_macos.ll     # Root of trust (LLVM IR)
  kernel.ast            # Kernel AST (for --embed-self bootstrap)
  lang_reader.ast       # Lang reader AST (renamed from lang_reader/source.ast)
```

After bootstrap, the kernel binary is self-contained (carries self_kernel).
The .ast files are only needed for the initial --embed-self step.

## Decisions Made

| Question | Decision | Rationale |
|----------|----------|-----------|
| Store source or AST? | **AST** | Consistent with reader resolution model |
| Compile reader at compose time or use time? | **Use time** | Simpler, AST is portable |
| Where does kernel AST live? | **In itself** | `self_kernel` variable - self-aware kernel |
| How to embed readers? | **AST arrays** | `embedded_readers[]` modified via AST manipulation |
| How does kernel know itself? | **Quine pattern** | self_kernel contains AST with placeholder, re-poked on each -r |

## Non-Goals

- Runtime reader compilation from source strings (that was the old broken approach)
- Standalone.lang (deprecated, will be removed)
- Generating .lang source as intermediate step
