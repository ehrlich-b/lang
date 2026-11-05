#!/usr/bin/env node
// One offline Chromium pass over all published pages, plus compact-row states.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
assert(process.env.CHROMIUM_PATH, 'CHROMIUM_PATH must name the shared cached Chromium');
const root = fileURLToPath(new URL('..', import.meta.url));
const web = path.join(root, 'web');
const evidence = path.resolve(process.argv[2]);
await fs.mkdir(evidence, { recursive: true });
const variants = spawnSync('python3', ['-c', `
import json
from web.generate_scoreboard import render, LIMIT
print(json.dumps({str(n):render([('a reader with a deliberately long language name', 'an outside conformance suite with a long name', 'not measured', 'LLVM, direct Wasm')]*n) for n in (0,1,LIMIT,LIMIT+3)}))
`], { cwd: root, encoding: 'utf8' });
assert.equal(variants.status, 0, variants.stderr);
const volumes = JSON.parse(variants.stdout);
const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, 'http://localhost');
    const pathname = url.pathname === '/' ? '/index.html' : decodeURIComponent(url.pathname);
    const filename = path.resolve(web, `.${pathname}`);
    assert(filename.startsWith(web + path.sep));
    let data = await fs.readFile(filename);
    if (url.searchParams.has('volume')) {
      data = Buffer.from(data.toString().replace(/  <!-- scoreboard:start -->[\s\S]*?  <!-- scoreboard:end -->/, volumes[url.searchParams.get('volume')]));
    }
    const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.wasm': 'application/wasm' };
    res.writeHead(200, { 'Content-Type': types[path.extname(filename)] || 'text/plain' });
    res.end(data);
  } catch {
    res.writeHead(404); res.end();
  }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const results = [];
let browser;
try {
  browser = await chromium.launch({ headless: true, executablePath: process.env.CHROMIUM_PATH,
    args: ['--disable-gpu', '--no-sandbox'] });
  for (const width of [1440, 390]) {
    for (const name of ['index', 'lab', 'readers']) {
      const page = await browser.newPage({ viewport: { width, height: 950 } });
      const errors = [], offHost = [], failures = [];
      page.on('pageerror', error => errors.push(String(error)));
      page.on('response', response => { if (response.status() >= 400) failures.push(response.url()); });
      await page.route('**/*', async route => {
        const url = route.request().url();
        if (new URL(url).origin !== origin) { offHost.push(url); await route.abort(); }
        else await route.continue();
      });
      page.on('dialog', async dialog => { errors.push(`dialog: ${dialog.type()}`); await dialog.dismiss(); });
      await page.goto(`${origin}/${name}.html`, { waitUntil: 'networkidle' });
      if (name === 'index') {
        await page.waitForFunction(() => document.querySelector('#st-polyglot_wasm .ok'));
        assert.equal(await page.locator('#scoreboard tbody tr').count(), 11);
        assert.equal(await page.locator('#traces h3').count(), 3);
      }
      if (name === 'lab') {
        await page.waitForFunction(() => !document.getElementById('compile').disabled);
      }
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${name}/${width} overflows`);
      await page.screenshot({ path: path.join(evidence, `${name}-${width}.png`), fullPage: true });
      if (name === 'index') {
        await page.locator('#scoreboard').screenshot({ path: path.join(evidence, `scoreboard-${width}.png`) });
        await page.locator('#traces').screenshot({ path: path.join(evidence, `traces-${width}.png`) });
        for (const [count, rendered] of Object.entries(volumes)) {
          assert(rendered);
          await page.goto(`${origin}/index.html?volume=${count}`, { waitUntil: 'networkidle' });
          assert.equal(await page.locator('#scoreboard tbody tr').count(), Number(count));
          assert.equal(await page.locator('#scoreboard summary').count(), Number(count) > 8 ? 1 : 0);
          assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
          await page.locator('#scoreboard').screenshot({ path: path.join(evidence, `volume-${count}-${width}.png`) });
        }
      }
      assert.deepEqual(errors, [], `${name}/${width} page errors`);
      assert.deepEqual(offHost, [], `${name}/${width} off-host requests`);
      assert.deepEqual(failures, [], `${name}/${width} failed responses`);
      results.push({ page: name, width, errors, offHost, failures });
      await page.close();
    }
  }
  await fs.writeFile(path.join(evidence, 'browser.json'), JSON.stringify(results, null, 2) + '\n');
  console.log('PASS Chromium: three pages at 1440/390, no page errors, off-host or failed requests; scoreboard 0/1/8/11 long-name states');
} finally {
  await browser?.close();
  await new Promise(resolve => server.close(resolve));
}
