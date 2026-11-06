#!/usr/bin/env python3
"""Build a local, host-profiled compiler archive from validated project inputs."""
import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

from package_kit import digest, require, verify

ROOT = Path(__file__).resolve().parents[1]


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ('compiler', 'project', 'metadata', 'output', 'entry'):
        parser.add_argument('--' + field, type=Path, required=True)
    parser.add_argument('--identity', required=True)
    parser.add_argument('--runtime', type=Path, action='append', default=[])
    parser.add_argument('--input', type=Path, action='append', default=[])
    args = parser.parse_args()
    require(platform.system() == 'Linux' and platform.machine() == 'x86_64', 'requires Linux x86-64')
    require(not args.output.exists() and not args.output.is_symlink(), 'archive destination already exists')
    require(args.output.name.endswith('.tar.gz'), 'archive must end in .tar.gz')
    metadata = json.loads(args.metadata.read_text())
    require(metadata['schema'] == 1 and isinstance(metadata['runtime_contract'], str)
            and metadata['runtime_contract'].strip(), 'missing runtime metadata')
    notices = metadata['licenses']
    require(isinstance(notices, list) and notices, 'missing license metadata')
    require({n['component'] for n in notices} >= {'compiler', 'reader', 'runtime'},
            'licenses must identify compiler, reader and runtime')
    license_paths = []
    for notice in notices:
        require(isinstance(notice['file'], str) and notice['file'], 'missing license file')
        path = (args.metadata.parent / notice['file']).resolve()
        require(path.is_file() and path.read_text().strip(), 'missing license notice: ' + str(path))
        license_paths.append(path)
    stages = []
    env = dict(os.environ, LANGBE='llvm', LANGOS='linux')

    def run(command, cwd=None):
        command = [str(p) for p in command]
        result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, timeout=240)
        stages.append(dict(command=command, cwd=str(cwd or Path.cwd()), exit=result.returncode,
                           stdout=result.stdout.decode(errors='replace'), stderr=result.stderr.decode(errors='replace')))
        if result.returncode:
            sys.stderr.buffer.write(result.stderr)
            raise ValueError('package command failed: ' + command[0])
        return result.stdout.decode()

    # Bind the minting compiler to its standard build receipt, including bootstrap
    # and complete compiler source inputs. The project resolver supplies frontend
    # and runtime transitive inputs, including sources outside this checkout.
    build_receipt = ROOT / 'out/build-receipt.json'
    run([sys.executable, ROOT / 'scripts/build_receipt.py', 'check',
         '--input', build_receipt, '--compiler', args.compiler.resolve()], ROOT)
    build = json.loads(build_receipt.read_text())
    require(not build['source']['dirty'], 'package requires a committed compiler build')
    resolved_inputs = [p if p.is_file() else ROOT / p for p in args.input]
    inputs = {str(p.resolve()): digest(p) for p in
              [*resolved_inputs, *args.runtime, args.project, args.entry, args.metadata,
               *license_paths, args.compiler, build_receipt,
               Path(__file__), ROOT / 'scripts/package_kit.py']}
    tools = {}
    for name in ('clang', 'ld', 'ldd', 'getconf', 'python3'):
        selected = env.get('LANG_CLANG') if name == 'clang' else None
        path = Path(selected or shutil.which(name) or '').resolve()
        require(path.is_file() and os.access(path, os.X_OK), 'missing tool: ' + name)
        tools[name] = dict(path=str(path), sha256=digest(path))
    env['LANG_CLANG'] = tools['clang']['path']
    clang_version = run([tools['clang']['path'], '--version'])
    libc = run([tools['getconf']['path'], 'GNU_LIBC_VERSION']).strip()
    # Files remain private until all dependencies and hashes are checked. The
    # archive uses exclusive creation; an existing output is never overwritten.
    with tempfile.TemporaryDirectory(prefix='.lang-package-', dir=args.output.absolute().parent) as temporary:
        work = Path(temporary)
        kit = work / 'kit'
        for name in ('bin', 'example', 'runtime', 'licenses'):
            (kit / name).mkdir(parents=True, exist_ok=True)
        compiler = args.compiler.resolve()
        run([compiler, 'project', 'compiler', args.project.resolve(), '-o', kit / 'bin/compiler'])
        shutil.copyfile(args.entry, kit / 'example' / args.entry.name)
        runtime_sources = []
        for index, source in enumerate(args.runtime):
            name = f'runtime/{index}-{source.name}'
            shutil.copyfile(source, kit / name)
            runtime_sources.append(name)
        selected_notices = []
        for index, (notice, path) in enumerate(zip(notices, license_paths)):
            name = f'licenses/{index}.txt'
            shutil.copyfile(path, kit / name)
            selected_notices.append(dict(component=notice['component'], file=name))
        write(kit / 'runtime/contract.json', dict(schema=1, runtime_contract=metadata['runtime_contract'],
              embedding='Lang AST embedded in bin/compiler; runtime sources retained for inspection; '
                        'their include dependencies are identified in receipt inputs, not an editable source SDK',
              runtime_sources=runtime_sources, licenses=selected_notices))
        shutil.copyfile(ROOT / 'scripts/package_kit.py', kit / 'kit.py')
        example = 'example/' + args.entry.name
        run([kit / 'bin/compiler', kit / example, '--emit=native', '-o', work / 'example-native'])
        shared = {}
        dependency_observations = {}
        for label, binary in [('compiler', kit / 'bin/compiler'), ('example-native', work / 'example-native')]:
            output = run([tools['ldd']['path'], binary])
            dependency_observations[label] = output
            paths = re.findall(r'(?:=>\s+|^\s*)(/[^\s]+)', output, re.M)
            require(paths and 'not found' not in output, 'unresolved dynamic dependencies')
            for path in paths:
                shared[path] = dict(sha256=digest(path), bytes=Path(path).stat().st_size)
        (kit / 'README.md').write_text(
            '# Local compiler kit\n\nLinux x86-64, ' + libc + '; dynamically linked, not runtime-free.\n'
            'Keep the system ELF loader and the shared libraries recorded in receipt.json available.\n'
            'IR needs this host ABI and Python 3 for verification; it needs no Clang or source tree.\n'
            'Native mode additionally needs an explicitly selected Clang and its system linker,\n'
            'libc development objects and headers for the same host profile; ld must be on PATH.\n'
            'Native uses -O0.\n'
            'The receipt records observed tool/library versions and hashes, not a compatibility guarantee.\n'
            'This is trusted native frontend code, not a sandbox. Nothing installs or publishes.\n\n'
            'From the extracted kit directory, with a fresh output directory beside it:\n\n```sh\n'
            'python3 kit.py verify\n'
            'mkdir ../kit-output\n'
            'PATH=/nonexistent /usr/bin/python3 kit.py llvm --output ../kit-output/example.ll\n'
            'python3 kit.py native --clang ' + tools['clang']['path'] + ' --output ../kit-output/example\n'
            '../kit-output/example 99\n../kit-output/example 100\n```\n\n'
            'The example arguments and output belong to the selected language; consult its runtime contract.\n'
            'For a different installation, replace --clang with that host\'s absolute Clang path.\n'
            'The metadata, notices, example and compiler must match their SHA-256 inventory before use.\n'
            'The receipt is an integrity record, not a signature against a malicious distributor.\n')
        artifacts = {str(p.relative_to(kit)): digest(p) for p in sorted(kit.rglob('*')) if p.is_file()}
        receipt = dict(schema=1, example=example, metadata='runtime/contract.json', artifacts=artifacts,
                       host=dict(os=platform.system(), architecture=platform.machine(), kernel=platform.release(),
                                 libc=libc),
                       dependencies=dict(linkage='dynamic', shared_libraries=shared,
                                         observations=dependency_observations, native_optimization='-O0',
                                         needs=['Python 3 for kit verifier', 'ELF loader and system libc',
                                                'native only: explicitly selected Clang, linker and libc development files']),
                       project_identity=args.identity, inputs_sha256=inputs,
                       compiler_build=build, tools=tools, clang_version=clang_version,
                       commands=stages)
        write(kit / 'receipt.json', receipt)
        verify(kit)
        require(all(digest(p) == h for p, h in inputs.items()), 'input hash changed during packaging')
        require(all(digest(t['path']) == t['sha256'] for t in tools.values()), 'tool hash changed during packaging')
        require(all(digest(p) == d['sha256'] for p, d in shared.items()), 'library hash changed during packaging')
        # Recheck the compiler receipt, including its source inventory, after minting.
        run([sys.executable, ROOT / 'scripts/build_receipt.py', 'check',
             '--input', build_receipt, '--compiler', compiler], ROOT)
        write(kit / 'receipt.json', receipt)
        verify(kit)
        with args.output.open('xb') as target:
            with tarfile.open(fileobj=target, mode='w:gz') as archive:
                archive.add(kit, arcname='kit')
    print('Packaged ' + str(args.output))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print('package: ' + str(error), file=sys.stderr)
        sys.exit(1)
