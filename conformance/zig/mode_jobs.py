"""Linux supervision for independent whole-mode oracle subprocesses."""
import ctypes
import json
import os
from pathlib import Path
import signal
import subprocess
import time


def tree():
    """pid -> (parent, resident bytes, start ticks, state), from one /proc scan."""
    result = {}
    for path in Path('/proc').glob('[0-9]*/stat'):
        try:
            fields = path.read_text().rsplit(')', 1)[1].split()
            result[int(path.parent.name)] = (int(fields[1]), int(fields[21]) * os.sysconf('SC_PAGE_SIZE'),
                                              int(fields[19]), fields[0])
        except (OSError, ValueError, IndexError):
            continue
    return result


def descendants(snapshot, root):
    found = {root}
    while True:
        more = {pid for pid, entry in snapshot.items() if entry[0] in found}
        if more <= found:
            return found - {root}
        found |= more


def handle(pid, entry):
    """Pin identity before signalling; never signal a reused numeric PID."""
    try:
        fd = os.pidfd_open(pid)
    except ProcessLookupError:
        return None
    try:
        fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        if int(fields[19]) == entry[2]:
            return fd
    except (FileNotFoundError, ProcessLookupError):
        pass
    os.close(fd)
    return None


def send(fd, sig):
    try:
        signal.pidfd_send_signal(fd, sig)
    except ProcessLookupError:
        pass


def cleanup(processes):
    # Subreaping keeps descendants addressable after a worker/runner dies.
    # Freeze to a fixed point, then kill; pidfds close the PID reuse window.
    held = {}
    deadline = time.monotonic() + 5
    try:
        while time.monotonic() < deadline:
            snapshot = tree()
            pids = descendants(snapshot, os.getpid())
            for pid in pids:
                identity = (pid, snapshot[pid][2])
                if identity not in held:
                    fd = handle(pid, snapshot[pid])
                    if fd is not None:
                        held[identity] = fd
                if identity in held:
                    send(held[identity], signal.SIGSTOP)
            if all(snapshot[p][3] in ('T', 't', 'Z', 'X') for p in pids):
                # These states cannot fork. A fresh scan catches children born
                # while the preceding scan was stopping their parents.
                after = tree()
                if descendants(after, os.getpid()) <= pids:
                    break
            time.sleep(.01)
        for fd in held.values():
            send(fd, signal.SIGKILL)
        # Rescan/reap with a deadline, including children of an uninterruptible
        # parent. Never hang forever or claim successful cleanup of survivors.
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            for process in processes:
                process.poll()
            # Avoid waitpid(-1) before Popen has collected its own children.
            if all(process.returncode is not None for process in processes):
                while True:
                    try:
                        pid, _ = os.waitpid(-1, os.WNOHANG)
                        if pid == 0:
                            break
                    except ChildProcessError:
                        break
            snapshot = tree()
            pids = descendants(snapshot, os.getpid())
            if not pids:
                return []
            for pid in pids:
                fd = handle(pid, snapshot[pid])
                if fd is not None:
                    try:
                        send(fd, signal.SIGKILL)
                    finally:
                        os.close(fd)
            time.sleep(.01)
        return sorted(descendants(tree(), os.getpid()))
    finally:
        for fd in held.values():
            os.close(fd)


