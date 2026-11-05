#!/usr/bin/env python3
"""Inventory syntactic test forms in an R7RS suite, without evaluating Scheme."""
import argparse
from pathlib import Path


class Token(str):
    def __new__(cls, value, start):
        obj = super().__new__(cls, value)
        obj.start = start
        return obj


class Datum(list):
    def __init__(self, items=(), start=-1):
        super().__init__(items)
        self.start = start


def tokens(source):
    i, n = 0, len(source)
    while i < n:
        c = source[i]
        if c.isspace():
            i += 1
        elif c == ';':
            end = source.find('\n', i)
            i = n if end < 0 else end + 1
        elif source.startswith('#|', i):
            depth, i = 1, i + 2
            while depth:
                if i >= n:
                    raise ValueError('unterminated block comment')
                if source.startswith('#|', i):
                    depth, i = depth + 1, i + 2
                elif source.startswith('|#', i):
                    depth, i = depth - 1, i + 2
                else:
                    i += 1
        elif source.startswith('#;', i):
            yield Token('#;', i)
            i += 2
        elif source.startswith('#(', i) or source.startswith('#u8(', i):
            prefix = '#u8(' if source.startswith('#u8(', i) else '#('
            yield Token(prefix, i)
            i += len(prefix)
        elif c in ('"', '|'):
            delimiter = c
            start, i = i, i + 1
            while i < n and source[i] != delimiter:
                i += 2 if source[i] == '\\' else 1
            if i >= n:
                raise ValueError(f'unterminated string at {start}: {source[start:start+100]!r}')
            i += 1
            yield Token(source[start:i], start)
        elif source.startswith('#\\', i):
            start, i = i, i + 2
            if i >= n:
                raise ValueError('incomplete character')
            i += 1
            while i < n and not source[i].isspace() and source[i] not in '()':
                i += 1
            yield Token(source[start:i], start)
        elif c in '()\'`':
            yield Token(c, i)
            i += 1
        elif c == ',':
            yield Token(',@' if source.startswith(',@', i) else ',', i)
            i += 2 if source.startswith(',@', i) else 1
        else:
            start = i
            while i < n and not source[i].isspace() and source[i] not in '();\'`",':
                i += 1
            yield Token(source[start:i], start)


class Vector(Datum):
    def __init__(self, items, prefix="#", start=-1):
        super().__init__(items, start)
        self.prefix = prefix


def forms(source):
    stream = iter(tokens(source))
    def read(token):
        if token in ('(', '#(', '#u8('):
            result = Datum(start=token.start)
            for item in stream:
                if item == ')':
                    return result if token == '(' else Vector(result, token[:-1], token.start)
                if item == '#;':
                    read(next(stream))
                else:
                    result.append(read(item))
            raise ValueError('unterminated list')
        if token == '#;':
            read(next(stream))
            return read(next(stream))
        if token == ')':
            raise ValueError('unexpected close parenthesis')
        if token in ("'", '`', ',', ',@'):
            try:
                return Datum([token, read(next(stream))], token.start)
            except StopIteration as exc:
                raise ValueError('incomplete abbreviation') from exc
        return token
    for token in stream:
        if token == '#;':
            read(next(stream))
        else:
            yield read(token)


def tests(source):
    def walk(form):
        if isinstance(form, list) and not isinstance(form, Vector):
            if form and form[0] in ("'", '`'):
                return
            if len(form) in (3, 4) and form[0] == 'test':
                yield form
            for child in form:
                yield from walk(child)
    for form in forms(source):
        yield from walk(form)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('suite', type=Path)
    args = parser.parse_args()
    print('Syntactic test forms:', len(list(tests(args.suite.read_text()))))


if __name__ == '__main__':
    main()
