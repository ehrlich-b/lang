'use strict';
// The Python arbitrary-precision model supplies expected decimal results.
// Read exact i64 results directly, without an 8-bit process exit code.
const fs = require('fs');
(async () => {
  const bytes = fs.readFileSync(process.argv[2]);
  const samples = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
  const { instance } = await WebAssembly.instantiate(bytes, {});
  for (const [index, a, b, expected] of samples) {
    const actual = instance.exports.main(BigInt(index), BigInt(a), BigInt(b)).toString();
    if (actual !== expected) throw new Error(`oracle mismatch wasm: ${index}, ${a}, ${b}: expected ${expected}, got ${actual}`);
  }
  console.log(`PASS direct Wasm oracle: ${samples.length} full-width results`);
})().catch(error => { console.error(error); process.exit(1); });
