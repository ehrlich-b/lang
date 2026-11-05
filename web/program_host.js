// Runtime for modules emitted by codegen_wasm.lang. Direct-wasm imports use a
// canonical i64 ABI in the "lang" namespace, including pointer values. The
// optional third argument supplies UTF-8 stdin, used by reusable reader Wasm.
'use strict';

// Canonical review form for the shared S-expression AST. This mirrors the
// native `lang read` formatter: tokens are unchanged, insignificant whitespace
// and comments are normalized, and the root always puts declarations on their
// own lines.
const AST_SHAPES = {
  'program': 'g:d*',
  'ast-version': 'z:#',
  'func': 'd:sPto',
  'extern_func': 'd:sPto',
  'var': 'd:sto?',
  'extern_var': 'd:sto?',
  'struct': 'd:sF',
  'enum': 'd:sV',
  'effect': 'd:sTt',
  'reader': 'd:ssn',
  'macro': 'd:sMn',
  'include': 'd:q',
  'require': 'd:q',
  'modules': 'd:q*',
  'param': 'p:st',
  'field_decl': 'f:st',
  'variant_decl': 'v:st?',
  'case': 'c:kn',
  'pattern_wildcard': 'k:',
  'pattern_variant': 'k:sss?',
  'return_handler': 'r:sn',
  'effect_handler': 'h:sssn',
  'type_base': 't:s',
  'type_ptr': 't:t',
  'type_func': 't:Tt',
  'type_closure': 't:Tt',
  'type_array': 't:#t',
  'block': 'n:n*',
  'block_expr': 'n:nn*',
  'array_literal': 'n:n*',
  'if': 'n:nno?',
  'while': 'n:nns?',
  'return': 'n:o?',
  'break': 'n:s?',
  'continue': 'n:s?',
  'expr_stmt': 'n:n',
  'assign': 'n:nn',
  'ident': 'n:s',
  'number': 'n:#',
  'string': 'n:q',
  'bool': 'n:b',
  'nil': 'n:',
  'binop': 'n:ann',
  'unop': 'n:an',
  'int_compare': 'n:stnn',
  'int_convert': 'n:sttn',
  'cast': 'n:tn',
  'bitcast': 'n:tn',
  'call': 'n:nn*',
  'field': 'n:ns',
  'index': 'n:nn',
  'quote': 'n:n',
  'unquote': 'n:s',
  'unquote_string': 'n:s',
  'let': 'n:snn',
  'lambda': 'n:Ptn',
  'match': 'n:nC',
  'perform': 'n:sn*',
  'handle': 'n:nrh*',
  'resume': 'n:no?',
  'reader_expr': 'n:sq',
  'span': 'n:##n',
};

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
    const start = offset;
    if (source[offset] === '(') {
      offset++;
      const children = [];
      for (;;) {
        skipTrivia();
        if (source[offset] === ')') {
          offset++;
          return { children, start, end: offset };
        }
        if (offset >= source.length) throw new Error("expected ')' in AST");
        children.push(parseNode());
      }
    }

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
    return { text: source.slice(start, offset), start, end: offset };
  }

  const root = parseNode();
  skipTrivia();
  if (offset !== source.length) throw new Error(`trailing AST input at byte ${offset}`);

  function invalid(node) {
    const start = encoder.encode(source.slice(0, node.start)).length;
    const end = encoder.encode(source.slice(0, node.end)).length;
    throw new Error(`ast-shape at bytes ${start}:${end}`);
  }

  function validate(node, role) {
    const text = node.text;
    if ((role === 'o' || role === 't') && text === 'nil') return;
    if (role === 'o') role = 'n';
    const symbol = text !== undefined && /^[A-Za-z_][A-Za-z_0-9-]*$/.test(text);
    if (role === 's' && symbol) return;
    if (role === 'a' && (symbol || /^[+*/%&|^<>=!~-]+$/.test(text || ''))) return;
    if (role === 'q' && text !== undefined && (text.startsWith('"') || text.startsWith("'"))) return;
    if (role === '#' && text !== undefined && /^-?[0-9]+$/.test(text)) return;
    if (role === 'b' && (text === 'true' || text === 'false')) return;
    if (!node.children) return invalid(node);
    const children = node.children;
    const element = { P: 'p', T: 't', F: 'f', V: 'v', M: 's', C: 'c' }[role];
    if (element) { children.forEach(child => validate(child, element)); return; }
    const head = children[0]?.text;
    const schema = AST_SHAPES[head];
    if (!schema) return invalid(node);
    if (head === 'span' && (role === 'n' || role === 'd')) {
      if (children.length !== 4) return invalid(node);
      validate(children[1], '#'); validate(children[2], '#');
      validate(children[3], role); return;
    }
    if (schema[0] !== role && !(role === 'n' && schema[0] === 'd')) return invalid(node);
    let signature = schema.slice(2);
    let index = 1;
    if (['func', 'extern_func', 'var', 'extern_var', 'struct', 'enum', 'effect', 'reader'].includes(head) &&
        children[index]?.text === 'pub') index++;
    if (head === 'program' && children[1]?.children?.[0]?.text === 'ast-version') {
      validate(children[1], 'z'); index++;
    }
    if (head === 'let' && children.length === 5) signature = 'stnn';
    for (let pos = 0; pos < signature.length; pos++) {
      const field = signature[pos];
      const repeated = signature[pos + 1] === '*';
      const optional = signature[pos + 1] === '?';
      if (repeated || optional) pos++;
      if (repeated) {
        while (index < children.length) validate(children[index++], field);
      } else if (index < children.length) validate(children[index++], field);
      else if (!optional) return invalid(node);
    }
    if (index !== children.length) invalid(node);
  }
  validate(root, 'g');

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
