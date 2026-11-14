#!/usr/bin/env python3
"""Bounded, interleaved metadata replay; CPU includes child processes."""
import glob
import hashlib
import json
from pathlib import Path
import resource
import shutil
import statistics
import subprocess


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cpu():
    r = resource.getrusage(resource.RUSAGE_CHILDREN)
    return r.ru_utime + r.ru_stime


def main():
    paths = sorted(glob.glob('test/suite/*.lang'))
    rows = []
    for _ in range(3):
        for label, argv in (
            ('parent-header-replay', ['bash', 'test/suite_metadata_reference.sh', *paths]),
            ('candidate', ['python3', 'test/suite_manifest.py', '--metadata-only']),
        ):
            start = cpu()
            result = subprocess.run(argv, capture_output=True)
            rows.append(dict(label=label, argv=argv, exit=result.returncode,
                             cpu_seconds=cpu() - start,
                             output_sha256=hashlib.sha256(result.stdout).hexdigest()))
    medians = {label: statistics.median(r['cpu_seconds'] for r in rows if r['label'] == label)
               for label in ('parent-header-replay', 'candidate')}
    print(json.dumps(dict(files=len(paths), runs=rows, median_cpu_seconds=medians,
                          input_sha256={p: digest(p) for p in paths},
                          tool_sha256={p: digest(shutil.which(p)) for p in ('python3', 'bash', 'head', 'grep', 'sed')},
                          source_sha256={p: digest(p) for p in ('test/suite_manifest.py', 'test/suite_metadata_reference.sh')}), indent=2))
    assert len(paths) == 239
    assert all(r['exit'] == 0 for r in rows)
    assert len({r['output_sha256'] for r in rows}) == 1
    assert medians['candidate'] < 0.1, medians


if __name__ == '__main__':
    main()
