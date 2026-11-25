#!/usr/bin/env node
// Final-program limits with the real reader and freshly built Wasm compiler.
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
    let artifact = filename;
    if (compilerWasm && pathname === '/compiler.wasm') artifact = compilerWasm;
    if (compilerWasm && pathname === '/stdlib.json') {
      artifact = path.join(path.dirname(compilerWasm), 'stdlib.json');
    }
    const data = await fs.readFile(artifact);
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
  const errors = [];
  page.on('pageerror', error => errors.push(String(error)));
  await page.goto(`http://127.0.0.1:${server.address().port}/lab.html`);
  await page.waitForFunction(() => !document.querySelector('#compile').disabled);
  await page.evaluate(() => {
    window.readerDeadlineMs = 5000;
    window.programDeadlineMs = 300;
    window.programOutputLimitBytes = 2048;
    window.readerBuilds = 0;
    window.programWorkers = [];
    const compile = window.runLangCompiler;
    window.runLangCompiler = (...args) => {
      if (args[1][0] === 'reader.lang') window.readerBuilds++;
      return compile(...args);
    };
    const NativeWorker = window.Worker;
    window.Worker = class extends NativeWorker {
      constructor(url, ...args) {
        super(url, ...args);
        if (url === 'program_worker.js') {
          this.record = { terminated: false };
          window.programWorkers.push(this.record);
          this.addEventListener('message', event => { this.record.result = event.data; });
        }
      }
      terminate() { if (this.record) this.record.terminated = true; return super.terminate(); }
    };
  });
  const flow = await fs.readFile(path.join(root, 'example/flow/flow.lang'), 'utf8');
  const line = 'compilation-result-for-a-very-long-author-program-name-0123456789 '.repeat(2) + 'é🌿\n';
  const runtime = `include "std/core.lang"
func burst() i64 { print(${JSON.stringify(line)}); return 0; }
func errors() i64 { file_write(2, ${JSON.stringify(line)}, ${Buffer.byteLength(line)}); return 0; }
func stop() i64 { burst(); exit(7); return 0; }
func huge() i64 { print(${JSON.stringify(line.repeat(100))}); return 0; }
func split() i64 {
  var c u8 = 195; file_write(1, &c, 1);
  c = 169; file_write(1, &c, 1); return 0;
}
func interleaved() i64 {
  var c u8 = 195; file_write(1, &c, 1);
  c = 240; file_write(2, &c, 1);
  c = 169; file_write(1, &c, 1);
  c = 159; file_write(2, &c, 1);
  c = 140; file_write(2, &c, 1);
  c = 191; file_write(2, &c, 1); return 0;
}
func malformed() i64 { var c u8 = 255; file_write(1, &c, 1); return 0; }
func incomplete() i64 { var c u8 = 195; file_write(1, &c, 1); return 0; }
func incomplete_exit() i64 { incomplete(); exit(7); return 0; }
`;
  await page.locator('#reader').fill(flow);
  await page.locator('#runtime').evaluate(element => { element.closest('details').open = true; });
  await page.locator('#runtime').fill(runtime);
  const source = page.locator('#custom-source');
  const output = () => page.locator('#output').textContent();
  const run = async (text, status) => {
    await source.fill(text);
    await page.locator('#compile').click();
    await page.waitForFunction(() => !document.querySelector('#compile').disabled);
    assert.match(await page.locator('#status').textContent(), status, await output());
    assert.equal(await source.inputValue(), text);
    assert.equal(await page.locator('#reader').inputValue(), flow);
    assert.equal(await page.locator('#runtime').inputValue(), runtime);
    assert.equal(await page.locator('#download-reader').isVisible(), true);
    assert.equal(await page.locator('#download-ast').isVisible(), true);
    assert.equal(await page.locator('#download-program').isVisible(), true);
    console.log(`checked ${text.slice(0, 70)}: ${await page.locator('#status').textContent()}`);
  };
  const normal = 'func main() { return 42; }';
  await run(normal, /ran/);
  assert.match(await output(), /main\(\) → 42/);
  await page.evaluate(() => { window.savedReader = cachedReaderProgram; });
  const reuse = async () => {
    assert.equal(await page.evaluate(() => cachedReaderProgram === window.savedReader && window.readerBuilds === 1), true);
    assert.equal(await page.evaluate(() => window.programWorkers.every(worker => worker.terminated)), true);
  };
  for (let i = 0; i < 2; i++) {
    await run('func main() { while 1 { } return 0; }', /program run failed/);
    assert.equal(await output(), 'program timed out');
    await reuse();
    await run(normal, /ran/);
    assert.match(await output(), /main\(\) → 42/);
  }
  console.log('PASS infinite programs terminate independently; corrected source reuses identical reader');
  await page.evaluate(() => { window.programDeadlineMs = 5000; });
  // Real compiled byte writes must retain UTF-8 state per output stream, and
  // replacement characters must also fit the combined retained-byte budget.
  for (const [call, limit, expectedOut, expectedErr, failure] of [
    ['split', 2, 'é', '', false],
    ['split', 1, '', '', true],
    ['interleaved', 6, 'é', '🌿', false],
    ['interleaved', 5, 'é', '', true],
    ['malformed', 2, '', '', true],
    ['malformed', 3, '�', '', false],
    ['incomplete', 1, '', '', true],
    ['incomplete', 3, '�', '', false],
    ['incomplete_exit', 1, '', '', true],
    ['incomplete_exit', 3, '�', '', true],
  ]) {
    await page.evaluate(value => { window.programOutputLimitBytes = value; }, limit);
    await run(`func main() { ${call}(); return 42; }`, failure ? /program run failed/ : /ran/);
    const result = await page.evaluate(() => window.programWorkers.at(-1).result);
    assert.equal(result.stdout, expectedOut, `${call} stdout at ${limit} bytes`);
    assert.equal(result.stderr, expectedErr, `${call} stderr at ${limit} bytes`);
    assert.ok(Buffer.byteLength(result.stdout) + Buffer.byteLength(result.stderr) <= limit);
    if (failure) {
      assert.match(await output(), call === 'incomplete_exit' && limit === 3
        ? /^program exited with code 7/ : new RegExp(`^program output truncated at ${limit} bytes`));
    } else assert.equal(result.value, 42n);
    await reuse();
  }
  await page.evaluate(() => { window.programOutputLimitBytes = 2048; });
  console.log('PASS split UTF-8, independent stdout/stderr decoding and bounded malformed/incomplete bytes');
  // Combined stdout/stderr budget, including multibyte text and partial writes.
  await run('func main() { while 1 { burst(); errors(); } return 0; }', /program run failed/);
  const flooded = await output();
  assert.match(flooded, /^program output truncated at 2048 bytes/);
  assert.ok(Buffer.byteLength(flooded.slice(flooded.indexOf('\n\n') + 2)) <= 2048);
  assert.ok(flooded.includes(line.trim()));
  assert.ok(!flooded.includes('�'), 'UTF-8 boundary must not introduce replacement characters');
  await reuse();
  await page.locator('#runtime').evaluate(element => { element.closest('details').open = false; });
  await page.locator('#reader').evaluate(element => { element.scrollTop = 0; });
  for (const width of [390, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    if (evidence) await page.screenshot({ path: path.join(evidence, `program-${width}-bounded.png`), fullPage: true });
  }
  // A single oversized write is capped before decoding or accumulating it.
  await run('func main() { huge(); return 0; }', /program run failed/);
  assert.match(await output(), /^program output truncated at 2048 bytes/);
  assert.ok(Buffer.byteLength((await output()).slice((await output()).indexOf('\n\n') + 2)) <= 2048);
  await page.evaluate(limit => { window.programOutputLimitBytes = limit; }, Buffer.byteLength(line) - 3);
  await run('func main() { burst(); return 42; }', /program run failed/);
  assert.ok(!(await output()).includes('�'), 'cap cuts an emoji without displaying a broken character');
  assert.ok(Buffer.byteLength((await output()).slice((await output()).indexOf('\n\n') + 2)) <= Buffer.byteLength(line) - 3);
  await page.evaluate(limit => { window.programOutputLimitBytes = limit; }, Buffer.byteLength(line));
  await run('func main() { burst(); return 42; }', /ran/);
  assert.ok((await output()).includes(line.trim()), 'exact byte budget must succeed');
  await page.evaluate(() => { window.programOutputLimitBytes = 2048; });
  await run('func main() { stop(); return 0; }', /program run failed/);
  assert.match(await output(), /^program exited with code 7/);
  assert.ok((await output()).includes(line.trim()));
  await run('func main() { errors(); return 42; }', /ran/);
  assert.match(await output(), /main\(\) → 42/);
  assert.ok((await output()).includes(line.trim()));
  console.log('PASS combined byte cap, Unicode truncation, stderr and explicit nonzero exit');
  // A completed worker message can already be queued when cancellation wins.
  await page.evaluate(() => {
    window.originalStartProgram = window.startProgram;
    window.startProgram = (...args) => {
      const task = window.originalStartProgram(...args);
      return { cancel: task.cancel, promise: task.promise.then(async result => {
        window.resultHeld = true;
        await new Promise(resolve => { window.releaseResult = resolve; });
        return result;
      }) };
    };
  });
  await source.fill(normal);
  await page.locator('#compile').click();
  await page.waitForFunction(() => window.resultHeld);
  await page.locator('#cancel-program').click();
  await page.evaluate(() => window.releaseResult());
  await page.waitForFunction(() => !document.querySelector('#compile').disabled);
  assert.equal(await output(), 'program cancelled');
  assert.match(await page.locator('#status').textContent(), /program run failed/);
  await page.evaluate(() => { window.startProgram = window.originalStartProgram; });
  await run(normal, /ran/);
  await reuse();
  // Exercise settled guards even if a terminated worker calls its old handler.
  assert.equal(await page.evaluate(async () => {
    const NativeWorker = window.Worker;
    let fake;
    window.Worker = class {
      constructor() { fake = this; }
      postMessage() {}
      terminate() { this.terminated = true; }
    };
    try {
      const task = startProgram(new Uint8Array(), 1000, 16);
      task.cancel();
      fake.onmessage({ data: { value: 99n, exit: 0, stdout: 'stale', stderr: '' } });
      try { await task.promise; return false; }
      catch (error) { return error.message === 'program cancelled' && fake.terminated; }
    } finally { window.Worker = NativeWorker; }
  }), true);
  assert.equal(await page.evaluate(() => {
    const count = window.programWorkers.length;
    for (const budget of [0, -1, NaN, Infinity, 60001]) {
      try { startProgram(cachedReaderProgram, budget); return false; }
      catch (error) { if (!/deadline/.test(error.message)) return false; }
    }
    for (const limit of [0, -1, 1.5, NaN, Infinity, 1048577]) {
      try { startProgram(cachedReaderProgram, 1000, limit); return false; }
      catch (error) { if (!/output limit/.test(error.message)) return false; }
    }
    return window.programWorkers.length === count;
  }), true);
  // An edit cancels real running code; saved drafts still contain all inputs.
  await source.fill('func main() { while 1 { } return 0; }');
  await page.locator('#compile').click();
  await page.locator('#cancel-program').waitFor({ state: 'visible' });
  await source.fill(normal);
  await page.waitForFunction(() => !document.querySelector('#compile').disabled);
  await run(normal, /ran/);
  await reuse();
  await page.waitForTimeout(200);
  assert.equal(await page.evaluate(() => localStorage.getItem('lang.lab.workspace.source')), normal);
  assert.equal(await page.evaluate(() => localStorage.getItem('lang.lab.workspace.reader')), flow);
  assert.equal(await page.evaluate(() => localStorage.getItem('lang.lab.workspace.runtime')), runtime);
  for (const width of [390, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const count of [0, 1, 8]) {
      await run(`func main() { ${'burst(); '.repeat(count)}return 42; }`, /ran/);
      if (evidence) await page.screenshot({ path: path.join(evidence, `program-${width}-${count}.png`), fullPage: true });
    }
  }
  assert.deepEqual(errors, []);
  console.log('PASS cancellation, late messages, edit recovery, intact drafts, invalid budgets and 390/1440 output');
} finally {
  if (browser) await browser.close();
  await new Promise(resolve => server.close(resolve));
}
