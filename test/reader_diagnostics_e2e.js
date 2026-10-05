#!/usr/bin/env node
'use strict';

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const cases = require('./reader_diagnostics_cases.json');
const compiler = path.resolve(process.argv[2] || './out/lang');
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'lang-reader-diagnostics-'));
const start = performance.now();

function run(args, extraEnv = {}) {
  return spawnSync(compiler, args, {
    encoding: 'utf8', timeout: 30000,
    env: { ...process.env, LANGBE: 'llvm', LANG_CACHE: path.join(tmp, 'cache'), ...extraEnv },
  });
}

try {
  const helperIR = path.join(tmp, 'helpers.ll');
  const helperBinary = path.join(tmp, 'helpers');
  const helperCompile = run(['test/reader_error_helpers.lang', '-o', helperIR]);
  assert.strictEqual(helperCompile.status, 0, helperCompile.stderr);
  const helperLink = spawnSync('clang', ['-w', helperIR, '-o', helperBinary], { encoding: 'utf8', timeout: 30000 });
  assert.strictEqual(helperLink.status, 0, helperLink.stderr);
  const helpers = spawnSync(helperBinary, [], { encoding: 'utf8', timeout: 30000 });
  assert.strictEqual(helpers.status, 0, helpers.stderr);
  assert.strictEqual(helpers.stderr, [
    'test:2:1: error: located', 'test:2:2: error: EOF',
    'test: error: unknown span', 'test: error: unknown source',
    'first:2:1: error: node', 'second: error: nil node', '',
  ].join('\n'));
  for (const test of cases) {
    const sourcePath = path.join(tmp, `${test.name}.${test.reader}`);
    const astPath = path.join(tmp, `${test.name}.ast`);
    fs.writeFileSync(sourcePath, test.source);
    const result = run(['read', `example/${test.reader}/${test.reader}.lang`, sourcePath, '-o', astPath]);
    assert.strictEqual(result.error, undefined, `${test.name}: ${result.error}`);
    assert.strictEqual(result.status, 1, `${test.name}: ${result.stderr}`);
    assert(!fs.existsSync(astPath), `${test.name}: emitted AST after failure`);
    assert(result.stderr.includes(`${test.reader}:${test.line}:${test.column}:`),
      `${test.name}: wrong location\n${result.stderr}`);
    assert(result.stderr.includes(test.message), `${test.name}: wrong message\n${result.stderr}`);
    assert(!/Segmentation|signal|internal compiler error/i.test(result.stderr), result.stderr);
  }

  // The minted compiler must keep the toolkit context and reject the same input.
  const minted = path.join(tmp, 'forthc');
  const build = run(['compiler', 'forth', 'example/forth/forth.lang', '-o', minted]);
  assert.strictEqual(build.status, 0, build.stderr);
  const bad = spawnSync(minted, [path.join(tmp, 'forth-plus.forth'), '-o', path.join(tmp, 'bad.ll')],
    { encoding: 'utf8', timeout: 30000 });
  assert.strictEqual(bad.status, 1, bad.stderr);
  assert(bad.stderr.includes('forth:2:5: error: stack underflow'), bad.stderr);
  assert(!fs.existsSync(path.join(tmp, 'bad.ll')));

  // A second invocation uses a different source; cached readers must not keep
  // the first input's line count. Also execute the resulting real program.
  const goodPath = path.join(tmp, 'good.forth');
  fs.writeFileSync(goodPath, ': main ( -- n ) 42 ;\n');
  const good = run(['run', 'example/forth/forth.lang', goodPath]);
  assert.strictEqual(good.status, 42, good.stderr);
  console.log(`PASS reader_diagnostics_e2e (${cases.length} rejections, minted compiler, corrected program; ${Math.round(performance.now() - start)} ms)`);
} finally {
  fs.rmSync(tmp, { recursive: true, force: true });
}
