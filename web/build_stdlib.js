#!/usr/bin/env node
'use strict';

const fs = require('fs');

const paths = [
  'src/limits.lang',
  'std/os.lang',
  'std/os/libc.lang',
  'std/os/libc_macos.lang',
  'std/tools.lang',
  'std/core.lang',
  'std/emit.lang',
  'std/ast.lang',
  'std/tok.lang',
  'std/pnode.lang',
  'std/parser_runtime.lang',
];

const files = Object.fromEntries(paths.map((path) => [path, fs.readFileSync(path, 'utf8')]));
fs.writeFileSync('web/stdlib.json', `${JSON.stringify(files)}\n`);
console.log(`built web/stdlib.json (${fs.statSync('web/stdlib.json').size} bytes)`);
