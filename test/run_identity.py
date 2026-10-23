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
from build_receipt import check, digest, hashes, write, require

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


def run(label, command, expected=0, cwd=root, run_env=None):
    with (output / (label + '.txt')).open('wb') as log:
        result = subprocess.run(command, cwd=cwd, env=run_env or env, stdout=log, stderr=subprocess.STDOUT)
    print(f'{label}: exit {result.returncode}; log {output / (label + ".txt")}', flush=True)
    require(result.returncode == expected, f'{label}: expected {expected}, got {result.returncode}')
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
    require(receipt['mode'] == 'promotion', 'identity validation failed')
    require(receipt['bootstrap']['inputs'] == before, 'identity validation failed')
    require(receipt['compiler']['sha256'] == digest(checkout / 'out/lang'), 'identity validation failed')
    require((checkout / 'bootstrap/current/COMMIT').read_text().strip() == receipt['source']['revision'][:7], 'identity validation failed')
    for p, item in receipt['artifacts'].items():
        require(item['sha256'] == digest(checkout / p), 'identity validation failed')
    require(receipt['bootstrap']['inputs'] != {str(p.relative_to(checkout)): digest(p) for p in (checkout / 'bootstrap/current').rglob('*') if p.is_file()}, 'identity validation failed')
    archive = checkout / 'bootstrap/archive' / receipt['bootstrap']['identity']
    require({str(p.relative_to(archive)): digest(p) for p in archive.rglob('*') if p.is_file()} == {str(Path(p).relative_to('bootstrap/current')): h for p, h in before.items()}, 'local archive differs from input seed')
    require(hashes('bootstrap/current') == before, 'identity validation failed')
    write(output / 'receipt.json', receipt)
else:
    if not Path('out/lang').exists():
        run('init', ['make', 'init'])
    before = {'seed': hashes('bootstrap/current'), 'stable': stable()}
    run('build', ['make', 'build'])
    require(before == {'seed': hashes('bootstrap/current'), 'stable': stable()}, 'build promoted the candidate')
    receipt = json.loads(Path('out/build-receipt.json').read_text())
    check(receipt, 'out/lang_next')
    require(receipt['source']['revision'] == subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(), 'identity validation failed')
    if args.mode == 'verify':
        replay_hashes = None
        for attempt in (1, 2):
            run(f'verify-{attempt}', ['make', 'verify'])
            after = {'seed': hashes('bootstrap/current'), 'stable': stable()}
            require(after == before, 'verification changed seed or stable compiler identity')
            verified = json.loads(Path('out/verify-receipt.json').read_text())
            check(verified, 'out/bootstrap_verify/kernel2')
            actual_hashes = {Path(p).name: item['sha256'] for p, item in verified['artifacts'].items()}
            if replay_hashes is not None:
                require(actual_hashes == replay_hashes, 'verification replay changed fixed-point artifacts')
            replay_hashes = actual_hashes
            for left, right in [('kernel2.ll', 'kernel3.ll'), ('reader_ast1.ast', 'reader_ast2.ast')]:
                require(digest('out/bootstrap_verify/' + left) == digest('out/bootstrap_verify/' + right), 'identity validation failed')
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
        # Test each receipt consumer with all Python optimization entry points.
        # finish consumes a start receipt; it binds a new compiler rather than
        # validating an existing compiler identity.
        run('control-web-version', [sys.executable, 'scripts/build_receipt.py', 'web-version',
                                   '--input', 'out/build-receipt.json', '--compiler', compiler,
                                   '--output', 'out/web_version_info.lang'])
        controls = []
        for mode, flags, optimize in [('normal', [], '0'), ('O', ['-O'], '0'),
                                      ('env', [], '1')]:
            control_env = dict(env, PYTHONOPTIMIZE=optimize)
            for action in ('finish', 'check', 'web-version', 'web'):
                good = json.loads(json.dumps(receipt))
                if action == 'finish':
                    good.pop('compiler')
                    good.pop('artifacts')
                cases = [('valid', good, 0)]
                wrong = json.loads(json.dumps(good))
                wrong['source']['inputs']['src/main.lang'] = '0' * 64
                cases.append(('wrong-source', wrong, 1))
                if action != 'finish':
                    for field, value in [('sha256', '0' * 64), ('version', 'wrong version\n')]:
                        wrong = json.loads(json.dumps(good))
                        wrong['compiler'][field] = value
                        cases.append(('wrong-' + field, wrong, 1))
                wrong = json.loads(json.dumps(good))
                wrong['schema'] = 99
                cases.extend([('wrong-schema', wrong, 1), ('missing-fields', {}, 1),
                              ('wrong-type', [], 1), ('invalid-json', None, 1)])
                for name, value, expected in cases:
                    label = f'{mode}-{action}-{name}'
                    path = output / (label + '.json')
                    if name == 'invalid-json':
                        path.write_text('{invalid json')
                    else:
                        write(path, value)
                    destination = output / (label + '.output')
                    command = [sys.executable, *flags, 'scripts/build_receipt.py', action,
                               '--input', str(path), '--compiler', compiler,
                               '--output', str(destination)]
                    run(label, command, expected=expected, run_env=control_env)
                    if expected:
                        require(not destination.exists(), label + ': wrote output for invalid receipt')
                    controls.append(dict(mode=mode, action=action, case=name, exit=expected))
        write(output / 'controls.json', controls)
        write(output / 'receipt.json', dict(compiler=receipt, gates=['tutorial', 'pack'], expected_exit=42))
print('PASS ' + args.mode + ' identity')
