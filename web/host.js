// Browser host for lang-compiled wasm modules — the web twin of
// test/wasm_host.js. Provides the std/os/libc.lang extern surface:
// real write/alloc/exit, stubs for process/file calls.
//
// lang declares externs all-i64 (pointers included), so scalar args arrive as
// BigInt; pointer RETURNS are real i8* (i32 -> js number). varargs (printf)
// lower to a pointer to an arg buffer in linear memory.
'use strict';

// Runs a lang wasm module. onWrite(text, isStderr) receives output as it
// happens. Returns {exit, trapped}.
async function runLangWasm(wasmBytes, onWrite) {
  let instance = null;
  let heapTop = 0;

  const mem = () => new Uint8Array(instance.exports.memory.buffer);

  const cstr = (ptr) => {
    const m = mem();
    let end = ptr;
    while (m[end] !== 0) end++;
    return new TextDecoder().decode(m.subarray(ptr, end));
  };

  function bump(size) {
    // +512 slop per allocation, mirroring native malloc bucket behavior
    size = Number(size) + 512;
    const memory = instance.exports.memory;
    if (heapTop === 0) {
      const hb = instance.exports.__heap_base;
      heapTop = hb ? Number(hb.value) : memory.buffer.byteLength;
    }
    const ptr = (heapTop + 15) & ~15;
    heapTop = ptr + size;
    if (heapTop > memory.buffer.byteLength) {
      const pages = Math.ceil((heapTop - memory.buffer.byteLength) / 65536) + 16;
      memory.grow(pages);
    }
    return ptr;
  }

  class ExitTrap { constructor(code) { this.code = Number(BigInt(code) & 255n); } }

  const env = {
    read: () => 0n,
    write: (fd, buf, count) => {
      const n = Number(count), p = Number(buf);
      onWrite(new TextDecoder().decode(mem().subarray(p, p + n)), Number(fd) === 2);
      return BigInt(n);
    },
    open: () => -1n,
    close: () => 0n,
    mmap: (addr, len) => bump(len),
    munmap: () => 0n,
    malloc: (size) => bump(size),
    calloc: (n, size) => bump(Number(n) * Number(size)),
    free: () => {},
    exit: (code) => { throw new ExitTrap(code); },
    _exit: (code) => { throw new ExitTrap(code); },
    getpid: () => 1n,
    getppid: () => 0n,
    getenv: () => 0,
    printf: (fmt, argbuf) => {
      const dv = new DataView(instance.exports.memory.buffer);
      let off = Number(argbuf);
      const s = cstr(Number(fmt)).replace(/%l?[dfg]/g, (spec) => {
        const v = spec.endsWith('d') ? dv.getBigInt64(off, true) : dv.getFloat64(off, true);
        off += 8;
        return String(v);
      });
      onWrite(s, false);
      return BigInt(s.length);
    },
    fork: () => -1n,
    execve: () => -1n,
    waitpid: () => -1n,
    pipe: () => -1n,
    dup2: () => -1n,
    stat: () => -1n,
    mkdir: () => -1n,
    unlink: () => -1n,
    rmdir: () => -1n,
    getcwd: () => 0,
    memcpy: (d, s, n) => { mem().copyWithin(d, s, s + n); return d; },
    memmove: (d, s, n) => { mem().copyWithin(d, s, s + n); return d; },
    memset: (d, c, n) => { mem().fill(c, d, d + n); return d; },
  };

  const { instance: inst } = await WebAssembly.instantiate(wasmBytes, { env });
  instance = inst;
  try {
    if (instance.exports.__wasm_call_ctors) instance.exports.__wasm_call_ctors();
    const ret = instance.exports.main(0n, 0, 0);
    return { exit: Number(BigInt(ret) & 255n), trapped: false };
  } catch (e) {
    if (e instanceof ExitTrap) return { exit: e.code, trapped: false };
    if (e instanceof WebAssembly.RuntimeError) return { exit: 139, trapped: true };
    throw e;
  }
}
