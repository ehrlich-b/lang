#!/usr/bin/env python3
"""Replay the project fixture oracle from a committed compiler and native tools."""
import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import sys
import uuid

from project import ProjectReplay
from route import ROOT, dump, require, sha

BASE = '74c0af702c6065170621a53487834b2336d522b7'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['oracle'], required=True)
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
    evidence = (args.evidence or ROOT.parent / 'evidence' / ('oracle-' + token)).resolve()
    require(evidence != ROOT and ROOT not in evidence.parents, 'evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=False)
    scratch = ROOT.parent / 'scratch' / ('oracle-' + token)
    scratch.mkdir(parents=True)
    replay = ProjectReplay(evidence, scratch)
    replay.env.update(MAKEFLAGS='-j2', PYTHONDONTWRITEBYTECODE='1')
    print('evidence: ' + str(evidence), flush=True)
    try:
        result = replay.run(['git', 'status', '--porcelain', '--untracked-files=all'], 'clean', ROOT)
        require(not result.stdout, 'commit candidate before replay')
        head = replay.run(['git', 'rev-parse', 'HEAD'], 'head', ROOT).stdout.decode().strip()
        replay.run(['git', 'merge-base', '--is-ancestor', BASE, head], 'source-ancestry', ROOT)
        clone = scratch / 'repo'
        replay.run(['git', 'clone', '--quiet', '--no-hardlinks', str(ROOT), str(clone)], 'clone', ROOT)
        files = replay.run(['git', 'ls-files', '-z'], 'inputs', clone).stdout.decode().split('\0')
        hashes = {p: sha(clone / p) for p in files if p and (clone / p).is_file()}
        tools = {name: {'path': str(Path(shutil.which(name)).resolve()),
                        'sha256': sha(Path(shutil.which(name)).resolve())}
                 for name in ['make', 'clang', 'ld', 'python3', 'git']}
        dump(evidence / 'identity.json', {'head': head, 'base': BASE, 'source_sha256': hashes, 'tools': tools,
             'limits': {'cpus': cpus, 'address_space_bytes': ceiling, 'JOBS': 2, 'MAKEFLAGS': '-j2'},
             'assumptions': 'Native Linux x86-64 libc; inherited free_over/base are threshold/fee; '
                'located reader diagnostics are normalized into structured assertions; '
                'no OS kernel tests, full suites, fixed points or web regeneration'})
        replay.run(['make', 'init'], 'init', clone)
        replay.run(['make', 'build'], 'build-current-sources', clone)
        compiler = str(clone / 'out/lang_next')
        shipping = clone / 'example/shipping/project.lang-project'

        def test(name, project=shipping, cwd=clone, fixture=None, expected=0, fixtures=None):
            command = [compiler, 'test', '--project', str(project), '--evidence', str(evidence / name)]
            if fixture is not None:
                command += ['--fixture', fixture]
            if fixtures is not None:
                command += ['--fixtures', str(fixtures)]
            return replay.run(command, name, cwd, expected=expected)

        result = test('shipping')
        require(all(('PASS ' + name).encode() in result.stdout for name in ['policy', 'reordered', 'syntax', 'semantic']),
                'missing project fixture')
        receipts = json.loads((evidence / 'shipping/commands.json').read_text())
        require(any(set(row['phase_seconds']) == {'reader', 'validation', 'llvm', 'object', 'link'} for row in receipts),
                'phase timing incomplete')
        ident = json.loads((evidence / 'shipping/identity.json').read_text())
        require(ident['compiler']['sha256'] == sha(compiler) and ident['reader'] and ident['runtime'] and ident['toolchain'],
                'incomplete identities')
        test('named', fixture='semantic')
        named = json.loads((evidence / 'named/result.json').read_text())
        require(named['fixtures'] == [{'name': 'semantic', 'pass': True}], 'filter ran extra fixtures')
        result = test('unknown', fixture='absent', expected=1)
        require(b'unknown fixture' in result.stderr, 'empty filter silently passed')
        replay.run([compiler, 'new', 'language', 'parcel'], 'generate', scratch)
        project_dir = scratch / 'parcel'
        manifest = project_dir / 'project.lang-project'
        shutil.copytree(project_dir, evidence / 'generated')
        test('generated-pass', project=manifest, cwd=project_dir)
        policy = project_dir / 'policy.parcel'
        original_policy = policy.read_text()
        # Independent directories keep every control source intact for inspection.
        for name, old, new in [('free_at', 'free_over 100', 'free_over 101'), ('fee', 'base 10', 'base 11')]:
            edited = scratch / name
            shutil.copytree(evidence / 'generated', edited)
            (edited / 'policy.parcel').write_text(original_policy.replace(old, new))
            shutil.copyfile(edited / 'policy.parcel', evidence / (name + '.parcel'))
            result = test('changed-' + name, project=edited / 'project.lang-project', cwd=edited, fixture='policy', expected=1)
            require(b'FAIL policy:' in result.stderr and b'expected' in result.stderr,
                    name + ': semantic mutation did not visibly fail')
        # Wrong exits and wrong located assertions must also make the runner fail.
        suite = json.loads((project_dir / 'tests.json').read_text())
        for name in ['exit', 'diagnostic']:
            altered = json.loads(json.dumps(suite))
            if name == 'exit':
                altered['fixtures'][0]['runs'][0]['exit'] = 7
            else:
                altered['fixtures'][2]['diagnostic']['column'] += 1
            fixture_path = project_dir / ('wrong-' + name + '.json')
            dump(fixture_path, altered)
            shutil.copyfile(fixture_path, evidence / fixture_path.name)
            test('wrong-' + name, project=manifest, cwd=project_dir, fixtures=fixture_path,
                 fixture='policy' if name == 'exit' else 'semantic', expected=1)
        # A real unresolved native symbol: compilation exits 0, linking exits nonzero.
        broken = scratch / 'unresolved'
        shutil.copytree(evidence / 'generated', broken)
        runtime = broken / 'runtime.lang'
        runtime.write_text(runtime.read_text().replace('print_int(fee); println(""); return 0;',
            'return project_test_unresolved(fee);') + '\nextern func project_test_unresolved(fee i64) i64;\n')
        shutil.copyfile(runtime, evidence / 'unresolved-runtime.lang')
        result = test('link-failure', project=broken / 'project.lang-project', cwd=broken, fixture='policy', expected=1)
        require(b'FAIL policy:' in result.stderr, 'link failure counted as a pass')
        commands = json.loads((evidence / 'link-failure/commands.json').read_text())
        build = commands[-1]
        stderr = (evidence / 'link-failure' / build['stderr']).read_bytes()
        require(build['exit'] != 0 and b'native build linker failed' in stderr and
                b'project_test_unresolved' in stderr and build['phase_exits'].get('llvm') == 0 and build['phase_exits'].get('object') == 0 and
                build['phase_exits'].get('link', 0) != 0,
                'control failed before real native linking')
        require(not list((evidence / 'link-failure').glob('*.native')), 'failed link published an executable')
        require(all(sha(clone / p) == h for p, h in hashes.items()), 'oracle edited committed inputs')
        dump(evidence / 'result.json', {'pass': True, 'head': head, 'compiler_sha256': sha(compiler),
             'observations': len(replay.rows), 'controls': ['free_at', 'fee', 'exit', 'diagnostic', 'link-failure']})
        print('PASS oracle: committed ancestry, shared compiler, shipped fixtures, filter, native outputs, structured negatives, mutations, exit and link failure')
        return 0
    except Exception as error:
        dump(evidence / 'result.json', {'pass': False, 'error': str(error)})
        print('FAIL: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
