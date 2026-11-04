#!/usr/bin/env python3
"""Bounded native-cache fragment using tiny real LLVM input and clang."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NativeSeedCache(unittest.TestCase):
    def test_cache_contract(self):
        # Keep all generated fixtures outside the checkout when requested.
        with tempfile.TemporaryDirectory(dir=os.environ.get('LANG_TEST_TMPDIR')) as temp:
            base = Path(temp)
            cache = base / 'cache'
            env = dict(os.environ, LANG_NATIVE_CACHE=str(cache))
            checkouts = []
            for name in ('first', 'second'):
                checkout = base / name
                subprocess.run(['git', 'clone', '--shared', '--quiet', str(ROOT), str(checkout)], check=True)
                (checkout / 'seed.ll').write_text('define i32 @main() { ret i32 7 }\n')
                checkouts.append(checkout)
            tool = shutil.which('clang')
            print(json.dumps(dict(tool_sha256=hashlib.sha256(Path(tool).resolve().read_bytes()).hexdigest(),
                                  seed_sha256=hashlib.sha256((checkouts[0] / 'seed.ll').read_bytes()).hexdigest())))

            def run(checkout, *extra, success=True):
                argv = ['make', 'init', 'BOOTSTRAP_LL=seed.ll', *extra]
                result = subprocess.run(argv, cwd=checkout, env=env, capture_output=True, text=True)
                print(json.dumps(dict(argv=argv, cwd=checkout.name, exit=result.returncode,
                                      stdout=result.stdout, stderr=result.stderr)))
                self.assertEqual(result.returncode == 0, success)
                return result.stdout

            first, second = checkouts
            self.assertIn('miss:', run(first))
            self.assertIn('hit:', run(second))
            self.assertEqual(os.readlink(second / 'out/lang'), 'lang_bootstrap')
            self.assertEqual(subprocess.run([second / 'out/lang']).returncode, 7)
            self.assertEqual(hashlib.sha256((first / 'out/lang_bootstrap').read_bytes()).digest(),
                             hashlib.sha256((second / 'out/lang_bootstrap').read_bytes()).digest())
            (second / 'out/lang_bootstrap').write_bytes(b'local edit')
            self.assertIn('hit:', run(second))
            jobs = [subprocess.Popen(['make', 'init', 'BOOTSTRAP_LL=seed.ll', 'INIT_ABI=concurrent'],
                    cwd=path, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    for path in checkouts]
            concurrent = [job.communicate() for job in jobs]
            self.assertTrue(all(job.returncode == 0 for job in jobs))
            self.assertEqual(sum('miss:' in out for out, err in concurrent), 1)
            self.assertEqual(sum('hit:' in out for out, err in concurrent), 1)
            print('PASS: concurrent publication and isolation from local output edits')
            (second / 'seed.ll').write_text('define i32 @main() { ret i32 8 }\n')
            self.assertIn('miss:', run(second))
            target = subprocess.check_output([tool, '-dumpmachine'], text=True).strip()
            alternate = 'x86_64-unknown-linux-gnu' if 'linux' in target else 'arm64-apple-macosx'
            self.assertNotEqual(target, alternate)
            self.assertIn('miss:', run(first, 'INIT_TARGET=' + alternate))
            wrapper = base / 'clang-proxy'
            wrapper.write_text('#!/bin/sh\nexec "' + tool + '" "$@"\n')
            wrapper.chmod(0o755)
            self.assertIn('miss:', run(first, 'CLANG=' + str(wrapper)))
            wrapper.write_text(wrapper.read_text() + '# changed tool bytes\n')
            self.assertIn('miss:', run(first, 'CLANG=' + str(wrapper)))
            version_tool = base / 'clang-version-proxy'
            version_tool.write_text('#!/bin/sh\nif [ "$1" = --version ]; then echo "$CLANG_TEST_VERSION"; fi\nexec "' + tool + '" "$@"\n')
            version_tool.chmod(0o755)
            env['CLANG_TEST_VERSION'] = 'one'
            self.assertIn('miss:', run(first, 'CLANG=' + str(version_tool)))
            env['CLANG_TEST_VERSION'] = 'two'
            self.assertIn('miss:', run(first, 'CLANG=' + str(version_tool)))
            self.assertIn('miss:', run(first, 'INIT_ABI=other'))
            self.assertIn('miss:', run(first, 'INIT_FLAGS=-O0'))
            before = (first / 'out/lang_bootstrap').read_bytes()
            # Corrupt the original entry deliberately, without removing or relocating it.
            identity = next(p for p in cache.iterdir() if p.is_dir() and
                            json.loads((p / 'receipt.json').read_text())['identity']['abi'] == 'native-v1'
                            and json.loads((p / 'receipt.json').read_text())['identity']['flags'] == ['-O2']
                            and json.loads((p / 'receipt.json').read_text())['identity']['target'] == target
                            and json.loads((p / 'receipt.json').read_text())['identity']['tool'] ==
                            hashlib.sha256(Path(tool).resolve().read_bytes()).hexdigest()
                            and json.loads((p / 'receipt.json').read_text())['identity']['seed'] ==
                            hashlib.sha256((first / 'seed.ll').read_bytes()).hexdigest())
            artifact = identity / 'compiler'
            artifact.chmod(0o755)
            artifact.write_bytes(b'corrupt')
            run(first, success=False)
            self.assertEqual((first / 'out/lang_bootstrap').read_bytes(), before)
            self.assertEqual(artifact.read_bytes(), b'corrupt')
            artifact.write_bytes(b'')
            run(first, success=False)
            self.assertEqual((first / 'out/lang_bootstrap').read_bytes(), before)
            print('PASS: two paths, native execution, seed, target, tool bytes, ABI, flags, corruption fail-closed')
            # Preserve failure behavior too: invalid input cannot publish a new entry.
            count = len(list(cache.iterdir()))
            (first / 'seed.ll').write_text('invalid llvm')
            run(first, success=False)
            self.assertEqual(len([p for p in cache.iterdir() if p.is_dir()]), (count // 2))
            self.assertEqual((first / 'out/lang_bootstrap').read_bytes(), before)
            # Temporary entries have normal cleanup; restore only test-injected permissions.
            for entry in cache.iterdir():
                if entry.is_dir():
                    entry.chmod(0o755)


if __name__ == '__main__':
    unittest.main()
