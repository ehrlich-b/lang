#!/usr/bin/env node
'use strict';

const fs = require('fs');
const { runLangCompiler } = require('../web/compiler_host.js');
const { formatLangAst, runLangProgram } = require('../web/program_host.js');
const stdlibFiles = JSON.parse(fs.readFileSync('web/stdlib.json', 'utf8'));

const compilerPath = process.argv[2];
if (!compilerPath) {
  console.error('usage: compiler_direct_wasm_e2e.js compiler.wasm');
  process.exit(2);
}

async function compileAndRun(sourcePath) {
  const source = fs.readFileSync(sourcePath, 'utf8');
  const result = await runLangCompiler(
    fs.readFileSync(compilerPath),
    ['input.lang', '-o', 'output.wasm'],
    { ...stdlibFiles, 'input.lang': source },
    undefined,
    { LANGBE: 'wasm' },
  );
  if (result.exit !== 0) {
    process.stderr.write(result.stderr || result.stdout || `compiler exit ${result.exit}\n`);
    process.exit(result.exit || 1);
  }
  const program = result.files.get('output.wasm');
  if (!program) throw new Error('compiler did not write output.wasm');
  const ran = await runLangProgram(program);
  return { ...ran, bytes: program.byteLength };
}

async function compileReaderPipeline(readerPath, readerName, source, runtimePaths = []) {
  return compileReaderSource(
    fs.readFileSync(readerPath, 'utf8'), readerName, source, runtimePaths,
  );
}

async function compileReaderModule(sourceText, readerName) {
  const readerSource = `${sourceText}
func main() *u8 {
    var text *u8 = alloc(4194304);
    var length i64 = 0;
    var chunk i64 = file_read(0, text, 4194303);
    while chunk > 0 {
        length = length + chunk;
        if length >= 4194303 { chunk = 0; }
        else { chunk = file_read(0, text + length, 4194303 - length); }
    }
    if chunk < 0 { return nil; }
    *(text + length) = 0;
    return ${readerName}(text);
}
`;
  const readerCompile = await runLangCompiler(
    fs.readFileSync(compilerPath),
    ['reader.lang', '-o', 'reader.wasm'],
    { ...stdlibFiles, 'reader.lang': readerSource },
    undefined,
    { LANGBE: 'wasm' },
  );
  if (readerCompile.exit !== 0) {
    throw new Error(readerCompile.stderr || readerCompile.stdout || `reader compiler exit ${readerCompile.exit}`);
  }
  const readerProgram = readerCompile.files.get('reader.wasm');
  if (!readerProgram) throw new Error('compiler did not write reader.wasm');
  return readerProgram;
}

async function runReaderModule(readerProgram, source) {
  const readerRun = await runLangProgram(readerProgram, undefined, source);
  if (readerRun.value === 0n) return { ast: null, readerRun };
  const memory = new Uint8Array(readerRun.instance.exports.memory.buffer);
  let end = Number(readerRun.value);
  while (memory[end] !== 0) end++;
  const ast = Buffer.from(memory.subarray(Number(readerRun.value), end)).toString('utf8');
  return { ast, readerRun };
}

async function runReaderSource(sourceText, readerName, source) {
  return runReaderModule(await compileReaderModule(sourceText, readerName), source);
}

async function compileReaderSource(sourceText, readerName, source, runtimePaths = []) {
  const read = await runReaderSource(sourceText, readerName, source);
  if (read.ast === null) return { ...read, ran: null };
  const formattedAst = formatLangAst(read.ast);
  const sourceName = `${readerName}.source`;
  const args = ['program.ast', '--from-ast', '--ast-source', sourceName];
  for (const runtimePath of runtimePaths) args.push('--runtime', runtimePath);
  args.push('-o', 'program.wasm');

  const programCompile = await runLangCompiler(
    fs.readFileSync(compilerPath),
    args,
    { ...stdlibFiles, 'program.ast': formattedAst, [sourceName]: source },
    undefined,
    { LANGBE: 'wasm' },
  );
  if (programCompile.exit !== 0) {
    throw new Error(programCompile.stderr || programCompile.stdout || `AST compiler exit ${programCompile.exit}`);
  }
  const program = programCompile.files.get('program.wasm');
  if (!program) throw new Error('compiler did not write program.wasm');
  return { ...read, formattedAst, ran: await runLangProgram(program) };
}

