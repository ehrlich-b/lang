#!/usr/bin/env node
// Real browser contract: use the shipped or supplied fresh Wasm compiler.
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
const compilerWasm = process.env.LAB_COMPILER_WASM;
const evidence = process.env.LAB_EVIDENCE_DIR;
if (evidence) await fs.mkdir(evidence, { recursive: true });
const server = http.createServer(async (req, res) => {
  try {
    const pathname = decodeURIComponent(new URL(req.url, 'http://127.0.0.1').pathname);
    const filename = path.resolve(web, `.${pathname}`);
    if (!filename.startsWith(`${web}${path.sep}`)) throw new Error('invalid path');
    const data = await fs.readFile(compilerWasm && pathname === '/compiler.wasm' ? compilerWasm : filename);
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
    window.workerEvents = [];
    const NativeWorker = window.Worker;
    window.Worker = class extends NativeWorker {
      constructor(...args) {
        super(...args);
        this.event = { terminated: false };
        window.workerEvents.push(this.event);
      }
      terminate() { this.event.terminated = true; return super.terminate(); }
    };
    const compile = window.runLangCompiler;
    window.originalCompiler = compile;
    window.runLangCompiler = (...args) => { if (args[1][0] === 'reader.lang') window.readerBuilds++; return compile(...args); };
  });
  const run = async status => {
    await page.locator('#compile').click();
    await page.waitForFunction(() => !document.querySelector('#compile').disabled);
    assert.match(await page.locator('#status').textContent(), status);
  };
  const tiny = await fs.readFile(path.join(root, 'example/tiny/tiny.lang'), 'utf8');
  await page.locator('#reader').fill('reader read(text *u8) *u8 { while true { } return nil; }');
  for (let i = 0; i < 3; i++) {
    await run(/reader run failed/);
    assert.match(await page.locator('#output').textContent(), /timed out/);
    assert.equal(await page.locator('#download-ast').isVisible(), false);
    assert.match(await page.locator('#reader').inputValue(), /while true/);
    assert.equal(await page.locator('#custom-source').inputValue(), i ? `edit ${i - 1}` : 'answer 42');
    await page.locator('#custom-source').fill(`edit ${i}`);
  }
  assert.deepEqual(await page.evaluate(() => window.workerEvents), Array.from({ length: 3 }, () => ({ terminated: true })));
  console.log('three looping readers timed out and terminated; workspace retained');
  assert.equal(await page.evaluate(() => window.readerBuilds), 1);
  await page.evaluate(() => { window.readerDeadlineMs = 5000; });
  await page.locator('#reader').fill(tiny);
  await page.locator('#custom-source').fill('answer 42');
  await run(/ran/);
  assert.match(await page.locator('#output').textContent(), /main\(\) → 42/);
  // A textarea commits its change on blur, after Ctrl+Enter has started the run.
  // Hold worker loading so that focus always moves during reader execution.
  for (const id of ['reader', 'custom-source', 'runtime']) {
    let releaseWorker;
    const workerReady = new Promise(resolve => { releaseWorker = resolve; });
    await page.route('**/reader_worker.js', async route => {
      await workerReady;
      await route.continue();
    });
    await page.evaluate(id => {
      window.blurChanges = 0;
      if (id === 'runtime') document.getElementById(id).closest('details').open = true;
      document.getElementById(id).addEventListener('change', () => window.blurChanges++, { once: true });
    }, id);
    await page.locator(`#${id}`).press('Control+End');
    await page.locator(`#${id}`).press('Space');
    await page.locator(`#${id}`).press('Control+Enter');
    await page.locator('#cancel-reader').waitFor({ state: 'visible' });
    await page.locator(id === 'custom-source' ? '#reader' : '#custom-source').focus();
    assert.equal(await page.evaluate(() => window.blurChanges), 1);
    releaseWorker();
    await page.waitForFunction(() => !document.querySelector('#compile').disabled);
    assert.match(await page.locator('#status').textContent(), /ran/, `${id} blur cancelled the keyboard run`);
    assert.match(await page.locator('#output').textContent(), /main\(\) → 42/);
    assert.equal(await page.locator('#download-ast').isVisible(), true);
    await page.unroute('**/reader_worker.js');
  }
  console.log('Ctrl+Enter followed by blur preserves reader, source and runtime runs');
  const count = await page.evaluate(() => window.readerBuilds);
  await page.locator('#custom-source').fill('answer 43');
  await run(/ran/);
  assert.match(await page.locator('#output').textContent(), /main\(\) → 43/);
  assert.equal(await page.evaluate(() => window.readerBuilds), count);
  console.log('42/43 recovery and source-only reader module reuse passed');
  assert.equal(await page.evaluate(() => {
    const workers = window.workerEvents.length;
    for (const deadline of [0, -1, 60001, NaN, Infinity]) {
      try { startReader(cachedReaderProgram, 'answer 42', deadline); return false; }
      catch (error) { if (!/deadline/.test(error.message)) return false; }
    }
    return window.workerEvents.length === workers;
  }), true, 'invalid deadlines must fail before starting a worker');
  // Deliver an actual successful reader result after cancellation. It must not
  // publish an AST even if termination races with an already completed worker.
  await page.evaluate(() => {
    window.originalStartReader = window.startReader;
    window.startReader = (...args) => {
      const task = window.originalStartReader(...args);
      return {
        cancel: task.cancel,
        promise: task.promise.then(async result => {
          window.resultHeld = true;
          await new Promise(resolve => { window.releaseResult = resolve; });
          return result;
        }),
      };
    };
  });
  await page.locator('#compile').click();
  await page.waitForFunction(() => window.resultHeld);
  await page.locator('#cancel-reader').click();
  await page.evaluate(() => window.releaseResult());
  await page.waitForFunction(() => !document.querySelector('#compile').disabled);
  assert.match(await page.locator('#status').textContent(), /reader run failed/);
  assert.equal(await page.locator('#output').textContent(), 'reader cancelled');
  assert.equal(await page.locator('#download-ast').isVisible(), false);
  await page.evaluate(() => { window.startReader = window.originalStartReader; });
  console.log('late successful reader result cannot publish a cancelled AST');
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
  await page.locator('#custom-source').fill('answer 42');
  await run(/ran/);
  await page.locator('#runtime').evaluate(element => { element.closest('details').open = false; });
  for (const width of [390, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const lines of [0, 1, 8, 10]) {
      await page.evaluate(n => { showReaderDiagnostics(Array.from({length:n}, (_, i) => `diagnostic ${i}: ${'long-name-'.repeat(12)}`).join('\n')); readerDiagnostics.open = true; }, lines);
      assert.equal(await page.locator('#reader-diagnostics').isVisible(), lines > 0);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      if (lines > 8) assert.match(await page.locator('#reader-diagnostics-label').textContent(), /\+2 more/);
      if (lines) assert.equal(await page.locator('#reader-stderr').evaluate(element => {
        const style = getComputedStyle(element);
        const contentHeight = element.clientHeight - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom);
        return contentHeight <= 8 * parseFloat(style.lineHeight) + 1;
      }), true, 'diagnostics exceed eight visible rows');
      if (evidence) await page.screenshot({ path: path.join(evidence, `deadline-${width}-${lines}.png`), fullPage: true });
    }
  }
  console.log('deadline, cancellation, reuse, edits and responsive diagnostics passed');
} finally {
  if (browser) await browser.close();
  await new Promise(resolve => server.close(resolve));
}
