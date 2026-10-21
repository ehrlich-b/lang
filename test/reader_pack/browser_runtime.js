/* Run with the same browser hosts as the reader lab, in a real browser. */
'use strict';
async function runReaderPack(payload) {
  const compiler = new Uint8Array(payload.compiler);
  const rows = [], artifacts = [];
  async function compile(args, files) {
    const result = await runLangCompiler(compiler, args, { ...payload.files, ...files }, undefined, { LANGBE: 'wasm' });
    return result;
  }
  for (const task of payload.tasks) {
    const start = performance.now();
    const built = await compile(['wrapper.lang', '-o', 'reader.wasm'], { 'wrapper.lang': task.wrapper });
    const reader = built.files.get('reader.wasm');
    if (task.compileFailure) {
      rows.push({ fixture: task.name, compileFailure: built.exit !== 0 && !reader,
        diagnostic: built.stderr, build_ms: performance.now() - start });
      continue;
    }
    if (built.exit !== 0 || !reader) throw Error(built.stderr || 'no reader module');
    artifacts.push({ name: task.name + '-reader.wasm', bytes: Array.from(reader) });
    const build_ms = performance.now() - start;
    for (const c of task.cases) {
      const begin = performance.now();
      const read = await runLangProgram(reader, undefined, c.source);
      const row = { id: c.id, fixture: task.name, split: c.split, stage: c.stage,
        backend: 'browser', build_ms, read_ms: performance.now() - begin,
        stdout: read.stdout, diagnostic: read.stderr, reader_exit: read.exit };
      if (read.value === 0n) {
        row.rejected = true;
      } else {
        const memory = new Uint8Array(read.instance.exports.memory.buffer);
        let end = Number(read.value);
        while (memory[end]) end++;
        row.ast = new TextDecoder().decode(memory.subarray(Number(read.value), end));
        const compileStart = performance.now();
        const compiled = await compile(['program.ast', '--from-ast', '-o', 'program.wasm'], { 'program.ast': row.ast });
        row.program_build_ms = performance.now() - compileStart;
        const program = compiled.files.get('program.wasm');
        if (compiled.exit || !program) throw Error(compiled.stderr || 'no program module');
        const runStart = performance.now();
        const ran = await runLangProgram(program);
        row.run_ms = performance.now() - runStart;
        row.value = Number(ran.value);
        row.program_exit = ran.exit;
        row.stdout += ran.stdout;
        row.diagnostic += ran.stderr;
        artifacts.push({ name: task.name + '-' + c.id + '.wasm', bytes: Array.from(program) });
      }
      rows.push(row);
    }
  }
  return { rows, artifacts, userAgent: navigator.userAgent };
}
