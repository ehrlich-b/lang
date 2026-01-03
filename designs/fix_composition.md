# Fix Composition (compose command)

## Status: BLOCKED (2025-01-03)

Composition works for small readers but **blocked on architecture issues** for the full use case.

### Blockers

| Blocker | Design Doc | Description |
|---------|------------|-------------|
| Kernel/Reader Split | `designs/kernel_reader_split.md` | Kernel includes lexer/parser, should be AST-only |
| Composition Dependencies | `designs/composition_dependencies.md` | Shared includes cause duplicates across composed ASTs |

These must be resolved before full composition (kernel + lang_reader + other readers) can work.

### Completed Work

1. ✅ **Function name mismatch**: Fixed - `-r` mode now pokes `lang` (not `reader_lang`)
2. ✅ **Embedded readers not invoked**: Fixed - code now checks for embedded function first
3. ✅ **Limits increased**: LIMIT_TOP_DECLS=4000, LIMIT_FUNCS=3000, etc.
4. ✅ **Bootstrap with new limits**: 169/169 tests pass

### What Works Now

Small reader composition works! See "Testing (Verified)" section below for the `#answer{}` example.

## The Design (How It Works)

### Core Insight: Pure AST Manipulation

Composition is ALL AST manipulation. No lang parsing. No source code. Just:
1. Read AST (S-expressions)
2. Combine AST nodes
3. Poke values into AST nodes
4. Re-serialize AST
5. Generate code from AST

### Data Structures

```lang
// In codegen.lang - these get poked by -r mode
var self_kernel *u8 = "";                    // Full program AST (quine)
var embedded_reader_names [1024]*u8 = [];    // ["lang", "lisp", nil, ...]
var embedded_reader_funcs [1024]*u8 = [];    // [lang, lisp, nil, ...]
// Nil-terminated, no count needed
```

### The Three Phases

```
Phase 1: Build composed compiler
──────────────────────────────────────────────────────────────
  kernel_self -r lang lang_reader.ast -o lang1

  This is BUILD TIME for lang1.
  kernel_self is RUNNING.

Phase 2: Composed compiler compiles user code
──────────────────────────────────────────────────────────────
  lang1 user.lang -o user

  This is lang1's RUNTIME = user code's COMPILE TIME.
  When lang1 hits #lang{...}, it must INVOKE the embedded reader.
  The reader function EXISTS inside lang1's binary.
  lang1 should CALL this function, not spawn a subprocess.

Phase 3: User program runs
──────────────────────────────────────────────────────────────
  ./user

  This is user code's RUNTIME.
```

### What Readers Are

Readers are functions that transform strings to AST:

```lang
reader lang(text *u8) *u8 {
    // Parse text, return S-expression AST string
    return ast_emit_program(parse_program());
}
```

**Signature**: `func name(text *u8) *u8`
- Takes: input text string
- Returns: S-expression AST string (e.g., `"(number 42)"`)

When you declare a reader, TWO things happen:
1. `compile_reader_to_executable()` creates external binary for compile-time use
2. `llvm_emit_reader()` emits the reader AS A FUNCTION `@name` in output binary

The function exists so composed compilers can invoke readers at their runtime.

## The Two Bugs (Fixed)

### Bug 1: Function Name Mismatch ✅

**Location**: `src/main.lang:862-865`

**Was**: `-r` mode built `reader_lang` but function emitted as `@lang`.
**Fix**: Use reader name directly without prefix.

### Bug 2: Embedded Readers Not Invoked ✅

**Locations**: `src/codegen.lang` at lines 1725, 3598, 5227

**Was**: Code always used `exec_capture()` even when embedded reader exists.
**Fix**: Check `find_embedded_reader_func()` first, call via function pointer:

```lang
var embedded_func *u8 = find_embedded_reader_func(name, name_len);
if embedded_func != nil {
    var reader_fn fn(*u8) *u8 = embedded_func;
    output = reader_fn(content);
} else {
    // ... exec_capture fallback ...
}
```

## What's Working

| Component | Status |
|-----------|--------|
| Array infrastructure (`embedded_reader_names/funcs`) | ✅ |
| `-r` mode AST combination | ✅ |
| `-r` mode array poking | ✅ |
| `--embed-self` mode | ✅ |
| `llvm_emit_reader()` emits function | ✅ |
| `find_embedded_reader_func()` lookup | ✅ |
| Embedded reader invocation via fn pointer | ✅ |
| `is_ast` flag to skip external compilation | ✅ |
| 169/169 LLVM tests | ✅ |

