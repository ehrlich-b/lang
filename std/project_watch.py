#!/usr/bin/env python3
"""Content-based project edit loop; compilation and caching belong to Lang."""
import argparse
import ctypes
from collections import deque
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import struct
import subprocess
import sys
import tempfile
import time

PHASES = ['reader', 'validation', 'llvm', 'object', 'link']


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class InputChanges:
    """Fence a content probe with Linux filesystem change notifications.

    The compiler supplies the dependency closure. File watches catch writes via
    aliases; directory watches catch replacement, symlink and ancestor changes.
    This is a short-lived publication fence, never a dependency/cache identity.
    """
    MASK = 0x00000fce  # modify, attrib, close-write, moves, create/delete, self

    def __init__(self, paths):
        libc = ctypes.CDLL(None, use_errno=True)
        libc.inotify_init1.argtypes = [ctypes.c_int]
        libc.inotify_add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
        self.fd = libc.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
        if self.fd < 0:
            raise OSError(ctypes.get_errno(), 'cannot guard project inputs')
        self.watches = {}
        try:
            def add(path, names):
                wd = libc.inotify_add_watch(self.fd, os.fsencode(path), self.MASK)
                if wd < 0:
                    raise OSError(ctypes.get_errno(), 'cannot guard input: ' + str(path))
                if wd not in self.watches:
                    self.watches[wd] = names
                elif self.watches[wd] is not None:
                    if names is None:
                        self.watches[wd] = None
                    else:
                        self.watches[wd].update(names)

            for name in paths:
                # Arm each directory entry BEFORE inspecting it. Resolving the
                # whole path would discard intermediate links, whose replacement
                # can redirect a dependency without touching either endpoint.
                path = Path(name).absolute()
                pending = deque(path.parts[1:])
                path = Path(path.anchor)
                links = 0
                while pending:
                    part = pending.popleft()
                    if part == '..':
                        path = path.parent
                        continue
                    add(path, {os.fsencode(part)})
                    child = path / part
                    try:
                        info = child.lstat()
                    except (FileNotFoundError, NotADirectoryError):
                        # A resource fallback may leave this route absent. Its
                        # first missing entry is now guarded against creation.
                        break
                    if stat.S_ISLNK(info.st_mode):
                        links += 1
                        if links > 40:
                            raise OSError(errno.ELOOP, 'cannot guard input: ' + str(name))
                        target = Path(os.readlink(child))
                        if target.is_absolute():
                            path = Path(target.anchor)
                            pending.extendleft(reversed(target.parts[1:]))
                        else:
                            pending.extendleft(reversed(target.parts))
                    else:
                        path = child
                        if stat.S_ISREG(info.st_mode):
                            add(path, None)
        except BaseException:
            self.close()
            raise

    def changed(self):
        changed = False
        while True:
            try:
                data = os.read(self.fd, 65536)
            except BlockingIOError:
                return changed
            offset = 0
            while offset < len(data):
                wd, mask, _, size = struct.unpack_from('iIII', data, offset)
                name = data[offset + 16:offset + 16 + size].rstrip(b'\0')
                offset += 16 + size
                names = self.watches.get(wd)
                if mask & 0xe000 or not name or names is None or name in names:
                    changed = True

    def close(self):
        os.close(self.fd)


