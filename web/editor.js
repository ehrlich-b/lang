// Tiny textarea editing layer for the dependency-free reader workbench.
'use strict';

function codeEdit(value, start, end, key, shiftKey) {
  if (key === 'Enter') {
    const lineStart = value.lastIndexOf('\n', start - 1) + 1;
    const before = value.slice(lineStart, start);
    const indent = (before.match(/^[ \t]*/) || [''])[0];
    const extra = /[{:][ \t]*$/.test(before) ? '    ' : '';
    const text = `\n${indent}${extra}`;
    return { from: start, to: end, text, start: start + text.length, end: start + text.length };
  }
  if (key !== 'Tab') return null;

  if (start === end && !shiftKey) {
    return { from: start, to: end, text: '    ', start: start + 4, end: start + 4 };
  }

  const blockStart = value.lastIndexOf('\n', start - 1) + 1;
  if (start === end) {
    const line = value.slice(blockStart);
    const match = line.match(/^(?: {1,4}|\t)/);
    if (!match) return { from: start, to: end, text: '', start, end };
    const removed = match[0].length;
    return {
      from: blockStart,
      to: blockStart + removed,
      text: '',
      start: Math.max(blockStart, start - removed),
      end: Math.max(blockStart, end - removed),
    };
  }

  const lastSelected = value[end - 1] === '\n' ? end - 1 : end;
  const newline = value.indexOf('\n', lastSelected);
  const blockEnd = newline < 0 ? value.length : newline;
  const lines = value.slice(blockStart, blockEnd).split('\n');
  const text = shiftKey
    ? lines.map(line => line.replace(/^(?: {1,4}|\t)/, '')).join('\n')
    : lines.map(line => `    ${line}`).join('\n');
  return {
    from: blockStart,
    to: blockEnd,
    text,
    start: blockStart,
    end: blockStart + text.length,
  };
}

function installCodeEditor(editor, onChange) {
  editor.addEventListener('keydown', event => {
    if (editor.readOnly || editor.disabled || event.metaKey || event.ctrlKey || event.altKey) return;
    const edit = codeEdit(
      editor.value, editor.selectionStart, editor.selectionEnd, event.key, event.shiftKey,
    );
    if (!edit) return;
    event.preventDefault();
    editor.setRangeText(edit.text, edit.from, edit.to, 'start');
    editor.setSelectionRange(edit.start, edit.end);
    if (onChange) onChange();
  });
}

// Compiler columns count UTF-8 bytes; textarea selections count UTF-16 units.
function diagnosticSelection(value, line, column) {
  const lines = value.split('\n');
  const row = Math.max(0, Math.min(line - 1, lines.length - 1));
  let start = lines.slice(0, row).reduce((size, text) => size + text.length + 1, 0);
  let bytes = 0;
  for (const character of lines[row]) {
    const width = new TextEncoder().encode(character).length;
    if (bytes + width > column - 1) break;
    bytes += width;
    start += character.length;
  }
  let end = start;
  while (end < value.length && /[A-Za-z0-9_]/.test(value[end])) end++;
  if (end === start) end = Math.min(start + (value.codePointAt(start) > 65535 ? 2 : 1), value.length);
  return { start, end };
}

if (typeof module !== 'undefined') module.exports = { codeEdit, installCodeEditor, diagnosticSelection };
