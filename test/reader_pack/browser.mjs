import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { pathToFileURL } from 'node:url';
// Chromium's Unix socket path is limited; allow a short local scratch root.
if (process.env.BROWSER_TMPDIR) process.env.TMPDIR = process.env.BROWSER_TMPDIR;
const [inputPath, outputPath] = process.argv.slice(2);
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE
  ? pathToFileURL(process.env.PLAYWRIGHT_MODULE).href : 'playwright');
const root = process.cwd();
const allowed = new Map([
  ['/compiler_host.js', 'web/compiler_host.js'], ['/program_host.js', 'web/program_host.js'],
  ['/runtime.js', 'test/reader_pack/browser_runtime.js'],
]);
const server = http.createServer((req, res) => {
  if (req.url === '/') {
    res.setHeader('Content-Type', 'text/html');
    res.end('<!doctype html><script src="/compiler_host.js"></script><script src="/program_host.js"></script><script src="/runtime.js"></script>');
  } else if (allowed.has(req.url)) {
    res.setHeader('Content-Type', 'text/javascript');
    res.end(fs.readFileSync(path.join(root, allowed.get(req.url))));
  } else res.writeHead(404).end();
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
let browser;
try {
  browser = await chromium.launch({ headless: true, executablePath: process.env.CHROMIUM_PATH,
    args: ['--no-sandbox', '--disable-gpu'] });
  const page = await browser.newPage();
  const origin = `http://127.0.0.1:${server.address().port}`;
  await page.route('**/*', route => route.request().url().startsWith(origin + '/') ? route.continue() : route.abort());
  await page.goto(origin);
  const payload = JSON.parse(fs.readFileSync(inputPath));
  const result = await page.evaluate(payload => runReaderPack(payload), payload);
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  const artifacts = result.artifacts;
  delete result.artifacts;
  for (const artifact of artifacts) fs.writeFileSync(path.join(path.dirname(outputPath), artifact.name), new Uint8Array(artifact.bytes));
  fs.writeFileSync(outputPath, JSON.stringify(result, null, 2) + '\n');
  console.log(`PASS real Chromium replay: ${result.rows.length} observations`);
} finally {
  if (browser) await browser.close();
  await new Promise(resolve => server.close(resolve));
}
