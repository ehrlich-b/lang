"""Archive-only consumer, executed as uid 1000 in a diskless Linux VM."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import time
import traceback

rows = []


def call(args, expected=0, output=None, env=None):
    args = [str(a) for a in args]
    start = time.perf_counter()
    result = subprocess.run(args, capture_output=True, env=env, timeout=180)
    row = dict(command=args, cwd=os.getcwd(), exit_code=result.returncode,
               seconds=time.perf_counter() - start,
               stdout=result.stdout.decode(errors='replace'), stderr=result.stderr.decode(errors='replace'))
    rows.append(row)
    if output:
        Path(output).write_bytes(result.stdout)
    print(json.dumps(row), flush=True)
    assert result.returncode == expected, row
    return result


def journey():
    assert os.getuid() == os.geteuid() == 1000
    inventory = json.loads(Path('/inventory.json').read_text())
    assert not any('/.git/' in p or '/bootstrap/' in p for p in inventory)
    # Inspect the entire guest root before extraction, not merely denied opens.
    actual = []
    for root, dirs, names in os.walk('/'):
        if root == '/':
            dirs.remove('proc')  # Live process metadata is not an input filesystem.
        actual.extend(str(Path(root) / name) for name in dirs + names)
    assert not any(p.endswith('/.git') or p.endswith('/bootstrap') for p in actual)
    assert not any(p.startswith(('/work/', '/home/')) for p in actual)
    assert Path('/proc/self/uid_map').read_text().split() == ['1000', '1000', '1']
    status = Path('/proc/self/status').read_text()
    assert 'CapEff:\t0000000000000000' in status
    assert list(Path('/consumer').iterdir()) == []
    os.chdir('/consumer')
    archive = Path('/sdk.tar.xz')
    with tarfile.open(archive) as tar:
        assert not any('/bootstrap/' in m.name or '/.git/' in m.name for m in tar)
    call(['tar', '-xJf', archive])
    sdk, = Path.cwd().glob('lang-*-x86_64-linux')
    manifest = json.loads((sdk / 'sdk.json').read_text())
    for p, meta in manifest['files'].items():
        assert hashlib.sha256((sdk / p).read_bytes()).hexdigest() == meta['sha256'], p
    os.environ['PATH'] = str(sdk / 'bin') + ':/usr/bin:/bin'
    Path('language').mkdir()
    os.chdir('language')
    call(['lang', 'new', 'reader', 'tiny'])
    call(['lang', 'compiler', 'tiny', 'tiny.lang', '-o', 'tinyc'])
    call(['./tinyc', 'answer.tiny', '-o', 'answer.ll'])
    call(['clang', '-O2', 'answer.ll', '-o', 'answer'])
    call(['./answer'], expected=42)
    source = sdk / 'examples/dsl-compare'
    call(['lang', 'new', 'reader', 'tariff'])
    # Record the unchanged frontend adaptation as an actual timed command.
    adapt = ("from pathlib import Path; import sys; "
             "s=Path(sys.argv[1]).read_text().split('\\nfunc main(',1)[0]; "
             "Path('tariff.lang').write_text(s+'\\nreader tariff(text *u8) *u8 { return tariff_read(text); }\\n')")
    call(['python3', '-c', adapt, source / 'lang/tariff.lang'])
    call(['lang', 'compiler', 'tariff', 'tariff.lang', '-o', 'tariffc'])
    call(['./tariffc', source / 'fixtures/benchmark.tariff', '-o', 'program.ll'])
    call(['clang', '-O2', 'program.ll', source / 'harness.c', '-o', 'program'])
    assert call(['./program', '2000000']).stdout == b'6000002995045\n'
    # Also preserve the comparison's CLI/AST path from the previous proof.
    call(['lang', source / 'lang/tariff.lang', '-o', 'frontend.ll'])
    call(['clang', '-O2', 'frontend.ll', '-o', 'frontend'])
    call(['./frontend', source / 'fixtures/benchmark.tariff'], output='program.ast')
    call(['lang', '--from-ast', 'program.ast', '--ast-source', source / 'fixtures/benchmark.tariff', '-o', 'ast.ll'])
    call(['clang', '-O2', 'ast.ll', source / 'harness.c', '-o', 'ast-program'])
    assert call(['./ast-program', '2000000']).stdout == b'6000002995045\n'
    clang_only = Path('/consumer/clang-only')
    clang_only.mkdir()
    (clang_only / 'clang').symlink_to(shutil.which('clang'))
    for tool, path in (('clang', str(sdk / 'bin')),
                       ('ld', str(sdk / 'bin') + ':' + str(clang_only))):
        assert shutil.which(tool, path=path) is None
        for command in (['lang', 'compiler', 'tiny', 'tiny.lang', '-o', 'missingc'],
                        ['lang', 'run', 'tiny.lang', 'answer.tiny']):
            result = call(command, expected=127, env=dict(os.environ, PATH=path))
            message = result.stderr.decode()
            assert len(message.splitlines()) == 1 and message.startswith(f'Error: {tool} is required;')
            assert 'apt install' in message and not result.stdout
    assert not Path('missingc').exists()
    call(['clang', '--version'])
    call(['ld', '--version'])
    return dict(status='PASS', head=manifest['commit'], uid=os.getuid(), euid=os.geteuid(),
                archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                initial_consumer_entries=[], checkout_present=False, bootstrap_seed_present=False,
                filesystem='initramfs only; no block devices, host shares or network attached',
                inventory_sha256=hashlib.sha256(Path('/inventory.json').read_bytes()).hexdigest())


try:
    receipt = journey()
except BaseException:
    receipt = dict(status='FAIL', error=traceback.format_exc())
receipt['commands'] = rows
print('SDK_JOURNEY_RESULT=' + json.dumps(receipt), flush=True)
