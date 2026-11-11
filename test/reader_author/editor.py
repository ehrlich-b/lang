#!/usr/bin/env python3
"""Small, tool-free project editor contract checks against a built compiler."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[2]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', type=Path, default=ROOT / 'out/lang_next')
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    compiler = args.compiler.resolve()
    evidence = (args.evidence or ROOT.parent / 'evidence' / ('editor-' + uuid.uuid4().hex)).resolve()
    require(evidence != ROOT and ROOT not in evidence.parents, 'evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, LANG_CACHE=str(evidence / 'cache'))
    calls = []

    def run(manifest, target=None, expected=0):
        command = [str(compiler), 'project', 'editor', str(manifest)]
        if target is not None:
            command += ['-o', str(target)]
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=20)
        calls.append({'command': command, 'exit': result.returncode,
                      'stdout': result.stdout.decode(), 'stderr': result.stderr.decode()})
        (evidence / 'commands.json').write_text(json.dumps(calls, indent=2) + '\n')
        require(result.returncode == expected, calls[-1])

    manifest = ROOT / 'example/shipping/project.lang-project'
    first, second = evidence / 'first', evidence / 'second'
    run(manifest, first)
    run(manifest, second)
    files = {p.name: p.read_bytes() for p in first.iterdir()}
    require(set(files) == {'package.json', 'language-configuration.json', 'shipping.tmLanguage.json'},
            'expected exactly the three extension files')
    require(files == {p.name: p.read_bytes() for p in second.iterdir()}, 'output must be byte-identical')
    package, config, grammar = [json.loads(files[name]) for name in
                              ['package.json', 'language-configuration.json', 'shipping.tmLanguage.json']]
    language, = package['contributes']['languages']
    registration, = package['contributes']['grammars']
    require(language['extensions'] == ['.shipping'], 'extension must come from the manifest')
    require(language['id'] == registration['language'] == 'shipping', 'language registration')
    require(registration['scopeName'] == grammar['scopeName'] == 'source.shipping', 'grammar scope')
    require(registration['path'] == './shipping.tmLanguage.json', 'grammar path')
    require(language['configuration'] == './language-configuration.json', 'configuration path')
    require(config['comments']['lineComment'] == '//', 'line comments')
    patterns = {p['name'].split('.')[0] + '.' + p['name'].split('.')[1]: p for p in grammar['patterns']}
    keyword = next(p['match'] for p in grammar['patterns'] if p['name'].startswith('keyword.control.'))
    operator = next(p['match'] for p in grammar['patterns'] if p['name'].startswith('keyword.operator.'))
    source = (ROOT / 'example/shipping/shipping.lang').read_text()
    words = re.findall(r"'([A-Za-z]+)'", source.split('#parser{', 1)[1].split('\n}', 1)[0])
    require(words, 'shipping oracle must contain keywords')
    for word in words:
        require(word in keyword and re.fullmatch(keyword, word), 'missing keyword: ' + word)
        require(not re.search(keyword, word + 'suffix'), 'keyword boundary')
    for literal in ['{', '}', ';', '-']:
        require(re.fullmatch(operator, literal), 'missing literal: ' + literal)
    require(re.fullmatch(patterns['constant.numeric']['match'], '12.5e-2'), 'number pattern')
    require(re.fullmatch(patterns['comment.line']['match'], '// a comment'), 'comment pattern')
    string = patterns['string.quoted']
    require(string['begin'] == string['end'] == '"', 'string delimiters')
    require(re.fullmatch(string['patterns'][0]['match'], r'\"'), 'escaped quote pattern')

    # Both empty and populated destinations must fail without changing a byte.
    empty = evidence / 'empty'
    empty.mkdir()
    run(manifest, empty, expected=1)
    require(list(empty.iterdir()) == [], 'existing empty directory was written')
    (first / 'sentinel').write_bytes(b'keep\x00exactly\n')
    before = {p.name: p.read_bytes() for p in first.iterdir()}
    run(manifest, first, expected=1)
    require(before == {p.name: p.read_bytes() for p in first.iterdir()}, 'existing directory changed')
    occupied = evidence / 'occupied'
    occupied.write_bytes(b'keep')
    run(manifest, occupied, expected=1)
    require(occupied.read_bytes() == b'keep', 'existing file changed')
    link = evidence / 'link'
    link.symlink_to(first, target_is_directory=True)
    run(manifest, link, expected=1)
    require(before == {p.name: p.read_bytes() for p in first.iterdir()}, 'symlink target changed')
    run(manifest, expected=1)

    # Multiple blocks, both quote forms, duplicates, regex metacharacters,
    # overlapping operators and decoys outside parser blocks.
    fixture = evidence / 'fixture'
    fixture.mkdir()
    (fixture / 'reader.lang').write_text(r'''// #parser{ fake = 'commentdecoy' }
var decoy *u8 = "#parser{ fake = 'stringdecoy' }";
#parser{ one = 'if' 'if' "else" '+' '++' '.' '[' '\\' }
#parser{ two = 'while' 'under_score' 'a|b' }
reader shipping(text *u8) *u8 { return nil; }
''')
    (fixture / 'policy.shipping').write_text('')
    (fixture / 'project.lang-project').write_text(manifest.read_text().replace('"shipping.lang"', '"reader.lang"')
                                                 .replace('["runtime.lang"]', '[]'))
    run(fixture / 'project.lang-project', evidence / 'custom')
    custom = json.loads((evidence / 'custom/shipping.tmLanguage.json').read_text())
    kw = next(p['match'] for p in custom['patterns'] if p['name'].startswith('keyword.control.'))
    op = next(p['match'] for p in custom['patterns'] if p['name'].startswith('keyword.operator.'))
    for word in ['if', 'else', 'while', 'under_score']:
        require(re.fullmatch(kw, word), 'multiple blocks / quote forms: ' + word)
    require(kw.count('if') == 1 and 'decoy' not in kw, 'deduplication and lexical isolation')
    for literal in ['+', '++', '.', '[', '\\\\', 'a|b']:
        require(re.fullmatch(op, literal), 'escaped literal: ' + literal)
    require(re.match(op, '++').group() == '++', 'longest operator first')
    print('PASS editor: three JSON files, shipping keywords, patterns, refusal without writes, byte determinism, lexical isolation')
    print('evidence:', evidence)


if __name__ == '__main__':
    main()
