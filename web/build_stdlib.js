#!/usr/bin/env node
'use strict';

const fs = require('fs');

const paths = [
  'src/limits.lang',
  'src/diagnostics.lang',
  'std/os.lang',
  'std/os/libc.lang',
  'std/os/libc_macos.lang',
  'std/tools.lang',
  'std/core.lang',
  'std/diagnostics.lang',
  'std/reader_diagnostics.lang',
  'std/reader_exports.lang',
  'src/reader_diagnostics.lang',
  'std/buffer.lang',
  'std/emit.lang',
  'std/ast.lang',
  'std/prec.lang',
  'std/tok.lang',
  'std/pnode.lang',
  'std/parser_runtime.lang',
  'example/tiny/tiny.lang',
  'example/tree/tree.lang',
  'example/calc/calc.lang',
  'example/c/c.lang',
  'example/forth/forth.lang',
  'example/minilisp/minilisp.lang',
  'example/minipy/minipy.lang',
  'example/flow/flow.lang',
  'example/minilisp/lisp_runtime.lang',
  'test/reader_locations/c.c',
  'test/reader_locations/flow.flow',
  'test/reader_locations/forth.forth',
  'test/reader_locations/minilisp.minilisp',
  'test/reader_locations/minipy.minipy',
];

const files = Object.fromEntries(paths.map((path) => [path, fs.readFileSync(path, 'utf8')]));
const output = process.argv[2] || 'web/stdlib.json';
fs.writeFileSync(output, `${JSON.stringify(files)}\n`);
console.log(`built ${output} (${fs.statSync(output).size} bytes)`);
