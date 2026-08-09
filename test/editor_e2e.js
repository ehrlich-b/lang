#!/usr/bin/env node
'use strict';

const assert = require('assert');
const { codeEdit } = require('../web/editor.js');

function apply(value, start, end, key, shiftKey = false) {
  const edit = codeEdit(value, start, end, key, shiftKey);
  assert(edit, `expected ${key} to be handled`);
  return {
    value: value.slice(0, edit.from) + edit.text + value.slice(edit.to),
    start: edit.start,
    end: edit.end,
  };
}

assert.deepStrictEqual(apply('x', 0, 0, 'Tab'), { value: '    x', start: 4, end: 4 });
assert.strictEqual(apply('a\nb', 0, 3, 'Tab').value, '    a\n    b');
assert.strictEqual(apply('    a\n\tb', 0, 8, 'Tab', true).value, 'a\nb');
assert.deepStrictEqual(
  apply('if ready {', 10, 10, 'Enter'),
  { value: 'if ready {\n    ', start: 15, end: 15 },
);
assert.strictEqual(apply('    if ready:', 13, 13, 'Enter').value, '    if ready:\n        ');
assert.strictEqual(codeEdit('x', 0, 0, 'Escape', false), null);

console.log('PASS editor_e2e');
