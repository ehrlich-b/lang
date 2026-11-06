#!/usr/bin/env python3
"""Export an explicit Lang source closure as Rill, without parsing to an AST."""
import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sys

WORDS = {b'func': b'fun', b'var': b'local', b'struct': b'record',
         b'include': b'use', b'reader': b'syntax', b'require': b'needs'}
RESERVED = set(WORDS.values())
BLOCKED = {b'macro', b'import', b'enum', b'match', b'effect', b'perform',
           b'handle', b'with', b'resume', b'closure', b'let', b'in'}
PREFIX = b'rill__'
OPERATORS = set(b'+ - * / % & ! = == != < > <= >= && || ( ) { } [ ] , ; . : | ^ << >> += -= *= /= %='.split())
WORD = re.compile(rb'[A-Za-z_][A-Za-z_0-9]*')
NUMBER = re.compile(rb'[0-9]+(?:\.[0-9]+)?')
PATH = re.compile(rb'"[A-Za-z_0-9/.-]+"')


class Unsupported(ValueError):
    pass


@dataclass(frozen=True)
class Token:
    kind: str
    start: int
    end: int
    value: bytes


def digest(data):
    return hashlib.sha256(data).hexdigest()


def scan(source, name):
    """Byte scanner: every input byte belongs to exactly one token or trivia."""
    source.decode('utf-8')
    i = 0
    while i < len(source):
        start = i
        c = source[i:i + 1]
        if c in b' \t\r\n':
            i += 1
            while i < len(source) and source[i:i + 1] in b' \t\r\n':
                i += 1
            kind = 'trivia'
        elif source.startswith(b'//', i):
            end = source.find(b'\n', i)
            i = len(source) if end < 0 else end
            kind = 'comment'
        elif source.startswith(b'/*', i):
            end = source.find(b'*/', i + 2)
            if end < 0:
                raise Unsupported(f'{name}:{i}: unterminated comment')
            i = end + 2
            kind = 'comment'
        elif c in (b'"', b"'"):
            quote = c
            i += 1
            units = 0
            while i < len(source) and source[i:i + 1] != quote:
                if source[i:i + 1] == b'\\':
                    if i + 1 >= len(source):
                        break
                    if quote == b"'" and source[i + 1:i + 2] not in b'ntr0\\\'"':
                        raise Unsupported(f'{name}:{i}: unsupported character escape')
                    i += 2
                else:
                    i += 1
                units += 1
            if i >= len(source) or source[i:i + 1] != quote:
                raise Unsupported(f'{name}:{start}: unterminated literal')
            if quote == b"'" and units != 1:
                raise Unsupported(f'{name}:{start}: unsupported character literal')
            i += 1
            kind = 'literal'
        elif WORD.match(source, i):
            i = WORD.match(source, i).end()
            kind = 'word'
            if source[start:i] in BLOCKED:
                raise Unsupported(f'{name}:{start}: unsupported source construct {source[start:i]!r}')
        elif NUMBER.match(source, i):
            i = NUMBER.match(source, i).end()
            if i < len(source) and (source[i:i + 1].isalnum() or source[i:i + 1] == b'_'):
                raise Unsupported(f'{name}:{start}: unsupported numeric spelling')
            kind = 'number'
        else:
            op = source[i:i + 2]
            if op in (b':=', b'=>'):
                raise Unsupported(f'{name}:{i}: unsupported source operator {op!r}')
            if op not in OPERATORS:
                op = c
            if op not in OPERATORS:
                raise Unsupported(f'{name}:{i}: unsupported source byte {c!r}')
            i += len(op)
            kind = 'operator'
        yield Token(kind, start, i, source[start:i])


def relative(path):
    p = Path(path)
    if p.is_absolute() or '..' in p.parts or not p.parts:
        raise Unsupported(f'non-local source path: {path}')
    return p.as_posix()


