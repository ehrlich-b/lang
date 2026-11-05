"""Small native Scheme toolchain; all generated files belong to the caller."""
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def invoke(command, log, timeout=120):
    env = dict(os.environ, LANGBE='llvm', LANGLIBC='libc')
    with Path(log).open('w') as stream:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream,
                                stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'{command[0]} exited {result.returncode}: {log}')


def compiler(folder):
    folder = Path(folder).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    output = folder / 'schemec'
    invoke([os.environ.get('COMPILER', 'out/lang'), 'compiler', 'scheme',
            'example/scheme/scheme.lang', '--runtime', 'example/scheme/runtime.lang',
            '-o', str(output)], folder / 'compiler.log')
    return output


def compile_program(cc, source, folder, name, optimization='0'):
    folder = Path(folder).resolve()
    ir, binary = folder / f'{name}.ll', folder / name
    invoke([str(cc), str(source), '-o', str(ir)], folder / f'{name}.compile.log')
    invoke(['clang', '-O' + optimization, str(ir), '-o', str(binary)],
           folder / f'{name}.link.log')
    return binary
