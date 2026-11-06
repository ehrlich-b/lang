#!/usr/bin/env python3
"""Replay complete-project creation from committed sources, outside the repo."""
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

BASE = '03ee80d3dfef74170bb2e0e600d1c36306ae8c89'


def snapshot(directory):
    return {str(p.relative_to(directory)): sha(p)
            for p in directory.rglob('*') if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['project'], required=True)
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
    evidence = (args.evidence or ROOT.parent / 'evidence' / ('project-' + token)).resolve()
    require(evidence != ROOT and ROOT not in evidence.parents, 'evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=False)
    scratch = ROOT.parent / 'scratch' / ('project-' + token)
    scratch.mkdir(parents=True)
    replay = ProjectReplay(evidence, scratch)
    replay.env.update(MAKEFLAGS='-j2', PYTHONDONTWRITEBYTECODE='1')
    replay.env.pop('LANG_ROOT', None)
    print(f'evidence: {evidence}', flush=True)
    try:
        status = replay.run(['git', 'status', '--porcelain', '--untracked-files=all'], 'clean', ROOT)
        require(not status.stdout, 'commit the candidate before replaying it')
        head = replay.run(['git', 'rev-parse', 'HEAD'], 'head', ROOT).stdout.decode().strip()
        replay.run(['git', 'merge-base', '--is-ancestor', BASE, head], 'contract-ancestry', ROOT)
        clone = scratch / 'repo'
        replay.run(['git', 'clone', '--no-hardlinks', '--quiet', str(ROOT), str(clone)], 'clone', ROOT)
        files = replay.run(['git', 'ls-files', '-z'], 'inputs', clone).stdout.decode().split('\0')
        hashes = {p: sha(clone / p) for p in files if p and (clone / p).is_file()}
        tools = {}
        for name in ('bash', 'make', 'clang', 'ld', 'python3', 'git'):
            path = Path(shutil.which(name)).resolve()
            tools[name] = {'path': str(path), 'sha256': sha(path)}
        dump(evidence / 'identity.json', {
            'head': head, 'base': BASE, 'source_sha256': hashes, 'tools': tools,
            'limits': {'cpus': cpus, 'address_space_bytes': ceiling, 'JOBS': 2, 'MAKEFLAGS': '-j2'},
            'assumptions': 'Linux x86-64 libc and Clang; fresh NAME directory; shipping whole units; '
                'inclusive free_over; project cwd for local inputs; no LANG_ROOT; failed writes retain '
                'incomplete new files; no OS kernel tests, fixed points or web artifacts'})
        replay.run(['make', 'init'], 'init', clone)
        replay.run(['make', 'build'], 'build-current-sources', clone)
        compiler = str(clone / 'out/lang_next')
        result = replay.run([compiler, 'new', 'language', 'parcel'], 'generate-outside-repo', scratch)
        require(not result.stderr, 'generation emitted diagnostics')
        project = scratch / 'parcel'
        expected = {'reader.lang', 'runtime.lang', 'project.lang-project', 'policy.parcel',
                    'syntax.parcel', 'semantic.parcel', 'tests.json', 'cases.json', 'check.py', 'README.md'}
        require({p.name for p in project.iterdir()} == expected, 'incomplete project')
        shutil.copytree(project, evidence / 'generated')
        initial = snapshot(project)
        dump(evidence / 'generated-hashes.json', initial)
        text = (project / 'reader.lang').read_text()
        require('#parser{' in text and 'func parcel_check(' in text and 'ast_ge(' in text,
                'syntax, semantic check and runtime comparison must be visible')
        # The exact printed block must work, including cd from the external cwd.
        commands = result.stdout.decode().split('Run these commands from this directory:\n', 1)[1]
        (evidence / 'commands.sh').write_text('set -euo pipefail\n' + commands)
        result = replay.shell(commands, 'printed-commands', scratch)
        require(b'PASS runtime comparison, syntax rejection, semantic rejection\n' in result.stdout,
                'printed commands did not run the fixture comparison')
        ast = (project / 'policy.ast').read_text()
        require('(binop >=' in ast and '(ident total)' in ast and '(number 100)' in ast,
                'runtime total was folded into a constant answer')
        shutil.copyfile(project / 'policy.ast', evidence / 'policy.ast')
        minted = str(project / 'parcelc')
        # Explicit negative command receipts distinguish syntax from semantics.
        for name, diagnostic in [('syntax', b'expected'), ('semantic', b'duplicate setting')]:
            result = replay.run([minted, name + '.parcel', '-o', name + '.ll'],
                                'reject-' + name, project, expected=1)
            require(diagnostic in result.stderr, 'wrong negative fixture diagnostic: ' + name)
            require(not (project / (name + '.ll')).exists(), 'rejected source emitted LLVM')
        # The minted compiler emits IR without compiler tools in PATH.
        saved_path = replay.env['PATH']
        replay.env['PATH'] = '/nonexistent'
        replay.run([minted, 'policy.parcel', '-o', 'isolated.ll'], 'minted-no-tools', project)
        replay.env['PATH'] = saved_path
        for total, expected_output in json.loads((project / 'cases.json').read_text()):
            result = replay.run([str(project / 'build/policy'), total], 'runtime-' + total, project)
            require(result.stdout == expected_output.encode() and not result.stderr, 'wrong runtime result')
        # An intentionally incorrect expectation must fail the generated runner.
        wrong = scratch / 'wrong-expectation'
        shutil.copytree(evidence / 'generated', wrong)
        cases = json.loads((wrong / 'cases.json').read_text())
        cases[0][1] = '11\n'
        (wrong / 'cases.json').write_text(json.dumps(cases) + '\n')
        result = replay.run(['python3', '-B', 'check.py', minted], 'expectation-must-fail', wrong, expected=1)
        require(b'expected' in result.stderr and b'FAIL:' in result.stderr, 'failed expectation was swallowed')
        # Editing only the generated frontend changes the boundary behavior.
        edited = scratch / 'edited'
        shutil.copytree(evidence / 'generated', edited)
        (edited / 'reader.lang').write_text(text.replace('ast_ge(', 'ast_gt('))
        cases = json.loads((edited / 'cases.json').read_text())
        cases[2][1] = '10\n'
        (edited / 'cases.json').write_text(json.dumps(cases) + '\n')
        replay.run([compiler, 'project', 'compiler', 'project.lang-project', '-o', 'parcelc'], 'editable-compiler', edited)
        replay.run(['python3', '-B', 'check.py', './parcelc'], 'editable-comparison', edited)
        shutil.copyfile(edited / 'reader.lang', evidence / 'edited-reader.lang')
        # Existing directories, files and dangling symlinks fail before writes.
        occupied = scratch / 'occupied'
        occupied.mkdir()
        (occupied / 'runtime.lang').write_text('existing runtime: keep these bytes\n')
        before = snapshot(occupied)
        result = replay.run([compiler, 'new', 'language', 'occupied'], 'partially-occupied', scratch, expected=1)
        require(snapshot(occupied) == before and b'destination may exist' in result.stderr,
                'partial destination changed before refusal')
        after = snapshot(project)
        replay.run([compiler, 'new', 'language', 'parcel'], 'repeat-refused', scratch, expected=1)
        require(snapshot(project) == after, 'repeat generation destroyed existing content')
        (scratch / 'empty').mkdir()
        replay.run([compiler, 'new', 'language', 'empty'], 'empty-directory-refused', scratch, expected=1)
        require(not list((scratch / 'empty').iterdir()), 'empty collision wrote files')
        (scratch / 'filecollision').write_text('keep file\n')
        replay.run([compiler, 'new', 'language', 'filecollision'], 'file-refused', scratch, expected=1)
        require((scratch / 'filecollision').read_text() == 'keep file\n', 'existing file changed')
        (scratch / 'dangling').symlink_to('absent-target')
        replay.run([compiler, 'new', 'language', 'dangling'], 'symlink-refused', scratch, expected=1)
        require((scratch / 'dangling').is_symlink() and not (scratch / 'absent-target').exists(), 'symlink changed')
        # Real write() failure on runtime.lang, after reader.lang was written.
        fault = scratch / 'second-write.so'
        replay.run(['clang', '-shared', '-fPIC', str(clone / 'test/reader_author/fixtures/project/second-write.c'),
                    '-ldl', '-o', str(fault)], 'build-storage-fault', scratch)
        sentinel = snapshot(occupied)
        replay.env['LD_PRELOAD'] = str(fault)
        result = replay.run([compiler, 'new', 'language', 'failed'], 'failed-second-write', scratch, expected=1)
        replay.env.pop('LD_PRELOAD')
        require(b'cannot finish failed/runtime.lang' in result.stderr, 'second write was not exercised')
        require((scratch / 'failed/reader.lang').read_text().startswith('include '), 'first write did not finish')
        require((scratch / 'failed/runtime.lang').stat().st_size == 0, 'second write unexpectedly succeeded')
        require(snapshot(occupied) == sentinel, 'write failure destroyed existing content')
        shutil.copytree(scratch / 'failed', evidence / 'failed-write')
        dump(evidence / 'collisions.json', {'occupied_before': before, 'occupied_after': snapshot(occupied),
             'repeat_before': after, 'repeat_after': snapshot(project), 'failed_write': snapshot(scratch / 'failed')})
        # Each name is itself free, but its generated helper collides with the
        # toolkit/compiler. Refusal must happen before reserving any directory.
        for name, symbol in [('tok', 'tok_number'), ('parse', 'parse_check'), ('scan', 'scan_number')]:
            before = {p.name for p in scratch.iterdir()}
            result = replay.run([compiler, 'new', 'language', name],
                                'derived-collision-' + name, scratch, expected=1)
            require(b'conflicts with a compiler or reader toolkit symbol' in result.stderr,
                    'missing derived-symbol diagnostic: ' + symbol)
            require(not result.stdout and {p.name for p in scratch.iterdir()} == before,
                    'derived-symbol collision wrote a destination: ' + symbol)
        # Existing content remains untouched even for a colliding helper name.
        (scratch / 'tok').mkdir()
        (scratch / 'tok/reader.lang').write_text('keep existing reader\n')
        before = snapshot(scratch / 'tok')
        replay.run([compiler, 'new', 'language', 'tok'], 'derived-collision-occupied', scratch, expected=1)
        require(snapshot(scratch / 'tok') == before, 'derived collision changed existing content')
        dump(evidence / 'derived-collisions.json', {
            'rejected': {'tok': 'tok_number', 'parse': 'parse_check', 'scan': 'scan_number'},
            'occupied_before': before, 'occupied_after': snapshot(scratch / 'tok')})
        for name in ('_start', '__dso_handle', 'Upper', 'aB', '9name', 'lang', 'ast', 'if', '../escape', 'bad-name', 'x' * 65,
                     'main', 'print', 'alloc', 'reader_transform', 'reader_build_arch', 'TOKEN_EOF',
                     'parcel ', ' parcel', 'parcel\t', 'parcel\n', 'parcel/*comment*/'):
            before = {p.name for p in scratch.iterdir()}
            result = replay.run([compiler, 'new', 'language', name],
                                'invalid-name-' + str(len(replay.rows)), scratch, expected=1)
            require(b'Error: language name' in result.stderr, 'missing name diagnostic')
            require({p.name for p in scratch.iterdir()} == before, 'invalid name wrote a destination')
        # The extension ll used to make the checker overwrite its own source.
        result = replay.run([compiler, 'new', 'language', 'll'], 'generate-ll', scratch)
        ll = scratch / 'll'
        ll_initial = snapshot(ll)
        commands = result.stdout.decode().split('Run these commands from this directory:\n', 1)[1]
        (evidence / 'll-commands.sh').write_text('set -euo pipefail\n' + commands)
        replay.shell(commands, 'll-printed-commands', scratch)
        replay.run(['python3', '-B', 'check.py', './llc'], 'll-repeat-check', ll)
        require(all(sha(ll / p) == h for p, h in ll_initial.items()),
                'll workflow overwrote generated source')
        require((ll / 'build/policy.ll').is_file() and (ll / 'build/policy').is_file(),
                'checker outputs are not separated from guest sources')
        dump(evidence / 'll-source-preservation.json', {
            'before': ll_initial, 'after': {p: sha(ll / p) for p in ll_initial}})
        legacy = scratch / 'legacy'
        legacy.mkdir()
        replay.run([compiler, 'new', 'reader', 'tiny'], 'legacy-scaffold', legacy)
        result = replay.run([compiler, 'read', 'tiny.lang', 'answer.tiny'], 'legacy-read', legacy)
        require(b'(number 42)' in result.stdout and not result.stderr, 'lang new reader changed')
        legacy_before = snapshot(legacy)
        replay.run([compiler, 'new', 'reader', 'tiny'], 'legacy-refusal', legacy, expected=1)
        require(snapshot(legacy) == legacy_before, 'legacy repeat destroyed content')
        require(all(sha(clone / p) == h for p, h in hashes.items()), 'compiler sources changed during project work')
        require(all(sha(project / p) == h for p, h in initial.items()), 'fixture run edited generated source')
        dump(evidence / 'artifacts.json', {'compiler': sha(compiler), 'minted': sha(minted),
             'program': sha(project / 'build/policy'), 'llvm': sha(project / 'build/policy.ll')})
        dump(evidence / 'result.json', {'pass': True, 'head': head, 'observations': len(replay.rows)})
        print('PASS project: ancestry, generation, printed commands, runtime, negatives, edits, collisions, write failure and legacy reader')
        return 0
    except Exception as error:
        dump(evidence / 'result.json', {'pass': False, 'error': str(error)})
        print(f'FAIL: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
