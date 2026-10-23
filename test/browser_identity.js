#!/usr/bin/env node
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { spawnSync } = require('child_process');
const { runLangCompiler } = require('../web/compiler_host.js');
const { runLangProgram } = require('../web/program_host.js');
const compiler = path.resolve(process.env.COMPILER || 'out/lang_next');
const output = process.argv[2];
assert(output, 'usage: browser_identity.js EVIDENCE_DIRECTORY');
fs.mkdirSync(output, { recursive: true });
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const receipt = JSON.parse(fs.readFileSync('web/receipt.json'));
function run(cmd, args, options = {}) {
  const result = spawnSync(cmd, args, { encoding: 'utf8', ...options });
  assert.strictEqual(result.status, 0, `${cmd}: ${result.stderr || result.stdout}`);
  return result.stdout;
}
(async () => {
  assert.strictEqual(receipt.source.dirty, false, 'committed browser artifacts must have clean source');
  run('git', ['merge-base', '--is-ancestor', receipt.source.revision, 'HEAD']);
  for (const [p, hash] of Object.entries(receipt.source.inputs)) assert.strictEqual(sha(fs.readFileSync(p)), hash, `source ${p}`);
  for (const name of ['web/receipt.json', 'web/compiler-receipt.json']) {
    const record = JSON.parse(fs.readFileSync(name));
    assert.deepStrictEqual(record.source, receipt.source);
    for (const [p, item] of Object.entries(record.artifacts)) {
      const bytes = fs.readFileSync(p);
      assert.strictEqual(bytes.length, item.bytes, `bytes ${p}`);
      assert.strictEqual(sha(bytes), item.sha256, `hash ${p}`);
    }
  }
  const bytes = fs.readFileSync('web/compiler.wasm');
  const version = await runLangCompiler(bytes, ['version'], {});
  assert.strictEqual(version.exit, 0);
  assert.strictEqual(version.stdout, `lang 0.1.0 (${receipt.source.revision.slice(0, 7)})\nbuilt: llvm, wasm-wasm32, libc\nbootstrap: from ${receipt.bootstrap.identity}\n`);
  const nativeVersion = run(compiler, ['version']);
  const stdlib = JSON.parse(fs.readFileSync('web/stdlib.json'));
  const rows = [];
  for (const fixture of ['test/direct_wasm_e2e.lang', 'test/direct_wasm_struct_e2e.lang', 'test/direct_wasm_memory_e2e.lang', 'test/direct_wasm_calc_reader_e2e.lang']) {
    const args = [fixture, '-o', path.join(output, path.basename(fixture) + '.wasm')];
    run(compiler, args, {env: {...process.env, LANGBE: 'wasm', LANGOS: 'wasm'}});
    const nativeBytes = fs.readFileSync(args[2]);
    const browser = await runLangCompiler(bytes, [fixture, '-o', 'result.wasm'], {...stdlib, [fixture]: fs.readFileSync(fixture)}, undefined, {LANGBE: 'wasm', LANGOS: 'wasm'});
    assert.strictEqual(browser.exit, 0, browser.stderr);
    const browserBytes = browser.files.get('result.wasm');
    assert(browserBytes, 'browser output missing');
    assert.deepStrictEqual(Buffer.from(browserBytes), nativeBytes, `emission ${fixture}`);
    const a = await runLangProgram(nativeBytes), b = await runLangProgram(browserBytes);
    assert.deepStrictEqual([a.exit, a.stdout, a.stderr], [b.exit, b.stdout, b.stderr]);
    rows.push({fixture, sha256: sha(nativeBytes), exit: a.exit, stdout: a.stdout});
  }
  // Negative fixture: browser and source compiler must both refuse invalid input.
  const bad = 'func main() i64 { return missing_name; }';
  const badPath = path.join(output, 'invalid.lang'); fs.writeFileSync(badPath, bad);
  const nativeBad = spawnSync(compiler, [badPath, '-o', path.join(output, 'invalid.wasm')], {encoding:'utf8', env:{...process.env, LANGBE:'wasm'}});
  const browserBad = await runLangCompiler(bytes, ['invalid.lang', '-o', 'invalid.wasm'], {'invalid.lang': bad}, undefined, {LANGBE:'wasm'});
  assert.notStrictEqual(nativeBad.status, 0); assert.notStrictEqual(browserBad.exit, 0);
  fs.writeFileSync(path.join(output, 'receipt.json'), JSON.stringify({source:receipt.source.revision, version:version.stdout, nativeVersion, artifacts:receipt.artifacts, rows, rejection:{native:nativeBad.status, browser:browserBad.exit}}, null, 2));
  console.log(`PASS browser identity: version, artifact hashes, ${rows.length} byte-for-byte source comparisons and invalid-input refusal`);
})().catch(error => { console.error(error); process.exit(1); });
