#!/usr/bin/env python3
"""Replay the public reader guide offline with a hash-pinned released SDK.

Example (all outputs stay outside the checkout):
  python3 test/sdk_reader_quickstart.py --archive /path/to/release.tar.xz \
      --output ../evidence/reader-guide --work-root ../scratch

Only curl's download transport is replaced, with the supplied release bytes.
The shell commands and reader are extracted from web/readers.html verbatim.
No repository compiler, bootstrap seed or source-build step is used.
"""
import argparse
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = 'lang-0.1.0+e5b90e2f0538-x86_64-linux.tar.xz'
SHA256 = '310c6467386ca7f5375b3136d807e3acf7b669bfcd9d740f048f5f6aa80a0424'
URL = 'https://lang.ehrlich.dev/releases/' + ARCHIVE


class Guide(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.blocks = {}
        self.current = None
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        if tag == 'pre':
            self.current = dict(attrs).get('id', 'sample')
            if self.current in self.blocks:
                raise AssertionError('duplicate guide code block: ' + self.current)
            self.blocks[self.current] = ''

    def handle_endtag(self, tag):
        if tag == 'pre':
            self.current = None

    def handle_data(self, data):
        if self.current:
            self.blocks[self.current] += data


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--work-root', type=Path, required=True)
    args = parser.parse_args()
    archive = args.archive.resolve()
    output = args.output.resolve()
    work_root = args.work_root.resolve()
    for path in (output, work_root):
        if path == ROOT or ROOT in path.parents:
            parser.error('outputs must be outside the checkout')
        path.mkdir(parents=True, exist_ok=True)
    assert digest(archive) == SHA256, 'released SDK SHA-256 mismatch'
    guide_path = ROOT / 'web/readers.html'
    guide = Guide(guide_path.read_text())
    blocks = guide.blocks
    sample = blocks['sample']
    assert 'reader tiny(' in sample
    assert URL in blocks['sdk-setup'] and SHA256 in blocks['sdk-setup']
    # A fresh directory and a clean environment exercise quoting and relocation.
    work = Path(tempfile.mkdtemp(prefix='SDK guide with spaces ', dir=work_root))
    assert ' ' in str(work) and not any(work.iterdir())
    controls = Path(tempfile.mkdtemp(prefix='SDK replay controls ', dir=work_root))
    tools = controls / 'transport'
    tools.mkdir()
    home = controls / 'home'
    home.mkdir()
    curl = tools / 'curl'
    curl.write_text('''#!/usr/bin/python3
import os, shutil, sys
from pathlib import Path
expected = ['--fail', '--location', '--output', ''' + repr(ARCHIVE) + ''', ''' + repr(URL) + ''']
if sys.argv[1:] != expected:
    raise SystemExit('Unexpected curl request: ' + repr(sys.argv[1:]))
print('OFFLINE TRANSPORT: copying hash-verified published archive fixture', flush=True)
shutil.copyfile(os.environ['REPLAY_ARCHIVE'], expected[3])
Path(os.environ['REPLAY_REQUEST']).write_text(expected[4] + '\\n')
''')
    curl.chmod(0o755)
    env = dict(HOME=str(home), PATH=str(tools) + ':/usr/bin:/bin',
               TMPDIR=str(controls), LANG_CACHE=str(controls / 'cache'),
               REPLAY_ARCHIVE=str(archive), REPLAY_REQUEST=str(controls / 'request.txt'))
    results = []

    def run(label, command, cwd, expected):
        (output / (label + '.sh')).write_text(command + '\n')
        result = subprocess.run(['/bin/sh', '-eu', '-c', command], cwd=cwd,
                                env=env, capture_output=True, timeout=120)
        (output / (label + '.stdout')).write_bytes(result.stdout)
        (output / (label + '.stderr')).write_bytes(result.stderr)
        results.append(dict(label=label, command=command, cwd=str(cwd),
                            exit_code=result.returncode,
                            stdout_sha256=hashlib.sha256(result.stdout).hexdigest(),
                            stderr_sha256=hashlib.sha256(result.stderr).hexdigest()))
        (output / 'execution.json').write_text(json.dumps(results, indent=2) + '\n')
        print(f'$ {command}\n{result.stdout.decode()}{result.stderr.decode()}exit={result.returncode}', flush=True)
        assert result.returncode == expected, f'{label}: expected exit {expected}; see {output}'
        return result

    assert not any(work.iterdir()), 'guide must start in an empty directory'
    run('setup', blocks['sdk-setup'], work, 0)
    assert (controls / 'request.txt').read_text() == URL + '\n'
    project = work / 'my first reader'
    (project / 'tiny.lang').write_text(sample + '\n')
    # Shell exports persist only inside setup; reproduce that exported SDK path.
    env['SDK'] = str(work / ARCHIVE.removesuffix('.tar.xz'))
    build = run('build', blocks['sdk-build'], project, 0)
    assert build.stdout == b'Wrote compiler tinyc\nWrote answer.ll\nanswer returned 42\n', build.stdout
    for name in ('tinyc', 'answer'):
        data = (project / name).read_bytes()
        assert data[:5] == b'\x7fELF\x02' and data[18:20] == b'\x3e\x00', name
        assert os.access(project / name, os.X_OK)
        shutil.copy2(project / name, output / name)
    malformed = run('malformed', blocks['sdk-malformed'], project, 1)
    assert b'malformed.tiny:1:8: expected number' in malformed.stderr, malformed.stderr
    assert not malformed.stdout.strip(), 'invalid source emitted output'
    for name in ('tiny.lang', 'answer.tiny', 'malformed.tiny', 'answer.ll'):
        shutil.copy2(project / name, output / name)
    (output / 'receipt.json').write_text(json.dumps(dict(
        archive_sha256=SHA256, guide_sha256=digest(guide_path), workspace=str(work),
        compiler_sha256=digest(Path(env['SDK']) / 'libexec/lang'),
        native_reader_sha256=digest(output / 'tinyc'),
        native_program_sha256=digest(output / 'answer'),
        transport='offline fixture; only curl replaced',
        clean_environment=True, valid_output=build.stdout.decode(),
        malformed_diagnostic=malformed.stderr.decode()), indent=2) + '\n')
    print('PASS: exact published commands and sample; native x86-64 reader/program; '
          'answer returned 42; malformed.tiny:1:8 diagnostic')


if __name__ == '__main__':
    main()
