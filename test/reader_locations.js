#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const cases = require('./reader_locations/cases.json');
const diagnostic = (c, label = c.name) => `${label}:${c.line}:${c.column}: ${c.message}`;

function nativeLocations() {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'reader-locations-'));
  // Keep failed artifacts for diagnosis; successful runs need no cleanup to pass.
  return cases.map(c => {
    const output = path.join(tmp, `${c.name}.ast`);
    const result = spawnSync(process.env.COMPILER || './out/lang', [
      'read', `example/${c.name}/${c.name}.lang`, c.path, '-o', output,
    ], { encoding: 'utf8', timeout: 120000, env: {
      ...process.env, LANGBE: 'llvm', LANG_CACHE: path.join(tmp, 'cache'),
    } });
    assert.ifError(result.error);
    assert.equal(result.signal, null, `${c.name} crashed`);
    assert.equal(result.status, 1, `${c.name} must fail`);
    assert.equal(result.stdout, '', `${c.name} emitted stdout`);
    assert(!fs.existsSync(output), `${c.name} emitted an AST`);
    assert(result.stderr.split('\n').includes(diagnostic(c, c.path)), result.stderr);
    return { name: c.name, exit: result.status, diagnostic: diagnostic(c, c.path), ast: false };
  });
}

if (require.main === module) {
  const receipt = nativeLocations();
  for (const c of receipt) console.log(`PASS ${c.name}: exit ${c.exit}, no AST, ${c.diagnostic}`);
  if (process.env.READER_LOCATION_REPORT) {
    fs.writeFileSync(process.env.READER_LOCATION_REPORT, JSON.stringify(receipt, null, 2) + '\n');
  }
}
module.exports = { cases, diagnostic, nativeLocations };
