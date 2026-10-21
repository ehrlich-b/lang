#!/usr/bin/env python3
"""M0 boundary: immutable inputs, upstream discovery, zero candidate credit.

Only the reference subcommand executes Zig. Candidate results are never inferred
from an oracle result; a future frontend must supply its own execution receipts.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import struct
import subprocess
import time
import sys
import math

from mode_jobs import supervise

HERE = Path(__file__).resolve().parent
LOCK = json.loads((HERE / 'oracle.lock.json').read_text())
LEX = re.compile(rb'//[^\n]*|\\\\[^\n]*|"(?:[^"\\]|\\.)*"|'
                 rb"'(?:[^'\\]|\\.)*'|[A-Za-z_]\w*|[^\s]", re.S)


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def declarations(source):
    tokens = [(m.group(), m.start()) for m in LEX.finditer(source)
              if not m.group().startswith((b'//', b'\\\\'))]
    out = []
    for i, (token, offset) in enumerate(tokens[:-2]):
        if token != b'test':
            continue
        j, name = i + 1, '<anonymous>'
        if tokens[j][0] == b'@':
            j += 1
        if tokens[j][0] != b'{':
            name = tokens[j][0].decode('utf-8')
            j += 1
        if tokens[j][0] == b'{':
            out.append({'byte_offset': offset, 'line': source.count(b'\n', 0, offset) + 1,
                        'name': name})
    return out


def inventory(source):
    rows = []
    for p in sorted((source / 'test/behavior').rglob('*.zig')):
        file = p.relative_to(source).as_posix()
        for decl in declarations(p.read_bytes()):
            rows.append(dict(decl, file=file, file_sha256=digest(p),
                             direct=p.parent == source / 'test/behavior',
                             id=f"{LOCK['source']['shasum']}:{file}:{decl['byte_offset']}"))
    assert len(rows) == LOCK['recursive_denominator'], len(rows)
    assert sum(r['direct'] for r in rows) == LOCK['direct_denominator']
    return rows


def run(command, log, timeout=180, env=None, cwd=None):
    start = time.monotonic()
    with open(log, 'wb') as f:
        p = subprocess.Popen(list(map(str, command)), stdout=f, stderr=f,
                             start_new_session=True, env=env, cwd=cwd)
        try:
            try:
                code = p.wait(timeout=timeout)
                outcome = 'pass' if code == 0 else 'compile_failure'
            except subprocess.TimeoutExpired:
                code, outcome = None, 'timeout'
        finally:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            p.wait()
    return {'command': list(map(str, command)), 'returncode': code,
            'outcome': outcome, 'seconds': time.monotonic() - start,
            'log': str(log)}


class Runner:
    """The pinned, unmodified test_runner.zig server, little-endian wire ABI.

    stderr goes to a file, never a bounded pipe that can deadlock. A timeout
    kills the process group; each subsequent instance gets a fresh runner.
    """
    def __init__(self, binary, log, timeout):
        self.timeout = timeout
        self.log = open(log, 'ab')
        self.p = subprocess.Popen([str(binary), '--listen=-', '--seed=0'],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=self.log, start_new_session=True)
        self.sel = selectors.DefaultSelector()
        self.sel.register(self.p.stdout, selectors.EVENT_READ)
        try:
            tag, version = self.receive()
            if tag != 0 or version.decode() != LOCK['version']:
                raise ValueError('runner version mismatch')
        except BaseException:
            self.close()
            raise

    def exact(self, n, deadline):
        out = b''
        while len(out) < n:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not self.sel.select(remaining):
                raise TimeoutError('runner deadline')
            block = os.read(self.p.stdout.fileno(), n - len(out))
            if not block:
                raise EOFError(f'runner terminated: {self.p.poll()}')
            out += block
        return out

    def receive(self):
        deadline = time.monotonic() + self.timeout
        tag, size = struct.unpack('<II', self.exact(8, deadline))
        if size > 32 * 1024 * 1024:
            raise ValueError('oversized protocol frame')
        return tag, self.exact(size, deadline)

    def send(self, tag, body=b''):
        self.p.stdin.write(struct.pack('<II', tag, len(body)) + body)
        self.p.stdin.flush()

    def metadata(self):
        self.send(4)
        tag, data = self.receive()
        if tag != 3:
            raise ValueError(f'expected test metadata, got {tag}')
        strings_len, count = struct.unpack_from('<II', data)
        if len(data) != 8 + 8 * count + strings_len:
            raise ValueError('malformed metadata')
        offsets = struct.unpack_from(f'<{count}I', data, 8)
        strings = data[8 + 8 * count:]
        return [strings[o:strings.index(b'\0', o)].decode() for o in offsets]

    def test(self, index):
        start = time.monotonic()
        try:
            self.send(5, struct.pack('<I', index))
            tag, data = self.receive()
            if tag == 5:  # test_started
                tag, data = self.receive()
            if tag != 4 or len(data) != 12:
                raise ValueError('malformed test result')
            actual, flags = struct.unpack('<IQ', data)
            if actual != index or flags & 3 == 3:
                raise ValueError('unexpected test index/status')
            outcome = ['pass', 'assertion_failure', 'skip'][flags & 3]
            if flags >> 3:  # error logs or allocator leaks also fail
                outcome = 'assertion_failure'
            return {'outcome': outcome, 'flags': flags,
                    'seconds': time.monotonic() - start}
        except TimeoutError:
            self.close()
            return {'outcome': 'timeout', 'seconds': time.monotonic() - start}
        except (EOFError, BrokenPipeError):
            self.close()
            return {'outcome': 'runtime_failure', 'seconds': time.monotonic() - start}

    def close(self):
        try:
            os.killpg(self.p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        self.p.wait()
        self.sel.close()
        self.p.stdin.close()
        self.p.stdout.close()
        self.log.close()


def llvm_origins(ir, source, rows):
    """Join runner names to upstream debug locations, never by bare test name.

    Debug info is reference identity evidence only, never executable candidate
    semantics. Ambiguous/missing locations fail closed and cannot earn U credit.
    """
    files, functions = {}, {}
    for line in Path(ir).open():
        m = re.match(r'!(\d+) = !DIFile\(filename: "(.*?)", directory: "(.*?)"', line)
        if m:
            files[m[1]] = (Path(m[3]) / m[2]).resolve()
        m = re.match(r'!\d+ = distinct !DISubprogram\(.*?linkageName: "(.*?)".*?file: !(\d+), line: (\d+)', line)
        if m:
            functions[m[1]] = (m[2], int(m[3]))
    wrapper = source / LOCK['root']
    extra = [dict(d, file=LOCK['root'], direct=False, file_sha256=digest(wrapper),
                  id=f"{LOCK['source']['shasum']}:{LOCK['root']}:{d['byte_offset']}")
             for d in declarations(wrapper.read_bytes())]
    by_location = {}
    for row in rows + extra:
        by_location.setdefault(((source / row['file']).resolve(), row['line']), []).append(row)
    result = {}
    for name, (file_id, line) in functions.items():
        matches = by_location.get((files.get(file_id), line), [])
        if len(matches) == 1:
            result[name] = matches[0]
    return result


def verify_archive(archive, expected, extracted):
    """Verify the archive digest AND every extracted regular file byte-for-byte."""
    import tarfile
    actual = digest(archive)
    if actual != expected['shasum']:
        raise ValueError(f'archive digest mismatch: {archive}')
    files = []
    with tarfile.open(archive) as tar:
        for member in tar:
            if not member.isfile():
                continue
            relative = Path(*Path(member.name).parts[1:])
            if '..' in relative.parts or relative.is_absolute():
                raise ValueError('unsafe archive path')
            contents = tar.extractfile(member).read()
            file_digest = hashlib.sha256(contents).hexdigest()
            if file_digest != digest(extracted / relative):
                raise ValueError(f'extracted file differs: {relative}')
            files.append({'file': relative.as_posix(), 'sha256': file_digest})
    return {'archive_sha256': actual, 'verified_files': len(files), 'files': files}


def negative_cases(compiler, source, work, env, timeout):
    manifest = json.loads((HERE / 'negative-cases.json').read_text())
    results = []
    for mode in manifest['modes']:
        for category in ['compile_rejection', 'checked_safety']:
            for file in manifest[category]:
                case = source / file
                case_id = hashlib.sha256(file.encode()).hexdigest()[:16] + '-' + mode
                binary = work / case_id
                command = [compiler, 'build-obj' if category == 'compile_rejection' else 'build-exe',
                           case, '-target', LOCK['target'], '-mcpu=' + LOCK['cpu'], '-O', mode,
                           LOCK['backend_flag'], '--cache-dir', work / 'local-cache',
                           '-femit-bin=' + str(binary)]
                result = run(command, work / f'{case_id}-compile.txt', timeout, env)
                success = result['outcome'] == 'compile_failure' if category == 'compile_rejection' else False
                receipt = {'file': file, 'file_sha256': digest(case), 'category': category,
                           'mode': mode, 'compile': result, 'upstream_credit': 0}
                if category == 'checked_safety' and result['outcome'] == 'pass':
                    # These upstream programs have their own panic handler:
                    # exit 0 proves the expected trap was observed; falling
                    # through the arithmetic produces error.TestFailed.
                    receipt['execution'] = run([binary], work / f'{case_id}-run.txt', 10, env)
                    success = receipt['execution']['outcome'] == 'pass'
                receipt['expected_category_observed'] = success
                results.append(receipt)
    save(work / 'negative-safety.json', results)
    return results


def mode_worker(args):
    work, source, compiler, mode = args.work.resolve(), args.source.resolve(), args.compiler.resolve(), args.mode
    env = dict(os.environ, ZIG_GLOBAL_CACHE_DIR=str(work / 'global-cache'), TMPDIR=str(work))
    rows = json.loads(args.declarations.read_text())
    binary, ir = work / f'behavior-{mode}', work / f'behavior-{mode}.ll'
    branch = run([compiler, 'test', HERE / 'fixtures/backend.zig',
                  '-target', LOCK['target'], '-mcpu=' + LOCK['cpu'], '-O', mode,
                  LOCK['backend_flag'], '--cache-dir', work / 'local-cache',
                  '--test-no-exec', '-femit-bin=' + str(work / f'backend-{mode}')],
                 work / f'backend-{mode}.txt', args.compile_timeout, env)
    if branch['outcome'] != 'pass':
        raise ValueError('builtin.zig_backend compatibility branch proof failed')
    command = [compiler, 'test', source / LOCK['root'], '-target', LOCK['target'],
               '-mcpu=' + LOCK['cpu'], '-O', mode, LOCK['backend_flag'],
               '--cache-dir', work / 'local-cache', '--test-no-exec',
               '-femit-bin=' + str(binary), '-femit-llvm-ir=' + str(ir)]
    compile_result = run(command, work / f'compile-{mode}.txt', args.compile_timeout, env)
    receipt = {'mode': mode, 'compile': compile_result, 'backend_proof': branch, 'instances': []}
    if compile_result['outcome'] != 'pass':
        save(work / 'raw.json', receipt)
        return
    origins = llvm_origins(ir, source, rows)
    runner = Runner(binary, work / f'run-{mode}.txt', args.test_timeout)
    try:
        names = runner.metadata()
        save(work / f'discovered-{mode}.json', names)
        occurrence = Counter()
        for index, name in enumerate(names):
            occurrence[name] += 1
            instance = f'{name}#{occurrence[name]}'
            item = {'index': index, 'name': name, 'instance': instance,
                    'declaration_id': None, 'id': None}
            if runner.p.poll() is not None:
                runner.close()
                runner = Runner(binary, work / f'run-{mode}.txt', args.test_timeout)
                if runner.metadata() != names:
                    raise ValueError('discovery changed after restart')
            item.update(runner.test(index))
            receipt['instances'].append(item)
    finally:
        runner.close()
    receipt['outcomes'] = dict(Counter(i['outcome'] for i in receipt['instances']))
    receipt['binary_sha256'] = digest(binary)
    receipt['llvm_ir_sha256'] = digest(ir)
    # P contains ONLY reference-supported instances. The full discovery list,
    # including skips, remains published. No candidate result is claimed.
    save(work / 'raw.json', dict(receipt, names=names, origins=origins))


def reference(args):
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    source, compiler = args.source.resolve(), args.compiler.resolve()
    identity = {'source': verify_archive(args.source_archive, LOCK['source'], source),
                'compiler': verify_archive(args.compiler_archive, LOCK['compiler_archive'], compiler.parent),
                'executable_sha256': digest(compiler)}
    # Do not accept a substituted runner or testing helper, even with a valid compiler.
    for relative in ['std/testing.zig', 'compiler/test_runner.zig']:
        if digest(source / 'lib' / relative) != digest(compiler.parent / 'lib' / relative):
            raise ValueError(f'source/compiler library mismatch: {relative}')
    env = dict(os.environ, ZIG_GLOBAL_CACHE_DIR=str(work / 'global-cache'),
               TMPDIR=str(work))
    version = subprocess.check_output([str(compiler), 'version'], env=env, text=True).strip()
    if version != LOCK['version']:
        raise ValueError(f'compiler version mismatch: {version}')
    help_text = subprocess.check_output([str(compiler), 'test', '--help'], env=env, text=True)
    (work / 'cli.txt').write_text(help_text)
    for spelling in LOCK['modes']:
        if not re.search(r'^\s+' + spelling + r'\s', help_text, re.M):
            raise ValueError(f'CLI does not document {spelling}')
    save(work / 'identity.json', dict(identity, version=version, profile=LOCK))
    rows = inventory(source)
    save(work / 'declarations.json', rows)
    commands = []
    for mode in LOCK['modes']:
        commands.append((mode, [sys.executable, '-B', Path(__file__).resolve(), '_mode',
                               '--mode', mode, '--source', source, '--compiler', compiler,
                               '--declarations', work / 'declarations.json',
                               '--work', work / mode, '--compile-timeout', args.compile_timeout,
                               '--test-timeout', args.test_timeout]))
    resources = None
    if args.mode_jobs > 1 or args.bounded:
        resources = supervise(commands, args.mode_jobs, work, memory_mib=args.memory_mib,
                              cpus=args.cpus, processes=args.process_limit, timeout=args.mode_timeout)
    else:
        # Preserve serial per-compile/per-instance budgets without a whole-mode
        # deadline or inherited CPU/resource restrictions.
        for mode in LOCK['modes']:
            folder = work / mode
            folder.mkdir(exist_ok=True)
            mode_worker(argparse.Namespace(**(vars(args) | {
                'mode': mode, 'work': folder, 'declarations': work / 'declarations.json'})))
    receipts = []
    canonical_names, canonical_origins = None, {}
    for mode in LOCK['modes']:
        raw = json.loads((work / mode / 'raw.json').read_text())
        names, origins = raw.pop('names', []), raw.pop('origins', {})
        if mode == 'debug':
            canonical_names, canonical_origins = names, origins
        elif raw['compile']['outcome'] == 'pass' and names != canonical_names:
            raise ValueError('mode discovery differs; qualify origins before freezing')
        origins = canonical_origins | origins
        if any(name not in origins for name in names):
            raise ValueError('discovered instance has no unique source declaration')
        for item in raw['instances']:
            origin = origins[item['name']]
            item.update(declaration_id=origin['id'], id=f"{origin['id']}:{item['instance']}")
        if raw['compile']['outcome'] == 'pass':
            raw['P'] = {'candidate_passes': 0,
                        'reference_supported': sum(i['outcome'] == 'pass' for i in raw['instances']),
                        'candidate_status': 'not_implemented'}
        save(work / f'discovered-{mode}.json', names)
        save(work / f'{mode}.json', raw)
        receipts.append(raw)
    summary = {'identity': identity, 'profile': LOCK,
               'U': {'candidate_passes': 0, 'denominator': 2137},
               'U_recursive': {'candidate_passes': 0, 'denominator': 2239},
               'candidate_status': 'not_implemented', 'upstream_passes_claimed': False,
               'modes': receipts}
    summary['resources'] = resources
    summary['generated_builtin_inputs'] = [
        {'file': str(p.relative_to(work)), 'sha256': digest(p)}
        for p in sorted(work.glob('*/global-cache/b/*/builtin.zig'))]
    coverage = []
    for row in rows:
        reached = {r['mode']: [{'id': i['id'], 'reference_outcome': i['outcome']}
                               for i in r['instances'] if i['declaration_id'] == row['id']]
                   for r in receipts}
        coverage.append(dict(row, modes=reached, candidate_outcome='not_implemented'))
    save(work / 'coverage.json', coverage)
    summary['negative_safety'] = negative_cases(compiler, source, work, env, args.compile_timeout)
    save(args.receipt, summary)
    if any(not r['expected_category_observed'] for r in summary['negative_safety']):
        raise SystemExit('reference negative/safety case failed')
    if any(r['compile']['outcome'] != 'pass' or any(
            i['outcome'] not in ('pass', 'skip') for i in r['instances']) for r in receipts):
        raise SystemExit('reference profile has failures; receipt is incomplete')


def selftest(args):
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, ZIG_GLOBAL_CACHE_DIR=str(work / 'global-cache'), TMPDIR=str(work))
    receipts = []
    for name, expected in [('pass', 'pass'), ('assertion', 'assertion_failure'),
                           ('compile', 'compile_failure'), ('timeout', 'timeout'),
                           ('skip', 'skip'), ('safety', 'runtime_failure')]:
        binary = work / name
        result = run([args.compiler.resolve(), 'test', HERE / 'fixtures' / f'{name}.zig',
                      '-target', LOCK['target'], '-O', 'debug', LOCK['backend_flag'],
                      '--cache-dir', work / 'local-cache', '--test-no-exec',
                      '-femit-bin=' + str(binary)], work / f'{name}-compile.txt', 180, env)
        if result['outcome'] == 'pass':
            runner = Runner(binary, work / f'{name}-run.txt', 0.5)
            try:
                names = runner.metadata()
                if len(names) != 1:
                    raise ValueError('selftest discovery must find exactly one test')
                result = runner.test(0)
            finally:
                runner.close()
        receipts.append({'fixture': name, 'expected': expected, 'actual': result})
    save(args.receipt, {'upstream_credit': 0, 'cases': receipts})
    if any(r['expected'] != r['actual']['outcome'] for r in receipts):
        raise SystemExit('harness fault detection failed')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    ref = sub.add_parser('reference')
    for name in ['source', 'source-archive', 'compiler-archive']:
        ref.add_argument('--' + name, type=Path, required=True)
    ref.add_argument('--compile-timeout', type=float, default=240)
    ref.add_argument('--test-timeout', type=float, default=10)
    ref.add_argument('--bounded', action='store_true', help='also supervise serial replay with resource and whole-mode limits')
    ref.add_argument('--mode-jobs', type=int, choices=range(1, 4), default=1)
    ref.add_argument('--cpus', type=int, choices=range(1, 17), default=4)
    ref.add_argument('--memory-mib', type=int, choices=range(256, 32769), metavar='MIB', default=12288)
    ref.add_argument('--process-limit', type=int, choices=range(4, 257), metavar='COUNT', default=128)
    ref.add_argument('--mode-timeout', type=float, default=600)
    worker = sub.add_parser('_mode', help=argparse.SUPPRESS)
    worker.add_argument('--mode', choices=LOCK['modes'], required=True)
    worker.add_argument('--declarations', type=Path, required=True)
    worker.add_argument('--source', type=Path, required=True)
    worker.add_argument('--compiler', type=Path, required=True)
    worker.add_argument('--work', type=Path, required=True)
    worker.add_argument('--compile-timeout', type=float, required=True)
    worker.add_argument('--test-timeout', type=float, required=True)
    for command in [ref, sub.add_parser('selftest')]:
        command.add_argument('--compiler', type=Path, required=True)
        command.add_argument('--work', type=Path, required=True)
        command.add_argument('--receipt', type=Path, required=True)
    args = p.parse_args()
    for name in ('compile_timeout', 'test_timeout', 'mode_timeout'):
        value = getattr(args, name, 1)
        if not math.isfinite(value) or value <= 0:
            p.error(name.replace('_', '-') + ' must be finite and positive')
    {'reference': reference, 'selftest': selftest, '_mode': mode_worker}[args.command](args)


if __name__ == '__main__':
    def cancelled(signum, frame):
        raise KeyboardInterrupt('oracle cancelled')
    for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT):
        signal.signal(sig, cancelled)
    main()
