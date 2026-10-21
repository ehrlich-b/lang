"""Facts for the common Lang wrapper around the two guest reader fixtures."""
import hashlib
import re


def envelope(source, syntax, marker):
    start = source.index(marker) + len(marker)
    end = source.index(b'}', start)
    body = source[start:end]
    scopes = [[1, 0, 0], [2, 1, 1], [3, 1, 0]]
    bindings, sites = [], []
    # Discover the phase parameter and the two host declarations from syntax.
    parameter = re.search(rb'reader \w+\((\w+) \*u8\)', source)[1]
    declarations = re.findall(rb'var (\w+) (?:i64|closure\(\) i64) =', source)
    assert len(declarations) == 2
    for name, scope in [(parameter, 2), *((name, 1) for name in declarations)]:
        bid = len(bindings) + 1
        bindings.append([bid, scope, 1, name.decode()])
        hits = list(re.finditer(rb'\b' + re.escape(name) + rb'\b', source))
        assert len(hits) == 2
        for i, hit in enumerate(hits):
            use_scope = 3 if i == 1 and name == declarations[0] else scope
            sites.append([1, hit.start(), hit.end(), use_scope, bid, 1, i + 1])
    return dict(version=1, mapped=1, origin=1, syntax=syntax, start=start, end=end,
                sources=[[1, hashlib.sha256(source).hexdigest()],
                         [2, hashlib.sha256(body).hexdigest()]],
                scopes=scopes, bindings=bindings, sites=sites)


def scope(e, parent):
    sid = len(e['scopes']) + 1
    e['scopes'].append([sid, parent, 0])
    return sid


def binding(e, sid, name):
    bid = len(e['bindings']) + 1
    e['bindings'].append([bid, sid, 2, name.decode()])
    return bid


def site(e, start, end, sid, bid, role):
    e['sites'].append([1, e['start'] + start, e['start'] + end, sid, bid, 2, role])


def project_slice(e):
    # The same guest facts also address the H slice minted by the compiler.
    e['sites'].extend([[2, a - e['start'], b - e['start'], sid, bid, 3, role]
                       for source, a, b, sid, bid, origin, role in list(e['sites'])
                       if origin == 2])
