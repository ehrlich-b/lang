#!/usr/bin/env python3
"""Reproduce CPS acceptance checks with evidence outside the source checkout."""
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tarfile
import tempfile

REPO = Path(__file__).resolve().parents[2]
WORKSPACE = REPO.parent
os.chdir(REPO)
os.environ['TMPDIR'] = str(WORKSPACE / 'scratch/tmp')
Path(os.environ['TMPDIR']).mkdir(parents=True, exist_ok=True)
BASE = '7ef0a1b'
PARKED = 'd192699e7d3caf2983196143bf34074cfe63b2bb'

def git(*args, cwd=REPO):
    return subprocess.check_output(['git', *args], cwd=cwd, text=True).strip()

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def run(args, **kw):
    print('+', ' '.join(map(str, args)), flush=True)
    subprocess.run(args, check=True, **kw)

item = sys.argv[1]
if item == 'A1':
    host = socket.gethostname()
    print('hostname:', host, 'uid:', os.geteuid())
    assert os.geteuid() != 0
    assert host != 'forge', 'Compiler suites require a suitable host; exact forge host is blocked.'
    print('Ordinary compiler suites permitted; no module, block-device or privileged operations requested.')
elif item == 'A2':
    previous = WORKSPACE / 'sources/previous'
    if not previous.exists():
        run(['git', 'clone', '/work/cache/git/' + PARKED + '.git', str(previous)])
        run(['git', '-C', str(previous), 'checkout', PARKED])
    assert git('rev-parse', 'HEAD', cwd=previous) == PARKED
    ancestor = git('rev-parse', PARKED + '~5', cwd=previous)
    originals = git('rev-list', '--reverse', ancestor + '..' + PARKED, cwd=previous).splitlines()
    run(['git', 'merge-base', '--is-ancestor', ancestor, BASE])
    replay = git('log', '--reverse', '--format=%H%n%B', BASE + '..HEAD')
    assert len(originals) == 5
    for original in originals:
        assert '(cherry picked from commit ' + original + ')' in replay
        print('preserved replay:', original, git('show', '-s', '--format=%s', original, cwd=previous))
    run(['git', 'merge-base', '--is-ancestor', BASE, 'HEAD'])
    print('Conflict: src/codegen_llvm.lang generate_llvm initialization; retain main debug/timing setup and CPS reset.')
    print('Empty source baseline and witness import commits preserved because their patches already exist on main.')
    print(replay)
elif item == 'A3':
    run(['make', 'build'])
    baseline = WORKSPACE / 'sources/main'
    if not baseline.exists():
        run(['git', 'worktree', 'add', '--detach', str(baseline), BASE])
    if not (baseline / 'out/lang_next').exists():
        run(['make', 'build'], cwd=baseline)
    assert git('rev-parse', 'HEAD', cwd=baseline) == git('rev-parse', BASE)
    assert not git('status', '--porcelain', cwd=baseline)
    scratch = Path(tempfile.mkdtemp(prefix='effects-', dir=WORKSPACE / 'scratch'))
    env = dict(os.environ, COMPILER='out/lang_next', LANG_EFFECTS='cps',
               BASE_COMPILER=str(baseline / 'out/lang_next'),
               EFFECTS_EVIDENCE_DIR=str(scratch / 'safety'),
               EFFECTS_CPS_EVIDENCE_DIR=str(scratch / 'cps'),
               EFFECTS_LEGACY_EVIDENCE_DIR=str(scratch / 'legacy'),
               EFFECTS_MACRO_EVIDENCE_DIR=str(scratch / 'macro'))
    (WORKSPACE / 'evidence').mkdir(exist_ok=True)
    try:
        for runner in ['test/run_effects_safety.py', 'test/effects_cps/run.py',
                       'test/effects_cps/compare_legacy.py', 'test/effects_cps/macro_boundary.py']:
            run(['python3', '-B', runner], env=env)
    finally:
        archive = WORKSPACE / 'evidence' / (scratch.name + '.tar.gz')
        with tarfile.open(archive, 'w:gz') as output:
            for path in sorted(scratch.rglob('*')):
                if path.is_file() and path.suffix in ('.ll', '.lang', '.stdout', '.stderr', '.exit', '.json', '.tsv') and 'cache' not in path.parts:
                    output.add(path, arcname=str(path.relative_to(scratch)))
        print('IR, results and execution logs:', archive, 'bytes:', archive.stat().st_size, 'sha256:', sha(archive), flush=True)
elif item == 'A4':
    run(['git', 'diff', '--check', BASE, 'HEAD'])
    run(['git', 'diff', '--exit-code', BASE, 'HEAD', '--', 'bootstrap/current', 'web'])
    run(['git', 'diff', '--exit-code', BASE, '--', 'bootstrap/current', 'web'])
    receipt = json.loads((REPO / 'out/build-receipt.json').read_text())
    assert receipt['source']['revision'] == git('rev-parse', 'HEAD')
    assert receipt['source']['dirty'] is False
    assert receipt['compiler']['sha256'] == sha(REPO / 'out/lang_next')
    assert receipt['builder']['sha256'] == sha(REPO / 'out/lang')
    for path, digest in receipt['bootstrap']['inputs'].items():
        assert sha(REPO / path) == digest
    (WORKSPACE / 'evidence/final-build-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('Final compiler built by unchanged preserved seed:', receipt['builder'])
    print('bootstrap/current and web have no committed or working-tree changes.')
elif item == 'A5':
    commits = git('log', '--format=%H|%an|%ae|%cn|%ce|%s', BASE + '..HEAD').splitlines()
    assert commits
    for line in commits:
        head, author, email, committer, cmail, subject = line.split('|', 5)
        assert (author, email, committer, cmail) == ('Bryan Ehrlich', 'ehrlich.bryan@gmail.com', 'Bryan Ehrlich', 'ehrlich.bryan@gmail.com')
        assert subject.endswith('.')
        print(line)
    assert not git('status', '--porcelain')
    print('Headless decision: preserve replay history and combine independent initialization lines; no dialog needed.')
else:
    raise ValueError(item)
print(item + ': PASS', flush=True)
