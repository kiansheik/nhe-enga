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
            def log_message(self, *_):
                pass

            def end_headers(self):
                self.send_header("Cache-Control", "no-store")
                super().end_headers()

            def do_GET(self):
                requests.append(self.path)
                super().do_GET()

        server = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), functools.partial(Handler, directory=tmp)
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}/nhe-enga/"
        try:
            with sync_playwright() as pw:
                launch = {"headless": True, "args": ["--no-sandbox"]}
                if os.environ.get("CHROMIUM_PATH"):
                    launch["executable_path"] = os.environ["CHROMIUM_PATH"]
                browser = pw.chromium.launch(**launch)
                context = browser.new_context(service_workers="allow")
                page = context.new_page()
                page.goto(base)
                page.wait_for_function(
                    "async () => {const r=await(await caches.open('nhe-offline-meta-v1')).match('/nhe-enga/offline/state');return r && !!(await r.json()).installed.core}"
                )
                page.reload()
                assert page.locator("#version").inner_text() == "v1"
                context.set_offline(True)
                page.reload()
                assert page.locator("#version").inner_text() == "v1"
                print("PASS cold offline navigation after core bootstrap")
                context.set_offline(False)
                worker = context.service_workers[0]
                # Exercise the same command used by the download UI.
                page.evaluate(
                    "navigator.serviceWorker.controller.postMessage({type:'sync',selected:['core','source-vlb'],allSources:false})"
                )
                page.wait_for_function(
                    "async () => {const r=await(await caches.open('nhe-offline-meta-v1')).match('/nhe-enga/offline/state');return !!(await r.json()).installed['source-vlb']}"
                )
                assert not any("/lerhist/2.png" in r for r in requests)
                context.set_offline(True)
                page.goto(base + "docs/primary_sources/?book_name=vlb&page_number=1")
                page.wait_for_function(
                    "document.getElementById('scan').naturalWidth > 0"
                )
                print(
                    "PASS selected source pack, query-string citation route, no bulk unselected images"
                )
                context.set_offline(False)
                page.goto(base)
                old = catalog["packs"][0]["sha256"]
                text = (site / "index.html").read_text().replace(">v1<", ">v2<")
                (site / "index.html").write_text(text)
                catalog = build_offline.generate(site, 2)
                expected = next(
                    p["sha256"] for p in catalog["packs"] if p["id"] == "core"
                )
                before = len([r for r in requests if "/vlb/1.png" in r])
                page.evaluate(
                    "navigator.serviceWorker.controller.postMessage({type:'sync'})"
                )
                page.wait_for_function(
                    "async h => {const r=await(await caches.open('nhe-offline-meta-v1')).match('/nhe-enga/offline/state');return (await r.json()).installed.core.hash===h}",
                    arg=expected,
                )
                assert (
                    page.locator("#version").inner_text() == "v1"
                ), "Running document changed during update"
                assert (
                    len([r for r in requests if "/vlb/1.png" in r]) == before
                ), "Unchanged source downloaded again"
                context.set_offline(True)
                page.reload()
                assert page.locator("#version").inner_text() == "v2"
                print(
                    "PASS coherent update, no unchanged-image transfer, old document remains usable"
                )
                context.set_offline(False)
                (site / "index.html").write_text(text.replace(">v2<", ">v3<"))
                build_offline.generate(site, 3)
                page.goto(base + "?release=3")
                assert page.locator("#version").inner_text() == "v3"
                print("PASS online navigation revalidates a stale offline catalog")
                (site / "index.html").write_text(text.replace(">v2<", ">v4<"))
                build_offline.generate(site, 4)
                (site / "index.html").write_text("corrupt server response")
                page.evaluate(
                    "window.offlineError=null;navigator.serviceWorker.addEventListener('message',e=>{if(e.data.type==='error')window.offlineError=e.data.text});navigator.serviceWorker.controller.postMessage({type:'sync'})"
                )
                page.wait_for_function("window.offlineError !== null")
                assert "corrompido" in page.evaluate("window.offlineError")
                context.set_offline(True)
                page.reload()
                assert page.locator("#version").inner_text() == "v2"
                print(
                    "PASS corrupt update rejected and last verified version preserved"
                )
                context.set_offline(False)
                page.goto(
                    base + "docs/primary_sources/?book_name=lerhist&page_number=2"
                )
                page.wait_for_function(
                    "document.getElementById('scan').naturalWidth > 0"
                )
                page.wait_for_function(
                    "async () => {const r=await(await caches.open('nhe-offline-meta-v1')).match('/nhe-enga/offline/state');return !!(await r.json()).saved['docs/primary_sources/lerhist/2.png']}"
                )
                page.goto(base + "offline/")
                saved_row = page.locator("#packs > div").filter(has_text="Léry")
                saved_row.get_by_role("button", name="Remover download").wait_for()
                page.on("dialog", lambda dialog: dialog.accept())
                saved_row.get_by_role("button", name="Remover download").click()
                page.wait_for_function(
                    "async () => {const r=await(await caches.open('nhe-offline-meta-v1')).match('/nhe-enga/offline/state');return !(await r.json()).saved['docs/primary_sources/lerhist/2.png']}"
                )
                print("PASS saved-only source removal through download UI")
                homepage = (build_offline.ROOT / "index.html").read_text()
                for viewport_width, android in (
                    (360, True),
                    (400, True),
                    (1280, False),
                ):
                    install_context = browser.new_context(
                        service_workers="block",
                        user_agent=(
                            "Mozilla/5.0 (Linux; Android 14) Chrome/140.0 Mobile"
                            if android
                            else "Desktop Browser"
                        ),
                        viewport={"width": viewport_width, "height": 800},
                    )
                    install_page = install_context.new_page()
                    install_page.route(
                        base,
                        lambda route: route.fulfill(
                            body=homepage, content_type="text/html"
                        ),
                    )
                    install_page.route(
                        "**/styles.css",
                        lambda route: route.fulfill(
                            body=(build_offline.ROOT / "styles.css").read_text(),
                            content_type="text/css",
                        ),
                    )
                    install_page.route(
                        "**/downloads/android.json",
                        lambda route: route.fulfill(
                            json={
                                "url": "nhe-enga.apk",
                                "versionCode": 1,
                                "versionName": "0.1.0",
                                "bytes": 350000,
                                "sha256": "a" * 64,
                            }
                        ),
                    )
                    install_page.goto(base)
                    if android:
                        install_page.locator("#android-install").wait_for()
                        install_page.evaluate("document.fonts.ready")
                        link_bounds = "links => links.map(link => {const bounds = link.getBoundingClientRect(); return [bounds.x, bounds.y, bounds.width, bounds.height]})"
                        shown = install_page.locator(
                            "main > .content > a"
                        ).evaluate_all(link_bounds)
                        install_page.locator("#android-install").evaluate(
                            "button => button.hidden = true"
                        )
                        hidden = install_page.locator(
                            "main > .content > a"
                        ).evaluate_all(link_bounds)
                        assert (
                            shown == hidden
                        ), "Install icon changed homepage link positions or spacing"
                        install_page.locator("#android-install").evaluate(
                            "button => button.hidden = false"
                        )
                        install_page.locator("#android-install").click()
                        assert install_page.locator(
                            "#android-install-dialog"
                        ).is_visible()
                        assert (
                            "APK é assinado"
                            in install_page.locator(
                                "#android-install-dialog"
                            ).inner_text()
                        )
                        assert (
                            install_page.locator("#android-apk-download").get_attribute(
                                "href"
                            )
                            == "/nhe-enga/downloads/nhe-enga.apk"
                        )
                        install_page.get_by_role("button", name="Agora não").click()
                        assert not install_page.locator(
                            "#android-install-dialog"
                        ).is_visible()
                    else:
                        assert install_page.locator("#android-install").is_hidden()
                    for navigation_link in install_page.locator(
                        "main > .content > a"
                    ).all():
                        bounds = navigation_link.bounding_box()
                        self_center = bounds["x"] + bounds["width"] / 2
                        assert (
                            abs(self_center - install_page.viewport_size["width"] / 2)
                            < 1
                        ), "Install icon shifted a centered navigation link"
                    install_context.close()
                print(
                    "PASS Android-only install icon, consent dialog, fixed APK URL, and centered homepage links"
                )
                browser.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    main()
