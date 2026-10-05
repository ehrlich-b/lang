#!/usr/bin/env node
'use strict';
const assert = require('assert/strict');
const { parseCDecimal, formatGeneral, formatNumericPrintf, createNumericHost } = require('../web/numeric_host.js');

for (const literal of ['-0', '0.3', '0.30000000000000002', '0.30000000000000003',
  '0.2', '1.3', '-0.00000001', '100000000000000000000', '2.2250738585072014e-308']) {
  assert(Object.is(parseCDecimal(literal).value, Number(literal)), literal);
  const printed = formatGeneral(Number(literal), 17);
  assert(Object.is(Number(printed), Number(literal)), `${literal} -> ${printed}`);
}
assert.deepEqual(parseCDecimal('  -1.25suffix'), { value: -1.25, consumed: 7 });
assert.deepEqual(parseCDecimal('not-a-number'), { value: 0, consumed: 0 });
assert.deepEqual(parseCDecimal('1e-?'), { value: 1, consumed: 1 });
assert.equal(formatGeneral(0.3, 17), '0.29999999999999999');
assert.equal(formatGeneral(0.00001, 17), '1.0000000000000001e-05');
assert.equal(formatGeneral(1e20, 17), '1e+20');
assert.equal(formatGeneral(Infinity, 17), 'inf');
assert.equal(formatGeneral(-Infinity, 17), '-inf');
assert.equal(formatNumericPrintf('%f', [2 ** 70]), '1180591620717411303424.000000');
assert.equal(formatNumericPrintf('%.17g,%ld,%%,%f\n', [0.3, 42n, -0]), '0.29999999999999999,42,%,-0.000000\n');

const memory = new WebAssembly.Memory({ initial: 1 });
const bytes = new Uint8Array(memory.buffer), view = new DataView(memory.buffer);
const encoder = new TextEncoder(), decoder = new TextDecoder();
const put = (pointer, text) => bytes.set(encoder.encode(text + '\0'), pointer);
function cstr(pointer) { let end = Number(pointer); while (bytes[end]) end++; return decoder.decode(bytes.subarray(Number(pointer), end)); }
let output = '';
const host = createNumericHost({ memory: () => memory, cstr, emit: text => { output += text; } });
assert.equal(host.fmod(-5.5, 2), -1.5);
assert(Object.is(host.fmod(-4, 2), -0));
assert(Number.isNaN(host.fmod(Infinity, 2)));
assert.equal(host.fmod(3, Infinity), 3);
assert.equal(host.fmodf(5.3, 2), Math.fround(Math.fround(5.3) % Math.fround(2)));
put(64, '-1.25tail');
assert.equal(host.strtod(64n, 128n), -1.25);
assert.equal(view.getBigUint64(128, true), 69n);
put(80, 'bad');
assert.equal(host.strtod(80n, 128n), 0);
assert.equal(view.getBigUint64(128, true), 80n);
put(256, '%.17g\n');
host.printf(256n, 0.3);
view.setFloat64(512, 0.3, true); host.printfBuffer(256n, 512n);
assert.equal(output, '0.29999999999999999\n0.29999999999999999\n');
const host32 = createNumericHost({ memory: () => memory, cstr, emit: () => {}, pointerBytes: 4 });
view.setUint32(132, 0x12345678, true);
host32.strtod(64, 128);
assert.equal(view.getUint32(128, true), 69);
assert.equal(view.getUint32(132, true), 0x12345678);
console.log('PASS numeric host: binary64 decimal boundaries, roundtrip17 digits, typed/buffer printf, 32/64-bit endptr');
