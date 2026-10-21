#!/usr/bin/env python3
"""Exercise compiler identity at the build, verification and promotion boundaries."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_receipt import check, digest, hashes, write

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('mode', choices=['verify', 'promotion', 'source'])
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
os.chdir(root)
output = args.output.resolve()
output.mkdir(parents=True, exist_ok=True)
output = Path(tempfile.mkdtemp(prefix=args.mode + '-', dir=output))
env = dict(os.environ, JOBS='2', TMPDIR=str(output), LANG_ROOT=str(root))
for key in ('COMPILER', 'LANGOS', 'LANGBE', 'LANGLIBC', 'COMPILER_RECEIPT', 'LANG_CACHE'):
    env.pop(key, None)


def run(label, command, expected=0, cwd=root):
    with (output / (label + '.txt')).open('wb') as log:
        result = subprocess.run(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
    print(f'{label}: exit {result.returncode}; log {output / (label + ".txt")}', flush=True)
    assert result.returncode == expected, f'{label}: expected {expected}, got {result.returncode}'
    return result


def stable():
    p = Path('out/lang')
    return dict(sha256=digest(p), link=os.readlink(p) if p.is_symlink() else None,
                version=subprocess.check_output([str(p.resolve()), 'version'], text=True))


if args.mode == 'promotion':
    # Promotion intentionally changes roots; preserve the caller's seed and stable binary.
    checkout = Path(tempfile.mkdtemp(prefix='promotion-', dir=output)) / 'repo'
    run('clone', ['git', 'clone', '--no-hardlinks', str(root), str(checkout)])
    env['LANG_ROOT'] = str(checkout)
    before = hashes('bootstrap/current')
    run('bootstrap', ['make', 'bootstrap', 'PUBLISH_BOOTSTRAP=0'], cwd=checkout)
    receipt = json.loads((checkout / 'out/bootstrap-receipt.json').read_text())
    assert receipt['mode'] == 'promotion'
    assert receipt['bootstrap']['inputs'] == before
    assert receipt['compiler']['sha256'] == digest(checkout / 'out/lang')
    assert (checkout / 'bootstrap/current/COMMIT').read_text().strip() == receipt['source']['revision'][:7]
    for p, item in receipt['artifacts'].items():
        assert item['sha256'] == digest(checkout / p)
    assert receipt['bootstrap']['inputs'] != {str(p.relative_to(checkout)): digest(p) for p in (checkout / 'bootstrap/current').rglob('*') if p.is_file()}
    archive = checkout / 'bootstrap/archive' / receipt['bootstrap']['identity']
    assert {str(p.relative_to(archive)): digest(p) for p in archive.rglob('*') if p.is_file()} == {str(Path(p).relative_to('bootstrap/current')): h for p, h in before.items()}, 'local archive differs from input seed'
    assert hashes('bootstrap/current') == before
    write(output / 'receipt.json', receipt)
else:
    if not Path('out/lang').exists():
        run('init', ['make', 'init'])
    before = {'seed': hashes('bootstrap/current'), 'stable': stable()}
    run('build', ['make', 'build'])
    assert before == {'seed': hashes('bootstrap/current'), 'stable': stable()}, 'build promoted the candidate'
    receipt = json.loads(Path('out/build-receipt.json').read_text())
    check(receipt, 'out/lang_next')
    assert receipt['source']['revision'] == subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    if args.mode == 'verify':
        replay_hashes = None
        for attempt in (1, 2):
            run(f'verify-{attempt}', ['make', 'verify'])
            after = {'seed': hashes('bootstrap/current'), 'stable': stable()}
            assert after == before, 'verification changed seed or stable compiler identity'
            verified = json.loads(Path('out/verify-receipt.json').read_text())
            check(verified, 'out/bootstrap_verify/kernel2')
            actual_hashes = {Path(p).name: item['sha256'] for p, item in verified['artifacts'].items()}
            if replay_hashes is not None:
                assert actual_hashes == replay_hashes, 'verification replay changed fixed-point artifacts'
            replay_hashes = actual_hashes
            for left, right in [('kernel2.ll', 'kernel3.ll'), ('reader_ast1.ast', 'reader_ast2.ast')]:
                assert digest('out/bootstrap_verify/' + left) == digest('out/bootstrap_verify/' + right)
            write(output / f'verify-{attempt}.json', verified)
        write(output / 'preservation.json', dict(before=before, after=after))
    else:
        compiler = str(Path('out/lang_next').resolve())
        # Follow the generated-reader tutorial, then pack the same reader into a native compiler.
        run('tutorial-new', [compiler, 'new', 'reader', 'tiny'], cwd=output)
        run('tutorial-run', [compiler, 'run', 'tiny.lang', 'answer.tiny'], expected=42, cwd=output)
        run('tutorial-read', [compiler, 'read', 'tiny.lang', 'answer.tiny', '-o', 'answer.ast'], cwd=output)
        run('tutorial-ast', [compiler, '--from-ast', 'answer.ast', '--ast-source', 'answer.tiny', '-o', 'answer.ll'], cwd=output)
        run('pack', [compiler, 'compiler', 'tiny', 'tiny.lang', '-o', 'tinyc'], cwd=output)
        run('pack-compile', [str(output / 'tinyc'), 'answer.tiny', '-o', 'packed.ll'], cwd=output)
        for label, ir in [('tutorial', 'answer.ll'), ('packed', 'packed.ll')]:
            run(label + '-link', ['clang', '-O2', ir, '-o', label], cwd=output)
            run(label + '-execute', [str(output / label)], expected=42, cwd=output)
        check(receipt, compiler)
        # A receipt for different compiler bytes or source inputs must fail closed.
        wrong = json.loads(json.dumps(receipt))
        wrong['compiler']['sha256'] = '0' * 64
        write(output / 'wrong-compiler.json', wrong)
        run('reject-wrong-compiler', [sys.executable, 'scripts/build_receipt.py', 'check', '--input', str(output / 'wrong-compiler.json'), '--compiler', compiler], expected=1)
        wrong = json.loads(json.dumps(receipt))
        wrong['source']['inputs']['src/main.lang'] = '0' * 64
        write(output / 'wrong-source.json', wrong)
        run('reject-wrong-source', [sys.executable, 'scripts/build_receipt.py', 'check', '--input', str(output / 'wrong-source.json'), '--compiler', compiler], expected=1)
        write(output / 'receipt.json', dict(compiler=receipt, gates=['tutorial', 'pack'], expected_exit=42))
print('PASS ' + args.mode + ' identity')
