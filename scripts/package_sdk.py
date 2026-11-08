#!/usr/bin/env python3
"""Build a versioned, reproducible Linux x86-64 SDK from committed source."""
import argparse
import hashlib
import io
import json
import lzma
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--version', help='default: 0.1.0+<12-digit commit>')
    args = parser.parse_args()
    for tool in ('git', 'make', 'clang'):
        if not shutil.which(tool):
            parser.exit(127, f'Error: {tool} is required; install {tool} with your system package manager and add it to PATH.\n')
    if platform.system() != 'Linux' or platform.machine() != 'x86_64':
        parser.exit(1, 'Error: packaging requires Linux x86-64.\n')
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT).strip():
        parser.exit(1, 'Error: commit the source before packaging.\n')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    version = args.version or '0.1.0+' + head[:12]
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.+_-]{0,79}', version):
        parser.error('version must be a safe filename component')
    output = args.output.resolve()
    if output.is_relative_to(ROOT):
        parser.error('output must be outside the source checkout')
    output.mkdir(parents=True, exist_ok=True)
    name = f'lang-{version}-x86_64-linux'
    archive = output / (name + '.tar.xz')
    receipt = output / (name + '.receipt.json')
    if archive.exists() or receipt.exists():
        parser.error('archive or receipt already exists; choose a fresh output directory')
    work = Path(tempfile.mkdtemp(prefix='sdk-build-', dir=output))
    source = work / 'source'
    # A fresh local clone supplies committed input and Git build identity, never
    # an existing compiler, reader cache, generated OS layer or bootstrap output.
    subprocess.run(['git', 'clone', '--quiet', '--no-local', str(ROOT), str(source)], check=True)
    subprocess.run(['git', 'checkout', '--quiet', '--detach', head], cwd=source, check=True)
    env = dict(os.environ, LANGBE='llvm', LANGOS='linux', JOBS='2')
    for key in ('LANG_ROOT', 'LANG_CLANG', 'VERIFY_CASE'):
        env.pop(key, None)
    with (output / (name + '.build.log')).open('wb') as log:
        subprocess.run(['make', 'build'], cwd=source, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    files = {
        'bin/lang': ((source / 'scripts/sdk-launcher.sh').read_bytes(), 0o755),
        'libexec/lang': ((source / 'out/lang_next').read_bytes(), 0o755),
    }
    for folder in ('std', 'src'):
        for path in sorted((source / folder).rglob('*.lang')):
            files[str(path.relative_to(source))] = (path.read_bytes(), 0o644)
    # The compiler's scaffolding is embedded in libexec/lang. Ship the Tariff
    # example too so the entire first journey needs no source checkout.
    for path in sorted((source / 'examples/dsl-compare').rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts:
            files[str(path.relative_to(source))] = (path.read_bytes(), 0o644)
    for filename in ('README.md', 'LICENSE', 'LANG.md', 'docs/READERS.md', 'docs/SDK.md'):
        files[filename] = ((source / filename).read_bytes(), 0o644)
    tools = {tool: subprocess.check_output([tool, '--version'], text=True).splitlines()[0]
             for tool in ('clang', 'make', 'git')}
    tools['python'] = platform.python_version()
    manifest = dict(version=1, sdk_version=version, commit=head, target='x86_64-linux',
                    tools=tools, flags=['-O2'],
                    files={p: dict(bytes=len(data), sha256=digest(data), mode=oct(mode))
                           for p, (data, mode) in sorted(files.items())})
    files['sdk.json'] = ((json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode(), 0o644)
    # Canonical metadata, order and XZ stream: no host paths, clock, UID or GID.
    with lzma.open(archive, 'wb', preset=6) as compressed:
        with tarfile.open(fileobj=compressed, mode='w|', format=tarfile.USTAR_FORMAT) as tar:
            for relative, (data, mode) in sorted(files.items()):
                info = tarfile.TarInfo(name + '/' + relative)
                info.size, info.mode, info.mtime = len(data), mode, 0
                info.uid = info.gid = 0
                info.uname = info.gname = ''
                tar.addfile(info, io.BytesIO(data))
    manifest['archive'] = dict(file=archive.name, bytes=archive.stat().st_size,
                               sha256=digest(archive.read_bytes()),
                               unpacked_file_bytes=sum(len(data) for data, _ in files.values()))
    receipt.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    print(archive)
    print(receipt)
    return 0


if __name__ == '__main__':
    sys.exit(main())
