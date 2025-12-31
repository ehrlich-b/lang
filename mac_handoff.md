# Mac Development Handoff

Temporary doc for bootstrapping on Mac. Delete after successful setup.

## Quick Start

```bash
# 1. Compile the libc-based LLVM IR with clang
clang -target arm64-apple-macos bootstrap/llvm_libc_compiler.ll -o lang

# 2. Test basic compilation
./lang test/suite/002_return_42.lang -o test.s
# Expected: "Wrote test.s" (x86 asm - won't run on ARM Mac but proves compiler works)

# 3. Test LLVM backend
LANGBE=llvm ./lang test/suite/002_return_42.lang -o test.ll
clang test.ll -o test
./test; echo "Exit: $?"
# Expected: Exit: 42
```

## If Target Triple Errors

The LLVM IR has `target triple = "x86_64-unknown-linux-gnu"`. Fix with:

```bash
# Option 1: Override with clang flag
clang -target arm64-apple-macos bootstrap/llvm_libc_compiler.ll -o lang

# Option 2: Edit the file
sed -i '' 's/x86_64-unknown-linux-gnu/arm64-apple-macos/' bootstrap/llvm_libc_compiler.ll
clang bootstrap/llvm_libc_compiler.ll -o lang
```

## Full Bootstrap on Mac

Once basic compilation works:

```bash
# Switch to libc layer for Mac-compatible output
LANGLIBC=libc make generate-os-layer

# Compile the compiler with LLVM backend
LANGBE=llvm ./lang std/core.lang src/lexer.lang src/parser.lang \
  src/codegen.lang src/codegen_llvm.lang src/ast_emit.lang \
  src/sexpr_reader.lang src/main.lang -o mac_compiler.ll

# Build native Mac binary
clang mac_compiler.ll -o lang_mac

# Verify it works
LANGBE=llvm ./lang_mac test/suite/002_return_42.lang -o test.ll
clang test.ll -o test && ./test
```

## Known Issues

1. **mmap flags**: macOS uses different flags (MAP_ANON = 0x1000 vs Linux 0x20). The libc.lang layer calls libc's mmap which handles this.

2. **x86 backend output**: The x86 backend generates Linux assembly. It compiles but won't run on Mac. Use LLVM backend for runnable binaries.

3. **Entry point**: LLVM IR declares `@main`. clang links against libc which provides `_start` → `main`.

## What's in bootstrap/llvm_libc_compiler.ll

- Full compiler with both x86 and LLVM backends
- Uses libc externals: `@read`, `@write`, `@malloc`, `@open`, `@close`, etc.
- ~57K lines of LLVM IR
- Has `init_environ` support for `LANGBE=llvm` detection

## Recent Commits

- `246b9db` - Add LLVM libc-based compiler for cross-platform bootstrap
- `5e4ebd1` - Enable init_environ in normal mode for LANGBE detection
- `e058042` - Fix LLVM bootstrap: string escapes and global type registration
