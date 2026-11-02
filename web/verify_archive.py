#!/usr/bin/env python3
"""Validate an archive completely before writing or shipping its contents."""
import hashlib
import pathlib
import re
import sys
import tarfile

archive, destination = sys.argv[1:]
dest = pathlib.Path(destination)
with tarfile.open(archive, 'r:gz') as tar:
    members = tar.getmembers()
    names = [m.name for m in members]
    if len(names) != len(set(names)) or 'MANIFEST' not in names:
        sys.exit('duplicate files or missing MANIFEST')
    if any(not m.isfile() or not re.fullmatch(r'[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*', m.name) or '..' in m.name.split('/') for m in members):
        sys.exit('invalid archive path or type')
    manifest = tar.extractfile('MANIFEST').read().decode('ascii')
    entries = {}
    for line in manifest.splitlines():
        match = re.fullmatch(r'([0-9a-f]{64})  ([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*)', line)
        if not match or match[2] in entries or match[2] in ('MANIFEST', '.files'):
            sys.exit('invalid MANIFEST')
        entries[match[2]] = match[1]
    if not entries or set(names) != set(entries) | {'MANIFEST'}:
        sys.exit('MANIFEST does not list exactly the archive files')
    contents = {name: tar.extractfile(name).read() for name in entries}
    if any(hashlib.sha256(contents[name]).hexdigest() != digest for name, digest in entries.items()):
        sys.exit('hash mismatch')
    for name, data in contents.items():
        path = dest / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (dest / '.files').write_text(''.join(name + '\n' for name in sorted(entries)))
