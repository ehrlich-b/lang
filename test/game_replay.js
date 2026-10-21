#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { runLangProgram } = require('../web/program_host.js');
const { runLangCompiler } = require('../web/compiler_host.js');

async function main() {
  const [wasmPath, compilerPath] = process.argv.slice(2);
  assert(wasmPath, 'usage: node test/game_replay.js program.wasm [compiler.wasm]');
  const bytes = fs.readFileSync(wasmPath);
  const contract = JSON.parse(fs.readFileSync('game-contract.json', 'utf8'));
  const replay = fs.readFileSync(contract.example.input, 'utf8');
  const expected = fs.readFileSync(contract.example.expected_output, 'utf8');
  // One trailing newline is file framing, never a game command.
  assert.equal(replay, 'ddadd\n');
  const input = replay.slice(0, -1);
  const module = await WebAssembly.compile(bytes);
  const exports = WebAssembly.Module.exports(module);
  assert(exports.some(e => e.name === 'main' && e.kind === 'function'));
  assert(exports.some(e => e.name === 'memory' && e.kind === 'memory'));
  assert(WebAssembly.Module.imports(module).every(i => i.module === 'lang'));
  console.log(JSON.stringify({ imports: WebAssembly.Module.imports(module), exports }));

  async function check(program, commands, stdout, exit = 0, stderr = '') {
    const ran = await runLangProgram(program, undefined, commands);
    assert.equal(ran.exit, exit);
    assert.equal(ran.stdout, stdout);
    assert.equal(ran.stderr, stderr);
    return ran;
  }
  await check(bytes, input, expected);
  await check(bytes, input, expected); // Every replay starts from the same state.
  await check(bytes, '', 'tick=0 x=0 score=0\nseek\n');
  await check(bytes, 'aa.', 'tick=0 x=0 score=0\ntick=1 x=0 score=0\ntick=2 x=0 score=0\ntick=3 x=0 score=0\nseek\n');
  await check(bytes, 'ddddd', 'tick=0 x=0 score=0\ntick=1 x=1 score=0\ntick=2 x=2 score=0\ntick=3 x=3 score=1\ntick=4 x=4 score=1\ntick=5 x=4 score=1\ncaught\n');
  await check(bytes, 'q', 'tick=0 x=0 score=0\n', 2, 'use a, d or .\n');
  await check(bytes, 'a'.repeat(16), Array.from({ length: 17 }, (_, i) => `tick=${i} x=0 score=0\n`).join('') + 'seek\n');
  await check(bytes, 'a'.repeat(17), '', 2, 'maximum 16 turns\n');
  for (let i = 0; i <= input.length; i++) {
    const ran = await runLangProgram(bytes, undefined, input.slice(0, i));
    assert.equal(ran.exit, 0);
    assert.equal(ran.stdout, expected.split('\n').slice(0, i + 1).join('\n') + '\n' + (i === 5 ? 'caught\n' : 'seek\n'));
  }
  console.log('PASS game replay: eight boundary/reset cases and six input prefixes');

  if (compilerPath) {
    const compiler = fs.readFileSync(compilerPath);
    const stdlib = JSON.parse(fs.readFileSync('web/stdlib.json', 'utf8'));
    const source = contract.example.source;
    const compiled = await runLangCompiler(compiler, [source, '-o', 'spark.wasm'],
      { ...stdlib, [source]: fs.readFileSync(source, 'utf8') }, undefined, { LANGBE: 'wasm' });
    assert.equal(compiled.exit, 0, compiled.stderr);
    const program = compiled.files.get('spark.wasm');
    assert(program, 'browser compiler must emit the module');
    await check(program, input, expected);
    for (const failure of contract.error_examples) {
      const result = await runLangCompiler(compiler, [failure.source, '-o', 'bad.wasm'],
        { ...stdlib, [failure.source]: fs.readFileSync(failure.source, 'utf8') }, undefined, { LANGBE: 'wasm' });
      assert.equal(result.exit, 1);
      assert(result.stderr.includes(failure.diagnostic), result.stderr);
      assert(!result.files.has('bad.wasm'), 'failure must not emit a module');
      console.log(`PASS browser target diagnostic: ${failure.diagnostic}`);
    }
    console.log('PASS game compiled and replayed by the Wasm-hosted compiler');
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
