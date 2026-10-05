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
  'std/numeric.lang',
  'std/emit.lang',
  'std/ast.lang',
  'std/prec.lang',
  'std/tok.lang',
  'std/pnode.lang',
  'std/reader_error.lang',
  'std/parser_runtime.lang',
  'std/parse.lang',
  'example/hamiltonian/hamiltonian.lang',
  'example/hamiltonian/expression.lang',
  'example/hamiltonian/lowering.lang',
  'example/hamiltonian/runtime.lang',
  'example/hamiltonian/decimal.lang',
  'example/hamiltonian/quartic.ham',
  'example/hamiltonian/double_well.ham',
  'example/tiny/tiny.lang',
  'example/workshop/workshop.lang',
  'example/workshop/example.workshop',
  'example/calc/calc.lang',
  'example/c/c.lang',
  'example/forth/forth.lang',
  'example/minilisp/minilisp.lang',
  'example/minipy/minipy.lang',
  'example/flow/flow.lang',
  'example/minilisp/lisp_runtime.lang',
];

const files = Object.fromEntries(paths.map((path) => [path, fs.readFileSync(path, 'utf8')]));
fs.writeFileSync('web/stdlib.json', `${JSON.stringify(files)}\n`);
console.log(`built web/stdlib.json (${fs.statSync('web/stdlib.json').size} bytes)`);
