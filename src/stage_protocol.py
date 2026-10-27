"""STG1 copied-value transport shared by compile and call engines.

Frame: <magic:4, payload:u32, kind:u32, reserved:u32> LE, then one tagged
value. No addresses, object IDs, native layouts or executable descriptors.
"""
from dataclasses import dataclass
import struct

MAX_BYTES = 8 * 1024 * 1024
MAX_DEPTH = 64
MAX_ITEMS = 100000
HEADER = struct.Struct('<4sIII')
TAGS = {'null': 0, 'bool': 1, 'i8': 2, 'i16': 3, 'i32': 4, 'i64': 5,
        'bytes': 6, 'text': 7, 'list': 8, 'record': 9, 'syntax': 10, 'descriptor': 11}
NAMES = {v: k for k, v in TAGS.items()}

class WireError(ValueError):
    pass

@dataclass(frozen=True)
class Value:
    kind: str
    data: object = None


def encode(value):
    active = set()
    count = 0
    def visit(v, depth):
        nonlocal count
        count += 1
        if depth > MAX_DEPTH or count > MAX_ITEMS:
            raise WireError('wire-budget')
        if type(v) is not Value or type(v.kind) is not str or v.kind not in TAGS:
            raise WireError('non-wire-value')
        ident = id(v)
        if ident in active: raise WireError('cyclic-wire-object')
        active.add(ident)
        tag, data = TAGS[v.kind], v.data
        if v.kind == 'null':
            if data is not None: raise WireError('null-value')
            payload = b''
        elif v.kind == 'bool':
            if type(data) is not bool: raise WireError('bool-value')
            payload = bytes([data])
        elif v.kind.startswith('i') and v.kind[1:].isdigit():
            bits = int(v.kind[1:])
            if type(data) is not int or not -(1 << (bits-1)) <= data < (1 << (bits-1)):
                raise WireError('integer-range')
            payload = data.to_bytes(bits//8, 'little', signed=True)
        elif v.kind == 'bytes':
            if type(data) is not bytes: raise WireError('bytes-value')
            payload = data
        elif v.kind in ('text', 'syntax'):
            if type(data) is not str: raise WireError('text-value')
            try: payload = data.encode('utf-8', errors='strict')
            except UnicodeError as e: raise WireError('invalid-utf8') from e
            if v.kind == 'syntax' and ('\0' in data or not data.startswith('(program')):
                raise WireError('syntax-value')
        elif v.kind in ('record', 'descriptor'):
            if type(data) is not dict or any(type(k) is not str for k in data):
                raise WireError('record-value')
            if len(data) > MAX_ITEMS: raise WireError('wire-budget')
            payload = bytearray(struct.pack('<I', len(data)))
            for key in sorted(data):
                for child in (Value('text', key), data[key]):
                    encoded = visit(child, depth+1)
                    if len(payload) + len(encoded) + 5 > MAX_BYTES:
                        raise WireError('wire-length')
                    payload.extend(encoded)
        else:
            if type(data) is not list: raise WireError('list-value')
            if len(data) > MAX_ITEMS: raise WireError('wire-budget')
            payload = bytearray(struct.pack('<I', len(data)))
            for child in data:
                encoded = visit(child, depth+1)
                if len(payload) + len(encoded) + 5 > MAX_BYTES:
                    raise WireError('wire-length')
                payload.extend(encoded)
        active.remove(ident)
        if len(payload) + 5 > MAX_BYTES: raise WireError('wire-length')
        return bytes([tag]) + struct.pack('<I', len(payload)) + bytes(payload)
    return visit(value, 0)


def decode(data):
    if type(data) not in (bytes, bytearray): raise WireError('wire-type')
    if len(data) > MAX_BYTES: raise WireError('wire-length')
    count = 0
    def visit(pos, end, depth):
        nonlocal count
        count += 1
        if depth > MAX_DEPTH or count > MAX_ITEMS: raise WireError('wire-budget')
        if end-pos < 5: raise WireError('value-header')
        tag, size = data[pos], struct.unpack_from('<I', data, pos+1)[0]
        pos += 5
        stop = pos + size
        if stop > end or tag not in NAMES: raise WireError('value-length-or-tag')
        kind = NAMES[tag]
        if kind == 'null':
            if size: raise WireError('null-length')
            result = None
        elif kind == 'bool':
            if size != 1 or data[pos] > 1: raise WireError('bool-value')
            result = bool(data[pos])
        elif kind.startswith('i') and kind[1:].isdigit():
            if size != int(kind[1:])//8: raise WireError('integer-length')
            result = int.from_bytes(data[pos:stop], 'little', signed=True)
        elif kind == 'bytes': result = bytes(data[pos:stop])
        elif kind in ('text', 'syntax'):
            try: result = data[pos:stop].decode('utf-8', errors='strict')
            except UnicodeError as e: raise WireError('invalid-utf8') from e
            if kind == 'syntax' and ('\0' in result or not result.startswith('(program')):
                raise WireError('syntax-value')
        else:
            if size < 4: raise WireError('container-length')
            n = struct.unpack_from('<I', data, pos)[0]
            pos += 4
            if n > MAX_ITEMS or n > (stop-pos)//(10 if kind != 'list' else 5):
                raise WireError('container-length')
            result = [] if kind == 'list' else {}
            previous = None
            for _ in range(n):
                item, pos = visit(pos, stop, depth+1)
                if kind == 'list': result.append(item)
                else:
                    if item.kind != 'text' or (previous is not None and item.data <= previous):
                        raise WireError('record-key')
                    previous = item.data
                    val, pos = visit(pos, stop, depth+1)
                    result[item.data] = val
            if pos != stop: raise WireError('container-trailing')
        return Value(kind, result), stop
    value, end = visit(0, len(data), 0)
    if end != len(data): raise WireError('value-trailing')
    return value


def frame(value, kind=1):
    if type(kind) is not int or kind not in (1, 2, 3): raise WireError('frame-kind')
    payload = encode(value)
    if len(payload) > MAX_BYTES: raise WireError('wire-length')
    return HEADER.pack(b'STG1', len(payload), kind, 0) + payload


def unframe(data, kind=None):
    if kind is not None and (type(kind) is not int or kind not in (1, 2, 3)):
        raise WireError('frame-kind')
    if type(data) not in (bytes, bytearray): raise WireError('wire-type')
    if len(data) < HEADER.size: raise WireError('frame-header')
    magic, size, actual, reserved = HEADER.unpack_from(data)
    if magic != b'STG1' or reserved or actual not in (1, 2, 3): raise WireError('frame-version')
    if kind is not None and actual != kind: raise WireError('frame-kind')
    if size > MAX_BYTES or size != len(data)-HEADER.size: raise WireError('frame-length')
    return decode(data[HEADER.size:])


def read_frame(stream):
    def exact(n):
        chunks = bytearray()
        while len(chunks) < n:
            remaining = n-len(chunks)
            part = stream.read(remaining)
            if not isinstance(part, (bytes, bytearray)) or len(part) > remaining:
                raise WireError('invalid-stream-read')
            if not part: raise WireError('truncated-frame')
            chunks.extend(part)
        return bytes(chunks)
    header = exact(HEADER.size)
    magic, size, kind, reserved = HEADER.unpack(header)
    if magic != b'STG1' or size > MAX_BYTES or reserved or kind not in (1, 2, 3):
        raise WireError('frame-header')
    return header + exact(size)
