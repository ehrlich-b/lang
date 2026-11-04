'use strict';
// Each invocation owns its worker and settles exactly once, including cancellation.
function startReader(program, source, deadlineMs = 2000, readerContext) {
  if (!Number.isFinite(deadlineMs) || deadlineMs <= 0 || deadlineMs > 60000) {
    throw new Error('reader deadline must be between 0 and 60000 ms');
  }
  const worker = new Worker('reader_worker.js');
  let finish;
  const promise = new Promise((resolve, reject) => {
    let settled = false;
    const timer = setTimeout(() => finish(new Error('reader timed out')), deadlineMs);
    finish = (error, result) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      worker.terminate();
      if (error) reject(error); else resolve(result);
    };
    worker.onmessage = ({ data }) => finish(data.error ? new Error(data.error) : null, data);
    worker.onerror = event => finish(new Error(event.message || 'reader worker failed'));
    try { worker.postMessage({ program, source, readerContext }); } catch (error) { finish(error); }
  });
  return { promise, cancel: () => finish(new Error('reader cancelled')) };
}
