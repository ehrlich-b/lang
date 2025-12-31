# Reader Lookup: `find_reader`

> Dynamic reader discovery for composable language tooling

## The Problem

You're writing a reader (e.g., Scheme) and want to support embedding other readers:

```scheme
(define (main)
  <lang#(return 42;)>      ;; embed lang
  <sql#(SELECT * FROM x)>  ;; embed sql
  <json#({ "x": 1 })>      ;; embed json
)
```

**Two approaches:**

| Approach | When to use |
|----------|-------------|
| **Hardcoded** | Specific DSL for a specific library. You know exactly which reader. |
| **Dynamic lookup** | Generic compiler. Support any reader that's available. |

```lang
// Hardcoded: you bundle this specific reader
include "my_project/sql_reader.lang"
sql_embed[$text] => sql_reader($text.text)

// Dynamic: infrastructure finds any reader by name
reader_embed[$name, $text] => find_reader($name.text)($text.text)
```

This design covers the dynamic case: `find_reader`.

---

## Existing Infrastructure

The compiler already has reader infrastructure in `src/codegen.lang`:

| Function | Location | Purpose |
|----------|----------|---------|
| `find_reader(name, len)` | codegen.lang:1161-1218 | Registry lookup, returns decl or path |
| `exec_capture(exe, input, ...)` | codegen.lang:5641-5734 | Fork/exec with stdin/stdout pipes |
| `compile_reader_to_executable(decl)` | codegen.lang:984-1159 | Compile reader to cached exe |
| `build_reader_cache_path(name, len)` | codegen.lang:922-941 | Returns `.lang-cache/readers/<name>` |
| `should_recompile_reader(exe)` | codegen.lang:959-981 | Mtime-based cache invalidation |

**The gap**: This is internal to the compiler. Readers can't call it. We need to expose it as a stdlib function.

---

## The API

```lang
// Provided by std/reader.lang
func find_reader(name *u8) fn(*u8) *u8;
```

**Input**: Reader name as string (e.g., `"lang"`, `"sql"`, `"json"`)

**Output**: Function pointer `fn(*u8) *u8` — a callable that takes text and returns AST

**Usage**:

```lang
// Get the reader
var reader fn(*u8) *u8 = find_reader("lang");

// Call it
var ast *u8 = reader("var x i64 = 1; return x;");
```

Or inline:

```lang
find_reader("lang")("var x i64 = 1;")
```

---

## Search Order

`find_reader("foo")` searches for a reader named `foo` in this order:

1. **Reader cache** (`~/.lang-cache/readers/foo`)
   - Pre-compiled reader executable
   - Fastest path

2. **Standard library** (`std/readers/foo.lang`)
   - Built-in readers (lang, json, etc.)
   - Compiled on first use, cached

3. **Project readers** (`./readers/foo.lang`)
   - Project-local reader definitions
   - Compiled on first use, cached

4. **Explicit path** (if `name` contains `/`)
   - `find_reader("./my/custom_reader.lang")`
   - Compiles and caches

If not found in any location: returns error function that produces `ast_error("reader not found: foo")`.

---

## Compilation & Caching

When `find_reader` finds a `.lang` source file but no cached executable:

1. **Compile the reader** using the current compiler
2. **Cache the executable** in `~/.lang-cache/readers/`
3. **Return function pointer** to the cached reader

Subsequent calls skip compilation and return the cached reader directly.

**Cache invalidation**: Reader is recompiled if source file is newer than cached executable.

---

## Implementation

### What Changes

We need to:
1. **Extract** `exec_capture` logic into a reusable stdlib function
2. **Add** search paths beyond just the cache
3. **Expose** as `std/reader.lang` that readers can include

### Step 1: Create `std/reader.lang`

