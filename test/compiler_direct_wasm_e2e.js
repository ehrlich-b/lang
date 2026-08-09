#!/usr/bin/env node
'use strict';

const fs = require('fs');
const { runLangCompiler } = require('../web/compiler_host.js');
const { runLangProgram } = require('../web/program_host.js');
const stdlibFiles = JSON.parse(fs.readFileSync('web/stdlib.json', 'utf8'));

const compilerPath = process.argv[2];
if (!compilerPath) {
  console.error('usage: compiler_direct_wasm_e2e.js compiler.wasm');
  process.exit(2);
}

async function compileAndRun(sourcePath) {
  const source = fs.readFileSync(sourcePath, 'utf8');
  const result = await runLangCompiler(
    fs.readFileSync(compilerPath),
    ['input.lang', '-o', 'output.wasm'],
    { ...stdlibFiles, 'input.lang': source },
    undefined,
    { LANGBE: 'wasm' },
  );
  if (result.exit !== 0) {
    process.stderr.write(result.stderr || result.stdout || `compiler exit ${result.exit}\n`);
    process.exit(result.exit || 1);
  }
  const program = result.files.get('output.wasm');
  if (!program) throw new Error('compiler did not write output.wasm');
  const ran = await runLangProgram(program);
  return { ...ran, bytes: program.byteLength };
}

async function compileReaderPipeline(readerPath, readerName, source) {
  return compileReaderSource(fs.readFileSync(readerPath, 'utf8'), readerName, source);
}

async function compileReaderSource(sourceText, readerName, source) {
  const readerSource = `${sourceText}
func main() *u8 { return ${readerName}(${JSON.stringify(source)}); }
`;
  const readerCompile = await runLangCompiler(
    fs.readFileSync(compilerPath),
    ['reader.lang', '-o', 'reader.wasm'],
    { ...stdlibFiles, 'reader.lang': readerSource },
    undefined,
    { LANGBE: 'wasm' },
  );
  if (readerCompile.exit !== 0) {
    throw new Error(readerCompile.stderr || readerCompile.stdout || `reader compiler exit ${readerCompile.exit}`);
  }
  const readerProgram = readerCompile.files.get('reader.wasm');
  if (!readerProgram) throw new Error('compiler did not write reader.wasm');
  const readerRun = await runLangProgram(readerProgram);
  if (readerRun.value === 0n) return { ast: null, readerRun, ran: null };
  const memory = new Uint8Array(readerRun.instance.exports.memory.buffer);
  let end = Number(readerRun.value);
  while (memory[end] !== 0) end++;
  const ast = Buffer.from(memory.subarray(Number(readerRun.value), end)).toString('utf8');

  const programCompile = await runLangCompiler(
    fs.readFileSync(compilerPath),
    ['program.ast', '--from-ast', '-o', 'program.wasm'],
    { 'program.ast': ast },
    undefined,
    { LANGBE: 'wasm' },
  );
  if (programCompile.exit !== 0) {
    throw new Error(programCompile.stderr || programCompile.stdout || `AST compiler exit ${programCompile.exit}`);
  }
  const program = programCompile.files.get('program.wasm');
  if (!program) throw new Error('compiler did not write program.wasm');
  return { ast, ran: await runLangProgram(program) };
}

(async () => {
  const arithmetic = await compileAndRun('test/direct_wasm_e2e.lang');
  if (Number(arithmetic.value) !== 42) throw new Error(`expected 42, got ${arithmetic.value}`);

  const memory = await compileAndRun('test/direct_wasm_memory_e2e.lang');
  if (Number(memory.value) !== 176) throw new Error(`expected 176, got ${memory.value}`);

  const imported = await compileAndRun('test/direct_wasm_import_e2e.lang');
  if (Number(imported.value) !== 17 || imported.stdout !== 'direct import\n') {
    throw new Error(`direct import mismatch: value=${imported.value} stdout=${JSON.stringify(imported.stdout)}`);
  }
  const ast = await compileAndRun('test/direct_wasm_ast_e2e.lang');
  if (Number(ast.value) !== 40) throw new Error(`expected AST builder to start with 40, got ${ast.value}`);

  const reader = await compileReaderPipeline('example/tiny/tiny.lang', 'tiny', 'answer 42');
  if (Number(reader.ran.value) !== 42 || !reader.ast.startsWith('(program ')) {
    throw new Error(`tiny reader pipeline mismatch: value=${reader.ran.value} ast=${reader.ast}`);
  }
  const calc = await compileReaderPipeline('example/calc/calc.lang', 'calc', 'answer 1 + 2 * 3');
  if (Number(calc.ran.value) !== 7 || !calc.ast.includes('(binop + ')) {
    throw new Error(`calc reader pipeline mismatch: value=${calc.ran.value} ast=${calc.ast}`);
  }
  const invalid = await compileReaderPipeline('example/calc/calc.lang', 'calc', 'wat');
  if (invalid.ast !== null || !invalid.readerRun.stderr.includes('expected `answer EXPRESSION`')) {
    throw new Error(`reader failure mismatch: ast=${invalid.ast} stderr=${invalid.readerRun.stderr}`);
  }
  const generated = await compileReaderPipeline(
    'test/direct_wasm_parser_reader.lang', 'parser_tiny', 'answer 42',
  );
  if (Number(generated.ran.value) !== 42 || !generated.ast.startsWith('(program ')) {
    throw new Error(`generated reader mismatch: value=${generated.ran.value} ast=${generated.ast}`);
  }

  const labHtml = fs.readFileSync('web/lab.html', 'utf8');
  const labSource = labHtml.match(/<textarea[^>]*\bid="reader"[^>]*>([\s\S]*?)<\/textarea>/);
  if (!labSource) throw new Error('could not find the reader source in web/lab.html');
  const read = await compileReaderSource(labSource[1], 'read', 'answer 42');
  if (Number(read.ran.value) !== 42 || !read.ast.startsWith('(program ')) {
    throw new Error(`lab read pipeline mismatch: value=${read.ran.value} ast=${read.ast}`);
  }

  console.log(`PASS compiler_direct_wasm_e2e (${arithmetic.bytes}/${memory.bytes}/${imported.bytes}/${ast.bytes}; readers → ${reader.ran.value}/${calc.ran.value}/${generated.ran.value}/${read.ran.value})`);
})().catch((error) => { console.error(error); process.exit(1); });
