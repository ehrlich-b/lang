#!/usr/bin/env node
'use strict';

const fs = require('fs');
const { runLangCompiler } = require('../web/compiler_host.js');

const compilerPath = process.argv[2];
if (!compilerPath) {
  console.error('usage: compiler_direct_wasm_e2e.js compiler.wasm');
  process.exit(2);
}

(async () => {
  const source = fs.readFileSync('test/direct_wasm_e2e.lang', 'utf8');
  const result = await runLangCompiler(
    fs.readFileSync(compilerPath),
    ['input.lang', '-o', 'output.wasm'],
    { 'input.lang': source },
    undefined,
    { LANGBE: 'wasm' },
  );
  if (result.exit !== 0) {
    process.stderr.write(result.stderr || result.stdout || `compiler exit ${result.exit}\n`);
    process.exit(result.exit || 1);
  }
  const program = result.files.get('output.wasm');
  if (!program) throw new Error('compiler did not write output.wasm');
  const built = await WebAssembly.instantiate(program, {});
  const value = Number(built.instance.exports.main());
  if (value !== 42) throw new Error(`expected main() to return 42, got ${value}`);
  console.log(`PASS compiler_direct_wasm_e2e (${program.byteLength} bytes)`);
})().catch((error) => { console.error(error); process.exit(1); });