```lang
// std/reader.lang
// Dynamic reader lookup for reader embedding

include "std/core.lang"

// Storage for cached reader function pointers
// (We cache the exe paths, closures capture them)

func find_reader(name *u8) fn(*u8) *u8 {
    var exe_path *u8 = locate_reader(name);
    if exe_path == nil {
        // Return error-producing function
        return |text *u8| *u8 {
            return str_concat("(error \"reader not found: ", name, "\")");
        };
    }

    // Return closure that invokes the reader
    return |text *u8| *u8 {
        return exec_reader(exe_path, text);
    };
}

func find_reader_or_nil(name *u8) fn(*u8) *u8 {
    var exe_path *u8 = locate_reader(name);
    if exe_path == nil {
        return nil;
    }
    return |text *u8| *u8 {
        return exec_reader(exe_path, text);
    };
}
```

### Step 2: `locate_reader` - Multi-Path Search

```lang
func locate_reader(name *u8) *u8 {
    var path *u8 = alloc(256);

    // 1. Check cache first (fastest)
    str_concat_into(path, ".lang-cache/readers/", name);
    if file_exists(path) {
        return path;
    }

    // 2. Check std/readers/<name>.lang, compile if found
    str_concat_into(path, "std/readers/", name, ".lang");
    if file_exists(path) {
        return compile_reader_source(path, name);
    }

    // 3. Check ./readers/<name>.lang, compile if found
    str_concat_into(path, "readers/", name, ".lang");
    if file_exists(path) {
        return compile_reader_source(path, name);
    }

    // 4. If name contains '/', treat as explicit path
    if str_contains(name, "/") {
        if file_exists(name) {
            return compile_reader_source(name, basename(name));
        }
    }

    return nil;  // Not found
}
```

### Step 3: `compile_reader_source` - On-Demand Compilation

```lang
func compile_reader_source(source_path *u8, name *u8) *u8 {
    var cache_path *u8 = alloc(256);
    str_concat_into(cache_path, ".lang-cache/readers/", name);

    // Check if recompilation needed (mtime-based)
    if !should_recompile(source_path, cache_path) {
        return cache_path;
    }

    // Compile: ./out/lang <source> -o <cache_path>
    var cmd *u8 = str_concat("./out/lang ", source_path, " -o ", cache_path);
    var status i64 = system(cmd);

    if status != 0 {
        return nil;  // Compilation failed
    }

    return cache_path;
}
```

### Step 4: `exec_reader` - Reuse Existing Infrastructure

This is essentially `exec_capture` from codegen.lang, wrapped for stdlib use:

```lang
func exec_reader(exe_path *u8, text *u8) *u8 {
    var text_len i64 = strlen(text);
    var output *u8 = alloc(131072);  // 128KB buffer

    // Fork/exec with pipes (same as codegen.lang:5641-5734)
    var stdin_pipe *i64 = alloc(16);
    var stdout_pipe *i64 = alloc(16);

    syscall(22, stdin_pipe);   // pipe()
    syscall(22, stdout_pipe);  // pipe()

    var pid i64 = syscall(57); // fork()

    if pid == 0 {
        // Child: setup pipes, exec reader
        syscall(33, *stdin_pipe, 0);       // dup2(stdin_read, 0)
        syscall(33, *(stdout_pipe + 8), 1); // dup2(stdout_write, 1)

        // Close all pipe fds
        syscall(3, *stdin_pipe);
        syscall(3, *(stdin_pipe + 8));
        syscall(3, *stdout_pipe);
        syscall(3, *(stdout_pipe + 8));

        // Build argv and exec
        var argv **u8 = alloc(16);
        *argv = exe_path;
        *(argv + 8) = nil;
        syscall(59, exe_path, argv, environ());  // execve
        syscall(60, 1);  // exit(1) if exec fails
    }

    // Parent: communicate with child
    syscall(3, *stdin_pipe);            // close stdin_read
    syscall(3, *(stdout_pipe + 8));     // close stdout_write

    // Write input
    syscall(1, *(stdin_pipe + 8), text, text_len);
    syscall(3, *(stdin_pipe + 8));      // close stdin_write (EOF)

    // Read output
    var total i64 = 0;
    var n i64 = syscall(0, *stdout_pipe, output, 131071);
    while n > 0 {
        total = total + n;
        n = syscall(0, *stdout_pipe, output + total, 131071 - total);
    }
    *(output + total) = 0;  // null-terminate

    syscall(3, *stdout_pipe);  // close stdout_read

    // Wait for child
    var status *i64 = alloc(8);
    syscall(61, pid, status, 0);  // waitpid

    return output;
}
```

