#!/usr/bin/env python3
"""Freeze static DejaGnu applicability without invoking a candidate compiler.

This is a bounded selector evaluator, not a DejaGnu replacement. Unknown
requirements remain reference-required; only proven exclusions become skips.
"""
import argparse
import fnmatch
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'conformance'
TARGETS = {
    'x86_64-linux-gnu': 'x86_64-pc-linux-gnu',
    'arm64-apple-macos': 'aarch64-apple-darwin',
}
# These are properties of the frozen hosted LP64 profiles, not toolchain probes.
FACTS = dict(lp64=True, llp64=False, ilp32=False, ia32=False,
             ptr32plus=True, int32plus=True, size20plus=True, freestanding=False)
OPTIMIZATIONS = ('-O0', '-O2')


def words(text):
    """Read a Tcl list's braces/quotes without substitution or code execution."""
    result = []
    i = 0
    while i < len(text):
        if text[i].isspace():
            i += 1
            continue
        if text[i] == '{':
            start = i = i + 1
            depth = 1
            while i < len(text) and depth:
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                i += 1
            if depth:
                raise ValueError('unterminated Tcl group')
            result.append(text[start:i-1].strip())
        elif text[i] == '"':
            start = i = i + 1
            while i < len(text) and text[i] != '"':
                if text[i] == '\\':
                    i += 1
                i += 1
            if i == len(text):
                raise ValueError('unterminated Tcl quote')
            result.append(text[start:i])
            i += 1
        else:
            start = i
            while i < len(text) and not text[i].isspace():
                i += 1
            result.append(text[start:i])
    return result


def any_of(values):
    values = list(values)
    return True if True in values else None if None in values else False


def all_of(values):
    values = list(values)
    return False if False in values else None if None in values else True


def selector(text, triple):
    def evaluate(parts):
        if not parts:
            return None
        for operator, combine in (('||', any_of), ('&&', all_of)):
            if operator in parts:
                chunks, chunk = [], []
                for part in parts + [operator]:
                    if part == operator:
                        chunks.append(evaluate(chunk))
                        chunk = []
                    else:
                        chunk.append(part)
                return combine(chunks)
        if parts[0] == '!':
            if len(parts) != 2:
                return None
            value = selector(parts[1], triple)
            return None if value is None else not value
        if len(parts) > 1:
            return any_of(selector(p, triple) for p in parts)
        token = parts[0]
        if len(words(token)) != 1 or token != words(token)[0]:
            return selector(token, triple)
        if token in FACTS:
            return FACTS[token]
        if token.count('-') >= 2:
            return fnmatch.fnmatchcase(triple, token)
        return None
    return evaluate(words(text))


def directives(case):
    for line in case.get('directives', []):
        match = re.search(r'\{\s*(dg-[\w-]+)', line)
        if not match:
            continue
        try:
            outer = words(line[match.start():])[0]
            yield words(outer)
        except ValueError:
            yield ['unparsed', line]


def option_match(patterns, flags, default):
    pats = words(patterns)
    if not pats or pats == ['']:
        return default
    return any(fnmatch.fnmatchcase(flag, pat) for pat in pats for flag in flags)


def classify(case, target, optimization):
    if case['corpus'] != 'gcc':
        return 'eligible'
    triple = TARGETS[target]
    ds = list(directives(case))
    flags = [*case['reference_flags'], optimization]
    pending = False
    # Establish options before resolving dg-skip-if's include/exclude lists.
    for d in ds:
        if d[0] in ('dg-options', 'dg-additional-options'):
            applies = selector(d[2][len('target '):], triple) if len(d) > 2 and d[2].startswith('target ') else True
            if applies is None:
                pending = True
            elif applies:
                flags.extend(words(d[1]))
    for d in ds:
        kind = d[0]
        if kind == 'dg-do' and len(d) > 2:
            value = selector(d[2][len('target '):], triple) if d[2].startswith('target ') else None
            if value is False:
                return 'platform-skip'
            pending |= value is None
        elif kind == 'dg-skip-if':
            if len(d) < 3:
                pending = True
                continue
            value = selector(d[2], triple)
            options = option_match(d[3], flags, True) if len(d) > 3 else True
            excluded = option_match(d[4], flags, False) if len(d) > 4 else False
            if options and not excluded:
                if value is True:
                    return 'platform-skip'
                pending |= value is None
        elif kind.startswith('dg-require-'):
            applies = selector(d[2][len('target '):], triple) if len(d) > 2 and d[2].startswith('target ') else True
            if applies is False:
                continue
            value = selector(d[1], triple) if kind == 'dg-require-effective-target' else None
            if applies is True and value is False:
                return 'platform-skip'
            pending |= applies is None or value is None
        elif kind == 'unparsed':
            pending = True
    # Diagnostics, xfail, support/.x files and runtime properties still require
    # the pinned upstream reference harness, even when static eligibility holds.
    return 'reference-required' if pending else 'eligible'


def applicability(case):
    return {target: {opt: classify(case, target, opt) for opt in OPTIMIZATIONS}
            for target in TARGETS}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    for path in sorted(ROOT.glob('C[123].json')):
        manifest = json.loads(path.read_text())
        if args.write:
            manifest['schema'] = 2
            manifest['applicability_contract'] = {
                'targets': TARGETS, 'profile_facts': FACTS,
                'mandatory': '100% of reference-applicable selected cases per target and optimization',
                'raw_floors': 'unchanged; additional pinned inventory cases in frozen hash order may meet floors; skips never count as passes',
                'reference': 'pending; static eligibility is not a reference receipt; unknown requirements must resolve before candidate work',
            }
            for case in manifest['cases']:
                case.pop('platform_skip_policy', None)
                case['applicability'] = applicability(case)
            path.write_text(json.dumps(manifest, indent=2) + '\n')
        else:
            assert manifest['applicability_contract']['targets'] == TARGETS
            assert manifest['applicability_contract']['profile_facts'] == FACTS
            for case in manifest['cases']:
                assert case['applicability'] == applicability(case), (path.name, case['path'])
        for target in TARGETS:
            for opt in OPTIMIZATIONS:
                counts = {}
                for corpus, kind in (('c-testsuite', 'execute'), ('gcc', 'execute'), ('gcc', 'compile-only')):
                    counts[corpus + '-' + kind] = {
                        status: sum(c['corpus'] == corpus and c['kind'] == kind
                                    and c['applicability'][target][opt] == status
                                    for c in manifest['cases'])
                        for status in ('eligible', 'platform-skip', 'reference-required')}
                print(path.stem, target, opt, json.dumps(counts, sort_keys=True))
    if args.write:
        (ROOT / 'SHA256SUMS').write_text(''.join(
            hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name + '\n'
            for p in sorted(ROOT.glob('*.json'))))


if __name__ == '__main__':
    main()
