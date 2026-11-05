module.exports = {
  testDir: '.', testMatch: 'sources.spec.cjs', workers: 1,
  outputDir: process.env.EFFECTS_BROWSER_RESULTS || '../scratch/browser-results',
  reporter: 'line',
  use: { browserName: 'chromium', headless: true, launchOptions: {
    ...(process.env.PLAYWRIGHT_HEADLESS_CHROMIUM
      ? { executablePath: process.env.PLAYWRIGHT_HEADLESS_CHROMIUM } : {})
  } }
};
