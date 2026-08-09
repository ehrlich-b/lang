#!/usr/bin/env node
'use strict';

const fs = require('fs');
const { runLangCompiler } = require('../web/compiler_host.js');

const compilerPath = process.argv[2];
const outputPath = process.argv[3];
if (!compilerPath || !outputPath) {
  console.error('usage: compiler_wasm_e2e.js compiler.wasm output.ll');
  process.exit(2);
}

const source = `var message *u8 = "a";
func main() i64 {
    message = "b";
    return *message;
}
`;

(async () => {
  const result = await runLangCompiler(
    fs.readFileSync(compilerPath),
    ['input.lang', '-o', 'output.ll'],
    { 'input.lang': source },
  );
  if (result.exit !== 0) {
    process.stderr.write(result.stderr || result.stdout || `compiler exit ${result.exit}\n`);
    process.exit(result.exit || 1);
  }
  const output = result.files.get('output.ll');
  if (!output) throw new Error('compiler did not write output.ll');
  fs.writeFileSync(outputPath, output);
})().catch((error) => { console.error(error); process.exit(1); });
