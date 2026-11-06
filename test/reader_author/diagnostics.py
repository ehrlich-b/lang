#!/usr/bin/env python3
"""Shipping diagnostic fragment: native records, text, browser Wasm and rejection."""
import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import time
import sys
import uuid

from route import ROOT, Replay, dump, require, sha


class DiagnosticReplay(Replay):
    """Monitor aggregate resident memory of the sequential fragment process tree."""

    @staticmethod
    def resident_tree(pid):
        total = 0
        pending = [pid]
        seen = set()
        while pending:
            child = pending.pop()
            if child in seen:
                continue
            seen.add(child)
            try:
                total += int(Path(f"/proc/{child}/statm").read_text().split()[1]) * os.sysconf("SC_PAGE_SIZE")
                pending.extend(int(p) for p in Path(f"/proc/{child}/task/{child}/children").read_text().split())
            except (FileNotFoundError, ProcessLookupError):
                pass
        return total

    def run(self, command, name, cwd, expected=0):
        prefix = self.evidence / f"{len(self.rows) + 1:03d}-{name}"
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        start = time.perf_counter()
        peak = 0
        failure = None
        with prefix.with_suffix(".stdout").open("wb") as stdout, prefix.with_suffix(".stderr").open("wb") as stderr:
            process = subprocess.Popen(command, cwd=cwd, env=self.env, stdout=stdout, stderr=stderr, start_new_session=True)
            while process.poll() is None:
                peak = max(peak, self.resident_tree(os.getpid()))
                if peak > 2 * 1024**3 or time.perf_counter() - start > 240:
                    failure = "aggregate memory limit" if peak > 2 * 1024**3 else "timeout"
                    os.killpg(process.pid, signal.SIGKILL)
                    break
                time.sleep(0.05)
            status = process.wait()
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        row = {"name": name, "command": command, "cwd": str(cwd),
               "environment": {k: self.env[k] for k in ("JOBS", "LANGBE", "LANGOS", "LANG_CACHE", "TMPDIR")},
               "exit": status, "wall_seconds": time.perf_counter() - start,
               "cpu_user_seconds": after.ru_utime - before.ru_utime,
               "cpu_system_seconds": after.ru_stime - before.ru_stime,
               "aggregate_peak_rss_bytes_sampled": peak, "monitor_failure": failure,
               "stdout": prefix.name + ".stdout", "stderr": prefix.name + ".stderr"}
        dump(prefix.with_suffix(".json"), row)
        self.rows.append(row)
        dump(self.evidence / "stages.json", self.rows)
        require(failure is None and status == expected,
                f"{name}: expected exit {expected}, got {status} ({failure}); see {prefix}.stderr")
        return subprocess.CompletedProcess(command, status, prefix.with_suffix(".stdout").read_bytes(), prefix.with_suffix(".stderr").read_bytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['shipping'], required=True)
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    os.nice(10)
    cpus = sorted(os.sched_getaffinity(0))[:2]
    os.sched_setaffinity(0, cpus)
    ceiling = 2 * 1024**3
    hard = resource.getrlimit(resource.RLIMIT_AS)[1]
    if hard != resource.RLIM_INFINITY:
        ceiling = min(ceiling, hard)
    resource.setrlimit(resource.RLIMIT_AS, (ceiling, ceiling))
    token = uuid.uuid4().hex
    evidence = (args.evidence or ROOT.parent / 'evidence' / ('diagnostics-' + token)).resolve()
    require(ROOT != evidence and ROOT not in evidence.parents, 'evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=False)
    scratch = ROOT.parent / 'scratch' / ('diagnostics-' + token)
    scratch.mkdir(parents=True)
    replay = DiagnosticReplay(evidence, scratch)
    print(f'evidence: {evidence}', flush=True)
    try:
        status = replay.run(['git', 'status', '--porcelain', '--untracked-files=all'], 'clean', ROOT)
        require(not status.stdout, 'commit candidate before running fragment')
        head = replay.run(['git', 'rev-parse', 'HEAD'], 'head', ROOT).stdout.decode().strip()
        replay.run(['git', 'merge-base', '--is-ancestor',
                    'fcf6dd72f2296e28543132213d301dbe0d9a2b08', head], 'base', ROOT)
        replay.run(['git', 'diff', '--exit-code', 'fcf6dd72f2296e28543132213d301dbe0d9a2b08',
                    '--', 'bootstrap/current', 'web/stdlib.js', 'web/stdlib.json', 'web/compiler.wasm'],
                   'protected-artifacts', ROOT)
        clone = scratch / 'repo'
        replay.run(['git', 'clone', '--no-hardlinks', '--quiet', str(ROOT), str(clone)], 'clone', ROOT)
        paths = replay.run(['git', 'ls-files', '-z'], 'inputs', clone).stdout.decode().split('\0')
        tools = {name: {'path': str(Path(shutil.which(name)).resolve()),
                        'sha256': sha(Path(shutil.which(name)).resolve())}
                 for name in ('python3', 'make', 'clang', 'ld', 'git', 'node')}
        dump(evidence / 'identity.json', {'head': head,
             'source_sha256': {p: sha(clone / p) for p in paths if p and (clone / p).is_file()},
             'tools': tools, 'limits': {'cpus': cpus, 'address_space_bytes': ceiling, 'JOBS': 2},
             'assumptions': 'Linux x86-64 libc; sequential commands; Node executes browser host Wasm with trap handler disabled to stay within address-space cap; no OS kernel tests; no web artifact regeneration; unchanged visual layout'})
        replay.run(['make', 'init'], 'seed', clone)
        replay.run(['make', 'build'], 'build', clone)
        compiler = clone / 'out/lang_next'
        shipping = 'example/shipping/shipping.lang'
        fixture = clone / 'test/reader_author/fixtures'
        observations = []
        inputs = {}

        def retain_input(path):
            relative = path.relative_to(scratch)
            target = evidence / 'inputs' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            inputs[str(relative)] = sha(path)
            dump(evidence / 'fixture-inputs.json', inputs)


        def diagnostic(path, reader=shipping, name='case', expected_code=None):
            commands = [str(compiler), 'read', reader, str(path)]
            text = replay.run(commands, name + '-text', clone, expected=1)
            result = replay.run([*commands, '--diagnostics=json'], name + '-json', clone, expected=1)
            require(not result.stdout and not text.stdout, name + ': diagnostic leaked into AST')
            records = [json.loads(line) for line in result.stderr.splitlines()]
            require(len(records) == 1, name + ': expected one diagnostic')
            d = records[0]
            require(d['path'] == str(path) and d['source_id'] > 0, name + ': wrong source identity')
            if expected_code:
                require(d['code'] == expected_code, name + ': wrong diagnostic code')
            if d['span']:
                data = path.read_bytes()
                start, end = d['span']['start'], d['span']['end']
                require(0 <= start <= end <= len(data), name + ': bad bytes')
                data[:start].decode(); data[start:end].decode()
                line = data[:start].count(b'\n') + 1
                column = len(data[:start].rsplit(b'\n', 1)[-1]) + 1
                expected = f"{path}:{line}:{column}: {d['message']}"
                if d['code'] == 'reader-syntax':
                    expected += f' @{start}:{end}'
            else:
                expected = f"{path}: {d['message']}"
            if d['code'] == 'reader-diagnostic-invalid':
                expected = f'{path}: invalid reader diagnostic'
            require(text.stderr == (expected + '\n').encode(), name + ': JSON/text differ')
            saved = evidence / (name + '.record.json')
            dump(saved, d)
            observations.append({'case': name, 'record': d})
            return d, saved

        duplicate_path = fixture / 'left/policy.shipping'
        syntax_path = fixture / 'right/policy.shipping'
        duplicate, duplicate_record = diagnostic(duplicate_path, name='duplicate', expected_code='shipping-duplicate')
        require(duplicate_path.read_bytes()[duplicate['span']['start']:duplicate['span']['end']] == b'base',
                'duplicate must select exact second setting')
        require(duplicate['span']['start'] == duplicate_path.read_bytes().rindex(b'base'), 'duplicate selected first setting')
        syntax, syntax_record = diagnostic(syntax_path, name='syntax', expected_code='reader-syntax')
        require(syntax_path.read_bytes()[syntax['span']['start']:syntax['span']['end']] == b'free_over',
                'backtracking lost furthest token')
        require("expected ';'" in syntax['message'], 'furthest expectation lost')
        require(duplicate['path'] != syntax['path'], 'same basename collapsed')
        valid = replay.run([str(compiler), 'read', shipping, 'example/shipping/policy.shipping'], 'valid-ast', clone)
        require(valid.stdout.startswith(b'(program') and not valid.stderr, 'valid AST transport changed')
        broken = 'test/reader_author/fixtures/broken.lang'
        broken_cases = []
        for value in ['missing', 'implementation', 'raw', 'forged', 'reverse', 'overflow', 'é']:
            path = scratch / (value + '.broken')
            path.write_text(value)
            retain_input(path)
            code = {'missing': 'missing-span', 'implementation': 'reader-implementation'}.get(value, 'reader-diagnostic-invalid')
            record, saved = diagnostic(path, broken, value, code)
            require(record['span'] is None, 'missing/bad span gained a position')
            require(record['category'] == ('guest' if value == 'missing' else 'reader'), 'reader implementation misclassified')
            broken_cases.append((path, saved))
        nested = replay.run([str(compiler), 'test/reader_author/fixtures/nested.lang',
                    '--diagnostics=json', '-o', str(scratch / 'nested.ll')], 'nested', clone, expected=1)
        nd = [json.loads(line) for line in nested.stderr.splitlines()]
        require(len(nd) == 2 and nd[0]['code'] == 'shipping-duplicate' and
                nd[1]['message'] == 'error: compilation failed', 'nested guest failure lost')
        require(len(nd[0]['origin_chain']) >= 2, 'nested expansion chain lost')
        require(any(o['path'].endswith('nested.lang') for o in nd[0]['origin_chain']), 'outer source lost')

        inline = replay.run([str(compiler), 'test/reader_author/fixtures/inline.lang',
                             '--diagnostics=json', '-o', str(scratch / 'inline.ll')], 'inline-range', clone, expected=1)
        inline_records = [json.loads(line) for line in inline.stderr.splitlines()]
        ir = inline_records[0]
        raw = (fixture / 'inline.lang').read_bytes()
        require(ir['code'] == 'shipping-duplicate' and ir['span']['start'] == raw.rindex(b'base') and
                raw[ir['span']['start']:ir['span']['end']] == b'base', 'inline invocation bytes not mapped to file')

        # Minted compilers use the same host mapping and JSON format.
        minted = scratch / 'shippingc'
        replay.run([str(compiler), 'compiler', 'shipping', shipping, '-o', str(minted)], 'mint', clone)
        minted_result = replay.run([str(minted), str(duplicate_path), '--diagnostics=json',
                                   '-o', str(scratch / 'rejected.ll')], 'minted-json', clone, expected=1)
        md = json.loads(minted_result.stderr)
        for field in ('code', 'path', 'span', 'message', 'category'):
            require(md[field] == duplicate[field], 'minted compiler differs: ' + field)
        require(not (scratch / 'rejected.ll').exists(), 'minted compiler accepted diagnostic as AST')
        # Equal basenames remain distinct immutable sources in one compilation.
        first = scratch / 'two/left/policy.shipping'
        second = scratch / 'two/right/policy.shipping'
        first.parent.mkdir(parents=True); second.parent.mkdir(parents=True)
        first.write_bytes((clone / 'example/shipping/policy.shipping').read_bytes())
        second.write_bytes(duplicate_path.read_bytes())
        retain_input(first); retain_input(second)
        same = replay.run([str(minted), str(first), str(second), '--diagnostics=json',
                           '-o', str(scratch / 'same.ll')], 'same-names-one-compilation', clone, expected=1)
        sd = json.loads(same.stderr)
        require(sd['path'] == str(second) and sd['source_id'] > md['source_id'], 'same-name source IDs collapsed')


        for key, source in [('shipping', shipping), ('broken', broken)]:
            harness = scratch / (key + '-harness.lang')
            harness.write_text(f'''include "std/core.lang"
include "{source}"
func main() *u8 {{
    var input *PhaseBuffer = phase_read_fd(0, phase_limit(), "<reader-input>");
    reader_diagnostic_wire = 1;
    return {key}(input.data);
}}
''')
            retain_input(harness)
            wasm = scratch / (key + '.wasm')
            old = replay.env.get('LANGBE')
            replay.env['LANGBE'] = 'wasm'
            replay.run([str(compiler), str(harness), '-o', str(wasm)], 'wasm-' + key, clone)
            replay.env['LANGBE'] = old
            cases = [(duplicate_path, duplicate_record), (syntax_path, syntax_record)] if key == 'shipping' else broken_cases
            for index, (path, saved) in enumerate(cases):
                replay.run(['node', '--disable-wasm-trap-handler', '--max-old-space-size=256', 'test/reader_author/browser_diagnostics.cjs', str(wasm), str(path), str(saved), key],
                           f'browser-{key}-{index}', clone)
        dump(evidence / 'observations.json', observations)
        dump(evidence / 'artifacts.json', {'compiler': sha(compiler.resolve()), 'minted': sha(minted)})
        dump(evidence / 'result.json', {'pass': True, 'head': head, 'commands': len(replay.rows)})
        print('PASS shipping diagnostics: exact guest bytes, text/JSON, nested origins, native/browser rejection')
        return 0
    except Exception as error:
        dump(evidence / 'result.json', {'pass': False, 'error': str(error)})
        print(f'FAIL: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
