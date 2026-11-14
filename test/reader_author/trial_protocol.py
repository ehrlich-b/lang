#!/usr/bin/env python3
"""Validate the frozen author protocol and recorder on one automated shipping replay."""
import argparse
import copy
import json
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import subprocess
import sys
import time
import uuid

from route import Replay, ROOT, dump, require, sha
from trial_recorder import Recorder, summarize

BASE = 'b3a93cd'
FIXTURES = ROOT / 'test/reader_author/fixtures/trial_protocol'


def contract():
    frozen = json.loads((FIXTURES / 'freeze.v2.json').read_text())
    for name, digest in frozen['sha256'].items():
        require(sha(ROOT / name) == digest, 'frozen input changed: ' + name)
    tasks = json.loads((FIXTURES / 'tasks.v2.json').read_text())
    oracles = json.loads((FIXTURES / 'heldout/oracles.v2.json').read_text())
    require(frozen['version'] == tasks['version'] == oracles['version'] == 2, 'protocol version mismatch')
    validate_diagnostics(tasks, oracles)
    require(tasks['tools'] == ['lang', 'Bison', 'ANTLR', 'Ohm', 'tree-sitter'], 'comparison tools changed')
    require([t['action'] for t in tasks['tasks']] ==
            ['create', 'add syntax', 'change semantics', 'repair an error', 'export a native compiler'],
            'five task coverage changed')
    require([t['id'] for t in tasks['tasks']] == list(oracles['tasks']), 'task/oracle IDs differ')
    for task in tasks['tasks']:
        oracle = oracles['tasks'][task['id']]
        require(oracle['cases'] or oracle['inherits'], 'empty oracle: ' + task['id'])
        require(task['training'] and task['time_limit_minutes'] == 15, 'missing training or unequal limit')
        for inherited in oracle['inherits']:
            require(inherited in oracles['tasks'], 'missing inherited oracle')
    bar = tasks['future_bar']
    require((bar['participants'], bar['unfamiliar_finishers_required'], bar['max_elapsed_minutes'],
             bar['max_authored_lines'], bar['max_compiler_core_edits'], bar['status']) ==
            (5, 4, 15, 100, 0, 'not measured'), 'future human bar changed')
    return tasks, oracles


def validate_diagnostics(tasks, oracles):
    published = set(tasks['contract']['compile_diagnostics'].values())
    cases = oracles['common_rejections'] + [case for task in oracles['tasks'].values()
                                           for case in task['cases'] if case['compile_exit'] != 0]
    cases += [case for case in oracles['replay'].values() if case.get('located')]
    for case in cases:
        require(case['stderr_contains'] in published, 'unpublished diagnostic: ' + case['stderr_contains'])


def diagnostic_checks(evidence, tasks, oracles):
    bad = copy.deepcopy(oracles)
    bad['common_rejections'][0]['stderr_contains'] = 'unpublished wording'
    try:
        validate_diagnostics(tasks, bad)
    except RuntimeError as error:
        require(str(error) == 'unpublished diagnostic: unpublished wording', 'wrong diagnostic check failure')
    else:
        raise RuntimeError('contract accepted an unpublished diagnostic')
    dump(evidence / 'diagnostic-checks.json', dict(published=tasks['contract']['compile_diagnostics'],
                                                 unpublished_diagnostic_rejected=True))


def recorder_checks(evidence):
    fixture = json.loads((FIXTURES / 'recorder.v1.json').read_text())
    report = summarize(fixture['events'])
    for key, expected in fixture['expected'].items():
        require(report[key] == expected, 'recorder accounting mismatch: ' + key)
    rejected = []
    for name in ('clock-regression', 'after-finish', 'unfinished', 'missing-experience', 'unknown-event'):
        bad = copy.deepcopy(fixture['events'])
        if name == 'clock-regression':
            bad[2]['t_ns'] = -1
        elif name == 'after-finish':
            bad.append(dict(seq=len(bad), t_ns=bad[-1]['t_ns'], type='doc', data={}))
        elif name == 'unfinished':
            bad.pop()
        elif name == 'missing-experience':
            bad[0]['data']['kind'] = 'human'
            bad[0]['data']['prior_experience']['tool_hours'] = None
        else:
            bad[2]['type'] = 'invented'
        try:
            summarize(bad)
        except (ValueError, KeyError):
            rejected.append(name)
        else:
            raise RuntimeError('recorder accepted invalid events: ' + name)
    dump(evidence / 'recorder-checks.json', dict(synthetic=True, report=report, rejected=rejected))


