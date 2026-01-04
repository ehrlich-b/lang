# Stdlib Strategy: Build vs Bring vs Bridge

## The Question

What do end-programs compiled by lang actually need, and how should we provide it?

**Concrete goal**: Compile a small web server in lang.

**Options on the table**:
1. Build our own stdlib (years of work)
2. Bring your own stdlib via C ABI (FFI-heavy)
3. Bridge to another language's stdlib (Zig, Rust, etc.)
4. Hybrid: minimal core + easy FFI + blessed libraries

---

## What Programs Actually Need

### Tier 0: Bare Metal (lang has this)
- Integer math, pointers, structs
- Stack allocation
- Function calls
- Syscalls (Linux direct, macOS via libc)

**Current state**: Works. You can write a compiler with this.

### Tier 1: Basic Runtime (lang has most of this)
- Heap allocation (malloc/free or bump allocator)
- String handling (strlen, strcmp, concat)
- Basic I/O (print, file read/write)
- Dynamic arrays, hash maps

**Current state**: std/core.lang provides this, but it's rough. No error handling, no generics, manual pointer math everywhere.

### Tier 2: Systems Programming (lang has some)
- File system operations (open, read, write, stat, readdir)
- Process management (fork, exec, wait)
- Environment variables
- Command-line argument parsing
- Buffered I/O

**Current state**: Partially there via raw syscalls. No abstractions.

### Tier 3: Network Programming (lang doesn't have this)
- Sockets (TCP, UDP)
- DNS resolution
- HTTP client/server
- TLS/SSL

**Current state**: Would need to either:
- Implement via raw syscalls (painful, platform-specific)
- Link against libc (socket functions)
- Link against external libs (libcurl, openssl)

### Tier 4: Rich Applications (lang definitely doesn't have this)
- JSON parsing
- Database drivers
- Async I/O / event loops
- Compression
- Cryptography

**Current state**: Would need external libraries.

---

## The Web Server Test

To build a minimal HTTP server, we need:

```
1. socket()      - create socket
2. bind()        - bind to port
3. listen()      - start listening
4. accept()      - accept connection
5. read()        - read HTTP request
6. write()       - write HTTP response
7. close()       - close connection
```

### Path A: Raw Syscalls (Linux only)

```lang
// This works TODAY on Linux x86-64
func socket(domain i64, type i64, protocol i64) i64 {
    return syscall(41, domain, type, protocol);  // SYS_socket
}

func bind(fd i64, addr *u8, len i64) i64 {
    return syscall(49, fd, addr, len);  // SYS_bind
}

// ... etc
```

