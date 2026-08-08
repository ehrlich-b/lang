#!/usr/bin/env node
// Minimal node host for lang-compiled wasm modules (LANGOS=wasm).
// Provides the std/os/libc.lang extern surface: real write/alloc/exit/printf,
// stubs for the process/file calls that make no sense in a wasm sandbox.
// Usage: node test/wasm_host.js module.wasm  (exit code = main's return & 255)
'use strict';
const fs = require('fs');

const wasmPath = process.argv[2];
if (!wasmPath) { console.error('usage: wasm_host.js module.wasm'); process.exit(2); }
const bytes = fs.readFileSync(wasmPath);

let instance = null;
let heapTop = 0;

const mem = () => new Uint8Array(instance.exports.memory.buffer);

function cstr(ptr) {
  const m = mem();
  let end = ptr;
  while (m[end] !== 0) end++;
  return Buffer.from(m.subarray(ptr, end)).toString('utf8');
}

function bump(size) {
  // Pad like a native malloc's bucket slop: the suite contains benign
  // out-of-bounds writes that libc allocators absorb; a tightly-packed bump
  // allocator would let them corrupt the next allocation instead.
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
  return ptr; // wasm memory is zero-initialized, so calloc semantics come free
}

class ExitTrap { constructor(code) { this.code = code & 255; } }

// lang declares externs all-i64 (pointers included), so scalar args arrive as
// BigInt; pointer RETURNS are real i8* (i32 -> js number). Coerce explicitly.
const env = {
  read: () => 0n,
  write: (fd, buf, count) => {
    const n = Number(count), p = Number(buf);
    const data = Buffer.from(mem().subarray(p, p + n));
    (Number(fd) === 2 ? process.stderr : process.stdout).write(data);
    return BigInt(n);
  },
  open: () => -1n,
  close: () => 0n,
  mmap: (addr, len) => bump(len),
  munmap: () => 0n,
  malloc: (size) => bump(size),
  calloc: (n, size) => bump(Number(n) * Number(size)),
  free: () => {},
  exit: (code) => { throw new ExitTrap(Number(BigInt(code) & 255n)); },
  _exit: (code) => { throw new ExitTrap(Number(BigInt(code) & 255n)); },
  getpid: () => 1n,
  getppid: () => 0n,
  getenv: () => 0,
  printf: (fmt, argbuf) => {
    // printf is varargs; wasm lowers varargs to a pointer to an arg buffer.
    // std/core print_float uses printf("%f\n", val) - read the f64 from there.
    const dv = new DataView(instance.exports.memory.buffer);
    let off = Number(argbuf);
    const s = cstr(Number(fmt)).replace(/%l?[dfg]/g, (spec) => {
      const v = spec.endsWith('d') ? dv.getBigInt64(off, true) : dv.getFloat64(off, true);
      off += 8;
      return String(v);
    });
    process.stdout.write(s);
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

WebAssembly.instantiate(bytes, { env }).then(({ instance: inst }) => {
  instance = inst;
  try {
    if (instance.exports.__wasm_call_ctors) instance.exports.__wasm_call_ctors();
    const ret = instance.exports.main(0n, 0, 0);
    process.exit(Number(BigInt(ret) & 255n));
  } catch (e) {
    if (e instanceof ExitTrap) process.exit(e.code);
    // A wasm trap (bad indirect call, OOB access) is the sandbox's SIGSEGV;
    // report it as 128+11 so segfault-expecting tests mean the same thing here.
    if (e instanceof WebAssembly.RuntimeError) process.exit(139);
    console.error(e);
    process.exit(120);
  }
}).catch((e) => { console.error(e); process.exit(121); });