## Files Modified

1. **`src/main.lang:862-865`** - Use reader name directly (no prefix)
2. **`src/codegen.lang:1725`** - Embedded reader invocation (x86 first pass)
3. **`src/codegen.lang:3598`** - Embedded reader invocation (x86 gen_expr)
4. **`src/codegen.lang:5227`** - Embedded reader invocation (LLVM backend)

## Testing (Verified)

```bash
# Build and test - all 169 tests pass
make build
LANGOS=macos COMPILER=./out/lang_next ./test/run_llvm_suite.sh  # 169/169

# Create full compiler AST and self-aware kernel
LANGBE=llvm LANGOS=macos ./out/lang_next --emit-expanded-ast \
    std/core.lang src/*.lang -o /tmp/compose_test/full_compiler.ast
LANGBE=llvm LANGOS=macos ./out/lang_next /tmp/compose_test/full_compiler.ast \
    --embed-self -o /tmp/compose_test/kernel_self.ll
clang -O2 /tmp/compose_test/kernel_self.ll -o /tmp/compose_test/kernel_self

# Add tiny reader (tests pass)
LANGBE=llvm LANGOS=macos /tmp/compose_test/kernel_self \
    -r answer tiny_reader.ast -o /tmp/compose_test/composed.ll
clang -O2 /tmp/compose_test/composed.ll -o /tmp/compose_test/composed

# Verify embedded reader is invoked correctly
echo 'func main() i64 { return #answer{ignored}; }' > /tmp/test.lang
/tmp/compose_test/composed /tmp/test.lang -o /tmp/test.ll
clang /tmp/test.ll -o /tmp/test && /tmp/test  # Returns 42!
```

## Root Cause Found (2025-01-03)

The crash was NOT a buffer issue - it was **limit overflow**:
- `LIMIT_TOP_DECLS = 1000` but full_compiler.ast has **1135 declarations**
- `LIMIT_FUNCS = 1000` but combined kernel + lang_reader has ~1849 declarations
- Heap corruption occurs when writing past allocated arrays

**Fix Applied** in `src/limits.lang`:
- `LIMIT_TOP_DECLS`: 1000 → 4000
- `LIMIT_FUNCS`: 1000 → 3000
- `LIMIT_GLOBALS`: 1000 → 2000
- `LIMIT_STRINGS`: 3000 → 6000
- `LIMIT_STRUCTS`: 100 → 200

**MUST RUN `make bootstrap`** to bake new limits into bootstrap compiler.

## Acceptance Criteria

The composition feature is complete when:

```bash
# 1. Build self-aware kernel from compiler
LANGBE=llvm LANGOS=macos ./out/lang --emit-expanded-ast \
    std/core.lang src/*.lang -o /tmp/full_compiler.ast
LANGBE=llvm LANGOS=macos ./out/lang /tmp/full_compiler.ast \
    --embed-self -o /tmp/kernel_self.ll
clang -O2 /tmp/kernel_self.ll -o /tmp/kernel_self

# 2. Add lang reader
LANGBE=llvm LANGOS=macos ./out/lang --emit-expanded-ast \
    src/lang_reader.lang -o /tmp/lang_reader.ast
LANGBE=llvm LANGOS=macos /tmp/kernel_self \
    -r lang /tmp/lang_reader.ast -o /tmp/lang1.ll
clang -O2 /tmp/lang1.ll -o /tmp/lang1

# 3. Add minilisp reader (can be trivial)
# Create simple lisp reader that returns (number 42) for any input
LANGBE=llvm LANGOS=macos /tmp/lang1 \
    -r lisp /tmp/lisp_reader.ast -o /tmp/lang2.ll
clang -O2 /tmp/lang2.ll -o /tmp/lang2

# 4. Compose program using both readers
cat > /tmp/hello.lang << 'EOF'
func get_hello() *u8 { return "hello "; }
func main() i64 {
    print(get_hello());
    print(#lisp{world});  // lisp reader provides "world\n"
    return 0;
}
EOF
/tmp/lang2 /tmp/hello.lang -o /tmp/hello.ll
clang /tmp/hello.ll -o /tmp/hello
/tmp/hello  # Prints "hello world"
```

## Next Steps

1. Resolve blocker: Kernel/Reader Split (`designs/kernel_reader_split.md`)
2. Resolve blocker: Composition Dependencies (`designs/composition_dependencies.md`)
3. Retry full composition test with acceptance criteria above
