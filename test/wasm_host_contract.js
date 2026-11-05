'use strict';
const assert = require('node:assert/strict');
const { test } = require('node:test');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const {
  runLangProgram, LangWasmTargetLimitError, LANG_WASM_INITIAL_MEMORY_PAGES,
} = require('../web/program_host.js');
const { runLangWasm } = require('../web/host.js');

const root = path.resolve(__dirname, '..');
const compiler = path.resolve(root, process.env.COMPILER || 'out/lang_next');
const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'wasm-host-contract-'));
const env = { ...process.env, LANGBE: 'wasm', LANGOS: 'wasm',
  LANG_CACHE: path.join(directory, 'cache') };
function compile(input, output, extra = []) {
  execFileSync(compiler, [input, ...extra, '-o', output], { cwd: root, env });
  return fs.readFileSync(output);
}
let reader, program, llvmProgram, expectedAst;
async function preparePair() {
  execFileSync('python3', ['scripts/build_receipt.py', 'check', '--input',
    process.env.COMPILER_RECEIPT || 'out/build-receipt.json', '--compiler', compiler],
  { cwd: root });
  reader = compile('test/wasm_host_contract_reader.lang', path.join(directory, 'reader.wasm'));
  const read = await runLangProgram(reader, undefined, 'answer 42');
  const bytes = new Uint8Array(read.instance.exports.memory.buffer);
  let end = Number(read.value);
  while (bytes[end]) end++;
  expectedAst = Buffer.from(bytes.subarray(Number(read.value), end)).toString('utf8');
  assert.match(expectedAst, /\(number 42\)/);
  const astPath = path.join(directory, 'program.ast');
  fs.writeFileSync(astPath, expectedAst);
  program = compile(astPath, path.join(directory, 'program.wasm'), ['--from-ast']);
  // One real LLVM/wasm32 program and its native twin protect the existing ABI.
  for (const target of ['wasm', 'linux']) {
    const ir = path.join(directory, `${target}.ll`);
    const output = path.join(directory, target === 'wasm' ? 'llvm.wasm' : 'native');
    execFileSync(compiler, ['test/direct_wasm_import_e2e.lang', '-o', ir], {
      cwd: root, env: { ...env, LANGBE: 'llvm', LANGOS: target },
    });
    const flags = target === 'wasm' ? ['--target=wasm32-unknown-unknown', '-nostdlib',
      '-Wl,--no-entry', '-Wl,--export-all', '-Wl,--allow-undefined'] : [];
    execFileSync('clang', [...flags, ir, '-o', output]);
    if (target === 'wasm') llvmProgram = fs.readFileSync(output);
    else {
      const ran = require('node:child_process').spawnSync(output, [], { encoding: 'utf8' });
      assert.equal(ran.status, 17);
      assert.equal(ran.stdout, 'direct import\n');
    }
  }
}
async function recover() {
  const read = await runLangProgram(reader, undefined, 'answer 42');
  const bytes = new Uint8Array(read.instance.exports.memory.buffer);
  const actual = Buffer.from(bytes.subarray(Number(read.value), Number(read.value) + Buffer.byteLength(expectedAst))).toString('utf8');
  assert.equal(actual, expectedAst);
  assert.equal((await runLangProgram(program)).value, 42n);
}

const uleb = value => {
  const out = [];
  do { const byte = value & 127; value = Math.floor(value / 128); out.push(byte | (value ? 128 : 0)); } while (value);
  return out;
};
const str = value => [...uleb(Buffer.byteLength(value)), ...Buffer.from(value)];
const section = (id, data) => [id, ...uleb(data.length), ...data];
function fixture(namespace, { name = 'getpid', kind = 0, minimum = 1,
  maximum, entry = 'main', memoryExport = true, call = false, trap = false, custom = false } = {}) {
  const descriptor = kind === 0 ? [0, 0] : kind === 1 ? [1, 0x70, 0, 1]
    : kind === 2 ? [2, 0, 1] : [3, 0x7e, 0];
  const code = trap ? [0, 0, 0x0b] : call ? [0, 0x10, 0, 0x0b] : [0, 0x42, 0, 0x0b];
  const exports = [...str(entry), 0, kind === 0 ? 1 : 0];
  if (memoryExport) exports.push(...str('memory'), 2, 0);
  return Uint8Array.from([0, 97, 115, 109, 1, 0, 0, 0,
    ...section(1, [1, 0x60, 0, 1, 0x7e]),
    ...section(2, [1, ...str(namespace), ...str(name), ...descriptor]),
    ...section(3, [1, 0]),
    ...(custom ? section(0, [...str('padding'), ...Array(140).fill(0)]) : []),
    ...(kind === 2 ? [] : section(5, [1, maximum === undefined ? 0 : 1, ...uleb(minimum),
      ...(maximum === undefined ? [] : uleb(maximum))])),
    ...section(7, [memoryExport ? 2 : 1, ...exports]),
    ...section(10, [1, ...uleb(code.length), ...code]),
  ]);
}
const hosts = [['lang', runLangProgram], ['env', runLangWasm]];
async function rejectBeforeInstantiation(run, bytes, expected) {
  const original = WebAssembly.instantiate;
  let calls = 0;
  WebAssembly.instantiate = (...args) => { calls++; return original(...args); };
  try {
    await assert.rejects(() => run(bytes, () => {}), error => {
      assert.ok(error instanceof LangWasmTargetLimitError);
      assert.ok(error instanceof WebAssembly.LinkError); // existing callers can still catch LinkError
      assert.equal(error.code, 'LANG_WASM_TARGET_LIMIT');
      assert.match(error.message, /^Wasm target limit:/);
      for (const pattern of expected) assert.match(error.message, pattern);
      return true;
    });
    assert.equal(calls, 0, 'rejected modules must never instantiate');
  } finally { WebAssembly.instantiate = original; }
  await recover();
}

