# Language Reference

**Living document** - describes what actually works right now.

**Vision**: Racket-style power with Zig-style minimalism. For fun.

See [TODO.md](./TODO.md) for roadmap, [designs/](./designs/) for design docs.

## Quick Reference

```lang
// Function definition
func add(a i64, b i64) i64 {
    return a + b;
}

// Variables
var x i64 = 42;
var p *i64 = &x;
var s *u8 = "hello";

// Control flow
if x > 0 {
    // ...
} else {
    // ...
}

while x > 0 {
    x = x - 1;
}

// Syscall
syscall(60, 0);  // exit(0)
```

## Types

### Primitive Types
| Type   | Size    | Description                                |
|--------|---------|-------------------------------------------|
| `i8`   | 1 byte  | Signed 8-bit integer                       |
| `i16`  | 2 bytes | Signed 16-bit integer                      |
| `i32`  | 4 bytes | Signed 32-bit integer                      |
| `i64`  | 8 bytes | Signed 64-bit integer (default for numbers)|
| `u8`   | 1 byte  | Unsigned 8-bit integer (char)              |
| `u16`  | 2 bytes | Unsigned 16-bit integer                    |
| `u32`  | 4 bytes | Unsigned 32-bit integer                    |
| `u64`  | 8 bytes | Unsigned 64-bit integer                    |
| `bool` | 1 byte  | Boolean (true/false)                       |
| `void` | 0 bytes | No return value                            |

### Pointer Types
- `*T` - pointer to type T
- `*u8` - commonly used for strings
- `**i64` - pointer to pointer

## Syntax

### Functions
```lang
func name(param1 Type1, param2 Type2) ReturnType {
    // body
    return value;
}

// Void function (can omit return)
func print_char(c u8) void {
    syscall(1, 1, &c, 1);
}
```

### Variables
```lang
var name Type;           // declaration (initialized to 0)
var name Type = expr;    // declaration with initialization

// Examples:
var x i64 = 42;
var ptr *i64 = &x;
var msg *u8 = "hello";
```

### Control Flow
```lang
// If statement
if condition {
    // then
}

if condition {
    // then
} else {
    // else
}

if cond1 {
    // ...
} else if cond2 {
    // ...
} else {
    // ...
}

// While loop
while condition {
    // body
}
```

### Operators

**Arithmetic** (operate on i64, result is i64):
- `+` addition
- `-` subtraction, unary negation
- `*` multiplication
- `/` integer division
- `%` modulo

**Comparison** (result is i64: 1 for true, 0 for false):
- `==` equal
- `!=` not equal
- `<` less than
- `>` greater than
- `<=` less than or equal
- `>=` greater than or equal

**Logical** (short-circuit evaluation):
- `&&` and
- `||` or
- `!` not

**Pointer**:
- `&expr` - address of (returns pointer to expr)
- `*expr` - dereference (reads value at pointer)
- `ptr + n` - pointer arithmetic (adds n bytes for *u8, n*8 for *i64, etc.)

**Assignment**:
- `=` assignment (also returns the assigned value)

### Precedence (lowest to highest)
1. `=` (assignment, right-to-left)
2. `||`
3. `&&`
4. `==` `!=`
5. `<` `>` `<=` `>=`
6. `+` `-`
7. `*` `/` `%`
8. `!` `-` (unary) `*` (deref) `&` (address-of)

## Strings

String literals have type `*u8` (pointer to bytes). They are null-terminated.

```lang
var s *u8 = "hello\n";

// Access individual characters via pointer arithmetic
var first u8 = *s;           // 'h' = 104
var second u8 = *(s + 1);    // 'e' = 101

// Strings are null-terminated
// *(s + 5) == '\n', *(s + 6) == 0
```

**Escape sequences:**
- `\n` newline
- `\t` tab
- `\r` carriage return
- `\\` backslash
- `\"` quote
- `\0` null byte

## Syscall

Direct Linux system call interface:

