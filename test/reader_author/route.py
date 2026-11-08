#!/usr/bin/env python3
"""Replay the shipping README in a fresh committed clone, with external receipts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shlex
import shutil
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


class Replay:
    def __init__(self, evidence, scratch):
        self.evidence = evidence
        self.scratch = scratch
        self.rows = []
        self.env = dict(os.environ, JOBS='2', LANGBE='llvm', LANGOS='linux',
                        LANG_CACHE=str(scratch / 'cache'), TMPDIR=str(scratch / 'tmp'))
        (scratch / 'tmp').mkdir()

    def run(self, command, name, cwd, expected=0):
        index = len(self.rows) + 1
        prefix = self.evidence / f'{index:03d}-{name}'
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        start = time.perf_counter()
        result = subprocess.run(command, cwd=cwd, env=self.env, capture_output=True, timeout=240)
        wall = time.perf_counter() - start
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        row = {'name': name, 'command': command, 'cwd': str(cwd),
               'environment': {k: self.env[k] for k in ('JOBS', 'LANGBE', 'LANGOS', 'LANG_CACHE', 'TMPDIR',
                                                                      'LANG_INSPECT_STAGE') if k in self.env},
               'exit': result.returncode, 'wall_seconds': wall,
               'cpu_user_seconds': after.ru_utime - before.ru_utime,
               'cpu_system_seconds': after.ru_stime - before.ru_stime,
               'stdout': prefix.name + '.stdout', 'stderr': prefix.name + '.stderr'}
        prefix.with_suffix('.stdout').write_bytes(result.stdout)
        prefix.with_suffix('.stderr').write_bytes(result.stderr)
        dump(prefix.with_suffix('.json'), row)
        self.rows.append(row)
        dump(self.evidence / 'stages.json', self.rows)
        require(result.returncode == expected,
                f'{name}: expected exit {expected}, got {result.returncode}; see {prefix}.stderr')
        return result

    def shell(self, line, name, cwd, expected=0):
        return self.run(['bash', '-euo', 'pipefail', '-c', line], name, cwd, expected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['shipping'], required=True)
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    # All stages are sequential; affinity is inherited by compiler/linker children.
    os.nice(10)
    cpus = sorted(os.sched_getaffinity(0))[:2]
    os.sched_setaffinity(0, cpus)
    ceiling = 2 * 1024**3
    old_limit = resource.getrlimit(resource.RLIMIT_AS)[1]
    if old_limit != resource.RLIM_INFINITY:
        ceiling = min(ceiling, old_limit)
    resource.setrlimit(resource.RLIMIT_AS, (ceiling, ceiling))
    token = uuid.uuid4().hex
    evidence = (args.evidence or ROOT.parent / 'evidence' / ('shipping-' + token)).resolve()
    require(evidence != ROOT and ROOT not in evidence.parents, 'evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=False)
    scratch = ROOT.parent / 'scratch' / ('shipping-' + token)
    scratch.mkdir(parents=True)
    replay = Replay(evidence, scratch)
    print(f'evidence: {evidence}', flush=True)
    try:
        status = replay.run(['git', 'status', '--porcelain', '--untracked-files=all'], 'clean', ROOT)
        require(not status.stdout, 'commit the candidate before replaying it')
        head = replay.run(['git', 'rev-parse', 'HEAD'], 'head', ROOT).stdout.decode().strip()
        clone = scratch / 'repo'
        replay.run(['git', 'clone', '--no-hardlinks', '--quiet', str(ROOT), str(clone)], 'clone', ROOT)
        files = replay.run(['git', 'ls-files', '-z'], 'inputs', clone).stdout.decode().split('\0')
        hashes = {p: sha(clone / p) for p in files if p and (clone / p).is_file()}
        tools = {}
        for name in ('bash', 'make', 'clang', 'ld', 'python3', 'git'):
            path = Path(shutil.which(name)).resolve()
            tools[name] = {'path': str(path), 'sha256': sha(path)}
        authored = ['example/shipping/shipping.lang', 'example/shipping/runtime.lang']
        dump(evidence / 'identity.json', {'head': head, 'source_sha256': hashes, 'tools': tools,
             'authored_lines': {p: len((clone / p).read_text().splitlines()) for p in authored},
             'limits': {'cpus': cpus, 'address_space_bytes': ceiling, 'JOBS': 2},
             'assumptions': 'Linux x86-64 libc; base 10, inclusive free_over 100; whole units; no OS kernel operations; machine timings only'})
        doc = (clone / 'example/shipping/README.md').read_text()
        blocks = re.findall(r'<!-- shipping-walkthrough -->\s*\n```bash\n(.*?)```', doc, re.S)
        require(len(blocks) == 1, 'README must mark exactly one complete executable walkthrough')
        cwd = clone
        run_number = 0
        for index, raw in enumerate(blocks[0].splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('cd '):
                cwd = (cwd / shlex.split(line)[1]).resolve()
                require(cwd.is_dir() and clone in cwd.parents, f'invalid README directory: {cwd}')
                continue
            # Each command is a complete shell line; exports persist in replay.env.
            if line.startswith('export '):
                replay.env.update(part.split('=', 1) for part in shlex.split(line)[1:])
            if line.startswith('PATH=/nonexistent '):
                require(sorted(p.name for p in cwd.iterdir()) == ['policy.shipping', 'shippingc'],
                        'isolated directory must contain only binary and guest source before IR')
                dump(evidence / 'isolation.json', {'files': {p.name: sha(p) for p in cwd.iterdir()},
                     'PATH': '/nonexistent', 'compiler_tools_available': [], 'command': line})
            result = replay.shell(line, f'readme-{index:02d}', cwd)
            if line == './exclusive 100':
                require(result.stdout == b'10\n' and not result.stderr, 'exclusive edit did not change boundary')
            if line.startswith('./shipping '):
                expected = [b'10\n', b'10\n', b'10\n', b'0\n', b'0\n'][run_number]
                require(result.stdout == expected and not result.stderr, f'wrong exact runtime output: {line}')
                run_number += 1
        require(run_number == 5, 'README must run all five inputs')
        work = clone / 'out/shipping-work'
        ast = (work / 'policy.ast').read_text()
        exclusive = (work / 'exclusive.ast').read_text()
        require(re.search(r'\(binop >=\s+\(ident total\)\s+\(number 100\)', ast), 'AST must compare variable total >= 100')
        require(re.search(r'\(binop >\s+\(ident total\)\s+\(number 100\)', exclusive), 'edited AST must compare variable total > 100')
        for name in ('policy.ast', 'exclusive.ast'):
            shutil.copyfile(work / name, evidence / name)
        compiler = clone / 'out/lang'
        isolated = work / 'isolated'
        minted = isolated / 'shippingc'
        # Reordered settings preserve the AST, not just the sample answers.
        result = replay.run([str(compiler), 'read', str(work / 'shipping.lang'),
                  'example/shipping/reordered.shipping'], 'reordered', clone)
        reordered = result.stdout.decode()
        # Spans naturally differ with source layout; compare only the core nodes.
        normalize = lambda text: re.sub(r'\(span\s+\d+\s+\d+\s+', '(span ', text)
        require(normalize(reordered) == normalize(ast), 'reordered settings changed emitted policy')
        diagnostics = {'duplicate': 'duplicate setting', 'unknown': 'unknown setting',
                       'missing': 'missing setting', 'range': 'decimal integer in 0..1000000'}
        for name, message in diagnostics.items():
            result = replay.run([str(minted), str(clone / f'example/shipping/invalid/{name}.shipping'),
                        '-o', str(scratch / (name + '.ll'))], name, isolated, expected=1)
            require(message.encode() in result.stderr and re.search(rb'shipping:\d+:\d+:', result.stderr),
                    f'{name}: missing located semantic diagnostic')
        cases = {
            'negative': ('shipping { base -1; free_over 100; }', 'decimal integer'),
            'fraction': ('shipping { base 1.5; free_over 100; }', "expected ';'"),
            'overflow': ('shipping { base 99999999999999999999999; free_over 100; }', 'decimal integer'),
            'hex': ('shipping { base 0x10; free_over 100; }', "expected ';'"),
            'trailing': ('shipping { base 10; free_over 100; } junk', 'end of input'),
            'unclosed': ('shipping { base 10; free_over 100; } /*', '*/'),
            'empty': ('shipping {}', 'missing setting'),
            'syntax': ('shipping { base 10 free_over 100; }', 'expected'),
        }
        for name, (source, message) in cases.items():
            path = scratch / (name + '.shipping')
            path.write_text(source)
            shutil.copyfile(path, evidence / path.name)
            result = replay.run([str(minted), str(path), '-o', str(scratch / (name + '.ll'))],
                                name, isolated, expected=1)
            require(message.encode() in result.stderr, f'{name}: missing expected diagnostic')
        # A changed policy must change both constants, preventing a canned 10/100 implementation.
        custom = scratch / 'custom.shipping'
        custom.write_text('shipping { free_over 00080; base 00007; }')
        shutil.copyfile(custom, evidence / custom.name)
        replay.run([str(minted), str(custom), '-o', str(scratch / 'custom.ll')], 'custom-llvm', isolated)
        replay.run(['clang', str(scratch / 'custom.ll'), '-o', str(scratch / 'custom')], 'custom-link', isolated)
        for total, expected in [('79', b'7\n'), ('80', b'0\n'), ('81', b'0\n')]:
            result = replay.run([str(scratch / 'custom'), total], 'custom-' + total, isolated)
            require(result.stdout == expected and not result.stderr, 'changed policy constants ignored')
        for index, arguments in enumerate([[], ['-1'], ['1.5'], ['abc'], ['1000001'], ['9999999999999999999999'], [''], ['0', '1']]):
            result = replay.run([str(isolated / 'shipping'), *arguments], f'bad-input-{index}', isolated, expected=64)
            require(not result.stdout and b'shipping:' in result.stderr, 'invalid runtime input accepted')
        for total in ('00080', '1000000'):
            result = replay.run([str(isolated / 'shipping'), total], 'valid-input-' + total, isolated)
            require(result.stdout == (b'10\n' if total == '00080' else b'0\n') and not result.stderr,
                    'valid runtime boundary failed')
        shutil.copyfile(isolated / 'policy.ll', evidence / 'policy.ll')
        dump(evidence / 'artifacts.json', {str(p.relative_to(clone)): sha(p) for p in
             (compiler, minted, isolated / 'policy.ll', isolated / 'shipping')})
        dump(evidence / 'result.json', {'pass': True, 'observations': len(replay.rows), 'head': head})
        print('PASS shipping: README, reader edit, shared AST, isolated minted compiler, diagnostics and runtime inputs')
        return 0
    except Exception as error:
        dump(evidence / 'result.json', {'pass': False, 'error': str(error)})
        print(f'FAIL: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
