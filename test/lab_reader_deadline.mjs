#!/usr/bin/env node
// Real browser contract: run after web/build_compiler.sh; no mocked compiler.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = fileURLToPath(new URL('..', import.meta.url));
const web = path.join(root, 'web');
const evidence = process.env.LAB_EVIDENCE_DIR;
if (evidence) await fs.mkdir(evidence, { recursive: true });
const server = http.createServer(async (req, res) => {
  try {
    const pathname = decodeURIComponent(new URL(req.url, 'http://127.0.0.1').pathname);
    const filename = path.resolve(web, `.${pathname}`);
    if (!filename.startsWith(`${web}${path.sep}`)) throw new Error('invalid path');
    const data = await fs.readFile(filename);
    const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.wasm': 'application/wasm' };
    res.writeHead(200, { 'Content-Type': types[path.extname(filename)] || 'text/plain' });
    res.end(data);
  } catch {
    res.writeHead(404);
    res.end();
  }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
let browser;
try {
  browser = await chromium.launch({ headless: true, args: ['--disable-gpu', '--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  page.setDefaultTimeout(120000);
  await page.goto(`http://127.0.0.1:${server.address().port}/lab.html`);
  await page.waitForFunction(() => !document.querySelector('#compile').disabled);
  await page.evaluate(() => { window.readerDeadlineMs = 300; window.readerBuilds = 0;
    const compile = window.runLangCompiler;
    window.originalCompiler = compile;
    window.runLangCompiler = (...args) => { if (args[1][0] === 'reader.lang') window.readerBuilds++; return compile(...args); };
  });
  const run = async status => {
    await page.locator('#compile').click();
    await page.waitForFunction(() => !document.querySelector('#compile').disabled);
    assert.match(await page.locator('#status').textContent(), status);
  };
  const tiny = await page.locator('#reader').inputValue();
  await page.locator('#reader').fill('reader read(text *u8) *u8 { while true { } return nil; }');
  for (let i = 0; i < 2; i++) {
    await run(/reader run failed/);
    assert.match(await page.locator('#output').textContent(), /timed out/);
    assert.equal(await page.locator('#download-ast').isVisible(), false);
    await page.locator('#custom-source').fill(`edit ${i}`);
  }
  assert.equal(await page.evaluate(() => window.readerBuilds), 1);
  await page.evaluate(() => { window.readerDeadlineMs = 5000; });
  await page.locator('#reader').fill(tiny);
  await page.locator('#custom-source').fill('answer 42');
  await run(/ran/);
  assert.match(await page.locator('#output').textContent(), /main\(\) → 42/);
  const count = await page.evaluate(() => window.readerBuilds);
  await page.locator('#custom-source').fill('answer 43');
  await run(/ran/);
  assert.match(await page.locator('#output').textContent(), /main\(\) → 43/);
  assert.equal(await page.evaluate(() => window.readerBuilds), count);
  // Cancellation must settle before a result can be published, even for valid Wasm.
  assert.equal(await page.evaluate(async () => {
    const task = startReader(cachedReaderProgram, 'answer 42', 2000);
    task.cancel();
    try { await task.promise; return false; } catch (e) { return /cancelled/.test(e.message); }
  }), true);
  await page.locator('#reader').fill('reader read(text *u8) *u8 { while true { } return nil; }');
  await page.locator('#compile').click();
  await page.locator('#cancel-reader').waitFor({ state: 'visible' });
  await page.locator('#cancel-reader').click();
  await page.waitForFunction(() => !document.querySelector('#compile').disabled);
  assert.match(await page.locator('#status').textContent(), /reader run failed/);
  assert.equal(await page.locator('#download-ast').isVisible(), false);
  // Hold a build open while a workspace replaces its source.
  await page.evaluate(() => {
    const compile = window.runLangCompiler;
    window.runLangCompiler = async (...args) => {
      const result = await compile(...args);
      if (args[1][0] === 'reader.lang') {
        window.buildHeld = true;
        await new Promise(resolve => { window.releaseBuild = resolve; });
      }
      return result;
    };
  });
  await page.locator('#reader').fill('reader read(text *u8) *u8 { while true { } return nil; }\n# changed');
  await page.locator('#compile').click();
  await page.waitForFunction(() => window.buildHeld);
  await page.locator('#open-workspace').setInputFiles({
    name: 'workspace.json', mimeType: 'application/json',
    buffer: Buffer.from(JSON.stringify({ format: 'lang-reader-workspace', version: 1, reader: tiny, source: 'answer 42', runtime: '' })),
  });
  await page.waitForFunction(() => document.querySelector('#status').textContent === 'loaded');
  await page.evaluate(() => window.releaseBuild());
  await page.waitForFunction(() => !document.querySelector('#compile').disabled);
  assert.equal(await page.locator('#status').textContent(), 'loaded');
  await page.evaluate(() => { window.runLangCompiler = window.originalCompiler; });
  await run(/ran/);
  assert.match(await page.locator('#output').textContent(), /main\(\) → 42/);
  // Editing with the editor's Enter and Tab handlers must cancel an active run.
  for (const key of ['Enter', 'Tab']) {
    await page.evaluate(() => {
      window.originalStartReader = window.startReader;
      window.startReader = () => {
        let reject;
        const promise = new Promise((_, fail) => { reject = fail; });
        return { promise, cancel() { window.editCancelled = true; reject(new Error('reader cancelled')); } };
      };
      window.editCancelled = false;
    });
    // Restore the normal compiler wrapper without holding the build.
    await page.locator('#compile').click();
    await page.locator('#cancel-reader').waitFor({ state: 'visible' });
    await page.locator('#custom-source').press(key);
    await page.waitForFunction(() => !document.querySelector('#compile').disabled);
    assert.equal(await page.evaluate(() => window.editCancelled), true);
    assert.equal(await page.locator('#download-ast').isVisible(), false);
    await page.evaluate(() => { window.startReader = window.originalStartReader; });
  }
  for (const width of [390, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const lines of [0, 1, 8, 10]) {
      await page.evaluate(n => { showReaderDiagnostics(Array.from({length:n}, (_, i) => `diagnostic ${i}: ${'long-name-'.repeat(12)}`).join('\n')); readerDiagnostics.open = true; }, lines);
      assert.equal(await page.locator('#reader-diagnostics').isVisible(), lines > 0);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      if (lines > 8) assert.match(await page.locator('#reader-diagnostics-label').textContent(), /\+2 more/);
      if (evidence) await page.screenshot({ path: path.join(evidence, `deadline-${width}-${lines}.png`), fullPage: true });
    }
  }
  console.log('deadline, cancellation, reuse, edits and responsive diagnostics passed');
} finally {
  if (browser) await browser.close();
  await new Promise(resolve => server.close(resolve));
}
