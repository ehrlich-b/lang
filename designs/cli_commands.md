# CLI Commands Design

This document proposes a subcommand-based CLI architecture for lang.

## Current State

```bash
lang file.lang -o out.s              # compile
lang -c reader src/reader.lang -o standalone.s  # compose (BROKEN)
lang file.lang --emit-ast -o file.ast           # emit AST
```

**Problems:**
1. No `--help` or usage info
2. No way to introspect environment variables
3. No way to check toolchain availability
4. No way to see what readers are available
5. `-c` composition is broken (AST round-trip corruption)

## Proposal: Subcommands

### Semantic Distinction

- **Subcommand** = which operation to perform
- **Flags** = how to perform that operation

This matches `cargo`, `go`, and `docker` conventions.

### Argument Disambiguation

Simple heuristic: **files have extensions, commands don't**.

```bash
lang help              # no extension → command
lang env               # no extension → command
lang file.lang -o out  # has .lang → file → implicit compile
lang compose reader src/reader.lang  # "compose" is command, rest are args
```

This is unambiguous:
- First arg has extension? → compile mode, all positional args are files
- First arg has no extension? → it's a subcommand

---

## Proposed Subcommands

### `lang help [subcommand]`

Show usage information.

```bash
lang help              # general help
lang help compile      # help for compile subcommand
lang help env          # help for env subcommand
```

Aliases: `lang --help`, `lang -h`

**Output format:**
```
lang - a self-hosted compiler where syntax is a plugin

Usage: lang [subcommand] [options]

Subcommands:
  compile    Compile source files (default)
  help       Show this help message
  version    Show version information
  env        Show environment variables
  tools      Show toolchain availability
  readers    Show available readers/syntaxes

Run 'lang help <subcommand>' for details.
```

### `lang version`

Show version and build info.

```bash
lang version
```

**Output:**
```
lang 0.1.0 (git: abc123)
backend: x86 (LANGBE=x86)
os: linux (LANGOS=linux)
libc: none (LANGLIBC=none)
```

Aliases: `lang --version`, `lang -V`

### `lang env`

Show all relevant environment variables.

```bash
lang env              # show all
lang env LANGBE       # show specific variable
```

**Output:**
```
LANGBE=x86
LANGOS=linux
LANGLIBC=none
LANGCACHE=.lang-cache
```

**Categories:**
- Core: LANGBE, LANGOS, LANGLIBC
- Paths: LANGCACHE, PATH
- Build: CC, AS, LD

**Flags:**
- `--export` - output in shell format: `export LANGBE=x86`
- `--json` - output as JSON

### `lang tools`

Introspect available toolchain.

```bash
lang tools            # show all tools
lang tools --check    # exit 0 if all required tools present, 1 otherwise
lang tools --verbose  # show versions
```

**Output:**
```
Required (for LANGBE=x86):
  ✓ as        GNU assembler
  ✓ ld        GNU linker

Required (for LANGBE=llvm):
  ✓ clang     LLVM C compiler (compile + link)

Optional (LLVM utilities):
  ✓ lli       LLVM interpreter (for testing)
  ✓ llc       LLVM static compiler
  ✗ opt       LLVM optimizer (not found)

Optional (test harness):
  ✓ timeout   GNU coreutils timeout
  ✗ gtimeout  GNU timeout for macOS (not found)
  ✓ xargs     parallel execution
```

**Tool categories:**

| Tool | When Required | Purpose |
|------|---------------|---------|
| `as` | LANGBE=x86 | Assemble x86 output |
| `ld` | LANGBE=x86 | Link x86 binaries |
| `clang` | LANGBE=llvm | Compile LLVM IR to native |
| `lli` | Testing | Interpret LLVM IR (fast tests) |
| `llc` | Optional | LLVM IR to assembly |
| `opt` | Optional | LLVM optimizer passes |
| `timeout`/`gtimeout` | Testing | Test timeout handling |

