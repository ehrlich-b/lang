"""Independent W/Q0 client encoder, with byte locations for mutation controls."""
import struct


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
