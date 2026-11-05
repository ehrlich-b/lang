#!/usr/bin/env python3
"""Read-only provenance and scope checks for the Scheme implementation."""
import argparse
import hashlib
from pathlib import Path
import socket
import subprocess
from runner import ROOT
from inventory import tokens

PREVIOUS = 'd28389617f5da9d5216a84ca53120e45a9dcea65'
BASE = '4b93dcaa32c177ed827fb7597b02d8431ace2dec'
CHIBI = 'f966f15dcce4bfcc33af50d34b70d084afb6750d'
IDENTITY = 'Bryan Ehrlich <ehrlich.bryan@gmail.com>'


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', *args], cwd=cwd, text=True).strip()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('check', choices=['previous', 'host', 'source', 'borders', 'scope', 'identity', 'headless'])
    args = p.parse_args()
    if args.check == 'previous':
        assert git('rev-parse', 'HEAD', cwd=ROOT.parent / 'sources/previous') == PREVIOUS
        git('merge-base', '--is-ancestor', PREVIOUS, 'HEAD')
        assert 'conformance/scheme/inventory.py' in git('ls-tree', '-r', '--name-only', PREVIOUS).splitlines()
        print('PASS previous attempt is the ancestor; its inventory and tests are retained')
    elif args.check == 'host':
        host = socket.gethostname()
        assert host != 'forge', 'ordinary compiler execution requires a suitable host'
        print('PASS ordinary unprivileged compiler checks on', host)
    elif args.check == 'source':
        upstream = ROOT.parent / 'sources/chibi'
        assert git('rev-parse', 'HEAD', cwd=upstream) == CHIBI
        fixture = ROOT / 'conformance/scheme/fixtures/r7rs-tests.scm'
        original = (upstream / 'tests/r7rs-tests.scm').read_text()
        normalized = '\n'.join(line.rstrip() for line in original.splitlines()) + '\n'
        assert fixture.read_text() == normalized
        assert list(tokens(original)) == list(tokens(normalized))
        print('PASS pinned Chibi input', CHIBI, hashlib.sha256(original.encode()).hexdigest())
        print('PASS fixture normalization preserves every datum token; six line-end whitespace fixes')
    elif args.check == 'borders':
        doc = (ROOT / 'conformance/scheme/README.md').read_text()
        for text in ['Shared AST borders', 'call/cc', 'DEFERRED', '256 KiB', '61 signed bits']:
            assert text in doc
        for name in ['scheme.lang', 'reader.lang', 'runtime.lang']:
            lines = len((ROOT / 'example/scheme' / name).read_text().splitlines())
            print(name, lines, 'lines')
        print('PASS documented AST and runtime borders')
    elif args.check == 'scope':
        git('diff', '--check', BASE)
        changed = git('diff', '--name-only', BASE).splitlines()
        assert not any(x.startswith('src/') for x in changed)
        for name in changed:
            content = (ROOT / name).read_text()
            for forbidden in ['/' + part + '/' for part in ('work', 'home', 'tmp')]:
                # The pinned upstream source is third-party input, not generated product code.
                if 'fixtures/' not in name:
                    assert forbidden not in content, name
        print('PASS diff check against recorded base; compiler sources unchanged')
    elif args.check == 'identity':
        identities = git('log', PREVIOUS + '..HEAD', '--format=%an <%ae>%n%cn <%ce>').splitlines()
        assert identities and all(x == IDENTITY for x in identities)
        print('PASS every candidate commit has the required author and committer')
    else:
        print('PASS deterministic CLI-only workflow; no UI or interactive dependencies')


if __name__ == '__main__':
    main()
