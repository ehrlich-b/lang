#!/usr/bin/env python3
"""Validate an archive completely before writing or shipping its contents."""
import hashlib
import pathlib
import re
import sys
import tarfile

# The deployable site is a complete snapshot, not a partial update.  Keep this
# inventory in step with the files packaged for the site.
SITE_FILES = frozenset('''
build_stdlib.js compiler-receipt.json compiler.wasm compiler_host.js editor.js
examples/fib.lang examples/fib.wasm examples/mandelbrot.lang
examples/mandelbrot.wasm examples/polyglot_wasm.lang examples/polyglot_wasm.wasm
host.js index.html lab.html program_host.js reader_runner.js reader_worker.js readers.html receipt.json stdlib.json
'''.split())

archive, destination = sys.argv[1:]
dest = pathlib.Path(destination)
with tarfile.open(archive, 'r:gz') as tar:
    members = tar.getmembers()
    names = [m.name for m in members]
    if len(names) != len(set(names)) or 'MANIFEST' not in names:
        sys.exit('duplicate files or missing MANIFEST')
    if any(not m.isfile() or not re.fullmatch(r'[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*', m.name) or any(part in ('.', '..') for part in m.name.split('/')) for m in members):
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
    if set(entries) != SITE_FILES:
        sys.exit('archive does not contain the complete site inventory')
    contents = {name: tar.extractfile(name).read() for name in entries}
    if any(hashlib.sha256(contents[name]).hexdigest() != digest for name, digest in entries.items()):
        sys.exit('hash mismatch')
    for name, data in contents.items():
        path = dest / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (dest / '.files').write_text(''.join(name + '\n' for name in sorted(entries)))
