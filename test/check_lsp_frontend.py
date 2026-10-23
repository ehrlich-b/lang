#!/usr/bin/env python3
"""Verify Q0 core fixtures against today's frontend, without claiming Q2/Q3."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
import check_lsp_contract as contract


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', required=True)
    args = parser.parse_args()
    compiler = str(Path(args.compiler).resolve())
    with tempfile.TemporaryDirectory(prefix='lsp-core-') as directory:
        temporary = Path(directory)

        def emit(source, name):
            output = temporary / (name + '.ast')
            subprocess.run([compiler, '--emit-expanded-ast', str(source), '-o', str(output)],
                           cwd=contract.ROOT, check=True)
            return output.read_bytes()

        # Keep the modules header: every top-level core path includes it.
        actual = emit(Path('test/lsp/lang.lang'), 'lang').rstrip() + b'\n'
        contract.require(actual == contract.fixture('lang.ast').read_bytes(), 'Lang core fixture differs from frontend')
        document = contract.load(contract.fixture('lang.golden.json'))
        contract.validate(document, contract.grants(document), actual)
        print('PASS real Lang AST, modules indices and phase-1 reader mappings')

        includes = ('include "std/core.lang"\n'
                    'include "example/minilisp/lisp_runtime.lang"\n'
                    'include "example/minilisp/minilisp.lang"\n')
        for name in ('minilisp', 'minilisp-lisp2'):
            source = temporary / (name + '.lang')
            surface = contract.fixture(name + '.minilisp').read_text()
            # Expanded AST emission retains reader_expr nodes. Execute the
            # existing reader's own parse/lower functions to obtain its result.
            source.write_text(includes + 'func main() i64 {\n'
                              'ml_src = ' + json.dumps(surface, ensure_ascii=False) + ';\n'
                              'var t *Tokenizer = tok_new_comments(ml_src, ";", nil, nil);\n'
                              'println(lisp_expr(parse_sexp(t))); return 0; }\n')
            llvm = temporary / (name + '.ll')
            executable = temporary / name
            subprocess.run([compiler, str(source), '-o', str(llvm)], cwd=contract.ROOT,
                           env=dict(os.environ, LANGBE='llvm'), check=True)
            subprocess.run(['clang', '-O0', str(llvm), '-o', str(executable)], check=True)
            actual = subprocess.check_output([str(executable)], text=True)
            # Only the address-derived closure temporary is unstable.
            actual = re.sub(r'__lt[0-9]+\b', '__lt_fixture', actual)
            actual_tree = contract.ast_tree(actual.encode())
            expected = contract.ast_tree(contract.fixture(name + '.ast').read_bytes())
            contract.require(actual_tree == expected, name + ' core fixture differs from frontend')
            print('PASS real', name, 'lowering (only address temporary alpha-normalized)')


if __name__ == '__main__':
    main()