**Problems**:
- Platform-specific syscall numbers
- Need to manually construct sockaddr structs
- No DNS (need libc's getaddrinfo or implement DNS protocol)
- No TLS (would need to implement TLS from scratch or link openssl)

### Path B: libc FFI (Cross-platform-ish)

```lang
extern func socket(domain i32, type i32, protocol i32) i32;
extern func bind(fd i32, addr *u8, len i32) i32;
extern func listen(fd i32, backlog i32) i32;
extern func accept(fd i32, addr *u8, len *i32) i32;
extern func getaddrinfo(node *u8, service *u8, hints *u8, res **u8) i32;
```

**This works TODAY** with LANGBE=llvm. The LLVM backend links against libc.

**Problems**:
- Need to know C struct layouts (sockaddr_in, addrinfo, etc.)
- Different on Linux vs macOS vs Windows
- Still no TLS without linking openssl/boringssl

### Path C: Link External Library

```bash
# Compile lang to LLVM IR
./out/lang server.lang -o server.ll

# Link with libcurl
clang server.ll -lcurl -o server
```

In lang:
```lang
extern func curl_easy_init() *u8;
extern func curl_easy_setopt(handle *u8, option i64, value i64) i64;
extern func curl_easy_perform(handle *u8) i64;
```

**This works TODAY** for HTTP client. For server, you'd link something like libevent or libuv.

---

## The Zig Bridge: Deep Dive

Zig is interesting because:
1. Compiles to object files with C ABI
2. Has a complete, well-designed stdlib
3. Can be built without libc dependency
4. Cross-compiles trivially

### What "Bridging to Zig" Would Mean

**Option 1: Link Zig stdlib as a library**

```bash
# Build Zig's stdlib as a static library
zig build-lib -OReleaseFast --emit=asm std

# Compile lang program
./out/lang myapp.lang -o myapp.ll

# Link together
clang myapp.ll libstd.a -o myapp
```

In lang, declare Zig functions as extern:
```lang
// Zig's std.net.Stream
extern func zig_net_listen(address *u8, port u16) *u8;  // returns Stream
extern func zig_net_accept(listener *u8) *u8;           // returns Connection
extern func zig_net_read(conn *u8, buf *u8, len i64) i64;
extern func zig_net_write(conn *u8, buf *u8, len i64) i64;
```

**Problem**: Zig's stdlib doesn't expose C-callable functions by default. You'd need to write Zig wrapper code:

```zig
// zig_wrappers.zig
const std = @import("std");

export fn zig_net_listen(address: [*:0]const u8, port: u16) ?*std.net.Stream.Server {
    // ...
}
```

This is a lot of glue code.

**Option 2: Capture Zig syntax as a reader**

More ambitious: write a Zig reader that parses Zig syntax and emits lang AST.

```lang
#zig{
    const std = @import("std");

    pub fn main() !void {
        const listener = try std.net.tcpListen(.{});
        // ...
    }
}
```

**Problems**:
- Zig has complex semantics (comptime, error unions, async)
- Some Zig features don't map to lang AST
- See designs/abi.md for analysis

**Option 3: Use Zig as a "batteries included" stdlib**

Don't capture Zig syntax - just use Zig to WRITE the stdlib, then expose via C ABI:

```
zig_stdlib/
  net.zig       → exports C-callable: lang_net_listen, lang_net_accept, ...
  http.zig      → exports C-callable: lang_http_server_new, lang_http_handle, ...
  fs.zig        → exports C-callable: lang_file_open, lang_file_read, ...

build.zig      → compiles to liblang_stdlib.a
```

In lang:
```lang
include "std/zig_bindings.lang"  // extern func declarations

func main() i64 {
    var server *u8 = lang_http_server_new(8080);
    while true {
        var conn *u8 = lang_http_accept(server);
        var req *u8 = lang_http_read_request(conn);
        lang_http_write_response(conn, 200, "Hello, World!");
        lang_http_close(conn);
    }
    return 0;
}
```

**This is actually viable.** Benefits:
- Zig stdlib is battle-tested
- Cross-platform for free
- Can incrementally add wrappers as needed
- Lang stays simple, Zig handles complexity

---

## The Rust Bridge

Similar idea, but Rust has more FFI friction:
- Rust's stdlib isn't designed for C export
- Would need lots of `#[no_mangle] pub extern "C" fn` wrappers
- Rust's error handling (Result) doesn't map to C cleanly

Zig is better suited for this because it was designed with C interop in mind.

---

## The "Just Use libc" Path

Maybe we're overthinking this. libc provides:
- Sockets
- File I/O
- Memory allocation
- String functions
- Math functions

And it's available everywhere.

**What we'd need**:
1. `std/libc.lang` - extern declarations for common libc functions
2. `std/posix.lang` - higher-level wrappers (error checking, etc.)
3. Platform detection (different struct layouts)

```lang
// std/libc.lang
extern func socket(domain i32, type i32, protocol i32) i32;
extern func connect(fd i32, addr *u8, len i32) i32;
extern func send(fd i32, buf *u8, len i64, flags i32) i64;
extern func recv(fd i32, buf *u8, len i64, flags i32) i64;
// ... hundreds more

// std/posix.lang (higher level)
func tcp_connect(host *u8, port i64) i64 {
    // Use getaddrinfo, socket, connect
    // Handle errors
    // Return fd or -1
}
```

**For TLS**, we'd still need openssl/boringssl/rustls.

---

## Hybrid Proposal: Minimal Core + Blessed Bridges

### The Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        lang program                              │
├─────────────────────────────────────────────────────────────────┤
│  std/core.lang     │  std/libc.lang    │  std/zig.lang          │
│  (pure lang)       │  (libc bindings)  │  (zig stdlib bindings) │
├─────────────────────────────────────────────────────────────────┤
│                        lang kernel                               │
├─────────────────────────────────────────────────────────────────┤
│  libc.so/dylib     │  libzig_runtime.a │  other libs            │
└─────────────────────────────────────────────────────────────────┘
```

### std/core.lang (Pure Lang - No Dependencies)

What we provide ourselves:
- Memory: bump allocator, malloc/free (current)
- Collections: Vec, Map, Set (improve current)
- Strings: basic operations (improve current)
- I/O: raw syscalls, print (current)

This is enough to write the compiler. Keep it minimal.

### std/libc.lang (C Standard Library)

Thin bindings to libc:
```lang
// Memory
extern func malloc(size i64) *u8;
extern func free(ptr *u8) void;
extern func realloc(ptr *u8, size i64) *u8;

// Strings
extern func strlen(s *u8) i64;
extern func strcmp(a *u8, b *u8) i32;
extern func strcpy(dst *u8, src *u8) *u8;

// I/O
extern func fopen(path *u8, mode *u8) *u8;
extern func fread(buf *u8, size i64, count i64, f *u8) i64;
extern func fwrite(buf *u8, size i64, count i64, f *u8) i64;
extern func fclose(f *u8) i32;

// Network
extern func socket(domain i32, type i32, protocol i32) i32;
extern func bind(fd i32, addr *u8, len i32) i32;
extern func listen(fd i32, backlog i32) i32;
extern func accept(fd i32, addr *u8, len *i32) i32;
extern func connect(fd i32, addr *u8, len i32) i32;
extern func getaddrinfo(node *u8, service *u8, hints *u8, res **u8) i32;
```

Plus helper structs and constants:
```lang
struct sockaddr_in {
    family i16;
    port i16;      // network byte order!
    addr i32;
    zero [8]u8;
}

var AF_INET i32 = 2;
var SOCK_STREAM i32 = 1;
```

### std/zig.lang (Zig Runtime - Optional)

If user wants richer functionality:
```lang
// Link: clang ... -lzig_lang_runtime

extern func zig_http_server(port u16) *u8;
extern func zig_http_accept(server *u8) *u8;
extern func zig_http_request_method(req *u8) *u8;
extern func zig_http_request_path(req *u8) *u8;
extern func zig_http_respond(req *u8, status i32, body *u8) void;
```

We'd write the Zig side once:
```zig
// zig_lang_runtime/http.zig
const std = @import("std");

export fn zig_http_server(port: u16) ?*Server {
    return std.net.StreamServer.init(.{
        .reuse_address = true,
    }).listen(std.net.Address.initIp4(.{0,0,0,0}, port)) catch null;
}
// ... etc
```

---

## The #emit Angle (Reader Authoring)

You mentioned `std/emit.lang` and a design for #emit. This is different from runtime stdlib - it's about **reader authoring**.

The vision:
```lang
#parser{
    expr = term (('+' | '-') term)*
    term = factor (('*' | '/') factor)*
    factor = NUMBER | '(' expr ')'
}