def supervise(commands, jobs, work, *, memory_mib, cpus, processes, timeout):
    """Detect/terminate aggregate RSS, process-count and CPU-affinity violations.

    Limits are sampled every 20ms plus scan time, not kernel quotas. RSS sums
    shared pages per process, misses spikes, and excludes swap/kernel memory.
    Affinity is inherited and checked; descendants can change it between scans.
    Call only from a dedicated process with no pre-existing child processes.
    """
    if not Path('/proc/self/stat').exists() or not hasattr(signal, 'pidfd_send_signal'):
        raise RuntimeError('whole-mode supervision requires Linux /proc and pidfds')
    if descendants(tree(), os.getpid()):
        raise RuntimeError('whole-mode supervisor requires a dedicated process')
    libc = ctypes.CDLL(None, use_errno=True)
    previous = ctypes.c_int()
    if libc.prctl(37, ctypes.byref(previous), 0, 0, 0) or libc.prctl(36, 1, 0, 0, 0):
        raise OSError(ctypes.get_errno(), 'child subreaper unavailable')
    affinity = os.sched_getaffinity(0)
    allowed = set(sorted(affinity)[:cpus])
    signals = (signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT)
    handlers = {sig: signal.getsignal(sig) for sig in signals}
    def cancelled(signum, frame):
        for sig in signals:
            signal.signal(sig, signal.SIG_IGN)
        raise KeyboardInterrupt('whole-mode jobs cancelled')
    for sig in signals:
        signal.signal(sig, cancelled)
    launched, running, finished = [], {}, {}
    start = time.monotonic()
    peak, peak_count, max_running = 0, 0, 0
    error = None
    try:
        os.sched_setaffinity(0, allowed)
        pending = iter(commands)
        exhausted = False
        while running or not exhausted:
            while len(running) < jobs and not exhausted:
                try:
                    mode, command = next(pending)
                except StopIteration:
                    exhausted = True
                    break
                folder = work / mode
                folder.mkdir(exist_ok=True)
                with (folder / 'worker.log').open('wb') as log:
                    process = subprocess.Popen(list(map(str, command)), stdout=log, stderr=log,
                                               start_new_session=True)
                launched.append(process)
                running[mode] = (process, time.monotonic())
            max_running = max(max_running, len(running))
            snapshot = tree()
            pids = descendants(snapshot, os.getpid())
            resident = sum(snapshot[p][1] for p in pids)
            peak, peak_count = max(peak, resident), max(peak_count, len(pids))
            if resident > memory_mib * 1024 * 1024:
                raise RuntimeError('whole-mode aggregate RSS limit exceeded')
            if len(pids) > processes:
                raise RuntimeError('whole-mode aggregate process limit exceeded')
            for pid in pids:
                try:
                    if not os.sched_getaffinity(pid) <= allowed:
                        raise RuntimeError('whole-mode CPU affinity limit exceeded')
                except ProcessLookupError:
                    pass
            for mode, (process, began) in list(running.items()):
                code = process.poll()
                if code is not None:
                    finished[mode] = {'returncode': code, 'seconds': time.monotonic() - began,
                                      'started_seconds': began - start,
                                      'finished_seconds': time.monotonic() - start}
                    del running[mode]
                    if code:
                        raise RuntimeError(f'{mode} worker failed ({code}); see {work / mode / "worker.log"}')
                elif time.monotonic() - began > timeout:
                    raise TimeoutError(f'{mode} whole-mode deadline exceeded')
            if running:
                time.sleep(.02)
    except BaseException as exc:
        error = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        # Repeated cancellation must not interrupt a stop/kill/reap sweep.
        for sig in signals:
            signal.signal(sig, signal.SIG_IGN)
        cleanup_error = None
        try:
            survivors = cleanup(launched)
        except BaseException as exc:
            cleanup_error = exc
            survivors = sorted(descendants(tree(), os.getpid()))
            error = f'cleanup failed: {exc}'
        try:
            os.sched_setaffinity(0, affinity)
            libc.prctl(36, previous.value, 0, 0, 0)
            report = {'jobs': jobs, 'cpu_affinity': sorted(allowed), 'memory_limit_mib': memory_mib,
                      'process_limit': processes, 'mode_timeout_seconds': timeout,
                      'peak_tree_rss_bytes': peak, 'peak_processes': peak_count,
                      'max_running_modes': max_running,
                      'seconds': time.monotonic() - start, 'modes': finished,
                      'error': error or ('cleanup left descendants' if survivors else None),
                      'remaining_descendants': survivors}
            (work / 'resources.json').write_text(json.dumps(report, indent=2) + '\n')
        finally:
            for sig, handler in handlers.items():
                signal.signal(sig, handler)
        if cleanup_error:
            raise cleanup_error
        if survivors:
            raise RuntimeError(f'whole-mode cleanup left descendants: {survivors}')
    return report
