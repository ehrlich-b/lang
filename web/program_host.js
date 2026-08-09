// Runtime for modules emitted by codegen_wasm.lang. Direct-wasm imports use a
// canonical i64 ABI in the "lang" namespace, including pointer values. The
// optional third argument supplies UTF-8 stdin, used by reusable reader Wasm.
'use strict';

// Canonical review form for the shared S-expression AST. This mirrors the
// native `lang read` formatter: tokens are unchanged, insignificant whitespace
// and comments are normalized, and the root always puts declarations on their
// own lines.
function formatLangAst(source) {
  let offset = 0;
  const encoder = new TextEncoder();

  function skipTrivia() {
    let again = true;
    while (again) {
      again = false;
      while (/\s/.test(source[offset] || '')) offset++;
      if (source.startsWith('//', offset)) {
        offset += 2;
        while (offset < source.length && source[offset] !== '\n') offset++;
        again = true;
      } else if (source.startsWith('/*', offset)) {
        const end = source.indexOf('*/', offset + 2);
        if (end < 0) throw new Error('unterminated AST comment');
        offset = end + 2;
        again = true;
      }
    }
  }

  function parseNode() {
    skipTrivia();
    if (source[offset] === '(') {
      offset++;
      const children = [];
      for (;;) {
        skipTrivia();
        if (source[offset] === ')') {
          offset++;
          return { children };
        }
        if (offset >= source.length) throw new Error("expected ')' in AST");
        children.push(parseNode());
      }
    }

    const start = offset;
    const quote = source[offset] === '"' || source[offset] === "'" ? source[offset++] : '';
    if (quote) {
      while (offset < source.length && source[offset] !== quote) {
        if (source[offset] === '\\') offset++;
        offset++;
      }
      if (source[offset] !== quote) throw new Error('unterminated AST string');
      offset++;
    } else {
      while (offset < source.length && !/[\s()]/.test(source[offset])) offset++;
    }
    if (offset === start) throw new Error(`unexpected AST token at byte ${offset}`);
    return { text: source.slice(start, offset) };
  }

  const root = parseNode();
  skipTrivia();
  if (offset !== source.length) throw new Error(`trailing AST input at byte ${offset}`);

  function measure(node) {
    if (node.text !== undefined) {
      node.flat = encoder.encode(node.text).length;
      node.simple = true;
      return node.flat;
    }
    node.simple = node.children.every(child => child.text !== undefined);
    node.flat = 2 + node.children.reduce(
      (width, child, index) => width + measure(child) + (index ? 1 : 0), 0,
    );
    return node.flat;
  }
  measure(root);

  const output = [];
  function emitFlat(node) {
    if (node.text !== undefined) {
      output.push(node.text);
      return;
    }
    output.push('(');
    node.children.forEach((child, index) => {
      if (index) output.push(' ');
      emitFlat(child);
    });
    output.push(')');
  }

  function emitPretty(node, indent, column, forceBreak = false) {
    if (node.text !== undefined) {
      output.push(node.text);
      return column + node.flat;
    }
    if (!forceBreak && column + node.flat <= 88) {
      emitFlat(node);
      return column + node.flat;
    }

    output.push('(');
    if (!node.children.length) {
      output.push(')');
      return column + 2;
    }
    emitFlat(node.children[0]);
    let current = column + 1 + node.children[0].flat;
    let broken = forceBreak;
    const childIndent = indent + 2;
    for (const child of node.children.slice(1)) {
      if (!broken && (child.text !== undefined || child.simple) &&
          current + 1 + child.flat <= 88) {
        output.push(' ');
        emitFlat(child);
        current += 1 + child.flat;
      } else {
        output.push('\n', ' '.repeat(childIndent));
        current = emitPretty(child, childIndent, childIndent);
        broken = true;
      }
    }
    output.push(')');
    return current + 1;
  }

  emitPretty(root, 0, 0, true);
  return output.join('');
}

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

if (typeof module !== 'undefined') module.exports = { formatLangAst, runLangProgram };