```lang
syscall(number, arg1, arg2, arg3, arg4, arg5, arg6);
```

Returns syscall result in `rax`.

**Common syscalls:**
| Number | Name  | Args                             |
|--------|-------|----------------------------------|
| 0      | read  | fd, buf, count                   |
| 1      | write | fd, buf, count                   |
| 2      | open  | path, flags, mode                |
| 3      | close | fd                               |
| 9      | mmap  | addr, len, prot, flags, fd, off  |
| 60     | exit  | status                           |

**Example:**
```lang
// write(1, "hi\n", 3)
syscall(1, 1, "hi\n", 3);

// exit(0)
syscall(60, 0);
```

## Standard Library (std/core.lang)

Include with: `./out/lang std/core.lang yourfile.lang -o out.s`

### Memory
```lang
func alloc(size i64) *u8;    // Bump allocator (fast, never frees)
func malloc(size i64) *u8;   // Allocator with free list (reuses freed blocks)
func free(ptr *u8) void;     // Free block allocated by malloc
```

### Dynamic Array (Vec)
```lang
func vec_new() *u8;                       // Create new vec, returns handle
func vec_len(v *u8) i64;                  // Get length
func vec_get(v *u8, index i64) i64;       // Get element at index
func vec_set(v *u8, index i64, val i64);  // Set element at index
func vec_push(v *u8, value i64);          // Append element (auto-grows)
func vec_free(v *u8);                     // Free vec and its data
```

### Hash Map (string keys -> i64 values)
```lang
func map_new() *u8;                       // Create new map, returns handle
func map_set(m *u8, key *u8, val i64);    // Set key to value
func map_get(m *u8, key *u8) i64;         // Get value (0 if not found)
func map_has(m *u8, key *u8) i64;         // Check if key exists (1=yes, 0=no)
func map_free(m *u8);                     // Free map and its data
```

### I/O
```lang
func print(s *u8) void;     // Print string to stdout
func println(s *u8) void;   // Print string + newline
func eprint(s *u8) void;    // Print to stderr
func eprintln(s *u8) void;  // Print to stderr + newline
func print_int(n i64) void; // Print integer
func exit(code i64) void;   // Exit program
```

### Strings
```lang
func strlen(s *u8) i64;           // String length
func streq(a *u8, b *u8) i64;     // String equality (1=equal, 0=not)
func str_concat(a *u8, b *u8) *u8; // Concatenate strings (allocates with malloc)
func str_dup(s *u8) *u8;          // Duplicate string (allocates with malloc)
```

### Files
```lang
func file_open(path *u8, flags i64) i64;             // Returns fd
func file_read(fd i64, buf *u8, count i64) i64;      // Returns bytes read
func file_write(fd i64, buf *u8, count i64) i64;     // Returns bytes written
func file_close(fd i64) void;
```

## Global Variables

```lang
var counter i64 = 0;  // Global, initialized to 0

func increment() void {
    counter = counter + 1;
}
```

## Structs

Structs allow grouping multiple values together:

```lang
struct Point {
    x i64;
    y i64;
}

func main() i64 {
    var p Point;
    p.x = 42;
    p.y = 100;
    return p.x + p.y;  // 142
}
```

Field access also works through pointers:

```lang
func alloc(size i64) *u8;  // from stdlib

func main() i64 {
    var p *Point = alloc(16);
    p.x = 42;
    p.y = 100;
    return p.x + p.y;  // 142
}
```

**Notes:**
- All fields are 8 bytes (aligned to 8-byte boundary)
- Field access works on both direct struct variables and pointers to structs

## Macros

Compile-time code generation with quote/unquote:

```lang
// Basic macro: expands at compile time
macro double(x) {
    return ${ $x + $x };
}

// Nested macros work
macro quad(x) {
    return ${ double(double($x)) };
}

// Usage
var n i64 = double(21);  // expands to (21 + 21) = 42
var m i64 = quad(5);     // expands to double(double(5)) = 20
```

