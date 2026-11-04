#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { runLangCompiler } = require('../web/compiler_host.js');

const [compilerPath, outputDir] = process.argv.slice(2);
if (!compilerPath || !outputDir) {
  console.error('usage: compiler_wasm_pointer_index_e2e.js compiler.wasm output-dir');
  process.exit(2);
}

(async () => {
  const compiler = fs.readFileSync(compilerPath);
  const stdlibFiles = JSON.parse(fs.readFileSync(path.join(path.dirname(compilerPath), 'stdlib.json'), 'utf8'));
  fs.mkdirSync(outputDir, { recursive: true });
  const sources = fs.readdirSync('test/suite')
    .filter((name) => /^(28[6-9]|29[01])_pointer_index_.*\.lang$/.test(name))
    .sort();
  if (sources.length !== 6) throw new Error('expected six pointer-index regressions');
  for (const name of sources) {
    const source = fs.readFileSync(path.join('test/suite', name), 'utf8');
    const result = await runLangCompiler(compiler,
      ['input.lang', '-o', 'output.ll'], { ...stdlibFiles, 'input.lang': source });
    if (result.exit !== 0) {
      throw new Error(`${name}: ${result.stderr || result.stdout || result.exit}`);
    }
    const output = result.files.get('output.ll');
    if (!output) throw new Error(`${name}: compiler did not write output.ll`);
    fs.writeFileSync(path.join(outputDir, name.replace(/\.lang$/, '.ll')), output);
  }
})().catch((error) => { console.error(error); process.exit(1); });
