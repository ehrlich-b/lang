#!/usr/bin/env python3
"""Real browser journeys against the local workshop or a deployed --base-url.

Uses an installed Chromium and Playwright; no browser download, build, or deploy.
The local HTTP server and browser always close, including on failed assertions.
"""
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import argparse
import hashlib
import json
import os
import threading
import time

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def browser_path():
    if os.environ.get('LANG_BROWSER_BIN'):
        return os.environ['LANG_BROWSER_BIN']
    cache = Path.home() / 'Library/Caches/ms-playwright'
    candidates = sorted(cache.glob('chromium_headless_shell-*/chrome-headless-shell-mac-arm64/chrome-headless-shell'))
    if candidates:
        return str(candidates[-1])
    chrome = Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    return str(chrome) if chrome.exists() else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', help='Existing site URL, e.g. https://lang.ehrlich.dev')
    parser.add_argument('--evidence', default=str(ROOT / 'out/authoring-browser.json'))
    args = parser.parse_args()
    server = None
    started_suite = time.perf_counter()
    evidence = {'base_url': args.base_url or 'local', 'status': 'running', 'journeys': []}
    if not args.base_url:
        evidence['inputs'] = {}
        for name in ['web/compiler.wasm', 'web/stdlib.json', 'web/lab.html', 'web/lab_worker.js', 'web/program_host.js']:
            contents = (ROOT / name).read_bytes()
            evidence['inputs'][name] = {'bytes': len(contents), 'sha256': hashlib.sha256(contents).hexdigest()}

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(ROOT), **kw)

        def log_message(self, *a):
            pass

    if args.base_url:
        base = args.base_url.rstrip('/')
    else:
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = f'http://127.0.0.1:{server.server_port}/web'

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, executable_path=browser_path())
            evidence['browser_version'] = browser.version
            try:
                context = browser.new_context(accept_downloads=True, viewport={'width': 1280, 'height': 1000})
                page = context.new_page()
                page_errors = []
                page.on('pageerror', lambda error: page_errors.append(str(error)))
                page.goto(base + '/lab.html')
                page.wait_for_function("!document.getElementById('compile').disabled")
                run_button = page.get_by_role('button', name='build + run', exact=True)
                reader = page.get_by_label('Reader source', exact=True)
                source = page.get_by_label('Source in your language', exact=True)

                def run(name, expected=None, failed=None):
                    started = time.perf_counter()
                    run_button.click()
                    page.wait_for_function("!document.getElementById('compile').disabled", timeout=60000)
                    status = page.locator('#status').inner_text()
                    output = page.locator('#output').inner_text()
                    if failed:
                        assert status == failed + ' failed', (name, status, output)
                    else:
                        assert status.startswith('ran ·'), (name, status, output)
                        if expected is not None:
                            assert f'main() → {expected}' in output, (name, output)
                        assert page.locator('.pipeline [data-state="done"]').count() == 4
                    evidence['journeys'].append({'name': name, 'elapsed_ms': round((time.perf_counter() - started) * 1000), 'status': status, 'output': output})
                    return output

                def selected(editor):
                    return editor.evaluate('el => ({active: document.activeElement === el, selected: el.value.slice(el.selectionStart, el.selectionEnd)})')

                run('fresh starter', 42)
                starter = reader.input_value()
                page.get_by_role('button', name='new language', exact=True).click()
                page.get_by_label('Language name', exact=True).fill('Orbit')
                page.get_by_label('First keyword', exact=True).fill('launch')
                page.get_by_role('button', name='create language', exact=True).click()
                assert page.locator('#workspace-title').inner_text() == 'Orbit'
                assert "'launch'" in reader.input_value()
                assert source.input_value() == 'launch 42'
                assert page.locator('#grammar-keyword').inner_text() == "'launch'"
                page.get_by_role('button', name='find grammar', exact=True).click()
                assert selected(reader) == {'active': True, 'selected': '#parser{'}
                orbit_id = page.locator('#preset').input_value()
                run('new language', 42)

                modified = reader.input_value().replace('ast_number(value.text)', 'ast_mul(ast_number(value.text), ast_number("2"))')
                reader.fill(modified)
                run('changed lowering', 84)
                page.get_by_role('tab', name='AST', exact=True).click()
                assert '(binop *' in page.locator('#ast-output').inner_text()
                page.get_by_role('tab', name='AST', exact=True).press('End')
                assert page.get_by_role('tab', name='parse tree', exact=True).get_attribute('aria-selected') == 'true'
                page.get_by_role('tab', name='parse tree', exact=True).click()
                tree = page.locator('#tree-output').inner_text()
                assert 'capture "value"' in tree and 'number "42"' in tree, tree
                source.fill('launch 21')
                run('source only reuses reader', 42)
                assert 'reused' in page.locator('#stage-reader-build').inner_text()

                for name, bad_source, token in [
                    ('bad source', 'launch nope', 'nope'),
                    ('Unicode source location', '/* 🐈 */\nlaunch nope', 'nope'),
                    ('trailing source rejected', 'launch 21 extra', 'extra'),
                ]:
                    source.fill(bad_source)
                    diagnostic = run(name, failed='reader run')
                    assert 'source.read:' in diagnostic and 'expected' in diagnostic
                    assert selected(source) == {'active': True, 'selected': token}, (name, selected(source))
                    assert not page.locator('#download-ast').is_visible()
                    assert page.locator('#stage-ast-compile').get_attribute('data-state') == 'pending'
                source.fill('launch 21')
                run('source corrected', 42)

                bad_reader = modified.replace('ast_number("2")', 'ast_number("2", "3")')
                reader.fill(bad_reader)
                diagnostic = run('lowering diagnostic', failed='reader build')
                assert 'takes 1 argument, called with 2' in diagnostic, diagnostic
                assert 'reader.lang:' in diagnostic, diagnostic
                assert selected(reader) == {'active': True, 'selected': 'ast_number'}, selected(reader)
                reader.fill(modified)
                run('reader corrected', 42)

                reader.fill(modified.replace('ast_number("2")', 'ast_number(;)'))
                diagnostic = run('reader syntax location', failed='reader build')
                assert 'reader.lang:' in diagnostic and 'error:' in diagnostic
                assert selected(reader) == {'active': True, 'selected': ';'}, selected(reader)
                reader.fill(modified)
                run('reader syntax corrected', 42)

                one_line = modified.replace("#parser{\n    answer_program = 'launch' value:number\n}", '#parser{ answer_program = missing }')
                # The starter may include explicit eof after a compiler refresh.
                if one_line == modified:
                    one_line = modified.replace("#parser{\n    answer_program = 'launch' value:number eof\n}", '#parser{ answer_program = missing }')
                assert one_line != modified
                reader.fill(one_line)
                diagnostic = run('same-line grammar location', failed='reader build')
                assert '#parser:1:' in diagnostic and 'found missing' in diagnostic
                assert selected(reader) == {'active': True, 'selected': 'missing'}, selected(reader)
                reader.fill(modified + '\n#parser{ other = missing }\n')
                diagnostic = run('multiple grammar blocks avoid false focus', failed='reader build')
                assert 'found missing' in diagnostic
                assert not page.locator('#jump-error').is_visible()
                assert 'multiple blocks' in page.locator('#error-hint').inner_text()
                reader.fill(modified)
                run('grammar corrected', 42)

                source.fill('launch 22')
                page.keyboard.press('Meta+Enter' if os.sys.platform == 'darwin' else 'Control+Enter')
                page.wait_for_function("!document.getElementById('compile').disabled", timeout=60000)
                assert 'main() → 44' in page.locator('#output').inner_text()
                evidence['journeys'].append({'name': 'keyboard build and run', 'output': page.locator('#output').inner_text()})
                source.fill('launch 21')

                page.wait_for_function("document.getElementById('draft-status').textContent === 'saved in this browser'")
                page.reload()
                page.wait_for_function("!document.getElementById('compile').disabled")
                assert page.locator('#workspace-title').inner_text() == 'Orbit'
                assert reader.input_value() == modified and source.input_value() == 'launch 21'
                run('saved language reopened', 42)

                exported = {}
                for artifact in ['reader', 'ast', 'program']:
                    with page.expect_download() as artifact_download:
                        page.locator('#download-' + artifact).click()
                    download = artifact_download.value
                    contents = Path(download.path()).read_bytes()
                    exported[artifact] = {'filename': download.suggested_filename, 'bytes': len(contents)}
                    if artifact == 'ast':
                        assert contents.decode().rstrip() == page.locator('#ast-output').inner_text()
                    else:
                        assert contents.startswith(b'\x00asm'), artifact
                        assert page.evaluate('bytes => WebAssembly.validate(new Uint8Array(bytes))', list(contents))
                    if artifact == 'program':
                        returned = page.evaluate('async bytes => String((await runLangProgram(new Uint8Array(bytes))).value)', list(contents))
                        assert returned == '42'
                evidence['journeys'].append({'name': 'exported AST and Wasm artifacts', 'artifacts': exported, 'exported_program_result': returned})

                with page.expect_download() as download_event:
                    page.keyboard.press('Meta+s' if os.sys.platform == 'darwin' else 'Control+s')
                downloaded = download_event.value
                payload = json.loads(Path(downloaded.path()).read_text())
                assert payload == {'format': 'lang-reader-workspace', 'version': 1, 'title': 'Orbit', 'reader': modified, 'source': 'launch 21', 'runtime': ''}, payload
                evidence['journeys'].append({'name': 'keyboard workspace export', 'filename': downloaded.suggested_filename, 'fields': sorted(payload)})

                page.get_by_role('button', name='fork this reader', exact=True).click()
                page.get_by_label('Language name', exact=True).fill('Orbit fork')
                page.get_by_role('button', name='create language', exact=True).click()
                assert reader.input_value() == modified
                source.fill('launch 5')
                run('fork preserves original draft', 10)
                page.get_by_label('Reader workspace', exact=True).select_option(orbit_id)
                assert source.input_value() == 'launch 21'

                page.locator('#open-workspace').set_input_files({'name': 'Orbit.lang-workspace.json', 'mimeType': 'application/json', 'buffer': json.dumps(payload).encode()})
                page.wait_for_function("document.getElementById('status').textContent === 'loaded'")
                imported_id = page.locator('#preset').input_value()
                assert imported_id != orbit_id
                run('imported workspace runs', 42)
                before = (reader.input_value(), source.input_value(), page.locator('#preset').input_value())
                excessive_field = {**payload, 'reader': '🐈' * (1024 * 1024 // 4 + 1)}
                for name, contents in [('invalid format', b'{"format":"other"}'), ('invalid JSON', b'{broken'), ('oversize container', b' ' * (20 * 1024 * 1024 + 1)), ('oversize UTF-8 field', json.dumps(excessive_field).encode())]:
                    page.locator('#open-workspace').set_input_files({'name': name + '.json', 'mimeType': 'application/json', 'buffer': contents})
                    page.wait_for_function("document.getElementById('status').textContent === 'open failed'")
                    assert (reader.input_value(), source.input_value(), page.locator('#preset').input_value()) == before
                    evidence['journeys'].append({'name': name + ' preserves draft', 'message': page.locator('#output').inner_text()})

                large_payload = {
                    **payload, 'title': 'Large valid draft',
                    'reader': modified + '\n/*' + 'r' * (700 * 1024 - len(modified.encode()) - 5) + '*/',
                    'source': '/*' + 's' * (400 * 1024 - 17) + '*/\nlaunch 21',
                }
                large_json = json.dumps(large_payload).encode()
                assert len(large_json) > 1024 * 1024
                page.locator('#open-workspace').set_input_files({'name': 'large-valid.json', 'mimeType': 'application/json', 'buffer': large_json})
                page.wait_for_function("document.getElementById('status').textContent === 'loaded'")
                assert reader.input_value() == large_payload['reader']
                assert source.input_value() == large_payload['source']
                with page.expect_download() as large_download:
                    page.locator('#save-workspace').click()
                assert json.loads(Path(large_download.value.path()).read_text()) == large_payload
                evidence['journeys'].append({'name': 'combined workspace over 1 MiB roundtrips', 'json_bytes': len(large_json)})
                page.get_by_label('Reader workspace', exact=True).select_option(imported_id)

                page.get_by_label('Reader workspace', exact=True).select_option('workshop')
                source.fill('add ;\nadd word;\nadd 42;')
                diagnostic = run('multiple diagnostics', failed='reader run')
                assert 'workshop:1:5:' in diagnostic and 'workshop:2:5:' in diagnostic
                page.get_by_label('Diagnostic location', exact=True).select_option('1')
                assert selected(source) == {'active': True, 'selected': 'word'}
                source.fill('add 20;\nadd 22;')
                run('recovered source', 42)

                page.get_by_label('Reader workspace', exact=True).select_option(imported_id)
                reader.fill('''reader read(text *u8) *u8 {
    while 1 { }
    return nil;
}
''')
                run_button.click()
                page.wait_for_function("document.getElementById('stage-reader-run').dataset.state === 'running'", timeout=60000)
                page.keyboard.press('Escape')
                assert page.locator('#status').inner_text() == 'stopped'
                assert not run_button.is_disabled()
                assert not reader.evaluate('el => el.readOnly')
                assert not page.locator('#download-reader').is_visible()
                evidence['journeys'].append({'name': 'infinite reader stopped with Escape', 'message': page.locator('#output').inner_text()})
                reader.fill(modified)
                source.fill('launch 21')
                run('corrected reader after cancellation', 42)

                # Compile valid AST containing an infinite loop, then stop it.
                # This would freeze the page if execution returned to the UI thread.
                page.get_by_label('Reader workspace', exact=True).select_option(imported_id)
                infinite = '''include "std/ast.lang"
reader read(text *u8) *u8 {
    return "(program (func main (params) i64 (block (while (number 1) (block)) (return (number 0)))))";
}
'''
                reader.fill(infinite)
                page.set_viewport_size({'width': 390, 'height': 844})
                run_button.click()
                page.wait_for_function("document.getElementById('stage-program-run').dataset.state === 'running'", timeout=60000)
                assert page.locator('#stop-build').is_enabled()
                assert reader.evaluate('el => el.readOnly')
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'active Stop controls overflow mobile viewport'
                page.get_by_role('button', name='stop', exact=True).click()
                assert page.locator('#status').inner_text() == 'stopped'
                assert not run_button.is_disabled()
                assert not reader.evaluate('el => el.readOnly')
                assert not page.locator('#download-program').is_visible()
                evidence['journeys'].append({'name': 'infinite program stopped on mobile', 'message': page.locator('#output').inner_text()})
                page.set_viewport_size({'width': 1280, 'height': 1000})
                reader.fill(modified)
                source.fill('launch 21')
                run('corrected program after cancellation', 42)

                # Explicit runtime exit must not be mistaken for main returning 3.
                reader.fill('''include "std/ast.lang"
reader read(text *u8) *u8 {
    var statements *u8 = ast_vec();
    ast_push(statements, ast_expr_stmt(ast_call1("exit", ast_number("3"))));
    ast_push(statements, ast_return(ast_number("0")));
    return ast_program1(ast_func("main", ast_vec(), ast_type_i64(), ast_block(statements)));
}
''')
                page.locator('details.runtime').evaluate('el => el.open = true')
                page.get_by_label('Target runtime source', exact=True).fill('include "std/core.lang"')
                diagnostic = run('explicit nonzero exit', failed='program run')
                assert 'program exited with status 3' in diagnostic
                reader.fill(modified)
                page.get_by_label('Target runtime source', exact=True).fill('')
                run('corrected after runtime exit', 42)

                reader.fill('''include "std/ast.lang"
reader read(text *u8) *u8 {
    return ast_main_i64(ast_binop("/", ast_number("1"), ast_number("0")));
}
''')
                diagnostic = run('runtime trap is a failure', failed='program run')
                assert 'divide by zero' in diagnostic, diagnostic
                reader.fill(modified)
                run('corrected after trap', 42)

                reader.fill('''include "std/ast.lang"
reader read(text *u8) *u8 {
    return ast_program1(ast_func("main", ast_vec(), ast_type("f64"),
        ast_block1(ast_return(ast_number("1.5")))));
}
''')
                run('reader floating AST and main ABI', '1.5')
                reader.fill(modified)
                run('integer reader restored after floating program', 42)

                evidence_path = Path(args.evidence)
                evidence_path.parent.mkdir(parents=True, exist_ok=True)
                page.locator('details.runtime').evaluate('el => el.open = false')
                page.screenshot(path=str(evidence_path.with_suffix('.desktop.png')), full_page=True)
                page.set_viewport_size({'width': 390, 'height': 844})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'workshop overflows mobile viewport'
                page.screenshot(path=str(evidence_path.with_suffix('.mobile.png')), full_page=True)
                evidence['screenshots'] = [str(evidence_path.with_suffix('.desktop.png')), str(evidence_path.with_suffix('.mobile.png'))]
                page.set_viewport_size({'width': 1280, 'height': 1000})

                assert not page_errors, page_errors
                evidence['page_errors'] = page_errors
                evidence['final_drafts'] = page.locator('#draft-options option').count()
                saved_library = page.evaluate("localStorage.getItem('lang.lab.library.v1')")
                context.close()

                recovery = browser.new_context()
                recovery.add_init_script('localStorage.setItem("lang.lab.library.v1.backup", ' + json.dumps(saved_library) + '); localStorage.setItem("lang.lab.library.v1", "{broken");')
                recovered = recovery.new_page()
                recovered.goto(base + '/lab.html')
                recovered.wait_for_function("!document.getElementById('compile').disabled")
                assert 'Recovered your draft library' in recovered.locator('#output').inner_text()
                assert recovered.get_by_label('Reader source', exact=True).input_value() == modified
                assert recovered.get_by_label('Source in your language', exact=True).input_value() == 'launch 21'
                evidence['journeys'].append({'name': 'corrupt library recovered from backup', 'message': recovered.locator('#output').inner_text()})
                recovery.close()

                offline = browser.new_context(accept_downloads=True)
                offline.add_init_script('localStorage.setItem("lang.lab.library.v1", ' + json.dumps(saved_library) + ');')
                offline_page = offline.new_page()
                offline_page.route('**/compiler.wasm?*', lambda route: route.abort())
                offline_page.goto(base + '/lab.html')
                offline_page.wait_for_function("document.getElementById('status').textContent === 'load failed'")
                assert offline_page.get_by_label('Reader source', exact=True).input_value() == modified
                assert offline_page.get_by_label('Source in your language', exact=True).input_value() == 'launch 21'
                assert offline_page.get_by_role('button', name='new language', exact=True).is_disabled()
                with offline_page.expect_download() as offline_download:
                    offline_page.locator('#save-workspace').click()
                assert json.loads(Path(offline_download.value.path()).read_text())['reader'] == modified
                evidence['journeys'].append({'name': 'offline compiler assets preserve and export draft', 'message': offline_page.locator('#output').inner_text()})
                offline.close()

                blocked = browser.new_context(accept_downloads=True)
                blocked.add_init_script('Storage.prototype.setItem = () => { throw new DOMException("storage blocked", "QuotaExceededError"); };')
                unsaved = blocked.new_page()
                unsaved.goto(base + '/lab.html')
                unsaved.wait_for_function("!document.getElementById('compile').disabled")
                unsaved.get_by_label('Source in your language', exact=True).fill('answer 19')
                unsaved.wait_for_function("document.getElementById('draft-status').textContent.startsWith('autosave unavailable')")
                with unsaved.expect_download() as blocked_download:
                    unsaved.locator('#save-workspace').click()
                assert json.loads(Path(blocked_download.value.path()).read_text())['source'] == 'answer 19'
                evidence['journeys'].append({'name': 'unavailable storage still exports', 'message': unsaved.locator('#draft-status').inner_text()})
                blocked.close()

                legacy = browser.new_context()
                legacy.add_init_script('localStorage.setItem("lang.lab.active", "workspace"); localStorage.setItem("lang.lab.workspace.reader", ' + json.dumps(starter) + '); localStorage.setItem("lang.lab.workspace.source", "answer 17"); localStorage.setItem("lang.lab.workspace.runtime", "");')
                older = legacy.new_page()
                older.goto(base + '/lab.html')
                older.wait_for_function("!document.getElementById('compile').disabled")
                assert older.get_by_label('Source in your language', exact=True).input_value() == 'answer 17'
                older.get_by_role('button', name='build + run', exact=True).click()
                older.wait_for_function("!document.getElementById('compile').disabled", timeout=60000)
                assert 'main() → 17' in older.locator('#output').inner_text()
                migrated = json.loads(older.evaluate("localStorage.getItem('lang.lab.library.v1')"))
                assert migrated['drafts']['workspace']['source'] == 'answer 17'
                evidence['journeys'].append({'name': 'legacy draft reopened and migrated', 'output': older.locator('#output').inner_text()})
                legacy.close()
            finally:
                browser.close()
        evidence['status'] = 'passed'
    except Exception as error:
        evidence['status'] = 'failed'
        evidence['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        if server:
            server.shutdown()
            server.server_close()
        path = Path(args.evidence)
        path.parent.mkdir(parents=True, exist_ok=True)
        evidence['elapsed_ms'] = round((time.perf_counter() - started_suite) * 1000)
        path.write_text(json.dumps(evidence, indent=2) + '\n')
    print(f'PASS authoring_browser_e2e ({len(evidence["journeys"])} journeys; {args.evidence})')


if __name__ == '__main__':
    main()
