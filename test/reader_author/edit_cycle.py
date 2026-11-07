#!/usr/bin/env python3
"""Replay the content-based shipping edit cycle from a committed candidate."""
import argparse
import errno
import importlib.util
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import time
import uuid

from project import ProjectReplay
from route import ROOT, dump, require, sha

BASE = '2bcf0b35fe91c6cd3b81c53483e5c16574dd7570'


def wait_for(predicate, message, timeout=30):
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        if predicate():
            return
        time.sleep(0.03)
    raise RuntimeError(message)


def same_time(path, text):
    stamp = path.stat()
    path.write_text(text)
    os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    require(path.stat().st_mtime_ns == stamp.st_mtime_ns, 'same timestamp control failed')


def alive(pid):
    try:
        return Path(f'/proc/{pid}/stat').read_text().split()[2] != 'Z'
    except FileNotFoundError:
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['content-changes'], required=True)
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
    evidence = (args.evidence or ROOT.parent / 'evidence' / ('edit-cycle-' + token)).resolve()
    require(evidence != ROOT and ROOT not in evidence.parents, 'evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=False)
    scratch = ROOT.parent / 'scratch' / ('edit-cycle-' + token)
    scratch.mkdir(parents=True)
    replay = ProjectReplay(evidence, scratch)
    replay.env.update(MAKEFLAGS='-j2', PYTHONDONTWRITEBYTECODE='1')
    watch = None
    cli = None
    print('evidence: ' + str(evidence), flush=True)
    try:
        result = replay.run(['git', 'status', '--porcelain', '--untracked-files=all'], 'clean', ROOT)
        require(not result.stdout, 'commit candidate before replay')
        head = replay.run(['git', 'rev-parse', 'HEAD'], 'head', ROOT).stdout.decode().strip()
        replay.run(['git', 'merge-base', '--is-ancestor', BASE, head], 'ancestry', ROOT)
        replay.run(['git', 'diff', '--exit-code', BASE, head, '--', 'bootstrap/current', 'web'], 'protected-inputs', ROOT)
        clone = scratch / 'repo'
        replay.run(['git', 'clone', '--quiet', '--no-hardlinks', str(ROOT), str(clone)], 'clone', ROOT)
        files = replay.run(['git', 'ls-files', '-z'], 'inputs', clone).stdout.decode().split('\0')
        hashes = {p: sha(clone / p) for p in files if p and (clone / p).is_file()}
        tools = {name: {'path': str(Path(shutil.which(name)).resolve()),
                        'sha256': sha(Path(shutil.which(name)).resolve())}
                 for name in ['make', 'clang', 'ld', 'python3', 'git']}
        dump(evidence / 'identity.json', dict(head=head, base=BASE, source_sha256=hashes, tools=tools,
             limits=dict(cpus=cpus, address_space_bytes=ceiling, JOBS=2, MAKEFLAGS='-j2'),
             assumptions='Linux x86-64 libc and Clang; two inherited CPUs, sequential build trees, '
             '2 GiB address-space ceiling; project entry is the watched guest; runtime edits rebuild '
             'the native program; no Linux kernel operations, web generation, full suites or fixed points; '
             'failed and pending generations invalidate the prior managed output; phase times are host-specific'))
        replay.run(['make', 'init'], 'init', clone)
        replay.run(['make', 'build'], 'build-current-sources', clone)
        compiler = str(clone / 'out/lang_next')
        tracer = scratch / 'trace.so'
        replay.run(['clang', '-shared', '-fPIC', str(clone / 'test/reader_author/fixtures/edit_cycle/process_trace.c'),
                    '-ldl', '-o', str(tracer)], 'process-tracer', clone)
        project_dir = scratch / 'shipping'
        shutil.copytree(clone / 'example/shipping', project_dir)
        shutil.copytree(project_dir, evidence / 'shipping-inputs')
        manifest = project_dir / 'project.lang-project'
        guest = project_dir / 'policy.shipping'
        reader = project_dir / 'shipping.lang'
        runtime = project_dir / 'runtime.lang'
        output = scratch / 'policy'
        spec = importlib.util.spec_from_file_location('watch_host', clone / 'std/project_watch.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        env = dict(replay.env, LANG_ROOT=str(clone), LD_PRELOAD=str(tracer), EDIT_PROCESS_TRACE=str(evidence / 'forks.log'))
        watch = module.Watch(compiler, manifest, output, evidence / 'watch', env)
        metrics = []

        def forks():
            path = evidence / 'forks.log'
            return len(path.read_text().splitlines()) if path.exists() else 0

        def readers():
            directory = scratch / 'cache/readers'
            return {p.name: dict(sha256=sha(p), mtime_ns=p.stat().st_mtime_ns)
                    for p in directory.iterdir() if p.is_file() and p.read_bytes().startswith(b'\x7fELF')}

        def completed():
            watch.tick()
            return watch.active is None

        def archive(name):
            directory = evidence / name
            directory.mkdir()
            for p in (guest, reader, runtime, manifest):
                shutil.copyfile(p, directory / p.name)
            for event in watch.events:
                if event.get('build_generation') != watch.generation:
                    continue
                build = Path(event['directory'])
                for p in build.rglob('*'):
                    if p.is_file():
                        dest = directory / p.relative_to(build)
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(p, dest)
            cache = scratch / 'cache/readers'
            for p in cache.iterdir():
                if p.suffix in ('.lang', '.identity'):
                    shutil.copyfile(p, directory / ('reader-cache-' + p.name))
            return directory

        def phase(name, expected='published'):
            before, start, index, probes = forks(), time.monotonic(), len(watch.events), watch.probes
            watch.tick()
            wait_for(completed, name + ' did not complete', timeout=90)
            events = watch.events[index:]
            event = events[-1] if events else None
            require(event is not None and event['event'] == expected, name + ': wrong result ' + str(event))
            directory = archive(name)
            count = forks() - before
            row = dict(name=name, seconds=time.monotonic() - start, descendant_subprocesses=count,
                       build_subprocesses=1 + count, identity_probe_subprocesses=watch.probes - probes,
                       phase_seconds=event.get('phase_seconds', {}), event=event,
                       readers=readers(), evidence=str(directory))
            metrics.append(row)
            dump(evidence / 'measurements.json', metrics)
            return row

        cold = phase('cold')
        require(set(cold['phase_seconds']) == set(module.PHASES) and cold['descendant_subprocesses'] > 0, 'missing phase/process measurements')
        cold_readers = readers()
        require(cold_readers, 'cold build did not mint any readers')
        result = replay.run([str(output), '99'], 'cold-runtime', scratch)
        require(result.stdout == b'10\n' and not result.stderr, 'cold shipping result')
        competing = module.Watch(compiler, manifest, output, evidence / 'competing', env)
        conflict = False
        try:
            competing.tick()
        except ValueError as error:
            conflict = 'another watch owns' in str(error)
        finally:
            competing.close()
        require(conflict and output.exists(), 'competing watch took ownership or invalidated the output')
        before, start, generation, probes = forks(), time.monotonic(), watch.generation, watch.probes
        watch.tick()
        require(watch.active is None and watch.generation == generation and readers() == cold_readers and forks() == before,
                'unchanged inputs rebuilt a stage')
        metrics.append(dict(name='unchanged', seconds=time.monotonic() - start,
            build_subprocesses=0, descendant_subprocesses=0, identity_probe_subprocesses=watch.probes - probes,
            phase_seconds={name: 0 for name in module.PHASES}, readers=readers()))
        same_time(guest, guest.read_text().replace('base 10', 'base 11'))
        edited = phase('guest-edit')
        require(readers() == cold_readers, 'guest edit reminted the reader')
        result = replay.run([str(output), '99'], 'guest-runtime', scratch)
        require(result.stdout == b'11\n', 'same-time guest edit was missed')
        same_time(reader, reader.read_text().replace('settings:shipping_setting*', 'settings:shipping_setting+'))
        grammar = phase('grammar-edit')
        require(readers() != cold_readers and grammar['descendant_subprocesses'] > edited['descendant_subprocesses'], 'grammar edit did not remint the reader')
        grammar_readers = readers()
        same_time(runtime, runtime.read_text().replace('print_int(fee);', 'print_int(fee + 1);'))
        phase('runtime-edit')
        require(readers() == grammar_readers, 'runtime edit rebuilt the frontend')
        result = replay.run([str(output), '99'], 'runtime-edited-result', scratch)
        require(result.stdout == b'12\n', 'runtime package was stale')
        # A failed mint must not execute a stale cached reader.
        valid_reader = reader.read_text()
        same_time(reader, valid_reader.replace('return ast_program(decls);', 'return edit_cycle_undefined(decls);'))
        failed_mint = phase('failed-mint', 'failed')
        require(not output.exists() and b'edit_cycle_undefined' in (Path(failed_mint['evidence']) / 'stderr').read_bytes(),
                'failed reader mint reused stale code or hid the compiler error')
        same_time(reader, valid_reader)
        phase('mint-recovery')
        valid_guest = guest.read_text()
        # An ABA edit between the probe and pipeline capture must never publish
        # output compiled from the intervening bytes, even if both probes agree.
        original_inputs = watch.inputs
        def intervening_inputs():
            value = original_inputs()
            same_time(guest, valid_guest.replace('base 11', 'base 19'))
            return value
        watch.inputs = intervening_inputs
        before_race = len(watch.events)
        watch.key = None
        watch.tick()
        watch.inputs = original_inputs
        wait_for(lambda: watch.active['process'].poll() is not None, 'ABA control build did not finish')
        same_time(guest, valid_guest)
        watch.tick()
        require(watch.events[-1]['event'] == 'superseded' and not output.exists(), 'ABA build published stale bytes')
        phase('capture-race-recovery')
        require(sum(e['event'] == 'published' for e in watch.events[before_race:]) == 1, 'ABA output was published')
        # Exercise both probes, including edits after the final probe's read,
        # same-byte ABA writes and atomic editor replacement. No identity probe
        # may expose a provisional executable at the destination.
        for boundary in ('probe', 'final-probe', 'final-probe-aba', 'final-probe-replace',
                         'rename', 'rename-aba', 'rename-cancel', 'rename-current'):
            watch.key = None
            watch.tick()
            wait_for(lambda: watch.active['process'].poll() is not None, 'publication control build did not finish')
            rejected_program = watch.active['directory'] / 'program'
            original_replace = module.os.replace
            injected = False
            probe_count = 0
            execution_attempts = []

            def edit_after_probe():
                nonlocal injected, probe_count
                require(not output.exists(), 'provisional executable visible during identity probe')
                value = original_inputs()
                probe_count += 1
                target_probe = 1 if boundary == 'probe' else 2
                if probe_count == target_probe:
                    injected = True
                    if boundary == 'final-probe-replace':
                        replacement = scratch / 'replacement.shipping'
                        replacement.write_text(valid_guest.replace('base 11', 'base 19'))
                        original_replace(replacement, guest)
                    else:
                        same_time(guest, valid_guest.replace('base 11', 'base 19'))
                    if boundary == 'final-probe-aba':
                        same_time(guest, valid_guest)
                return value

            def edit_at_rename(source, destination):
                nonlocal injected
                if injected or Path(destination) != output:
                    return original_replace(source, destination)
                injected = True
                # Open the inode before rename too: a consumer can retain a
                # descriptor rather than execute via the public pathname.
                with Path(source).open('rb') as consumer:
                    if boundary == 'rename-cancel':
                        watch.stopped = True
                    elif boundary != 'rename-current':
                        same_time(guest, valid_guest.replace('base 11', 'base 19'))
                        if boundary == 'rename-aba':
                            same_time(guest, valid_guest)
                    original_replace(source, destination)
                    # Attempt execution BEFORE the watcher resumes validation,
                    # reproducing the externally observable replacement race.
                    for command in ([str(output), '99'], [f'/proc/self/fd/{consumer.fileno()}', '99']):
                        try:
                            result = subprocess.run(command, capture_output=True, pass_fds=(consumer.fileno(),))
                        except OSError as error:
                            require(error.errno == errno.ETXTBSY, 'unexpected execution exclusion: ' + str(error))
                            execution_attempts.append(dict(command=command, errno=error.errno))
                        else:
                            raise RuntimeError('unvalidated executable ran during replacement: ' + repr(result.stdout))
                return None

            if not boundary.startswith('rename'):
                watch.inputs = edit_after_probe
            else:
                module.os.replace = edit_at_rename
            before_publication = len(watch.events)
            try:
                watch.tick()
            finally:
                watch.inputs = original_inputs
                module.os.replace = original_replace
                watch.stopped = False
            if boundary.startswith('rename'):
                require(len(execution_attempts) == 2, 'replacement consumers were not exercised')
                dump(evidence / (boundary + '-execution.json'), execution_attempts)
            if boundary == 'rename-current':
                require(injected and watch.events[-1]['event'] == 'published' and output.exists(),
                        'current candidate did not publish after execution exclusion')
                result = replay.run([str(output), '99'], boundary + '-runtime', scratch)
                require(result.stdout == b'12\n', 'accepted output stayed excluded or ran wrong code')
                archive('publication-' + boundary)
                continue
            require(injected and watch.events[-1]['event'] == 'superseded' and
                    not output.exists() and rejected_program.exists() and watch.key is None,
                    boundary + ': publication race accepted obsolete output or lost retry/artifact')
            require(not any(e['event'] == 'published' for e in watch.events[before_publication:]),
                    boundary + ': obsolete publication event')
            archive('publication-' + boundary + '-superseded')
            phase('publication-' + boundary + '-latest')
            result = replay.run([str(output), '99'], 'publication-' + boundary + '-runtime', scratch)
            expected = b'12\n' if boundary in ('final-probe-aba', 'rename-aba', 'rename-cancel') else b'20\n'
            require(result.stdout == expected, boundary + ': latest generation was not rebuilt')
            same_time(guest, valid_guest)
            if boundary not in ('final-probe-aba', 'rename-aba', 'rename-cancel'):
                phase('publication-' + boundary + '-recovery')
        same_time(guest, 'shipping { base 11 free_over 100; }\n')
        failure = phase('reader-failure', 'failed')
        require(not output.exists() and failure['event']['exit'] == 1, 'failed build left a published output')
        require(b"expected ';'" in (Path(failure['evidence']) / 'stderr').read_bytes(), 'original reader error lost')
        same_time(guest, valid_guest)
        phase('recovery')
        valid_runtime = runtime.read_text()
        same_time(runtime, valid_runtime.replace('print_int(fee + 1); println(""); return 0;',
            'return edit_cycle_missing(fee);') + '\nextern func edit_cycle_missing(fee i64) i64;\n')
        failure = phase('link-failure', 'failed')
        require(not output.exists() and b'edit_cycle_missing' in (Path(failure['evidence']) / 'stderr').read_bytes(), 'original link error lost')
        same_time(runtime, valid_runtime)
        phase('link-recovery')
        # Invalid manifest/dependency edits remain observable and can recover.
        valid_reader = reader.read_text()
        same_time(reader, valid_reader + '\ninclude "missing-edit-dependency.lang"\n')
        watch.tick()
        require(watch.active is None and not output.exists() and watch.events[-1]['event'] == 'invalid', 'missing dependency not invalidated')
        same_time(reader, valid_reader)
        phase('dependency-recovery')
        # A controlled tool delay lets successive edits overtake active builds.
        blocker, marker = scratch / 'block', scratch / 'tool-pids'
        blocker.write_text('block')
        tool = scratch / 'clang-delay'
        tool.write_text('#!/bin/bash\nif [ "$(cat "$EDIT_BLOCK_TOOL")" = block ] && [ "$1" = -O0 ]; then\n'
            'trap "" TERM\nsleep 120 &\nprintf "%s %s\\n" "$$" "$!" >> "$EDIT_TOOL_PIDS"\nwait\nfi\n'
            'exec ' + tools['clang']['path'] + ' "$@"\n')
        tool.chmod(0o755)
        shutil.copyfile(tool, evidence / tool.name)
        watch.env.update(LANG_CLANG=str(tool), EDIT_BLOCK_TOOL=str(blocker), EDIT_TOOL_PIDS=str(marker))
        rapid_start = len(watch.events)
        old_groups = []
        for n in (12, 13):
            same_time(guest, valid_guest.replace('base 11', 'base ' + str(n)))
            watch.tick()
            old_groups.append(watch.active['process'].pid)
            wait_for(lambda: marker.exists() and len(marker.read_text().splitlines()) == n - 11,
                     'controlled tool did not start')
        blocker.write_text('go')
        same_time(guest, valid_guest.replace('base 11', 'base 14'))
        phase('rapid-latest')
        events = watch.events[rapid_start:]
        require([r['event'] for r in events].count('cancelled') == 2 and
                [r['event'] for r in events].count('published') == 1, 'superseded generation published')
        pids = old_groups + [int(p) for line in marker.read_text().splitlines() for p in line.split()]
        wait_for(lambda: not any(alive(p) for p in pids), 'cancelled tool descendants survived')
        result = replay.run([str(output), '99'], 'latest-runtime', scratch)
        require(result.stdout == b'15\n', 'rapid edit published obsolete output')
        watch.close()
        # Exercise public CLI cancellation, recovery and destination protection.
        cli_evidence = evidence / 'cli-cancel'
        cli_output = scratch / 'cli-program'
        blocker.write_text('block')
        cli_env = dict(env, LANG_CLANG=str(tool), EDIT_BLOCK_TOOL=str(blocker), EDIT_TOOL_PIDS=str(marker))
        command = [compiler, 'watch', '--project', str(manifest), '-o', str(cli_output),
                   '--evidence', str(cli_evidence), '--interval', '0.02']
        with (evidence / 'cli.stdout').open('wb') as out, (evidence / 'cli.stderr').open('wb') as err:
            cli = subprocess.Popen(command, env=cli_env, cwd=clone, stdout=out, stderr=err)
            wait_for(lambda: len(marker.read_text().splitlines()) == 3, 'CLI did not build')
            cli.send_signal(signal.SIGINT)
            code = cli.wait(timeout=10)
        dump(evidence / 'cli-command.json', dict(command=command, cwd=str(clone), exit=code,
             stdout='cli.stdout', stderr='cli.stderr'))
        require(code == 130 and not cli_output.exists(), 'cancelled CLI published output or lost exit')
        pids = [int(p) for line in marker.read_text().splitlines() for p in line.split()]
        wait_for(lambda: not any(alive(p) for p in pids), 'CLI left a child alive')
        blocker.write_text('go')
        saved_env = replay.env
        replay.env = cli_env
        replay.run([compiler, 'watch', '--project', str(manifest), '-o', str(cli_output),
                    '--evidence', str(evidence / 'cli-once'), '--once'], 'cli-once', clone)
        result = replay.run([str(cli_output), '99'], 'cli-runtime', scratch)
        require(result.stdout == b'15\n', 'public CLI did not recover')
        for boundary in ('probe', 'final-probe', 'cancel-final-probe', 'rename', 'cancel-rename'):
            same_time(guest, valid_guest.replace('base 11', 'base 14'))
            race_evidence = evidence / ('cli-once-race-' + boundary)
            replay.run([sys.executable, str(clone / 'test/reader_author/fixtures/edit_cycle/publication_race.py'),
                        str(clone / 'std/project_watch.py'), str(guest), 'base 14', 'base 19', boundary,
                        '--compiler', compiler, '--project', str(manifest), '-o', str(cli_output),
                        '--evidence', str(race_evidence), '--once'], 'cli-once-race-' + boundary, clone,
                       expected=130 if boundary.startswith('cancel-') else 0)
            events = [json.loads(line) for line in (race_evidence / 'events.jsonl').read_text().splitlines()]
            if boundary.startswith('cancel-'):
                require(not cli_output.exists() and not any(e['event'] == 'published' for e in events),
                        'cancellation during final probe published output')
            else:
                require([e['event'] for e in events].count('superseded') == 1 and
                        [e['event'] for e in events].count('published') == 1 and
                        events[-1]['build_generation'] == 2, '--once exited on a superseded generation')
                result = replay.run([str(cli_output), '99'], 'cli-once-race-runtime-' + boundary, scratch)
                require(result.stdout == b'20\n', '--once published obsolete output')
        sentinel = scratch / 'sentinel'
        sentinel.write_text('keep this input\n')
        replay.run([compiler, 'watch', '--project', str(manifest), '-o', str(sentinel), '--once',
                    '--evidence', str(evidence / 'cli-refuse')], 'refuse-input', clone, expected=1)
        require(sentinel.read_text() == 'keep this input\n', 'watch overwrote an unrelated file')
        replay.env = saved_env
        require(all(sha(clone / p) == h for p, h in hashes.items()), 'edit cycle mutated committed sources')
        dump(evidence / 'measurements.json', metrics)
        dump(evidence / 'result.json', dict({'pass': True}, head=head, compiler_sha256=sha(compiler),
             controls=['same-mtime-guest', 'same-mtime-grammar', 'runtime', 'reader-failure', 'link-failure',
                       'failed-mint', 'capture-race', 'publication-probe-race', 'publication-rename-race',
                       'final-probe-race', 'final-probe-aba', 'final-probe-replacement',
                       'rename-exec-exclusion', 'rename-fd-exec-exclusion', 'rename-aba', 'rename-cancellation', 'rename-current',
                       'once-final-probe-race', 'final-probe-cancellation', 'once-publication-race', 'missing-dependency', 'rapid-edits', 'process-tree-cancellation', 'CLI', 'output-protection']))
        print('PASS content-changes: cold/unchanged/guest/grammar phase timings and process counts, runtime invalidation, errors, rapid edits and cancellation')
        return 0
    except Exception as error:
        dump(evidence / 'result.json', {'pass': False, 'error': str(error)})
        print('FAIL: ' + str(error), file=sys.stderr)
        return 1
    finally:
        if watch is not None:
            watch.close()
        if cli is not None and cli.poll() is None:
            cli.send_signal(signal.SIGTERM)
            cli.wait(timeout=10)


if __name__ == '__main__':
    sys.exit(main())
