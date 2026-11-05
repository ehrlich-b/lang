#!/usr/bin/env python3
"""Check effects in debug modules linked at different optimization levels."""
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
compiler = str(Path(os.environ.get('COMPILER', 'out/lang_next')).resolve())
cases = {
    'test/effects/two_performs.lang': b'500491\n',
    'test/effects/two_handlers.lang': b'2268\n',
    'test/effects_o2_twice.lang': b'62\n2\n',
}
sources = sorted(p for p in Path('test/suite').glob('*.lang')
                 if re.search(r'^\s*effect\s|\bperform\s|\bhandle\s*\{', p.read_text(), re.M))
sources += [Path(p) for p in cases]
with tempfile.TemporaryDirectory(prefix='debug-effects-') as directory:
    work = Path(directory)
    env = dict(os.environ, LANGBE='llvm', LANG_CACHE=str(work / 'cache'))
    def run(args):
        return subprocess.run(list(map(str, args)), env=env, check=True,
                              capture_output=True, timeout=120)
    for source in sources:
        expected = cases.get(str(source))
        ir = work / 'program.ll'
        run([compiler, '-g', source, '-o', ir])
        text = ir.read_text()
        definitions = re.findall(r'^define .*$', text, re.M)
        assert definitions and all(re.search(r'\) #0(?: !dbg !\d+)? \{$', d) for d in definitions)
        assert 'attributes #0 = { noinline optnone }' in text
        run(['opt', '-passes=verify', '-disable-output', ir])
        reference = None
        lto = ['-O2', '-flto'] + ([] if sys.platform == 'darwin' else ['-fuse-ld=lld'])
        for flags in (['-O0'], ['-O2'], lto):
            binary = work / 'program'
            run(['clang', *flags, ir, '-o', binary])
            result = subprocess.run([str(binary)], env=env, capture_output=True, timeout=120)
            behavior = (result.returncode, result.stdout, result.stderr)
            if reference is None:
                match = re.search(r'expect:\s*(\d+)', source.read_text().splitlines()[0])
                assert result.returncode == (int(match.group(1)) if match else 0), (source, behavior)
                if expected is not None:
                    assert result.stdout == expected, (source, behavior)
                reference = behavior
            assert behavior == reference, (source, flags, behavior, reference)
        print(f'PASS {source}: debug effects at O0, O2, and O2 LTO', flush=True)
