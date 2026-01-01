# Building Lang

This guide covers building lang from source.

## Quick Start

### Linux (x86-64)

```bash
# First time setup
make init        # Initialize from bootstrap
make bootstrap   # Verify and build

# After that
make build       # Quick build without verification
```

### macOS (ARM64 or x86-64)

```bash
# First time setup
clang bootstrap/llvm_libc_macos.ll -o lang

# Verify it works
make llvm-verify
```

## Prerequisites

### Linux

Install build essentials:
```bash
# Debian/Ubuntu
sudo apt install build-essential

# Fedora
sudo dnf install gcc binutils make

# Arch
sudo pacman -S base-devel
```

### macOS

Install Xcode Command Line Tools:
```bash
xcode-select --install
```

## Build Commands

### Core Commands

| Command | Description |
|---------|-------------|
| `make init` | Initialize from bootstrap (first time only) |
| `make build` | Compile `src/*.lang` → `out/lang_next` |
| `make bootstrap` | Full verification + promotion |
| `make clean` | Remove build artifacts |
| `make distclean` | Remove everything in `out/` |

### Testing Commands

| Command | Description |
|---------|-------------|
| `make test-suite` | Run x86 test suite |
| `make test-run` | Run sample programs |
| `make test-all` | Run all tests |

### Development Commands

| Command | Description |
|---------|-------------|
| `make run FILE=path.lang` | Compile and run a file |
| `make dev-run FILE=path.lang` | Run with `lang_next` |
| `make dev-stdlib-run FILE=path.lang` | Run with stdlib + `lang_next` |

## Environment Variables

### LANGOS - Target Operating System

```bash
LANGOS=linux   # (default) Linux x86-64
LANGOS=macos   # macOS ARM64
```

### LANGBE - Backend

```bash
LANGBE=x86     # (default) x86-64 assembly output
LANGBE=llvm    # LLVM IR output
```

### LANGLIBC - C Library

```bash
LANGLIBC=none  # (default) Raw syscalls, no libc
LANGLIBC=libc  # Use system libc (required for LLVM)
```

### Examples

```bash
# Build for macOS with LLVM backend
LANGOS=macos LANGBE=llvm make build

# Run a test with LLVM backend
LANGBE=llvm make dev-run FILE=test/suite/181_hello.lang

# Build compiler using libc
LANGLIBC=libc make build
```

## Output Files

After building:

```
out/
├── lang -> lang_<commit>          # Active compiler symlink
├── lang_next -> lang_<commit>     # New compiler (pre-promotion)
├── lang_<commit>                  # Compiler binary
├── lang_<commit>.s                # Compiler assembly
├── lang_standalone                # Standalone compiler
├── llvm_libc_linux                # LLVM-based compiler (Linux)
└── ast/
    └── lang_reader_v1.ast         # Expanded reader AST
```

## Compilation Pipeline

### Default (x86)

```
.lang → lang → .s → as → .o → ld → binary
```

1. `lang` compiles `.lang` files to x86-64 assembly (`.s`)
2. `as` assembles to object file (`.o`)
3. `ld` links to executable

### LLVM Backend

```
.lang → lang → .ll → clang → binary
```

1. `lang` compiles `.lang` files to LLVM IR (`.ll`)
2. `clang` compiles and links to executable

## Directory Structure

```
language/
├── src/                    # Compiler source code
│   ├── lexer.lang         # Tokenizer
│   ├── parser.lang        # Parser + AST nodes
│   ├── codegen.lang       # x86-64 backend
│   ├── codegen_llvm.lang  # LLVM backend
│   ├── sexpr_reader.lang  # S-expression AST reader
│   ├── ast_emit.lang      # AST emitter
│   └── main.lang          # CLI driver
├── std/                    # Standard library
│   ├── core.lang          # Core utilities
│   ├── tok.lang           # Tokenizer for readers
│   └── os/                # OS abstraction layer
│       ├── linux_x86_64.lang
│       ├── macos_arm64.lang
│       ├── libc.lang
│       └── libc_macos.lang
├── test/                   # Test suite (167 tests)
│   ├── suite/             # Individual test files
│   ├── run_lang1_suite.sh # x86 test runner
│   └── run_llvm_suite.sh  # LLVM test runner
├── bootstrap/             # Bootstrap artifacts
│   ├── current/           # Active bootstrap (symlink)
│   ├── escape_hatch.s     # Emergency recovery
│   └── llvm_libc_macos.ll # macOS bootstrap
├── out/                   # Build output
└── docs/                  # Documentation
```

