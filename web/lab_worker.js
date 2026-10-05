// Keep untrusted reader and program loops away from the editor's event loop.
'use strict';
importScripts('numeric_host.js?v=workbench11', 'compiler_host.js?v=workbench11', 'program_host.js?v=workbench11');

let compilerBytes;
let stdlibFiles;
let cachedReaderSource;
let cachedReaderProgram;

function readCString(instance, pointer) {
  const memory = new Uint8Array(instance.exports.memory.buffer);
  const start = Number(pointer);
  if (!Number.isSafeInteger(start) || start < 0 || start >= memory.length) throw new Error('reader returned an invalid AST pointer');
  let end = start;
  const limit = Math.min(memory.length, start + 1024 * 1024 + 1);
  while (end < limit && memory[end] !== 0) end++;
  if (end - start > 1024 * 1024) throw new Error('generated AST exceeds the browser limit of 1 MiB');
  if (end === memory.length) throw new Error('reader returned an unterminated AST');
  return new TextDecoder().decode(memory.subarray(start, end));
}

function readerName(source) {
  const matches = [...source.matchAll(/^\s*reader\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(/gm)];
  if (!matches.length) throw new Error('define a reader with `reader name(text *u8)`');
  return matches[matches.length - 1][1];
}

function outputBudget() {
  let length = 0;
  const encoder = new TextEncoder();
  return text => {
    length += encoder.encode(text).length;
    if (length > 1024 * 1024) throw new Error('browser output exceeds the 1 MiB limit');
  };
}

async function compile(args, files) {
  const result = await runLangCompiler(compilerBytes, args, files, outputBudget(), { LANGBE: 'wasm' });
  if (result.exit !== 0) throw new Error(result.stderr || result.stdout || `compiler exit ${result.exit}`);
  return result;
}

async function build(job) {
  const { id, reader, source, runtime } = job;
  const send = data => postMessage({ id, ...data });
  const stage = (phase, state, detail) => send({ type: 'stage', phase, state, detail });
  let phase = 'reader build';
  try {
    for (const [name, text] of Object.entries({ reader, source, runtime })) {
      if (new TextEncoder().encode(text).length > 1024 * 1024) throw new Error(`${name} exceeds the browser workspace limit of 1 MiB`);
    }
    stage(phase, 'running');
    const name = readerName(reader);
    let readerProgram = cachedReaderProgram;
    if (!readerProgram || cachedReaderSource !== reader) {
      const harness = `include "std/core.lang"
include "reader.lang"
func main() *u8 {
    var text *u8 = alloc(4194304);
    var length i64 = 0;
    var chunk i64 = file_read(0, text, 4194303);
    while chunk > 0 {
        length = length + chunk;
        if length >= 4194303 { chunk = 0; }
        else { chunk = file_read(0, text + length, 4194303 - length); }
    }
    if chunk < 0 { return nil; }
    *(text + length) = 0;
    return ${name}(text);
}
`;
      const built = await compile(['lab-harness.lang', '-o', 'reader.wasm'], {
        ...stdlibFiles, 'lab-harness.lang': harness, 'reader.lang': reader,
      });
      readerProgram = built.files.get('reader.wasm');
      if (!readerProgram) throw new Error('reader compiler wrote no module');
      cachedReaderSource = reader;
      cachedReaderProgram = readerProgram;
      stage(phase, 'done', 'reader compiled');
    } else {
      stage(phase, 'done', 'reused · reader unchanged');
    }
    send({ type: 'artifact', kind: 'reader', bytes: readerProgram, name: `${name}-reader.wasm` });

    phase = 'reader run';
    stage(phase, 'running');
    const readerRun = await runLangProgram(readerProgram, outputBudget(), source);
    send({ type: 'artifact', kind: 'tree', text: `${readerRun.stdout}${readerRun.stderr}` });
    if (readerRun.didExit) throw new Error(readerRun.stderr || readerRun.stdout || `reader exited with status ${readerRun.exit}`);
    if (readerRun.value === 0n) throw new Error(readerRun.stderr || readerRun.stdout || 'reader returned nil');
    const ast = readCString(readerRun.instance, readerRun.value);
    const formattedAst = formatLangAst(ast);
    const astBytes = new TextEncoder().encode(formattedAst).length;
    if (astBytes > 1024 * 1024) throw new Error('formatted AST exceeds the browser limit of 1 MiB');
    send({ type: 'artifact', kind: 'ast', text: formattedAst, name: `${name}.ast` });
    stage(phase, 'done', `${astBytes} AST bytes`);

    phase = 'AST compile';
    stage(phase, 'running');
    const args = ['program.ast', '--from-ast', '--ast-source', 'source.read'];
    const files = { ...stdlibFiles, 'program.ast': formattedAst, 'source.read': source };
    if (runtime.trim()) {
      args.push('--runtime', 'runtime.lang');
      files['runtime.lang'] = runtime;
    }
    args.push('-o', 'program.wasm');
    const built = await compile(args, files);
    const program = built.files.get('program.wasm');
    if (!program) throw new Error('kernel wrote no module');
    send({ type: 'artifact', kind: 'program', bytes: program, name: `${name}-program.wasm` });
    stage(phase, 'done', `${program.byteLength} program bytes`);

    phase = 'program run';
    stage(phase, 'running');
    const ran = await runLangProgram(program, outputBudget());
    if (ran.didExit && ran.exit !== 0) throw new Error(`${ran.stdout}${ran.stderr}program exited with status ${ran.exit}`);
    stage(phase, 'done', ran.didExit ? `exit status ${ran.exit}` : `main() → ${ran.value}`);
    send({ type: 'done', value: String(ran.value), stdout: ran.stdout, stderr: ran.stderr, didExit: ran.didExit, exit: ran.exit });
  } catch (error) {
    send({ type: 'error', phase, message: String(error).replace(/^Error: /, '') });
  }
}

onmessage = event => {
  if (event.data.type === 'init') {
    compilerBytes = event.data.compilerBytes;
    stdlibFiles = event.data.stdlibFiles;
  } else if (event.data.type === 'build') {
    build(event.data);
  }
};