**Exit codes:**
- 0: All required tools for current LANGBE are available
- 1: Missing required tools

**Flags:**
- `--check` - silent mode, just check and exit
- `--verbose` - show version info
- `--json` - output as JSON

### `lang readers`

Show available readers/syntaxes.

```bash
lang readers          # list readers
lang readers --check  # verify readers can parse
```

**Output:**
```
Built-in readers:
  lang    Lang syntax (.lang files)

Cached readers (in .lang-cache/readers/):
  lisp    Lisp syntax (from example/minilisp/)
  parser  Parser reader (metaprogramming)

Composable readers (require -c to use):
  (none currently composed)

File extension mappings:
  .lang  → lang reader
  .lisp  → lisp reader (if cached)
```

**Questions to answer:**
- "If I pass you a .lisp file, can you compile it?" → Check if lisp reader exists
- "What syntaxes does this compiler understand?" → List built-in + cached

### `lang compile [files...] -o output`

The default operation. Compile source files.

```bash
lang compile std/core.lang main.lang -o main.s
lang main.lang -o main.s  # same (compile is default)
```

**Flags:**
- `-o <file>` - output file (required)
- `--emit-ast` - emit AST instead of assembly
- `--emit-expanded-ast` - emit fully expanded AST
- `--from-ast` - input is AST, not source

### `lang compose <reader> <files...> -o output`

Generate a standalone compiler with a reader.

```bash
lang compose lang src/lang_reader.lang -o standalone.s
lang compose lisp example/minilisp/lisp.lang -o lang_lisp.s
```

This replaces the broken `-c` flag with a cleaner interface.

**What it does:**
1. Compile the reader source files
2. Merge with kernel
3. Generate glue code (reader_transform function)
4. Output a standalone compiler binary

**Flags:**
- `-o <file>` - output file (required)
- `--emit-ast` - emit composed AST instead of compiling

---

## Implementation Notes

### Argument Parsing

```c
// Pseudocode
func has_extension(s *u8) bool {
    // Look for '.' in the string
    while *s != 0 {
        if *s == '.' { return true; }
        s = s + 1;
    }
    return false;
}

func main(argc, argv) {
    if argc < 2 {
        return cmd_help(0, nil);
    }

    var first = argv[1];

    // If first arg has an extension, it's a file → compile mode
    if has_extension(first) {
        return cmd_compile(argc - 1, argv + 1);
    }

    // Otherwise it's a command
    if streq(first, "help")     { return cmd_help(argc-2, argv+2); }
    if streq(first, "version")  { return cmd_version(); }
    if streq(first, "env")      { return cmd_env(argc-2, argv+2); }
    if streq(first, "tools")    { return cmd_tools(argc-2, argv+2); }
    if streq(first, "readers")  { return cmd_readers(argc-2, argv+2); }
    if streq(first, "compile")  { return cmd_compile(argc-2, argv+2); }
    if streq(first, "compose")  { return cmd_compose(argc-2, argv+2); }

    // Unknown command
    eprint("Unknown command: ");
    eprintln(first);
    return 1;
}
```

### Command Summary

| Command | Description |
|---------|-------------|
| `lang file.lang -o out` | Compile (implicit, first arg has extension) |
| `lang help` | Show usage |
| `lang version` | Show version info |
| `lang env` | Show environment variables |
| `lang tools` | Show toolchain status |
| `lang readers` | Show available syntaxes |
| `lang compose reader file.lang -o out` | Generate standalone compiler |

---

## String Utilities Needed

The stdlib (`std/core.lang`) has basic string functions. For robust arg parsing, we need a few more:

### Already Available

```lang
func streq(a *u8, b *u8) i64;           // string equality
func strlen(s *u8) i64;                  // string length
func str_dup(s *u8) *u8;                 // duplicate string
func str_concat(a *u8, b *u8) *u8;       // concatenate
func str_eq_n(a *u8, a_len i64, b *u8, b_len i64) bool;  // length-bounded eq
```

