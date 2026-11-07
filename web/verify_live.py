#!/usr/bin/env python3
"""Compare every published asset with a verified site's MANIFEST."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive')
    parser.add_argument('url', help='Public site base URL, including any path prefix')
    args = parser.parse_args()
    base = urllib.parse.urlsplit(args.url)
    if base.scheme not in ('http', 'https') or not base.netloc or base.query or base.fragment:
        parser.error('supply an http(s) base URL without a query or fragment')
    failures = []
    # Reuse the strict inventory/path/hash validator before making any requests.
    with tempfile.TemporaryDirectory() as temporary:
        subprocess.run([sys.executable, str(Path(__file__).with_name('verify_archive.py')),
                        args.archive, temporary], check=True)
        files = (Path(temporary) / '.files').read_text().splitlines()
        base_url = args.url.rstrip('/') + '/'
        # The directory homepage and ordinary asset URLs are what visitors use.
        # Cache-busted requests alone can hide stale or missing public responses.
        targets = [('', 'index.html')] + [(name, name) for name in files]
        for path, name in targets:
            expected = hashlib.sha256((Path(temporary) / name).read_bytes()).hexdigest()
            label = path or urllib.parse.urlsplit(base_url).path
            urls = [(base_url + path, label, False)]
            if path:
                urls.append((base_url + path + '?site-check=' + expected,
                             label + ' (cache-busted)', True))
            for url, label, cache_busted in urls:
                headers = {'User-Agent': 'lang-site-verifier/1.0',
                           'Accept-Encoding': 'identity'}
                if cache_busted:
                    headers['Cache-Control'] = 'no-cache'
                request = urllib.request.Request(url, headers=headers)
                try:
                    with urllib.request.urlopen(request, timeout=15) as response:
                        actual = hashlib.sha256(response.read()).hexdigest()
                    if actual != expected:
                        failures.append(label + ': published bytes differ from the release')
                except (OSError, urllib.error.URLError) as error:
                    failures.append(label + ': ' + str(error))
    if failures:
        print('Live site verification FAILED:\n' + '\n'.join(failures), file=sys.stderr)
        return 1
    print(f'PASS: all {len(files)} live assets match the release at {args.url}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
