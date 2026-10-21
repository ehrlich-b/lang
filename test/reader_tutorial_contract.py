#!/usr/bin/env python3
"""Keep the copyable reader tutorial, shipped example and CLI starter in sync."""
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
COMPILER = Path(os.environ.get('COMPILER', ROOT / 'out/lang')).resolve()
EVIDENCE = Path(tempfile.mkdtemp(prefix='reader-tutorial-',
                               dir=os.environ.get('TUTORIAL_EVIDENCE_DIR')))
env = dict(os.environ, LANG_ROOT=str(ROOT), LANGBE='llvm',
           LANG_CACHE=str(EVIDENCE / 'cache'))


def run(args, label, cwd=ROOT):
    result = subprocess.run([str(COMPILER), *map(str, args)], cwd=cwd,
                            env=env, capture_output=True, timeout=60)
    (EVIDENCE / (label + '.stdout')).write_bytes(result.stdout)
    (EVIDENCE / (label + '.stderr')).write_bytes(result.stderr)
    (EVIDENCE / (label + '.exit')).write_text(str(result.returncode) + '\n')
    return result


def require(condition, message):
    if not condition:
        raise AssertionError(f'{message}; evidence: {EVIDENCE}')


# Extract what readers actually copy, rather than maintaining a third fixture.
guide = (ROOT / 'docs/READERS.md').read_text()
snippets = re.findall(r'```lang\n(.*?)\n```', guide, re.S)
snippet = next(source for source in snippets if 'reader tiny(' in source)
documented = EVIDENCE / 'documented.lang'
documented.write_text(snippet + '\n')
scaffold = EVIDENCE / 'scaffold'
scaffold.mkdir()
created = run(['new', 'reader', 'tiny'], 'scaffold-create', cwd=scaffold)
require(created.returncode == 0, 'CLI scaffold creation failed')
readers = {'shipped': ROOT / 'example/tiny/tiny.lang',
           'documented': documented, 'scaffold': scaffold / 'tiny.lang'}
cases = {
    'valid': ('answer 42', 42),
    'different-number': ('answer 17', 17),
    'whitespace': (' \t\n answer \t42\r\n ', 42),
    'comments': ('// before\nanswer /* between */ 42 /* after */ // end\n', 42),
    'trailing-identifier': ('answer 42 ignored tokens', None),
    'trailing-number': ('answer 42 7', None),
    'trailing-punctuation': ('answer 42 ;', None),
    'second-program': ('answer 42\nanswer 7', None),
    'empty': ('', None),
    'missing-number': ('answer', None),
    'comments-only': (' /* empty */ // still empty\n', None),
    'missing-number-comments': ('answer /* no number */', None),
}
for reader_name, reader in readers.items():
    for case_name, (source, expected) in cases.items():
        label = f'{reader_name}-{case_name}'
        source_file = EVIDENCE / (label + '.tiny')
        source_file.write_text(source)
        # Check both public AST destinations and the executable CLI path.
        output = EVIDENCE / (label + '.ast')
        for mode, args in [('stdout', ['read', reader, source_file]),
                           ('file', ['read', reader, source_file, '-o', output]),
                           ('run', ['run', reader, source_file])]:
            result = run(args, label + '-' + mode)
            if expected is None:
                require(result.returncode != 0, f'{label}/{mode} accepted invalid source')
                require(not result.stdout.strip(), f'{label}/{mode} emitted usable AST/output')
                require(not output.exists() or not output.read_bytes().strip(),
                        f'{label}/{mode} left a usable AST file')
            elif mode == 'run':
                require(result.returncode == expected,
                        f'{label}/run returned {result.returncode}, expected {expected}')
            else:
                require(result.returncode == 0, f'{label}/{mode} rejected valid source')
                ast = output.read_bytes() if mode == 'file' else result.stdout
                require(b'(program' in ast, f'{label}/{mode} omitted program AST')
        print(f'PASS {label}: ' + ('reject; no AST' if expected is None else f'return {expected}'))
print(f'PASS reader tutorial contract ({len(readers)} readers, {len(cases)} cases, 3 CLI paths); evidence: {EVIDENCE}')
