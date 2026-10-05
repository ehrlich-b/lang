'use strict';
const assert = require('node:assert/strict');
const { runLangProgram } = require('../web/program_host.js');

// A minimal independent Wasm module isolates the host's floating return ABI
// from compiler code generation. main takes argc/argv and exports memory.
function constantMain(type, value) {
  const encoder = new TextEncoder();
  const name = text => [text.length, ...encoder.encode(text)];
  const section = (id, bytes) => [id, bytes.length, ...bytes];
  const bits = new Uint8Array(type === 0x7c ? 8 : 4);
  const view = new DataView(bits.buffer);
  if (type === 0x7c) view.setFloat64(0, value, true);
  else view.setFloat32(0, value, true);
  const body = [0, type === 0x7c ? 0x44 : 0x43, ...bits, 0x0b];
  return new Uint8Array([
    0, 97, 115, 109, 1, 0, 0, 0,
    ...section(1, [1, 0x60, 2, 0x7e, 0x7e, 1, type]),
    ...section(3, [1, 0]),
    ...section(5, [1, 0, 32]),
    ...section(7, [2, ...name('main'), 0, 0, ...name('memory'), 2, 0]),
    ...section(10, [1, body.length, ...body]),
  ]);
}

(async () => {
  for (const [type, value] of [[0x7c, 1.5], [0x7d, -2.75], [0x7c, -0], [0x7c, Infinity], [0x7c, NaN]]) {
    const module = constantMain(type, value);
    assert(WebAssembly.validate(module));
    const result = await runLangProgram(module);
    assert(Object.is(result.value, value), `floating return changed: ${value}`);
    assert.equal(result.didExit, false);
    assert.equal(result.stdout, '');
    assert.equal(result.stderr, '');
  }
  console.log('PASS program host floating return ABI');
})().catch(error => { console.error(error); process.exitCode = 1; });
