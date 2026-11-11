#!/usr/bin/env python3
"""Compare every published asset with a verified site's MANIFEST."""
import argparse
import hashlib
from html.parser import HTMLParser
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request


class DownloadLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.extend(value for key, value in attrs
                              if key == 'href' and value and value.startswith('releases/'))


class BeaconScripts(HTMLParser):
    """Locate empty Cloudflare beacon scripts without rewriting other HTML."""

    def __init__(self, data):
        super().__init__(convert_charrefs=False)
        # Latin-1 keeps character offsets identical to byte offsets, including
        # non-ASCII bytes. No decoding or serialization changes the comparison.
        self.source = data.decode('latin-1')
        self.lines = [0] + [m.end() for m in re.finditer('\n', self.source)]
        self.pending = None
        self.spans = []
        self.feed(self.source)
        self.close()

    def byte_offset(self):
        line, column = self.getpos()
        return self.lines[line - 1] + column

    def handle_starttag(self, tag, attrs):
        if tag in ('textarea', 'title', 'xmp', 'iframe', 'noembed', 'noframes', 'plaintext'):
            self.set_cdata_mode(tag)
        if tag != 'script':
            return
        self.pending = None
        names = [key for key, _ in attrs]
        attributes = dict(attrs)
        if (len(names) == len(set(names))
                and set(names) <= {'src', 'defer', 'async', 'type', 'integrity',
                                   'data-cf-beacon', 'crossorigin'}
                and re.fullmatch(r'https://static\.cloudflareinsights\.com/'
                                 r'beacon\.min\.js(?:/v[0-9a-f]+)?',
                                 attributes.get('src') or '')):
            start = self.byte_offset()
            self.pending = (start, start + len(self.get_starttag_text()))

    def handle_startendtag(self, tag, attrs):
        # A script needs a closing tag in HTML; do not ignore malformed tags.
        pass

    def handle_endtag(self, tag):
        if tag == 'script' and self.pending is not None:
            start, content = self.pending
            end = self.byte_offset()
            if content == end:
                self.spans.append((start, self.source.index('>', end) + 1))
            self.pending = None


def published_matches(name, expected, actual):
    if actual == expected:
        return True
    if not name.endswith('.html'):
        return False
    spans = BeaconScripts(actual).spans
    if len(spans) != 1:
        return False
    start, end = spans[0]
    # Cloudflare can put its tag on a new line even between adjacent closing
    # tags. Permit the tag's trailing line ending, plus a leading line ending
    # only when it separates otherwise adjacent content. Never collapse blank
    # lines or rewrite any other whitespace.
    if actual[:start] + actual[end:] == expected:
        return True
    for ending in (b'\r\n', b'\n'):
        if actual[end:].startswith(ending):
            suffix = actual[end + len(ending):]
            if actual[:start] + suffix == expected:
                return True
            if actual[:start].endswith(ending):
                prefix = actual[:start - len(ending)]
                if (not prefix.endswith((b'\r', b'\n'))
                        and not suffix.startswith((b'\r', b'\n'))
                        and prefix + suffix == expected):
                    return True
    return False


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
        links = DownloadLinks()
        links.feed((Path(temporary) / 'index.html').read_text(encoding='utf-8'))
        if len(links.links) != 1 or not re.fullmatch(
                r'releases/lang-[A-Za-z0-9_.+\-]+-x86_64-linux\.tar\.xz',
                links.links[0]):
            failures.append('index.html: expected one versioned Linux SDK link')
        else:
            url = base_url + links.links[0]
            try:
                request = urllib.request.Request(url, headers={
                    'User-Agent': 'lang-site-verifier/1.0', 'Accept-Encoding': 'identity'})
                with urllib.request.urlopen(request, timeout=15) as response:
                    while response.read(1024 * 1024):
                        pass
            except (OSError, urllib.error.URLError) as error:
                failures.append(links.links[0] + ': ' + str(error))
        # The directory homepage and ordinary asset URLs are what visitors use.
        # Cache-busted requests alone can hide stale or missing public responses.
        targets = [('', 'index.html')] + [(name, name) for name in files]
        for path, name in targets:
            expected_bytes = (Path(temporary) / name).read_bytes()
            expected = hashlib.sha256(expected_bytes).hexdigest()
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
                        actual = response.read()
                    if not published_matches(name, expected_bytes, actual):
                        failures.append(label + ': published bytes differ from the release')
                except (OSError, urllib.error.URLError) as error:
                    failures.append(label + ': ' + str(error))
    if failures:
        print('Live site verification FAILED:\n' + '\n'.join(failures), file=sys.stderr)
        return 1
    print(f'PASS: all {len(files)} live assets match and the SDK download is reachable at {args.url}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
