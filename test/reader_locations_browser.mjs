#!/usr/bin/env node
// Real browser contract: native reader diagnostics must select the same source
// after a Wasm reader build, then still work when the user clicks the jump.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import locations from './reader_locations.js';
import diagnosticBytes from './reader_diagnostic_bytes.js';

const root = fileURLToPath(new URL('../', import.meta.url));
process.chdir(root);
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE
  ? pathToFileURL(process.env.PLAYWRIGHT_MODULE).href : 'playwright');
const evidence = path.resolve(process.env.EVIDENCE_DIR || 'out/reader-locations');
fs.mkdirSync(evidence, { recursive: true });
const native = locations.nativeLocations();
const webRoot = path.join(root, 'web');
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.wasm': 'application/wasm' };
const server = http.createServer((req, res) => {
  const name = path.resolve(webRoot, '.' + new URL(req.url, 'http://localhost').pathname);
  if (!name.startsWith(webRoot + path.sep)) { res.writeHead(403).end(); return; }
  try {
    res.setHeader('Content-Type', types[path.extname(name)] || 'application/octet-stream');
    res.end(fs.readFileSync(name));
  } catch { res.writeHead(404).end(); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
let browser;
try {
  browser = await chromium.launch({ headless: true, executablePath: process.env.CHROMIUM_PATH,
    args: ['--no-sandbox', '--disable-gpu'] });
  const page = await browser.newPage({ viewport: { width: 1200, height: 850 } });
  const errors = [];
  page.on('pageerror', error => errors.push(String(error)));
  await page.goto(`http://127.0.0.1:${server.address().port}/lab.html`);
  await page.waitForFunction(() => !document.querySelector('#compile').disabled);
  // Exercise the actual starter rather than a separately maintained reader.
  await page.fill('#custom-source', 'answer 42 junk');
  await page.click('#compile');
  await page.waitForFunction(() => !document.querySelector('#compile').disabled, null, { timeout: 120000 });
  assert.match(await page.locator('#output').innerText(), /source\.read:1:11: expected end of input, found junk @10:14/);
  assert.equal(await page.locator('#custom-source').evaluate(el => el.value.slice(el.selectionStart, el.selectionEnd)), 'junk');
  console.log('PASS lab starter: expected end of input, selected complete trailing token');
  const receipts = [];
  async function run() {
    await page.click('#compile');
    await page.waitForFunction(() => !document.querySelector('#compile').disabled, null, { timeout: 120000 });
  }
  async function selection() {
    return page.locator('#custom-source').evaluate(el => ({
      focused: document.activeElement === el,
      start: el.selectionStart, end: el.selectionEnd,
      text: el.value.slice(el.selectionStart, el.selectionEnd),
    }));
  }
  for (const [index, c] of locations.cases.entries()) {
    const source = fs.readFileSync(c.path, 'utf8');
    await page.selectOption('#preset', `${c.name}-error`);
    assert.equal(await page.locator('#custom-source').inputValue(), source);
    await run();
    assert.equal(await page.locator('#status').innerText(), 'reader run failed');
    const diagnostic = await page.locator('#output').innerText();
    assert(diagnostic.split('\n').includes(native[index].diagnostic), diagnostic);
    const selected = await selection();
    assert.equal(selected.focused, true, `${c.name} focus`);
    assert.equal(selected.text, c.selected, `${c.name} token`);
    // Check absolute byte offset independently from the UI's UTF-16 conversion.
    const prefix = source.slice(0, selected.start);
    assert.equal(prefix.split('\n').length, c.line);
    assert.equal(Buffer.byteLength(prefix.split('\n').at(-1)) + 1, c.column);
    assert.equal(await page.locator('#download-ast').isVisible(), false);
    assert.equal(await page.locator('#download-program').isVisible(), false);
    await page.locator('#reader').focus();
    await page.locator('#custom-source').evaluate(el => el.setSelectionRange(0, 0));
    await page.click('#jump-error');
    assert.deepEqual(await selection(), selected, `${c.name} click jump`);
    await page.screenshot({ path: path.join(evidence, `${c.name}.png`), fullPage: true });
    const receipt = { ...native[index], wasmDiagnostic: diagnostic, selection: selected, clickJump: true };
    receipts.push(receipt);
    console.log(`PASS ${c.name}: native = Wasm, selected ${JSON.stringify(selected.text)}, click jump`);
    // Reuse the compiled reader for its existing valid example.
    await page.selectOption('#preset', 'starter');
    await page.selectOption('#preset', c.name);
    await page.fill('#custom-source', {
      c: 'int main() { return 42; }', flow: 'func main() { return 42; }',
      forth: ': main ( -- n ) 42 ;', minilisp: '(defun main () 42)',
      minipy: 'def main():\n    return 42\n',
    }[c.name]);
    await run();
    if (c.name === 'minilisp') {
      // Lisp values are boxed: the program returns a pointer, whose tag and
      // payload must represent 42, just as in compiler_direct_wasm_e2e.js.
      const boxed = await page.evaluate(async () => {
        const bytes = await fetch(document.querySelector('#download-program').href).then(r => r.arrayBuffer());
        const ran = await runLangProgram(bytes);
        const memory = new DataView(ran.instance.exports.memory.buffer);
        return { tag: String(memory.getBigInt64(Number(ran.value), true)),
          value: String(memory.getBigInt64(Number(ran.value) + 8, true)) };
      });
      assert.deepEqual(boxed, { tag: '0', value: '42' });
      receipt.validValue = boxed;
    } else {
      assert.match(await page.locator('#output').innerText(), /main\(\) → 42/);
      receipt.validValue = '42';
    }
    assert.equal(await page.locator('#jump-error').isVisible(), false);
  }
  // The same raw-byte inputs must survive a real Wasm reader and select its
  // exact token, even when UTF-8 bytes and textarea offsets differ.
  const byteNative = diagnosticBytes.nativeDiagnostics();
  const byteReceipts = [];
  await page.fill('#reader', fs.readFileSync(diagnosticBytes.reader, 'utf8'));
  await page.click('#runtime-label');
  await page.fill('#runtime', '');
  for (const [index, c] of diagnosticBytes.cases.entries()) {
    await page.fill('#reader', fs.readFileSync(c.reader || diagnosticBytes.reader, 'utf8'));
    // Populate both result downloads before failure to exercise stale cleanup.
    await page.fill('#custom-source', 'answer 42');
    await run();
    assert.match(await page.locator('#output').innerText(), /main\(\) → 42/);
    for (const id of ['download-ast', 'download-program']) {
      assert.equal(await page.locator(`#${id}`).isVisible(), true);
    }
    await page.fill('#custom-source', c.source);
    await run();
    assert.equal(await page.locator('#status').innerText(), 'reader run failed');
    const diagnostic = await page.locator('#output').innerText();
    assert(diagnostic.split('\n').includes(byteNative[index].diagnostic), diagnostic);
    const selected = await selection();
    assert.equal(selected.focused, true);
    assert.equal(selected.text, c.token, `${c.name}: full token`);
    assert.equal(Buffer.byteLength(c.source.slice(0, selected.start)), c.start);
    assert.equal(Buffer.byteLength(c.source.slice(0, selected.end)), c.end);
    for (const id of ['download-ast', 'download-program']) {
      assert.equal(await page.locator(`#${id}`).isVisible(), false);
      assert.equal(await page.locator(`#${id}`).getAttribute('href'), null);
    }
    await page.locator('#reader').focus();
    await page.locator('#custom-source').evaluate(el => el.setSelectionRange(0, 0));
    await page.click('#jump-error');
    assert.deepEqual(await selection(), selected);
    byteReceipts.push({ ...byteNative[index], wasmDiagnostic: diagnostic, selection: selected, staleDownloadsCleared: true });
    console.log(`PASS ${c.name}: native = Wasm, exact byte span and full token, stale downloads cleared`);
    if (['emoji', 'trailing'].includes(c.name)) {
      for (const width of [390, 1440]) {
        await page.setViewportSize({ width, height: 900 });
        await page.screenshot({ path: path.join(evidence, `${c.name}-${width}.png`), fullPage: true });
      }
    }
  }
  fs.writeFileSync(path.join(evidence, 'diagnostic-bytes.json'), JSON.stringify(byteReceipts, null, 2) + '\n');
  for (const c of diagnosticBytes.controls) {
    await page.fill('#reader', fs.readFileSync(c.reader || diagnosticBytes.reader, 'utf8'));
    await page.fill('#custom-source', c.source);
    await run();
    assert.match(await page.locator('#output').innerText(), /main\(\) → 42/);
    console.log(`PASS control ${c.name}: native = Wasm, return 42`);
  }
  // Compiler diagnostics still target the correct pane, including a byte
  // column after an emoji, and opening a folded runtime pane.
  for (const [label, id] of [['reader.lang', 'reader'], ['source.read', 'custom-source'], ['runtime.lang', 'runtime']]) {
    const result = await page.evaluate(({ label, id }) => {
      const el = document.getElementById(id);
      el.value = '// café 🧭\n/*é🧭*/ bad';
      const column = new TextEncoder().encode('/*é🧭*/ ').length + 1;
      const found = focusDiagnostic(`${label}:2:${column}: error: bad`);
      return { found, focused: document.activeElement === el,
        selected: el.value.slice(el.selectionStart, el.selectionEnd) };
    }, { label, id });
    assert.deepEqual(result, { found: true, focused: true, selected: 'bad' });
  }
  assert.deepEqual(errors, []);
  fs.writeFileSync(path.join(evidence, 'reader-locations.json'), JSON.stringify(receipts, null, 2) + '\n');
  console.log('PASS all five valid reader examples and compiler diagnostic panes');
} finally {
  if (browser) await browser.close();
  await new Promise(resolve => server.close(resolve));
}