#emit{
    expr(a, op, b) => ast_binop(op, a, b)
    factor(n) => ast_number(n)
}
```

The #parser generates parsing code, #emit generates AST-building code.

**Current state**: We have pieces but not the full vision:
- `std/grammar.lang` - grammar representation
- `std/rdgen.lang` - reader generation
- `std/ast.lang` - AST constructors
- `std/emit.lang` - basic emission

**What's missing**: The #emit reader that ties parser rules to AST rules.

This is orthogonal to runtime stdlib - it's about making reader authoring delightful.

---

## Concrete Proposal: Web Server in 3 Phases

### Phase 1: Prove It Works (Today)

Write a web server using raw libc bindings:

```lang
include "std/core.lang"

// Raw libc declarations
extern func socket(domain i32, type i32, protocol i32) i32;
extern func bind(fd i32, addr *u8, len i32) i32;
extern func listen(fd i32, backlog i32) i32;
extern func accept(fd i32, addr *u8, len *i32) i32;
extern func read(fd i32, buf *u8, len i64) i64;
extern func write(fd i32, buf *u8, len i64) i64;
extern func close(fd i32) i32;
extern func htons(n u16) u16;

struct sockaddr_in {
    family i16;
    port u16;
    addr u32;
    zero0 i64;  // padding
}

