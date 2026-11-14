#!/usr/bin/env node
// Real Wasm, layout and failure-state checks for the homepage.
// PLAYWRIGHT_MODULE may point at an existing local Playwright installation.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = fileURLToPath(new URL('..', import.meta.url));
const web = path.join(root, 'web');
const evidence = process.env.HOMEPAGE_EVIDENCE_DIR;
if (evidence) await fs.mkdir(evidence, { recursive: true });
const receipt = { checks: [], wasm_sha256: createHash('sha256').update(await fs.readFile(path.join(web, 'examples/polyglot_wasm.wasm'))).digest('hex') };
const server = http.createServer(async (req, res) => {
  try {
    const pathname = new URL(req.url, 'http://127.0.0.1').pathname;
    const file = path.resolve(web, `.${pathname === '/' ? '/index.html' : decodeURIComponent(pathname)}`);
    assert(file.startsWith(web + path.sep));
    const data = await fs.readFile(file);
    const types = { '.html': 'text/html', '.js': 'text/javascript', '.wasm': 'application/wasm', '.json': 'application/json' };
    res.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'text/plain' });
    res.end(data);
  } catch { res.writeHead(404); res.end(); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
let browser;
try {
  browser = await chromium.launch({ headless: true, executablePath: process.env.CHROMIUM_PATH || undefined, args: ['--disable-gpu', '--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, reducedMotion: 'reduce' });
  const errors = [], external = [];
  page.on('pageerror', error => errors.push(String(error)));
  page.on('request', req => { if (!req.url().startsWith(origin + '/')) external.push(req.url()); });
  const text = id => page.locator('#' + id).textContent();
  const waitVisual = pattern => page.waitForFunction(source => new RegExp(source).test(document.getElementById('visual-status').textContent), pattern.source);
  await page.goto(origin);
  await waitVisual(/Ran successfully/);
  assert.deepEqual(await Promise.all(['prime-count', 'prime-sum', 'digit-sum'].map(text)), ['10', '129', '12']);
  assert.deepEqual(await page.locator('#prime-chips span').allTextContents(), ['2', '3', '5', '7', '11', '13', '17', '19', '23', '29']);
  receipt.stdout = await text('out-polyglot_wasm');
  assert.match(receipt.stdout, /POLYGLOT PASS \(wasm\)/);
  assert.equal(await page.locator('#demo-details').evaluate(el => el.open), false);
  receipt.checks.push('real precompiled polyglot Wasm exits 0; list and all three result cards match stdout; source starts collapsed');

  // Native button keyboard behavior must change the reader, keeping one compiler.
  await page.locator('[data-reader="Lisp"]').focus();
  await page.keyboard.press('Enter');
  assert.equal(await page.locator('[data-reader="Lisp"]').getAttribute('aria-pressed'), 'true');
  assert.match(await text('reader-note'), /Lisp reader/);
  await page.locator('[data-reader="Forth"]').click();
  assert.match(await text('ast-caption'), /Forth reader/);
  assert.equal(await page.locator('[data-reader][aria-pressed="true"]').count(), 1);
  receipt.checks.push('reader diagram works with keyboard and pointer; exactly one syntax is selected');

  for (const width of [1440, 1297, 768, 390]) {
    await page.setViewportSize({ width, height: 1100 });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `page overflows at ${width}px`);
    assert(await page.locator('.compiler-map').isVisible());
    assert(await page.locator('.results').isVisible());
    if (evidence) await page.screenshot({ path: path.join(evidence, `homepage-${width}.png`), fullPage: true });
  }
  receipt.checks.push('1440, 1297, 768 and 390px layouts fit viewport; screenshots retained');

  await page.locator('#demo-details summary').click();
  for (const id of ['fib', 'mandelbrot']) {
    await page.locator('#tab-' + id).click();
    await page.locator('#run-' + id).click();
    await page.waitForFunction(id => !document.getElementById('run-' + id).disabled && /exit 0/.test(document.getElementById('st-' + id).textContent), id);
    assert((await text('out-' + id)).length > 0);
  }
  await page.locator('#tab-polyglot_wasm').click();
  assert.match(await text('out-polyglot_wasm'), /POLYGLOT PASS/);
  receipt.checks.push('source/output disclosure works; Fibonacci and Mandelbrot still run to exit 0');

  // A rerun must clear the last successful numbers immediately on a real HTTP failure.
  await page.route('**/examples/polyglot_wasm.wasm', route => route.fulfill({ status: 503, body: 'unavailable' }));
  await page.locator('#run-visual').click();
  await waitVisual(/Could not run/);
  assert.deepEqual(await Promise.all(['prime-count', 'prime-sum', 'digit-sum'].map(text)), ['—', '—', '—']);
  assert.equal(await page.locator('#prime-chips span').count(), 0);
  assert.match(await text('out-polyglot_wasm'), /503/);
  await page.unroute('**/examples/polyglot_wasm.wasm');

  await page.evaluate(() => {
    window.savedRunLangWasm = window.runLangWasm;
    window.runLangWasm = async (_bytes, write) => { write('partial output\n', false); return { exit: 1, trapped: false }; };
  });
  await page.locator('#run-visual').click();
  await waitVisual(/Program failed \(exit 1\)/);
  assert.equal(await text('prime-count'), '—');
  await page.evaluate(() => {
    window.runLangWasm = async (_bytes, write) => { write('changed output format\n', false); return { exit: 0, trapped: false }; };
  });
  await page.locator('#run-visual').click();
  await waitVisual(/summary unavailable/);
  assert.equal(await text('prime-sum'), '—');
  await page.evaluate(() => { window.runLangWasm = window.savedRunLangWasm; });
  await page.locator('#run-visual').click();
  await waitVisual(/Ran successfully/);
  assert.equal(await text('prime-count'), '10');
  receipt.checks.push('HTTP error, nonzero program exit and changed output cannot show stale success; real rerun recovers');

  await page.locator('#reader-details summary').click();
  assert(await page.locator('#reader-details a[href="readers.html"]').isVisible());
  await page.locator('#capability-details > summary').click();
  const borders = JSON.parse(await fs.readFile(path.join(root, 'borders.json')));
  assert.equal(await page.locator('.border-cell').count(), borders.cells.length);
  assert.deepEqual(errors, []);
  assert.deepEqual(external, []);
  receipt.checks.push('reader guide and generated capability evidence remain accessible; no page errors or external requests');
  if (evidence) await fs.writeFile(path.join(evidence, 'homepage-browser.json'), JSON.stringify(receipt, null, 2) + '\n');
  console.log('PASS homepage_visual_browser: ' + receipt.checks.join('; '));
} finally {
  if (browser) await browser.close();
  await new Promise(resolve => server.close(resolve));
}
