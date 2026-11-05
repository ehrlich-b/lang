'use strict';
// A separate worker and budget for each final program; no reader is transferred.
function startProgram(program, deadlineMs = 2000, outputLimitBytes = 65536) {
  if (!Number.isFinite(deadlineMs) || deadlineMs <= 0 || deadlineMs > 60000) {
    throw new Error('program deadline must be between 0 and 60000 ms');
  }
  if (!Number.isInteger(outputLimitBytes) || outputLimitBytes <= 0 || outputLimitBytes > 1048576) {
    throw new Error('program output limit must be between 1 and 1048576 bytes');
  }
  const worker = new Worker('program_worker.js');
  let finish;
  const promise = new Promise((resolve, reject) => {
    let settled = false;
    const timer = setTimeout(() => finish(new Error('program timed out')), deadlineMs);
    finish = (error, result) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      worker.terminate();
      if (error) reject(error); else resolve(result);
    };
    worker.onmessage = ({ data }) => {
      const message = data.error || (data.exited && data.exit !== 0
        ? `program exited with code ${data.exit}` : '');
      finish(message ? new Error(`${message}${data.stdout || data.stderr ? `\n\n${data.stdout}${data.stderr}` : ''}`) : null, data);
    };
    worker.onerror = event => finish(new Error(event.message || 'program worker failed'));
    try { worker.postMessage({ program, outputLimitBytes }); } catch (error) { finish(error); }
  });
  return { promise, cancel: () => finish(new Error('program cancelled')) };
}
