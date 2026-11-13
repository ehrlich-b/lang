#!/usr/bin/env python3
"""Recompute the six Harbor audit rows from the frozen original byte streams.

This fragment never executes a recorded command or compiles a trial program.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re

MANIFEST_SHA256 = '0be69a0effd5dab92a1122471a382d0e32fe49b495ee298e36c3e370bef9702e'
CASES = ('setup-boundary', 'first-working-sample', 'failed-attempts',
         'handwritten-lines', 'native-dependencies', 'missing-timestamp')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text())


def verify_inputs(root):
    manifest = root / 'MANIFEST.json'
    assert sha(manifest.read_bytes()) == MANIFEST_SHA256, 'changed manifest'
    for row in load(manifest):
        path = root / row['path']
        assert path.is_file(), 'missing input: ' + row['path']
        assert sha(path.read_bytes()) == row['sha256'], 'changed input: ' + row['path']


def timestamp(record, key):
    assert key in record, 'missing timestamp: ' + key
    value = record[key]
    assert type(value) in (float, int) and math.isfinite(value), 'invalid timestamp: ' + key
    return value


def interval(start, start_key, end, end_key, divisor=1):
    elapsed = (timestamp(end, end_key) - timestamp(start, start_key)) / divisor
    assert elapsed >= 0, 'contradictory timestamp order'
    return elapsed


def command(record):
    return record.get('argv', record.get('command', record.get('operation')))


def sample(record):
    cmd = command(record)
    if isinstance(cmd, list):
        return Path(cmd[-1]).name == 'sample.conf' and any('harbor-config' in x for x in cmd)
    return bool(cmd and re.search(r'harbor-config\s+\S*sample\.conf\s*$', cmd))


def working(record):
    assert record['exit'] == 0 and record['stdout'] and not record['stderr'], 'false sample success'
    for word in ('service', 'workers', 'integer', 'network', '8080', 'false'):
        assert word in record['stdout'], 'incomplete sample output: ' + word


def bison_events(root):
    # Combined log retains excluded attempts first. Accepted author events begin
    # at their own structured first_command marker; no clock is restarted here.
    lines = (root / 'bison/trial.log').read_text().splitlines()
    events = []
    for number, line in enumerate(lines, 1):
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if not isinstance(row, dict):
            continue
        if row.get('event') == 'first_command':
            events = []
        if row.get('event') and (events or row['event'] == 'first_command'):
            row['_source_line'] = number
            events.append(row)
    assert events and events[0]['event'] == 'first_command'
    return events


def antlr_events(root):
    return [dict(json.loads(s), _source_line=i) for i, s in
            enumerate((root / 'antlr/commands.jsonl').read_text().splitlines(), 1)]


def trial1_events(root):
    text = (root / 'trial1/trial.log').read_text()
    pattern = r'^\[([^\]]+)\] \$ ([^\n]+)\n(.*?)\nexit=(\d+)\n'
    # The old logger merged stdout/stderr. Preserve that fact; never invent a split.
    return [dict(command=m[2], start_utc=m[1], exit=int(m[4]),
                 combined_output=m[3], source_offset=m.start())
            for m in re.finditer(pattern, text, re.M | re.S)]


def derive(root):
    b = bison_events(root)
    a = antlr_events(root)
    bc = [r for r in b if 'exit' in r and command(r)]
    bs = next(r for r in bc if sample(r) and r['exit'] == 0)
    ast = next(r for r in a if sample(r) and r['exit'] == 0)
    working(bs)
    working(ast)
    btime = interval(b[0]['timing'], 'monotonic_ns', bs, 'monotonic_ns', 1e9)
    atime = interval(a[0], 'start_epoch', ast, 'end_epoch')
    marker = load(root / 'antlr/first-passing-sample.json')
    assert timestamp(marker, 'epoch') == timestamp(ast, 'end_epoch'), 'contradictory first-pass marker'
    summary = load(root / 'antlr/trial-results.json')
    assert abs(atime - interval(summary, 'trial_start_monotonic', summary,
                               'first_passing_sample_monotonic')) < .001, 'contradictory clocks'
    assert abs(btime - load(root / 'bison/trial-results.json')['timing']['seconds_to_first_passing_sample']) < 1e-9
    t = trial1_events(root)
    ts = next(r for r in t if sample(r) and r['exit'] == 0)
    assert '8080' in ts['combined_output'] and 'workers' in ts['combined_output']
    lang = load(root / 'lang/commands.json')
    ls = next(r for r in lang if sample(r) and r['exit'] == 0)
    working(ls)

    # Setup receipt survives inside the excluded Bison attempt's captured stdout.
    text = (root / 'bison/trial.log').read_text()
    setup, _ = json.JSONDecoder().raw_decode(text[text.index('{\n  "started_at"'):])
    setup_seconds = setup['wall_seconds']
    assert setup_seconds > 0
    boundary = {
        'trial1': dict(setup_seconds=None, reason='Archive extraction logged with start only; author start/end absent.'),
        'lang': dict(setup_seconds=None, reason='Provisioning logs not in frozen packet; consumer replay has durations only.'),
        'bison': dict(setup_seconds=setup_seconds, source='bison/trial.log: captured setup-results.json stdout',
                      reason='Package provisioning precedes both author attempts; excluded attempt remains retained.'),
        'antlr': dict(setup_seconds=None, reason='Boundary names setup-results.json, but receipt bytes are absent.')}
    first = {
        'trial1': dict(source='trial1/trial.log', author_seconds=None, event=ts, reason='First observed sample command start, no completion timestamp or author start.'),
        'lang': dict(source='lang/commands.json', author_seconds=None, event=ls, reason='Final scripted consumer replay; no fresh-author clock in retained logs.'),
        'bison': dict(source='bison/trial.log', author_seconds=btime, event=bs, start=b[0]['timing'], reason='Accepted independent author, procedural documentation boundary; initial excluded attempt is separate.'),
        'antlr': dict(source='antlr/commands.jsonl', author_seconds=atime, event=ast, start_epoch=a[0]['start_epoch'], reason='Fresh agent procedural context isolation, not a blinded human study.')}
    failed = {}
    for label, events, first_event in [('trial1', t, ts), ('lang', lang, ls), ('bison', bc, bs), ('antlr', a, ast)]:
        index = events.index(first_event)
        failures = [r for r in events if r['exit'] != 0 and 'fixtures/' not in str(command(r))]
        failed[label] = dict(before_first_sample=sum(r['exit'] != 0 and 'fixtures/' not in str(command(r)) for r in events[:index]),
                             observed_unexpected_failures=len(failures), events=failures)
    failed['lang']['coverage'] = 'Final replay only: 0 observed; FRICTION separately reports 2 isolation failures and 1 generated-name compile failure; raw failed runs absent.'
    failed['trial1']['coverage'] = 'Three cascading failures after the first working sample; not three independent fixes.'
    failed['bison']['coverage'] = 'Accepted attempt only: two failed build commands, not four C diagnostics; initial disqualified attempt excluded.'
    failed['antlr']['coverage'] = 'Zero failing author commands; eight invalid fixtures are successful negative tests.'

    # Physical lines include blank and comment lines, not generated files or inputs.
    files = {'trial1': ['harbor.lang'], 'lang': ['harbor.lang'],
             'bison': ['harbor.h', 'harbor.y', 'harbor.l', 'harbor.c'],
             'antlr': ['Harbor.g4', 'main.cpp']}
    lines = {}
    for arm, names in files.items():
        counts = {n: len((root / arm / n).read_bytes().splitlines()) for n in names}
        lines[arm] = dict(language_files=counts, language_total=sum(counts.values()))
    authored = {r['file']: r['content'] for r in b if r['event'] == 'write' and 'content' in r}
    btools = ['build.sh', 'replay.py', 'reproduce.py', 'reproduce.sh']
    lines['bison']['historical_support_files'] = {n: len(authored[n].splitlines()) for n in btools}
    lines['bison']['historical_total'] = lines['bison']['language_total'] + sum(lines['bison']['historical_support_files'].values())
    lines['bison']['qualification'] = 'Original support bytes recovered from write events; current build.sh is a later replay wrapper, counted separately.'
    for arm in files:
        names = [n for n in ('build.sh', 'reproduce.sh', 'check-trial.py', 'run-trial.py') if (root / arm / n).is_file()]
        lines[arm]['retained_support_files'] = {n: len((root / arm / n).read_bytes().splitlines()) for n in names}
    lines['antlr']['qualification'] = 'Reported verify.py/run.py counts excluded: standalone source files absent; no generated HarborLexer/Parser files counted.'

    deps = {
        'trial1': dict(build=['versioned Lang SDK e5b90e2f0538', 'Clang', 'system C toolchain'], runtime=['native executable', 'system C runtime'], source=['trial1/reproduce.sh', 'trial1/trial.log']),
        'lang': dict(build=['Lang SDK e148de1', 'Clang', 'system C toolchain'], runtime=['native executable', 'system C runtime'], source=['lang/commands.json', 'lang/run-trial.py']),
        'bison': dict(build=['flex 2.6.4', 'Bison 3.8.2', 'm4 1.4.19', 'Clang 19.1.7', 'system C toolchain'], runtime=['native executable', 'system C runtime; no libfl (noyywrap)'], source=['bison/trial.log: accepted version/build commands and authored build.sh']),
        'antlr': dict(build=['ANTLR 4.13.2 jar', 'Java 21 (boundary claim)', 'ANTLR C++ runtime 4.13.2', 'Clang++', 'C++17 toolchain'], runtime=['native executable', 'statically linked ANTLR C++ runtime', 'system C/C++ runtime and pthread support'], source=['antlr/build.sh', 'antlr/trial-boundary.md'])}
    compiler = {
        'trial1': dict(build_seconds=None, runtime_seconds=None, reason='Start-only timestamps do not define durations.'),
        'lang': dict(frontend_seconds=lang[0]['seconds'], native_link_seconds=lang[1]['seconds'], sample_runtime_seconds=ls['seconds'], kind='scripted consumer replay, not authoring'),
        'bison': dict(build_attempt_seconds=[interval(r, 'start_monotonic_ns', r, 'monotonic_ns', 1e9) for r in bc if './build.sh' in str(command(r)) and bc.index(r) < bc.index(bs)], sample_runtime_seconds=interval(bs,'start_monotonic_ns',bs,'monotonic_ns',1e9), kind='build includes parser generation and native link; no per-tool split'),
        'antlr': dict(build_seconds=interval(a[5], 'start_epoch', a[5], 'end_epoch'), sample_runtime_seconds=interval(ast,'start_epoch',ast,'end_epoch'), kind='build includes generation and native link; not provisioning')}
    return dict(version=1, rows={'setup-boundary': boundary, 'first-working-sample': first,
                                'failed-attempts': failed, 'handwritten-lines': lines,
                                'native-dependencies': deps,
                                'missing-timestamp': dict(policy='Reject a required timestamp; absent historical phases stay null, never zero.')},
                compiler_and_runtime=compiler,
                definitions=dict(failed_attempt='One nonzero command excluding expected negative fixture probes; diagnostics and nested wrapper/child executions are not independent author attempts.',
                                 lines='Physical lines including blanks/comments; language source, support scripts, dependencies and generated code are separate.',
                                 clocks='Author intervals require explicit start and first successful sample completion; never infer end from next command.',
                                 replay='Only re-evaluate frozen bytes; no new author trial, build, runtime or scale measurement.'))


def check_case(name, metrics, root):
    rows = metrics['rows']
    assert set(rows) == set(CASES)
    if name == 'setup-boundary':
        assert rows[name]['lang']['setup_seconds'] is None
        assert rows[name]['bison']['setup_seconds'] > 0
    elif name == 'first-working-sample':
        r = rows[name]
        assert r['lang']['author_seconds'] is None and r['trial1']['author_seconds'] is None
        assert 174 < r['bison']['author_seconds'] < 175
        assert 170 < r['antlr']['author_seconds'] < 171
    elif name == 'failed-attempts':
        assert [rows[name][a]['observed_unexpected_failures'] for a in ('trial1', 'lang', 'bison', 'antlr')] == [3, 0, 2, 0]
    elif name == 'handwritten-lines':
        assert rows[name]['bison']['language_total'] == 230
        assert rows[name]['bison']['historical_total'] == 368
        assert rows[name]['antlr']['language_total'] == 134
    elif name == 'native-dependencies':
        for row in rows[name].values():
            assert row['build'] and row['runtime'] and row['source']
        assert '-pthread' in (root / 'antlr/build.sh').read_text()
    elif name == 'missing-timestamp':
        mutant = copy.deepcopy(antlr_events(root))
        first = next(r for r in mutant if sample(r) and r['exit'] == 0)
        del first['end_epoch']
        try:
            interval(mutant[0], 'start_epoch', first, 'end_epoch')
        except AssertionError as exc:
            assert str(exc) == 'missing timestamp: end_epoch'
        else:
            raise AssertionError('missing timestamp accepted as zero')


def render(metrics):
    rows = metrics['rows']
    out = ['# Harbor metric audit', '',
           'Frozen historical observations only. Unmeasured means the retained bytes do not establish an interval; it never means zero.', '',
           '| Measure | Lang trial 1 | Lang trial 2 | flex/Bison accepted | ANTLR C++ |',
           '|---|---|---|---|---|']
    arms = ('trial1', 'lang', 'bison', 'antlr')
    def fmt(v):
        return 'unmeasured' if v is None else f'{v:.6f} s'
    out += ['| Setup | ' + ' | '.join(fmt(rows['setup-boundary'][a]['setup_seconds']) for a in arms) + ' |',
            '| Author start to first sample | ' + ' | '.join(fmt(rows['first-working-sample'][a]['author_seconds']) for a in arms) + ' |',
            '| Observed failed commands (before first sample) | ' + ' | '.join(f"{rows['failed-attempts'][a]['observed_unexpected_failures']} ({rows['failed-attempts'][a]['before_first_sample']})" for a in arms) + ' |',
            '| Retained handwritten language lines | ' + ' | '.join(str(rows['handwritten-lines'][a]['language_total']) for a in arms) + ' |', '',
            'The six recomputed ledger rows are setup-boundary, first-working-sample, failed-attempts, handwritten-lines, native-dependencies and missing-timestamp. Per-file counts, raw event references, compiler/runtime durations and dependency lists are in metrics.json.', '',
            'Trial 1 has start-only command timestamps, so its first working sample is identified without a duration. Trial 2 retains a scripted final consumer run, with frontend 0.815359 s and link 3.815668 s; those durations cannot be relabeled fresh authoring. Its friction reports three earlier failures whose raw failed runs are absent.', '',
            'Bison setup is a captured package-provisioning receipt shared by the attempts. Its initial documentation-boundary violation is retained and excluded; the accepted author clock is independent. ANTLR setup is described but its receipt is absent. Bison and ANTLR author intervals include thinking and builds; they are fresh-agent procedural trials, not blinded human studies.', '',
            'Expected rejection of each of eight malformed fixtures is successful validation, excluded from failed attempts. Trial 1 has three cascading failures after first sample. Bison has two failed build invocations; multiple C diagnostics in one build count once. Generated files, installed library/compiler sources, supplied fixtures and input documents are excluded from handwritten language lines. Support/replay scripts are separate; missing historical script bytes are qualified.', '',
            'Dependencies:', '']
    for arm in arms:
        d = rows['native-dependencies'][arm]
        out.append(f"- {arm}: build — {', '.join(d['build'])}; runtime — {', '.join(d['runtime'])}.")
    out += ['', 'Required timestamp removal fails explicitly. Unknown historical setup, authoring and compiler phases remain null. No new timed author trial, scale benchmark or compiler suite was run by this fragment.', '']
    return '\n'.join(out)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inputs', type=Path, required=True)
    p.add_argument('--case', choices=CASES, required=True)
    p.add_argument('--output', type=Path)
    p.add_argument('--verify-ledger', type=Path)
    p.add_argument('--timestamp-source', type=Path)
    args = p.parse_args()
    verify_inputs(args.inputs)
    metrics = derive(args.inputs)
    check_case(args.case, metrics, args.inputs)
    document = (Path(__file__).resolve().parents[2] / 'docs/compare-yacc-antlr.md').read_text()
    first = metrics['rows']['first-working-sample']
    expected_row = ('| Author start to first working sample | unmeasured | unmeasured | '
                    f"{first['bison']['author_seconds']:.6f} s | {first['antlr']['author_seconds']:.6f} s |")
    assert expected_row in document, 'public authoring table differs from audit'
    counts = metrics['rows']['handwritten-lines']
    expected_lines = '| Retained handwritten language lines | ' + ' | '.join(
        str(counts[a]['language_total']) for a in ('trial1', 'lang', 'bison', 'antlr')) + ' |'
    assert expected_lines in document, 'public line counts differ from audit'
    if args.verify_ledger:
        assert load(args.verify_ledger) == metrics, 'ledger differs from recomputed source bytes'
    if args.timestamp_source:
        assert args.case == 'missing-timestamp'
        events = [json.loads(s) for s in args.timestamp_source.read_text().splitlines()]
        event = next(r for r in events if sample(r) and r['exit'] == 0)
        interval(events[0], 'start_epoch', event, 'end_epoch')
    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / 'metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
        (args.output / 'METRICS.md').write_text(render(metrics))
    print('PASS:', args.case, 'recomputed from frozen source bytes')


if __name__ == '__main__':
    main()
