"""Fixture Lang client: derive lexical facts from let/in expression syntax."""
import re
from host_client import envelope, scope, binding, site, project_slice


def read(source, syntax):
    e = envelope(source, syntax, b'#lang{')
    body = source[e['start']:e['end']]
    tokens = list(re.finditer(rb'\w+|[^\s]', body))
    pos = 0

    def take(expected=None):
        nonlocal pos
        token = tokens[pos]
        pos += 1
        if expected is not None:
            assert token[0] == expected, token[0]
        return token

    def atom(parent, names):
        token = take()
        if token[0] == b'let':
            name = take()
            take(b'=')
            expression(parent, names)
            take(b'in')
            sid = scope(e, parent)
            bid = binding(e, sid, name[0])
            site(e, name.start(), name.end(), sid, bid, 1)
            expression(sid, dict(names, **{name[0].decode(): bid}))
        elif token[0] == b'(':
            expression(parent, names)
            take(b')')
        elif not token[0].isdigit():
            site(e, token.start(), token.end(), parent, names[token[0].decode()], 2)

    def expression(parent, names):
        atom(parent, names)
        while pos < len(tokens) and tokens[pos][0] == b'+':
            take(b'+')
            atom(parent, names)

    expression(3, {})
    assert pos == len(tokens)
    project_slice(e)
    return e
