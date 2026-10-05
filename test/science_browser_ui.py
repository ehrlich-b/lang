#!/usr/bin/env python3
"""Actual Chromium science journeys; local serving is stopped even on failure.

python3 test/science_browser_ui.py [--url https://lang.ehrlich.dev/science.html]
Uses the already installed Playwright/Chromium; no browser download occurs.
"""
import argparse
import csv
import io
import json
import math
import re
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import threading
import time

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url')
    parser.add_argument('--output', default='out/science-browser-ui')
    parser.add_argument('--browser', default='/Users/ehrlich/Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    output = Path(args.output).resolve(); output.mkdir(parents=True, exist_ok=True)
    server = None
    if not args.url:
        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *values, **kwargs):
                super().__init__(*values, directory=str(root / 'web'), **kwargs)
            def log_message(self, *values):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        args.url = f'http://127.0.0.1:{server.server_port}/science.html'
    receipts = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, executable_path=args.browser)
            page = browser.new_page(viewport={'width': 1360, 'height': 1000})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(args.url)
            page.wait_for_function("!document.getElementById('run').disabled")
            source = page.locator('#model')
            default = source.input_value()
            assert 'b*x^2*y^2/2' in default

            def run(name):
                start = time.perf_counter()
                page.locator('#run').click()
                page.wait_for_function("document.getElementById('status').textContent.startsWith('Experiment complete')", timeout=90000)
                assert page.locator('#csv-download').is_visible()
                generated = page.locator('#forces').text_content()
                assert re.search(r'\(func\s+ham_force_x\b', generated), generated[:200]
                assert re.search(r'\(func\s+ham_step\b', generated), generated[:200]
                receipts.append({'journey': name, 'wall_ms': round((time.perf_counter() - start) * 1000),
                                 'status': page.locator('#status').inner_text(),
                                 'stats': page.locator('#stats').inner_text()})

            run('default quartic model → reader → AST → Wasm trajectory')
            page.get_by_text('Inspect generated forces and solver', exact=True).click()
            assert 'ham_force_x' in page.locator('#forces').inner_text()
            exports = {}
            for kind in ['csv', 'json', 'ast', 'wasm']:
                with page.expect_download() as event:
                    page.locator(f'#{kind}-download').click()
                download = event.value
                target = output / download.suggested_filename
                download.save_as(target); exports[kind] = target
            rows = list(csv.DictReader(io.StringIO(exports['csv'].read_text())))
            assert len(rows) == 369 and rows[-1]['time'] == '3.6800000000000002'
            data = json.loads(exports['json'].read_text())
            assert data['schema'] == 'lang.hamiltonian.trajectory.v1' and data['nondimensional'] is True
            assert data['method'] == 'velocity-verlet' and data['coordinates'] == ['x', 'y']
            assert data['masses'] == [1.3, 1.3] and data['steps'] == 368 and data['sample_stride'] == 1
            assert len(data['samples']) == len(rows)
            for sample, row in zip(data['samples'], rows):
                assert sample['step'] == int(row['step']) and sample['time'] == float(row['time'])
                assert sample['q'] == [float(row['q_x']), float(row['q_y'])]
                assert sample['p'] == [float(row['p_x']), float(row['p_y'])]
                assert sample['energy'] == float(row['energy'])
            assert exports['wasm'].read_bytes()[:4] == b'\0asm'
            assert re.search(r'\(func\s+ham_force_x\b', exports['ast'].read_text())
            receipts.append({'journey': 'CSV/JSON/AST/Wasm downloads', 'samples': len(rows),
                             'wasm_bytes': exports['wasm'].stat().st_size})

            page.locator('#force-probe').click()
            page.wait_for_function("document.getElementById('status').textContent.startsWith('Inspection complete')")
            probe = list(csv.DictReader(io.StringIO(page.locator('#probe-output').inner_text())))[0]
            assert abs(float(probe['force_x']) + .8106) < 5e-13
            assert abs(float(probe['force_y']) - .4368) < 5e-13
            page.locator('#reverse').click()
            page.wait_for_function("document.getElementById('probe-output').textContent.startsWith('Maximum full-state')")
            reversal = page.locator('#probe-output').inner_text()
            assert float(reversal.splitlines()[0].split(': ')[1]) < 5e-10
            receipts.append({'journey': 'generated force inspection and correct two-flip reversal', 'reversal': reversal})

            # Flush an edit by switching before the autosave debounce expires.
            edited = default.replace('param b = 0.4;', 'param b = 0.9;')
            source.fill(edited)
            page.locator('#preset').select_option('harmonic')
            page.locator('#preset').select_option('quartic')
            assert source.input_value() == edited
            page.reload(); page.wait_for_function("!document.getElementById('run').disabled")
            assert source.input_value() == edited
            run('changed coupling, saved and reopened')
            with page.expect_download() as event:
                page.locator('#csv-download').click()
            changed_csv = output / 'changed-coupling.csv'; event.value.save_as(changed_csv)
            assert changed_csv.read_text() != exports['csv'].read_text()

            # Empty source is a real saved draft, not a signal to reset a preset.
            source.fill('')
            page.locator('#preset').select_option('double_well')
            page.locator('#preset').select_option('quartic')
            assert source.input_value() == ''
            page.reload(); page.wait_for_function("!document.getElementById('run').disabled")
            assert source.input_value() == ''
            receipts.append({'journey': 'empty draft persists across quick switch and reload'})

            # Save/open operates on local files; models do not leave this browser.
            source.fill(edited)
            with page.expect_download() as event:
                page.locator('#save-model').click()
            saved = output / 'saved-model.ham'; event.value.save_as(saved)
            assert saved.read_text() == edited
            page.locator('#model-file').set_input_files({
                'name': 'independent-model.ham', 'mimeType': 'text/plain',
                'buffer': default.replace('param b = 0.4;', 'param b = 0.2;').encode()})
            page.wait_for_function("document.getElementById('model').value.includes('param b = 0.2;')")
            assert 'param b = 0.2;' in source.input_value()
            run('open changed model file and recompile')

            invalid = '// café λ\n' + default.replace('k*(x^2+y^2)', 'missing*(x^2+y^2)')
            source.fill(invalid); page.locator('#run').click()
            page.wait_for_function("document.getElementById('status').textContent.endsWith(' failed')")
            assert 'unknown symbol' in page.locator('#diagnostic').inner_text()
            selected = source.evaluate("el => ({active:document.activeElement===el, text:el.value.slice(el.selectionStart,el.selectionEnd)})")
            assert selected == {'active': True, 'text': 'missing'}, selected
            assert not page.locator('#csv-download').is_visible()
            receipts.append({'journey': 'located Unicode-source rejection, focus and invalidated exports', 'selection': selected})

            source.fill(f'model overflow {{ nondimensional; pair x mass 1 position {"9" * 128} momentum 0; potential = x^8; run step 0.01 steps 1 sample 1; }}')
            page.locator('#run').click()
            page.wait_for_function("document.getElementById('status').textContent === 'run solver failed'")
            assert 'nonfinite' in page.locator('#diagnostic').inner_text()
            assert not page.locator('#csv-download').is_visible()
            receipts.append({'journey': 'runtime nonfinite trajectory rejected, incomplete output not exported'})

            source.fill(default)
            # Stop atomically before a worker response; Run must stay gated until
            # the fresh worker's ready event, preserving the stopped source.
            disabled = page.evaluate("""() => {
              document.getElementById('run').click();
              document.getElementById('stop').click();
              return document.getElementById('run').disabled;
            }""")
            assert disabled
            page.wait_for_function("!document.getElementById('run').disabled")
            assert source.input_value() == default
            run('stop → worker restart → preserved model → successful run')

            # A large constant coordinate requires a scale-relative plot range.
            page.evaluate("""() => {
              window.invalidPlotCoordinates = [];
              const original = CanvasRenderingContext2D.prototype.lineTo;
              CanvasRenderingContext2D.prototype.lineTo = function(x,y) {
                if (!Number.isFinite(x) || !Number.isFinite(y)) window.invalidPlotCoordinates.push([x,y]);
                return original.call(this,x,y);
              };
            }""")
            source.fill('model free { nondimensional; pair x mass 1 position 100000000000000000 momentum 0; potential = 0; run step 0.01 steps 10 sample 1; }')
            run('large constant one-coordinate model plots finite ranges')
            assert page.locator('#plot-mode option[value="phase"]').is_disabled()
            assert page.evaluate('window.invalidPlotCoordinates') == []

            source.fill('model zero { nondimensional; pair z mass 1 position -0.0 momentum -0.0; potential = 0; run step 0.01 steps 2 sample 2; }')
            run('native-schema JSON preserves signed zero')
            with page.expect_download() as event:
                page.locator('#json-download').click()
            target = output / 'signed-zero.json'; event.value.save_as(target)
            zero = json.loads(target.read_text())
            assert [s['step'] for s in zero['samples']] == [0, 2]
            assert math.copysign(1, zero['samples'][0]['q'][0]) == -1
            assert math.copysign(1, zero['samples'][0]['p'][0]) == -1

            page.locator('#preset').select_option('harmonic'); run('harmonic browser preset')
            page.locator('#preset').select_option('double_well'); run('double-well browser preset')
            for mode in ['momenta', 'phase', 'energy', 'coordinates']:
                page.locator('#plot-mode').select_option(mode)
                assert 'emitted samples' in page.locator('#plot').get_attribute('aria-label')
            page.screenshot(path=str(output / 'science-desktop.png'), full_page=True)
            page.set_viewport_size({'width': 390, 'height': 844})
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
            page.screenshot(path=str(output / 'science-mobile.png'), full_page=True)
            assert not errors, errors
            receipts.append({'journey': 'all plot modes, desktop/mobile layout, no uncaught page errors'})
            browser.close()
    finally:
        if server:
            server.shutdown(); server.server_close()
        (output / 'receipt.json').write_text(json.dumps({'url': args.url, 'journeys': receipts}, indent=2) + '\n')
    print(json.dumps(receipts, indent=2))


if __name__ == '__main__':
    main()
