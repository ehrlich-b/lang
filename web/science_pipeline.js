// The science page and its Node/browser tests use this identical compiler path.
// JavaScript hosts libc calls and displays CSV; every force and step is Wasm.
'use strict';

(function (scope) {
  const encoder = new TextEncoder();
  const decoder = new TextDecoder();

  class ScienceError extends Error {
    constructor(phase, message, exit) {
      super(message);
      this.phase = phase;
      this.exit = exit;
    }
  }

  function readCString(instance, pointer) {
    const bytes = new Uint8Array(instance.exports.memory.buffer);
    const start = Number(pointer);
    if (!Number.isSafeInteger(start) || start <= 0 || start >= bytes.length) {
      throw new ScienceError('derive forces', 'reader returned an invalid AST pointer');
    }
    let end = start;
    while (end < bytes.length && bytes[end] !== 0) end++;
    if (end === bytes.length) throw new ScienceError('derive forces', 'reader returned an unterminated AST');
    return decoder.decode(bytes.subarray(start, end));
  }

  function generatedFunctions(ast) {
    // Find complete function forms, respecting escaped strings and nested ASTs.
    const functions = [];
    const pattern = /\(func\s+(ham_(?:force_[A-Za-z0-9_]+|potential|step))\b/g;
    let match;
    while ((match = pattern.exec(ast))) {
      let depth = 0, quote = '', end = match.index;
      for (; end < ast.length; end++) {
        const ch = ast[end];
        if (quote) {
          if (ch === '\\') end++;
          else if (ch === quote) quote = '';
        } else if (ch === '"' || ch === "'") quote = ch;
        else if (ch === '(') depth++;
        else if (ch === ')' && --depth === 0) { end++; break; }
      }
      functions.push({ name: match[1], ast: ast.slice(match.index, end) });
      pattern.lastIndex = end;
    }
    return functions;
  }

  function parseScientificCsv(text) {
    const lines = text.trim().split(/\r?\n/);
    if (lines.length < 2) throw new ScienceError('read trajectory', 'solver emitted no complete CSV rows');
    const headers = lines[0].split(',');
    if (new Set(headers).size !== headers.length ||
        headers.some(header => !/^[A-Za-z][A-Za-z0-9_]*$/.test(header))) {
      throw new ScienceError('read trajectory', 'solver emitted an invalid CSV header');
    }
    const rows = lines.slice(1).map((line, index) => {
      const cells = line.split(',');
      if (cells.length !== headers.length || cells.some(cell => cell.trim() === '' || !Number.isFinite(Number(cell)))) {
        throw new ScienceError('read trajectory', `solver emitted an invalid or nonfinite CSV row ${index + 1}`);
      }
      return Object.fromEntries(headers.map((header, column) => [header, Number(cells[column])]));
    });
    return { headers, rows, text };
  }

  function createSciencePipeline(compilerBytes, files, dependencies = {}) {
    const compiler = dependencies.runLangCompiler || scope.runLangCompiler;
    const program = dependencies.runLangProgram || scope.runLangProgram;
    const format = dependencies.formatLangAst || scope.formatLangAst;
    if (!compiler || !program || !format) throw new Error('science compiler hosts are unavailable');
    const readerPath = 'example/hamiltonian/hamiltonian.lang';
    const runtimePath = 'example/hamiltonian/runtime.lang';
    if (!files[readerPath] || !files[runtimePath]) throw new Error('scientific reader assets are missing; reload the complete site bundle');
    let readerBytes;

    async function build(args, input, phase) {
      let result;
      try { result = await compiler(compilerBytes, args, input, undefined, { LANGBE: 'wasm' }); }
      catch (error) { throw new ScienceError(phase, error.message || String(error), error.exit); }
      if (result.exit !== 0) throw new ScienceError(phase,
        result.stderr || result.stdout || `compiler exited ${result.exit}`, result.exit);
      return result;
    }

    async function compileModel(source, progress = () => {}) {
      if (encoder.encode(source).length > 65536) throw new ScienceError('derive forces', 'hamiltonian: source exceeds 65536 bytes');
      const phases = [];
      async function stage(name, action) {
        progress(name);
        const start = performance.now();
        let value;
        try { value = await action(); }
        catch (error) {
          if (error instanceof ScienceError) throw error;
          throw new ScienceError(name, error.message || String(error), error.exit);
        }
        phases.push({ name, milliseconds: performance.now() - start });
        return value;
      }
      if (!readerBytes) {
        readerBytes = await stage('build reader', async () => {
          const harness = `include "${readerPath}"
func main() *u8 {
    var text *u8 = alloc(65537);
    var length i64 = 0;
    var count i64 = file_read(0, text, 65536);
    while count > 0 {
        length = length + count;
        if length >= 65536 { count = 0; }
        else { count = file_read(0, text + length, 65536 - length); }
    }
    if count < 0 { return nil; }
    *(text + length) = 0;
    return ham(text);
}
`;
          const result = await build(['science-reader.lang', '-o', 'science-reader.wasm'],
            { ...files, 'science-reader.lang': harness }, 'build reader');
          const bytes = result.files.get('science-reader.wasm');
          if (!bytes) throw new ScienceError('build reader', 'compiler wrote no reader module');
          return bytes;
        });
      } else phases.push({ name: 'reuse reader', milliseconds: 0 });

      const ast = await stage('derive forces', async () => {
        const result = await program(readerBytes, undefined, source);
        if (result.value === 0n) throw new ScienceError('derive forces',
          result.stderr || result.stdout || 'reader returned no model', result.exit);
        return format(readCString(result.instance, result.value));
      });
      const wasm = await stage('build solver', async () => {
        const result = await build(['experiment.ast', '--from-ast', '--ast-source', 'model.ham',
          '--runtime', runtimePath, '-o', 'experiment.wasm'],
        { ...files, 'experiment.ast': ast, 'model.ham': source }, 'build solver');
        const bytes = result.files.get('experiment.wasm');
        if (!bytes) throw new ScienceError('build solver', 'compiler wrote no experiment module');
        return bytes;
      });
      return { source, ast, functions: generatedFunctions(ast), wasm, readerBytes, phases };
    }

    async function executeModel(model, args, progress) {
      progress(args[0] === '--forces' ? 'inspect forces' : args[0] === '--reverse' ? 'reverse trajectory' : 'run solver');
      const start = performance.now();
      let result;
      try {
        result = await program(model.wasm, undefined, undefined,
          { args, maxOutputBytes: 8 * 1024 * 1024 });
      } catch (error) { throw new ScienceError('run solver', error.message || String(error), error.exit); }
      if (result.exit !== 0) throw new ScienceError('run solver',
        result.stderr || `experiment exited ${result.exit}`, result.exit);
      return { text: result.stdout, milliseconds: performance.now() - start };
    }
    async function runModel(model, args = [], progress = () => {}) {
      const result = await executeModel(model, args, progress);
      return { ...parseScientificCsv(result.text), milliseconds: result.milliseconds };
    }
    async function runJson(model, progress = () => {}) {
      const result = await executeModel(model, ['--json'], progress);
      let document;
      try { document = JSON.parse(result.text); }
      catch (_) { throw new ScienceError('read trajectory', 'solver emitted incomplete trajectory JSON'); }
      if (document.schema !== 'lang.hamiltonian.trajectory.v1' || document.nondimensional !== true ||
          document.method !== 'velocity-verlet' || !Array.isArray(document.coordinates) ||
          !Array.isArray(document.masses) || !Array.isArray(document.samples) ||
          document.coordinates.length < 1 || document.coordinates.length > 4 ||
          new Set(document.coordinates).size !== document.coordinates.length ||
          document.coordinates.some(q => typeof q !== 'string' || !/^[A-Za-z_][A-Za-z0-9_]*$/.test(q)) ||
          document.coordinates.length !== document.masses.length ||
          document.masses.some(m => !Number.isFinite(m) || m <= 0) ||
          !Number.isFinite(document.step_size) || document.step_size <= 0 ||
          !Number.isInteger(document.steps) || document.steps < 1 || document.steps > 1000000 ||
          !Number.isInteger(document.sample_stride) || document.sample_stride < 1 || document.sample_stride > document.steps ||
          document.samples.length < 2) {
        throw new ScienceError('read trajectory', 'solver emitted invalid trajectory JSON metadata');
      }
      let previous = -1;
      for (const sample of document.samples) {
        if (!Number.isInteger(sample.step) || sample.step <= previous ||
            !Number.isFinite(sample.time) || !Number.isFinite(sample.energy) ||
            !Array.isArray(sample.q) || !Array.isArray(sample.p) ||
            sample.q.length !== document.coordinates.length || sample.p.length !== document.coordinates.length ||
            [...sample.q, ...sample.p].some(value => !Number.isFinite(value))) {
          throw new ScienceError('read trajectory', 'solver emitted an invalid JSON state');
        }
        previous = sample.step;
      }
      if (document.samples[0].step !== 0 || document.samples.at(-1).step !== document.steps) {
        throw new ScienceError('read trajectory', 'solver emitted an incomplete JSON trajectory');
      }
      return { ...result, document };
    }
    return { compileModel, runModel, runJson };
  }

  const api = { ScienceError, createSciencePipeline, generatedFunctions, parseScientificCsv };
  if (typeof module !== 'undefined') module.exports = api;
  scope.LangScience = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
