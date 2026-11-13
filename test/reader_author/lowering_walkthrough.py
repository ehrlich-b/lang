#!/usr/bin/env python3
"""Retain and replay six observations through the existing shipping reader."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import uuid

BASE = 'e148de1e1a3bb1a229f3a8369e41e4b0241783e3'
INPUT_HEAD = '209e4ca1e12a643102e37b58b6e43fe7ce4c5eaf'
KIND = 'lowering-walkthrough'
CASES = ('guest-source', 'grammar-capture', 'shared-ast', 'runtime-link',
         'native-result', 'located-error')
SOURCES = ('example/shipping/policy.shipping', 'example/shipping/shipping.lang',
           'example/shipping/runtime.lang', 'example/shipping/exports.lang',
           'example/shipping/project.lang-project',
           'example/shipping/invalid/unknown.shipping')
PM_SOURCES = ('lang/harbor.lang', 'lang/sample.conf',
              'trial1/fixtures/missing-equals.conf')


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def local(base, name):
    path = (base / name).resolve()
    require(not Path(name).is_absolute() and path.is_relative_to(base.resolve())
            and path.is_file(), 'missing or escaping evidence: ' + name)
    return path


def input_hashes(repo, inputs):
    require(git(inputs, 'rev-parse', 'HEAD').decode().strip() == INPUT_HEAD,
            'wrong frozen input commit')
    require(not git(inputs, 'status', '--porcelain', '--untracked-files=all'),
            'changed frozen inputs')
    manifest = json.loads((inputs / 'MANIFEST.json').read_text())
    for row in manifest:
        require(sha(inputs / row['path']) == row['sha256'], 'changed frozen input: ' + row['path'])
    git(repo, 'merge-base', '--is-ancestor', BASE, 'HEAD')
    require(git(repo, 'cat-file', '-t', BASE + ':test/reader_author/inspect.py') == b'blob\n',
            'missing dispatched inspection anchor')
    hashes = {}
    for name in SOURCES:
        expected = hashlib.sha256(git(repo, 'show', BASE + ':' + name)).hexdigest()
        require(sha(repo / name) == expected, 'changed shipping input: ' + name)
        hashes[name] = expected
    for name in PM_SOURCES + ('MANIFEST.json',):
        hashes['pm-inputs/' + name] = sha(inputs / name)
    return hashes


class Replay:
    def __init__(self, repo, base, scratch, hashes):
        self.repo, self.base, self.rows, self.hashes = repo, base, [], hashes
        self.env = dict(os.environ, JOBS='2', MAKEFLAGS='-j2', LANGBE='llvm', LANGOS='linux',
                        LANG_CACHE=str(scratch / 'cache'), PYTHONDONTWRITEBYTECODE='1')
        for name in ('LANG_ROOT', 'LANG_INSPECT_STAGE', 'VERIFY_CASE'):
            self.env.pop(name, None)

    def run(self, name, argv, expected=0):
        argv = list(map(str, argv))
        result = subprocess.run(['nice', '-n', '10', *argv], cwd=self.repo, env=self.env,
                                capture_output=True, timeout=240)
        stdout, stderr = name + '.stdout', name + '.stderr'
        (self.base / stdout).write_bytes(result.stdout)
        (self.base / stderr).write_bytes(result.stderr)
        row = dict(name=name, command=['nice', '-n', '10', *argv], cwd=str(self.repo),
                   exit_code=result.returncode, expected_exit=expected, stdout=stdout, stderr=stderr,
                   files={stdout: sha(self.base / stdout), stderr: sha(self.base / stderr)},
                   inputs=self.hashes)
        self.rows.append(row)
        (self.base / 'commands.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in self.rows))
        require(result.returncode == expected, name + ': unexpected exit; see ' + stderr)
        return result


def validate(base, repo, inputs):
    trace = json.loads((base / 'trace.json').read_text())
    head = git(repo, 'rev-parse', 'HEAD').decode().strip()
    require(trace['head'] == head and trace['base'] == BASE, 'stale product identity')
    require(trace['inputs'] == input_hashes(repo, inputs), 'changed input identity')
    for name, digest in trace['artifacts'].items():
        require(sha(local(base, name)) == digest, 'changed artifact: ' + name)
    for name in SOURCES:
        require(sha(local(base, 'sources/' + name)) == trace['inputs'][name],
                'changed retained input: ' + name)
    for name in PM_SOURCES + ('MANIFEST.json',):
        require(sha(local(base, 'sources/pm-inputs/' + name)) == trace['inputs']['pm-inputs/' + name],
                'changed retained frozen input: ' + name)
    rows = [json.loads(line) for line in (base / 'commands.jsonl').read_text().splitlines()]
    by_name = {r['name']: r for r in rows}
    require(len(rows) == len(by_name), 'duplicate commands')
    for row in rows:
        require(row['command'] and row['cwd'] == str(repo) and row['inputs'] == trace['inputs'],
                'unbound command')
        require(type(row['exit_code']) is int and row['exit_code'] == row['expected_exit'],
                'false success: command exit')
        for name, digest in row['files'].items():
            require(sha(local(base, name)) == digest, 'changed command evidence: ' + name)
        require(row['stdout'] in row['files'] and row['stderr'] in row['files'], 'missing raw streams')
    require(tuple(trace['observations']) == CASES, 'missing observations')
    for case in trace['observations'].values():
        require(case['claim'] and case['commands'] and case['links'], 'empty observation')
        for name in case['commands']:
            require(name in by_name, 'missing command: ' + name)
        for link in case['links']:
            path, _, line = link.partition('#L')
            source = local(base, path)
            require(path in trace['artifacts'], 'unhashed observation link')
            if line:
                require(0 < int(line) <= len(source.read_text().splitlines()), 'invalid line link')
    doc = (base / 'WALKTHROUGH.md').read_text()
    for link in re.findall(r'\]\(([^)]+)\)', doc):
        path, _, anchor = link.partition('#')
        target = local(base, path)
        if anchor:
            require(anchor.startswith('L') and 0 < int(anchor[1:]) <= len(target.read_text().splitlines()),
                    'invalid document line link')
    require((base / 'guest-source.stdout').read_bytes() == (repo / SOURCES[0]).read_bytes(),
            'source receipt differs')
    tree = (base / 'tree.stdout').read_bytes()
    tokens = (base / 'tokens.stdout').read_bytes()
    source = (repo / SOURCES[0]).read_bytes()
    for value in (b'base', b'10', b'free_over', b'100'):
        start = source.index(value)
        needle = b'"' + value + f'" @{start}:{start + len(value)}'.encode()
        require(needle in tree and needle in tokens, 'lost source byte span')
    require(all(b'capture "' + c + b'"' in tree for c in (b'settings', b'name', b'value')),
            'lost grammar captures')
    core = (base / 'core.stdout').read_bytes()
    require(core == (base / 'read-core.stdout').read_bytes(), 'inspect core differs from reader AST')
    require(all(s in core for s in (b'(span 0 44', b'(func shipping_cost',
            b'(binop >= (ident total) (number 100))', b'(return (number 10))',
            b'(ident shipping_total)', b'(ident shipping_print)')), 'wrong shared AST')
    llvm = (base / 'llvm.stdout').read_bytes()
    require(all(s in llvm for s in (b'define i64 @shipping_cost(', b'define i64 @shipping_total(',
                                  b'define i64 @shipping_print(')), 'missing linked runtime')
    for total, answer in (('99', b'10\n'), ('100', b'0\n'), ('101', b'0\n')):
        row = by_name['native-' + total]
        require(row['command'][-1] == total and row['exit_code'] == 0
                and local(base, row['stdout']).read_bytes() == answer
                and not local(base, row['stderr']).read_bytes(), 'false success: literal native result')
    row = by_name['invalid-core']
    expected = (str(repo / SOURCES[-1]) + ':1:12: unknown setting; expected base or free_over\n').encode()
    require(row['exit_code'] == 1 and not local(base, row['stdout']).read_bytes()
            and local(base, row['stderr']).read_bytes() == expected, 'false success: located error')
    require(not (base / 'invalid-llvm.stdout').read_bytes()
            and (base / 'invalid-llvm.stderr').read_bytes() == expected
            and by_name['invalid-llvm']['exit_code'] == 1, 'invalid source produced LLVM')
    for name in ('tokens', 'tree', 'core', 'read-core', 'llvm'):
        require(not (base / (name + '.stderr')).read_bytes(), 'success artifact has diagnostics')
    return trace, rows


def walkthrough(trace):
    lines = ['# One shipping policy, from syntax to a native result', '',
             'This replays the existing shipping DSL on product commit `' + trace['head'] + '`.',
             'The policy is `shipping { base 10; free_over 100; }`; the comparison is inclusive.', '',
             '| Observation | Exact retained artifacts |', '| --- | --- |']
    for name, case in trace['observations'].items():
        links = ', '.join('[' + p + '](' + p + ')' for p in case['links'])
        lines.append('| ' + name + ': ' + case['claim'] + ' | ' + links + ' |')
    lines += ['', 'The frontend owns setting names, duplicate/missing-setting checks, decimal range',
              'validation, the inclusive threshold, and elaboration into `shipping_cost(total: i64)`.',
              'The grammar accepts a symbol for each name; `tax` therefore parses but the reader',
              'rejects it at byte column 12. The kernel receives explicit functions, integers,',
              'comparison, branches and calls; it gains no shipping-specific rule.', '',
              'Core inspection emits the reader AST, including calls to `shipping_total` and',
              '`shipping_print`. The project explicitly selects `runtime.lang`; LLVM inspection',
              'includes those implementations and `std/core.lang`. The target runtime parses the',
              'CLI argument and prints the fee. Clang and the system linker produce the native',
              'Linux x86-64 executable from that LLVM. Execution still depends on the platform',
              'and libc; native readers are trusted build programs. This is neither a runtime-free',
              'claim nor a bootstrap proof.', '',
              'Reproduce from the checkout root:', '```bash',
              'nice -n 10 python3 -B test/reader_author/lowering_walkthrough.py --replay --repo . --inputs sources/pm-inputs',
              'nice -n 10 python3 -B test/reader_author/lowering_walkthrough.py --selftest --repo . --inputs sources/pm-inputs',
              '```', '',
              'Replay uses `make init`, then `make build`, the existing `inspect` stages, `read`,',
              'Clang, and three tiny native executions. It also requests core and LLVM for the',
              'existing invalid source. These commands run sequentially; no suite is selected.',
              '[Raw argv, exits, stdout/stderr and input hashes](commands.jsonl) accompany',
              '[the source-bound trace](trace.json). Selftest invokes the same validator in three',
              'separate scratch copies: changed retained input, forged native success with updated',
              'hashes, and an omitted error stream. [Mutation receipts](mutations.json) retain each rejection.', '']
    return '\n'.join(lines)


def selftest(base, scratch, repo, inputs, replay):
    receipts = []
    # Copy small evidence, never binaries/build trees; mutant copies remain scratch.
    for mode in ('changed-input', 'false-success', 'missing-evidence'):
        dest = scratch / mode
        def omit(directory, names):
            return ['invalid-core.stderr'] if mode == 'missing-evidence' and Path(directory) == base else []
        shutil.copytree(base, dest, ignore=omit)
        trace = json.loads((dest / 'trace.json').read_text())
        if mode == 'changed-input':
            name = 'sources/' + SOURCES[0]
            (dest / name).write_text('shipping { base 11; free_over 100; }\n')
            trace['artifacts'][name] = sha(dest / name)
        if mode == 'false-success':
            name = 'native-100.stdout'
            (dest / name).write_bytes(b'10\n')
            trace['artifacts'][name] = sha(dest / name)
            rows = [json.loads(line) for line in (dest / 'commands.jsonl').read_text().splitlines()]
            for row in rows:
                if row['name'] == 'native-100':
                    row['files'][name] = sha(dest / name)
            (dest / 'commands.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
        dump(dest / 'trace.json', trace)
        result = replay.run('mutation-' + mode, [sys.executable, '-B', str(base / 'check.py'),
                            '--validate', str(dest), '--repo', repo, '--inputs', inputs], expected=1)
        reason = {'changed-input': 'changed retained input', 'false-success': 'literal native result',
                  'missing-evidence': 'missing or escaping evidence'}[mode]
        require(reason.encode() in result.stderr, 'mutant rejected for the wrong reason: ' + mode)
        receipts.append(dict(mode=mode, copy=str(dest), rejected=True, reason=reason,
                             command='mutation-' + mode))
    dump(base / 'mutations.json', receipts)
    return len(receipts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--replay', action='store_true')
    mode.add_argument('--selftest', action='store_true')
    mode.add_argument('--validate', type=Path)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    repo, inputs = args.repo.resolve(), args.inputs.resolve()
    if args.validate:
        validate(args.validate.resolve(), repo, inputs)
        print('PASS: retained walkthrough validation')
        return 0
    base = (args.evidence or repo.parent / 'evidence' / KIND).resolve()
    require(not base.is_relative_to(repo), 'evidence must be outside checkout')
    base.mkdir(parents=True, exist_ok=True)
    os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:2])
    scratch = repo.parent / 'scratch' / (KIND + '-' + uuid.uuid4().hex)
    scratch.mkdir(parents=True)
    head = git(repo, 'rev-parse', 'HEAD').decode().strip()
    hashes = input_hashes(repo, inputs)
    replay = Replay(repo, base, scratch, hashes)
    checker = repo / 'test/reader_author/lowering_walkthrough.py'
    (base / 'check.py').write_bytes(checker.read_bytes())
    require(git(repo, 'show', head + ':test/reader_author/lowering_walkthrough.py') == checker.read_bytes(),
            'commit the candidate before replay')
    for name in SOURCES:
        dest = base / 'sources' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((repo / name).read_bytes())
    for name in PM_SOURCES + ('MANIFEST.json',):
        dest = base / 'sources/pm-inputs' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((inputs / name).read_bytes())
    replay.run('init', ['make', 'init'])
    replay.run('build', ['make', 'build'])
    replay.run('guest-source', ['git', 'show', head + ':' + SOURCES[0]])
    compiler = repo / 'out/lang_next'
    project = repo / SOURCES[4]
    for stage in ('tokens', 'tree', 'core', 'llvm'):
        replay.run(stage, [compiler, 'inspect', '--project', project, '--stage', stage])
    replay.run('read-core', [compiler, 'read', repo / SOURCES[1], repo / SOURCES[0]])
    # The retained raw LLVM stdout is the exact input to the native linker.
    native = scratch / 'shipping'
    replay.run('link', ['clang', '-x', 'ir', base / 'llvm.stdout', '-o', native])
    for total in ('99', '100', '101'):
        replay.run('native-' + total, [native, total])
    invalid = scratch / 'invalid.lang-project'
    text = project.read_text().replace('"shipping.lang"', json.dumps(str(repo / SOURCES[1])))
    text = text.replace('"runtime.lang"', json.dumps(str(repo / SOURCES[2])))
    text = text.replace('"policy.shipping"', json.dumps(str(repo / SOURCES[-1])))
    invalid.write_text(text)
    (base / 'invalid.lang-project').write_text(text)
    for stage in ('core', 'llvm'):
        replay.run('invalid-' + stage, [compiler, 'inspect', '--project', invalid, '--stage', stage], expected=1)
    tools = {}
    for name in ('python3', 'make', 'clang', 'ld', 'git'):
        path = Path(shutil.which(name)).resolve()
        tools[name] = dict(path=str(path), sha256=sha(path))
    dump(base / 'identity.json', dict(head=head, compiler_sha256=sha(compiler), tools=tools,
         inputs=hashes, cpus=sorted(os.sched_getaffinity(0)), JOBS=2,
         environment={k: replay.env[k] for k in ('LANGBE', 'LANGOS', 'LANG_CACHE', 'MAKEFLAGS')}))
    claims = (
        ('The unchanged source sets base=10 and inclusive free_over=100.', ['guest-source'],
         ['sources/' + SOURCES[0] + '#L1', 'guest-source.stdout']),
        ('The actual grammar captures settings/name/value with half-open byte spans.', ['tokens', 'tree'],
         ['sources/' + SOURCES[1] + '#L5', 'tokens.stdout', 'tree.stdout']),
        ('Constants become a >= comparison and returns; total remains a parameter.', ['core', 'read-core'],
         ['sources/' + SOURCES[1] + '#L65', 'core.stdout', 'read-core.stdout']),
        ('The project runtime supplies argument parsing and printing before Clang links LLVM.', ['llvm', 'link'],
         ['sources/' + SOURCES[4] + '#L6', 'sources/' + SOURCES[2] + '#L3', 'llvm.stdout', 'link.stderr']),
        ('Native totals 99, 100 and 101 print exactly 10, 0 and 0, each with a newline.',
         ['native-99', 'native-100', 'native-101'], ['native-99.stdout', 'native-100.stdout', 'native-101.stdout']),
        ('An unknown setting is rejected at source line 1, byte column 12, with no core or LLVM.',
         ['invalid-core', 'invalid-llvm'], ['sources/' + SOURCES[-1] + '#L1', 'invalid-core.stderr',
                                         'invalid-llvm.stderr', 'invalid.lang-project']))
    observations = {name: dict(claim=claim, commands=commands, links=links)
                    for name, (claim, commands, links) in zip(CASES, claims)}
    files = ['check.py', 'identity.json', 'invalid.lang-project']
    files += ['sources/' + p for p in SOURCES]
    files += ['sources/pm-inputs/' + p for p in PM_SOURCES + ('MANIFEST.json',)]
    files += [p for row in replay.rows for p in row['files']]
    trace = dict(version=1, kind=KIND, head=head, base=BASE, inputs=hashes,
                 observations=observations, artifacts={p: sha(base / p) for p in files})
    dump(base / 'trace.json', trace)
    (base / 'WALKTHROUGH.md').write_text(walkthrough(trace))
    dump(base / 'mutations.json', [])
    validate(base, repo, inputs)
    mutations = selftest(base, scratch, repo, inputs, replay)
    validate(base, repo, inputs)
    cases = {}
    by_name = {r['name']: r for r in replay.rows}
    for name, observation in observations.items():
        rows = [by_name[n] for n in observation['commands']]
        names = {p.split('#')[0] for p in observation['links']}
        names.update(p for row in rows for p in row['files'])
        cases[name] = dict(passed=True, command=' && '.join(shlex.join(r['command']) for r in rows),
                           exit_code=rows[-1]['exit_code'], assertion=observation['claim'],
                           files={p: sha(base / p) for p in sorted(names)})
    dump(base / 'result.json', dict(kind=KIND, head=head, cases=cases, mutation_checks=mutations))
    print('PASS: six shipping observations, literal native results, located rejection, three mutants at ' + head)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print('FAIL: ' + str(error), file=sys.stderr)
        sys.exit(1)
