#!/usr/bin/env python3
"""Bounded integration probes for development-build invalidation."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DevelopmentBuild(unittest.TestCase):
    def test_content_identity(self):
        with tempfile.TemporaryDirectory(prefix='dev-build-') as directory:
            root = Path(directory)
            for name in ['scripts', 'std', 'src', 'bootstrap/current', 'out']:
                (root / name).mkdir(parents=True, exist_ok=True)
            for name in ['Makefile', 'scripts/dev_build.py', 'scripts/write_if_changed.py',
                         'scripts/build_receipt.py', 'scripts/build_inputs.py']:
                shutil.copyfile(ROOT / name, root / name)
            sources = ['lexer', 'parser', 'codegen', 'codegen_llvm', 'codegen_wasm',
                       'ast_emit', 'sexpr_reader', 'compiler_readers_none', 'main']
            for name in sources:
                (root / f'src/{name}.lang').write_text('// fixture\n')
            (root / 'src/receipt_only.lang').write_text('// receipt input\n')
            (root / 'std/core.lang').write_text('include "std/os.lang"\nrequire "std/middle"\n')
            (root / 'std/middle.lang').write_text('include /* comment between tokens */ "std/leaf.lang"\n// include "not-a-dependency.lang"\n')
            (root / 'std/leaf.lang').write_text('// leaf\n')
            (root / 'std/os').mkdir()
            (root / 'std/os/libc.lang').write_text('// libc\n')
            (root / 'std/os/alternate.lang').write_text('// alternate OS\n')
            (root / 'bootstrap/current/COMMIT').write_text('fixture-root\n')
            (root / 'bootstrap/current/compiler_linux.ll').write_text('; fixture\n')
            (root / 'out/lang').write_text('''#!/usr/bin/env python3
import pathlib,sys
if sys.argv[1:] == ['version']: print('fixture compiler')
else: pathlib.Path(sys.argv[sys.argv.index('-o')+1]).write_text('; compiled fixture\\n')
''')
            cc = root / 'cc'
            cc.write_text('''#!/usr/bin/env python3
import pathlib,sys
if '--version' in sys.argv: print('fixture cc v1')
elif '--fail' in sys.argv: sys.exit(9)
else:
 p=pathlib.Path(sys.argv[sys.argv.index('-o')+1]); p.write_text('#!/bin/sh\\necho fixture compiler\\n'); p.chmod(0o755)
''')
            cc.chmod(0o755)
            (root / 'out/lang').chmod(0o755)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            subprocess.run(['git', 'add', '.'], cwd=root, check=True)
            subprocess.run(['git', '-c', 'user.name=Build Test', '-c',
                            'user.email=build@example.com', 'commit', '-qm',
                            'Create build fixture.'], cwd=root, check=True)

            def make(*options, rebuilt=False, fail=False):
                result = subprocess.run(['make', '--no-print-directory', '-j2', 'build',
                                         'VERSION=fixture', f'DEV_CC={cc}', *options],
                                        cwd=root, text=True, capture_output=True)
                if fail:
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    return
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stdout.count('Created: out/lang_next'), int(rebuilt),
                                 result.stdout)
                return result

            def once(label, *options):
                make(*options, rebuilt=True)
                times = {p: (root/p).stat().st_mtime_ns for p in
                         ['std/os.lang', 'out/version_info.lang', 'out/dev-build.json']}
                make(*options)
                self.assertEqual(times, {p: (root/p).stat().st_mtime_ns for p in times})
                print(label + ': rebuilt exactly once, then no-op', flush=True)

            once('initial')
            (root / 'src/receipt_only.lang').write_text('// changed receipt input\n')
            once('receipt-only source change')
            subprocess.run(['git', 'add', 'src/receipt_only.lang'], cwd=root, check=True)
            subprocess.run(['git', '-c', 'user.name=Build Test', '-c',
                            'user.email=build@example.com', 'commit', '-qm',
                            'Record new fixture revision.'], cwd=root, check=True)
            once('full revision change with fixed version option')
            make()
            os.utime(root / 'src/lexer.lang', None)
            make()
            print('mtime-only touch: no rebuild', flush=True)
            source = root / 'src/lexer.lang'
            original = source.read_bytes(); stamp = source.stat()
            source.write_bytes(original + b'// changed\n')
            os.utime(source, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
            once('compiler source with preserved mtime')
            source.write_bytes(original)
            once('source revert')
            leaf = root / 'std/leaf.lang'; leaf.write_text('// changed leaf\n')
            once('transitive require/include')
            (root / 'std/new_leaf.lang').write_text('// new untracked leaf\n')
            (root / 'std/middle.lang').write_text('include "std/new_leaf.lang"\n')
            once('include graph change')
            (root / 'std/new_leaf.lang').write_text('// changed untracked leaf\n')
            once('untracked transitive include')
            extra = root / 'out/extra source.lang'
            extra.write_text('include "out/extra-leaf.lang"\n')
            extra_leaf = root / 'out/extra-leaf.lang'
            extra_leaf.write_text('// extra leaf\n')
            flags = 'DEV_LANGFLAGS="out/extra source.lang"'
            once('additional source from flags', flags)
            stamp = extra.stat()
            extra.write_text(extra.read_text() + '// changed extra source\n')
            os.utime(extra, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
            once('flag source with preserved mtime', flags)
            extra_leaf.write_text('// changed extra leaf\n')
            once('transitive include from flag source', flags)
            # Reader names and output paths must not be treated as input files.
            once('reader file operand', 'DEV_LANGFLAGS=-r reader out/extra-leaf.lang')
            extra_leaf.write_text('// changed reader source\n')
            once('reader file edit', 'DEV_LANGFLAGS=-r reader out/extra-leaf.lang')
            once('non-file option operands', 'DEV_LANGFLAGS=-c reader -o out/unused.ll')
            seed = root / 'out/lang'; seed.write_text(seed.read_text() + '\n# seed changed\n')
            once('seed content')
            twin = root / 'out/other-seed'; shutil.copy2(seed, twin)
            twin.write_text(twin.read_text() + '# different bytes at another path\n')
            os.utime(twin, ns=(seed.stat().st_atime_ns, seed.stat().st_mtime_ns))
            once('cross-path seed with equal mtime', 'LANG=out/other-seed')
            once('flags', 'DEV_CFLAGS=-O0')
            cc.write_text(cc.read_text() + '\n# toolchain changed\n')
            once('toolchain content', 'DEV_CFLAGS=-O0')
            once('generated version', 'VERSION=changed')
            once('generated architecture', 'BUILD_ARCH=arm64')
            once('generated OS selection', 'OS_LAYER=std/os/alternate.lang')
            make('DEV_CFLAGS=--fail', fail=True)
            once('recovery after failed toolchain')
            # A corrupt artifact cannot be reused even with unchanged inputs.
            output = (root / 'out/lang_next').resolve()
            output.write_text(output.read_text() + '# corrupt\n')
            once('artifact corruption')
            print('All invalidation probes passed.', flush=True)


if __name__ == '__main__':
    unittest.main()
