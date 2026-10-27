#!/usr/bin/env python3
"""Controlled-fixture AOT engine behind H compile/call hooks.

This is a process isolation boundary, not a qualified native sandbox. Until a
confinement engine is qualified, only the checked-in fixture manifest can run,
and only with the explicit --controlled-fixtures flag. No source RPC exists.
"""
import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import resource
import signal
import subprocess
import sys
import tempfile
import uuid

from stage_protocol import Value, WireError, frame, unframe, read_frame, TAGS, MAX_BYTES

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / 'test/staging/fixtures.json'

class StageError(RuntimeError):
    pass

@dataclass(frozen=True)
class Artifact:
    path: Path
    digest: str
    signature: tuple
    result: str
    execution_host: str
    output_target: Value


def limits():
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_FSIZE, (64*1024*1024, 64*1024*1024))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


class Host:
    """H owns artifact capabilities; serialized descriptors grant no execution.

    Engine hooks consume/produce the same byte frames. Each subprocess starts
    by exec, with private working storage and a sanitized host-target environment.
    Output-target data is opaque to the execution engine.
    """
    worker_timeout = 90

    def __init__(self, compiler, storage, *, controlled_fixtures=False):
        if not controlled_fixtures: raise StageError('native-confinement-unavailable')
        self.compiler = Path(compiler).resolve(strict=True)
        self.storage = Path(storage).resolve()
        self.storage.mkdir(parents=True, exist_ok=True)
        self.fixtures = json.loads(MANIFEST.read_text())
        self.artifacts = {}
        self.compile_hook = self._aot_compile
        self.call_hook = self._aot_call
        self.host = platform.system().lower()
        if self.host not in ('linux', 'darwin'): raise StageError('unsupported-execution-host')
        self.env = {k: os.environ[k] for k in ('PATH', 'LANG_ROOT') if k in os.environ}
        self.env.update(LANGBE='llvm', LANGOS='macos' if self.host == 'darwin' else 'linux',
                        LANG_LAYOUT_PROFILE='audited-slots-v1', LANG_STAGE_FRESH_COMPILER='0')
        self.diagnostic_index = 0

    def run(self, argv, directory, data=b''):
        env = dict(self.env, LANG_CACHE=str(directory / 'cache'), TMPDIR=str(directory))
        # Bounded spool files keep a misbehaving fixture from exhausting H's
        # memory. stderr is a separate channel throughout; it is never parsed.
        with tempfile.TemporaryFile(dir=directory) as stdout, tempfile.TemporaryFile(dir=directory) as stderr:
            process = subprocess.Popen(argv, cwd=directory, env=env, stdin=subprocess.PIPE,
                                       stdout=stdout, stderr=stderr, close_fds=True,
                                       start_new_session=True, preexec_fn=limits)
            timed_out = False
            try: process.communicate(data, timeout=self.worker_timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                try:
                    try: os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError: pass
                finally:
                    process.communicate()
            try:
                stdout.seek(0); stderr.seek(0)
                output = stdout.read(MAX_BYTES + 17)
                diagnostic = stderr.read(MAX_BYTES)
                self.diagnostic_index += 1
                prefix = directory / ('process-' + str(self.diagnostic_index))
                prefix.with_suffix('.stderr').write_bytes(diagnostic)
                prefix.with_suffix('.stdout').write_bytes(output)
                receipt = {'argv': list(map(str, argv)), 'exit': process.returncode}
                if timed_out: receipt['timed_out'] = True
                prefix.with_suffix('.json').write_text(json.dumps(receipt)+'\n')
            except Exception:
                if not timed_out: raise
                # Publication is best effort after the worker has been reaped.
            if timed_out: raise StageError('worker-deadline')
        if process.returncode: raise StageError('worker-failed: ' + diagnostic.decode(errors='replace')[:2000])
        if len(output) > MAX_BYTES + 16: raise StageError('worker-output-limit')
        return output

    def snapshot(self, relative, job, seen=None):
        seen = set() if seen is None else seen
        if relative in seen: return
        seen.add(relative)
        if relative == 'std/os.lang':
            target = job / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            dependency = 'std/os/libc_macos.lang' if self.host == 'darwin' else 'std/os/libc.lang'
            target.write_text('include \"'+dependency+'\"\n')
            self.snapshot(dependency, job, seen)
            return
        source = (ROOT / relative).resolve()
        if not source.is_relative_to(ROOT) or not source.is_file(): raise StageError('missing-import: ' + relative)
        text = source.read_text()
        target = job / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        for dependency in re.findall(r'^\s*include\s+"([^"]+)"', text, re.M):
            self.snapshot(dependency, job, seen)

    def compile(self, fixture, signature, result, output_target):
        spec = self.fixtures.get(fixture)
        if spec is None: raise StageError('uncontrolled-source')
        if list(signature) != spec['params'] or result != spec['result']: raise StageError('wrong-signature')
        if output_target.kind != 'descriptor': raise StageError('output-target-descriptor')
        # Copy immediately; neither caller mutations nor target addresses can
        # change a pending compile request or an admitted artifact.
        output_target = unframe(frame(output_target))
        artifact = self.compile_hook(spec, output_target)
        token = uuid.uuid4().hex
        self.artifacts[token] = artifact
        return token

    def _aot_compile(self, spec, output_target):
        job = Path(tempfile.mkdtemp(prefix='compile-', dir=self.storage))
        self.snapshot('std/stage.lang', job)
        self.snapshot(spec['source'], job)
        # The generated wrapper has a single copied-value entry signature.
        # Language-specific admission stays in the fixture manifest.
        wrapper = job / 'entry.lang'
        wrapper.write_text('include "std/stage.lang"\ninclude "'+spec['source']+'"\n'
                           'func main() i64 { var args *StageValue = stage_read(); '
                           'stage_write('+spec['entry']+'(args)); return 0; }\n')
        ir = job / 'entry.ll'
        self.run([str(self.compiler), str(wrapper), '-o', str(ir)], job)
        pending = job / 'entry.pending'
        self.run(['clang', '-O0', str(ir), '-o', str(pending)], job)
        # Unique paths, no old executable to reuse, publish only a complete
        # linked executable. A failed compile never returns a capability.
        with pending.open('rb') as f: os.fsync(f.fileno())
        executable = job / 'entry'
        os.replace(pending, executable)
        fd = os.open(job, os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)
        digest = hashlib.sha256(executable.read_bytes()).hexdigest()
        return Artifact(executable, digest, tuple(spec['params']), spec['result'], self.host, output_target)

    def call(self, token, args):
        if type(token) is not str: raise StageError('unknown-artifact')
        artifact = self.artifacts.get(token)
        if artifact is None: raise StageError('unknown-artifact')
        # Frame first to reject cycles/foreign native values before traversal.
        request = frame(args)
        copied = unframe(request)
        if copied.kind != 'list' or tuple(v.kind for v in copied.data) != artifact.signature:
            raise StageError('wrong-signature')
        response = self.call_hook(artifact, request)
        value = unframe(response, 2)
        if value.kind != artifact.result: raise StageError('wrong-result-signature')
        return value

    def _aot_call(self, artifact, request):
        if hashlib.sha256(artifact.path.read_bytes()).hexdigest() != artifact.digest:
            raise StageError('artifact-integrity')
        job = Path(tempfile.mkdtemp(prefix='call-', dir=self.storage))
        return self.run([str(artifact.path)], job, request)

    def dispatch(self, request):
        if request.kind != 'record': raise StageError('request-record')
        fields = request.data
        def get(key, kind):
            value = fields.get(key)
            if value is None or value.kind != kind: raise StageError('request-field: '+key)
            return value.data
        op = get('op', 'text')
        if op == 'compile':
            signature = get('signature', 'list')
            if any(v.kind != 'text' or v.data not in TAGS for v in signature): raise StageError('wrong-signature')
            token = self.compile(get('fixture', 'text'), [v.data for v in signature],
                                 get('result', 'text'), Value('descriptor', get('output_target', 'descriptor')))
            return Value('text', token)
        if op == 'call':
            return self.call(get('artifact', 'text'), Value('list', get('args', 'list')))
        raise StageError('request-operation')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--controlled-fixtures', action='store_true')
    parser.add_argument('--compiler', type=Path, required=True)
    parser.add_argument('--storage', type=Path, required=True)
    args = parser.parse_args()
    host = Host(args.compiler, args.storage, controlled_fixtures=args.controlled_fixtures)
    while True:
        first = sys.stdin.buffer.peek(1)
        if not first: return
        try:
            request = unframe(read_frame(sys.stdin.buffer), 1)
        except WireError as error:
            # A malformed frame has no trustworthy next boundary.
            sys.stdout.buffer.write(frame(Value('text', str(error)), 3)); sys.stdout.buffer.flush()
            return
        try: response = frame(host.dispatch(request), 2)
        except (StageError, WireError, OSError, ValueError) as error:
            response = frame(Value('text', str(error)), 3)
        sys.stdout.buffer.write(response); sys.stdout.buffer.flush()

if __name__ == '__main__':
    main()
