"""Real Chromium service-worker smoke test, with a synthetic local static site.

Install: python -m pip install playwright && python -m playwright install chromium
Optional: CHROMIUM_PATH=/usr/bin/chromium
"""
import functools
import http.server
import json
import os
from pathlib import Path
import tempfile
import threading
from playwright.sync_api import sync_playwright
from fixture import fixture, build_offline


def main():
    with tempfile.TemporaryDirectory() as tmp:
        site = Path(tmp) / "nhe-enga"
        catalog = fixture(site)
        requests = []
        class Handler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *_): pass
            def do_GET(self):
                requests.append(self.path)
                super().do_GET()
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=tmp))
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        base = f"http://127.0.0.1:{server.server_port}/nhe-enga/"
        try:
            with sync_playwright() as pw:
                launch = {"headless": True, "args": ["--no-sandbox"]}
                if os.environ.get("CHROMIUM_PATH"): launch["executable_path"] = os.environ["CHROMIUM_PATH"]
                browser = pw.chromium.launch(**launch)
                context = browser.new_context(service_workers="allow")
                page = context.new_page(); page.goto(base)
                page.wait_for_function("async () => {const r=await(await caches.open('nhe-offline-meta-v1')).match('/nhe-enga/offline/state');return r && !!(await r.json()).installed.core}")
                page.reload(); assert page.locator("#version").inner_text() == "v1"
                context.set_offline(True); page.reload(); assert page.locator("#version").inner_text() == "v1"
                print("PASS cold offline navigation after core bootstrap")
                context.set_offline(False)
                worker = context.service_workers[0]
                # Exercise the same command used by the download UI.
                page.evaluate("navigator.serviceWorker.controller.postMessage({type:'sync',selected:['core','source-vlb'],allSources:false})")
                page.wait_for_function("async () => {const r=await(await caches.open('nhe-offline-meta-v1')).match('/nhe-enga/offline/state');return !!(await r.json()).installed['source-vlb']}")
                assert not any('/lerhist/2.png' in r for r in requests)
                context.set_offline(True)
                page.goto(base + 'docs/primary_sources/?book_name=vlb&page_number=1')
                page.wait_for_function("document.getElementById('scan').naturalWidth > 0")
                print("PASS selected source pack, query-string citation route, no bulk unselected images")
                context.set_offline(False); page.goto(base)
                old = catalog['packs'][0]['sha256']
                text = (site / 'index.html').read_text().replace('>v1<', '>v2<')
                (site / 'index.html').write_text(text)
                catalog = build_offline.generate(site, 2)
                expected = next(p['sha256'] for p in catalog['packs'] if p['id'] == 'core')
                before = len([r for r in requests if '/vlb/1.png' in r])
                page.evaluate("navigator.serviceWorker.controller.postMessage({type:'sync'})")
                page.wait_for_function("async h => {const r=await(await caches.open('nhe-offline-meta-v1')).match('/nhe-enga/offline/state');return (await r.json()).installed.core.hash===h}", arg=expected)
                assert page.locator('#version').inner_text() == 'v1', 'Running document changed during update'
                assert len([r for r in requests if '/vlb/1.png' in r]) == before, 'Unchanged source downloaded again'
                context.set_offline(True); page.reload(); assert page.locator('#version').inner_text() == 'v2'
                print("PASS coherent update, no unchanged-image transfer, old document remains usable")
                context.set_offline(False)
                (site / 'index.html').write_text(text.replace('>v2<', '>v3<'))
                build_offline.generate(site, 3)
                (site / 'index.html').write_text('corrupt server response')
                page.evaluate("window.offlineError=null;navigator.serviceWorker.addEventListener('message',e=>{if(e.data.type==='error')window.offlineError=e.data.text});navigator.serviceWorker.controller.postMessage({type:'sync'})")
                page.wait_for_function('window.offlineError !== null')
                assert 'corrompido' in page.evaluate('window.offlineError')
                context.set_offline(True); page.reload(); assert page.locator('#version').inner_text() == 'v2'
                print("PASS corrupt update rejected and last verified version preserved")
                browser.close()
        finally:
            server.shutdown(); server.server_close(); thread.join()


if __name__ == '__main__': main()