**Syntax:**
- `macro name(params) { body }` - define a macro
- `${ expr }` - quote: treat `expr` as AST to be returned
- `$name` - unquote: splice the bound AST into the quote
- `$@name` - unquote-string: splice a string value as a string literal

**Compile-time builtins:**
- `ast_to_string(expr)` - convert AST node to string representation

**Example: get expression as string:**
```lang
macro get_name(expr) {
    var s *u8 = ast_to_string(expr);
    return ${ $@s };
}

func main() i64 {
    var x i64 = 10;
    var name *u8 = get_name(x + 1);  // name = "(x + 1)"
    println(name);
    return 0;
}
```

**How it works:**
1. At call site, parser identifies macro call
2. Arguments are bound to parameters as AST nodes (not values)
3. Macro body executes at compile-time in an interpreter
4. Quote expansion substitutes `$param` with bound AST
5. `$@param` splices a string value as a string literal
6. Resulting AST replaces the call site

**Debug:**
```bash
./out/lang --expand-macros file.lang -o out.s  # shows expansions
```

## Reader Macros

Custom syntax extensions via `#name{content}`:

```lang
// Define a reader (V1: limited interpreter, V2: full lang power)
reader lisp(text *u8) *u8 {
    // Parse text, return lang source code
    // ...
}

// Use it
var x i64 = #lisp{(+ 1 2)};  // Reader transforms to lang expression
```

**V1 (current)**: Readers run in a toy interpreter with limited builtins.
**V2 (in progress)**: Readers compile to native executables with full lang power.

See [designs/reader_v2_design.md](./designs/reader_v2_design.md) for the V2 design.

## What's NOT Implemented Yet

- Arrays (use pointer arithmetic instead)
- Struct literals (`Point{x: 1, y: 2}`)
- Passing/returning structs by value
- For loops
- Break/continue
- Switch/case
- Floating point types
- Comments in middle of expressions

## Common Patterns

### Manual "Struct" (Legacy Pattern)
Now that real structs exist, this pattern is discouraged. Shown for reference since the compiler still uses it internally.

```lang
// Token "struct": [type:8][ptr:8][len:8][line:8][col:8] = 40 bytes
var tok *u8 = alloc(40);

// Set type (offset 0)
*tok = 42;

// Set ptr (offset 8)
var tok_ptr **u8 = tok + 8;
*tok_ptr = some_ptr;

// Get line (offset 24)
var line_ptr *i64 = tok + 24;
var line i64 = *line_ptr;
```

### Character Classification
```lang
func is_digit(c u8) i64 {
    if c >= 48 {  // '0'
        if c <= 57 {  // '9'
            return 1;
        }
    }
    return 0;
}

func is_alpha(c u8) i64 {
    if c >= 65 {  // 'A'
        if c <= 90 {  // 'Z'
            return 1;
        }
    }
    if c >= 97 {  // 'a'
        if c <= 122 {  // 'z'
            return 1;
        }
    }
    if c == 95 {  // '_'
        return 1;
    }
    return 0;
}
```

### Reading File
```lang
func read_file(path *u8) *u8 {
    var fd i64 = file_open(path, 0);
    if fd < 0 {
        return 0;
    }

    var buf *u8 = alloc(65536);
    var n i64 = file_read(fd, buf, 65536);
    file_close(fd);

    // Null-terminate
    var end *u8 = buf + n;
    *end = 0;

    return buf;
}
```

## Build Commands

```bash
# Bootstrap from preserved assembly
make bootstrap

# Build compiler from source
make build

# Verify fixed point
make verify

# Compile and run a file
make run FILE=test/hello.lang

# Compile with stdlib
make stdlib-run FILE=myfile.lang

# Run all tests
make test-all

# Just compile to assembly
./out/lang myfile.lang -o out/myfile.s

# Debug macro expansions (prints each expansion to stderr)
./out/lang --expand-macros myfile.lang -o out/myfile.s
```
