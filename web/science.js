'use strict';
(function () {
  const get = id => document.getElementById(id);
  const model = get('model'), preset = get('preset'), status = get('status');
  const run = get('run'), stop = get('stop');
  const actions = ['reset', 'save-model', 'force-probe', 'reverse'];
  const colors = ['#7ee787', '#79c0ff', '#ffa657', '#d2a8ff'];
  let worker, presets, busy = false, ready = false, activePreset, trajectory, lastResult, pendingAction, saveTimer;
  const downloads = new Map();
  const storage = {
    get(key) { try { return localStorage.getItem(`lang.science.${key}`); } catch (_) { return null; } },
    set(key, value) { try { localStorage.setItem(`lang.science.${key}`, value); } catch (_) {} },
  };

  function save() {
    if (!activePreset) return;
    storage.set(activePreset, model.value); storage.set('preset', activePreset);
  }
  function changed() {
    clearTimeout(saveTimer); saveTimer = setTimeout(save, 200);
    syncCoupling();
    if (lastResult && lastResult.source !== model.value) {
      status.className = '';
      status.textContent = 'Model changed. Compile to update the trajectory and exports.';
      for (const id of ['csv-download', 'json-download', 'wasm-download', 'ast-download']) get(id).hidden = true;
    }
    if (trajectory && trajectory.source !== model.value) get('trajectory-title').textContent = 'Previous trajectory';
  }
  function syncCoupling() {
    const match = model.value.match(/^\s*param b\s*=\s*(-?\d+(?:\.\d+)?);/m);
    get('coupling-control').hidden = !match || Number(match[1]) < 0 || Number(match[1]) > 1;
    if (match) { get('coupling').value = match[1]; get('coupling-value').textContent = match[1]; }
  }
  function selectExample(reset = false) {
    clearTimeout(saveTimer);
    const saved = reset ? null : storage.get(preset.value);
    model.value = saved === null ? presets[preset.value] : saved;
    activePreset = preset.value;
    storage.set('preset', preset.value); changed();
  }
  function setBusy(value) {
    busy = value; run.disabled = value || !ready; model.disabled = value || !ready;
    preset.disabled = value || !ready; stop.hidden = !value;
    for (const id of actions) get(id).disabled = value || !ready;
    get('coupling').disabled = value || !ready; get('open-model').disabled = value || !ready;
  }
  function clearError() { get('diagnostic').hidden = true; get('diagnostic').textContent = ''; status.className = ''; }
  function diagnostic(message) {
    const match = message.match(/(?:hamiltonian|model\.ham):(\d+):(\d+):/);
    if (!match) return;
    const selection = diagnosticSelection(model.value, Number(match[1]), Number(match[2]));
    model.focus(); model.setSelectionRange(selection.start, selection.end);
    const before = model.value.slice(0, selection.start).split('\n').length;
    model.scrollTop = Math.max(0, (before - 4) * 21);
  }
  function phase(name) {
    const phases = [...document.querySelectorAll('[data-phase]')];
    const active = phases.findIndex(el => el.dataset.phase === name);
    phases.forEach((el, index) => {
      el.className = index === active ? 'active' : active >= 0 && index < active ? 'done' : '';
    });
    status.textContent = `${name}…`;
  }
  function startWorker() {
    ready = false; setBusy(false); get('restart').hidden = true;
    worker = new Worker('science_worker.js?v=science1');
    const currentWorker = worker;
    worker.onmessage = ({ data }) => {
      if (worker !== currentWorker) return;
      if (data.type === 'ready') {
        ready = true;
        presets = data.presets;
        if (!activePreset) {
          const saved = storage.get('preset');
          if (presets[saved]) preset.value = saved;
          selectExample();
        }
        setBusy(false); status.textContent = 'Ready. Edit the potential or coupling, then compile + run.';
      } else if (data.type === 'progress') phase(data.phase);
      else if (data.type === 'error') {
        setBusy(false); status.className = 'error'; status.textContent = `${data.phase} failed`;
        get('diagnostic').textContent = data.message; get('diagnostic').hidden = false;
        if (!ready) get('restart').hidden = false;
        diagnostic(data.message);
      } else if (data.type === 'result') {
        setBusy(false);
        lastResult = data;
        get('forces').textContent = data.functions.map(fn => fn.ast).join('\n\n');
        get('ast').textContent = data.ast;
        const coordinates = data.headers.filter(header => header.startsWith('q_'));
        document.querySelector('label[for="probe"]').textContent = `Coordinates (${coordinates.map(key => key.slice(2)).join(', ')})`;
        if (get('probe').value.trim().split(/\s+/).length !== coordinates.length) {
          get('probe').value = coordinates.map(() => '0').join(' ');
        }
        if (pendingAction === 'trajectory') showTrajectory(data);
        else showProbe(data);
        status.className = 'success';
        const build = data.phases.reduce((total, item) => total + item.milliseconds, 0);
        status.textContent = `${pendingAction === 'trajectory' ? 'Experiment complete' : 'Inspection complete'} · ${data.wasm.byteLength.toLocaleString()} byte Wasm · build ${Math.round(build)} ms · run ${Math.round(data.milliseconds)} ms`;
        for (const el of document.querySelectorAll('[data-phase]')) el.className = 'done';
      }
    };
    worker.onerror = event => {
      if (worker !== currentWorker) return;
      worker.terminate(); ready = false;
      setBusy(false); status.className = 'error'; status.textContent = 'Scientific worker failed';
      get('diagnostic').textContent = `${event.message || 'Worker failed.'}\nRestart the compiler; your model is preserved.`;
      get('diagnostic').hidden = false;
      get('restart').hidden = false;
    };
  }
  function request(action, args = []) {
    if (busy || !ready) return;
    save(); clearError(); setBusy(true); pendingAction = action;
    if (action === 'trajectory') {
      for (const id of ['csv-download', 'json-download', 'wasm-download', 'ast-download']) get(id).hidden = true;
    }
    worker.postMessage({ source: model.value, args });
  }
  function download(id, value, name, type) {
    if (downloads.has(id)) URL.revokeObjectURL(downloads.get(id));
    const url = URL.createObjectURL(new Blob([value], { type })); downloads.set(id, url);
    const anchor = get(id); anchor.href = url; anchor.download = name; anchor.hidden = false;
  }
  function saveFile(value, name, type) {
    const anchor = document.createElement('a');
    const url = URL.createObjectURL(new Blob([value], { type }));
    anchor.href = url; anchor.download = name; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function modelName(source) { return source.match(/\bmodel\s+([A-Za-z_][A-Za-z0-9_]*)/)?.[1] || 'experiment'; }
  function showTrajectory(data) {
    trajectory = data;
    get('trajectory-title').textContent = 'Compiled trajectory';
    const name = modelName(data.source);
    download('csv-download', data.text, `${name}.csv`, 'text/csv');
    download('json-download', data.jsonText, `${name}.json`, 'application/json');
    download('wasm-download', data.wasm, `${name}.wasm`, 'application/wasm');
    download('ast-download', data.ast + '\n', `${name}.ast`, 'text/plain');
    sampleTable(data); drawPlot();
    const first = data.rows[0], last = data.rows.at(-1);
    const energyError = Math.max(...data.rows.slice(0, 5000).map(row => Math.abs(row.energy - first.energy)));
    // Avoid spreading a potentially million-row array into a function call.
    let maximum = energyError;
    for (const row of data.rows.slice(5000)) maximum = Math.max(maximum, Math.abs(row.energy - first.energy));
    get('stats').textContent = `${data.rows.length.toLocaleString()} samples · t = ${last.time} · max sampled |H − H₀| = ${maximum.toPrecision(6)}. This is measured error, not an exact conservation claim.`;
  }
  function sampleTable(data) {
    const table = get('samples'); table.replaceChildren();
    const head = table.createTHead().insertRow();
    for (const header of data.headers) { const cell = document.createElement('th'); cell.textContent = header; head.append(cell); }
    const body = table.createTBody();
    const raw = data.text.trim().split(/\r?\n/).slice(1);
    const indices = data.rows.length <= 7 ? data.rows.map((_, index) => index)
      : [0, 1, 2, 3, 4, data.rows.length - 2, data.rows.length - 1];
    indices.forEach(index => {
      const row = body.insertRow();
      for (const text of raw[index].split(',')) row.insertCell().textContent = text;
    });
  }
  function showProbe(data) {
    const output = get('probe-output');
    if (data.args[0] !== '--reverse') { output.textContent = data.text; return; }
    const [first, last] = data.rows;
    const state = data.headers.filter(header => /^[qp]_/.test(header));
    const error = Math.max(...state.map(header => Math.abs(last[header] - first[header])));
    output.textContent = `Maximum full-state return error: ${error.toPrecision(17)}\n${data.text}`;
  }
  function drawPlot() {
    const canvas = get('plot');
    const width = canvas.clientWidth, height = canvas.clientHeight;
    const ratio = window.devicePixelRatio || 1;
    canvas.width = Math.round(width * ratio); canvas.height = Math.round(height * ratio);
    const ctx = canvas.getContext('2d'); ctx.scale(ratio, ratio); ctx.clearRect(0, 0, width, height);
    ctx.font = '11px ui-monospace, monospace'; ctx.fillStyle = '#9da7b3';
    if (!trajectory) { ctx.fillText('Compile a model to see its trajectory.', 18, height / 2); return; }
    const coordinates = trajectory.headers.filter(header => header.startsWith('q_'));
    const phaseOption = get('plot-mode').querySelector('[value="phase"]');
    phaseOption.disabled = coordinates.length < 2;
    if (phaseOption.disabled && get('plot-mode').value === 'phase') get('plot-mode').value = 'coordinates';
    const mode = get('plot-mode').value;
    const keys = mode === 'energy' ? ['energy'] : mode === 'momenta'
      ? trajectory.headers.filter(header => header.startsWith('p_')) : coordinates;
    const e0 = trajectory.rows[0].energy;
    const phasePlane = mode === 'phase' && coordinates.length >= 2;
    const xKey = phasePlane ? coordinates[0] : 'time';
    const shown = phasePlane ? [coordinates[1]] : keys;
    const values = row => shown.map(key => mode === 'energy' ? row.energy - e0 : row[key]);
    let xmin = Infinity, xmax = -Infinity, ymin = Infinity, ymax = -Infinity;
    for (const row of trajectory.rows) {
      xmin = Math.min(xmin, row[xKey]); xmax = Math.max(xmax, row[xKey]);
      for (const value of values(row)) { ymin = Math.min(ymin, value); ymax = Math.max(ymax, value); }
    }
    if (xmin === xmax) {
      const padding = Math.max(1, Math.abs(xmin)) * .05;
      xmin -= padding; xmax += padding;
    }
    if (ymin === ymax) {
      const padding = Math.max(1, Math.abs(ymin)) * .05;
      ymin -= padding; ymax += padding;
    }
    const margin = { left: 66, right: 15, top: 18, bottom: 30 };
    const plotWidth = width - margin.left - margin.right, plotHeight = height - margin.top - margin.bottom;
    const px = value => margin.left + (value - xmin) / (xmax - xmin) * plotWidth;
    const py = value => margin.top + (ymax - value) / (ymax - ymin) * plotHeight;
    ctx.strokeStyle = '#30363d';
    for (let i = 0; i <= 4; i++) {
      const fraction = i / 4, y = margin.top + fraction * plotHeight;
      ctx.beginPath(); ctx.moveTo(margin.left, y); ctx.lineTo(width - margin.right, y); ctx.stroke();
      ctx.fillText((ymax - fraction * (ymax - ymin)).toPrecision(3), 2, y + 4);
    }
    ctx.fillText(xmin.toPrecision(3), margin.left, height - 8);
    ctx.fillText(xmax.toPrecision(3), width - margin.right - 44, height - 8);
    ctx.fillText(phasePlane ? xKey : 'time', width / 2, height - 8);
    const stride = Math.max(1, Math.ceil(trajectory.rows.length / 3000));
    shown.forEach((key, series) => {
      ctx.strokeStyle = colors[series % colors.length]; ctx.lineWidth = 1.6; ctx.beginPath();
      for (let index = 0; index < trajectory.rows.length; index += stride) {
        const row = trajectory.rows[index], x = px(row[xKey]), y = py(values(row)[series]);
        if (index === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      const last = trajectory.rows.at(-1); ctx.lineTo(px(last[xKey]), py(values(last)[series])); ctx.stroke();
    });
    const legend = get('legend'); legend.replaceChildren();
    shown.forEach((key, index) => {
      const item = document.createElement('span'); item.style.color = colors[index % colors.length];
      item.textContent = mode === 'energy' ? 'H − H₀' : key; legend.append(item);
    });
    canvas.setAttribute('aria-label', `${shown.join(', ')} versus ${xKey}, ${trajectory.rows.length} emitted samples. Numeric samples are in the table and CSV export.`);
  }

  installCodeEditor(model, changed); model.addEventListener('input', changed);
  preset.addEventListener('change', () => { save(); selectExample(); });
  get('reset').onclick = () => { selectExample(true); save(); };
  run.onclick = () => request('trajectory');
  get('force-probe').onclick = () => request('forces', ['--forces', ...get('probe').value.trim().split(/\s+/)]);
  get('reverse').onclick = () => request('reverse', ['--reverse']);
  stop.onclick = () => {
    worker.terminate(); startWorker();
    status.textContent = 'Stopped. Your model is preserved; the compiler worker is restarting.';
  };
  get('restart').onclick = () => {
    worker.terminate(); clearError(); startWorker(); status.textContent = 'Restarting the compiler; your model is preserved…';
  };
  get('coupling').oninput = event => {
    model.value = model.value.replace(/^(\s*param b\s*=\s*)-?\d+(?:\.\d+)?;/m,
      (_, prefix) => `${prefix}${event.target.value};`);
    changed();
  };
  get('edit-potential').onclick = () => {
    const match = /\bpotential\s*=\s*([^;]+);/.exec(model.value);
    if (match) { const start = match.index + match[0].indexOf(match[1]); model.focus(); model.setSelectionRange(start, start + match[1].length); }
  };
  get('save-model').onclick = () => saveFile(model.value, `${modelName(model.value)}.ham`, 'text/plain');
  get('open-model').onclick = () => get('model-file').click();
  get('model-file').onchange = async event => {
    const file = event.target.files[0]; if (!file) return;
    if (file.size > 65536) { clearError(); get('diagnostic').textContent = 'Model exceeds the 65536-byte source bound.'; get('diagnostic').hidden = false; return; }
    const targetPreset = activePreset;
    try {
      const text = await file.text();
      if (activePreset === targetPreset) { model.value = text; changed(); save(); }
      else storage.set(targetPreset, text);
    } catch (error) {
      get('diagnostic').textContent = `Cannot read the model file: ${error.message || error}`;
      get('diagnostic').hidden = false;
    }
    event.target.value = '';
  };
  get('plot-mode').onchange = drawPlot;
  window.addEventListener('resize', drawPlot);
  window.addEventListener('beforeunload', save);
  document.addEventListener('keydown', event => {
    if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') { event.preventDefault(); run.click(); }
  });
  drawPlot(); startWorker();
})();