test('valid imports use each actual host; generated reader and program execute', async () => {
  await preparePair();
  let output = '';
  assert.equal((await runLangWasm(llvmProgram, text => { output += text; })).exit, 17);
  assert.equal(output, 'direct import\n');
  for (const [namespace, run] of hosts) {
    // Import every documented name against the actual function object.
    const names = `read write open close stat unlink mkdir rmdir getcwd mmap munmap
      malloc calloc free memcpy memmove memset getenv getpid getppid fork execve
      waitpid pipe dup2 exit _exit printf`.split(/\s+/);
    for (const name of names) assert.equal((await run(fixture(namespace, { name }), () => {})).exit, 0);
    const bytes = fixture(namespace, { custom: true, call: true });
    assert.equal((await run(bytes, () => {})).exit, 1);
    // BufferSource views must respect their offset and length.
    const padded = Buffer.concat([Buffer.from([255]), bytes, Buffer.from([255])]);
    assert.equal((await run(padded.subarray(1, -1), () => {})).exit, 1);
    assert.equal((await run(bytes.buffer, () => {})).exit, 1);
  }
  await assert.rejects(() => runLangProgram(fixture('lang', { trap: true })), WebAssembly.RuntimeError);
  assert.deepEqual(await runLangWasm(fixture('env', { trap: true }), () => {}), { exit: 139, trapped: true });
  await recover();
});
test('misspelled functions, inherited names and wrong import kinds are target limits', async () => {
  for (const [namespace, run] of hosts) {
    for (const name of ['getpdi', 'toString', '__proto__']) {
      await rejectBeforeInstantiation(run, fixture(namespace, { name }),
        [new RegExp(`"${namespace}"\\."${name}"`), /\(function\)/]);
    }
    for (const [kind, label] of [[1, 'table'], [2, 'memory'], [3, 'global']]) {
      await rejectBeforeInstantiation(run, fixture(namespace, { kind }),
        [new RegExp(`"${namespace}"\\."getpid"`), new RegExp(`\\(${label}\\)`)]);
    }
  }
});
test('wrong modules report their concrete namespace and name', async () => {
  for (const [namespace, run] of hosts) {
    for (const wrong of [namespace === 'lang' ? 'env' : 'lang', 'wasi_snapshot_preview1']) {
      await rejectBeforeInstantiation(run, fixture(wrong),
        [new RegExp(`"${wrong}"\\."getpid"`), /\(function\)/]);
    }
  }
});
test('memory minimum is checked against the cap before allocation', async () => {
  for (const [namespace, run] of hosts) {
    for (const maximum of [undefined, LANG_WASM_INITIAL_MEMORY_PAGES + 2]) {
      await rejectBeforeInstantiation(run, fixture(namespace, {
        minimum: LANG_WASM_INITIAL_MEMORY_PAGES + 1, maximum, custom: true,
      }), [/minimum 4097 pages \(268500992 bytes\)/, /cap 4096 pages \(268435456 bytes\)/]);
    }
    // A larger declared maximum is a possible future growth, not an initial allocation.
    assert.equal((await run(fixture(namespace, { maximum: 65536 }), () => {})).exit, 0);
    await rejectBeforeInstantiation(run, fixture('unsupported', {
      minimum: LANG_WASM_INITIAL_MEMORY_PAGES + 1,
    }), [/unsupported import/, /memory 0 minimum/]);
  }
});
test('missing or wrongly typed entry and memory exports are target limits', async () => {
  for (const [namespace, run] of hosts) {
    await rejectBeforeInstantiation(run, fixture(namespace, { entry: 'other' }),
      [/requires export "main" \(function\)/]);
    await rejectBeforeInstantiation(run, fixture(namespace, { memoryExport: false }),
      [/requires export "memory" \(memory\)/]);
    // A memory named main does not satisfy the function entry contract.
    const wrong = Uint8Array.from([0, 97, 115, 109, 1, 0, 0, 0,
      ...section(5, [1, 0, 1]), ...section(7, [1, ...str('main'), 2, 0])]);
    await rejectBeforeInstantiation(run, wrong, [/requires export "main" \(function\)/]);
  }
});
test('malformed binaries stay compile errors and a valid pair still executes', async () => {
  for (const [, run] of hosts) {
    for (const bytes of [new Uint8Array([0, 97]), fixture('lang').subarray(0, 12)]) {
      await assert.rejects(() => run(bytes, () => {}), error =>
        error instanceof WebAssembly.CompileError && !(error instanceof LangWasmTargetLimitError));
      await recover();
    }
  }
});
