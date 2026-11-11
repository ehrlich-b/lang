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
  ['quoted', '"café 🧭"', 'end of input'], ['speculative', 'nope', "'more'"],
  ['eof', '', 'number'], ['stale', 'junk', 'end of input'],
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
for (const name of ['comment-opener', 'comment-open', 'comment-truncated', 'comment-utf8',
                    'comment-leading', 'custom-opener', 'custom-truncated', 'custom-utf8']) {
  const custom = name.startsWith('custom-');
  const file = `${directory}/${name}.read`;
  const source = fs.readFileSync(file, 'utf8');
  const index = source.lastIndexOf(custom ? '<!--' : '/*');
  const token = source.slice(index);
  const start = Buffer.byteLength(source.slice(0, index));
  const end = Buffer.byteLength(source);
  const prefix = source.slice(0, index).split('\n');
  const diagnostic = `diagnostic:${prefix.length}:${Buffer.byteLength(prefix.at(-1)) + 1}: expected ${custom ? '-->' : '*/'}, found unterminated block comment @${start}:${end}`;
  cases.push({ name, file, token, source, start, end, diagnostic,
    reader: custom ? `${directory}/customdiagnostic.lang` : reader,
    extension: 'diagnostic' });
}
cases.push({ name: 'bare-markers', file: `${directory}/comment-open.read`,
  source: fs.readFileSync(`${directory}/comment-open.read`, 'utf8'),
  token: '/', start: 10, end: 11,
  diagnostic: 'diagnostic:1:11: expected end of input, found / @10:11',
  reader: `${directory}/bare.lang` });
const controls = [
  { name: 'closed', source: 'answer 42 /* é🧭 */' },
  { name: 'line-eof', source: 'answer 42 // é🧭' },
  { name: 'custom-closed', source: '<!-- é🧭 --> answer 42 <!-- done -->', reader: `${directory}/customdiagnostic.lang`, extension: 'diagnostic' },
  { name: 'custom-line-eof', source: 'answer 42 # é🧭', reader: `${directory}/customdiagnostic.lang`, extension: 'diagnostic' },
  { name: 'bare', source: 'answer 42', reader: `${directory}/bare.lang`, extension: 'diagnostic' },
];
function nativeDiagnostics() {
  const evidence = fs.mkdtempSync(path.join(process.env.EVIDENCE_DIR || os.tmpdir(), 'diagnostic-bytes-'));
  const receipts = cases.map(c => {
    // The native CLI dispatches by extension; browser source labels are arbitrary.
    const input = path.join(evidence, `${c.name}.${c.extension || 'diagnostic'}`);
    fs.writeFileSync(input, fs.readFileSync(c.file));
    const output = path.join(evidence, `${c.name}.ast`);
    const result = spawnSync(process.env.COMPILER || './out/lang', ['read', c.reader || reader, input, '-o', output], {
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
    const expected = input + c.diagnostic.slice('diagnostic'.length);
    assert(stderr.split('\n').includes(expected), stderr);
    assert(!stderr.includes('\ufffd'), stderr);
    console.log(`PASS ${c.name}: strict UTF-8, exit 1, no AST, ${c.diagnostic}`);
    return { name: c.name, diagnostic: c.diagnostic, start: c.start, end: c.end, exit: result.status, ast: false };
  });
  for (const c of controls) {
    const input = path.join(evidence, `${c.name}.${c.extension || 'diagnostic'}`);
    fs.writeFileSync(input, c.source);
    const result = spawnSync(process.env.COMPILER || './out/lang', ['read', c.reader || reader, input], {
      timeout: 120000, env: { ...process.env, LANGBE: 'llvm', LANG_CACHE: path.join(evidence, 'cache') },
    });
    assert.ifError(result.error);
    assert.equal(result.status, 0, String(result.stderr));
    assert.match(String(result.stdout), /\(program/);
    console.log(`PASS control ${c.name}: usable AST`);
  }
  fs.writeFileSync(path.join(evidence, 'native.json'), JSON.stringify(receipts, null, 2) + '\n');
  return receipts;
}
if (require.main === module) nativeDiagnostics();
module.exports = { cases, controls, reader, nativeDiagnostics };
