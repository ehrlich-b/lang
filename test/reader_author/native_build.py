#!/usr/bin/env python3
"""Prove the native shipping build fragment using real subprocesses and receipts."""
import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import sys
import uuid

from project import ProjectReplay
from route import ROOT, dump, require, sha


class NativeReplay(ProjectReplay):
    def run(self, command, name, cwd, expected=0):
        try:
            return super().run(command, name, cwd, expected)
        finally:
            if self.rows and self.rows[-1]['name'] == name:
                row = self.rows[-1]
                row['environment'].update({k: v for k, v in self.env.items()
                                           if k.startswith('NATIVE_') or k == 'LANG_CLANG'})
                dump(self.evidence / (Path(row['stdout']).stem + '.json'), row)
                dump(self.evidence / 'stages.json', self.rows)


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
    evidence = (args.evidence or ROOT.parent / 'evidence' / ('native-' + token)).resolve()
    require(evidence != ROOT and ROOT not in evidence.parents, 'evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=False)
    scratch = ROOT.parent / 'scratch' / ('native-' + token)
    scratch.mkdir(parents=True)
    replay = NativeReplay(evidence, scratch)
    replay.env.update(MAKEFLAGS='-j2', PYTHONDONTWRITEBYTECODE='1')
    # Verification's fragment selector must not affect the compiler build.
    replay.env.pop('VERIFY_CASE', None)
    replay.env.pop('LANG_CLANG', None)
    print(f'evidence: {evidence}', flush=True)
    try:
        status = replay.run(['git', 'status', '--porcelain', '--untracked-files=all'], 'clean', ROOT)
        require(not status.stdout, 'commit the candidate before replaying it')
        head = replay.run(['git', 'rev-parse', 'HEAD'], 'head', ROOT).stdout.decode().strip()
        replay.run(['git', 'merge-base', '--is-ancestor', 'ed73e20a974eccdba76e0cdb4ca9409260ffa37f', head],
                   'required-base', ROOT)
        replay.run(['git', 'diff', '--exit-code', 'ed73e20a974eccdba76e0cdb4ca9409260ffa37f',
                    head, '--', 'bootstrap/current', 'web'], 'protected-inputs-unchanged', ROOT)
        clone = scratch / 'repo'
        replay.run(['git', 'clone', '--no-hardlinks', '--quiet', str(ROOT), str(clone)], 'clone', ROOT)
        files = replay.run(['git', 'ls-files', '-z'], 'inputs', clone).stdout.decode().split('\0')
        hashes = {p: sha(clone / p) for p in files if p and (clone / p).is_file()}
        tools = {}
        for name in ('make', 'clang', 'ld', 'python3', 'git'):
            found = shutil.which(name)
            require(found is not None, name + ' is required')
            path = Path(found).resolve()
            tools[name] = {'path': str(path), 'sha256': sha(path)}
        dump(evidence / 'identity.json', {
            'head': head, 'source_sha256': hashes, 'tools': tools,
            'limits': {'cpus': cpus, 'address_space_bytes': ceiling, 'JOBS': 2, 'MAKEFLAGS': '-j2'},
            'assumptions': 'Linux x86-64 libc; trusted native readers; Clang family from manifest; '
                           'native default -O0; no OS kernel tests, fixed points or browser rebuilds'})
        replay.run(['make', 'init'], 'init', clone)
        replay.run(['make', 'build'], 'build-current-sources', clone)
        compiler = str(clone / 'out/lang_next')
        fixtures = clone / 'test/reader_author/fixtures/native_build'
        shipping = clone / 'example/shipping'
        manifest = shipping / 'project.lang-project'
        source = shipping / 'policy.shipping'
        exe = scratch / 'shipping'

        def build(name, guest=source, project=manifest, output=exe, expected=0, emit=None):
            command = [compiler, 'build', '--project', str(project), str(guest), '-o', str(output)]
            if emit:
                command += ['--emit=' + emit]
            result = replay.run(command, name, scratch, expected)
            require(not list(output.parent.glob(output.name + '.lang-build-*')), name + ': staging files leaked')
            if expected:
                require(not output.exists(), name + ': stale or partial output survived')
                require(b'Built ' not in result.stdout, name + ': failure announced success')
            return result

        result = build('shipping-valid')
        require(b'optimization=-O0' in result.stderr, 'default optimization was not recorded')
        require(exe.read_bytes().startswith(b'\x7fELF'), 'build did not publish a native executable')
        saved_exe = exe.read_bytes()

        def seed_previous():
            exe.write_bytes(saved_exe)
            exe.chmod(0o755)
        for total, expected in [('0', b'10\n'), ('99', b'10\n'), ('100', b'0\n'), ('120', b'0\n')]:
            path = replay.env['PATH']
            replay.env['PATH'] = '/nonexistent'
            result = replay.run([str(exe), total], 'runtime-no-tools-' + total, scratch)
            replay.env['PATH'] = path
            require(result.stdout == expected and not result.stderr, 'shipping runtime mismatch')

        # Inspectable alternatives use the same reader and validation boundary.
        ast = scratch / 'policy.ast'
        llvm = scratch / 'policy.ll'
        replay.env['LANG_CLANG'] = str(scratch / 'absent final toolchain')
        build('emit-ast', output=ast, emit='ast')
        build('emit-llvm', output=llvm, emit='llvm')
        replay.env.pop('LANG_CLANG')
        require(b'(binop >=' in ast.read_bytes() and b'(ident total)' in ast.read_bytes(), 'wrong shared AST')
        require(b'define i64 @main' in llvm.read_bytes(), 'LLVM is not inspectable')
        shutil.copyfile(ast, evidence / ast.name)
        shutil.copyfile(llvm, evidence / llvm.name)
        replay.run([tools['clang']['path'], '-O0', str(llvm), '-o', str(scratch / 'inspected')], 'link-inspected-llvm', scratch)
        result = replay.run([str(scratch / 'inspected'), '100'], 'run-inspected-llvm', scratch)
        require(result.stdout == b'0\n', 'inspectable LLVM disagrees with native output')

        # Each negative begins with the actual prior success artifact.
        seed_previous()
        result = build('syntax-error', guest=fixtures / 'syntax.shipping', expected=1)
        require(b'native build reader failed' in result.stderr and b'expected' in result.stderr,
                'reader failure lost its stage or original diagnostic')
        seed_previous()
        result = build('reader-exit-status', guest=fixtures / 'guest.readerexit',
                       project=fixtures / 'exit.lang-project', expected=37)
        require(b'reader exit control: original diagnostic' in result.stderr and b'exit 37' in result.stderr,
                'reader exit status or original diagnostic was lost')
        seed_previous()
        result = build('validation-error', guest=fixtures / 'guest.invalid',
                       project=fixtures / 'invalid.lang-project', expected=1)
        require(b'native build validation failed' in result.stderr and b'ast' in result.stderr.lower(),
                'invalid shared AST reached LLVM or lost its diagnostic')

        # Invalid options invalidate the prior native output, regardless of ordering.
        for before_output in (False, True):
            seed_previous()
            command = [compiler, 'build', '--project', str(manifest), str(source)]
            if before_output:
                command += ['--emit=bogus']
            command += ['-o', str(exe)]
            if not before_output:
                command += ['--emit=bogus']
            result = replay.run(command, 'invalid-emit-' + str(before_output), scratch, expected=1)
            require(b'--emit must be native, ast or llvm' in result.stderr and not exe.exists(),
                    'invalid emit left a previous executable or lost its diagnostic')

        # A configured executable that cannot be launched is a toolchain failure.
        seed_previous()
        missing_tool = scratch / 'missing configured clang'
        replay.env['LANG_CLANG'] = str(missing_tool)
        result = build('missing-configured-clang', expected=127)
        require(b'toolchain could not execute:' in result.stderr and
                str(missing_tool).encode() in result.stderr and b'optimizer/object' not in result.stderr,
                'configured Clang launch failure was not attributed to the toolchain')
        replay.env.pop('LANG_CLANG')

        # Warm shipping reader cache allows this to target the final tool lookup.
        path = replay.env['PATH']
        replay.env['PATH'] = '/nonexistent'
        seed_previous()
        result = build('missing-clang', expected=127)
        replay.env['PATH'] = path
        require(b'toolchain: clang not found in PATH' in result.stderr, 'missing Clang was not distinct')

        # An explicit executable path with spaces is honored with an argv vector.
        tool = scratch / 'configured tool with spaces'
        shutil.copyfile(fixtures / 'clang_proxy.py', tool)
        tool.chmod(0o755)
        log = evidence / 'native-tool-argv.jsonl'
        replay.env.update(LANG_CLANG=str(tool), NATIVE_TOOL_LOG=str(log),
                          NATIVE_REAL_CLANG=tools['clang']['path'], NATIVE_BAD_IR=str(fixtures / 'malformed.ll'))
        seed_previous()
        result = build('optimizer-error', expected=1)
        require(b'optimizer/object compilation failed' in result.stderr and b'expected top-level entity' in result.stderr,
                'Clang optimizer diagnostic was not preserved')
        replay.env.pop('NATIVE_BAD_IR')
        build('configured-tool')
        calls = [json.loads(line) for line in log.read_text().splitlines()]
        require(any(args[:2] == ['-O0', '-c'] for args in calls), 'driver did not explicitly select -O0')
        require(any(args[0].endswith('/guest.o') and args[1] == '-o' for args in calls), 'link is not a separate stage')
        replay.env.pop('LANG_CLANG')

        broken = scratch / 'unresolved runtime'
        shutil.copytree(shipping, broken)
        runtime = broken / 'runtime.lang'
        runtime.write_text(runtime.read_text().replace('print_int(fee); println(""); return 0;',
            'return native_build_missing_link_symbol(fee);') +
            '\nextern func native_build_missing_link_symbol(fee i64) i64;\n')
        shutil.copyfile(runtime, evidence / 'unresolved-runtime.lang')
        result = build('linker-error', guest=broken / 'policy.shipping',
                       project=broken / 'project.lang-project', expected=1)
        require(b'native build linker failed' in result.stderr and b'native_build_missing_link_symbol' in result.stderr,
                'linker failure lost its original unresolved symbol')

        quoted = scratch / 'project with spaces and "quotes'
        shutil.copytree(shipping, quoted)
        spaced_exe = scratch / 'result with spaces and "quotes'
        build('paths-with-spaces', guest=quoted / 'reordered.shipping',
              project=quoted / 'project.lang-project', output=spaced_exe)
        replay.env['PATH'] = '/nonexistent'
        result = replay.run([str(spaced_exe), '99'], 'spaced-runtime-no-tools', scratch)
        replay.env['PATH'] = path
        require(result.stdout == b'10\n' and not result.stderr, 'quoted paths changed execution')

        # Existing unrelated inputs and symlinks must survive a mistaken -o.
        original = sha(source)
        result = replay.run([compiler, 'build', '--project', str(manifest), str(source), '-o', str(source)],
                            'refuse-source-overwrite', scratch, expected=1)
        require(b'overwrite an input' in result.stderr and sha(source) == original, 'source was overwritten')
        sentinel = scratch / 'unrelated.txt'
        sentinel.write_text('preserve me\n')
        replay.run([compiler, 'build', '--project', str(manifest), str(source), '-o', str(sentinel)],
                   'refuse-unrelated-output', scratch, expected=1)
        require(sentinel.read_text() == 'preserve me\n', 'unrelated destination was destroyed')
        link = scratch / 'output-symlink'
        link.symlink_to(spaced_exe)
        prior = sha(spaced_exe)
        replay.run([compiler, 'build', '--project', str(manifest), str(source), '-o', str(link)],
                   'refuse-output-symlink', scratch, expected=1)
        require(link.is_symlink() and sha(spaced_exe) == prior, 'symlink destination was destroyed')
        # Invalid manifests also invalidate the previous native success.
        seed_previous()
        build('manifest-error', project=clone / 'test/reader_author/fixtures/project/version.lang-project', expected=1)
        require(all(sha(clone / p) == h for p, h in hashes.items()), 'test edited committed source inputs')
        dump(evidence / 'artifacts.json', {'compiler': sha(compiler), 'native': sha(spaced_exe),
             'ast': sha(ast), 'llvm': sha(llvm), 'configured_tool': sha(tool), 'unresolved_runtime': sha(runtime)})
        dump(evidence / 'result.json', {'pass': True, 'head': head, 'observations': len(replay.rows)})
        print('PASS native shipping: staged build, AST/LLVM, -O0, runtime without tools, reader/validation/optimizer/linker failures, missing Clang, quoted paths and stale output')
        return 0
    except Exception as error:
        dump(evidence / 'result.json', {'pass': False, 'error': str(error)})
        print(f'FAIL: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
