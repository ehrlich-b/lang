const { test } = require('playwright/test');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
test('snapshot primary LLVM contracts with bundled headless Chromium', async ({ page, browser }) => {
  const sources = [
    ['indirectbr', 'https://llvm.org/docs/LangRef.html#indirectbr-instruction'],
    ['callbr', 'https://llvm.org/docs/LangRef.html#callbr-instruction'],
    ['returns_twice', 'https://llvm.org/docs/LangRef.html#function-attributes'],
  ];
  const results = [];
  for (const [id, url] of sources) {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    const text = await page.locator(id === 'returns_twice' ? '#function-attributes' : `#${id}-instruction`).innerText();
    results.push({ id, url, retrieved: new Date().toISOString(), browser: browser.version(),
      chars: text.length, sha256: crypto.createHash('sha256').update(text).digest('hex'),
      headless: true, executable: require('./playwright.config.cjs').use.launchOptions.executablePath });
  }
  fs.writeFileSync(path.resolve(process.env.EFFECTS_SOURCES_FILE || '../evidence/sources.json'), JSON.stringify(results, null, 2) + '\n');
});
