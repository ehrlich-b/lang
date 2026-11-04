'use strict';
importScripts('program_host.js');
function readCString(instance, pointer) {
  const bytes = new Uint8Array(instance.exports.memory.buffer);
  const start = Number(pointer);
  let end = start;
  while (end < bytes.length && bytes[end] !== 0) end++;
  return new TextDecoder().decode(bytes.subarray(start, end));
}
self.onmessage = async ({ data }) => {
  try {
    const result = await runLangProgram(data.program, undefined, data.source, data.readerContext);
    const ast = result.value === 0n ? null : readCString(result.instance, result.value);
    self.postMessage({ ast, stdout: result.stdout, stderr: result.stderr });
  } catch (error) {
    self.postMessage({ error: String(error) });
  }
};
