#!/usr/bin/env python3
"""Check only the embedded-runtime shipping fragment, with external receipts."""
import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import uuid

from project import ProjectReplay
from route import ROOT, dump, require, sha

BASE = 'dea0065aaba6729afdc97097d4998216d6baa1f6'
FIXTURES = Path('test/reader_author/fixtures/runtime_reachability')


def limits():
    os.nice(10)
    cpus = sorted(os.sched_getaffinity(0))[:2]
    os.sched_setaffinity(0, cpus)
    hard = resource.getrlimit(resource.RLIMIT_AS)[1]
    ceiling = 2 * 1024**3
    if hard != resource.RLIM_INFINITY:
        ceiling = min(ceiling, hard)
    resource.setrlimit(resource.RLIMIT_AS, (ceiling, ceiling))
    return {'cpus': cpus, 'address_space_bytes': ceiling, 'JOBS': 2, 'MAKEFLAGS': '-j2'}


def check_measurements():
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    candidates = []
    for path in (ROOT.parent / 'evidence').glob('reachability-*/result.json'):
        result = json.loads(path.read_text())
        if result.get('pass') and not result.get('audit_only') and result.get('head') == head:
            candidates.append(path)
    require(candidates, 'run --case shipping at the current committed HEAD first')
    path = max(candidates, key=lambda p: p.stat().st_mtime_ns)
    measurements = json.loads((path.parent / 'measurements.json').read_text())
    require(measurements['ir_lines']['after'] < measurements['ir_lines']['before'], 'IR did not shrink')
    samples = measurements['samples']
    require(len(samples) == 20, 'need five before/after samples at each optimization level')
    for opt in ('O0', 'O2'):
        for variant in ('before', 'after'):
            rows = [r for r in samples if r['optimization'] == opt and r['variant'] == variant]
            require([r['sample'] for r in rows] == list(range(5)), 'missing interleaved sample')
            require(all(r['native_bytes'] > 0 and r['clang_cpu_seconds'] >= 0 for r in rows), 'invalid measurement')
    print(f'PASS measurements: {path.parent}; IR {measurements["ir_lines"]}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['shipping'])
    parser.add_argument('--audit', action='store_true')
    parser.add_argument('--check-measurements', action='store_true')
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    bounded = limits()
    if args.check_measurements:
        check_measurements()
        return 0
    require(args.case or args.audit, 'select --case shipping or --audit')
    token = uuid.uuid4().hex
    evidence = (args.evidence or ROOT.parent / 'evidence' / ('reachability-' + token)).resolve()
    require(evidence != ROOT and ROOT not in evidence.parents, 'evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=False)
    scratch = ROOT.parent / 'scratch' / ('reachability-' + token)
    scratch.mkdir(parents=True)
    replay = ProjectReplay(evidence, scratch)
    replay.env.update(MAKEFLAGS='-j2', PYTHONDONTWRITEBYTECODE='1', LANGLIBC='libc')
    replay.env.pop('VERIFY_CASE', None)
    replay.env.pop('LANG_CLANG', None)
    print(f'evidence: {evidence}', flush=True)
    try:
        status = replay.run(['git', 'status', '--porcelain', '--untracked-files=all'], 'clean', ROOT)
        require(not status.stdout, 'commit the candidate before replaying it')
        head = replay.run(['git', 'rev-parse', 'HEAD'], 'head', ROOT).stdout.decode().strip()
        replay.run(['git', 'merge-base', '--is-ancestor', BASE, head], 'required-base', ROOT)
        replay.run(['git', 'diff', '--exit-code', BASE, head, '--', 'bootstrap/current', 'web'],
                   'protected-inputs', ROOT)
        paths = replay.run(['git', 'ls-files', '-z'], 'source-inputs', ROOT).stdout.decode().split('\0')
        hashes = {p: sha(ROOT / p) for p in paths if p and (ROOT / p).is_file()}
        tools = {}
        for name in ('make', 'clang', 'ld', 'python3', 'git'):
            path = Path(shutil.which(name)).resolve()
            tools[name] = {'path': str(path), 'sha256': sha(path)}
        dump(evidence / 'identity.json', {'head': head, 'base': BASE, 'limits': bounded,
             'source_sha256': hashes, 'tools': tools,
             'assumptions': 'Linux x86-64 with ordinary system libc; trusted native reader; '
                            'pub in supplied runtime files is the explicit export root set; '
                            'included module pub is module visibility; no OS kernel operations; '
                            'sequential fragment only, no fixed points or web rebuilds; CPU times are noisy observations'})
        require(len(bounded['cpus']) <= 2 and bounded['address_space_bytes'] <= 2 * 1024**3,
                'resource bounds not enforced')
        if args.audit:
            dump(evidence / 'result.json', {'pass': True, 'head': head, 'audit_only': True})
            print('PASS ancestry, protected inputs, two-core/2-GiB limits and host assumptions')
            return 0
        versions = {}
        for variant, revision in (('before', BASE), ('after', head)):
            clone = scratch / variant
            replay.run(['git', 'clone', '--no-hardlinks', '--quiet', str(ROOT), str(clone)], variant + '-clone', ROOT)
            replay.run(['git', 'checkout', '--quiet', revision], variant + '-checkout', clone)
            replay.run(['make', 'init'], variant + '-init', clone)
            replay.run(['make', 'build'], variant + '-source-build', clone)
            compiler = str(clone / 'out/lang_next')
            ship = clone / 'example/shipping'
            minted = scratch / (variant + '-shipc')
            replay.run([compiler, 'compiler', 'shipping', str(ship / 'shipping.lang'),
                        '--runtime', str(ship / 'runtime.lang'), '-o', str(minted)], variant + '-mint', clone)
            ir = evidence / (variant + '-shipping.ll')
            replay.run([str(minted), str(ship / 'policy.shipping'), '-o', str(ir)], variant + '-guest-ir', scratch)
            versions[variant] = (clone, compiler, minted, ir)
        ir_lines = {v: len(data[3].read_text().splitlines()) for v, data in versions.items()}
        require(ir_lines['after'] < ir_lines['before'], 'unreachable runtime helpers did not shrink shipping IR')
        after_ir = versions['after'][3].read_text()
        require('@vec_new(' not in after_ir and '@map_new(' not in after_ir, 'unused std helpers survived')
        require('@shipping_total(' in after_ir and '@shipping_print(' in after_ir, 'emitted calls lost roots')
        print(f'IR lines: {ir_lines}', flush=True)
        samples = []
        runtime_inputs = [([], 64, b'', b'shipping:'), (['0'], 0, b'10\n', b''),
                          (['99'], 0, b'10\n', b''), (['100'], 0, b'0\n', b''),
                          (['120'], 0, b'0\n', b''), (['00080'], 0, b'10\n', b''),
                          (['1000000'], 0, b'0\n', b''), (['-1'], 64, b'', b'shipping:'),
                          (['1.5'], 64, b'', b'shipping:'), (['abc'], 64, b'', b'shipping:'),
                          (['1000001'], 64, b'', b'shipping:'), (['9999999999999999999999'], 64, b'', b'shipping:'),
                          ([''], 64, b'', b'shipping:'), (['0', '1'], 64, b'', b'shipping:')]
        observed = {}
        for opt in ('O0', 'O2'):
            for sample in range(5):
                # Alternate the first variant to avoid always favoring a warm cache.
                order = ('before', 'after') if sample % 2 == 0 else ('after', 'before')
                for variant in order:
                    exe = scratch / (variant + '-' + opt)
                    replay.run(['clang', '-' + opt, str(versions[variant][3]), '-o', str(exe)],
                               f'{opt}-{sample}-{variant}-clang', scratch)
                    row = replay.rows[-1]
                    samples.append({'optimization': opt, 'sample': sample, 'variant': variant,
                                    'clang_cpu_seconds': row['cpu_user_seconds'] + row['cpu_system_seconds'],
                                    'native_bytes': exe.stat().st_size, 'native_sha256': sha(exe),
                                    'stage': row['name']})
                    if sample == 0:
                        for index, (argv, exit_code, stdout, stderr) in enumerate(runtime_inputs):
                            result = replay.run([str(exe), *argv], f'{variant}-{opt}-runtime-{index}', scratch, exit_code)
                            require(result.stdout == stdout and (result.stderr.startswith(stderr) if stderr else not result.stderr),
                                    'shipping output mismatch')
                            observed[(variant, opt, index)] = (result.returncode, result.stdout, result.stderr)
            for index in range(len(runtime_inputs)):
                require(observed[('before', opt, index)] == observed[('after', opt, index)], 'runtime semantic regression')
        dump(evidence / 'measurements.json', {'ir_lines': ir_lines, 'samples': samples,
             'timing_note': 'Five alternating interleaved before/after pairs at O0 and O2; machine-local CPU observations, no speed target.'})
        clone, compiler, _, _ = versions['after']
        fixtures = clone / FIXTURES
        minted = scratch / 'fixturec'
        replay.run([compiler, 'compiler', 'core_ast', str(fixtures / 'reader.lang'),
                    '--runtime', str(fixtures / 'runtime.lang'), '-o', str(minted)], 'mint-root-fixture', clone)
        for name in ('roots', 'indirect', 'foreign'):
            ir = evidence / (name + '.ll')
            replay.run([str(minted), str(fixtures / (name + '.ast')), '-o', str(ir)], name + '-ir', scratch)
            text = ir.read_text()
            if name == 'roots':
                for root in ('external_export', 'second_export', 'exported_leaf', 'callback_value', 'initialized_callback', 'initialized_seed'):
                    require('@' + root in text, root + ' was incorrectly pruned')
                require('@dead_helper(' not in text and '@vec_new(' not in text, 'root fixture did not prune')
            else:
                require('@dead_helper(' in text and '@vec_new(' in text, name + ': unknown dependencies must retain whole runtime')
            for opt in ('O0', 'O2'):
                exe = scratch / (name + '-' + opt)
                c = [str(fixtures / (name + '.c'))] if name != 'indirect' else []
                replay.run(['clang', '-' + opt, str(ir), *c, '-o', str(exe)], name + '-' + opt + '-clang', scratch)
                result = replay.run([str(exe)], name + '-' + opt + '-run', scratch)
                require(not result.stdout and not result.stderr, name + ': external ABI or callback failed')
        # The shared --from-ast path must apply the same runtime boundary.
        direct_ir = evidence / 'from-ast.ll'
        replay.run([compiler, '--from-ast', str(fixtures / 'roots.ast'), '--runtime', str(fixtures / 'runtime.lang'),
                    '-o', str(direct_ir)], 'from-ast-ir', clone)
        require('@dead_helper(' not in direct_ir.read_text(), 'shared AST runtime did not prune')
        for opt in ('O0', 'O2'):
            exe = scratch / ('from-ast-' + opt)
            replay.run(['clang', '-' + opt, str(direct_ir), str(fixtures / 'roots.c'), '-o', str(exe)], 'from-ast-' + opt, scratch)
            replay.run([str(exe)], 'from-ast-' + opt + '-run', scratch)
        require(all(sha(ROOT / p) == h for p, h in hashes.items()), 'test edited committed input files')
        dump(evidence / 'result.json', {'pass': True, 'head': head, 'base': BASE, 'stages': len(replay.rows),
             'ir_lines': ir_lines, 'semantic_vectors': len(runtime_inputs), 'optimizations': ['O0', 'O2']})
        print('PASS shipping reachability: O0/O2 outputs, external exports, initializer/address-taken callback, indirect/foreign fallback and five interleaved samples')
        return 0
    except Exception as error:
        dump(evidence / 'result.json', {'pass': False, 'error': str(error)})
        print(f'FAIL: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