(async () => {
  const arithmetic = await compileAndRun('test/direct_wasm_e2e.lang');
  if (Number(arithmetic.value) !== 42) throw new Error(`expected 42, got ${arithmetic.value}`);

  const memory = await compileAndRun('test/direct_wasm_memory_e2e.lang');
  if (Number(memory.value) !== 176) throw new Error(`expected 176, got ${memory.value}`);

  const imported = await compileAndRun('test/direct_wasm_import_e2e.lang');
  if (Number(imported.value) !== 17 || imported.stdout !== 'direct import\n') {
    throw new Error(`direct import mismatch: value=${imported.value} stdout=${JSON.stringify(imported.stdout)}`);
  }
  const ast = await compileAndRun('test/direct_wasm_ast_e2e.lang');
  if (Number(ast.value) !== 40) throw new Error(`expected AST builder to start with 40, got ${ast.value}`);
  const labeledBreak = await compileAndRun('test/suite/185_labeled_break.lang');
  if (Number(labeledBreak.value) !== 5) {
    throw new Error(`expected labeled break result 5, got ${labeledBreak.value}`);
  }
  const labeledContinue = await compileAndRun('test/suite/186_labeled_continue.lang');
  if (Number(labeledContinue.value) !== 15) {
    throw new Error(`expected labeled continue result 15, got ${labeledContinue.value}`);
  }
  const addressed = await compileAndRun('test/direct_wasm_address_e2e.lang');
  if (Number(addressed.value) !== 42) {
    throw new Error(`expected address-taken local result 42, got ${addressed.value}`);
  }

  const reader = await compileReaderPipeline('example/tiny/tiny.lang', 'tiny', 'answer 42');
  if (Number(reader.ran.value) !== 42 || !reader.ast.startsWith('(program ')) {
    throw new Error(`tiny reader pipeline mismatch: value=${reader.ran.value} ast=${reader.ast}`);
  }
  const reusableTiny = await compileReaderModule(
    fs.readFileSync('example/tiny/tiny.lang', 'utf8'), 'tiny',
  );
  const reused41 = await runReaderModule(reusableTiny, 'answer 41');
  const reused42 = await runReaderModule(reusableTiny, 'answer 42');
  if (!reused41.ast.includes('(number 41)') || !reused42.ast.includes('(number 42)')) {
    throw new Error('one reader module did not accept two different stdin inputs');
  }
  const calc = await compileReaderPipeline('example/calc/calc.lang', 'calc', 'answer 1 + 2 * 3');
  if (Number(calc.ran.value) !== 7 || !calc.ast.includes('(binop + ')) {
    throw new Error(`calc reader pipeline mismatch: value=${calc.ran.value} ast=${calc.ast}`);
  }
  const invalid = await compileReaderPipeline('example/calc/calc.lang', 'calc', 'wat');
  if (invalid.ast !== null || !invalid.readerRun.stderr.includes('expected `answer EXPRESSION`')) {
    throw new Error(`reader failure mismatch: ast=${invalid.ast} stderr=${invalid.readerRun.stderr}`);
  }
  const generated = await compileReaderPipeline(
    'test/direct_wasm_parser_reader.lang', 'parser_tiny', 'answer 42',
  );
  if (Number(generated.ran.value) !== 42 || !generated.ast.startsWith('(program ')) {
    throw new Error(`generated reader mismatch: value=${generated.ran.value} ast=${generated.ast}`);
  }
  const debugTree = await compileReaderPipeline(
    'test/pnode_dump_reader.lang', 'pdebug',
    fs.readFileSync('test/pnode_dump_source.pdebug', 'utf8'),
  );
  const expectedTree = fs.readFileSync('test/pnode_dump.expected', 'utf8');
  if (Number(debugTree.ran.value) !== 32 || debugTree.readerRun.stderr !== expectedTree) {
    throw new Error(`parse-tree dump mismatch: value=${debugTree.ran.value}\n${debugTree.readerRun.stderr}`);
  }
  const ambiguousCapture = await compileReaderPipeline(
    'test/pnode_ambiguity_reader.lang', 'pambiguity',
    fs.readFileSync('test/pnode_ambiguity_source.pambiguity', 'utf8'),
  );
  const expectedAmbiguity = fs.readFileSync('test/pnode_ambiguity.expected', 'utf8');
  if (ambiguousCapture.ast !== null ||
      ambiguousCapture.readerRun.stderr !== expectedAmbiguity) {
    throw new Error(`capture ambiguity mismatch: ast=${ambiguousCapture.ast}\n${ambiguousCapture.readerRun.stderr}`);
  }
  const badGrammars = [
    ['undefined', 'bad = missing', 'expected defined rule, found missing'],
    ['duplicate-capture', 'bad = value:number value:symbol',
      'expected capture name used once per branch, found value'],
    ['left-recursive', 'bad = prefix bad | number\nprefix = number?',
      'expected non-left-recursive rule, found bad'],
    ['nested-branch-label', 'bad = a:inner | b:number\ninner = p:symbol | q:string',
      'expected branch label on a rule that does not label its own alternatives, found a'],
  ];
  for (const [name, grammar, expected] of badGrammars) {
    const sourceName = `bad-grammar-${name}.lang`;
    const badGrammarCompile = await runLangCompiler(
      fs.readFileSync(compilerPath),
      [sourceName, '-o', `bad-grammar-${name}.wasm`],
      {
        ...stdlibFiles,
        [sourceName]: `include "std/parser_runtime.lang"
#parser{
    ${grammar}
}
func main() i64 { return 0; }
`,
      },
      undefined,
      { LANGBE: 'wasm' },
    );
    if (badGrammarCompile.exit === 0 ||
        !/#parser:\d+:\d+:/.test(badGrammarCompile.stderr) ||
        !badGrammarCompile.stderr.includes(expected)) {
      throw new Error(`browser ${name} grammar diagnostic mismatch: ${badGrammarCompile.stderr}`);
    }
  }
  // `.field` on a value with no struct type is a located error here too. The
  // browser compiles with the direct wasm backend, which infers types its own
  // way, so it needs its own guard rather than trusting the native one.
  const badFields = [
    ['untyped-base', `struct Item { name i64; }
func pick(i i64) i64 { return i; }
func main() i64 {
    if pick(0).name != 0 { return 1; }
    return 0;
}
`, "bad-field-untyped-base.lang:4:16: error: cannot access field 'name' of type i64"],
    ['misspelled', `struct Item { name i64; }
func head(it *Item) i64 { return it.nmae; }
func main() i64 { var it *Item = 0; return head(it); }
`, "error: struct 'Item' has no field 'nmae'"],
  ];
  for (const [name, source, expected] of badFields) {
    const sourceName = `bad-field-${name}.lang`;
    const badFieldCompile = await runLangCompiler(
      fs.readFileSync(compilerPath),
      [sourceName, '-o', `bad-field-${name}.wasm`],
      { [sourceName]: source },
      undefined,
      { LANGBE: 'wasm' },
    );
    if (badFieldCompile.exit === 0 || !badFieldCompile.stderr.includes(expected)) {
      throw new Error(`browser ${name} field diagnostic mismatch: ${badFieldCompile.stderr}`);
    }
    if (name === 'untyped-base' &&
        !badFieldCompile.stderr.includes('note:   var it *Item = <expr>;  then  it.name')) {
      throw new Error(`browser field note missing: ${badFieldCompile.stderr}`);
    }
  }
  const generatedSource = fs.readFileSync('test/direct_wasm_parser_reader.lang', 'utf8');
  const generatedBad = await runReaderSource(
    generatedSource, 'parser_tiny', 'bad\nmissing',
  );
  const generatedBadCompile = await runLangCompiler(
    fs.readFileSync(compilerPath),
    ['program.ast', '--from-ast', '--ast-source', 'bad.ptiny', '-o', 'bad.wasm'],
    { 'program.ast': generatedBad.ast, 'bad.ptiny': 'bad\nmissing' },
    undefined,
    { LANGBE: 'wasm' },
  );
  if (generatedBadCompile.exit === 0 ||
      !generatedBadCompile.stderr.includes('bad.ptiny:2:1: error: unknown function')) {
    throw new Error(`generated reader span mismatch: ${generatedBadCompile.stderr}`);
  }
  const forth = await compileReaderPipeline(
    'example/forth/forth.lang', 'forth', ': main ( -- n ) 42 ;',
  );
  if (Number(forth.ran.value) !== 42 || !forth.ast.startsWith('(program ')) {
    throw new Error(`forth reader mismatch: value=${forth.ran.value} ast=${forth.ast}`);
  }
  const minilisp = await compileReaderPipeline(
    'example/minilisp/minilisp.lang', 'minilisp', '(defun main () 42)',
    ['example/minilisp/lisp_runtime.lang'],
  );
  const lispPointer = Number(minilisp.ran.value);
  const lispMemory = new DataView(minilisp.ran.instance.exports.memory.buffer);
  const lispTag = lispMemory.getBigInt64(lispPointer, true);
  const lispValue = lispMemory.getBigInt64(lispPointer + 8, true);
  if (!minilisp.ast.startsWith('(program ') || !minilisp.ast.includes('lisp_int') ||
      lispTag !== 0n || lispValue !== 42n) {
    throw new Error(
      `minilisp pipeline mismatch: result=${minilisp.ran.value} tag=${lispTag} value=${lispValue}`,
    );
  }
  const cRead = await compileReaderPipeline(
    'example/c/c.lang', 'c', 'int main() { return 42; }',
  );
  if (Number(cRead.ran.value) !== 42 ||
      !cRead.ast?.startsWith('(program ') || !cRead.ast.includes('(func main ')) {
    throw new Error(`C reader mismatch: ast=${cRead.ast}`);
  }
  const flowRead = await compileReaderPipeline(
    'example/flow/flow.lang', 'flow', 'func main() { return 42; }',
  );
  if (Number(flowRead.ran.value) !== 42 ||
      !flowRead.ast?.startsWith('(program ') || !flowRead.ast.includes('(func main ')) {
    throw new Error(`Flow reader mismatch: ast=${flowRead.ast}`);
  }
  const minipyRead = await compileReaderPipeline(
    'example/minipy/minipy.lang', 'minipy', 'def main():\n    return 42\n',
  );
  if (Number(minipyRead.ran.value) !== 42 ||
      !minipyRead.ast?.startsWith('(program ') || !minipyRead.ast.includes('(func main ')) {
    throw new Error(`Minipy reader mismatch: ast=${minipyRead.ast}`);
  }

  const labHtml = fs.readFileSync('web/lab.html', 'utf8');
  for (const path of [
    'example/tiny/tiny.lang', 'example/calc/calc.lang', 'example/c/c.lang',
    'example/forth/forth.lang', 'example/minilisp/minilisp.lang',
    'example/minipy/minipy.lang', 'example/flow/flow.lang',
  ]) {
    if (stdlibFiles[path] !== fs.readFileSync(path, 'utf8')) {
      throw new Error(`browser preset is missing or stale: ${path}`);
    }
  }
  const inlineScripts = [...labHtml.matchAll(/<script>([\s\S]*?)<\/script>/g)];
  new Function(inlineScripts.at(-1)[1]);
  for (const marker of [
    'id="preset"', 'id="download-reader"', 'id="download-ast"', 'id="download-program"',
    'id="save-workspace"', 'id="open-workspace"',
    'lang-reader-workspace', 'lang.lab.active', 'readerName(reader.value)',
    'focusDiagnostic(message)', "target.closest('details').open = true", "phase = 'AST compile'",
    'cachedReaderSource !== reader.value', 'customSource.value)',
    'editor.js?v=workbench10', 'formatLangAst(ast)', 'value:number',
    "'program.ast': formattedAst", 'installCodeEditor(reader, queueSave)',
  ]) {
    if (!labHtml.includes(marker)) throw new Error(`lab workbench marker missing: ${marker}`);
  }
  const labSource = labHtml.match(/<textarea[^>]*\bid="reader"[^>]*>([\s\S]*?)<\/textarea>/);
  if (!labSource) throw new Error('could not find the reader source in web/lab.html');
  const starterLines = labSource[1].trimEnd().split('\n').length;
  if (starterLines > 15) {
    throw new Error(`lab starter no longer fits without scrolling: ${starterLines} lines`);
  }
  const read = await compileReaderSource(labSource[1], 'read', 'answer 42');
  if (Number(read.ran.value) !== 42 || !read.ast.startsWith('(program ') ||
      !read.formattedAst.startsWith('(program\n  (func ')) {
    throw new Error(`lab read pipeline mismatch: value=${read.ran.value} ast=${read.ast}`);
  }
  const readBad = await runReaderSource(labSource[1], 'read', 'answer nope');
  if (readBad.ast !== null ||
      !readBad.readerRun.stderr.includes('source.read:1:8: expected number, found nope')) {
    throw new Error(`lab reader failure mismatch: ${readBad.readerRun.stderr}`);
  }

  console.log(`PASS compiler_direct_wasm_e2e (${arithmetic.bytes}/${memory.bytes}/${imported.bytes}/${ast.bytes}/${addressed.bytes}; readers → tiny:${reader.ran.value}/calc:${calc.ran.value}/generated:${generated.ran.value}/forth:${forth.ran.value}/lisp:${lispValue}/C/Flow/Minipy/lab:${read.ran.value})`);
})().catch((error) => { console.error(error); process.exit(1); });
