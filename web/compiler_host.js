// Browser host for compiler.wasm. It supplies argv, environment variables, and
// a tiny in-memory filesystem, then returns every file the compiler wrote.
'use strict';

async function runLangCompiler(wasmBytes, args, initialFiles, onWrite) {
  const encoder = new TextEncoder();
  const decoder = new TextDecoder();
  const files = new Map();
  for (const [path, value] of Object.entries(initialFiles || {})) {
    files.set(path, typeof value === 'string' ? encoder.encode(value) : new Uint8Array(value));
  }

  let instance = null;
  let heapTop = 0;
  let nextFd = 3;
  const fds = new Map();
  const output = { stdout: '', stderr: '' };
  const envStrings = new Map();

  const memory = () => instance.exports.memory;
  const bytes = () => new Uint8Array(memory().buffer);
  const view = () => new DataView(memory().buffer);
  const number = (value) => Number(value);

  function cstr(ptrValue) {
    const ptr = number(ptrValue);
    const mem = bytes();
    let end = ptr;
    while (end < mem.length && mem[end] !== 0) end++;
    return decoder.decode(mem.subarray(ptr, end));
  }

  function bump(sizeValue) {
    const size = number(sizeValue) + 512;
    if (heapTop === 0) {
      const heapBase = instance.exports.__heap_base;
      heapTop = heapBase ? Number(heapBase.value) : memory().buffer.byteLength;
    }
    const ptr = (heapTop + 15) & ~15;
    heapTop = ptr + size;
    if (heapTop > memory().buffer.byteLength) {
      const pages = Math.ceil((heapTop - memory().buffer.byteLength) / 65536) + 16;
      memory().grow(pages);
    }
    return ptr;
  }

  function putString(text) {
    const data = encoder.encode(text);
    const ptr = bump(data.length + 1);
    bytes().set(data, ptr);
    bytes()[ptr + data.length] = 0;
    return ptr;
  }

  function appendFile(path, data) {
    const old = files.get(path) || new Uint8Array();
    const joined = new Uint8Array(old.length + data.length);
    joined.set(old);
    joined.set(data, old.length);
    files.set(path, joined);
  }

  class ExitTrap {
    constructor(code) { this.code = number(BigInt(code) & 255n); }
  }

  const emit = (text, isErr) => {
    if (isErr) output.stderr += text;
    else output.stdout += text;
    if (onWrite) onWrite(text, isErr);
  };

  const env = {
    read: (fdValue, ptrValue, countValue) => {
      const fd = number(fdValue);
      if (fd === 0) return 0n;
      const entry = fds.get(fd);
      if (!entry || entry.write) return -1n;
      const data = files.get(entry.path) || new Uint8Array();
      const count = Math.min(number(countValue), data.length - entry.pos);
      if (count <= 0) return 0n;
      bytes().set(data.subarray(entry.pos, entry.pos + count), number(ptrValue));
      entry.pos += count;
      return BigInt(count);
    },
    write: (fdValue, ptrValue, countValue) => {
      const fd = number(fdValue);
      const count = number(countValue);
      const data = bytes().slice(number(ptrValue), number(ptrValue) + count);
      if (fd === 1 || fd === 2) {
        emit(decoder.decode(data), fd === 2);
      } else {
        const entry = fds.get(fd);
        if (!entry || !entry.write) return -1n;
        appendFile(entry.path, data);
      }
      return BigInt(count);
    },
    open: (pathValue, flagsValue) => {
      const path = cstr(pathValue);
      const write = number(flagsValue) !== 0;
      if (!write && !files.has(path)) return -1n;
      if (write) files.set(path, new Uint8Array());
      const fd = nextFd++;
      fds.set(fd, { path, pos: 0, write });
      return BigInt(fd);
    },
    close: (fdValue) => { fds.delete(number(fdValue)); return 0n; },
    stat: (pathValue, statPtrValue) => {
      if (!files.has(cstr(pathValue))) return -1n;
      view().setBigInt64(number(statPtrValue) + 88, 1n, true);
      return 0n;
    },
    unlink: (pathValue) => { files.delete(cstr(pathValue)); return 0n; },
    mkdir: () => 0n,
    rmdir: () => 0n,
    getcwd: () => 0,
    mmap: (addr, len) => bump(len),
    munmap: () => 0n,
    malloc: (size) => bump(size),
    calloc: (count, size) => bump(number(count) * number(size)),
    free: () => {},
    getenv: (nameValue) => {
      const name = cstr(nameValue);
      const values = { LANGOS: 'wasm', LANGBE: 'llvm' };
      if (!(name in values)) return 0;
      if (!envStrings.has(name)) envStrings.set(name, putString(values[name]));
      return envStrings.get(name);
    },
    printf: (fmtValue, argbufValue) => {
      let offset = number(argbufValue);
      const text = cstr(fmtValue).replace(/%l?[dfg]/g, (spec) => {
        const value = spec.endsWith('d')
          ? view().getBigInt64(offset, true)
          : view().getFloat64(offset, true);
        offset += 8;
        return String(value);
      });
      emit(text, false);
      return BigInt(text.length);
    },
    exit: (code) => { throw new ExitTrap(code); },
    _exit: (code) => { throw new ExitTrap(code); },
    getpid: () => 1n,
    getppid: () => 0n,
    fork: () => -1n,
    execve: () => -1n,
    waitpid: () => -1n,
    pipe: () => -1n,
    dup2: () => -1n,
    memcpy: (dst, src, count) => {
      bytes().copyWithin(number(dst), number(src), number(src) + number(count));
      return dst;
    },
    memmove: (dst, src, count) => {
      bytes().copyWithin(number(dst), number(src), number(src) + number(count));
      return dst;
    },
    memset: (dst, value, count) => {
      bytes().fill(number(value), number(dst), number(dst) + number(count));
      return dst;
    },
  };

  const instantiated = await WebAssembly.instantiate(wasmBytes, { env });
  instance = instantiated.instance;
  if (instance.exports.__wasm_call_ctors) instance.exports.__wasm_call_ctors();

  const argv = ['lang', ...(args || [])];
  const argvPtr = bump(argv.length * 8);
  for (let i = 0; i < argv.length; i++) {
    view().setBigUint64(argvPtr + i * 8, BigInt(putString(argv[i])), true);
  }

  let exit = 0;
  let trapped = false;
  try {
    exit = number(BigInt(instance.exports.main(BigInt(argv.length), BigInt(argvPtr), 0)) & 255n);
  } catch (error) {
    if (error instanceof ExitTrap) exit = error.code;
    else if (error instanceof WebAssembly.RuntimeError) { exit = 139; trapped = true; }
    else throw error;
  }

  return { exit, trapped, files, stdout: output.stdout, stderr: output.stderr };
}

if (typeof module !== 'undefined') module.exports = { runLangCompiler };