def inside(folder, name):
    path = (folder / name).resolve()
    require(folder in path.parents, 'receipt path escapes evidence')
    return path


def verify_receipt(path):
    """Recompute every expectation from raw command receipts, ignoring success claims."""
    _, oracles = contract()
    path = path.resolve()
    receipt = json.loads(path.read_text())
    folder = path.parent
    require(receipt['version'] == 2 and receipt['kind'] == 'automated', 'unlabeled replay')
    identity_path = inside(folder, receipt['identity']['path'])
    require(sha(identity_path) == receipt['identity']['sha256'], 'identity hash mismatch')
    identity = json.loads(identity_path.read_text())
    require(identity['head'] == receipt['head'], 'receipt head mismatch')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    require(receipt['head'] == head, 'receipt is not for the current committed HEAD')
    for name, digest in identity['source_sha256'].items():
        require(sha(ROOT / name) == digest, 'source hash mismatch: ' + name)
    require(set(receipt['observations']) == set(oracles['replay']), 'missing or extra success observations')
    for name, expected in oracles['replay'].items():
        reference = receipt['observations'][name]
        raw = inside(folder, reference['path'])
        require(sha(raw) == reference['sha256'], name + ': raw receipt hash mismatch')
        row = json.loads(raw.read_text())
        bindings = dict(exported=identity['replay_directory'], fixtures=str(FIXTURES))
        command = [argument.format(**bindings) for argument in expected['command']]
        require(row['command'] == command, name + ': command mismatch')
        require(row['name'] == name, name + ': observation name mismatch')
        require(row['cwd'] == identity['replay_directory'], name + ': working directory mismatch')
        stdout, stderr = (inside(folder, row[stream]).read_bytes() for stream in ('stdout', 'stderr'))
        require(sha(inside(folder, row['stdout'])) == row['stdout_sha256'] and
                sha(inside(folder, row['stderr'])) == row['stderr_sha256'], name + ': output hash mismatch')
        require(row['exit'] == expected['exit'], name + ': exit mismatch')
        require(stdout == expected['stdout'].encode(), name + ': stdout mismatch')
        if 'stderr' in expected:
            require(stderr == expected['stderr'].encode(), name + ': stderr mismatch')
        if 'stderr_contains' in expected:
            require(expected['stderr_contains'].encode() in stderr, name + ': diagnostic mismatch')
        if expected.get('located'):
            require(re.search(rb'shipping:[1-9][0-9]*:[1-9][0-9]*:', stderr), name + ': missing source location')
    return dict(pass_=True, observations=len(oracles['replay']), head=receipt['head'])


