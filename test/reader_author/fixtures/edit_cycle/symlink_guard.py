#!/usr/bin/env python3
"""Check notification coverage for every link traversed by a project input."""
import errno
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

spec = importlib.util.spec_from_file_location('watch_host', sys.argv[1])
host = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)
checks = []
with tempfile.TemporaryDirectory(dir=sys.argv[2]) as temporary:
    root = Path(temporary).resolve()
    for directory in (False, True):
        for absolute in (False, True):
            for aba in (False, True):
                case = root / str(len(checks))
                for folder in ('entry', 'links', 'targets'):
                    (case / folder).mkdir(parents=True)
                old, new = (case / 'targets' / name for name in ('old', 'new'))
                if directory:
                    old.mkdir()
                    new.mkdir()
                    (old / 'input').write_text('old')
                    (new / 'input').write_text('new')
                else:
                    old.write_text('old')
                    new.write_text('new')
                middle = case / 'links/middle'
                middle.symlink_to(old if absolute else '../targets/old')
                outer = case / 'entry/outer'
                outer.symlink_to(middle if absolute else '../links/middle')
                source = outer / 'input' if directory else outer
                guard = host.InputChanges([source])
                try:
                    before = source.read_text()
                    replacement = middle.with_name('replacement')
                    replacement.symlink_to(new if absolute else '../targets/new')
                    os.replace(replacement, middle)
                    if aba:
                        replacement.symlink_to(old if absolute else '../targets/old')
                        os.replace(replacement, middle)
                    changed = guard.changed()
                    assert before == 'old' and changed, 'middle-link replacement escaped guard'
                    checks.append(dict(directory=directory, absolute=absolute, aba=aba,
                                       before=before, after=source.read_text(), changed=changed))
                finally:
                    guard.close()
    missing = root / 'missing'
    guard = host.InputChanges([missing / 'child'])
    try:
        (root / 'unrelated').write_text('unrelated')
        assert not guard.changed(), 'unrelated sibling invalidated guard'
        missing.mkdir()
        assert guard.changed(), 'missing dependency creation escaped guard'
    finally:
        guard.close()
    loop = root / 'loop'
    loop.symlink_to('loop')
    try:
        host.InputChanges([loop])
    except OSError as error:
        assert error.errno == errno.ELOOP
    else:
        raise AssertionError('symlink loop did not fail closed')
print(json.dumps(dict(checks=checks, missing_creation=True, unrelated_ignored=True, loop_rejected=True)))
