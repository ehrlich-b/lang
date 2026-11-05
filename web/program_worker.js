// Final program execution has no access to reader state or workspace files.
'use strict';
importScripts('program_host.js');
self.onmessage = async ({ data }) => {
  let stdout = '';
  let stderr = '';
  try {
    const result = await runLangProgram(data.program, (text, isError) => {
      if (isError) stderr += text; else stdout += text;
    }, undefined, { outputLimitBytes: data.outputLimitBytes });
    const { value, exit, exited } = result;
    self.postMessage({ value, exit, exited, stdout, stderr });
  } catch (error) {
    self.postMessage({ error: String(error).replace(/^Error: /, ''), stdout, stderr });
  }
};
