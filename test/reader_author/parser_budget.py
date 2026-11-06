#!/usr/bin/env python3
"""Replay bounded recognition and small reader overhead from committed inputs."""
import argparse
import os
from pathlib import Path
import re
import resource
import shutil
import statistics
import sys
import uuid

from route import Replay, ROOT, dump, require, sha

BASE = '03ee80d3dfef74170bb2e0e600d1c36306ae8c89'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['bounded'], required=True)
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    os.nice(10)
    cpus = sorted(os.sched_getaffinity(0))[:2]
    os.sched_setaffinity(0, cpus)
    ceiling = min(2 * 1024**3, resource.getrlimit(resource.RLIMIT_AS)[1])
    if ceiling < 0:
        ceiling = 2 * 1024**3
    resource.setrlimit(resource.RLIMIT_AS, (ceiling, ceiling))
    token = uuid.uuid4().hex
    evidence = (args.evidence or ROOT.parent / 'evidence' / ('bounded-' + token)).resolve()
    require(evidence != ROOT and ROOT not in evidence.parents, 'evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=False)
    scratch = ROOT.parent / 'scratch' / ('bounded-' + token)
    scratch.mkdir(parents=True)
    replay = Replay(evidence, scratch)
    replay.env.update(MAKEFLAGS='-j2', PYTHONDONTWRITEBYTECODE='1')
    # Ambient quotas must not alter test expectations; projects also override them.
    for key in ('LANG_PARSER_MAX_WORK', 'LANG_PARSER_MAX_DEPTH', 'LANG_PARSER_SOURCE'):
        replay.env.pop(key, None)
    print(f'evidence: {evidence}', flush=True)
    try:
        status = replay.run(['git', 'status', '--porcelain', '--untracked-files=all'], 'clean', ROOT)
        require(not status.stdout, 'commit the candidate before replaying it')
        replay.run(['git', 'merge-base', '--is-ancestor', BASE, 'HEAD'], 'required-base', ROOT)
        head = replay.run(['git', 'rev-parse', 'HEAD'], 'head', ROOT).stdout.decode().strip()
        clone = scratch / 'repo'
        replay.run(['git', 'clone', '--no-hardlinks', '--quiet', str(ROOT), str(clone)], 'clone', ROOT)
        files = replay.run(['git', 'ls-files', '-z'], 'inputs', clone).stdout.decode().split('\0')
        dump(evidence / 'identity.json', {
            'head': head, 'base': BASE,
            'source_sha256': {p: sha(clone / p) for p in files if p and (clone / p).is_file()},
            'tools': {name: {'path': str(Path(shutil.which(name)).resolve()),
                             'sha256': sha(Path(shutil.which(name)).resolve())}
                      for name in ('make', 'clang', 'ld', 'python3', 'git')},
            'limits': {'cpus': cpus, 'address_space_bytes': ceiling, 'JOBS': 2, 'MAKEFLAGS': '-j2'},
            'assumptions': 'Linux x86-64 libc; trusted native readers; no OS kernel operations; '
                           'only bounded fragment, no full suites or fixed points; byte offsets; '
                           'timings are local measurements, unrestricted backtracking is not linear'})
        replay.run(['make', 'init'], 'init', clone)
        replay.run(['make', 'build'], 'build-current-sources', clone)
        compiler = str(clone / 'out/lang_next')
        fixture = 'test/reader_author/fixtures/budget'
        for name in ('recognition', 'overhead'):
            ir = scratch / (name + '.ll')
            replay.run([compiler, 'std/core.lang', f'{fixture}/{name}.lang', '-o', str(ir)], name + '-ir', clone)
            replay.run(['clang', '-O2', str(ir), '-o', str(scratch / name)], name + '-link', clone)
        measurements = []
        def recognize(grammar, path, work, depth, enabled=1, repeat=1, expected=0, name='recognize'):
            return replay.run([str(scratch / 'recognition'), grammar, str(path), str(work), str(depth),
                               str(enabled), str(repeat)], name, clone, expected=expected)
        for grammar, sizes in [('ambiguous', (4, 6, 8)), ('chain', (8, 16, 32))]:
            for n in sizes:
                text = '(' * n + '1' + ']' * n if grammar == 'ambiguous' else ' '.join(['1'] * n)
                path = evidence / f'{grammar}-{n}.input'
                path.write_text(text)
                good = recognize(grammar, path, 1000000, 128, name=f'{grammar}-{n}-success')
                work, peak, end = map(int, good.stdout.split())
                require(work > 0 and peak >= n and end == len(text) and good.stderr, 'bad counters or parse')
                again = recognize(grammar, path, 1000000, 128, repeat=2, name=f'{grammar}-{n}-reset')
                require(again.stdout == good.stdout and again.stderr == good.stderr, 'invocation counters did not reset')
                off = recognize(grammar, path, 1000000, 128, enabled=0, name=f'{grammar}-{n}-disabled')
                require(off.stdout == f'0 0 {len(text)}\n'.encode() and off.stderr == good.stderr, 'disabled parse semantics changed')
                for kind, quota, dep in [('work', work - 1, 128), ('depth', 1000000, 4)]:
                    outputs = []
                    for attempt in range(2):
                        failed = recognize(grammar, path, quota, dep, expected=1,
                                           name=f'{grammar}-{n}-{kind}-{attempt}')
                        require(not failed.stdout and f'parser-{kind}-budget'.encode() in failed.stderr,
                                'budget did not stop normally')
                        require(re.search(rb'parser rule ' + grammar.encode() + rb' grammar @\d+ source ' +
                                          re.escape(str(path).encode()) + rb' @(\d+)\n', failed.stderr),
                                'missing responsible grammar rule/source byte offset')
                        if kind == 'depth':
                            offset = 4 if grammar == 'ambiguous' else 8
                            require(f' @{offset}\n'.encode() in failed.stderr, 'wrong depth source offset')
                        outputs.append(failed.stderr)
                    require(outputs[0] == outputs[1], 'breach is nondeterministic')
                exact = recognize(grammar, path, work, peak, name=f'{grammar}-{n}-exact-limits')
                require(exact.stdout == good.stdout, 'inclusive budget boundary changed success')
                measurements.append({'grammar': grammar, 'size': n, 'bytes': len(text), 'work': work, 'peak_depth': peak})
        # Count repeated inline terminals too, even when no rule reference occurs.
        path = evidence / 'flat.input'
        path.write_text('1 ' * 32)
        recognize('flat', path, 8, 128, expected=1, name='flat-terminal-budget')
        ordered = evidence / 'ordered.input'
        ordered.write_text('1')
        for enabled in (0, 1):
            recognize('ordered', ordered, 1000, 128, enabled=enabled, name='ordered-first-alternative')
        malformed = evidence / 'malformed.input'
        malformed.write_text(']')
        result = recognize('chain', malformed, 1000, 128, expected=1, name='ordinary-failure')
        require(b'parser-' not in result.stderr and b'expected number' in result.stderr,
                'ordinary failure became a budget error')
        # Real manifest execution, cached worker reuse and minted compiler quotas.
        manifest = str(clone / fixture / 'project.lang-project')
        replay.env.update(LANG_PARSER_MAX_WORK='1000000', LANG_PARSER_MAX_DEPTH='256')
        for i in range(2):
            result = replay.run([compiler, 'project', 'read', manifest], f'project-budget-{i}', clone, expected=1)
            require(b'parser-depth-budget' in result.stderr and b'parser rule chain' in result.stderr and
                    b'input.budget @8' in result.stderr, 'manifest limit or source did not reach cached reader')
        work_manifest = scratch / 'work.lang-project'
        work_manifest.write_text(Path(manifest).read_text().replace('parser_work 1000', 'parser_work 3')
                                 .replace('parser_depth 4', 'parser_depth 128')
                                 .replace('"budget.lang"', '"' + str(clone / fixture / 'budget.lang') + '"')
                                 .replace('"input.budget"', '"' + str(clone / fixture / 'input.budget') + '"'))
        shutil.copyfile(work_manifest, evidence / work_manifest.name)
        result = replay.run([compiler, 'project', 'read', str(work_manifest)], 'project-work-budget', clone, expected=1)
        require(b'parser-work-budget' in result.stderr and b'parser rule chain' in result.stderr,
                'project work limit did not reach reader')
        minted = scratch / 'budgetc'
        replay.run([compiler, 'project', 'compiler', manifest, '-o', str(minted)], 'mint-budget-compiler', clone)
        result = replay.run([str(minted), str(clone / fixture / 'input.budget'), '-o', str(scratch / 'bad.ll')],
                            'minted-budget', clone, expected=1)
        require(b'parser-depth-budget' in result.stderr and b'input.budget @8' in result.stderr,
                'minted compiler lost project limits')
        # Validate located manifest failures for zero, overflow, and unsafe depth.
        for field, value in [('parser_work', '0'), ('parser_work', '999999999999999999999'), ('parser_depth', '257')]:
            project = scratch / f'invalid-{field}-{value}.lang-project'
            project.write_text(Path(manifest).read_text().replace(f'{field} ' + ('1000' if field == 'parser_work' else '4'), f'{field} {value}'))
            shutil.copyfile(project, evidence / project.name)
            result = replay.run([compiler, 'project', 'check', str(project)], 'invalid-limit', clone, expected=1)
            require(b'invalid parser limit' in result.stderr and re.search(rb':\d+:\d+: error:', result.stderr),
                    'invalid project quota was not located')
        shipping_manifest = clone / 'example/shipping/project.lang-project'
        project_ast = replay.run([compiler, 'project', 'read', str(shipping_manifest)], 'shipping-project-success', clone)
        legacy_ast = replay.run([compiler, 'read', 'example/shipping/shipping.lang', 'example/shipping/policy.shipping'],
                                'shipping-legacy-success', clone)
        require(project_ast.stdout == legacy_ast.stdout and not project_ast.stderr and not legacy_ast.stderr,
                'project quotas changed successful shipping AST')
        small = evidence / 'small.budget'
        small.write_text('1')
        replay.run([str(minted), str(small), '-o', str(scratch / 'small.ll')], 'minted-under-budget', clone)
        require((scratch / 'small.ll').is_file() and not (scratch / 'bad.ll').exists(),
                'minted compiler failed success or emitted an over-budget artifact')
        overhead = {}
        for reader in ('tiny', 'shipping'):
            outputs, times = {}, {'off': [], 'on': []}
            # Alternating order, five samples per mode; each process runs 10000 reads.
            for sample in range(5):
                for mode in (('off', 'on') if sample % 2 == 0 else ('on', 'off')):
                    result = replay.run([str(scratch / 'overhead'), reader, mode], f'overhead-{reader}-{mode}-{sample}', clone)
                    require(not result.stderr and result.stdout, 'overhead reader failed')
                    outputs[mode] = result.stdout
                    times[mode].append(replay.rows[-1]['wall_seconds'])
            require(outputs['off'] == outputs['on'], 'instrumentation changed reader AST')
            medians = {mode: statistics.median(values) for mode, values in times.items()}
            overhead[reader] = {'reads_per_process': 10000, 'wall_seconds': times, 'median_seconds': medians,
                                'enabled_over_disabled': medians['on'] / medians['off'],
                                'note': 'tiny is handwritten: a control with no generated recognition calls' if reader == 'tiny'
                                        else 'shipping uses generated recognition counters; process and AST costs included'}
        dump(evidence / 'measurements.json', {'bounded': measurements, 'overhead': overhead,
                                              'complexity': 'No linear complexity claim for unrestricted backtracking.'})
        dump(evidence / 'artifacts.json', {p.name: sha(p) for p in (Path(compiler), scratch / 'recognition', scratch / 'overhead', minted)})
        dump(evidence / 'result.json', {'pass': True, 'head': head, 'observations': len(replay.rows)})
        print('PASS bounded: work/depth, deterministic located breaches, reset, exact limits, project/minted propagation and reader overhead')
        return 0
    except Exception as error:
        dump(evidence / 'result.json', {'pass': False, 'error': str(error)})
        print(f'FAIL: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