class Watch:
    def __init__(self, compiler, project, output, evidence, env=None):
        self.compiler = str(Path(compiler).resolve(strict=True))
        self.project = Path(project).resolve()
        self.output = Path(output).absolute() if output else None
        self.evidence = Path(evidence).resolve()
        self.evidence.mkdir(parents=True, exist_ok=False)
        self.env = dict(os.environ if env is None else env, LANG_TEST_TIMINGS='1', LANG_BUILD_RETAIN='1')
        self.key = None
        self.generation = 0
        self.active = None
        self.lock = None
        self.events = []
        self.stopped = False
        self.last_exit = 1
        self.probes = 0

    def event(self, kind, **values):
        row = dict(event=kind, generation=self.generation, **values)
        self.events.append(row)
        with (self.evidence / 'events.jsonl').open('a') as stream:
            stream.write(json.dumps(row) + '\n')
        print(json.dumps(row), flush=True)
        return row

    def inputs(self):
        # The compiler owns manifest parsing and transitive dependency resolution.
        # Never approximate its closure with a directory scan or mtime predicate.
        command = [self.compiler, 'project', 'watch-inputs', str(self.project)]
        start = time.monotonic()
        result = subprocess.run(command, env=self.env, capture_output=True, timeout=30)
        self.probes += 1
        with (self.evidence / 'probes.jsonl').open('a') as stream:
            stream.write(json.dumps(dict(command=command, exit=result.returncode,
                seconds=time.monotonic() - start, stdout=result.stdout.decode(errors='replace'),
                stderr=result.stderr.decode(errors='replace'))) + '\n')
        tool = shutil.which(self.env.get('LANG_CLANG') or 'clang', path=self.env.get('PATH'))
        tools = [(self.compiler, digest(self.compiler)), (str(Path(__file__).resolve()), digest(__file__)),
                 (tool, digest(tool) if tool else None)]
        # Retain exact errors even when a malformed edit prevents a dependency ID.
        key = (result.returncode, result.stdout, result.stderr, tuple(tools))
        entry = None
        if result.returncode == 0:
            _, entry, paths = result.stdout.split(b'\n', 2)
            entry = Path(os.fsdecode(entry))
            self.input_paths = [os.fsdecode(p) for p in paths.split(b'\0') if p]
        return key, entry, result

    def reserve_output(self, entry):
        if self.output is None:
            self.output = self.project.parent / 'build' / entry.stem
        self.output.parent.mkdir(parents=True, exist_ok=True)
        if self.lock is None:
            lock_path = self.output.with_name('.' + self.output.name + '.watch-lock')
            fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
            self.lock = os.fdopen(fd, 'w')
            try:
                fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError('another watch owns this output')
        self.check_output()

    def check_output(self):
        try:
            info = self.output.lstat()
        except FileNotFoundError:
            return
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError('watch output must be a regular native file without aliases')
        with self.output.open('rb') as stream:
            if stream.read(4) != b'\x7fELF':
                raise ValueError('refusing to replace an existing non-native file')

    def cancel(self, reason):
        if self.active is None:
            return
        build = self.active
        # Kill the entire compilation tree, including a tool ignoring SIGTERM.
        try:
            os.killpg(build['process'].pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            build['process'].wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(build['process'].pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        build['process'].wait()
        self.finish_record(build, 'cancelled', reason=reason)
        self.active = None

    def finish_record(self, build, kind, **values):
        build['stdout'].close()
        build['stderr'].close()
        stderr = (build['directory'] / 'stderr').read_bytes()
        phases = re.findall(rb'^Native phase ([0-4]) nanoseconds (\d+) exit (-?\d+)$', stderr, re.M)
        self.last_exit = build['process'].returncode
        return self.event(kind, build_generation=build['generation'], command=build['command'],
            cwd=os.getcwd(), exit=self.last_exit, seconds=time.monotonic() - build['start'],
            phase_seconds={PHASES[int(n)]: int(t) / 1e9 for n, t, _ in phases},
            phase_exits={PHASES[int(n)]: int(c) for n, _, c in phases},
            directory=str(build['directory']), **values)

    def tick(self):
        if self.stopped:
            return
        key, entry, result = self.inputs()
        if self.stopped:
            return
        if key != self.key:
            self.cancel('inputs changed')
            self.key = key
            self.generation += 1
            if self.output is not None and self.lock is not None:
                self.check_output()
                self.output.unlink(missing_ok=True)
            if result.returncode:
                self.last_exit = result.returncode
                sys.stderr.buffer.write(result.stderr)
                sys.stderr.flush()
                self.event('invalid', exit=result.returncode)
                return
            self.reserve_output(entry)
            self.output.unlink(missing_ok=True)
            # A private sibling keeps publication atomic on the output filesystem.
            directory = Path(tempfile.mkdtemp(prefix='.' + self.output.name + '.watch-', dir=self.output.parent))
            stdout = (directory / 'stdout').open('wb')
            stderr = (directory / 'stderr').open('wb')
            command = [self.compiler, 'build', '--project', str(self.project), str(entry),
                       '-o', str(directory / 'program')]
            start = time.monotonic()
            process = subprocess.Popen(command, env=self.env, stdout=stdout, stderr=stderr, start_new_session=True)
            self.active = dict(process=process, command=command, generation=self.generation,
                directory=directory, stdout=stdout, stderr=stderr, start=start,
                input_identity=result.stdout.decode().splitlines()[0])
            self.event('building', command=command, directory=str(directory),
                       input_identity=result.stdout.decode().splitlines()[0], tools=key[3])
        elif self.active is not None and self.active['process'].poll() is not None:
            build = self.active
            self.active = None
            if build['process'].returncode == 0:
                build['stderr'].flush()
                actual = re.findall(rb'^Native inputs (\w+)$', (build['directory'] / 'stderr').read_bytes(), re.M)
                if actual != [build['input_identity'].encode()]:
                    self.finish_record(build, 'superseded', reason='pipeline captured different inputs')
                    self.key = None
                    return
                # Install notifications BEFORE the final identity probe. An edit
                # after that probe reads a file must invalidate its returned ID,
                # including same-mtime and ABA edits. No compiler probe runs with
                # a provisional executable exposed at the destination.
                guard = InputChanges(self.input_paths + [p for p, _ in self.key[3] if p])
                accepted = False
                installed = False
                try:
                    # Linux excludes exec while this inode is open for writing,
                    # including exec through a descriptor opened before rename.
                    # Keep the exclusion through validation AND rollback: a
                    # rejected candidate must never become runnable in public.
                    with (build['directory'] / 'program').open('r+b'):
                        try:
                            output_digest = digest(build['directory'] / 'program')
                            current, _, _ = self.inputs()
                            self.check_output()
                            if current == self.key and not self.stopped and not guard.changed():
                                os.replace(build['directory'] / 'program', self.output)
                                installed = True
                                # This is the acceptance boundary. Edits already
                                # queued here supersede the candidate while exec
                                # is still excluded; later edits are a new cycle.
                                accepted = not guard.changed() and not self.stopped
                            if accepted:
                                self.finish_record(build, 'published', output=str(self.output), sha256=output_digest)
                        finally:
                            if not accepted:
                                if installed:
                                    os.replace(self.output, build['directory'] / 'program')
                                self.key = None
                                self.finish_record(build, 'superseded', reason='inputs changed during publication')
                finally:
                    guard.close()
            else:
                self.finish_record(build, 'failed')
                sys.stderr.buffer.write((build['directory'] / 'stderr').read_bytes())
                sys.stderr.flush()

    def close(self):
        self.stopped = True
        self.cancel('watch stopped')
        if self.lock is not None:
            self.lock.close()
            self.lock = None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', required=True)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('-o', type=Path)
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--interval', type=float, default=0.15)
    parser.add_argument('--once', action='store_true', help='build the current generation and exit')
    args = parser.parse_args()
    if not 0.01 <= args.interval <= 60:
        parser.error('interval must be between 0.01 and 60 seconds')
    evidence = args.evidence or args.project.resolve().parent / 'build' / ('watch-' + str(time.time_ns()))
    watch = Watch(args.compiler, args.project, args.o, evidence)
    watch.event('watching', evidence=str(watch.evidence))
    def stop(signum, frame):
        watch.stopped = True
    previous = {s: signal.signal(s, stop) for s in (signal.SIGINT, signal.SIGTERM)}
    try:
        while not watch.stopped:
            watch.tick()
            if args.once and watch.active is None and watch.key is not None:
                return watch.last_exit
            time.sleep(args.interval)
        return 130
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print('Error: ' + str(error), file=sys.stderr)
        return 1
    finally:
        watch.close()
        for s, handler in previous.items():
            signal.signal(s, handler)


if __name__ == '__main__':
    sys.exit(main())
