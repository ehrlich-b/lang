#!/usr/bin/env node
'use strict';

// Frozen cross-host examples, not a conformance claim. Build instructions live
// beside cases.json. Compiler receipts must match this checkout and each other.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const { test, after } = require('node:test');
const { runLangCompiler } = require('../web/compiler_host.js');
const { runLangProgram, formatLangAst } = require('../web/program_host.js');
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const hash = file => sha(fs.readFileSync(file));
const corpusPath = process.env.READER_TRANSCRIPT_CORPUS || 'test/reader_target_transcripts/cases.json';
const cases = JSON.parse(fs.readFileSync(corpusPath, 'utf8'));
const names = ['tiny', 'calc', 'forth', 'minilisp', 'c', 'flow', 'minipy'];
assert.equal(cases.length, 21);
assert.equal(new Set(cases.map(c => c.id)).size, 21);
for (const name of names) {
  assert.equal(cases.filter(c => c.reader === name && c.kind === 'positive').length, 2);
  assert.equal(cases.filter(c => c.reader === name && c.kind === 'negative').length, 1);
}
if (process.argv.includes('--check-corpus')) {
  console.log(`PASS frozen corpus: 21 cases, seven readers, sha256=${hash(corpusPath)}`);
} else {
  const native = process.env.COMPILER || './out/lang_next';
  const wasmPath = process.env.COMPILER_WASM || 'web/compiler.wasm';
  const buildReceipt = process.env.COMPILER_RECEIPT || 'out/build-receipt.json';
  const webDir = path.dirname(wasmPath);
  const tmp = fs.mkdtempSync(path.join(process.env.READER_TRANSCRIPT_WORK || os.tmpdir(), 'reader-target-'));
  const env = { ...process.env, LANGBE: 'llvm', LANG_CACHE: path.join(tmp, 'cache') };
  const report = { schema: 1, corpus: hash(corpusPath), cases: [] };
  const readers = new Map();
  let initialized;

  function command(exe, args, options = {}) {
    const result = spawnSync(exe, args, { encoding: 'utf8', timeout: 120000,
      maxBuffer: 32 * 1024 * 1024, env, ...options });
    assert.ifError(result.error);
    assert.equal(result.signal, null, `${exe} crashed: ${result.stderr}`);
    return { stdout: result.stdout, stderr: result.stderr, status: result.status };
  }
  function success(exe, args, options) {
    const result = command(exe, args, options);
    assert.equal(result.status, 0, JSON.stringify({ exe, args, ...result }));
    return result;
  }
  async function initialize() {
    success('python3', ['scripts/build_receipt.py', 'check', '--input', buildReceipt, '--compiler', native]);
    const receipt = JSON.parse(fs.readFileSync(buildReceipt));
    const webReceipt = JSON.parse(fs.readFileSync(path.join(webDir, 'compiler-receipt.json')));
    assert.deepEqual(webReceipt.source, receipt.source, 'browser compiler source differs');
    assert.equal(webReceipt.builder.sha256, hash(native), 'browser builder differs');
    for (const file of ['compiler.wasm', 'stdlib.json']) {
      const item = Object.values(webReceipt.artifacts).find(a => path.basename(a.path) === file);
      assert(item, `missing ${file} receipt`);
      assert.equal(hash(path.join(webDir, file)), item.sha256, `stale ${file}`);
    }
    report.pipeline = Object.fromEntries(['test/reader_target_transcripts.js', 'web/compiler_host.js', 'web/program_host.js', 'std/os.lang'].map(file => [file, hash(file)]));
    report.normalization = 'CRLF to LF; format shared AST; alpha-rename Flow __k/__rv/__send address suffixes consistently before reformatting. Raw output is retained.';
    report.head = success('git', ['rev-parse', 'HEAD']).stdout.trim();
    report.compilers = { native: hash(native), wasm: hash(wasmPath), stdlib: hash(path.join(webDir, 'stdlib.json')) };
    report.sources = receipt.source.inputs;
    report.hosts = { node: process.version, clang: success('clang', ['--version']).stdout };
    report.adapter = 'Rename main to transcript_value; print its integer result and return it. Minilisp uses lisp_to_int.';
    return { compiler: fs.readFileSync(wasmPath), files: JSON.parse(fs.readFileSync(path.join(webDir, 'stdlib.json'))) };
  }
  async function browserCompile(args, extra) {
    const { compiler, files } = await (initialized ||= initialize());
    const result = await runLangCompiler(compiler, args, { ...files, ...extra }, undefined, { LANGBE: 'wasm' });
    return { ...result, status: result.exit };
  }
  function transcript(stage, run) {
    return { stage, stdout: run.stdout, stderr: run.stderr, status: run.status ?? run.exit };
  }
  // No output or diagnostic text is discarded. Only CRLF is normalized when
  // comparing hosts; the report always retains the exact bytes as UTF-8 strings.
  function normalized(run) {
    return { ...run, stdout: run.stdout.replace(/\r\n/g, '\n'), stderr: run.stderr.replace(/\r\n/g, '\n') };
  }
  function comparableAst(name, ast) {
    if (name !== 'flow') return ast;
    // Flow's fl_gensym derives only these three private bindings from node
    // addresses. Alpha-rename atoms, preserving identity and leaving strings,
    // spans, numeric literals and every other symbol untouched.
    const nodes = new Map();
    return formatLangAst(ast.replace(/"(?:\\.|[^"\\])*"|[^\s()]+/g, atom => {
      const match = /^(__k|__rv|__send)([0-9]+)$/.exec(atom);
      if (!match) return atom;
      if (!nodes.has(match[2])) nodes.set(match[2], nodes.size);
      return match[1] + nodes.get(match[2]);
    }));
  }
  async function readerModules(name) {
    if (readers.has(name)) return readers.get(name);
    const readerPath = `example/${name}/${name}.lang`;
    const readerSource = fs.readFileSync(readerPath, 'utf8');
    const source = `${readerSource}\nfunc main() i64 {
    var text *u8 = alloc(4194304);
    var length i64 = 0;
    var chunk i64 = file_read(0, text, 4194303);
    while chunk > 0 {
        length = length + chunk;
        if length >= 4194303 { chunk = 0; }
        else { chunk = file_read(0, text + length, 4194303 - length); }
    }
    if chunk < 0 { return 1; }
    *(text + length) = 0;
    var ast *u8 = ${name}(text);
    if ast == nil { return 1; }
    print(ast);
    return 0;
}\n`;
    const file = path.join(tmp, `${name}-reader.lang`);
    const ll = path.join(tmp, `${name}-reader.ll`);
    const exe = path.join(tmp, `${name}-reader`);
    fs.writeFileSync(file, source);
    success(native, [file, '-o', ll]);
    success('clang', ['-O0', ll, '-o', exe]);
    const compiled = await browserCompile(['reader.lang', '-o', 'reader.wasm'], { 'reader.lang': source });
    assert.equal(compiled.status, 0, compiled.stderr);
    const wasm = compiled.files.get('reader.wasm');
    assert(wasm, 'reader module missing');
    const modules = { exe, wasm, hashes: { source: hash(readerPath), wrapper: sha(source), native: hash(exe), wasm: sha(wasm) } };
    readers.set(name, modules);
    return modules;
  }
  async function runCase(c) {
    await (initialized ||= initialize());
    const modules = await readerModules(c.reader);
    const record = { id: c.id, source: sha(c.source), reader: modules.hashes, hosts: {} };
    report.cases.push(record); // Partial failures also retain evidence.
    const nativeRead = command(modules.exe, [], { input: c.source });
    const wasmRead = await runLangProgram(modules.wasm, undefined, c.source);
    const asts = {};
    for (const [host, read] of [['native', nativeRead], ['wasm', wasmRead]]) {
      record.hosts[host] = { reader: transcript('reader', read) };
      if ((read.status ?? read.exit) === 0) {
        asts[host] = formatLangAst(read.stdout);
        assert(asts[host].startsWith('(program'), 'reader did not emit shared AST');
        record.hosts[host].ast = sha(asts[host]);
      } else {
        assert.equal(read.stdout, '', 'failed reader emitted an AST');
      }
    }
    const comparableReads = [nativeRead, wasmRead].map(read => {
      const value = transcript('reader', read);
      if (value.status === 0) value.stdout = comparableAst(c.reader, formatLangAst(value.stdout));
      return normalized(value);
    });
    assert.deepEqual(...comparableReads, `${c.id}: reader hosts differ`);
    if (asts.native) assert.equal(comparableAst(c.reader, asts.native), comparableAst(c.reader, asts.wasm), `${c.id}: shared AST differs`);
    for (const host of ['native', 'wasm']) {
      const out = record.hosts[host];
      if (!asts[host]) { out.final = out.reader; continue; }
      // Keep the reader artifact intact in the report. The adapter is applied
      // identically to both targets, outside the compiler and reader semantics.
      assert.equal((asts[host].match(/\(func main /g) || []).length, 1);
      const ast = asts[host].replace('(func main ', '(func transcript_value ');
      const call = c.reader === 'minilisp' ? 'lisp_to_int(transcript_value())' : 'transcript_value()';
      const adapter = `include "std/core.lang"\npub func main() i64 { var value i64 = ${call}; print_int(value); print("\\n"); return value; }\n`;
      out.adapter = sha(adapter);
      out.adaptedAst = sha(ast);
      const runtimes = c.reader === 'minilisp' ? ['example/minilisp/lisp_runtime.lang'] : [];
      const args = ['program.ast', '--from-ast', '--ast-source', 'source.' + c.reader];
      for (const runtime of [...runtimes, 'adapter.lang']) args.push('--runtime', runtime);
      const extension = host === 'native' ? 'll' : 'wasm';
      args.push('-o', 'program.' + extension);
      let compiled;
      if (host === 'native') {
        const dir = path.join(tmp, c.id);
        fs.mkdirSync(dir, { recursive: true });
        for (const [name, text] of Object.entries({ 'program.ast': ast, ['source.' + c.reader]: c.source, 'adapter.lang': adapter })) fs.writeFileSync(path.join(dir, name), text);
        // Keep runtime resources relative to the repository; only generated
        // inputs and output names need absolute paths for the native compiler.
        const nativeArgs = args.map(a => ['program.ast', 'source.' + c.reader, 'adapter.lang', 'program.ll'].includes(a) ? path.join(dir, a) : a);
        compiled = command(native, nativeArgs);
        out.compile = transcript('compile', compiled);
        if (compiled.status === 0) {
          const exe = path.join(dir, 'program');
          success('clang', ['-O0', path.join(dir, 'program.ll'), '-o', exe]);
          out.llvm = hash(path.join(dir, 'program.ll'));
          out.module = hash(exe);
          out.final = transcript('program', command(exe, []));
        }
      } else {
        compiled = await browserCompile(args, { 'program.ast': ast, ['source.' + c.reader]: c.source, 'adapter.lang': adapter });
        out.compile = transcript('compile', compiled);
        if (compiled.status === 0) {
          const bytes = compiled.files.get('program.wasm');
          assert(bytes, 'final module missing');
          out.module = sha(bytes);
          out.final = transcript('program', await runLangProgram(bytes));
        }
      }
      if (!out.final) out.final = out.compile;
    }
    for (const host of ['native', 'wasm']) {
      const expected = c.expected[host] || c.expected;
      assert.deepEqual(record.hosts[host].final, expected, `${c.id}: ${host} frozen transcript`);
    }
    if (!c.unsupported) assert.deepEqual(normalized(record.hosts.native.final), normalized(record.hosts.wasm.final), `${c.id}: final hosts differ`);
  }
  if (process.env.READER_TRANSCRIPT_CASE) assert(cases.some(c => c.id === process.env.READER_TRANSCRIPT_CASE), 'unknown case');
  if (process.env.READER_TRANSCRIPT_READER) assert(names.includes(process.env.READER_TRANSCRIPT_READER), 'unknown reader');
  for (const c of cases) {
    if (process.env.READER_TRANSCRIPT_READER && process.env.READER_TRANSCRIPT_READER !== c.reader) continue;
    if (process.env.READER_TRANSCRIPT_CASE && process.env.READER_TRANSCRIPT_CASE !== c.id) continue;
    test(c.id + (c.unsupported ? ' (explicit target rejection)' : ''), { concurrency: false }, () => runCase(c));
  }
  after(() => {
    if (process.env.READER_TRANSCRIPT_REPORT) fs.writeFileSync(process.env.READER_TRANSCRIPT_REPORT, JSON.stringify(report, null, 2) + '\n');
  });
}
