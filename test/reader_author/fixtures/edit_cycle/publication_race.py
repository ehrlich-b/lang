#!/usr/bin/env python3
"""Inject a publication edit or cancellation before a consumer can execute."""
import errno
import os
from pathlib import Path
import runpy
import signal
import subprocess
import sys


script, guest_name, before, after, boundary = sys.argv[1:6]
sys.argv = [script, *sys.argv[6:]]
host = runpy.run_path(script)
Watch = host['Watch']
original_inputs = Watch.inputs
injected = False
completed_probes = 0


def edit_after_probe(self):
    global injected, completed_probes
    if self.active is not None and self.active['process'].poll() == 0:
        completed_probes = 1
    elif completed_probes:
        completed_probes += 1
    if completed_probes and self.output.exists():
        raise RuntimeError('provisional output visible during publication probe')
    value = original_inputs(self)
    target = 1 if boundary == 'probe' else 2
    if not injected and 'rename' not in boundary and completed_probes == target:
        if boundary == 'cancel-final-probe':
            injected = True
            os.kill(os.getpid(), signal.SIGINT)
            return value
        guest = Path(guest_name)
        stamp = guest.stat()
        source = guest.read_text()
        if before not in source:
            raise RuntimeError('publication race control did not match guest source')
        guest.write_text(source.replace(before, after))
        os.utime(guest, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
        injected = True
    return value



original_replace = os.replace
output = Path(sys.argv[sys.argv.index('-o') + 1])


def edit_at_rename(source, destination):
    global injected
    if injected or Path(destination) != output:
        return original_replace(source, destination)
    injected = True
    if boundary == 'cancel-rename':
        os.kill(os.getpid(), signal.SIGINT)
    else:
        guest = Path(guest_name)
        stamp = guest.stat()
        contents = guest.read_text()
        if before not in contents:
            raise RuntimeError('replacement race control did not match guest source')
        guest.write_text(contents.replace(before, after))
        os.utime(guest, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    original_replace(source, destination)
    try:
        result = subprocess.run([str(destination), '99'], capture_output=True)
    except OSError as error:
        if error.errno != errno.ETXTBSY:
            raise
    else:
        raise RuntimeError('provisional executable ran during replacement: ' + repr(result.stdout))


Watch.inputs = edit_after_probe
if 'rename' in boundary:
    os.replace = edit_at_rename
code = host['main']()
if not injected:
    raise RuntimeError('publication race control was not exercised')
sys.exit(code)
