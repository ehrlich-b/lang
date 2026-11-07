#!/usr/bin/env python3
"""Provision pinned Linux x86-64 comparison tools under an explicit directory."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import urllib.request
import zipfile

PACKAGES = [
    ('bison_2%3a3.8.2+dfsg-1+b2_amd64.deb',
     'https://deb.debian.org/debian/pool/main/b/bison/bison_3.8.2+dfsg-1+b2_amd64.deb',
     'ce6eb1f7aad18850e32d223a68f54bcbe756d74f138c8ec5460ad9d220f4d335'),
    ('flex_2.6.4-8.2+b4_amd64.deb',
     'https://deb.debian.org/debian/pool/main/f/flex/flex_2.6.4-8.2+b4_amd64.deb',
     '75f963765232c356d0a2fb70e780dfa9de2425aca036ec60eefb7fc98a2c905b'),
    ('m4_1.4.19-8_amd64.deb',
     'https://deb.debian.org/debian/pool/main/m/m4/m4_1.4.19-8_amd64.deb',
     '221b3e224708c1da2a1a88b6824380593579b2254ae7d914afa14cbd5d343334'),
    ('antlr-4.13.2-complete.jar', 'https://www.antlr.org/download/antlr-4.13.2-complete.jar',
     'eae2dfa119a64327444672aff63e9ec35a20180dc5b8090b7a6ab85125df4d76'),
    ('jre.tar.gz',
     'https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.13%2B9/OpenJDK21U-jre_x64_linux_hotspot_21.0.13_9.tar.gz',
     'a535a1df9c6284d9618872984e026ae0352d1f7e9e0605425c0e6114f47351dd'),
    ('antlr4_python3_runtime-4.13.2-py3-none-any.whl',
     'https://files.pythonhosted.org/packages/89/03/a851e84fcbb85214dc637b6378121ef9a0dd61b4c65264675d8a5c9b1ae7/antlr4_python3_runtime-4.13.2-py3-none-any.whl',
     'fe3835eb8d33daece0e799090eda89719dbccee7aa39ef94eed3818cafa5a7e8'),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tools', type=Path, required=True)
    args = parser.parse_args()
    root = args.tools.resolve()
    root.mkdir(parents=True, exist_ok=True)
    for name, url, checksum in PACKAGES:
        path = root / name
        if not path.exists():
            print('Downloading', url, flush=True)
            with urllib.request.urlopen(url, timeout=120) as response, path.open('wb') as out:
                while chunk := response.read(1024 * 1024):
                    out.write(chunk)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != checksum:
            raise ValueError(f'{path}: expected {checksum}, got {actual}; refusing to use it')
        if name.endswith('.deb'):
            subprocess.run(['dpkg-deb', '-x', path, root / 'prefix'], check=True)
        elif name.endswith('.whl'):
            with zipfile.ZipFile(path) as archive:
                archive.extractall(root / 'python')
        elif name == 'jre.tar.gz' and not (root / 'jre/bin/java').exists():
            # Strip the versioned top directory, keeping every extraction local.
            with tarfile.open(path) as archive:
                for member in archive.getmembers():
                    parts = Path(member.name).parts[1:]
                    if not parts:
                        continue
                    member.name = str(Path(*parts))
                    archive.extract(member, root / 'jre', filter='data')
    (root / 'manifest.json').write_text(json.dumps(dict(packages=PACKAGES), indent=2) + '\n')
    print('Pinned tools ready:', root)


if __name__ == '__main__':
    main()
