#!/usr/bin/env node
'use strict';
const assert = require('assert/strict');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execFileSync } = require('child_process');
const { runLangCompiler } = require('../web/compiler_host.js');
const { runLangProgram, formatLangAst } = require('../web/program_host.js');
const { createSciencePipeline, parseScientificCsv } = require('../web/science_pipeline.js');
const { diagnosticSelection } = require('../web/editor.js');

const compilerPath = process.argv[2] || 'web/compiler.wasm';
const output = path.resolve(process.argv[3] || 'out/hamiltonian-browser');
const nativeDirectory = process.argv[4] && path.resolve(process.argv[4]);
fs.mkdirSync(output, { recursive: true });
const stdlib = JSON.parse(fs.readFileSync('web/stdlib.json', 'utf8'));
// Test the delivered bundle, and fail if it silently packs an old reader/model.
for (const name of ['hamiltonian.lang', 'expression.lang', 'lowering.lang', 'runtime.lang', 'decimal.lang', 'quartic.ham', 'double_well.ham']) {
  const file = `example/hamiltonian/${name}`;
  assert.equal(stdlib[file], fs.readFileSync(file, 'utf8'), `packed science asset is stale or missing: ${file}`);
}
const compilerBytes = fs.readFileSync(compilerPath);
const pipeline = createSciencePipeline(compilerBytes, stdlib,
  { runLangCompiler, runLangProgram, formatLangAst });
const quartic = stdlib['example/hamiltonian/quartic.ham'];
const doubleWell = stdlib['example/hamiltonian/double_well.ham'];
const harmonic = quartic.replace('model quartic {', 'model harmonic {')
  .replace('param a = 0.6;', 'param a = 0.0;').replace('param b = 0.4;', 'param b = 0.0;');
const settings = (source, h, count) => source.replace(/run step .*?;/, `run step ${h} steps ${count} sample 1;`);
const receipts = [];
const manifest = { harmonic: [], long_harmonic: [], native_browser_pairs: [] };

async function experiment(name, source, args = [], compiled) {
  const model = compiled || await pipeline.compileModel(source);
  assert(model.functions.some(fn => fn.name === 'ham_potential'));
  assert(model.functions.some(fn => fn.name === 'ham_step'));
  assert(model.functions.some(fn => fn.name.startsWith('ham_force_')));
  const run = await pipeline.runModel(model, args);
  const file = path.join(output, `${name}.csv`);
  fs.writeFileSync(file, run.text); fs.writeFileSync(path.join(output, `${name}.ast`), model.ast);
  fs.writeFileSync(path.join(output, `${name}.ham`), source);
  fs.writeFileSync(path.join(output, `${name}.wasm`), model.wasm);
  receipts.push({ name, args, phases: model.phases, runMilliseconds: run.milliseconds,
    wasmBytes: model.wasm.byteLength, rows: run.rows.length });
  if (nativeDirectory && !args.length) {
    const native = path.join(nativeDirectory, `${name}-O2.csv`);
    assert(fs.existsSync(native), `native receipt missing: ${native}`);
    manifest.native_browser_pairs.push([file, native]);
  }
  return { model, run, file };
}

