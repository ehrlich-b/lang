#!/usr/bin/env python3
"""Prove archive-only use on a separate, diskless Linux x86-64 machine.

Build an allowlisted initramfs without a checkout, seed, disks, network, or host
shares. All host operations are unprivileged. The tiny guest init immediately
drops to uid 1000, then mounts proc in an unprivileged user/PID namespace with
only uid 1000 mapped. All recorded consumer commands run as uid 1000.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import selectors
import stat
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--qemu', type=Path, required=True)
    parser.add_argument('--bios', type=Path, required=True)
    parser.add_argument('--kernel', type=Path, required=True)
    args = parser.parse_args()
    assert os.geteuid() != 0, 'run without root'
    evidence, scratch = args.evidence.resolve(), args.scratch.resolve()
    assert not evidence.is_relative_to(ROOT) and not scratch.is_relative_to(ROOT)
    evidence.mkdir(parents=True, exist_ok=True)
    scratch.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='sdk-vm-', dir=scratch))
    package = json.loads((evidence / 'sdk-package.json').read_text())
    archive = Path(package['archive'])
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    assert package['head'] == head and sha(archive) == package['sha256']
    files = {}
    setup = []

    def call(command):
        command = [str(a) for a in command]
        start = time.perf_counter()
        result = subprocess.run(command, capture_output=True, text=True, timeout=180)
        setup.append(dict(command=command, exit_code=result.returncode,
                          seconds=time.perf_counter() - start, stdout=result.stdout, stderr=result.stderr))
        assert result.returncode == 0, setup[-1]
        return result.stdout

    def add(source, dest=None):
        source = Path(source)
        if source.is_file():
            name = str(dest or source).lstrip('/')
            files[name] = (source, stat.S_IMODE(source.stat().st_mode))

    def tree(source, dest=None):
        source = Path(source)
        for path in sorted(source.rglob('*')):
            if '__pycache__' not in path.parts:
                add(path, Path(dest or source) / path.relative_to(source))

    def elf(source, dest=None):
        add(source, dest)
        for line in call(['ldd', source]).splitlines():
            for word in line.split():
                if word.startswith('/') and Path(word).is_file():
                    add(word)

    # Exact tool allowlist, not a copy of the producer's root filesystem.
    for source, dest in (('/usr/bin/python3.13', '/usr/bin/python3'),
                         ('/usr/lib/llvm-19/bin/clang', '/usr/bin/clang'),
                         ('/usr/bin/ld', None), ('/usr/bin/x86_64-linux-gnu-ld', None),
                         ('/usr/bin/tar', None), ('/usr/bin/xz', None), ('/bin/sh', None)):
        elf(source, dest)
    tree('/usr/lib/python3.13')
    for extension in sorted(Path('/usr/lib/python3.13/lib-dynload').glob('*.so')):
        elf(extension)
    tree('/usr/lib/llvm-19/lib/clang/19/include', '/usr/lib/clang/19/include')
    for folder in ('/usr/include/x86_64-linux-gnu', '/usr/include/linux', '/usr/include/asm-generic'):
        tree(folder)
    for path in Path('/usr/include').glob('*.h'):
        add(path)
    gcc = Path('/usr/lib/gcc/x86_64-linux-gnu/14')
    for pattern in ('*.o', 'libgcc*.a', 'libgcc_s.so'):
        for path in gcc.glob(pattern):
            add(path)
    lib = Path('/usr/lib/x86_64-linux-gnu')
    for pattern in ('*crt*.o', 'libc.so', 'libm.so', 'lib*_nonshared.a'):
        for path in lib.glob(pattern):
            add(path)
    for path in ('/lib/x86_64-linux-gnu/libm.so.6', '/lib/x86_64-linux-gnu/libmvec.so.1',
                 '/lib/x86_64-linux-gnu/libgcc_s.so.1'):
        elf(path)
    init = work / 'init'
    call(['/usr/bin/clang', '-O2', '-static', ROOT / 'scripts/sdk_vm_init.c', '-o', init])
    add(init, '/init')
    add(ROOT / 'scripts/sdk_vm_guest.py', '/journey.py')
    add(archive, '/sdk.tar.xz')
    inventory = {p: dict(bytes=source.stat().st_size, sha256=sha(source), mode=oct(mode))
                 for p, (source, mode) in sorted(files.items())}
    assert not any('/.git/' in p or '/bootstrap/' in p for p in inventory)
    inventory_path = evidence / 'sdk-vm-inventory.json'
    inventory_path.write_text(json.dumps(inventory, indent=2) + '\n')
    add(inventory_path, '/inventory.json')
    # Write newc ourselves: device-node metadata in an archive needs no mknod,
    # root, loop devices or block-image tooling on the host.
    image = work / 'initramfs.cpio.gz'
    directories = {'consumer', 'tmp', 'dev', 'proc'}
    for name in files:
        directories.update(str(p) for p in Path(name).parents if str(p) != '.')
    with gzip.open(image, 'wb', compresslevel=1) as out:
        inode = 0

        def entry(name, mode, data=b'', major=0, minor=0):
            nonlocal inode
            inode += 1
            encoded = name.encode() + b'\0'
            fields = (inode, mode, 1000, 1000, 1, 1, len(data), 0, 0, major, minor, len(encoded), 0)
            header = b'070701' + b''.join(f'{v:08x}'.encode() for v in fields)
            out.write(header + encoded + b'\0' * (-(len(header) + len(encoded)) % 4))
            out.write(data)
            out.write(b'\0' * (-len(data) % 4))

        for directory in sorted(directories, key=lambda p: (p.count('/'), p)):
            entry(directory, stat.S_IFDIR | 0o755)
        for name, (source, mode) in sorted(files.items()):
            entry(name, stat.S_IFREG | mode, source.read_bytes())
        for name, major, minor in (('console', 5, 1), ('null', 1, 3), ('urandom', 1, 9), ('random', 1, 8)):
            entry('dev/' + name, stat.S_IFCHR | 0o666, major=major, minor=minor)
        entry('TRAILER!!!', 0)
    qemu = args.qemu.resolve()
    env = dict(os.environ)
    # Locally extracted Debian QEMU dependencies; no system installation.
    env['LD_LIBRARY_PATH'] = str(qemu.parents[1] / 'lib/x86_64-linux-gnu')
    command = [str(qemu), '-no-user-config', '-nodefaults', '-machine', 'q35,accel=kvm',
               '-cpu', 'host', '-smp', '2', '-m', '4096', '-display', 'none',
               '-serial', 'stdio', '-monitor', 'none', '-nic', 'none', '-no-reboot',
               '-L', str(args.bios.resolve()), '-kernel', str(args.kernel.resolve()),
               '-initrd', str(image), '-append', 'console=ttyS0 quiet panic=-1 rdinit=/init']
    start = time.perf_counter()
    transcript = evidence / 'sdk-vm-console.log'
    result = None
    with transcript.open('wb') as log:
        process = subprocess.Popen(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        pending = b''
        try:
            while time.perf_counter() - start < 300:
                if not selector.select(timeout=1):
                    if process.poll() is not None:
                        break
                    continue
                chunk = os.read(process.stdout.fileno(), 65536)
                if not chunk:
                    break
                log.write(chunk)
                log.flush()
                pending += chunk
                while b'\n' in pending:
                    line, pending = pending.split(b'\n', 1)
                    if line.startswith(b'SDK_JOURNEY_RESULT='):
                        result = json.loads(line.split(b'=', 1)[1])
                if result:
                    break
        finally:
            process.terminate()
            process.wait(timeout=10)
            selector.close()
    assert result is not None, f'no guest receipt; inspect {transcript}'
    result.update(version=2, host=os.uname().nodename, isolation='separate diskless Linux VM',
                  vm=dict(command=command, seconds=time.perf_counter() - start,
                          kernel_sha256=sha(args.kernel), qemu_sha256=sha(qemu),
                          initramfs_sha256=sha(image), inventory=str(inventory_path),
                          console=str(transcript), setup_commands=setup,
                          attached_disks=[], host_shares=[], network_devices=[], host_uid=os.getuid()))
    (evidence / 'sdk-journey.json').write_text(json.dumps(result, indent=2) + '\n')
    assert result['status'] == 'PASS', result.get('error')
    assert result['head'] == head and result['archive_sha256'] == package['sha256']
    assert result['uid'] == result['euid'] == 1000
    assert result['inventory_sha256'] == sha(inventory_path)
    print(json.dumps(dict(status=result['status'], head=head, commands=len(result['commands']),
                          receipt=str(evidence / 'sdk-journey.json'))))


if __name__ == '__main__':
    main()
