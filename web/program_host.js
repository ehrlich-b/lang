// Runtime for modules emitted by codegen_wasm.lang. Direct-wasm imports use a
// canonical i64 ABI in the "lang" namespace, including pointer values. The
// optional third argument supplies UTF-8 stdin, used by reusable reader Wasm.
'use strict';

async function runLangProgram(wasmBytes, onWrite, inputText) {
  let instance = null;
  let heapTop = 0;
  let inputPos = 0;
  let stdout = '';
  let stderr = '';
  const decoder = new TextDecoder();
  const input = typeof inputText === 'string'
    ? new TextEncoder().encode(inputText)
    : inputText || new Uint8Array();

  const memory = () => instance.exports.memory;
  const bytes = () => new Uint8Array(memory().buffer);
  const number = (value) => Number(value);

  function bump(sizeValue) {
    if (heapTop === 0) {
      const base = instance.exports.__heap_base;
      heapTop = base ? Number(base.value) : 1024 * 1024;
    }
    const size = number(sizeValue) + 16;
    const ptr = (heapTop + 15) & ~15;
    heapTop = ptr + size;
    if (heapTop > memory().buffer.byteLength) {
      memory().grow(Math.ceil((heapTop - memory().buffer.byteLength) / 65536) + 1);
    }
    return ptr;
  }

  class ExitTrap {
    constructor(code) { this.code = number(BigInt(code) & 255n); }
  }

  const emit = (text, isError) => {
    if (isError) stderr += text;
    else stdout += text;
    if (onWrite) onWrite(text, isError);
  };

  const lang = {
    read: (fdValue, ptrValue, countValue) => {
      if (number(fdValue) !== 0) return 0n;
      const count = Math.min(number(countValue), input.length - inputPos);
      if (count <= 0) return 0n;
      bytes().set(input.subarray(inputPos, inputPos + count), number(ptrValue));
      inputPos += count;
      return BigInt(count);
    },
    write: (fdValue, ptrValue, countValue) => {
      const data = bytes().subarray(number(ptrValue), number(ptrValue) + number(countValue));
      emit(decoder.decode(data), number(fdValue) === 2);
      return BigInt(data.length);
    },
    open: () => -1n,
    close: () => 0n,
    stat: () => -1n,
    unlink: () => -1n,
    mkdir: () => -1n,
    rmdir: () => -1n,
    getcwd: () => 0n,
    mmap: (addr, len) => BigInt(bump(len)),
    munmap: () => 0n,
    malloc: (size) => BigInt(bump(size)),
    calloc: (count, size) => BigInt(bump(number(count) * number(size))),
    free: () => {},
    getenv: () => 0n,
    getpid: () => 1n,
    getppid: () => 0n,
    fork: () => -1n,
    execve: () => -1n,
    waitpid: () => -1n,
    pipe: () => -1n,
    dup2: () => -1n,
    exit: (code) => { throw new ExitTrap(code); },
    _exit: (code) => { throw new ExitTrap(code); },
    memcpy: (dstValue, srcValue, countValue) => {
      const dst = number(dstValue), src = number(srcValue), count = number(countValue);
      bytes().copyWithin(dst, src, src + count);
      return dstValue;
    },
    memmove: (dstValue, srcValue, countValue) => {
      const dst = number(dstValue), src = number(srcValue), count = number(countValue);
      bytes().copyWithin(dst, src, src + count);
      return dstValue;
    },
    memset: (dstValue, value, countValue) => {
      bytes().fill(number(value), number(dstValue), number(dstValue) + number(countValue));
      return dstValue;
    },
    printf: () => 0n,
  };

  const built = await WebAssembly.instantiate(wasmBytes, { lang });
  instance = built.instance;
  let value = 0n;
  let exit = 0;
  try {
    const returned = instance.exports.main();
    value = returned === undefined ? 0n : returned;
    exit = number(BigInt(value) & 255n);
  } catch (error) {
    if (error instanceof ExitTrap) exit = error.code;
    else throw error;
  }
  return { value, exit, stdout, stderr, instance };
}

if (typeof module !== 'undefined') module.exports = { runLangProgram };
