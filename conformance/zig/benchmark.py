#!/usr/bin/env python3
"""Replay equal cold-cache oracle work and compare stable outcomes and throughput."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

from oracle import LOCK, digest, save

HERE = Path(__file__).resolve().parent


def stable(receipt):
    """Exclude only execution paths, emitted bytes and elapsed timings."""
    return {
        'identity': receipt['identity'], 'profile': receipt['profile'],
        'U': receipt['U'], 'U_recursive': receipt['U_recursive'],
        'candidate_status': receipt['candidate_status'],
        'upstream_passes_claimed': receipt['upstream_passes_claimed'],
        'modes': [{'mode': row['mode'],
                   'compile': (row['compile']['outcome'], row['compile']['returncode']),
                   'backend': (row['backend_proof']['outcome'], row['backend_proof']['returncode']),
                   'P': row.get('P'), 'outcomes': row.get('outcomes'),
                   'instances': [{k: v for k, v in item.items() if k != 'seconds'}
                                 for item in row['instances']]} for row in receipt['modes']],
        'negative_safety': [{'file': row['file'], 'file_sha256': row['file_sha256'],
                             'mode': row['mode'], 'category': row['category'],
                             'upstream_credit': row['upstream_credit'],
                             'expected_category_observed': row['expected_category_observed'],
                             'compile': (row['compile']['outcome'], row['compile']['returncode']),
                             'execution': (row['execution']['outcome'], row['execution']['returncode'])
                             if 'execution' in row else None}
                            for row in receipt['negative_safety']],
    }


def frozen(receipt, work):
    baseline = json.loads((HERE / 'baseline.json').read_text())
    assert receipt['U'] == baseline['U'] and receipt['U_recursive'] == baseline['U_recursive']
    assert receipt['candidate_status'] == 'not_implemented'
    assert receipt['upstream_passes_claimed'] is False
    assert digest(work / 'declarations.json') == baseline['declaration_index_sha256']
    for row in receipt['modes']:
        prior = baseline['modes'][row['mode']]
        assert len(row['instances']) == prior['discovered_instances']
        assert row['outcomes'] == prior['reference_outcomes'] and row['P'] == prior['P']
        assert digest(work / f"discovered-{row['mode']}.json") == prior['discovery_sha256']
        assert len({i['id'] for i in row['instances']}) == len(row['instances'])
    assert all(row['expected_category_observed'] and row['upstream_credit'] == 0
               for row in receipt['negative_safety'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'source-archive', 'compiler', 'compiler-archive', 'work'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--baseline-receipt', type=Path)
    p.add_argument('--baseline-work', type=Path)
    p.add_argument('--rounds', type=int, choices=range(1, 6), default=2)
    p.add_argument('--parallel-jobs', type=int, choices=(2, 3), default=2)
    p.add_argument('--cpus', type=int, default=4)
    args = p.parse_args()
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=False)
    report = {'profile': LOCK, 'runs': [], 'stable_equal': False, 'retain_parallel': False}
    canonical, canonical_coverage = None, None
    if args.baseline_receipt:
        if not args.baseline_work:
            p.error('--baseline-work is required with --baseline-receipt')
        baseline = json.loads(args.baseline_receipt.read_text())
        frozen(baseline, args.baseline_work)
        canonical = stable(baseline)
        canonical_coverage = digest(args.baseline_work / 'coverage.json')
        report['original_receipt'] = str(args.baseline_receipt.resolve())
    for round_index in range(args.rounds):
        order = (1, args.parallel_jobs) if round_index % 2 == 0 else (args.parallel_jobs, 1)
        for jobs in order:
            name = f'round-{round_index + 1}-jobs-{jobs}'
            folder, receipt_path = work / name, work / (name + '.json')
            command = [sys.executable, '-B', HERE / 'oracle.py', 'reference',
                       '--work', folder, '--receipt', receipt_path,
                       '--mode-jobs', jobs, '--cpus', args.cpus]
            for field in ('source', 'source_archive', 'compiler', 'compiler_archive'):
                command.extend(['--' + field.replace('_', '-'), getattr(args, field).resolve()])
            start = time.monotonic()
            with (work / (name + '.log')).open('wb') as log:
                subprocess.run(list(map(str, command)), stdout=log, stderr=log, check=True)
            seconds = time.monotonic() - start
            receipt = json.loads(receipt_path.read_text())
            frozen(receipt, folder)
            resources = receipt['resources']
            assert resources['error'] is None and resources['remaining_descendants'] == []
            assert resources['max_running_modes'] == jobs
            caches = []
            for mode in receipt['modes']:
                command = mode['compile']['command']
                cache = Path(command[command.index('--cache-dir') + 1])
                assert cache == folder / mode['mode'] / 'local-cache'
                caches.append(cache)
            assert len(set(caches)) == len(LOCK['modes'])
            outcomes = stable(receipt)
            if canonical is None:
                canonical = outcomes
            assert outcomes == canonical, f'stable outcome drift: {name}'
            # Coverage includes declaration IDs, unreached declarations and skips.
            coverage = digest(folder / 'coverage.json')
            if canonical_coverage is None:
                canonical_coverage = coverage
            assert coverage == canonical_coverage
            checks = sum(len(row['instances']) for row in receipt['modes'])
            report['runs'].append({'name': name, 'jobs': jobs, 'seconds': seconds,
                                   'completed_checks': checks, 'checks_per_hour': checks * 3600 / seconds,
                                   'peak_tree_rss_bytes': receipt['resources']['peak_tree_rss_bytes'],
                                   'resources': receipt['resources'], 'coverage_sha256': coverage,
                                   'receipt': str(receipt_path)})
            save(work / 'comparison.json', report)
            print(f'{name}: {seconds:.2f}s, {checks * 3600 / seconds:.0f} checks/hour', flush=True)
    rates = {}
    for jobs in (1, args.parallel_jobs):
        runs = [r for r in report['runs'] if r['jobs'] == jobs]
        rates[jobs] = sum(r['completed_checks'] for r in runs) * 3600 / sum(r['seconds'] for r in runs)
    paired_speedups = []
    for index in range(args.rounds):
        paired = {r['jobs']: r for r in report['runs'] if r['name'].startswith(f'round-{index + 1}-')}
        paired_speedups.append(paired[1]['seconds'] / paired[args.parallel_jobs]['seconds'])
    report['paired_speedups'] = paired_speedups
    report.update(stable_equal=True, serial_checks_per_hour=rates[1],
                  parallel_checks_per_hour=rates[args.parallel_jobs],
                  speedup=rates[args.parallel_jobs] / rates[1],
                  retain_parallel=rates[args.parallel_jobs] > rates[1] and all(s > 1 for s in paired_speedups))
    save(work / 'comparison.json', report)
    print(json.dumps({k: v for k, v in report.items() if k not in ('profile', 'runs')}, indent=2))


if __name__ == '__main__':
    main()
