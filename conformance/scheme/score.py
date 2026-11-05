#!/usr/bin/env python3
"""Run contextual R7RS test forms through the lang-built native compiler.

The pinned file has 989 textual test sites, of which 980 are executable forms.
Commented sites remain in the denominator and can never earn a pass.
"""
import argparse
import json
import re
from pathlib import Path
import subprocess
from inventory import Datum, Vector, forms
from runner import ROOT, compiler, compile_program


def render(x):
    if isinstance(x, Vector):
        return x.prefix + '(' + ' '.join(map(render, x)) + ')'
    if isinstance(x, list):
        if len(x) == 2 and x[0] in ("'", '`', ',', ',@'):
            return str(x[0]) + render(x[1])
        return '(' + ' '.join(map(render, x)) + ')'
    return str(x)


def is_test(x):
    return isinstance(x, list) and not isinstance(x, Vector) and len(x) == 3 and x[0] == 'test'


def walk(x):
    if not isinstance(x, list) or isinstance(x, Vector) or (x and x[0] in ("'", '`', 'quote')):
        return
    yield x
    for item in x:
        yield from walk(item)


def symbols(x):
    if isinstance(x, Vector):
        return set()
    if isinstance(x, list):
        if x and x[0] in ("'", 'quote'):
            return set()
        return set().union(*(symbols(y) for y in x))
    return {str(x)}


def definition(x):
    if isinstance(x, list) and len(x) >= 3 and x[0] in ('define', 'define-syntax'):
        return str(x[1][0] if isinstance(x[1], list) else x[1])
    return None


def contextual(top, target, ident):
    def replace(x):
        if x is target:
            return ['test-result', str(ident), x[1], x[2]]
        if is_test(x):
            return ['begin', x[1], x[2], '#f']
        if isinstance(x, Vector):
            return x
        if isinstance(x, list):
            if x and x[0] in ("'", '`', 'quote'):
                return x
            return [replace(y) for y in x]
        return x
    return replace(top)


def inventory(source):
    sites = [m.start() for m in re.finditer(r'\(test(?=\s|\))', source)]
    ids = {pos: i for i, pos in enumerate(sites)}
    contexts, prefix = {}, []
    for top in forms(source):
        for target in walk(top):
            if not is_test(target):
                continue
            ident = ids[target.start]
            context = contextual(top, target, ident)
            # Keep all versions of a binding, not just its latest definition.
            definitions = {}
            for item in prefix:
                name = definition(item)
                if name:
                    definitions.setdefault(name, []).append(item)

            def dependencies(expr):
                refs = symbols(expr)
                while True:
                    more = set().union(*(symbols(val) for key in refs
                                         for val in definitions.get(key, [])))
                    if more <= refs:
                        return refs
                    refs |= more

            def eager_references(expr):
                if definition(expr):
                    # Installing a procedure does not execute its body. Other
                    # initializers can mutate state even if their name is unused.
                    if isinstance(expr[1], list):
                        return set()
                    expr = expr[2]
                    if isinstance(expr, list) and expr and expr[0] == 'lambda':
                        return set()
                return dependencies(expr)

            needed = dependencies(context)
            chosen = set()
            while True:
                add = {i for i, item in enumerate(prefix) if i not in chosen and
                       (definition(item) in needed or
                        eager_references(item) & needed & definitions.keys())}
                if not add:
                    break
                chosen |= add
                for i in add:
                    needed |= dependencies(prefix[i])
            # Replay earlier tests as expressions, preserving their effects but
            # emitting a comparison only for this context's target.
            prelude = [contextual(item, None, ident) for i, item in enumerate(prefix) if i in chosen]
            contexts[ident] = '\n'.join(map(render, prelude + [context]))
        prefix.append(top)
    return sites, contexts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample', type=int, default=1)
    parser.add_argument('--suite', type=Path, default=ROOT / 'conformance/scheme/fixtures/r7rs-tests.scm')
    parser.add_argument('--evidence', type=Path, default=ROOT.parent / 'evidence/score')
    args = parser.parse_args()
    if args.sample < 1:
        parser.error('--sample must be positive')
    folder = args.evidence.resolve()
    folder.mkdir(parents=True, exist_ok=True)
    source = args.suite.read_text()
    sites, contexts = inventory(source)
    chosen = list(range(0, len(sites), args.sample))
    results = {i: 'non-executable source site' for i in chosen if i not in contexts}
    cc = compiler(folder)
    serial = 0

    def batch(ids):
        nonlocal serial
        serial += 1
        name = f'batch-{serial:03d}'
        scm = folder / (name + '.scm')
        # Isolate top-level bindings between test cases, without losing their scope.
        scm.write_text('\n'.join('(let ()\n' + contexts[i] + '\n)' for i in ids) + '\n')
        try:
            binary = compile_program(cc, scm, folder, name)
            run = subprocess.run([str(binary)], text=True, capture_output=True, stdin=subprocess.DEVNULL, timeout=15)
            (folder / (name + '.run.log')).write_text(run.stdout + run.stderr)
            reports = {int(i): status for status, i in re.findall(r'^(PASS|FAIL) (\d+)$', run.stdout, re.M)}
            results.update({i: reports[i] for i in ids if i in reports})
            ids = [i for i in ids if i not in reports]
            if not ids:
                return
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            (folder / (name + '.failure.log')).write_text(str(exc) + '\n')
        if len(ids) == 1:
            results[ids[0]] = 'compile/runtime refusal: ' + name
        else:
            mid = len(ids) // 2
            batch(ids[:mid])
            batch(ids[mid:])

    runnable = [i for i in chosen if i in contexts]
    for start in range(0, len(runnable), 4):
        batch(runnable[start:start + 4])
    for i in chosen:
        print(f'{i}: {results[i]}')
    passed = sum(status == 'PASS' for status in results.values())
    record = {'textual_sites': len(sites), 'executable_tests': len(contexts),
              'sample': args.sample, 'passed': passed, 'total': len(chosen), 'results': results}
    (folder / 'results.json').write_text(json.dumps(record, indent=2) + '\n')
    print(f'TOTAL {passed}/{len(chosen)}', flush=True)
    if args.sample == 10 and len(sites) == 989 and passed < 30:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