class TrialReplay(Replay):
    def __init__(self, evidence, scratch, recorder):
        super().__init__(evidence, scratch)
        self.recorder = recorder

    def run(self, command, name, cwd, expected=0):
        self.recorder.emit('state', mode='waiting', activity='build')
        prefix = self.evidence / f'{len(self.rows) + 1:03d}-{name}'
        stdout_path, stderr_path = prefix.with_suffix('.stdout'), prefix.with_suffix('.stderr')
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        start = time.monotonic()
        peak_rss, failure = 0, None
        try:
            with stdout_path.open('wb') as stdout, stderr_path.open('wb') as stderr:
                try:
                    process = subprocess.Popen(command, cwd=cwd, env=self.env, stdout=stdout, stderr=stderr,
                                               start_new_session=True)
                except OSError as error:
                    stderr.write(str(error).encode())
                    code = 127
                else:
                    while process.poll() is None:
                        peak_rss = max(peak_rss, process_tree_rss(os.getpid()))
                        if peak_rss > 2 * 1024**3:
                            failure = 'aggregate RSS exceeded 2 GiB'
                        if time.monotonic() - start > 240:
                            failure = 'command exceeded 240 seconds'
                        if failure:
                            os.killpg(process.pid, signal.SIGKILL)
                            break
                        time.sleep(0.02)
                    code = process.wait()
            after = resource.getrusage(resource.RUSAGE_CHILDREN)
            row = dict(name=name, command=command, cwd=str(cwd), exit=code, expected_exit=expected,
                       wall_seconds=time.monotonic() - start,
                       cpu_user_seconds=after.ru_utime - before.ru_utime,
                       cpu_system_seconds=after.ru_stime - before.ru_stime,
                       peak_aggregate_rss_bytes=peak_rss, guard_failure=failure,
                       stdout=stdout_path.name, stderr=stderr_path.name,
                       stdout_sha256=sha(stdout_path), stderr_sha256=sha(stderr_path),
                       environment={k: self.env[k] for k in
                                    ('JOBS', 'MAKEFLAGS', 'LANGBE', 'LANGOS', 'LANG_CACHE', 'TMPDIR', 'PATH')})
            dump(prefix.with_suffix('.json'), row)
            self.rows.append(row)
            dump(self.evidence / 'stages.json', self.rows)
            self.recorder.emit('receipt', path=prefix.with_suffix('.json').name,
                               sha256=sha(prefix.with_suffix('.json')))
            require(not failure, name + ': ' + str(failure))
            require(code == expected, f'{name}: expected exit {expected}, got {code}; see {stderr_path}')
            return subprocess.CompletedProcess(command, code, stdout_path.read_bytes(), stderr_path.read_bytes())
        except Exception as error:
            self.recorder.emit('error', category='build', message=str(error))
            raise
        finally:
            self.recorder.emit('state', mode='active', activity='evaluation')

    def reference(self, name):
        row = next(row for row in self.rows if row['name'] == name)
        raw = self.evidence / (Path(row['stdout']).stem + '.json')
        return dict(path=raw.name, sha256=sha(raw))


