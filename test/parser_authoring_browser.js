#!/usr/bin/env node
'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { runLangCompiler } = require('../web/compiler_host.js');
const { runLangProgram } = require('../web/program_host.js');

async function verifyBrowser(compilerPath) {
  const compiler = fs.readFileSync(compilerPath);
  const stdlib = JSON.parse(fs.readFileSync('web/stdlib.json', 'utf8'));
  // A host-lexer regression runs as a target program too. This source is a
  // local test input, not an addition to the deployed authoring stdlib bundle.
  const testFiles = { 'src/lexer.lang': fs.readFileSync('src/lexer.lang', 'utf8') };
  const cases = [];
  async function compile(source, filename = 'input.lang', ast = false) {
    const args = [filename];
    if (ast) args.push('--from-ast');
    args.push('-o', 'output.wasm');
    return runLangCompiler(compiler, args, { ...stdlib, ...testFiles, [filename]: source },
      undefined, { LANGBE: 'wasm' });
  }
  for (const filename of ['test/suite/289_parser_recovery.lang', 'test/parser_eof.lang', 'test/parser_literal.lang', 'test/parser_literal_raw.lang', 'test/parser_macro_boundary.lang', 'test/parser_lisp_quote.lang']) {
    const built = await compile(fs.readFileSync(filename, 'utf8'));
    assert.strictEqual(built.exit, 0, built.stderr || built.stdout);
    const ran = await runLangProgram(built.files.get('output.wasm'));
    assert.strictEqual(ran.value, 0n, `${filename}: result ${ran.value}`);
    cases.push({ name: path.basename(filename), value: Number(ran.value) });
  }

  for (const [name, grammar] of [
    ['eof_left_recursion', 'thing = eof thing | number'],
    ['indirect_eof_left_recursion', 'thing = eof other\n other = thing | number'],
    ['empty_literal', "thing = '' thing | number"],
  ]) {
    const cycle = await compile(`include "std/parser_reader.lang"\n#parser{\n ${grammar}\n}\n`);
    assert.notStrictEqual(cycle.exit, 0, 'zero-width EOF recursion must be rejected');
    assert.match(cycle.stderr, name === 'empty_literal'
      ? /#parser:\d+:\d+:.*nonempty literal/
      : /#parser:\d+:\d+:.*non-left-recursive rule/);
    assert.ok(!cycle.files.has('output.wasm'), 'no partial binary on invalid grammar');
    cases.push({ name, diagnostic: cycle.stderr.trim() });
  }

  const source = fs.readFileSync('example/workshop/workshop.lang', 'utf8') + `
func main() *u8 {
    var text *u8 = alloc(65536);
    var length i64 = file_read(0, text, 65535);
    if length < 0 { return nil; }
    *(text + length) = 0;
    return workshop(text);
}
`;
  const builtReader = await compile(source, 'reader.lang');
  assert.strictEqual(builtReader.exit, 0, builtReader.stderr || builtReader.stdout);
  const reader = builtReader.files.get('output.wasm');
  async function read(text) {
    const ran = await runLangProgram(reader, undefined, text);
    if (ran.value === 0n) return { ast: null, stderr: ran.stderr };
    const memory = new Uint8Array(ran.instance.exports.memory.buffer);
    const start = Number(ran.value);
    let end = start;
    while (end < memory.length && memory[end] !== 0) end++;
    return { ast: Buffer.from(memory.subarray(start, end)).toString('utf8'), stderr: ran.stderr };
  }
  const rejected = await read('add ;\nadd word;\nadd 42;');
  assert.strictEqual(rejected.ast, null, 'recovery must not emit partial AST');
  assert.match(rejected.stderr, /^workshop:1:5: expected number, found ;$/m);
  assert.match(rejected.stderr, /^workshop:2:5: expected number, found word$/m);
  assert.strictEqual(rejected.stderr.trim().split('\n').length, 2);
  cases.push({ name: 'two_independent_errors', diagnostic: rejected.stderr.trim(), ast: null });

  const accepted = await read('add 20;\nadd 22;');
  assert.ok(accepted.ast && accepted.ast.includes('(program'), 'corrected source emits shared AST');
  assert.strictEqual(accepted.stderr, '');
  const program = await compile(accepted.ast, 'program.ast', true);
  assert.strictEqual(program.exit, 0, program.stderr || program.stdout);
  const ran = await runLangProgram(program.files.get('output.wasm'));
  assert.strictEqual(ran.value, 42n);
  cases.push({ name: 'fresh_language_ast_run', value: Number(ran.value),
    astBytes: accepted.ast.length, ast: accepted.ast });
  return { backend: 'browser-compiler-to-direct-wasm', cases };
}

if (require.main === module) {
  const compilerPath = process.argv[2] || 'web/compiler.wasm';
  verifyBrowser(compilerPath).then(report => console.log(JSON.stringify(report, null, 2)))
    .catch(error => { console.error(error.stack || error); process.exitCode = 1; });
}

module.exports = { verifyBrowser };
