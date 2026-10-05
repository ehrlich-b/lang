#!/usr/bin/env node
'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { performance } = require('perf_hooks');
const { runLangCompiler } = require('../web/compiler_host.js');
const { runLangProgram } = require('../web/program_host.js');

const cases = [
  ['test/suite/156_local_array_literal.lang', 42],
  ['test/suite/250_arrays.lang', 150],
  ['test/suite/251_array_literals.lang', 42],
  ['test/suite/252_array_narrow_assignment.lang', 42],
  ['test/direct_wasm_arrays.lang', 42],
  ['test/parser_array_length.lang', 0],
];

const rejectedLengths = [
  ['decimal-length', '1.5', 'array length must be an integer literal'],
  ['integral-float-length', '15.0', 'array length must be an integer literal'],
  ['negative-length', '-1', 'array length must be an integer literal'],
  ['symbol-length', 'size', 'array length must be an integer literal'],
  ['empty-length', '', 'array length must be an integer literal'],
  ['overflow-length', '9223372036854775808', 'array length exceeds i64 range'],
  ['wraparound-length', '18446744073709551631', 'array length exceeds i64 range'],
];

const rejectedCases = [
  ['zero-length', 'var a [0]i64;', 'length must be between 1 and 8192'],
  ['large-length', 'var a [8193]i64;', 'length must be between 1 and 8192'],
  ['nested-array', 'var a [2][2]i64;', 'require scalar or pointer elements'],
  ['long-literal', 'var a [1]i64 = [1, 2];', 'more elements than its declared length'],
  ['array-copy', 'var a [2]i64 = [1]; var b [2]i64 = a;', 'initializer must be an array literal'],
  ['array-assignment', 'var a [2]i64 = [1]; var b [2]i64 = [2]; a = b;', 'whole-array assignment is unsupported'],
  ['float-index', 'var a [2]i64 = [1]; return a[0.5];', 'index must be an integer'],
];

async function checkStackGuard(module) {
  // This fixture has no host calls; direct instantiation keeps the trapped
  // instance available so static bytes can be inspected afterwards.
  const { instance } = await WebAssembly.instantiate(module, {});
  const memory = new Uint8Array(instance.exports.memory.buffer);
  const matches = [];
  for (let i = 1024; i < 1024 * 1024 - 1; i++) {
    if (memory[i] === 65 && memory[i + 1] === 66) matches.push(i);
  }
  assert.strictEqual(matches.length, 1, 'unique mutable anchor segment');
  const offset = matches[0];
  let trap = null;
  try { instance.exports.main(); } catch (error) { trap = error; }
  assert.ok(trap instanceof WebAssembly.RuntimeError, 'recursive resource probe must trap');
  assert.match(trap.message, /unreachable/);
  assert.deepStrictEqual(Array.from(memory.subarray(offset, offset + 2)), [65, 66],
    'guard must trap before overwriting static data');
  return { trap: trap.message, anchorOffset: offset, anchorAfterTrap: [65, 66] };
}

async function verifyBrowser(compilerPath) {
  const compiler = fs.readFileSync(compilerPath);
  const stdlib = JSON.parse(fs.readFileSync('web/stdlib.json', 'utf8'));
  // Compiler source is input to one local parser regression, not a deployed
  // stdlib addition. This executes the same parser code as an ordinary program.
  const testFiles = {};
  for (const filename of ['src/parser.lang', 'src/lexer.lang', 'src/limits.lang']) {
    testFiles[filename] = fs.readFileSync(filename, 'utf8');
  }
  const receipts = [];
  async function compile(source, filename) {
    const start = performance.now();
    const result = await runLangCompiler(compiler, [filename, '-o', 'output.wasm'],
      { ...stdlib, ...testFiles, [filename]: source }, undefined, { LANGBE: 'wasm' });
    return { ...result, milliseconds: performance.now() - start };
  }
  for (const [filename, expected] of cases) {
    const built = await compile(fs.readFileSync(filename, 'utf8'), filename);
    assert.strictEqual(built.exit, 0, built.stderr || built.stdout);
    const module = built.files.get('output.wasm');
    assert.ok(WebAssembly.validate(module), `${filename}: valid binary`);
    const start = performance.now();
    const ran = await runLangProgram(module);
    assert.strictEqual(ran.value, BigInt(expected), `${filename}: ${ran.stderr}`);
    receipts.push({ case: path.basename(filename), value: expected, bytes: module.length,
      compileMilliseconds: built.milliseconds, runMilliseconds: performance.now() - start });
  }
  for (const [name, body, message] of rejectedCases) {
    const filename = `bad-${name}.lang`;
    const built = await compile(`func main() i64 { ${body} return 42; }\n`, filename);
    assert.notStrictEqual(built.exit, 0, `${name}: invalid source accepted`);
    assert.ok(built.stderr.includes(message), built.stderr);
    assert.ok(built.stderr.includes(`${filename}:1:`), built.stderr);
    assert.ok(!built.files.has('output.wasm'), 'rejected source must leave no partial binary');
    receipts.push({ case: name, rejected: true, diagnostic: built.stderr.trim() });
  }
  for (const [name, length, message] of rejectedLengths) {
    const filename = `bad-${name}.lang`;
    const built = await compile(`func main() i64 {\n    var a [${length}]i64;\n    return 42;\n}\n`, filename);
    assert.ok(built.exit > 0, `${name}: invalid source accepted or trapped`);
    assert.ok(built.stderr.includes(message), built.stderr);
    assert.ok(built.stderr.includes(`${filename}:2:12:`), built.stderr);
    assert.ok(!built.files.has('output.wasm'), 'invalid extent emitted a partial module');
    receipts.push({ case: name, rejected: true, diagnostic: built.stderr.trim() });
  }
  const guardSource = 'test/direct_wasm_array_stack_guard.lang';
  const guard = await compile(fs.readFileSync(guardSource, 'utf8'), guardSource);
  assert.strictEqual(guard.exit, 0, guard.stderr || guard.stdout);
  receipts.push({ case: 'recursive-frame-static-guard',
    ...await checkStackGuard(guard.files.get('output.wasm')) });
  return { backend: 'browser-compiler-to-direct-wasm', receipts };
}

if (require.main === module) {
  verifyBrowser(process.argv[2] || 'web/compiler.wasm')
    .then(result => console.log(JSON.stringify(result, null, 2)))
    .catch(error => { console.error(error.stack || error); process.exitCode = 1; });
}

module.exports = { cases, rejectedCases, rejectedLengths, checkStackGuard, verifyBrowser };
