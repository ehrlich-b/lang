"""Fixture minilisp client: derive lexical facts by walking Lisp forms."""
import re
from host_client import envelope, scope, binding, site, project_slice


def read(source, syntax):
    e = envelope(source, syntax, b'#minilisp{')
    body = source[e['start']:e['end']]
    tokens = iter(re.finditer(rb'[^\s()]+|[()]', body))

    def form(token):
        if token[0] != b'(':
            return token
        children = []
        for child in tokens:
            if child[0] == b')':
                return children
            children.append(form(child))
        raise AssertionError('unclosed Lisp form')

    tree = form(next(tokens))
    assert next(tokens, None) is None

    def walk(node, parent, names):
        if isinstance(node, list):
            if node[0][0] == b'let':
                sid = scope(e, parent)
                local = dict(names)
                for name, value in node[1]:
                    walk(value, parent, names)
                    bid = binding(e, sid, name[0])
                    site(e, name.start(), name.end(), sid, bid, 1)
                    local[name[0]] = bid
                for child in node[2:]:
                    walk(child, sid, local)
            else:
                assert node[0][0] == b'+'
                for child in node[1:]:
                    walk(child, parent, names)
        elif not node[0].isdigit():
            site(e, node.start(), node.end(), parent, names[node[0]], 2)

    # The enclosing Lang reader is an additional invocation scope.
    walk(tree, scope(e, 3), {})
    project_slice(e)
    return e
