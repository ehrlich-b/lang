#!/usr/bin/env python3
"""Check Q0 contract examples, never claim production adapter conformance."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / 'test/lsp'


class Rejected(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise Rejected(code)


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate-key')
        result[key] = value
    return result


def load(path):
    return json.loads(path.read_text(), object_pairs_hook=unique)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fixture(name):
    path = (FIXTURES / name).resolve()
    require(FIXTURES in path.parents and path.is_file(), 'missing fixture: ' + name)
    return path


def integer(value):
    return type(value) is int and 0 <= value <= 0xffffffff


def span(data, start, end):
    require(integer(start) and integer(end) and start <= end <= len(data), 'invalid-span')
    try:
        data[:start].decode('utf-8')
        data[start:end].decode('utf-8')
    except UnicodeDecodeError:
        raise Rejected('invalid-span') from None


def index(rows, code):
    result = {}
    for row in rows:
        key = row['id']
        require(isinstance(key, str) and key and key not in result, code)
        result[key] = row
    return result


def ast_tree(data):
    # Fixtures intentionally contain no quoted atoms. This is a path checker,
    # not the production sexpr parser or a frontend semantic verifier.
    tokens = re.findall(r'\(|\)|[^\s()]+', data.decode())
    stack = []
    result = None
    for token in tokens:
        if token == '(':
            node = []
            if stack:
                stack[-1].append(node)
            else:
                require(result is None, 'invalid-mapping')
                result = node
            stack.append(node)
        elif token == ')':
            require(bool(stack), 'invalid-mapping')
            stack.pop()
        else:
            require(bool(stack), 'invalid-mapping')
            stack[-1].append(token)
    require(result is not None and not stack, 'invalid-mapping')
    return result


def decode(frame, limit=65536):
    require(len(frame) >= 8, 'wire-length')
    version, size = struct.unpack('<II', frame[:8])
    require(version == 1, 'wire-version')
    require(size <= limit, 'byte-limit')
    require(size == len(frame) - 8, 'wire-length')
    return json.loads(frame[8:].decode('utf-8'), object_pairs_hook=unique)


def validate(document, granted, ast, max_nodes=10000, max_depth=32):
    """Generic decoded-envelope model with out-of-band immutable host grants."""
    require(type(document['schema']) is int and document['schema'] == 1, 'wire-version')
    for key in ('session', 'request', 'revision'):
        require(document[key] == granted[key], 'stale-source')
    # Iterative budget walk before recursive consumers; values cannot buy fuel.
    todo = [(document, 0)]
    count = 0
    while todo:
        value, depth = todo.pop()
        count += 1
        require(count <= max_nodes and depth <= max_depth, 'metadata-limit')
        if isinstance(value, dict):
            todo.extend((v, depth + 1) for v in value.values())
        elif isinstance(value, list):
            todo.extend((v, depth + 1) for v in value)
    sources = index(document['sources'], 'unknown-source')
    require(document['source'] in sources, 'unknown-source')
    source_bytes = {}
    for sid, source in sources.items():
        require(sid in granted['sources'], 'unknown-source')
        data = granted['sources'][sid]
        require(integer(source['bytes']) and source['bytes'] == len(data), 'invalid-span')
        require(source['sha256'] == digest(data), 'stale-source')
        data.decode('utf-8')
        source_bytes[sid] = data
        parent = source['slice']
        if parent:
            require(parent['source'] in source_bytes, 'unknown-source')
            original = source_bytes[parent['source']]
            span(original, parent['start'], parent['end'])
            require(original[parent['start']:parent['end']] == data, 'invalid-span')
    origins = {}
    for origin in document['origins']:
        require(origin['id'] in granted['origins'], 'invalid-origin')
        require(origin == granted['origins'][origin['id']], 'invalid-origin')
        require(origin['id'] not in origins, 'invalid-origin')
        for key in ('include_parent', 'expansion_parent'):
            require(origin[key] is None or origin[key] in origins, 'invalid-origin')
        require(origin['source'] in sources, 'unknown-source')
        span(source_bytes[origin['source']], origin['start'], origin['end'])
        origins[origin['id']] = origin
    scopes = index(document['scopes'], 'conflicting-scope')
    seen = set()
    for scope in document['scopes']:
        parent = scope['parent']
        require(integer(scope['phase']) and scope['origin'] in origins, 'invalid-scope')
        require(parent is None or parent in seen and scopes[parent]['phase'] == scope['phase'], 'invalid-scope')
        seen.add(scope['id'])
    bindings = index(document['bindings'], 'dangling-binding')
    sites = index(document['sites'], 'invalid-mapping')
    core = index(document['core'], 'invalid-mapping')
    require(document['core_sha256'] == digest(ast), 'invalid-mapping')
    tree = ast_tree(ast)
    for node in core.values():
        require(node['binding'] in bindings, 'dangling-binding')
        require(node['origin'] in origins, 'invalid-origin')
        value = tree
        for part in node['path']:
            require(integer(part) and isinstance(value, list) and part < len(value), 'invalid-mapping')
            value = value[part]
        require(value == bindings[node['binding']]['name'], 'invalid-mapping')
        require(node['generated'] == bindings[node['binding']]['generated'], 'invalid-mapping')
    for site in sites.values():
        require(site['binding'] in bindings, 'dangling-binding')
    for binding in bindings.values():
        require(binding['scope'] in scopes and binding['phase'] == scopes[binding['scope']]['phase'], 'invalid-scope')
        require(bool(binding['name']) and bool(binding['namespace']), 'invalid-mapping')
        if binding['generated']:
            require(binding['declaration'] is None, 'invalid-mapping')
        else:
            declaration = sites.get(binding['declaration'])
            require(declaration is not None and declaration['role'] == 'declaration' and declaration['binding'] == binding['id'], 'invalid-mapping')
    for site in sites.values():
        require(site['source'] in sources, 'unknown-source')
        require(site['binding'] in bindings, 'dangling-binding')
        binding = bindings[site['binding']]
        require(site['scope'] in scopes and site['phase'] == scopes[site['scope']]['phase'] == binding['phase'], 'invalid-scope')
        require(site['origin'] in origins, 'invalid-origin')
        require(site['namespace'] == binding['namespace'], 'invalid-mapping')
        if site['role'] == 'generated':
            require(binding['generated'] and site['start'] is None and site['end'] is None and site['name'] is None, 'invalid-mapping')
        else:
            require(site['role'] in ('declaration', 'reference') and not binding['generated'], 'invalid-mapping')
            data = source_bytes[site['source']]
            span(data, site['start'], site['end'])
            require(site['start'] < site['end'] and data[site['start']:site['end']].decode() == site['name'] == binding['name'], 'invalid-mapping')
            if site['role'] == 'declaration':
                require(binding['declaration'] == site['id'] and binding['scope'] == site['scope'], 'invalid-mapping')
        require(bool(site['core']), 'invalid-mapping')
        for cid in site['core']:
            require(cid in core and core[cid]['binding'] == site['binding'], 'invalid-mapping')
    require(set(core) == {cid for site in sites.values() for cid in site['core']}, 'invalid-mapping')
    capabilities = document['capabilities']
    require(capabilities['rename'] is False and capabilities['reason'] == 'Q0-contract-only', 'invalid-mapping')


def grants(document):
    return dict(session=document['session'], request=document['request'], revision=document['revision'],
                sources={s['id']: fixture(s['path']).read_bytes() for s in document['sources']},
                origins={o['id']: copy.deepcopy(o) for o in document['origins']})


def examples():
    documents = {}
    for name in ('lang', 'minilisp'):
        document = load(fixture(name + '.golden.json'))
        ast = fixture(name + '.ast').read_bytes()
        validate(document, grants(document), ast)
        documents[name] = document
        # Check exact surface occurrences and explicit shadowing, independently
        # from the author's ID spelling. Equal names must not merge bindings.
        visible = [b for b in document['bindings'] if b['name'] == 'value']
        require(len(visible) == 2 and len({b['id'] for b in visible}) == 2, 'shadowing lost')
        for binding in visible:
            require(any(s['binding'] == binding['id'] and s['role'] == 'reference' for s in document['sites']), 'reference lost')
        print('PASS Q0 decoded golden:', name)
    require({s['phase'] for s in documents['lang']['sites']} == {0, 1}, 'phase lost')
    ml = documents['minilisp']
    require({b['name'] for b in ml['bindings'] if b['generated']} == {'__args', '__lt_fixture'}, 'closure names lost')
    # Demonstrate two-level local-to-root mapping using the actual source bytes.
    by_id = {s['id']: s for s in ml['sources']}
    for site in ml['sites']:
        if site['role'] == 'generated':
            continue
        sid, start, end, depth = site['source'], site['start'], site['end'], 0
        while by_id[sid]['slice']:
            parent = by_id[sid]['slice']
            start += parent['start']; end += parent['start']
            sid = parent['source']; depth += 1
        require(depth == 2 and fixture(by_id[sid]['path']).read_bytes()[start:end].decode() == site['name'], 'slice translation lost')
    print('PASS Q0 exact UTF-8 spans, distinct shadows, phases, generated closures and two slice offsets')
    return documents


def negatives(document):
    raw = json.dumps(document).encode()
    good = struct.pack('<II', 1, len(raw)) + raw
    require(decode(good) == document, 'wire roundtrip')
    for case in load(fixture('invalid.json')):
        example = load(fixture(case.get('golden', 'lang') + '.golden.json'))
        mutated = copy.deepcopy(example)
        case_grants = grants(example)
        case_ast = fixture(case.get('golden', 'lang') + '.ast').read_bytes()
        try:
            if 'path' in case:
                parts = case['path'].strip('/').split('/')
                target = mutated
                for part in parts[:-1]:
                    target = target[int(part)] if isinstance(target, list) else target[part]
                key = int(parts[-1]) if isinstance(target, list) else parts[-1]
                target[key] = case['value']
                validate(mutated, case_grants, case_ast)
            elif 'frame' in case:
                frames = dict(short=good[:7], mismatch=struct.pack('<II', 1, len(raw)+1)+raw,
                              trailing=good+b'x', oversized=struct.pack('<II', 1, 65537)+b'(program)',
                              version=struct.pack('<II', 2, len(raw))+raw)
                decode(frames[case['frame']])
            else:
                validate(mutated, case_grants, case_ast,
                         max_nodes=1 if case['budget'] == 'nodes' else 10000,
                         max_depth=1 if case['budget'] == 'depth' else 32)
        except Rejected as error:
            require(str(error) == case['code'], case['id'] + ': wrong error ' + str(error))
            print('PASS Q0 rejection model:', case['id'], case['code'])
        else:
            raise Rejected(case['id'] + ': accepted invalid example')
    try:
        decode(struct.pack('<II', 1, 13) + b'{"a":1,"a":2}')
    except Rejected as error:
        require(str(error) == 'duplicate-key', 'duplicate key diagnostic')
    else:
        raise Rejected('duplicate keys accepted')


def compatibility():
    matrix = load(fixture('compatibility.json'))
    require({row['kind'] for row in matrix} == {'legacy-unspanned', 'legacy-spanned', 'generated', 'unmapped', 'complete'}, 'incomplete feature matrix')
    for row in matrix:
        require(row['diagnostics'], 'missing fallback diagnostics')
        if row['kind'] != 'complete':
            require(row['rename'] is False and bool(row['reason']), 'unsafe limited rename')
        if row['kind'].startswith('legacy'):
            require(not row['navigation'] and not row['references'], 'legacy inferred binding')
    require(ast_tree(fixture('legacy.ast').read_bytes())[0] == 'program', 'invalid legacy AST')
    print('PASS Q0 legacy/limited feature matrix (actual compilation is a Q4 requirement)')


def dispatch_contract():
    # No fixture removal/mutation is needed to prove missing input fails.
    try:
        fixture('intentionally-absent.fixture')
    except Rejected as error:
        require('missing fixture:' in str(error), 'missing-fixture diagnostic')
    else:
        raise Rejected('missing fixture accepted')
    for phase in ('Q1', 'Q2', 'Q3', 'Q4', 'Q9'):
        result = subprocess.run([str(ROOT / 'test/run_lsp.sh'), phase], capture_output=True, text=True)
        require(result.returncode != 0 and phase in result.stderr, 'phase silently passed: ' + phase)
        require(('unimplemented' if phase != 'Q9' else 'unknown') in result.stderr, 'wrong phase refusal')
    result = subprocess.run([str(ROOT / 'test/run_lsp.sh'), 'Q0', 'extra'], capture_output=True, text=True)
    require(result.returncode != 0 and 'usage:' in result.stderr, 'extra argument accepted')
    print('PASS Q0 fail-fast dispatch Q1..Q4, unknown phase, extra arguments and missing fixture')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=['Q0', 'Q1', 'Q2', 'Q3', 'Q4'], default='Q0')
    parser.add_argument('--area', choices=['all', 'manifest', 'goldens', 'validation', 'compatibility'], default='all')
    args = parser.parse_args()
    manifest = load(fixture('phases.json'))
    require(manifest['version'] == 1 and set(manifest['phases']) == {'Q0', 'Q1', 'Q2', 'Q3', 'Q4'}, 'invalid phase manifest')
    for phase, row in manifest['phases'].items():
        require(bool(row['fixtures']), 'empty fixtures: ' + phase)
        for name in row['fixtures']:
            fixture(name)
    # Explicit dispatch cannot be made successful by toggling JSON metadata.
    if args.phase != 'Q0':
        raise Rejected('unimplemented LSP phase ' + args.phase + ': ' + manifest['phases'][args.phase]['requires'])
    documents = examples() if args.area in ('all', 'goldens', 'validation') else None
    if args.area in ('all', 'validation'):
        negatives(documents['lang'])
    if args.area in ('all', 'compatibility'):
        compatibility()
    if args.area in ('all', 'manifest'):
        dispatch_contract()
    print('PASS Q0 contract examples only; Q1..Q4 remain unimplemented')


if __name__ == '__main__':
    try:
        main()
    except (Rejected, OSError, KeyError, TypeError, UnicodeError, json.JSONDecodeError) as error:
        print('FAIL LSP contract: ' + str(error), file=sys.stderr)
        sys.exit(1)