### Alternative: Extract from Compiler

Instead of duplicating `exec_capture`, we could:

1. **Move** `exec_capture` to `std/process.lang`
2. **Have** codegen.lang include it
3. **Have** std/reader.lang include it

This avoids duplication and keeps the fork/exec logic in one place.

```lang
// std/process.lang
func exec_capture(program *u8, input *u8, input_len i64,
                  output *u8, output_cap i64) i64;

// std/reader.lang
include "std/process.lang"

func exec_reader(exe_path *u8, text *u8) *u8 {
    var output *u8 = alloc(131072);
    var n i64 = exec_capture(exe_path, text, strlen(text), output, 131072);
    if n <= 0 {
        return "(error \"reader returned no output\")";
    }
    return output;
}
```

---

## Error Handling

```lang
var reader fn(*u8) *u8 = find_reader("nonexistent");
var ast *u8 = reader("some text");
// ast = "(error \"reader not found: nonexistent\")"
```

Errors are AST error nodes. The kernel will report them during compilation.

For explicit checking:

```lang
func find_reader_or_nil(name *u8) fn(*u8) *u8;  // Returns nil if not found

var reader fn(*u8) *u8 = find_reader_or_nil("maybe_exists");
if reader == nil {
    // Handle missing reader
}
```

---

## Integration with #emit{}

In your emit rules:

```lang
#emit{
    // Dynamic: any reader by name
    reader_embed[$name, $text] => find_reader($name.text)($text.text)
}
```

The pattern matches `<foo#(...)>`, extracts name `"foo"` and text, calls `find_reader("foo")`, invokes the result with text, splices AST output.

---

## Built-in Readers

These are always available via `find_reader`:

| Name | Source | Description |
|------|--------|-------------|
| `lang` | `std/readers/lang.lang` | The lang language itself |
| `json` | `std/readers/json.lang` | JSON → AST data literals |
| `sexpr` | `std/readers/sexpr.lang` | S-expression parser |

Additional readers can be installed project-locally or globally.

---

## Example: Universal Polyglot Reader

A reader that supports embedding ANY available reader:

```lang
include "std/core.lang"
include "std/tok.lang"
include "std/parser_reader.lang"
include "std/ast.lang"
include "std/reader.lang"

#parser{
    program = stmt*
    stmt    = embed | expr_stmt

    // Universal embedding: @reader_name{ text }
    embed   = '@' IDENT '{' raw_text '}'

    expr_stmt = expr ';'
    expr    = NUMBER | IDENT | call
    call    = IDENT '(' args? ')'
    args    = expr (',' expr)*
}

#emit{
    program[$stmts*] => ast_program($stmts)

    // The magic: any reader, found dynamically
    embed[$name, $text] => find_reader($name.text)($text.text)

    NUMBER($n)   => ast_number($n.text)
    IDENT($id)   => ast_ident($id.text)
    call[$fn, $args*] => ast_call(ast_ident($fn.text), $args)
    expr_stmt[$e] => ast_expr_stmt($e)
}

reader polyglot(text *u8) *u8 {
    var t *Tokenizer = tok_new(text);
    var tree *PNode = parse_program(t);
    return emit(tree);
}
```

Usage:

```
// polyglot source
@lang{
    func helper() i64 {
        return 42;
    }
}

@scheme{
    (define (factorial n)
      (if (< n 2) 1 (* n (factorial (- n 1)))))
}

@sql{
    SELECT * FROM users WHERE id = :user_id
}

main();
```

Each `@name{...}` block is compiled by finding that reader dynamically. The polyglot reader doesn't know about lang, scheme, or sql specifically—it just finds and calls whatever readers are available.

