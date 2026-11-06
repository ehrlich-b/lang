#!/usr/bin/env python3
"""Inject one same-timestamp edit after a completed build's identity probe."""
import os
from pathlib import Path
import runpy
import sys


script, guest_name, before, after = sys.argv[1:5]
sys.argv = [script, *sys.argv[5:]]
host = runpy.run_path(script)
Watch = host['Watch']
original_inputs = Watch.inputs
injected = False


def edit_after_probe(self):
    global injected
    value = original_inputs(self)
    if not injected and self.active is not None and self.active['process'].poll() == 0:
        guest = Path(guest_name)
        stamp = guest.stat()
        source = guest.read_text()
        if before not in source:
            raise RuntimeError('publication race control did not match guest source')
        guest.write_text(source.replace(before, after))
        os.utime(guest, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
        injected = True
    return value


Watch.inputs = edit_after_probe
code = host['main']()
if not injected:
    raise RuntimeError('publication race control was not exercised')
sys.exit(code)
