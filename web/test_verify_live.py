import contextlib
import hashlib
import io
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import urllib.parse

import verify_live


BEACON = (
    b'<script defer src="https://static.cloudflareinsights.com/beacon.min.js/'
    b'vce701823e78c4301a35b7e07294d87301792088814092" '
    b'integrity="sha512-test" data-cf-beacon=\'{"token":"test"}\' '
    b'crossorigin="anonymous"></script>'
)
PAGE = (b'<!doctype html>\n<html><body>caf\xc3\xa9\n'
        b'<a href="releases/lang-test-x86_64-linux.tar.xz">SDK</a>\n'
        b'</body></html>\n')


class PublishedMatchesTests(unittest.TestCase):
    def test_unchanged_bytes_pass(self):
        for name, data in [('index.html', PAGE), ('compiler.wasm', b'\0asm\xff')]:
            with self.subTest(name=name):
                self.assertTrue(verify_live.published_matches(name, data, data))

    def test_one_beacon_passes_for_each_html_page(self):
        for name in ('index.html', 'lab.html', 'readers.html'):
            for tag in (BEACON, BEACON.replace(b'defer', b'type="module"'),
                        b"<SCRIPT src='https://static.cloudflareinsights.com/"
                        b"beacon.min.js'></SCRIPT>"):
                for extra in (tag, tag + b'\n', tag + b'\r\n'):
                    with self.subTest(name=name, extra=extra):
                        actual = PAGE.replace(b'</body>', extra + b'</body>')
                        self.assertTrue(verify_live.published_matches(name, PAGE, actual))

    def test_two_beacons_fail(self):
        for extra in (BEACON * 2, (BEACON + b'\n') * 2):
            self.assertFalse(verify_live.published_matches(
                'index.html', PAGE, PAGE.replace(b'</body>', extra + b'</body>')))

    def test_beacon_between_adjacent_closing_tags(self):
        for ending in (b'\n', b'\r\n'):
            expected = b'<html><body><main>release</main></body></html>' + ending
            actual = expected.replace(b'</body>', ending + BEACON + ending + b'</body>')
            self.assertTrue(verify_live.published_matches('readers.html', expected, actual))
            self.assertFalse(verify_live.published_matches(
                'readers.html', expected, actual.replace(b'<main>', b'<main> ')))

    def test_any_other_page_change_fails(self):
        injected = PAGE.replace(b'</body>', BEACON + b'\n</body>')
        for actual in (injected.replace(b'SDK', b'changed'), injected + b' ',
                       injected.replace(b'caf\xc3\xa9', b'cafe'),
                       injected.replace(b'<a ', b'<a  '),
                       injected.replace(BEACON, BEACON + b'\n')):
            with self.subTest(actual=actual):
                self.assertFalse(verify_live.published_matches('index.html', PAGE, actual))

    def test_other_scripts_and_lookalike_urls_fail(self):
        for src in (b'https://example.com/beacon.min.js',
                    b'https://static.cloudflareinsights.com.evil/beacon.min.js',
                    b'https://static.cloudflareinsights.com@evil/beacon.min.js',
                    b'https://static.cloudflareinsights.com/other.js',
                    b'http://static.cloudflareinsights.com/beacon.min.js'):
            tag = b'<script src="' + src + b'"></script>'
            with self.subTest(src=src):
                self.assertFalse(verify_live.published_matches('index.html', PAGE, PAGE + tag))

    def test_nonempty_or_malformed_beacon_fails(self):
        for tag in (BEACON.replace(b'></script>', b'>alert(1)</script>'),
                    BEACON.replace(b'</script>', b''),
                    BEACON.replace(b'></script>', b'/>'),
                    BEACON.replace(b'defer', b'onload="alert(1)"'),
                    BEACON.replace(b'defer', b'src="https://example.com/evil.js"')):
            with self.subTest(tag=tag):
                self.assertFalse(verify_live.published_matches('index.html', PAGE, PAGE + tag))

    def test_script_text_and_comments_are_not_tags(self):
        for wrapper in (b'<!--%s-->', b'<script>const text = `%s`;</script>',
                        b'<textarea>%s</textarea>', b'<title>%s</title>'):
            expected = PAGE + wrapper % b''
            self.assertFalse(verify_live.published_matches(
                'index.html', expected, PAGE + wrapper % BEACON))

    def test_non_html_assets_remain_exact(self):
        for name in ('host.js', 'compiler.wasm', 'receipt.json', 'examples/fib.lang'):
            with self.subTest(name=name):
                self.assertFalse(verify_live.published_matches(name, PAGE, PAGE + BEACON))


class LiveVerifierTests(unittest.TestCase):
    def test_archive_and_all_response_paths(self):
        # A complete, tiny archive exercises the real inventory/hash validator
        # and CLI, including the homepage, ordinary and cache-busted URLs.
        names = '''build_stdlib.js compiler-receipt.json compiler.wasm
            compiler_host.js editor.js examples/fib.lang examples/fib.wasm
            examples/mandelbrot.lang examples/mandelbrot.wasm
            examples/polyglot_wasm.lang examples/polyglot_wasm.wasm host.js
            index.html lab.html program_host.js readers.html receipt.json stdlib.json'''.split()
        files = {name: PAGE if name.endswith('.html') else b'asset: ' + name.encode()
                 for name in names}
        manifest = ''.join(hashlib.sha256(data).hexdigest() + '  ' + name + '\n'
                           for name, data in files.items()).encode()
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / 'site.tar.gz'
            with tarfile.open(archive, 'w:gz') as tar:
                for name, data in dict(files, MANIFEST=manifest).items():
                    info = tarfile.TarInfo(name)
                    info.size = len(data)
                    tar.addfile(info, io.BytesIO(data))
            for mode in ('unchanged', 'one', 'two', 'changed', 'binary', 'ordinary', 'cache-busted'):
                requests = []

                def fetch(request, timeout):
                    requests.append(request)
                    url = urllib.parse.urlsplit(request.full_url)
                    path = url.path.removeprefix('/prefix/') or 'index.html'
                    if path.startswith('releases/'):
                        return io.BytesIO(b'SDK archive')
                    data = files[path]
                    if path.endswith('.html') and mode != 'unchanged':
                        count = 2 if mode == 'two' else 1
                        data = data.replace(b'</body>', (BEACON + b'\n') * count + b'</body>')
                    if mode == 'changed' and path.endswith('.html'):
                        data += b'changed'
                    if mode == 'binary' and path == 'compiler.wasm':
                        data += BEACON
                    if path == 'index.html' and ((mode == 'ordinary' and not url.query)
                                                or (mode == 'cache-busted' and url.query)):
                        data += b'changed'
                    return io.BytesIO(data)

                output = io.StringIO()
                with self.subTest(mode=mode), patch.object(sys, 'argv', [
                        'verify_live.py', str(archive), 'https://example.test/prefix/']), \
                        patch.object(verify_live.urllib.request, 'urlopen', side_effect=fetch), \
                        contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                    self.assertEqual(verify_live.main(), 0 if mode in ('unchanged', 'one') else 1,
                                     output.getvalue())
                    self.assertEqual(len(requests), 2 + 2 * len(names))
                    self.assertTrue(all(r.get_method() == 'GET' for r in requests))
                    self.assertTrue(any(r.get_header('Cache-control') == 'no-cache' for r in requests))


if __name__ == '__main__':
    unittest.main()