(async () => {
  const started = performance.now();
  let harmonicModel;
  for (const [h, count] of [[0.04, 92], [0.02, 184], [0.01, 368]]) {
    const result = await experiment(`harmonic-${h}`, settings(harmonic, h, count));
    manifest.harmonic.push(result.file); harmonicModel = result.model;
  }
  // Check the analytic harmonic gate before attempting nonlinear experiments.
  execFileSync('python3', ['-c',
    'import sys,json; sys.dont_write_bytecode=True; sys.path.insert(0,"test"); import hamiltonian_reference as r; assert r.analyze_harmonic(json.loads(sys.argv[1]))["passed"]',
    JSON.stringify(manifest.harmonic)], { stdio: 'inherit' });
  for (const [h, count] of [[0.04, 25000], [0.02, 50000]]) {
    manifest.long_harmonic.push((await experiment(`long-harmonic-${h}`, settings(harmonic, h, count))).file);
  }
  const quarticRun = await experiment('quartic', quartic);
  await assert.rejects(() => runLangProgram(quarticRun.model.wasm, undefined, undefined,
    { maxOutputBytes: 32 }), /output limit/);
  const doubleWellRun = await experiment('double_well', doubleWell);
  const changedQuartic = quartic.replace('param b = 0.4;', 'param b = 0.9;');
  const changedRun = await experiment('quartic_changed', changedQuartic);
  manifest.quartic_changed = changedRun.file;
  manifest.quartic = quarticRun.file; manifest.double_well = doubleWellRun.file;
  for (const [name, result] of [['quartic', quarticRun], ['double_well', doubleWellRun], ['quartic_changed', changedRun]]) {
    const json = await pipeline.runJson(result.model);
    fs.writeFileSync(path.join(output, `${name}.json`), json.text);
    assert.equal(json.document.samples.length, result.run.rows.length);
    for (const [index, row] of result.run.rows.entries()) {
      const sample = json.document.samples[index];
      assert.equal(sample.step, row.step);
      assert(Object.is(sample.time, row.time) && Object.is(sample.energy, row.energy));
      for (const [i, coordinate] of json.document.coordinates.entries()) {
        assert(Object.is(sample.q[i], row[`q_${coordinate}`]) && Object.is(sample.p[i], row[`p_${coordinate}`]));
      }
    }
  }
  const zeroSource = 'model zero { nondimensional; pair z mass 1 position -0.0 momentum -0.0; potential = 0; run step 0.01 steps 2 sample 2; }';
  const zeroJson = await pipeline.runJson(await pipeline.compileModel(zeroSource));
  assert(Object.is(zeroJson.document.samples[0].q[0], -0));
  assert(Object.is(zeroJson.document.samples[0].p[0], -0));
  fs.writeFileSync(path.join(output, 'signed-zero.json'), zeroJson.text);
  const reversal = await experiment('reversal', quartic, ['--reverse'], quarticRun.model);
  manifest.reversal = reversal.file;
  if (nativeDirectory) manifest.native_browser_pairs.push([reversal.file, path.join(nativeDirectory, 'reversal-O2.csv')]);
  const points = [[0, 0], [0.7, -0.4], [-1.2, 0.3], [0.25, -0.9], [1.1, 1.3]];
  let gradients = 'model,x,y,force_x,force_y,potential\n';
  for (const [name, compiled] of [['harmonic', harmonicModel], ['quartic', quarticRun.model], ['double_well', doubleWellRun.model], ['quartic_changed', changedRun.model]]) {
    for (const [x, y] of points) {
      const result = await pipeline.runModel(compiled, ['--forces', String(x), String(y)]);
      assert.equal(result.rows.length, 1);
      const row = result.rows[0];
      gradients += `${name},${x},${y},${row.force_x},${row.force_y},${row.potential}\n`;
    }
  }
  manifest.gradients = path.join(output, 'gradients-wasm.csv'); fs.writeFileSync(manifest.gradients, gradients);
  if (nativeDirectory) manifest.native_gradients = path.join(nativeDirectory, 'gradients-O2.csv');

  // Generic cases prevent a special-cased quartic implementation from passing.
  const free = `model free { nondimensional;
pair u mass 1 position -0.1 momentum 0.2;
pair v mass 2 position 0.3 momentum -0.4;
pair w mass 3 position -0.5 momentum 0.6;
pair z mass 4 position 0.7 momentum -0.8;
potential = u^0 - 1; run step 0.01 steps 10 sample 1; }`;
  const freeModel = await pipeline.compileModel(free);
  const last = (await pipeline.runModel(freeModel)).rows.at(-1);
  for (const [name, expected] of [['u', -.08], ['v', .28], ['w', -.48], ['z', .68]]) assert(Math.abs(last[`q_${name}`] - expected) < 1e-14);
  const power = 'model power { nondimensional; pair x mass 1 position -0.5 momentum 0; potential = x^8; run step 0.01 steps 1 sample 1; }';
  const force8 = (await pipeline.runModel(await pipeline.compileModel(power), ['--forces', '-0.5'])).rows[0].force_x;
  assert.equal(force8, .0625);
  const cancellation = power.replace('x^8', '(0.3-0.30000000000000002)*x');
  const canceled = (await pipeline.runModel(await pipeline.compileModel(cancellation), ['--forces', '1'])).rows[0].force_x;
  assert.equal(canceled, -(0.3 - 0.30000000000000002));
  const generic = `model generic { nondimensional;
pair u mass 1.1 position -0.2 momentum 0.1;
pair v mass 2.3 position 0.4 momentum -0.3;
pair w mass 0.7 position -0.6 momentum 0.2;
potential = ((-u)^3-2*u*v+v^2*w)/(2+2)+(u-w)^4/5-0.25*w^2;
run step 0.01 steps 73 sample 1; }`;
  const genericModel = await pipeline.compileModel(generic);
  const genericGradients = [];
  for (const [u, v, w] of [[0, 0, 0], [-.2, .4, -.6], [1.1, -.7, .3]]) {
    const actual = (await pipeline.runModel(genericModel, ['--forces', String(u), String(v), String(w)])).rows[0];
    // Independently handwritten analytic derivatives, outside shipped JS.
    const expected = [(3*u*u + 2*v)/4 - .8*(u-w)**3,
      (u - v*w)/2, -v*v/4 + .8*(u-w)**3 + .5*w];
    ['u', 'v', 'w'].forEach((key, index) => assert(Math.abs(actual[`force_${key}`] - expected[index]) < 5e-13));
    genericGradients.push({ point: [u, v, w], actual, expected });
  }
  const genericReverse = (await pipeline.runModel(genericModel, ['--reverse'])).rows;
  for (const key of ['q_u', 'q_v', 'q_w', 'p_u', 'p_v', 'p_w']) {
    assert(Math.abs(genericReverse[0][key] - genericReverse[1][key]) < 5e-10);
  }
  fs.writeFileSync(path.join(output, 'generic-three-coordinate.json'), JSON.stringify(genericGradients, null, 2));
  const invalid = [
    ['zero mass', 'mass m position', 'mass 0 position', 'mass must be'],
    ['negative mass', 'mass m position', 'mass -1 position', 'mass must be'],
    ['unknown symbol', 'k*(x^2+y^2)', 'missing*(x^2+y^2)', 'unknown symbol'],
    ['state denominator', '/2 + a', '/x + a', 'state-independent'],
    ['rounded zero denominator', '/2 + a', '/(0.2+0.1-0.30000000000000003) + a', 'nonzero'],
    ['fractional power', 'x^4', 'x^0.5', 'integer'],
    ['out of range power', 'x^4', 'x^9', 'bound'],
    ['function', 'x^4', 'sin(x)', 'expected'],
    ['momentum dependent', 'x^4', 'p_x^2', 'unknown symbol'],
    ['invalid step', 'step 0.01', 'step -0.01', 'step must be'],
    ['invalid count', 'steps 368', 'steps 0', 'bound'],
    ['invalid sample', 'sample 1', 'sample 369', 'sample stride'],
    ['unsupported kinetics', 'potential =', 'kinetic = x^2; potential =', 'expected'],
    ['nonfinite constant', 'param a = 0.6;', 'param a = NaN;', 'unknown constant'],
  ];
  const rejections = [];
  for (const [name, before, after, message] of invalid) {
    const source = quartic.replace(before, after);
    await assert.rejects(() => pipeline.compileModel(source), error => {
      assert.equal(error.phase, 'derive forces'); assert(error.message.includes(message), error.message);
      const location = /hamiltonian:(\d+):(\d+):/.exec(error.message);
      assert(location, error.message);
      const selection = diagnosticSelection(source, Number(location[1]), Number(location[2]));
      assert(selection.start < selection.end);
      rejections.push({ name, diagnostic: error.message, selected: source.slice(selection.start, selection.end) });
      return true;
    });
  }
  const unstable = power.replace('position -0.5', `position ${'9'.repeat(128)}`);
  const unstableModel = await pipeline.compileModel(unstable);
  await assert.rejects(() => pipeline.runModel(unstableModel), error => error.exit === 3 && error.message.includes('nonfinite'));
  await assert.rejects(() => pipeline.runJson(unstableModel), error => error.exit === 3 && error.message.includes('nonfinite'));
  await assert.rejects(() => pipeline.runModel(quarticRun.model, ['--forces', 'NaN', '0']), error => error.exit === 2 && error.message.includes('invalid decimal'));
  assert.throws(() => parseScientificCsv('step,time,energy\n0,0,NaN\n'), /nonfinite/);

  fs.writeFileSync(path.join(output, 'manifest.json'), JSON.stringify(manifest, null, 2));
  fs.writeFileSync(path.join(output, 'commands.json'), JSON.stringify({ compilerPath, nativeDirectory,
    compilerSha256: crypto.createHash('sha256').update(compilerBytes).digest('hex'),
    stdlibSha256: crypto.createHash('sha256').update(fs.readFileSync('web/stdlib.json')).digest('hex'),
    seconds: (performance.now() - started) / 1000, receipts, rejections }, null, 2));
  execFileSync('python3', ['test/hamiltonian_browser_reference.py', path.join(output, 'manifest.json'),
    '--output', path.join(output, 'numerical-report.json')], { stdio: 'inherit' });
  const report = JSON.parse(fs.readFileSync(path.join(output, 'numerical-report.json'), 'utf8'));
  console.log(`PASS real ham reader → AST → direct-Wasm science (${receipts.length} runs, ${rejections.length} located rejections, native parity ${report.native_parity_verified})`);
})().catch(error => { console.error(error.stack || error); process.exit(1); });