class Exporter:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.modules = {}

    def load(self, name):
        name = relative(name)
        if name in self.modules:
            return
        path = (self.root / name).resolve()
        if self.root not in path.parents or path.suffix != '.lang':
            raise Unsupported(f'unsupported source path: {name}')
        source = path.read_bytes()
        tokens = list(scan(source, name))
        deps = []
        meaningful = [t for t in tokens if t.kind not in ('trivia', 'comment')]
        stack = []
        for index, token in enumerate(meaningful):
            if token.value in (b'include', b'require') and token.kind == 'word':
                if stack or index + 1 >= len(meaningful):
                    raise Unsupported(f'{name}:{token.start}: unsupported dependency declaration')
                target = meaningful[index + 1]
                if not PATH.fullmatch(target.value):
                    raise Unsupported(f'{name}:{target.start}: unsupported dependency path')
                dep = target.value[1:-1].decode('ascii')
                if token.value == b'require':
                    dep += '.lang'
                dep = relative(dep)
                deps.append({'kind': token.value.decode(), 'source': dep,
                             'tokens': [token.start, target.start]})
            if token.kind == 'operator':
                if token.value in (b'{', b'(', b'['):
                    stack.append(token.value)
                if token.value in (b'}', b')', b']'):
                    opening = {b'}': b'{', b')': b'(', b']': b'['}[token.value]
                    if not stack or stack.pop() != opening:
                        raise Unsupported(f'{name}:{token.start}: unbalanced delimiter')
        if stack:
            raise Unsupported(f'{name}: unclosed delimiter')
        self.modules[name] = {'source': source, 'tokens': tokens, 'dependencies': deps}
        for dep in deps:
            self.load(dep['source'])

    def order(self, roots):
        seen, ordered = set(), []

        def visit(name):
            if name in seen:
                return
            seen.add(name)  # Include/require deduplicate, including dependency cycles.
            for dep in self.modules[name]['dependencies']:
                visit(dep['source'])
            ordered.append(name)

        for name in roots:
            visit(name)
        return ordered

    def render(self, name, flatten=False):
        module = self.modules[name]
        omitted = {start for dep in module['dependencies'] for start in dep['tokens']} if flatten else set()
        chunks, spans, end = [], [], 0
        for token in module['tokens']:
            value, kind = token.value, 'copy'
            if token.start in omitted:
                value, kind = b'', 'dependency'
            elif token.kind == 'word':
                if value in WORDS:
                    value, kind = WORDS[value], 'keyword'
                elif value in RESERVED or value.startswith(PREFIX):
                    value, kind = PREFIX + value, 'identifier'
            next_end = end + len(value)
            row = [token.start, token.end, end, next_end, kind]
            if kind == 'copy' and spans and spans[-1][4] == 'copy':
                spans[-1][1], spans[-1][3] = token.end, next_end
            else:
                spans.append(row)
            chunks.append(value)
            end = next_end
        return b''.join(chunks), spans

    def export(self, closures, output):
        closures = {label: [relative(name) for name in roots] for label, roots in closures.items()}
        for label in closures:
            if not re.fullmatch(r'[A-Za-z0-9_-]+', label):
                raise Unsupported(f'invalid closure name: {label}')
        for roots in closures.values():
            for name in roots:
                self.load(name)
        # Validate the entire closure before creating any output files.
        output = Path(output)
        output.mkdir(parents=True, exist_ok=False)
        manifest = {'version': 1, 'dialect': 'rill-v2',
                    'span_columns': ['source_start', 'source_end', 'export_start', 'export_end', 'kind'],
                    'span_unit': 'half-open UTF-8 bytes', 'modules': [], 'closures': {}}
        for name, module in sorted(self.modules.items()):
            data, spans = self.render(name)
            target = 'modules/' + str(Path(name).with_suffix('.rill'))
            path = output / target
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            manifest['modules'].append({'source': name, 'export': target,
                'source_sha256': digest(module['source']), 'export_sha256': digest(data),
                'source_bytes': len(module['source']), 'export_bytes': len(data),
                'dependencies': module['dependencies'], 'spans': spans})
        for label, roots in sorted(closures.items()):
            order = self.order(roots)
            chunks, mapping, offset = [], [], 0
            for name in order:
                data, spans = self.render(name, flatten=True)
                chunks.append(data + b'\n')
                mapping.append({'source': name, 'export_start': offset,
                                'export_end': offset + len(data), 'spans': spans})
                offset += len(data) + 1
            data = b''.join(chunks)
            target = label + '.rill'
            (output / target).write_bytes(data)
            manifest['closures'][label] = {'roots': roots, 'order': order, 'export': target,
                'export_sha256': digest(data), 'export_bytes': len(data), 'modules': mapping,
                'separator': 'one generated newline after each module'}
        (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--entry', action='append', help='custom program roots instead of the compiler specification')
    args = parser.parse_args()
    try:
        root = args.root.resolve()
        spec = json.loads((root / 'example/rill/compiler-closure.json').read_text())
        closures = {'program': args.entry} if args.entry else spec['closures']
        manifest = Exporter(root).export(closures, args.output)
        print(f'Exported {len(manifest["modules"])} modules in {len(closures)} closures')
        return 0
    except (OSError, ValueError) as error:
        print(f'rill export: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
