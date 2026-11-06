#!/usr/bin/env python3
"""Small committed generated-parser recovery fragment with external receipts."""
import argparse
import os
from pathlib import Path
import re
import resource
import shutil
import sys
import uuid

from diagnostics import DiagnosticReplay
from route import ROOT, dump, require, sha

BASE = '79d0cae5c5ba84d30c8348c0d4a053b7dc5b1f0d'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['settings'], required=True)
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    os.nice(10)
    cpus = sorted(os.sched_getaffinity(0))[:2]
    os.sched_setaffinity(0, cpus)
    ceiling = 2 * 1024**3
    hard = resource.getrlimit(resource.RLIMIT_AS)[1]
    if hard != resource.RLIM_INFINITY:
        ceiling = min(ceiling, hard)
    resource.setrlimit(resource.RLIMIT_AS, (ceiling, ceiling))
    token = uuid.uuid4().hex
    evidence = (args.evidence or ROOT.parent / 'evidence' / ('recovery-' + token)).resolve()
    require(ROOT != evidence and ROOT not in evidence.parents, 'evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=False)
    scratch = ROOT.parent / 'scratch' / ('recovery-' + token)
    scratch.mkdir(parents=True)
    replay = DiagnosticReplay(evidence, scratch)
    print(f'evidence: {evidence}', flush=True)
    try:
        status = replay.run(['git', 'status', '--porcelain', '--untracked-files=all'], 'clean', ROOT)
        require(not status.stdout, 'commit candidate before running fragment')
        head = replay.run(['git', 'rev-parse', 'HEAD'], 'head', ROOT).stdout.decode().strip()
        replay.run(['git', 'merge-base', '--is-ancestor', BASE, head], 'base', ROOT)
        replay.run(['git', 'diff', '--exit-code', BASE, '--', 'bootstrap/current',
                    'web/stdlib.js', 'web/stdlib.json', 'web/compiler.wasm'], 'protected', ROOT)
        clone = scratch / 'repo'
        replay.run(['git', 'clone', '--no-hardlinks', '--quiet', str(ROOT), str(clone)], 'clone', ROOT)
        files = replay.run(['git', 'ls-files', '-z'], 'inputs', clone).stdout.decode().split('\0')
        dump(evidence / 'identity.json', {'head': head,
             'source_sha256': {p: sha(clone / p) for p in files if p and (clone / p).is_file()},
             'tools': {n: {'path': str(Path(shutil.which(n)).resolve()), 'sha256': sha(Path(shutil.which(n)).resolve())}
                       for n in ('python3', 'git', 'make', 'clang', 'ld')},
             'limits': {'cpus': cpus, 'address_space_bytes': ceiling, 'JOBS': 2},
             'assumptions': 'Headless Linux x86-64 libc; syntax trees are editor-only; semicolon consumes, brace stops; no OS kernel work; sequential fragment only; fixed points deferred to integration'})
        fixture = Path('test/reader_author/fixtures/recovery')
        shutil.copytree(clone / fixture, evidence / 'fixtures')
        replay.run(['make', 'init'], 'seed', clone)
        replay.run(['make', 'build'], 'build', clone)
        compiler = clone / 'out/lang_next'
        probe = scratch / 'probe'
        ir = scratch / 'probe.ll'
        replay.run([str(compiler), str(fixture / 'probe.lang'), '-o', str(ir)], 'probe-build', clone)
        replay.run(['clang', str(ir), '-o', str(probe)], 'probe-link', clone)

        def run(mode, filename, name, expected=0):
            return replay.run([str(probe), mode, str(fixture / filename)], name, clone, expected)

        damaged = run('editor', 'settings.shipping', 'two-errors')
        require(damaged.stdout == b'partial\n', 'damaged source must return a partial tree')
        tree = damaged.stderr.decode()
        raw = (clone / fixture / 'settings.shipping').read_bytes()
        errors = re.findall(r'^\s*error "(.*)" @(\d+):(\d+)$', tree, re.M)
        mismatches = re.findall(r'^\s*mismatch(?: <[^>]*>)? "([^"]*)" @(\d+):(\d+)$', tree, re.M)
        skipped = re.findall(r'^\s*skipped @(\d+):(\d+)$', tree, re.M)
        missing = re.findall(r'^\s*missing "([^"]*)" @(\d+):(\d+)$', tree, re.M)
        require(len(errors) == len(mismatches) == len(skipped) == len(missing) == 2, 'must preserve exactly two located errors and markers')
        require([raw[int(a):int(b)] for _, a, b in mismatches] == [b'nope', b';'], 'wrong diagnostic locations')
        require([raw[int(a):int(b)] for a, b in skipped] == [b'base nope;', b'free_over ;'], 'skipped statement bytes lost')
        require(all(a == b for _, a, b in missing), 'missing tokens must have zero-width spans')
        require('symbol "base" @' + str(raw.rindex(b'base')) in tree and 'number "7"' in tree, 'valid setting lost')
        for mode in ('strict', 'disabled'):
            run(mode, 'settings.shipping', mode + '-reject', expected=1)
        valid = 'example/shipping/policy.shipping'
        strict = replay.run([str(probe), 'strict', valid], 'valid-strict', clone)
        editor = replay.run([str(probe), 'editor', valid], 'valid-editor', clone)
        disabled = replay.run([str(probe), 'disabled', valid], 'valid-disabled', clone)
        require(strict.stdout == editor.stdout == disabled.stdout == b'complete\n' and
                strict.stderr == editor.stderr == disabled.stderr, 'successful parse shape changed')
        legacy = run('legacy', 'number.shipping', 'legacy-rule-name')
        require(b'number "42"' in legacy.stderr, 'existing recover rule name changed')
        choice = run('choice', 'choice.shipping', 'ordered-choice')
        require(b'<short>' in choice.stderr and b'<long>' not in choice.stderr, 'ordered transactional choice changed')
        repeated = run('editor', 'repeated.shipping', 'repeated-delimiters')
        require(len(re.findall(rb'^\s*error ', repeated.stderr, re.M)) == 3 and b'number "7"' in repeated.stderr, 'repeated delimiters stalled')
        eof = run('setting', 'eof.shipping', 'eof')
        size = len((clone / fixture / 'eof.shipping').read_bytes())
        require(f'missing "\';\'" @{size}:{size}'.encode() in eof.stderr, 'EOF missing token lost')
        run('setting', 'stop.shipping', 'stop-no-progress', expected=1)
        zero = run('zero', 'stop.shipping', 'zero-width')
        require(len(re.findall(rb'^\s*error ', zero.stderr, re.M)) == 2, 'zero-width tokens stalled')
        # Strict reader and minted compiler must reject before any runnable IR.
        source = str(fixture / 'settings.shipping')
        rejected = replay.run([str(compiler), 'read', 'example/shipping/shipping.lang', source], 'strict-reader', clone, 1)
        require(not rejected.stdout and b'expected number' in rejected.stderr, 'strict reader accepted damaged input')
        minted = scratch / 'shippingc'
        replay.run([str(compiler), 'compiler', 'shipping', 'example/shipping/shipping.lang', '-o', str(minted)], 'mint', clone)
        output = scratch / 'rejected.ll'
        replay.run([str(minted), source, '-o', str(output)], 'strict-compiler', clone, 1)
        require(not output.exists(), 'damaged program reached runnable IR')
        dump(evidence / 'artifacts.json', {'compiler': sha(compiler.resolve()), 'probe': sha(probe), 'minted': sha(minted)})
        dump(evidence / 'result.json', {'pass': True, 'head': head, 'commands': len(replay.rows)})
        print('PASS settings: two errors, valid node, strict rejection, unchanged success, choice, EOF, delimiters, zero-width')
        return 0
    except Exception as error:
        dump(evidence / 'result.json', {'pass': False, 'error': str(error)})
        print(f'FAIL: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
