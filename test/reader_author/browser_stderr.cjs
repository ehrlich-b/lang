'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { runLangProgram } = require('../../web/program_host.js');
(async () => {
  const wasm = fs.readFileSync(process.argv[2]);
  for (const text of ['plain-stderr', 'legacy-error', 'legacy-exit', 'mixed-stderr', 'plain-malformed']) {
    const context = { key: 'broken', path: '/guest/input.broken', text, sourceId: 7 };
    const result = await runLangProgram(wasm, undefined, text, context);
    if (text === 'plain-stderr') {
      assert.equal(result.stderr, Buffer.concat([Buffer.from('debug é\r\n\0'), Buffer.from([255, 82])]).toString());
      assert.equal(result.diagnostics.length, 0);
    } else if (text.startsWith('legacy-')) {
      assert.equal(result.stderr, 'legacy: lowering failed\n');
      assert.equal(result.diagnostics.length, 0);
    } else {
      assert.equal(result.exit, 1);
      assert.equal(result.diagnostics.length, 1);
      assert.equal(result.diagnostics[0].code, text === 'mixed-stderr' ? 'mixed-error' : 'reader-diagnostic-invalid');
      assert.equal(result.stderr, text === 'mixed-stderr'
        ? 'debug before é\n/guest/input.broken: guest failure\ndebug after é\n'
        : 'debug before é\n/guest/input.broken: invalid reader diagnostic\n');
    }
  }
  console.log('PASS browser plain and mixed stderr, legacy errors, malformed records');
})().catch(error => { console.error(error); process.exitCode = 1; });
