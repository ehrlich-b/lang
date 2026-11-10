#!/usr/bin/env python3
"""A completed upload must not report a stale or incomplete public release."""
from functools import partial
import http.server
import os
from pathlib import Path
import subprocess
import threading
import sys
import unittest
import urllib.parse

import test_verify_archive as archive_fixture

FILES = archive_fixture.FILES
ROOT = archive_fixture.ROOT
SDK = 'releases/lang-0.1.0+test-x86_64-linux.tar.xz'
INDEX = f'<a href="{SDK}">Download SDK</a>'.encode()


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def do_GET(self):
        self.server.requests.append((self.path, self.headers.get('Cache-Control')))
        if self.path in self.server.responses:
            status, body = self.server.responses[self.path]
            self.send_response(status)
            self.end_headers()
            self.wfile.write(body)
            return
        if urllib.parse.urlsplit(self.path).path in self.server.missing_assets:
            self.send_error(404)
            return
        super().do_GET()


class LiveTest(unittest.TestCase):
    def setUp(self):
        # Reuse only the archive fixture, not the other test class's test cases.
        fixture = archive_fixture.ArchiveTest()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.directory = fixture.root
        self.archive = fixture.archive(FILES, {'index.html': INDEX})
        self.site = self.directory / 'site'
        self.site.mkdir()
        for name in FILES:
            file = self.site / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(INDEX if name == 'index.html' else name.encode())
        (self.site / SDK).parent.mkdir()
        (self.site / SDK).write_bytes(b'sdk archive')
        server = http.server.ThreadingHTTPServer(
            ('127.0.0.1', 0), partial(QuietHandler, directory=str(self.site)))
        server.missing_assets = set()
        server.responses = {}
        server.requests = []
        self.server = server
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        def close():
            server.shutdown()
            server.server_close()
            thread.join()
        self.addCleanup(close)
        self.url = f'http://127.0.0.1:{server.server_port}/'

    def check(self, url=None):
        return subprocess.run(['python3', str(ROOT / 'web/verify_live.py'),
                               str(self.archive), url or self.url], capture_output=True, text=True)

    def test_exact_site_passes(self):
        self.assertEqual(self.check().returncode, 0)
        canonical = {path for path, cache in self.server.requests if not cache}
        self.assertEqual(canonical, {'/', '/' + SDK} | {'/' + name for name in FILES})
        cache_busted = {urllib.parse.urlsplit(path).path
                        for path, cache in self.server.requests if cache == 'no-cache'}
        self.assertEqual(cache_busted, {'/' + name for name in FILES})

    def test_stale_homepage_fails(self):
        (self.site / 'index.html').write_text('previous release')
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('index.html: published bytes differ', result.stderr)

    def test_missing_wasm_fails(self):
        self.server.missing_assets.add('/examples/polyglot_wasm.wasm')
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('polyglot_wasm.wasm: HTTP Error 404', result.stderr)

    def test_missing_sdk_fails(self):
        self.server.missing_assets.add('/' + SDK)
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(SDK + ': HTTP Error 404', result.stderr)

    def test_path_prefix_passes(self):
        (self.directory / 'site-with-prefix').mkdir()
        # Serve this same site below a path, as on ehrlich.dev/lang/.
        (self.site / 'lang').symlink_to(self.directory / 'site-with-prefix', target_is_directory=True)
        for name in FILES:
            dest = self.directory / 'site-with-prefix' / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(INDEX if name == 'index.html' else name.encode())
        sdk = self.directory / 'site-with-prefix' / SDK
        sdk.parent.mkdir()
        sdk.write_bytes(b'sdk archive')
        self.assertEqual(self.check(self.url + 'lang/').returncode, 0)

    def test_deploy_requires_public_bytes_to_match(self):
        # Stub transport only; execute the real verifiers against a local server.
        tools = self.directory / 'tools'
        tools.mkdir()
        transport_log = self.directory / 'transport.log'
        for command in ('ssh', 'scp'):
            stub = tools / command
            stub.write_text('#!/bin/sh\nprintf "%s\\n" "' + command +
                            '" >> "$TRANSPORT_LOG"\n')
            stub.chmod(0o755)
        python = tools / 'python3'
        python.write_text('#!/bin/sh\n'
                          'case "$1" in\n'
                          '  */verify_live.py)\n'
                          '    case "$3" in\n'
                          '      https://lang.ehrlich.dev/) url="$TEST_SITE_URL" ;;\n'
                          '      https://ehrlich.dev/lang/) url="$TEST_SITE_URL/lang/" ;;\n'
                          '      *) exit 99 ;;\n'
                          '    esac\n'
                          '    printf "%s\\n" "$3" >> "$TRANSPORT_LOG"\n'
                          '    exec "$REAL_PYTHON" "$1" "$2" "$url" ;;\n'
                          '  *) exec "$REAL_PYTHON" "$@" ;;\n'
                          'esac\n')
        python.chmod(0o755)
        for name in FILES:
            dest = self.site / 'lang' / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(INDEX if name == 'index.html' else name.encode())
        sdk = self.site / 'lang' / SDK
        sdk.parent.mkdir()
        sdk.write_bytes(b'sdk archive')
        env = dict(os.environ, PATH=f'{tools}:{os.environ["PATH"]}',
                   REAL_PYTHON=sys.executable, TEST_SITE_URL=self.url.rstrip('/'),
                   TRANSPORT_LOG=str(transport_log))
        attempts = 0
        second_site_checks = 0
        for prefix in ('', 'lang/'):
            failures = (
                ('stale', 'index.html: published bytes differ'),
                ('missing', 'polyglot_wasm.wasm: HTTP Error 404'),
                ('missing SDK', SDK + ': HTTP Error 404'),
                ('stale root', '/' + prefix + ': published bytes differ'),
                ('missing root', '/' + prefix + ': HTTP Error 404'),
                ('stale ordinary index', 'index.html: published bytes differ'),
                ('stale ordinary Wasm', 'polyglot_wasm.wasm: published bytes differ'),
                ('missing ordinary Wasm', 'polyglot_wasm.wasm: HTTP Error 404'),
            )
            for failure, expected in failures:
                with self.subTest(prefix=prefix, failure=failure):
                    index = self.site / prefix / 'index.html'
                    if failure == 'stale':
                        index.write_text('previous release')
                    elif failure == 'missing':
                        self.server.missing_assets.add('/' + prefix + 'examples/polyglot_wasm.wasm')
                    elif failure == 'missing SDK':
                        self.server.missing_assets.add('/' + prefix + SDK)
                    else:
                        path = '/' + prefix
                        if 'index' in failure:
                            path += 'index.html'
                        elif 'Wasm' in failure:
                            path += 'examples/polyglot_wasm.wasm'
                        status = 404 if failure.startswith('missing') else 200
                        # Exact URL overrides leave every cache-busted URL correct.
                        self.server.responses[path] = (status, b'previous release')
                    result = subprocess.run(['bash', str(ROOT / 'web/deploy.sh'), 'ship',
                                             str(self.archive)], env=env, capture_output=True, text=True)
                    attempts += 1
                    second_site_checks += int(bool(prefix))
                    index.write_bytes(INDEX)
                    self.server.missing_assets.clear()
                    self.server.responses.clear()
                    self.assertNotEqual(result.returncode, 0)
                    self.assertNotIn('Deployed:', result.stdout)
                    self.assertIn(expected, result.stderr)
                    self.assertEqual(result.stdout.count('PASS: all'), int(bool(prefix)))
                    print(f'PASS deploy rejects {failure} asset at /{prefix}: '
                          f'exit {result.returncode}, no Deployed, {expected}')
        result = subprocess.run(['bash', str(ROOT / 'web/deploy.sh'), 'ship',
                                 str(self.archive)], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count('PASS: all'), 2)
        self.assertIn('Deployed:', result.stdout)
        calls = transport_log.read_text().splitlines()
        self.assertEqual(calls.count('ssh'), 2 * (attempts + 1))
        self.assertEqual(calls.count('scp'), len(FILES) * (attempts + 1))
        self.assertEqual(calls.count('https://lang.ehrlich.dev/'), attempts + 1)
        self.assertEqual(calls.count('https://ehrlich.dev/lang/'), second_site_checks + 1)
        print('PASS deploy reports Deployed only after both local public copies match; '
              'all ssh/scp calls used stand-ins')


if __name__ == '__main__':
    unittest.main()
