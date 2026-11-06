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
      // Match std/tok.lang boundaries: numbers stop before symbols and each
      // operator consumes at most its supported two-character form.
      const atom = source.slice(offset).match(/^(?:[A-Za-z_][A-Za-z_0-9]*|-?[0-9]+)/) ||
        source.slice(offset).match(/^(?:\+\+|--|[+\-*/%!=]=|<<|>>|<=|>=|&&|\|\||[+\-*/%&|^<>=!])/);
      // Native '->' is a field-access token, not an S-expression operator.
      if (!atom || source.startsWith('->', offset)) {
        throw new Error(`unexpected AST token at byte ${encoder.encode(source.slice(0, offset)).length}`);
      }
      offset += atom[0].length;
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
    const symbol = text !== undefined && /^[A-Za-z_][A-Za-z_0-9]*$/.test(text);
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
    if (schema[0] !== role && !(role === 'n' && schema[0] === 'd') &&
        !(role === 'd' && head === 'reader_expr')) return invalid(node);
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

// Decode the same NUL-prefixed RDI1 records as the native compiler. Hosts mint
// source IDs; reader-local names cannot name unrelated files or editor buffers.
function decodeReaderDiagnostics(data, context, onStderr = () => {}) {
  const records = [];
  const text = new TextEncoder().encode(context.text);
  // Each field is exact UTF-8 data, including U+FEFF in source keys.
  const decoder = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true });
  const view = new DataView(data.buffer, data.byteOffset, data.byteLength);
  let pos = 0;
  if (data.length > 1048576) throw new Error('invalid reader diagnostic');
  const boundary = n => n >= 0 && n <= text.length &&
    (n === text.length || text[n] < 128 || text[n] >= 192);
  while (pos < data.length) {
    const plain = pos;
    while (pos < data.length && !(data[pos] === 0 && data[pos + 1] === 82 &&
           data[pos + 2] === 68 && data[pos + 3] === 73 && data[pos + 4] === 49)) pos++;
    if (pos > plain) onStderr(new TextDecoder('utf-8', { ignoreBOM: true }).decode(data.subarray(plain, pos)));
    if (pos === data.length) break;
    pos++; // Printable RDI1 alone never enters the binary record decoder.
    if (data.length - pos < 28) {
      throw new Error('invalid reader diagnostic');
    }
    const fields = Array.from({ length: 6 }, (_, i) => view.getUint32(pos + 4 + i * 4, true));
    const [category, from, to, codeLen, keyLen, messageLen] = fields;
    const size = codeLen + keyLen + messageLen;
    if (category > 1 || !codeLen || codeLen > 256 || !keyLen || keyLen > 4096 ||
        messageLen > 1048576 || size > data.length - pos - 28 ||
        !((from === 0 && to === 0) ||
          (from > 0 && to >= from && boundary(from - 1) && boundary(to - 1)))) {
      throw new Error('invalid reader diagnostic');
    }
    pos += 28;
    const code = decoder.decode(data.subarray(pos, pos += codeLen));
    const key = decoder.decode(data.subarray(pos, pos += keyLen));
    const message = decoder.decode(data.subarray(pos, pos += messageLen));
    // The caller grants the reader name and this input's display path to the
    // same immutable snapshot, including readers that already use that path.
    if ((key !== context.key && key !== context.path) ||
        [code, key, message].some(s => s.includes('\0'))) {
      throw new Error('invalid reader diagnostic');
    }
    const record = { version: 1, code, message, severity: 'error', path: context.path,
      source_id: context.sourceId, category: category ? 'reader' : 'guest',
      span: from && !category ? { start: from - 1, end: to - 1 } : null,
      origin_chain: context.originChain || [] };
    records.push(record);
    onStderr(readerDiagnosticText(record, context.text));
  }
  return records;
}

function readerDiagnosticText(record, text) {
  let location = `${record.path}:`;
  if (record.span) {
    const prefix = new TextEncoder().encode(text).subarray(0, record.span.start);
    const lines = new TextDecoder().decode(prefix).split('\n');
    const column = new TextEncoder().encode(lines[lines.length - 1]).length + 1;
    location += `${lines.length}:${column}:`;
  }
  let message = `${location} ${record.message}`;
  if (record.code === 'reader-syntax' && record.span) {
    message += ` @${record.span.start}:${record.span.end}`;
  }
  return `${message}\n`;
}

async function runLangProgram(wasmBytes, onWrite, inputText, readerContext) {
  let instance = null;
  let heapTop = 0;
  let inputPos = 0;
  let stdout = '';
  let stderr = '';
  const readerChunks = [];
  let readerByteLength = 0;
  let readerOverflow = false;
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
      if (readerContext && number(fdValue) === 2) {
        if (data.length > 1048576 - readerByteLength) readerOverflow = true;
        else { readerChunks.push(data.slice()); readerByteLength += data.length; }
      }
      else emit(decoder.decode(data), number(fdValue) === 2);
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
  let diagnostics = [];
  if (readerContext) {
    try {
      if (readerOverflow) throw new Error('invalid reader diagnostic');
      const readerBytes = new Uint8Array(readerByteLength);
      let offset = 0;
      for (const chunk of readerChunks) { readerBytes.set(chunk, offset); offset += chunk.length; }
      stderr = '';
      diagnostics = decodeReaderDiagnostics(readerBytes, readerContext, text => { stderr += text; });
    } catch {
      diagnostics = [{ version: 1, code: 'reader-diagnostic-invalid', severity: 'error',
        path: readerContext.path, source_id: readerContext.sourceId, span: null,
        message: 'invalid reader diagnostic', category: 'reader', origin_chain: readerContext.originChain || [] }];
      stderr += `${readerContext.path}: invalid reader diagnostic\n`;
    }
    if (diagnostics.length) { value = 0n; exit = 1; }
  }
  return { value, exit, stdout, stderr, instance, diagnostics };
}

if (typeof module !== 'undefined') module.exports = { formatLangAst, runLangProgram, decodeReaderDiagnostics, readerDiagnosticText };
