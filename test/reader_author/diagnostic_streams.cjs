'use strict';
const assert = require('node:assert/strict');
const { decodeReaderDiagnostics } = require('../../web/program_host.js');

const context = { key: 'broken', path: '/guest/policy.broken', text: 'é\r\nx', sourceId: 7 };
function frame(code, message, category = 0, start = -1, end = -1) {
  const fields = [code, 'broken', message].map(value => Buffer.from(value));
  const header = Buffer.alloc(28);
  header.write('RDI1');
  [category, start + 1, end + 1, ...fields.map(value => value.length)]
    .forEach((value, index) => header.writeUInt32LE(value, 4 + index * 4));
  return Buffer.concat([header, ...fields]);
}
const message = 'x'.repeat(131072);
const large = frame('\ufefflarge', message);
const tail = frame('reader-implementation', '"\\\n\t\u0001é\ufeff', 1);
const located = frame('last-guest', 'last guest message', 0, 0, 2);
const stream = Buffer.concat([large, tail, located]);
const records = decodeReaderDiagnostics(stream, context);
assert.deepEqual(records.map(record => record.code), ['\ufefflarge', 'reader-implementation', 'last-guest']);
assert.equal(records[0].message, message);
assert.equal(records[1].message, '"\\\n\t\u0001é\ufeff');
assert.equal(records[1].category, 'reader');
assert.equal(records[1].span, null);
assert.deepEqual(records[2].span, { start: 0, end: 2 });
assert.ok(records.every(record => record.path === context.path && record.source_id === 7));
// Every nonempty truncated prefix must reject even after complete large frames.
for (let length = 1; length < tail.length; length++) {
  assert.throws(() => decodeReaderDiagnostics(Buffer.concat([large, tail.subarray(0, length)]), context));
}
assert.throws(() => decodeReaderDiagnostics(Buffer.concat([stream, Buffer.from('RDI1')]), context));
console.log(JSON.stringify({ pass: true, messageBytes: Buffer.byteLength(message),
  mixedRecords: records.length, truncatedFrames: tail.length - 1 }));
