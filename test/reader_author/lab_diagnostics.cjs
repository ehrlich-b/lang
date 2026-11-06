'use strict';
// Exercise the actual Lab button handler with its bundled compiler/stdlib and
// with the current source library, without regenerating either web artifact.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const { runLangCompiler } = require('../../web/compiler_host.js');
const { runLangProgram, formatLangAst } = require('../../web/program_host.js');

(async () => {
  const [mode] = process.argv.slice(2);
  const html = fs.readFileSync('web/lab.html', 'utf8');
  const elements = new Map();
  function element(id) {
    if (!elements.has(id)) elements.set(id, {
      value: '', textContent: '', hidden: true, disabled: false,
      addEventListener() {}, removeAttribute() {}, focus() {},
      setSelectionRange(start, end) { this.selection = [start, end]; },
    });
    return elements.get(id);
  }
  element('reader').value = html.match(/<textarea id="reader"[^>]*>([\s\S]*?)<\/textarea>/)[1];
  const bundled = JSON.parse(fs.readFileSync('web/stdlib.json', 'utf8'));
  const stdlib = { ...bundled };
  if (mode === 'current') {
    const paths = spawnSync('git', ['ls-files', '-z', '--', 'std', 'src'], { encoding: 'utf8' }).stdout.split('\0');
    for (const name of paths.filter(name => name.endsWith('.lang'))) {
      stdlib[name] = fs.readFileSync(name, 'utf8');
    }
  }
  const builds = [];
  const runs = [];
  const context = vm.createContext({
    document: { getElementById: element, addEventListener() {} },
    localStorage: { getItem() { return null; }, setItem() {} },
    installCodeEditor() {}, TextEncoder, TextDecoder, Uint8Array, Blob, URL, performance,
    getComputedStyle: () => ({ lineHeight: '20', fontSize: '14' }),
    setTimeout, clearTimeout,
    fetch: async url => ({ ok: true,
      arrayBuffer: async () => fs.readFileSync('web/compiler.wasm'), json: async () => stdlib }),
    runLangCompiler: async (...args) => {
      const result = await runLangCompiler(...args);
      builds.push({ args: args[1], exit: result.exit, stderr: result.stderr });
      return result;
    },
    runLangProgram: async (...args) => {
      const result = await runLangProgram(...args);
      runs.push(result);
      return result;
    },
    formatLangAst,
  });
  vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1], context);
  // Let the local fetch promises and Lab initialization complete.
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(element('compile').disabled, false);
  element('custom-source').value = 'answer 42';
  await element('compile').onclick();
  assert.match(element('output').textContent, /main\(\) → 42/);
  assert.equal(builds.length, 2);
  assert.ok(builds.every(build => build.exit === 0), JSON.stringify(builds));
  const source = '// café\r\nanswer nope';
  element('custom-source').value = source;
  await element('compile').onclick();
  assert.equal(element('output').textContent, 'source.read:2:8: expected number, found nope @17:21\n');
  assert.doesNotMatch(element('output').textContent, /invalid reader diagnostic/);
  assert.equal(element('jump-error').hidden, false);
  assert.deepEqual(element('custom-source').selection, [16, 20]);
  assert.equal(builds.length, 2, 'cached reader should reject before AST compilation');
  const last = runs[runs.length - 1];
  if (mode === 'current') {
    assert.equal(last.diagnostics.length, 1);
    assert.equal(last.diagnostics[0].code, 'reader-syntax');
    assert.equal(last.diagnostics[0].path, 'source.read');
    assert.deepEqual(last.diagnostics[0].span, { start: 17, end: 21 });

    // Compile and invoke a real Lab reader through the bundled Wasm compiler.
    // The same valid range must be rejected when its text is not the input.
    element('reader').value = `reader snapshot(text *u8) *u8 {
      if streq(text, "guest input") {
        reader_error("snapshot", "wrong snapshot", "snapshot", "other input", 0, 5);
      } else {
        reader_error("snapshot", "matching snapshot", "snapshot", text, 0, 5);
      }
      return nil;
    }`;
    element('custom-source').value = 'guest input';
    await element('compile').onclick();
    const mismatch = runs[runs.length - 1].diagnostics;
    assert.equal(mismatch.length, 1);
    assert.equal(mismatch[0].code, 'reader-diagnostic-invalid');
    assert.equal(mismatch[0].category, 'reader');
    assert.equal(mismatch[0].span, null);
    assert.equal(element('jump-error').hidden, true);

    element('custom-source').value = 'other input';
    await element('compile').onclick();
    const matching = runs[runs.length - 1].diagnostics;
    assert.equal(matching.length, 1);
    assert.equal(matching[0].code, 'snapshot');
    assert.equal(matching[0].category, 'guest');
    assert.deepEqual(matching[0].span, { start: 0, end: 5 });
    assert.equal(element('jump-error').hidden, false);
    assert.deepEqual(element('custom-source').selection, [0, 5]);
    console.log(JSON.stringify({ mismatch, matching }));
  }
  console.log(JSON.stringify({ pass: true, mode, builds, message: element('output').textContent,
    diagnostics: last.diagnostics, selection: element('custom-source').selection }));
})().catch(error => { console.error(error); process.exitCode = 1; });