### Already in main.lang

```lang
func get_extension(path *u8) *u8;        // returns extension or nil
func is_lang_extension(ext *u8) i64;     // check for "lang"
```

### Need to Add

```lang
// Check if string starts with prefix
func str_starts_with(s *u8, prefix *u8) i64 {
    while *prefix != 0 {
        if *s != *prefix { return 0; }
        s = s + 1;
        prefix = prefix + 1;
    }
    return 1;
}

// Check if string ends with suffix
func str_ends_with(s *u8, suffix *u8) i64 {
    var slen i64 = strlen(s);
    var suffixlen i64 = strlen(suffix);
    if suffixlen > slen { return 0; }
    return streq(s + slen - suffixlen, suffix);
}

// Check if file exists (for tools --check)
func file_exists(path *u8) i64 {
    var fd i64 = file_open(path, 0);
    if fd < 0 { return 0; }
    file_close(fd);
    return 1;
}

// Check if command exists in PATH
func command_exists(cmd *u8) i64 {
    // Implementation: use access() syscall or try to execute with --version
    // For now, can shell out to "which"
}
```

### Where to Put These

Options:
1. Add to `std/core.lang` - general utilities
2. Add to `src/main.lang` - compiler-specific
3. New file `std/cli.lang` - CLI utilities

Recommendation: Add `str_starts_with` and `str_ends_with` to `std/core.lang` (they're general-purpose). Put CLI-specific helpers in `src/main.lang`.

---

## Fixing `-c` / Composition

The current `-c` implementation is broken due to AST round-trip corruption.

### Current Flow (broken)

```
1. Compile reader sources to .lang-cache/readers/<name>
2. Include standalone.lang template
3. Generate glue code
4. Compile everything together
```

The problem is in step 1-2: AST merging produces incorrect code.

### Proposed Fix

Option A: **Don't merge ASTs at runtime**
- Compile reader to a cached binary reader function
- Link the function at compile time, not compose time
- Requires rethinking how readers are invoked

Option B: **Fix AST round-trip**
- Debug why AST → text → AST loses information
- Fix the sexpr_reader to preserve all node types
- This is the root cause

Option C: **Emit source, not AST**
- Instead of parsing/emitting AST, just concatenate source files
- Simpler but loses some flexibility

### Investigation Needed

The `kernel_main.lang` `combine_programs()` function looks correct. The issue is likely in:
1. `parse_ast_from_string()` - losing information during parse
2. The AST files themselves - missing required structure
3. `generate()` - assuming structure that combined ASTs don't have

Need to:
1. Dump AST before and after combination
2. Compare with working non-composed compilation
3. Find the specific corruption point

---

## Open Questions

1. Should `lang tools --check` be run automatically before compilation?
   - Pro: Fail fast with helpful error
   - Con: Adds latency

2. Should readers be registered globally or per-project?
   - Current: per-project in `.lang-cache/`
   - Alternative: `~/.lang/readers/`

3. Should `lang env` modify environment or just display?
   - Display only (like `go env`)
   - Use `eval $(lang env --export)` to set

4. Should there be a `lang init` command?
   - Creates `.lang-cache/`
   - Sets up default readers
   - Like `cargo init` or `npm init`

---

## Implementation Plan

### Phase 1: Foundation (do first)
1. Add `str_starts_with` to `std/core.lang`
2. Refactor `main.lang` arg parsing to use command detection
3. Implement `lang help` (just usage text)
4. Implement `lang version` (git commit + env vars)

### Phase 2: Introspection
5. Implement `lang env` (dump environment variables)
6. Implement `lang tools` (check toolchain)
7. Implement `lang readers` (list available syntaxes)

### Phase 3: Fix Composition
8. Debug `-c` / composition AST corruption
9. Implement `lang compose` as clean replacement
10. Remove old `-c` flag

### Phase 4: Polish
11. Add `--json` output option for scripting
12. Add `--check` modes for CI
13. Consider `lang init` command
