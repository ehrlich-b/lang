"""Independent W/Q0 client encoder, with byte locations for mutation controls."""
import hashlib
import re
import struct


def envelope(source, syntax, marker, body):
    start = source.index(marker) + len(marker)
    end = start + len(body)
    assert source[start:end] == body
    scopes = [[1, 0, 0], [2, 1, 1], [3, 1, 0], [4, 3, 0], [5, 4, 0]]
    bindings = [[1, 2, 1, 'text'], [2, 1, 1, 'seed'], [3, 1, 1, 'f'],
                [4, 4, 2, 'x'], [5, 5, 2, 'x']]
    sites = []
    for name, scope, binding in [(b'text', 2, 1), (b'seed', 1, 2), (b'f', 1, 3)]:
        hits = list(re.finditer(rb'\b' + name + rb'\b', source))
        assert len(hits) == 2
        for i, hit in enumerate(hits):
            use_scope = scope if i == 0 or name == b'text' else 3 if name == b'seed' else 1
            sites.append([1, hit.start(), hit.end(), use_scope, binding, 1, 1 if i == 0 else 2])
    hits = list(re.finditer(rb'\bx\b', body))
    assert len(hits) == 4
    for i, hit in enumerate(hits):
        scope = [4, 5, 5, 4][i]
        binding = [4, 5, 5, 4][i]
        sites.append([1, start + hit.start(), start + hit.end(), scope, binding, 2, 1 if i < 2 else 2])
    return dict(version=1, mapped=1, origin=1, syntax=syntax, start=start, end=end,
                sources=[[1, hashlib.sha256(source).hexdigest()], [2, hashlib.sha256(body).hexdigest()]],
                scopes=scopes, bindings=bindings, sites=sites)


def encode(e):
    out = bytearray(16)
    offsets = {}

    def word(key, value):
        offsets[key] = len(out)
        out.extend(struct.pack('<I', value))

    def string(key, value):
        raw = value.encode() if isinstance(value, str) else value
        word(key + '.length', len(raw))
        offsets[key] = len(out)
        out.extend(raw)

    word('version', e['version'])
    word('mapped', e['mapped'])
    string('syntax', e['syntax'])
    word('sources.count', len(e['sources']))
    for i, (sid, digest) in enumerate(e['sources']):
        word(f'sources.{i}.id', sid)
        offsets[f'sources.{i}.digest'] = len(out)
        out.extend(digest.encode())
    for kind, fields in [('scopes', ['id', 'parent', 'phase']),
                         ('bindings', ['id', 'scope', 'origin', 'name']),
                         ('sites', ['source', 'start', 'end', 'scope', 'binding', 'origin', 'role'])]:
        word(kind + '.count', len(e[kind]))
        for i, row in enumerate(e[kind]):
            for field, value in zip(fields, row):
                key = f'{kind}.{i}.{field}'
                (string if field == 'name' else word)(key, value)
    out[:16] = struct.pack('<IIII', 1, len(out) - 16, e['origin'], 1)
    return bytes(out), offsets
