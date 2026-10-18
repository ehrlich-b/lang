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
const expected = await fs.readFile(path.join(root, 'test/pnode_dump.expected'), 'utf8');
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
const receipt = { checks: [] };
try {
  browser = await chromium.launch({
    headless: true,
    executablePath: process.env.CHROMIUM_PATH || undefined,
    args: ['--disable-gpu', '--no-sandbox'],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  page.setDefaultTimeout(120000);
  const errors = [];
  page.on('pageerror', error => errors.push(String(error)));
  await page.goto(`http://127.0.0.1:${server.address().port}/lab.html`);
  await page.waitForFunction(() => !document.getElementById('compile').disabled);
  // Count actual compiler calls and preserve module identity across reruns.
  await page.evaluate(() => {
    window.readerBuilds = 0;
    const original = window.runLangCompiler;
    window.runLangCompiler = (...args) => {
      if (args[1][0] === 'reader.lang') window.readerBuilds++;
      return original(...args);
    };
  });
  const text = selector => page.locator(selector).textContent();
  const build = async expectedStatus => {
    await page.locator('#compile').click();
    await page.waitForFunction(() => !document.getElementById('compile').disabled);
    assert.match(await text('#status'), expectedStatus, await text('#output'));
  };
  const downloadText = selector => page.locator(selector).evaluate(async anchor => (await fetch(anchor.href)).text());

  await build(/ran/);
  assert.match(await text('#output'), /main\(\) → 42/);
  assert.equal(await page.locator('#reader-diagnostics').isVisible(), false);
  receipt.checks.push('starter output stays compact with no diagnostics');

  await page.selectOption('#preset', 'tree');
  const originalReader = await page.locator('#reader').inputValue();
  await build(/ran/);
  assert.equal(await text('#reader-stderr'), expected);
  assert.match(await text('#output'), /main\(\) → 32/);
  const ast = await downloadText('#download-ast');
  assert.match(ast, /^\(program\n/);
  assert.match(ast, /\(number 32\)/);
  assert.doesNotMatch(ast, /capture|marker|list @/);
  await page.evaluate(() => { window.savedReader = cachedReaderProgram; });
  const builds = await page.evaluate(() => window.readerBuilds);
  receipt.tree = expected;
  receipt.checks.push('browser stderr equals pnode_dump.expected; AST download contains only lowered AST');

  for (const width of [1280, 390]) {
    await page.setViewportSize({ width, height: 900 });
    assert.equal(await page.locator('#reader-diagnostics').evaluate(el => el.open), true);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    if (evidence) await page.screenshot({ path: path.join(evidence, `tree-${width}.png`), fullPage: true });
    await page.locator('#reader-diagnostics summary').click();
    assert.equal(await page.locator('#reader-stderr').isVisible(), false);
    await page.locator('#reader-diagnostics summary').click();
    assert.equal(await page.locator('#reader-stderr').isVisible(), true);
  }
  receipt.checks.push('1280px and 390px layouts have no page overflow and tree collapses/reopens');

  await page.locator('#custom-source').fill('10:42');
  await build(/ran/);
  assert.match(await text('#reader-stderr'), /number "42" @3:5/);
  assert.match(await text('#output'), /main\(\) → 42/);
  assert.equal(await page.evaluate(() => window.readerBuilds), builds);
  assert.equal(await page.evaluate(() => window.savedReader === cachedReaderProgram), true);
  receipt.checks.push('source-only edit changes tree and program value while reusing the identical reader Wasm');

  const editedReader = originalReader.replace("left:number ':' right:number", "left:number '+' right:number").replaceAll('right', 'result');
  await page.locator('#reader').fill(editedReader);
  await page.locator('#custom-source').fill('10+43');
  await build(/ran/);
  assert.match(await text('#reader-stderr'), /marker "\+" @2:3/);
  assert.match(await text('#reader-stderr'), /capture "result" @3:5/);
  assert.match(await text('#output'), /main\(\) → 43/);
  assert.equal(await page.evaluate(() => window.readerBuilds), builds + 1);
  receipt.editedTree = await text('#reader-stderr');
  if (evidence) await page.screenshot({ path: path.join(evidence, 'tree-edited-390.png'), fullPage: true });
  receipt.checks.push('literal and capture edit rebuilds reader and changes visible tree; generated program returns 43');

  await page.locator('#custom-source').fill('10:43');
  await build(/reader run failed/);
  assert.match(await text('#output'), /source.read:1:3: expected/);
  assert.equal(await page.locator('#download-ast').isVisible(), false);
  assert.equal(await page.locator('#download-program').isVisible(), false);
  assert.doesNotMatch(await text('#reader-stderr'), /capture "result"/);
  receipt.checks.push('failed parse retains location, clears stale tree and program downloads');

  await page.locator('#reader').fill(originalReader.replace('ast_number(right.text)', 'ast_call0("missing_tree_function")'));
  await page.locator('#custom-source').fill('10:32');
  await build(/AST compile failed/);
  assert.equal(await text('#reader-stderr'), expected);
  assert.match(await text('#output'), /source.read:1:4: error: unknown function/);
  assert.equal(await page.locator('#custom-source').evaluate(el => el === document.activeElement), true);
  assert.equal(await page.locator('#custom-source').evaluate(el => el.value.slice(el.selectionStart, el.selectionEnd)), '32');
  receipt.checks.push('later compiler failure preserves successful reader stderr and focuses the source span');

  // Diagnostics are arbitrary text, not just trees; never interpret them as HTML.
  await page.locator('#reader').fill(originalReader.replace('pnode_dump(tree);', 'eprintln("<b>reader note</b>");'));
  await build(/ran/);
  assert.equal(await text('#reader-stderr'), '<b>reader note</b>\n');
  assert.equal(await page.locator('#reader-stderr b').count(), 0);
  receipt.checks.push('successful arbitrary reader stderr is retained as plain text');

  await page.selectOption('#preset', 'starter');
  assert.equal(await page.locator('#reader-diagnostics').isVisible(), false);
  await build(/ran/);
  assert.equal(await page.locator('#reader-diagnostics').isVisible(), false);
  assert.deepEqual(errors, []);
  receipt.checks.push('preset changes and subsequent runs do not retain stale diagnostics; no browser errors');
  if (evidence) await fs.writeFile(path.join(evidence, 'lab-tree.json'), `${JSON.stringify(receipt, null, 2)}\n`);
  console.log(`PASS lab_tree_browser: ${receipt.checks.join('; ')}`);
} finally {
  if (browser) await browser.close();
  await new Promise(resolve => server.close(resolve));
}
