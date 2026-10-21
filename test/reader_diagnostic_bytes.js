#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const directory = 'test/reader_diagnostic_bytes';
const reader = `${directory}/reader.lang`;
const cases = [
  ['nbsp', '\u00a0', 'number'], ['accent', 'é', 'number'], ['emoji', '🧭', 'number'],
  ['trailing', 'garbage', 'end of input'], ['operator', '++', 'end of input'],
  ['quoted', '"café 🧭"', 'end of input'], ['speculative', '!', 'end of input'],
  ['eof', '', 'number'],
].map(([name, token, expected]) => {
  const file = `${directory}/${name}.read`;
  const source = fs.readFileSync(file, 'utf8');
  const index = token ? source.lastIndexOf(token) : source.length;
  const start = Buffer.byteLength(source.slice(0, index));
  const end = start + Buffer.byteLength(token);
  const prefix = source.slice(0, index).split('\n');
  const line = prefix.length;
  const column = Buffer.byteLength(prefix.at(-1)) + 1;
  const diagnostic = `diagnostic:${line}:${column}: expected ${expected}, found ${token || 'end of input'} @${start}:${end}`;
  return { name, file, token, source, start, end, diagnostic };
});
function nativeDiagnostics() {
  const evidence = fs.mkdtempSync(path.join(process.env.EVIDENCE_DIR || os.tmpdir(), 'diagnostic-bytes-'));
  const receipts = cases.map(c => {
    // The native CLI dispatches by extension; browser source labels are arbitrary.
    const input = path.join(evidence, `${c.name}.diagnostic`);
    fs.writeFileSync(input, fs.readFileSync(c.file));
    const output = path.join(evidence, `${c.name}.ast`);
    const result = spawnSync(process.env.COMPILER || './out/lang', ['read', reader, input, '-o', output], {
      timeout: 120000, env: { ...process.env, LANGBE: 'llvm', LANG_CACHE: path.join(evidence, 'cache') },
    });
    assert.ifError(result.error);
    fs.writeFileSync(path.join(evidence, `${c.name}.stderr`), result.stderr);
    fs.writeFileSync(path.join(evidence, `${c.name}.stdout`), result.stdout);
    const stderr = new TextDecoder('utf-8', { fatal: true }).decode(result.stderr);
    assert.equal(result.signal, null);
    assert.equal(result.status, 1, stderr);
    assert.equal(result.stdout.length, 0);
    assert.equal(fs.existsSync(output), false, `${c.name}: AST emitted`);
    assert(stderr.split('\n').includes(c.diagnostic), stderr);
    assert(!stderr.includes('\ufffd'), stderr);
    console.log(`PASS ${c.name}: strict UTF-8, exit 1, no AST, ${c.diagnostic}`);
    return { name: c.name, diagnostic: c.diagnostic, start: c.start, end: c.end, exit: result.status, ast: false };
  });
  fs.writeFileSync(path.join(evidence, 'native.json'), JSON.stringify(receipts, null, 2) + '\n');
  return receipts;
}
if (require.main === module) nativeDiagnostics();
module.exports = { cases, reader, nativeDiagnostics };