def process_tree_rss(pid):
    """Sum this process tree conservatively (shared pages may be counted twice)."""
    pending, seen, total = [pid], set(), 0
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        try:
            status = Path(f'/proc/{current}/status').read_text()
            match = re.search(r'^VmRSS:\s+(\d+) kB', status, re.M)
            total += int(match[1]) * 1024 if match else 0
            children = Path(f'/proc/{current}/task/{current}/children').read_text()
            pending.extend(int(child) for child in children.split())
        except (FileNotFoundError, ProcessLookupError):
            pass
    return total


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['replay'], required=True)
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--verify-receipt', type=Path)
    args = parser.parse_args()
    if args.verify_receipt:
        try:
            print(json.dumps(verify_receipt(args.verify_receipt)))
            return 0
        except Exception as error:
            print('FAIL: ' + str(error), file=sys.stderr)
            return 1

    os.nice(10)
    cpus = sorted(os.sched_getaffinity(0))[:2]
    os.sched_setaffinity(0, cpus)
    ceiling = 2 * 1024**3
    hard = resource.getrlimit(resource.RLIMIT_AS)[1]
    if hard != resource.RLIM_INFINITY:
        ceiling = min(ceiling, hard)
    resource.setrlimit(resource.RLIMIT_AS, (ceiling, ceiling))
    token = uuid.uuid4().hex
    evidence = (args.evidence or ROOT.parent / 'evidence' / ('author-trials-' + token)).resolve()
    require(evidence != ROOT and ROOT not in evidence.parents, 'evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=False)
    scratch = ROOT.parent / 'scratch' / ('author-trials-' + token)
    scratch.mkdir(parents=True)
    recorder = Recorder.start(evidence / 'events.jsonl', 'automated', 'shipping-replay', 'lang',
                              dict(tool_hours=None, language_author_hours=None, seen_task=True),
                              sha(FIXTURES / 'tasks.v2.json'))
    replay = TrialReplay(evidence, scratch, recorder)
    replay.env.update(MAKEFLAGS='-j2', PYTHONDONTWRITEBYTECODE='1')
    for key in ('VERIFY_CASE', 'LANG_CLANG', 'LANG_ROOT'):
        replay.env.pop(key, None)
    print('evidence: ' + str(evidence), flush=True)
    try:
        tasks, oracles = contract()
        diagnostic_checks(evidence, tasks, oracles)
        recorder_checks(evidence)
        status = replay.run(['git', 'status', '--porcelain', '--untracked-files=all'], 'clean', ROOT)
        require(not status.stdout, 'commit the candidate before replaying it')
        head = replay.run(['git', 'rev-parse', 'HEAD'], 'head', ROOT).stdout.decode().strip()
        replay.run(['git', 'merge-base', '--is-ancestor', BASE, head], 'required-base', ROOT)
        replay.run(['git', 'diff', '--exit-code', BASE, head, '--', 'bootstrap/current', 'web', 'src', 'std'],
                   'protected-inputs', ROOT)
        clone = scratch / 'repo'
        replay.run(['git', 'clone', '--quiet', '--no-hardlinks', str(ROOT), str(clone)], 'clone', ROOT)
        files = replay.run(['git', 'ls-files', '-z'], 'inputs', clone).stdout.decode().split('\0')
        hashes = {p: sha(clone / p) for p in files if p and (clone / p).is_file()}
        tools = {}
        for name in ('make', 'clang', 'ld', 'python3', 'git'):
            found = shutil.which(name)
            require(found, name + ' is required; installation is not performed by replay')
            path = Path(found).resolve()
            tools[name] = dict(path=str(path), sha256=sha(path))
            recorder.emit('installation', tool=name, status='preinstalled', path=str(path))
        identity = evidence / 'identity.json'
        dump(identity, dict(head=head, base=BASE, source_sha256=hashes, tools=tools,
             replay_directory=str(scratch / 'exported'),
             limits=dict(cpus=cpus, address_space_bytes=ceiling, JOBS=2, MAKEFLAGS='-j2', sequential=True,
                         aggregate_rss_guard_bytes=2 * 1024**3, rss_sample_seconds=0.02),
             assumptions='Linux x86-64 libc; trusted shipping frontend; explicit native Clang; '
                         'automated replay of supplied code, not a human session; no installation, '
                         'OS kernel operations, network, fixed points or web generation'))
        for doc in ('docs/AUTHOR_TRIALS.md', 'example/shipping/README.md'):
            recorder.emit('doc', uri=doc, sha256=sha(clone / doc))
        for name in ('shipping.lang', 'runtime.lang'):
            source = clone / 'example/shipping' / name
            recorder.emit('code', path='example/shipping/' + name, sha256=sha(source),
                          baseline_sha256=sha(source), authored_lines=0, generated_lines=0,
                          compiler_core_edits=0, reused_lines=len(source.read_text().splitlines()))
        replay.run(['make', 'init'], 'init', clone)
        replay.run(['make', 'build'], 'build-current-sources', clone)
        compiler = str(clone / 'out/lang_next')
        exported = scratch / 'exported'
        exported.mkdir()
        minted = exported / 'shippingc'
        replay.run([compiler, 'project', 'compiler', str(clone / 'example/shipping/project.lang-project'),
                    '-o', str(minted)], 'export-native-compiler', scratch)
        require(minted.read_bytes().startswith(b'\x7fELF'), 'export is not a native compiler')
        source = exported / 'policy.shipping'
        shutil.copyfile(FIXTURES / 'heldout/native.shipping', source)
        program = exported / 'policy'
        replay.run([str(minted), str(source), '--emit=native', '-o', str(program)], 'compile-heldout', exported)
        require(program.read_bytes().startswith(b'\x7fELF'), 'guest is not a native executable')
        saved_path = replay.env['PATH']
        replay.env['PATH'] = '/nonexistent'
        for name, total in [('below', '79'), ('boundary', '80'), ('above', '81')]:
            replay.run([str(program), total], name, exported)
        replay.run([str(program), '-1'], 'bad-total', exported, expected=64)
        recorder.emit('error', category='runtime', message='expected invalid-total rejection',
                      receipt=replay.reference('bad-total'))
        replay.env['PATH'] = saved_path
        bad_output = exported / 'rejected'
        replay.run([str(minted), str(FIXTURES / 'heldout/duplicate.shipping'), '--emit=native',
                    '-o', str(bad_output)], 'duplicate', exported, expected=1)
        require(not bad_output.exists(), 'failed compile left an artifact')
        recorder.emit('error', category='semantics', message='expected duplicate-setting rejection',
                      receipt=replay.reference('duplicate'))
        receipt = dict(version=2, kind='automated', claimed_success=True, head=head,
                       identity=dict(path=identity.name, sha256=sha(identity)),
                       observations={name: replay.reference(name) for name in
                                     ('below', 'boundary', 'above', 'duplicate', 'bad-total')})
        good = evidence / 'success-receipt.json'
        dump(good, receipt)
        verify_receipt(good)
        # Above and boundary both print zero: output equality cannot prove which
        # input ran. Also reject altered commands even with the right row name.
        boundary = json.loads(inside(evidence, replay.reference('boundary')['path']).read_text())
        false_references = [('false-success', 'boundary', replay.reference('below'), 'command mismatch'),
                            ('same-output-swap', 'boundary', replay.reference('above'), 'command mismatch')]
        for name in ('wrong-argument', 'wrong-executable', 'wrong-directory', 'wrong-output'):
            row = copy.deepcopy(boundary)
            if name == 'wrong-argument':
                row['command'][1] = '81'
            elif name == 'wrong-executable':
                row['command'][0] += '-other'
            elif name == 'wrong-directory':
                row['cwd'] = str(scratch)
            else:
                below = next(row for row in replay.rows if row['name'] == 'below')
                row['stdout'], row['stdout_sha256'] = below['stdout'], below['stdout_sha256']
            raw = evidence / (name + '-raw.json')
            dump(raw, row)
            failure = ('working directory mismatch' if name == 'wrong-directory' else
                       'stdout mismatch' if name == 'wrong-output' else 'command mismatch')
            false_references.append((name, 'boundary', dict(path=raw.name, sha256=sha(raw)), failure))
        duplicate = json.loads(inside(evidence, replay.reference('duplicate')['path']).read_text())
        for name, location in [('zero-line', '0:1'), ('zero-column', '1:0'), ('zero-location', '0:0')]:
            row = copy.deepcopy(duplicate)
            stderr = evidence / (name + '.stderr')
            stderr.write_text('shipping:' + location + ': duplicate setting\n')
            row['stderr'], row['stderr_sha256'] = stderr.name, sha(stderr)
            raw = evidence / (name + '-raw.json')
            dump(raw, row)
            false_references.append((name, 'duplicate', dict(path=raw.name, sha256=sha(raw)),
                                     'missing source location'))
        for name, observation, reference, failure in false_references:
            false = copy.deepcopy(receipt)
            false['observations'][observation] = reference
            false_path = evidence / (name + '-receipt.json')
            dump(false_path, false)
            stage = name + '-must-fail'
            result = replay.run([sys.executable, '-B', str(ROOT / 'test/reader_author/trial_protocol.py'),
                                 '--case', 'replay', '--verify-receipt', str(false_path)],
                                stage, ROOT, expected=1)
            require((observation + ': ' + failure).encode() in result.stderr,
                    name + ' failed for the wrong reason')
            recorder.emit('error', category='oracle', message=name + ' receipt rejected',
                          receipt=replay.reference(stage))
        # Source hashes bind the replay to an unchanged compiler and frontend.
        require(all(sha(clone / p) == digest for p, digest in hashes.items()), 'replay changed tracked source')
        dump(evidence / 'artifacts.json', dict(compiler=sha(compiler), exported_compiler=sha(minted),
                                               native_program=sha(program), guest=sha(source)))
        recorder.emit('finish')
        dump(evidence / 'session.json', recorder.summary())
        dump(evidence / 'result.json', dict(passed=True, head=head, kind='automated', human_results='not measured',
                                           observations=len(replay.rows), false_success_rejected=True,
                                           rejected_receipts=[name for name, _, _, _ in false_references]))
        print('PASS replay: five frozen tasks, recorder accounting, real native shipping export, '
              'held-out outputs and false success refusal; human results: not measured')
        return 0
    except Exception as error:
        if recorder.events[-1]['type'] != 'finish':
            recorder.emit('error', category='oracle', message=str(error))
            recorder.emit('finish')
        dump(evidence / 'session.json', recorder.summary())
        dump(evidence / 'result.json', dict(passed=False, kind='automated', error=str(error)))
        print('FAIL: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
