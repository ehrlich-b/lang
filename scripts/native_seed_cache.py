#!/usr/bin/env python3
"""Content-addressed native bootstrap artifacts; entries are never overwritten."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import tempfile


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def validate(entry, identity):
    receipt = json.loads((entry / 'receipt.json').read_text())
    artifact = entry / 'compiler'
    if (receipt['identity'] != identity or artifact.is_symlink()
            or not artifact.is_file() or not artifact.stat().st_size
            or receipt['sha256'] != digest(artifact)):
        raise ValueError('native seed cache validation failed: ' + str(entry))
    return artifact


def sync_file(path):
    with open(path, 'rb') as stream:
        os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', required=True)
    parser.add_argument('--clang', default='clang')
    parser.add_argument('--flags', default='-O2')
    parser.add_argument('--target', default='')
    parser.add_argument('--abi', default='native-v1')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    tool = Path(shutil.which(args.clang) or args.clang).resolve(strict=True)
    flags = shlex.split(args.flags)
    target = args.target or subprocess.check_output([str(tool), '-dumpmachine'], text=True).strip()
    identity = dict(format=1, seed=digest(args.seed), tool=digest(tool),
                    version=subprocess.check_output([str(tool), '--version'], text=True),
                    target=target, flags=flags, abi=args.abi,
                    host=[platform.system(), platform.machine()])
    key = hashlib.sha256(encoded(identity)).hexdigest()
    cache = Path(os.environ.get('LANG_NATIVE_CACHE',
                 str(Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')) / 'lang' / 'native-seed-v1')))
    cache.mkdir(parents=True, exist_ok=True)
    entry = cache / key
    # The lock also covers installation, so no consumer can observe a partial entry.
    with (cache / (key + '.lock')).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        hit = entry.exists()
        if not hit:
            with tempfile.TemporaryDirectory(prefix='.build-', dir=cache) as scratch:
                staging = Path(scratch) / 'entry'
                staging.mkdir()
                artifact = staging / 'compiler'
                subprocess.run([str(tool), *flags, '--target=' + target,
                                args.seed, '-o', str(artifact)], check=True)
                # Detect inputs changed during compilation, never publish that result.
                if digest(args.seed) != identity['seed'] or digest(tool) != identity['tool']:
                    raise ValueError('native seed cache inputs changed during build')
                receipt = dict(identity=identity, sha256=digest(artifact))
                (staging / 'receipt.json').write_bytes(encoded(receipt))
                validate(staging, identity)
                for path in staging.iterdir():
                    path.chmod(0o555 if path.name == 'compiler' else 0o444)
                    sync_file(path)
                directory = os.open(staging, os.O_RDONLY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
                staging.rename(entry)
                entry.chmod(0o555)
                directory = os.open(cache, os.O_RDONLY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
        artifact = validate(entry, identity)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        # Copy rather than hardlink: local edits must not mutate a shared entry.
        with tempfile.TemporaryDirectory(prefix='.install-', dir=output.parent) as scratch:
            local = Path(scratch) / 'compiler'
            shutil.copyfile(artifact, local)
            local.chmod(0o755)
            if digest(local) != digest(artifact):
                raise ValueError('native seed cache install validation failed')
            os.replace(local, output)
            link = Path(scratch) / 'lang'
            link.symlink_to(output.name)
            os.replace(link, output.parent / 'lang')
        print('native seed cache ' + ('hit: ' if hit else 'miss: ') + key)


if __name__ == '__main__':
    main()