func main() i64 {
    var server_fd i32 = socket(2, 1, 0);  // AF_INET, SOCK_STREAM
    if server_fd < 0 {
        eprintln("socket failed");
        return 1;
    }

    var addr sockaddr_in;
    addr.family = 2;
    addr.port = htons(8080);
    addr.addr = 0;

    if bind(server_fd, &addr, 16) < 0 {
        eprintln("bind failed");
        return 1;
    }

    if listen(server_fd, 10) < 0 {
        eprintln("listen failed");
        return 1;
    }

    println("Listening on :8080");

    var buf [4096]u8;
    var response *u8 = "HTTP/1.1 200 OK\r\nContent-Length: 13\r\n\r\nHello, World!";

    while true {
        var client_fd i32 = accept(server_fd, 0, 0);
        if client_fd < 0 { continue; }

        var n i64 = read(client_fd, &buf, 4096);
        write(client_fd, response, 53);
        close(client_fd);
    }

    return 0;
}
```

Compile:
```bash
LANGBE=llvm ./out/lang server.lang -o server.ll
clang server.ll -o server
./server
```

**This should work TODAY.** Let's verify.

### Phase 2: std/net.lang (Thin Wrapper)

Clean up the ergonomics:

```lang
// std/net.lang
include "std/libc.lang"  // raw extern declarations

pub struct TcpListener {
    fd i32;
}

pub func tcp_listen(port u16) TcpListener {
    var listener TcpListener;
    listener.fd = socket(AF_INET, SOCK_STREAM, 0);
    // ... bind, listen
    return listener;
}

pub func tcp_accept(listener *TcpListener) i32 {
    return accept(listener.fd, 0, 0);
}
```

### Phase 3: Zig Bridge (If We Want More)

For TLS, async, HTTP parsing - link Zig runtime:

```lang
include "std/zig_http.lang"

func main() i64 {
    var server *u8 = zig_http_server(8080);

    while true {
        var req *u8 = zig_http_accept(server);
        var path *u8 = zig_http_path(req);

        if streq(path, "/") {
            zig_http_respond(req, 200, "Hello, World!");
        } else {
            zig_http_respond(req, 404, "Not Found");
        }
    }
}
```

---

## What About "Bring Your Own Stdlib"?

The original vision from ast_as_language.md:

> Readers choose memory model by which stdlib they include

This still works with the hybrid approach:
- Reader for GC'd language includes `std/gc/tracing.lang`
- Reader for manual memory includes `std/core.lang`
- Reader for Zig-style includes `std/zig.lang`

The kernel doesn't care. It just compiles AST.

---

## Decision Matrix

| Approach | Effort | Capability | Portability | Maintenance |
|----------|--------|------------|-------------|-------------|
| Pure lang stdlib | Very High | Limited | High | High (us) |
| libc bindings | Medium | Good | Medium | Low |
| Zig bridge | Medium | Excellent | High | Medium |
| Link whatever | Low | Unlimited | Varies | None |

**Recommendation**:

1. **Now**: Prove libc path works (Phase 1 web server)
2. **Soon**: Clean libc bindings (std/libc.lang, std/net.lang)
3. **Later**: Zig bridge for batteries-included option
4. **Never**: Build our own complete stdlib

The lang project is about **syntax** and **composition**, not about competing with Zig/Rust on stdlib quality. Let those projects do the hard systems work, we provide the frontend magic.

---

## Open Questions

1. **Struct layout compatibility**: Do lang structs match C structs? (Probably yes for simple cases, need to verify padding)

2. **Calling convention edge cases**: Does lang handle varargs? (No - `printf` won't work without changes)

3. **Error handling**: How do we surface errno? Result types? (Need design)

4. **Build system**: How does user specify "link libcurl"? (Could be compiler flag, could be pragma)

5. **Distribution**: If we ship a Zig runtime, how big is it? (Zig can be quite small with careful builds)

---

## Next Steps

1. **Try Phase 1 today** - write the raw libc web server
2. **Document what breaks** - struct layouts? calling conventions?
3. **Decide on std/libc.lang scope** - what functions to include?
4. **Prototype Zig bridge** - can we actually link Zig code?

The goal: by end of polish phase, `lang` can compile a useful web server without heroics.
