#!/usr/bin/env python3
"""Build source → reader AST → LLVM panels and the reader-guide tutorial.

Only the functions emitted by the reader are displayed; the compiler links the
real target runtime before producing IR. No AST or IR is synthesized here.
"""
import argparse
import html
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TRACE_START = '  <!-- traces:start -->'
TRACE_END = '  <!-- traces:end -->'
TUTORIAL_START = '  <!-- tutorial:start -->'
TUTORIAL_END = '  <!-- tutorial:end -->'
TRACES = (
    ('lox', 'example/lox/lox.lang', 'example/lox/runtime.lang'),
    ('forth', 'example/forth/forth.lang', None),
    ('minilisp', 'example/minilisp/minilisp.lang', 'example/minilisp/lisp_runtime.lang'),
)


def tutorial_source():
    guide = (ROOT / 'docs/READERS.md').read_text()
    source = re.search(r'```lang\n(.*?)```', guide, re.S).group(1)
    if len(source.splitlines()) >= 100:
        raise ValueError('first reader tutorial must stay under 100 lines')
    return source


def run(compiler, *args):
    result = subprocess.run([compiler, *map(str, args)], cwd=ROOT,
                            env={**os.environ, 'LANGBE': 'llvm'},
                            text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout


def traces(compiler):
    panels = [TRACE_START, '  <section id="traces" aria-labelledby="traces-title">',
              '    <h2 id="traces-title">three syntaxes. one compiler.</h2>',
              '    <p>Follow each reader into the shared AST and native LLVM IR. Runtime calls stay explicit; runtime definitions are omitted here.</p>']
    with tempfile.TemporaryDirectory() as directory:
        scratch = Path(directory)
        for language, reader, runtime in TRACES:
            source = ROOT / f'web/trace_inputs/answer.{language}'
            ast, ir = scratch / 'answer.ast', scratch / 'answer.ll'
            run(compiler, 'read', reader, source.relative_to(ROOT), '-o', ast)
            args = ['--from-ast', ast, '--ast-source', source.relative_to(ROOT)]
            if runtime:
                args += ['--runtime', runtime]
            run(compiler, *args, '-o', ir)
            ast_text = ast.read_text()
            functions = re.findall(r'\(func\s+([^\s()]+)', ast_text)
            definitions = []
            for name in functions:
                match = re.search(r'^define [^\n]*@' + re.escape(name) + r'\([^\n]*\).*?^}', ir.read_text(), re.M | re.S)
                if not match:
                    raise ValueError(f'no LLVM definition for {language}/{name}')
                definitions.append(match.group())
            panels += [f'    <h3>{language}</h3>', '    <div class="trace-panes">']
            for label, text in [('Source', source.read_text()), ('Shared AST', ast_text), ('LLVM IR', '\n\n'.join(definitions))]:
                panels.append(f'      <div><h4>{label}</h4><pre><code>{html.escape(text.strip())}</code></pre></div>')
            panels += ['    </div>']
    return '\n'.join(panels + ['  </section>', TRACE_END])


def tutorial():
    source = tutorial_source()
    return '\n'.join([TUTORIAL_START, '  <pre><code>' + html.escape(source.rstrip()) + '</code></pre>', TUTORIAL_END])


def replace(path, start, end, generated, check):
    text = path.read_text()
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    updated = before + generated + after
    if check:
        if text != updated:
            raise SystemExit(f'{path.name} is stale; run python3 web/generate_language_maker.py')
    else:
        path.write_text(updated)


def generate(compiler, check=False):
    replace(ROOT / 'web/index.html', TRACE_START, TRACE_END, traces(compiler), check)
    replace(ROOT / 'web/readers.html', TUTORIAL_START, TUTORIAL_END, tutorial(), check)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--compiler', default=os.environ.get('COMPILER', './out/lang_next'))
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    generate(str(Path(args.compiler).resolve()), args.check)
