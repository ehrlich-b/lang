#!/usr/bin/env python3
"""Install generated text atomically without touching unchanged files."""
import os
from pathlib import Path
import sys
import tempfile


def write_if_changed(path, content):
    path = Path(path)
    if path.is_file() and path.read_bytes() == content:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        stream.write(content)
        temporary = stream.name
    os.replace(temporary, path)


if __name__ == '__main__':
    write_if_changed(sys.argv[1], sys.stdin.buffer.read())
