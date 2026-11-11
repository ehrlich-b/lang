#!/usr/bin/env python3
"""Replay an archive-only config-language trial against retained external inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

# The retained inputs are pinned here so a replay cannot substitute its own proof.
PINNED_INPUTS = {'FRICTION.md': '1153bba196daf8bed819534274679045daeb07579cf83ace15ec9565199ddbb0',
 'brief.md': '00d4619c4c9b46f887c5b1e58fa401ae69ed8bff4c7ee7ec0388d09ba0cce07e',
 'check-trial.py': 'd4f07725c20fada35ee892cb181bfd6b9fdf1c9b4cc06e4a6cab8f5556f7e476',
 'docs-index.html': '0f39b19384a70b18af92f1b21c37ac48393523c4a0258a6d5a11d3eb9e989231',
 'docs-readers.html': '9aa74a22bb9e45efff158cdcc49401b47079dc303835b028aefd81ca10ef14e0',
 'fixtures/invalid-boolean.conf': 'b0638036619212cba7cda2f4162b63858a084747f33339fc2d1792b780df4c29',
 'fixtures/invalid-escape.conf': '09a4f0e0ef3ff6d4b9dbcbca5c48e30aeb2af4ae44aa5ceb4906832e29913f34',
 'fixtures/missing-bracket.conf': '34540d90a6857562a46d3f8e4d1f02adcf0a77607e12c75064fb5c4aac052d1f',
 'fixtures/missing-equals.conf': '0343ec69b3249f277e1e51e8155901c9538ad456e2350c0da071686a02087c91',
 'fixtures/same-line.conf': 'e8fbbdc1fa77d0bf17ab4d57714f60ff3790bdd3048f8c313f02cde18af88e25',
 'fixtures/single-quote.conf': '91ceaef3166dc87427858b932907428fc64b57f4490caf8580959c4f200acd42',
 'fixtures/trailing.conf': '3a325cde85ea6dd5f17ad7fa923e10a94262814ac37ca6f3b7805bfe6a37421c',
 'fixtures/unterminated-string.conf': 'cf52f55ae149c501f156ced55e016254fb1109c2938586204198f80a6cdf1aeb',
 'fixtures/valid-edge.conf': '2bc2f6631150b9af30a6faa020b8e199bee08aa21165da93bcd8484ada6367b7',
 'gate-setup.log': 'e9b3b36e6f7e0f93b6a4ee8516d647ab0dc35c3e14da8987b69046048efd42dd',
 'harbor-config': '165a3ff8cb99b75cd04de6bf64bfcba5b13dcf2262f025937df8a0e4902e630b',
 'harbor.lang': '5c6ce77833ed754ec9261160ac4f2bcf7aa515a05359b4c8be3756f2b0836abc',
 'harbor.ll': 'd24ce88eabe77abe4ba017d06f86768c20509eba61cf49abcc8b3e1f3096404f',
 'lang-0.1.0+e5b90e2f0538-x86_64-linux.tar.xz': '310c6467386ca7f5375b3136d807e3acf7b669bfcd9d740f048f5f6aa80a0424',
 'reproduce.sh': 'a2fe227e5894a4ad726aa9c215e0ea50834bb0a9ce0eeef249bdb1784d082f5c',
 'run.py': 'bb2e948a4e5416ac52ed03dce2704b41f6dd44eb540b7fb2d9567de6b4eb6f84',
 'sample.conf': 'b38fbebbecf23226a4745bfb4726f44a8637e25fc7fcb14d959a7a69a83f97f4',
 'trial-boundary.md': '88b2a616a5b9eb65b227bce6badb997c8e964c1fcf59e73f1aeefe39373c386a',
 'trial-results.json': 'b81210143a33527730587e7c5ab0f94f0a9e8276924dde584a6395beade938d7',
 'trial.log': '8a844e513d06e6fdf3992327b7448bfadead8b71388081d502c508e90f9977ab'}
SDK_SHA256 = '310c6467386ca7f5375b3136d807e3acf7b669bfcd9d740f048f5f6aa80a0424'
AUTHOR = 'Bryan Ehrlich <ehrlich.bryan@gmail.com>'


def run(argv, **kwargs):
    print('$', ' '.join(map(str, argv)), flush=True)
    return subprocess.run(list(map(str, argv)), check=True, **kwargs)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--case', choices=['A1', 'A2', 'A3', 'A4', 'A5'], required=True)
    args = parser.parse_args()
    evidence = args.evidence.resolve()
    for name, expected in PINNED_INPUTS.items():
        assert digest(evidence / name) == expected, f'changed external input: {name}'
    trial = (evidence / 'trial.log').read_text()
    commands = re.findall(r'^\[[^\n]+\] \$ (.+)$', trial, re.M)
    assert commands, 'missing executed trial commands'
    if args.case == 'A1':
        assert os.geteuid() != 0
        assert all(not re.search(r'\b(sudo|modprobe|insmod|losetup|nbd-client|ublk)\b', c) for c in commands)
        print('PASS: unprivileged user; no operating-system kernel operations in trial commands')
    elif args.case == 'A2':
        archive = evidence / 'lang-0.1.0+e5b90e2f0538-x86_64-linux.tar.xz'
        assert digest(archive) == SDK_SHA256
        assert '[service]' in (evidence / 'brief.md').read_text()
        assert 'Trial complete: no checkout exists; uid= 1000' in trial
        scratch = evidence.parent / 'scratch'
        scratch.mkdir(exist_ok=True)
        output = Path(tempfile.mkdtemp(prefix='sdk-replay-', dir=scratch)) / 'output'
        run(['sh', evidence / 'reproduce.sh', output])
        for record in json.loads((evidence / 'trial-results.json').read_text()):
            source = evidence / record['file']
            if not source.is_file():
                source = evidence / 'fixtures' / record['file']
            result = subprocess.run([str(output / 'harbor-config'), str(source)], capture_output=True, text=True)
            assert result.returncode == record['exit'], record['file']
            assert result.stdout == record['stdout'], record['file']
            # Recorded diagnostics contain the trial's original absolute path.
            # Require the same diagnostic at the relocated input path.
            expected_stderr = re.sub(r'^.*?(?=:\d+:\d+:)', lambda _: str(source),
                                     record['stderr'], count=1)
            assert result.stderr == expected_stderr, record['file']
        assert (evidence / 'harbor-config').read_bytes().startswith(b'\x7fELF')
        print('PASS: pinned public SDK replay; native sample exit 0; ten config cases reproduced')
    elif args.case == 'A3':
        friction = (evidence / 'FRICTION.md').read_text()
        assert '| File? | Line? | Column? | Expected tokens? |' in friction
        for record in json.loads((evidence / 'trial-results.json').read_text()):
            if not record['valid']:
                assert record['file'] in friction
                assert re.search(r':\d+:\d+: expected .+, found ', record['stderr'])
        for message in ['unsupported global initializer', 'linker command failed', 'FileNotFoundError',
                        "couldn't find remote ref", 'not accessible via this tool', 'git clone']:
            assert message in friction, message
        print('PASS: exact error/dead-end log with diagnostic-field matrix; eight rejected configs')
    elif args.case == 'A4':
        assert not any(re.search(r'(^|\s)git\s+clone\b|\bmake\s+(init|build|bootstrap)\b', c) for c in commands)
        assert not any('src/compiler' in c or 'src/main.lang' in c for c in commands)
        assert 'no checkout exists' in trial
        assert 'strictly after this boundary' in (evidence / 'trial-boundary.md').read_text()
        print('PASS: trial commands contain no repository clone or compiler build; gate setup is separately logged')
    elif args.case == 'A5':
        assert os.geteuid() != 0
        commits = subprocess.check_output(['git', 'log', '--format=%an <%ae>|%cn <%ce>', '1d76914..HEAD'], text=True).splitlines()
        assert commits and all(c == AUTHOR + '|' + AUTHOR for c in commits)
        assert not any(re.search(r'\b(sudo|push|deploy|xdg-open)\b', c) for c in commands)
        print('PASS: candidate authors/committers match; headless unprivileged trial; see provenance boundary for audit limits')


if __name__ == '__main__':
    main()
