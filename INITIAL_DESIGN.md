# lang - Design Specification

## Philosophy

- **Types after names** - Eliminates C's parsing ambiguities
- **Bootstrap-first** - Phase 0 compiles stdlib, stdlib enables Phase 1
- **Minimal** - Start tiny, extend later

## Syntax Summary

```
func factorial(n i64) i64 {
    var result i64 = 1;
    var i i64 = 1;
    while i <= n {
        result = result * i;
        i = i + 1;
    }
    return result;
}

struct Point { x i64; y i64; }
```

| Feature      | Syntax                 | Notes            |
|--------------|------------------------|------------------|
| Functions    | `func f(x i64) i64 {}` | Keyword required |
| Variables    | `var x i64 = 5;`       | Explicit type    |
| Inference    | `x := 5;`              | Phase 1+         |
| Pointers     | `*i64`, `*p`, `&x`     | C-style operators|
| Blocks       | `{ }`                  | Braces           |
| Conditionals | `if x > 0 {}`          | No parens        |
| Comments     | `//`, `/* */`          | C-style          |

## Types

```
i8  i16  i32  i64      // signed
u8  u16  u32  u64      // unsigned
bool                    // true, false
void                    // return type only
*T                      // pointer to T
[N]T                    // array (Phase 1+)
```

## Grammar (EBNF)

```ebnf
program      = { func-decl | struct-decl | var-decl } ;

func-decl    = "func" IDENT "(" [param-list] ")" [type] block ;
param-list   = param { "," param } ;
param        = IDENT type ;

struct-decl  = "struct" IDENT "{" { IDENT type ";" } "}" ;

var-decl     = "var" IDENT type ["=" expr] ";" ;

type         = base-type | "*" type | "[" NUMBER "]" type ;
base-type    = "i8"|"i16"|"i32"|"i64"|"u8"|"u16"|"u32"|"u64"|"bool"|"void"|IDENT ;

block        = "{" { statement } "}" ;
statement    = var-decl | if-stmt | while-stmt | return-stmt | expr ";" | block ;
if-stmt      = "if" expr block ["else" (if-stmt | block)] ;
while-stmt   = "while" expr block ;
return-stmt  = "return" [expr] ";" ;

expr         = assignment ;
assignment   = or-expr ["=" assignment] ;
or-expr      = and-expr {"||" and-expr} ;
and-expr     = equality {"&&" equality} ;
equality     = comparison {("=="|"!=") comparison} ;
comparison   = additive {("<"|">"|"<="|">=") additive} ;
additive     = mult {("+"|"-") mult} ;
mult         = unary {("*"|"/"|"%") unary} ;
unary        = ("-"|"!"|"*"|"&") unary | postfix ;
postfix      = primary {call | index | field} ;
call         = "(" [expr {"," expr}] ")" ;
index        = "[" expr "]" ;
field        = "." IDENT ;
primary      = NUMBER | STRING | "true" | "false" | "nil" | IDENT | "(" expr ")" ;
```

## Phase 0 Subset

**Included**: `func`, `var`, `i64`, `u8`, `bool`, `void`, `*T`, arithmetic, comparison, logical ops, `if`/`else`, `while`, `return`, function calls, string literals, `syscall` builtin.

**Excluded**: `:=` inference, structs, arrays, `for`, `const`, function pointers.

## x86-64 Calling Convention (System V ABI)

| Register     | Value                                       |
|--------------|---------------------------------------------|
| Args 1-6     | `rdi`, `rsi`, `rdx`, `rcx`, `r8`, `r9`      |
| Return       | `rax`                                       |
| Caller-saved | `rax`, `rcx`, `rdx`, `rsi`, `rdi`, `r8-r11` |
| Callee-saved | `rbx`, `rbp`, `r12-r15`                     |
| Stack        | 16-byte aligned before `call`               |

**Syscalls**: Number in `rax`, args in `rdi`, `rsi`, `rdx`, `r10`, `r8`, `r9`. Use `syscall` instruction.

## Stdlib Strategy

The stdlib is written in `language` and compiled by Phase 0. This:
1. Tests the Phase 0 compiler thoroughly
2. Provides ready-made utilities for Phase 1 compiler
3. Keeps syscall knowledge in one place

### Required Syscalls (Linux x86-64)

| Syscall | Number | Purpose |
|---------|--------|---------|
| `read` | 0 | Read file |
| `write` | 1 | Write file/stdout/stderr |
| `open` | 2 | Open file |
| `close` | 3 | Close file |
| `mmap` | 9 | Allocate memory |
| `exit` | 60 | Exit process |

### Minimal Stdlib (~60 lines)

```
// std/core.lang

// ---- Memory (bump allocator, never frees) ----
var heap_pos *u8 = nil;
var heap_end *u8 = nil;

func alloc(size i64) *u8 {
    if heap_pos == nil {
        heap_pos = syscall(9, 0, 67108864, 3, 34, -1, 0);  // mmap 64MB
        heap_end = heap_pos + 67108864;
    }
    var ptr *u8 = heap_pos;
    heap_pos = heap_pos + size;
    return ptr;
}

// ---- File I/O ----
func file_open(path *u8, flags i64) i64  { return syscall(2, path, flags, 420); }
func file_read(fd i64, buf *u8, n i64) i64  { return syscall(0, fd, buf, n); }
func file_write(fd i64, buf *u8, n i64) i64 { return syscall(1, fd, buf, n); }
func file_close(fd i64)                     { syscall(3, fd); }

// ---- Strings ----
func strlen(s *u8) i64 {
    var n i64 = 0;
    while *(s + n) != 0 { n = n + 1; }
    return n;
}

func streq(a *u8, b *u8) bool {
    while *a != 0 && *b != 0 {
        if *a != *b { return false; }
        a = a + 1;
        b = b + 1;
    }
    return *a == *b;
}

// ---- I/O ----
func print(s *u8)   { file_write(1, s, strlen(s)); }
func println(s *u8) { print(s); file_write(1, "\n", 1); }
func eprint(s *u8)  { file_write(2, s, strlen(s)); }

// ---- Process ----
func exit(code i64) { syscall(60, code); }
```

### What the Phase 1 Compiler Needs

```
func main() i64 {
    var src *u8 = alloc(65536);
    var fd i64 = file_open("input.lang", 0);
    var len i64 = file_read(fd, src, 65536);
    file_close(fd);

    // ... lexer, parser, codegen ...

    var out i64 = file_open("output.s", 577);  // O_WRONLY|O_CREAT|O_TRUNC
    file_write(out, asm_buf, asm_len);
    file_close(out);
    return 0;
}
```

## Build Process

```bash
# Phase 0: Go compiler builds stdlib + user code
cd boot && go build -o lang0
./lang0 std/core.lang hello.lang -o hello.s
as hello.s -o hello.o
ld hello.o -o hello
./hello

# Phase 1: Compiler in language compiles itself
./lang0 std/core.lang src/*.lang -o lang1.s
as lang1.s -o lang1.o
ld lang1.o -o lang1
./lang1 std/core.lang src/*.lang -o lang2.s  # should match lang1.s
```

## Implementation Order

1. **Lexer** - Tokenize Phase 0 subset
2. **Parser** - Build AST
3. **Codegen** - Emit x86-64 assembly
4. **std/core.lang** - Stdlib (tests compiler!)
5. **Hello world** - First milestone
6. **Phase 1 compiler** - Self-hosting begins

## Open Questions (Deferred)

- Mutability: default mutable or immutable?
- Modules/imports syntax
- Error handling strategy
- Generics (if ever)