## Compiler Flags

```
lang [options] <files...> -o <output>

Options:
  -o <file>             Output file (required)
  -c <reader>           Compose with reader (creates standalone)
  --emit-ast            Emit AST instead of compiling
  --emit-expanded-ast   Emit fully expanded AST
```

### Examples

```bash
# Basic compilation
./out/lang test.lang -o test.s

# With standard library
./out/lang std/core.lang test.lang -o test.s

# Emit AST
./out/lang test.lang --emit-ast -o test.ast

# Create standalone compiler
./out/lang -c lang src/lang_reader.lang -o standalone.s
```

## Running Tests

### Full Test Suite (x86)

```bash
./test/run_lang1_suite.sh
```

Runs 167 tests, outputs:
```
Test 001_return_0... PASS
Test 002_return_42... PASS
...
167/167 tests passed
```

### Full Test Suite (LLVM)

```bash
./test/run_llvm_suite.sh
```

### Single Test

```bash
# With current compiler
make dev-stdlib-run FILE=test/suite/195_effect_in_loop.lang

# Check exit code
./out/test; echo "Exit: $?"
```

### Using a Specific Compiler

```bash
COMPILER=./out/lang_next ./test/run_lang1_suite.sh
```

## Troubleshooting

### "lang: command not found"

Run `make init` to initialize from bootstrap.

### "undefined reference to..."

Missing symbol. Make sure you include `std/core.lang` if using stdlib functions:
```bash
./out/lang std/core.lang myprogram.lang -o out.s
```

### Assembler errors

The generated assembly might have issues. Check:
```bash
# View generated assembly
cat out/myprogram.s

# Try assembling manually
as out/myprogram.s -o out/myprogram.o
```

### Linker errors

On Linux with raw syscalls, no libraries are needed. With libc:
```bash
# Manual linking with libc
clang out/myprogram.ll -o myprogram
```

### LLVM backend not working

Ensure you have clang installed:
```bash
clang --version
```

Generate LLVM IR and compile manually:
```bash
LANGBE=llvm ./out/lang std/core.lang myprogram.lang -o out/myprogram.ll
clang out/myprogram.ll -o myprogram
```

## Advanced: Manual Bootstrap Recovery

If something goes wrong with bootstrap:

### From x86 Assembly (Linux)

```bash
# Assemble escape hatch
as bootstrap/escape_hatch.s -o /tmp/emergency.o
ld /tmp/emergency.o -o /tmp/emergency

# Rebuild compiler
/tmp/emergency std/core.lang src/*.lang -o /tmp/recovered.s
as /tmp/recovered.s -o /tmp/recovered.o
ld /tmp/recovered.o -o /tmp/recovered

# Verify fixed point
/tmp/recovered std/core.lang src/*.lang -o /tmp/gen2.s
diff /tmp/recovered.s /tmp/gen2.s  # Should be identical
```

### From LLVM IR (Any Platform)

```bash
# Build from LLVM bootstrap
clang bootstrap/llvm_libc_macos.ll -o /tmp/emergency

# Generate new compiler
LANGBE=llvm /tmp/emergency std/core.lang src/*.lang -o /tmp/recovered.ll
clang /tmp/recovered.ll -o /tmp/recovered

# Verify fixed point
LANGBE=llvm /tmp/recovered std/core.lang src/*.lang -o /tmp/gen2.ll
diff /tmp/recovered.ll /tmp/gen2.ll  # Should be identical
```

## Performance

Typical compile times on modern hardware:

| Operation | x86 Backend | LLVM Backend |
|-----------|-------------|--------------|
| Full compiler build | ~3s | ~5s + clang |
| Full bootstrap | ~10s | ~30s |
| Single file | <1s | <1s + clang |
| Test suite | ~30s | ~60s |

LLVM is slower but produces optimized code and works cross-platform.
