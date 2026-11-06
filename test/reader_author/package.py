#!/usr/bin/env python3
"""Prove the committed local compiler export in a source-free filesystem namespace."""
import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import sys
import tarfile
import uuid

from native_build import NativeReplay
from route import ROOT, dump, require, sha

BASE = 'dea0065aaba6729afdc97097d4998216d6baa1f6'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['relocated'], required=True)
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
    evidence = (args.evidence or ROOT.parent / 'evidence' / ('package-' + token)).resolve()
    require(evidence != ROOT and ROOT not in evidence.parents, 'evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=False)
    scratch = ROOT.parent / 'scratch' / ('package-' + token)
    scratch.mkdir(parents=True)
    replay = NativeReplay(evidence, scratch)
    replay.env.update(MAKEFLAGS='-j2', PYTHONDONTWRITEBYTECODE='1')
    for key in ('VERIFY_CASE', 'LANG_CLANG', 'LANG_ROOT'):
        replay.env.pop(key, None)
    print('evidence: ' + str(evidence), flush=True)
    try:
        status = replay.run(['git', 'status', '--porcelain', '--untracked-files=all'], 'clean', ROOT)
        require(not status.stdout, 'commit the candidate before replaying it')
        head = replay.run(['git', 'rev-parse', 'HEAD'], 'head', ROOT).stdout.decode().strip()
        replay.run(['git', 'merge-base', '--is-ancestor', BASE, head], 'required-base', ROOT)
        replay.run(['git', 'diff', '--exit-code', BASE, head, '--', 'bootstrap/current', 'web'],
                   'protected-inputs', ROOT)
        clone = scratch / 'repo'
        replay.run(['git', 'clone', '--quiet', '--no-hardlinks', str(ROOT), str(clone)], 'clone', ROOT)
        files = replay.run(['git', 'ls-files', '-z'], 'inputs', clone).stdout.decode().split('\0')
        hashes = {p: sha(clone / p) for p in files if p and (clone / p).is_file()}
        tools = {}
        for name in ('make', 'clang', 'ld', 'python3', 'git', 'bwrap', 'ldd'):
            found = shutil.which(name)
            require(found is not None, name + ' is required')
            path = Path(found).resolve()
            tools[name] = dict(path=str(path), sha256=sha(path))
        dump(evidence / 'identity.json', dict(head=head, base=BASE, source_sha256=hashes, tools=tools,
             limits=dict(cpus=cpus, address_space_bytes=ceiling, JOBS=2, MAKEFLAGS='-j2'),
             assumptions='Linux x86-64 glibc; trusted native frontend; dynamic libc; Python 3 verifier; '
                         'native -O0 with explicit Clang; bubblewrap hides both source roots and disables network; '
                         'no OS kernel tests, fixed points, web generation, installs or publication'))
        replay.run(['make', 'init'], 'init', clone)
        replay.run(['make', 'build'], 'build-current-sources', clone)
        compiler = str(clone / 'out/lang_next')
        shipping = clone / 'example/shipping'
        project = shipping / 'project.lang-project'
        metadata = shipping / 'package.json'
        archive = evidence / 'shipping-kit.tar.gz'

        def package(meta, output, name, expected=0):
            result = replay.run([compiler, 'package', '--project', str(project), '--metadata', str(meta),
                                 '-o', str(output)], name, scratch, expected)
            if expected:
                require(not output.exists(), name + ': failed packaging emitted an archive')
                require(b'Packaged ' not in result.stdout, name + ': failure announced success')
            return result

        # Prove required metadata refusal before creating the successful archive.
        original_metadata = json.loads(metadata.read_text())
        for field in ('runtime_contract', 'licenses'):
            bad = dict(original_metadata)
            bad.pop(field)
            path = scratch / ('missing-' + field + '.json')
            dump(path, bad)
            package(path, scratch / ('missing-' + field + '.tar.gz'), 'missing-' + field, 1)
        bad = dict(original_metadata, licenses=[dict(component=c, file='absent-notice')
                                               for c in ('compiler', 'reader', 'runtime')])
        path = scratch / 'absent-notice.json'
        dump(path, bad)
        package(path, scratch / 'absent-notice.tar.gz', 'absent-notice', 1)
        package(metadata, archive, 'package')
        unpacked = scratch / 'relocated directory with spaces'
        unpacked.mkdir()
        with tarfile.open(archive) as bundle:
            members = bundle.getmembers()
            require(all(not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
                        and (m.isfile() or m.isdir()) for m in members), 'unsafe archive member')
            bundle.extractall(unpacked)
        kit = unpacked / 'kit'
        receipt = json.loads((kit / 'receipt.json').read_text())
        shutil.copyfile(kit / 'receipt.json', evidence / 'dependency-receipt.json')
        require(receipt['compiler_build']['source']['revision'] == head, 'receipt names another candidate')
        for input_path in (project, shipping / 'shipping.lang', shipping / 'runtime.lang',
                           shipping / 'policy.shipping', clone / 'std/core.lang', clone / 'std/os/libc.lang'):
            require(receipt['inputs_sha256'].get(str(input_path.resolve())) == sha(input_path),
                    'missing resolved input hash: ' + str(input_path))
        require(receipt['dependencies']['linkage'] == 'dynamic' and
                'libc.so' in receipt['dependencies']['observations']['compiler'], 'untruthful linkage receipt')
        output = scratch / 'relocated output'
        output.mkdir()
        # Only the kit, output and system libraries/tools are mounted. Both
        # original checkout roots, caches and all other /work content are absent.
        isolation = [tools['bwrap']['path'], '--die-with-parent', '--unshare-net',
                     '--ro-bind', '/usr', '/usr', '--ro-bind', '/lib', '/lib',
                     '--ro-bind', '/lib64', '/lib64', '--ro-bind', '/etc', '/etc',
                     '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp',
                     '--ro-bind', str(kit), '/kit', '--bind', str(output), '/output',
                     '--chdir', '/output', '--clearenv', '--setenv', 'PATH', '/nonexistent',
                     '--setenv', 'LANGBE', 'llvm', '--setenv', 'LANGOS', 'linux', '--setenv', 'JOBS', '2']
        probe = ('from pathlib import Path; '
                 'roots=' + repr([str(ROOT), str(clone)]) + '; '
                 'assert all(not Path(p).exists() for p in roots); '
                 'print("source roots inaccessible:", roots)')
        replay.run([*isolation, '/usr/bin/python3', '-B', '-c', probe], 'source-roots-inaccessible', scratch)
        replay.run([*isolation, '/usr/bin/python3', '-B', '/kit/kit.py', 'verify'], 'relocated-verify', scratch)
        replay.run([*isolation, '/usr/bin/python3', '-B', '/kit/kit.py', 'llvm',
                    '--output', '/output/policy.ll'], 'relocated-llvm-no-tools', scratch)
        replay.run([*isolation, '/usr/bin/python3', '-B', '/kit/kit.py', 'native',
                    '--clang', tools['clang']['path'], '--output', '/output/shipping'], 'relocated-native', scratch)
        unbundled = scratch / 'unbundled'
        replay.run([compiler, 'build', '--project', str(project), str(shipping / 'policy.shipping'),
                    '--emit=llvm', '-o', str(unbundled.with_suffix('.ll'))], 'unbundled-llvm', scratch)
        replay.env['LANG_CLANG'] = tools['clang']['path']
        replay.run([compiler, 'build', '--project', str(project), str(shipping / 'policy.shipping'),
                    '-o', str(unbundled)], 'unbundled-native', scratch)
        require((output / 'policy.ll').read_bytes() == unbundled.with_suffix('.ll').read_bytes(),
                'packaged LLVM differs from unbundled shipping fixture')
        # Explicit expected outputs prevent agreement between two wrong programs.
        cases = [([], 64, b''), (['0'], 0, b'10\n'), (['99'], 0, b'10\n'),
                 (['100'], 0, b'0\n'), (['120'], 0, b'0\n'), (['1000000'], 0, b'0\n'),
                 (['1000001'], 64, b''), (['bad'], 64, b'')]
        for index, (arguments, code, stdout) in enumerate(cases):
            relocated = replay.run([*isolation, '/output/shipping', *arguments],
                                   'relocated-runtime-' + str(index), scratch, code)
            reference = replay.run([str(unbundled), *arguments], 'unbundled-runtime-' + str(index), scratch, code)
            require(relocated.stdout == reference.stdout == stdout and relocated.stderr == reference.stderr,
                    'runtime behavior differs at ' + repr(arguments))
            require((b'shipping:' in relocated.stderr) if code else not relocated.stderr, 'runtime diagnostic mismatch')
        replay.run([*isolation, '/usr/bin/python3', '-B', '/kit/kit.py', 'native',
                    '--output', '/output/unselected'], 'require-explicit-clang', scratch, 1)
        # Each mutant is a separate copy; retain the original archive and kit.
        for name in receipt['artifacts']:
            mutant = scratch / ('mutant-' + str(len(replay.rows)))
            shutil.copytree(kit, mutant)
            with (mutant / name).open('ab') as changed:
                changed.write(b'\n')
            result = replay.run(['/usr/bin/python3', '-B', str(mutant / 'kit.py'), 'verify'],
                                'changed-artifact-' + name.replace('/', '-'), scratch, 1)
            require(b'artifact hash mismatch' in result.stderr, 'changed artifact escaped hash verification')
        for field in ('runtime_contract', 'licenses', 'runtime_sources'):
            mutant = scratch / ('missing-contract-' + field)
            shutil.copytree(kit, mutant)
            contract_path = mutant / 'runtime/contract.json'
            contract = json.loads(contract_path.read_text())
            contract.pop(field)
            dump(contract_path, contract)
            modified_receipt = dict(receipt, artifacts=dict(receipt['artifacts']))
            modified_receipt['artifacts']['runtime/contract.json'] = sha(contract_path)
            dump(mutant / 'receipt.json', modified_receipt)
            replay.run(['/usr/bin/python3', '-B', str(mutant / 'kit.py'), 'verify'],
                       'missing-contract-' + field, scratch, 1)
        mutable_metadata = scratch / 'mutable-metadata.json'
        mutable = json.loads(metadata.read_text())
        for notice in mutable['licenses']:
            notice['file'] = str(clone / 'LICENSE')
        dump(mutable_metadata, mutable)
        replay.env.update(LANG_CLANG=str(clone / 'test/reader_author/fixtures/package/mutate_clang.py'),
                          PACKAGE_MUTATE=str(mutable_metadata), PACKAGE_REAL_CLANG=tools['clang']['path'])
        result = package(mutable_metadata, scratch / 'changed-input.tar.gz', 'changed-input-during-mint', 1)
        require(b'input hash changed during packaging' in result.stderr, 'input mutation was not diagnosed')
        require(all(sha(clone / p) == h for p, h in hashes.items()), 'test changed committed inputs')
        shutil.copyfile(output / 'policy.ll', evidence / 'policy.ll')
        dump(evidence / 'artifacts.json', dict(archive=sha(archive), compiler=sha(kit / 'bin/compiler'),
             llvm=sha(output / 'policy.ll'), native=sha(output / 'shipping'),
             unbundled_native=sha(unbundled)))
        dump(evidence / 'result.json', dict(passed=True, head=head, observations=len(replay.rows),
             acceptance=['A1', 'A2', 'A3', 'A4', 'A5']))
        print('PASS relocated package: source-free IR/native, explicit Clang, shipping parity, metadata and hash refusals')
        return 0
    except Exception as error:
        dump(evidence / 'result.json', dict(passed=False, error=str(error)))
        print('FAIL: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
