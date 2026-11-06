#!/usr/bin/python3
"""Record explicit Clang invocations and reject accidental PATH selection."""
import json
import os
from pathlib import Path
import sys

with Path(os.environ['PACKAGE_CLANG_LOG']).open('a') as log:
    log.write(json.dumps(dict(tool=sys.argv[0], arguments=sys.argv[1:])) + '\n')
if Path(sys.argv[0]).name == 'clang':
    print('unexpected PATH Clang selection', file=sys.stderr)
    sys.exit(91)
os.execv(os.environ['PACKAGE_REAL_CLANG'], [os.environ['PACKAGE_REAL_CLANG'], *sys.argv[1:]])
