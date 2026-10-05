'use strict';
importScripts('numeric_host.js?v=science1', 'compiler_host.js?v=science1',
  'program_host.js?v=science1', 'science_pipeline.js?v=science1');

let pipeline;
let compiled;
let compiledSource;
let busy = false;
async function initialize() {
  const responses = await Promise.all([fetch('compiler.wasm?v=science1'), fetch('stdlib.json?v=science1')]);
  for (const response of responses) if (!response.ok) throw new Error(`scientific compiler asset: HTTP ${response.status}`);
  const [bytes, files] = await Promise.all([responses[0].arrayBuffer(), responses[1].json()]);
  pipeline = LangScience.createSciencePipeline(bytes, files);
  postMessage({ type: 'ready', presets: {
    quartic: files['example/hamiltonian/quartic.ham'],
    double_well: files['example/hamiltonian/double_well.ham'],
    harmonic: files['example/hamiltonian/quartic.ham']
      .replace('model quartic {', 'model harmonic {')
      .replace('param a = 0.6;', 'param a = 0.0;').replace('param b = 0.4;', 'param b = 0.0;'),
  } });
}
const ready = initialize().catch(error => postMessage({ type: 'error', phase: 'load compiler', message: String(error) }));

onmessage = async ({ data }) => {
  if (busy) return;
  busy = true;
  try {
    await ready;
    if (!pipeline) throw new Error('scientific compiler assets failed to load');
    const progress = phase => postMessage({ type: 'progress', phase });
    const reused = compiled && compiledSource === data.source;
    if (!compiled || compiledSource !== data.source) {
      compiled = await pipeline.compileModel(data.source, progress);
      compiledSource = data.source;
    }
    const trajectory = await pipeline.runModel(compiled, data.args || [], progress);
    let jsonText;
    let jsonMilliseconds = 0;
    if (!(data.args || []).length) {
      // Export the generated solver's JSON verbatim. Re-serializing parsed
      // CSV with JSON.stringify would lose signed zero and change the schema.
      const json = await pipeline.runJson(compiled, progress);
      if (json.document.samples.length !== trajectory.rows.length) throw new Error('CSV/JSON sample count differs');
      for (let i = 0; i < trajectory.rows.length; i++) {
        const row = trajectory.rows[i], sample = json.document.samples[i];
        if (row.step !== sample.step || !Object.is(row.time, sample.time) || !Object.is(row.energy, sample.energy) ||
            json.document.coordinates.some((q, j) => !Object.is(row[`q_${q}`], sample.q[j]) || !Object.is(row[`p_${q}`], sample.p[j]))) {
          throw new Error('CSV/JSON numeric values differ');
        }
      }
      jsonText = json.text;
      jsonMilliseconds = json.milliseconds;
    }
    postMessage({ type: 'result', ...compiled, readerBytes: undefined, ...trajectory,
      jsonText,
      milliseconds: trajectory.milliseconds + jsonMilliseconds,
      phases: reused ? [{ name: 'reuse solver', milliseconds: 0 }] : compiled.phases,
      args: data.args || [] });
  } catch (error) {
    postMessage({ type: 'error', phase: error.phase || 'compile experiment',
      message: error.message || String(error), exit: error.exit });
  } finally { busy = false; }
};
