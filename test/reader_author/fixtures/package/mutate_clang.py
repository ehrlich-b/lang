#!/usr/bin/python3
"""Change a scratch metadata input after the packager snapshots its hash."""
import os
from pathlib import Path
import sys

if '--version' in sys.argv:
    path = Path(os.environ['PACKAGE_MUTATE'])
    path.write_text(path.read_text() + '\n')
os.execv(os.environ['PACKAGE_REAL_CLANG'], [os.environ['PACKAGE_REAL_CLANG'], *sys.argv[1:]])
