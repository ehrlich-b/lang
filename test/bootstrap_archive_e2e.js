#!/usr/bin/env node
'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { spawnSync } = require('child_process');

// Exercise the real shell recipe without compiler generations or publication.
// A succeeding archive step may enter its directory; make runs promotion in a
// separate shell. An absolute sentinel models that subsequent step here.
const makefile = fs.readFileSync(process.argv[2] || 'Makefile', 'utf8');
const start = makefile.indexOf('\t@# Archive current bootstrap to GitHub release + local cache');
const end = makefile.indexOf('\t@# Stage complete files', start);
assert(start >= 0 && end > start, 'cannot find bootstrap archive recipe');
const recipe = makefile.slice(start, end)
  .replaceAll('\t@', '').replaceAll('\t', '')
  .replaceAll('$(VERSION)', 'test-new').replaceAll('$(PUBLISH_BOOTSTRAP)', '0')
  .replaceAll('$(GH)', 'false').replaceAll('$$', '$');

function snapshot(root) {
  const files = {};
  function walk(dir) {
    if (!fs.existsSync(dir)) return;
    for (const name of fs.readdirSync(dir)) {
      const file = path.join(dir, name);
      if (fs.statSync(file).isDirectory()) walk(file);
      else files[path.relative(root, file)] = fs.readFileSync(file).toString('hex');
    }
  }
  for (const dir of ['bootstrap/current', 'out', 'docs', 'designs', 'src', 'sentinels']) {
    walk(path.join(root, dir));
  }
  return files;
}

for (const kind of ['missing-parent', 'blocked-parent', 'copy-failure', 'cd-failure',
  'mismatch', 'matching', 'conflicting-tarball', 'retention']) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'lang-bootstrap-archive-'));
  try {
    const current = path.join(root, 'bootstrap/current');
    const archive = path.join(root, 'bootstrap/archive');
    for (const file of ['bootstrap/current/compiler_linux.ll', 'bootstrap/current/compiler_macos.ll',
      'bootstrap/current/PROVENANCE', 'bootstrap/current/lang_reader/source.ast',
      'out/lang', 'docs/sentinel', 'designs/sentinel', 'src/sentinel', 'sentinels/sentinel']) {
      fs.mkdirSync(path.dirname(path.join(root, file)), { recursive: true });
      fs.writeFileSync(path.join(root, file), `preserved ${file}`);
    }
    fs.writeFileSync(path.join(current, 'COMMIT'), 'test-old\n');
    // A cwd fallthrough must never compress checkout directories, even when
    // the checkout has enough entries to trigger the retention policy.
    for (let i = 0; i < 25; i++) {
      const dir = path.join(root, `root-${i}`);
      fs.mkdirSync(dir);
      fs.writeFileSync(path.join(dir, 'sentinel'), `root-${i}`);
    }
    if (kind === 'blocked-parent') fs.writeFileSync(archive, 'not a directory');
    if (kind === 'mismatch' || kind === 'matching') {
      fs.cpSync(current, path.join(archive, 'test-old'), { recursive: true });
      if (kind === 'mismatch') fs.writeFileSync(path.join(archive, 'test-old/COMMIT'), 'different\n');
    }
    if (kind === 'conflicting-tarball') {
      fs.mkdirSync(archive);
      fs.writeFileSync(path.join(archive, 'test-old.tar.gz'), 'existing archive');
    }
    if (kind === 'retention') {
      for (let i = 0; i < 30; i++) {
        fs.cpSync(current, path.join(archive, `history-${i}`), { recursive: true });
      }
    }
    const before = snapshot(root);
    const preamble = kind === 'copy-failure' ? 'cp() { return 6; };\n'
      : kind === 'cd-failure' ? 'cd() { return 7; };\n' : '';
    const script = `TEST_ROOT="$PWD"\n${preamble}${recipe}\nprintf promoted > "$TEST_ROOT/promotion-sentinel"\n`;
    const result = spawnSync('/bin/sh', ['-c', script], { cwd: root, encoding: 'utf8', timeout: 10000 });
    assert.strictEqual(result.error, undefined, `${kind}: ${result.error}`);
    assert.strictEqual(result.signal, null, `${kind}: ${result.signal}`);
    const success = ['missing-parent', 'matching', 'retention'].includes(kind);
    assert.strictEqual(result.status === 0, success, `${kind}: ${result.stdout}\n${result.stderr}`);
    assert.strictEqual(fs.existsSync(path.join(root, 'promotion-sentinel')), success, kind);
    assert.deepStrictEqual(snapshot(root), before, `${kind}: checkout or current root changed`);
    for (let i = 0; i < 25; i++) {
      assert.strictEqual(fs.readFileSync(path.join(root, `root-${i}/sentinel`), 'utf8'), `root-${i}`, kind);
    }
    if (kind === 'missing-parent') {
      assert.deepStrictEqual(fs.readFileSync(path.join(archive, 'test-old/compiler_linux.ll')),
        fs.readFileSync(path.join(current, 'compiler_linux.ll')));
    }
    if (kind === 'retention') {
      assert.strictEqual(fs.readdirSync(archive).length, 31, 'unverified history was deleted');
      assert.strictEqual(fs.readdirSync(archive).filter(name => name.endsWith('.tar.gz')).length, 10);
    }
    console.log(`PASS bootstrap_archive_${kind}`);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
}
