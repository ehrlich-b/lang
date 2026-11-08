#!/usr/bin/env python3
"""Exercise versioned SDK acceptance using real archives and native programs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time

from sdk_isolation import isolate

ROOT = Path(__file__).resolve().parents[1]
BASE = 'dc228a8a74f9c1fa63cf82915afc5d2a0d4d3d5c'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


class Check:
    def __init__(self, args):
        self.evidence = args.evidence.resolve()
        self.scratch = args.scratch.resolve()
        self.tools = args.tools.resolve()
        assert not self.evidence.is_relative_to(ROOT) and not self.scratch.is_relative_to(ROOT)
        self.evidence.mkdir(parents=True, exist_ok=True)
        self.scratch.mkdir(parents=True, exist_ok=True)
        self.work = Path(tempfile.mkdtemp(prefix='sdk-proof-', dir=self.scratch))
        self.head = git('rev-parse', 'HEAD')
        self.env = {k: v for k, v in os.environ.items() if not k.startswith('LANG') and k != 'VERIFY_CASE'}
        self.env.update(PATH=str(self.tools / 'llvm/bin') + ':/usr/bin:/bin',
                        LANGBE='llvm', LANGOS='linux', TMPDIR=str(self.work),
                        PYTHONDONTWRITEBYTECODE='1', HOME=str(self.work))
        self.rows = []

    def call(self, args, *, cwd=None, expected=0, isolated=False, env=None, output=None):
        args = [str(a) for a in args]
        cwd = cwd or self.work
        start = time.perf_counter()
        preexec = None
        if isolated:
            preexec = lambda: isolate([self.work, '/dev'],
                                     ['/usr', '/bin', '/lib', '/lib64', '/etc', '/proc', self.tools])
        result = subprocess.run(args, cwd=cwd, env=env or self.env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                preexec_fn=preexec, timeout=180)
        row = dict(command=args, cwd=str(cwd), exit_code=result.returncode,
                   seconds=time.perf_counter() - start, isolated=isolated,
                   stdout=result.stdout.decode(errors='replace'), stderr=result.stderr.decode(errors='replace'))
        self.rows.append(row)
        if output:
            output.write_bytes(result.stdout)
            row.update(output=str(output), output_sha256=sha(output))
        print(json.dumps(row), flush=True)
        assert result.returncode == expected, row
        return result

    def write(self, name, **extra):
        path = self.evidence / name
        path.write_text(json.dumps(dict(version=1, head=self.head, host=platform.node(),
                                        commands=self.rows, **extra), indent=2) + '\n')
        print(path)

    def package(self):
        outputs = []
        for name in ('one', 'two'):
            out = self.work / name
            self.call([sys.executable, ROOT / 'scripts/package_sdk.py', '--output', out])
            archive, = out.glob('*.tar.xz')
            receipt, = out.glob('*.receipt.json')
            data = json.loads(receipt.read_text())
            assert data['commit'] == self.head and data['tools']['clang'].startswith('clang version 23.1.5')
            assert data['archive']['sha256'] == sha(archive)
            assert data['archive']['bytes'] == archive.stat().st_size
            outputs.append((archive, receipt))
        assert outputs[0][0].read_bytes() == outputs[1][0].read_bytes(), 'archives differ'
        target = self.evidence / 'sdk-artifacts' / self.head
        target.mkdir(parents=True, exist_ok=True)
        # Retain one release archive and both receipts, never the source snapshots.
        saved = target / outputs[0][0].name
        if saved.exists():
            assert saved.read_bytes() == outputs[0][0].read_bytes()
        else:
            shutil.copyfile(outputs[0][0], saved)
        for i, (archive, receipt) in enumerate(outputs, 1):
            shutil.copyfile(receipt, target / f'build-{i}.receipt.json')
            log, = receipt.parent.glob('*.build.log')
            shutil.copyfile(log, target / f'build-{i}.log')
        self.write('sdk-package.json', archive=str(saved), sha256=sha(saved),
                   byte_identical=True, receipt_directory=str(target))

    def extract(self):
        package = json.loads((self.evidence / 'sdk-package.json').read_text())
        assert package['head'] == self.head
        archive = Path(package['archive'])
        assert sha(archive) == package['sha256']
        self.call(['/usr/bin/tar', '-xJf', archive, '-C', self.work])
        sdk, = self.work.glob('lang-*-x86_64-linux')
        with tarfile.open(archive) as tar:
            assert not any('/bootstrap/' in m.name or '/.git/' in m.name for m in tar)
        data = json.loads((sdk / 'sdk.json').read_text())
        assert data['commit'] == self.head
        for p, meta in data['files'].items():
            assert sha(sdk / p) == meta['sha256'], p
            assert (sdk / p).stat().st_size == meta['bytes']
        self.env['PATH'] = str(sdk / 'bin') + ':' + self.env['PATH']
        return sdk

    def journey(self, missing=False):
        sdk = self.extract()
        consumer = self.work / 'stranger'
        consumer.mkdir()
        # The checkout is invisible to all consumer subprocesses. Prove the
        # boundary with actual failed opens, including the preserved seed.
        for forbidden in (ROOT / 'README.md', ROOT / 'bootstrap/current/compiler_linux.ll'):
            self.call([sys.executable, '-c',
                       'import sys; open(sys.argv[1]).read()', forbidden],
                      cwd=consumer, expected=1, isolated=True)
            assert 'PermissionError' in self.rows[-1]['stderr']
        self.call(['lang', 'new', 'reader', 'tiny'], cwd=consumer, isolated=True)
        if missing:
            no_tools = dict(self.env, PATH=str(sdk / 'bin'))
            for command in (['lang', 'compiler', 'tiny', 'tiny.lang', '-o', 'tinyc'],
                            ['lang', 'run', 'tiny.lang', 'answer.tiny']):
                result = self.call(command, cwd=consumer, isolated=True, env=no_tools, expected=127)
                message = result.stderr.decode()
                assert len(message.splitlines()) == 1 and 'clang' in message and 'apt install' in message
                assert not result.stdout
            assert not (consumer / 'tinyc').exists()
            self.write('sdk-missing-tools.json', status='PASS')
            return
        self.call(['lang', 'compiler', 'tiny', 'tiny.lang', '-o', 'tinyc'], cwd=consumer, isolated=True)
        self.call(['./tinyc', 'answer.tiny', '-o', 'answer.ll'], cwd=consumer, isolated=True)
        self.call(['clang', '-O2', 'answer.ll', '-o', 'answer'], cwd=consumer, isolated=True)
        self.call(['./answer'], cwd=consumer, isolated=True, expected=42)
        # Reproduce the comparison frontend unchanged, using only packaged inputs.
        source = sdk / 'examples/dsl-compare'
        self.call(['lang', 'std/core.lang', source / 'lang/tariff.lang', '-o', 'tariff.ll'], cwd=consumer, isolated=True)
        self.call(['clang', '-O2', 'tariff.ll', '-o', 'tariff'], cwd=consumer, isolated=True)
        self.call(['./tariff', source / 'fixtures/benchmark.tariff'], cwd=consumer, isolated=True,
                  output=consumer / 'program.ast')
        self.call(['lang', '--from-ast', 'program.ast', '--ast-source', source / 'fixtures/benchmark.tariff',
                   '-o', 'program.ll'], cwd=consumer, isolated=True)
        self.call(['clang', '-O2', 'program.ll', source / 'harness.c', '-o', 'program'], cwd=consumer, isolated=True)
        result = self.call(['./program', '2000000'], cwd=consumer, isolated=True)
        assert result.stdout == b'6000002995045\n'
        self.write('sdk-journey.json', status='PASS', archive_sha256=sha(Path(json.loads(
            (self.evidence / 'sdk-package.json').read_text())['archive'])),
                   isolation='Landlock: source checkout and seed inaccessible to consumer and all descendants; system tools, SDK and empty consumer directory allowed',
                   qualification='The checkout remains on the host disk, outside the consumer filesystem access boundary; no privileged namespace or root used.')

    def compare(self):
        sdk = self.extract()
        self.call([sys.executable, ROOT / 'examples/dsl-compare/run.py', '--tools', self.tools,
                   '--sdk', sdk, '--report', self.evidence / 'compare.json'])
        self.call([sys.executable, ROOT / 'examples/dsl-compare/check.py', 'report', '--relocate',
                   '--report', self.evidence / 'compare.json'])
        report = json.loads((self.evidence / 'compare.json').read_text())
        print(json.dumps({arm: row['clean_to_binary_seconds'] for arm, row in report['arms'].items()}))
        self.write('sdk-comparison.json', status='PASS', target_seconds=2,
                   target_met=report['arms']['lang-sdk']['clean_to_binary_seconds'] < 2)

    def policy(self):
        self.call(['git', 'merge-base', '--is-ancestor', BASE, 'HEAD'], cwd=ROOT)
        assert platform.node() != 'forge', 'compiler gate blocked on exactly forge'
        assert os.geteuid() != 0, 'run without root'
        commits = git('log', '--format=%an <%ae>|%cn <%ce>|%s', BASE + '..HEAD').splitlines()
        identity = 'Bryan Ehrlich <ehrlich.bryan@gmail.com>'
        assert commits
        for line in commits:
            author, committer, subject = line.split('|', 2)
            assert author == committer == identity and subject.endswith('.'), line
        assert not git('status', '--porcelain')
        self.write('sdk-policy.json', status='PASS', base=BASE, commits=commits,
                   decisions='Native Linux SDK; use existing resource discovery; no kernel or limits changes; no publication; Landlock consumer isolation avoids namespace root.')

    def docs(self):
        readme = (ROOT / 'README.md').read_text()
        sdk = (ROOT / 'docs/SDK.md').read_text()
        comparison = (ROOT / 'docs/compare-yacc-antlr.md').read_text()
        assert readme.index('tar -xJf') < readme.index('git clone')
        for phrase in ('no public download', 'Clang', 'system C development toolchain', 'Second path'):
            assert phrase in readme, phrase
        for phrase in ('glibc', '23.1.5', 'SHA-256', 'PATH', 'bootstrap seed'):
            assert phrase in sdk, phrase
        assert 'Lang SDK' in comparison and '9.596' in comparison
        self.write('sdk-docs.json', status='PASS', files={p: sha(ROOT / p) for p in
                   ('README.md', 'docs/SDK.md', 'docs/compare-yacc-antlr.md')})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', choices=('package', 'journey', 'missing', 'compare', 'policy', 'docs'))
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--tools', type=Path, required=True)
    args = parser.parse_args()
    check = Check(args)
    if args.case == 'missing':
        check.journey(missing=True)
    else:
        getattr(check, args.case)()


if __name__ == '__main__':
    main()