---

## Enumerating Readers: `list_readers`

Sometimes you need to know what's available:

```lang
// Provided by std/reader.lang
func list_readers() *Vec;  // Returns Vec of reader name strings
```

**Implementation**: Scans all search paths, deduplicates, returns names:

```lang
func list_readers() *Vec {
    var names *Vec = vec_new();

    // 1. Scan cache directory
    scan_dir_for_readers(".lang-cache/readers/", names, false);

    // 2. Scan std/readers/ (strip .lang extension)
    scan_dir_for_readers("std/readers/", names, true);

    // 3. Scan ./readers/ (strip .lang extension)
    scan_dir_for_readers("readers/", names, true);

    return names;
}

func scan_dir_for_readers(dir *u8, names *Vec, strip_ext bool) void {
    var d *DIR = opendir(dir);
    if d == nil { return; }

    var entry *dirent = readdir(d);
    while entry != nil {
        var name *u8 = entry.d_name;

        // Skip . and ..
        if !streq(name, ".") && !streq(name, "..") {
            if strip_ext {
                name = strip_extension(name, ".lang");
            }
            // Only add if not already present
            if !vec_contains_str(names, name) {
                vec_push(names, str_dup(name));
            }
        }
        entry = readdir(d);
    }
    closedir(d);
}
```

**Usage**:

```lang
var readers *Vec = list_readers();
for var i i64 = 0; i < readers.len; i = i + 1 {
    var name *u8 = vec_get(readers, i) as *u8;
    printf("Available: %s\n", name);
}
```

Or for probing specific capabilities:

```lang
func has_reader(name *u8) bool {
    return find_reader_or_nil(name) != nil;
}

if has_reader("sql") {
    // Use SQL embedding
}
```

---

## Summary

| Function | Returns | Use case |
|----------|---------|----------|
| `find_reader(name)` | `fn(*u8) *u8` | Dynamic lookup, always returns callable (may return error-producer) |
| `find_reader_or_nil(name)` | `fn(*u8) *u8` or `nil` | When you need to check existence |
| `list_readers()` | `*Vec` | Enumerate all available readers |
| `has_reader(name)` | `bool` | Quick existence check |

**The pattern:**

```lang
find_reader($name.text)($text.text)
```

1. Find reader by name → get function pointer
2. Call function with text → get AST
3. Splice AST into output

**Infrastructure handles**: discovery, compilation, caching. You just call and receive.

---

## Specific Changes Required

### Files to Create

| File | Purpose |
|------|---------|
| `std/reader.lang` | Exposes `find_reader()` and `find_reader_or_nil()` |
| `std/process.lang` | Extracted `exec_capture()` for reuse |

### Files to Modify

| File | Change |
|------|--------|
| `src/codegen.lang` | Replace inline `exec_capture` with `include "std/process.lang"` |

### Implementation Order

1. **Extract** `exec_capture` from codegen.lang:5641-5734 → `std/process.lang`
2. **Update** codegen.lang to include std/process.lang
3. **Create** `std/reader.lang` with:
   - `find_reader(name) → fn(*u8) *u8`
   - `find_reader_or_nil(name) → fn(*u8) *u8`
   - `has_reader(name) → bool`
   - `list_readers() → *Vec`
   - `locate_reader(name) → *u8` (internal)
   - `compile_reader_source(path, name) → *u8` (internal)
   - `exec_reader(exe, text) → *u8` (internal, wraps exec_capture)
   - `scan_dir_for_readers(dir, names, strip_ext)` (internal)
4. **Test** with a reader that embeds another reader
5. **Test** `list_readers()` returns expected results

### LOC Estimate

| Component | Lines |
|-----------|-------|
| std/process.lang | ~80 (extracted from codegen) |
| std/reader.lang | ~150 (includes list_readers, dir scanning) |
| codegen.lang changes | -80 (remove), +2 (include) |
| **Net new** | ~150 |

---

*"Any reader, anywhere, anytime."*
