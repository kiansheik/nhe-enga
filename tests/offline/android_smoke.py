"""Emulator-only Android/WebView acceptance test. Resets only the debug package.

Run with JDK 17/21, ANDROID_HOME, adb, and Playwright available:
    python3 tests/offline/android_smoke.py
    python3 tests/offline/android_smoke.py --site .pages-build
"""
import argparse
import functools
import http.server
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import threading
import time
import xml.etree.ElementTree as ET

import playwright
from fixture import fixture

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = "io.kiansheik.nheenga.debug"
ACTIVITY = "io.kiansheik.nheenga.MainActivity"
BASE = "https://appassets.androidplatform.net/nhe-enga/"


def adb(*arguments, check=True):
    serial = os.environ.get("ANDROID_SERIAL", "emulator-5554")
    return subprocess.run(["adb", "-s", serial, *arguments], check=check, capture_output=True, text=True).stdout.strip()


def state():
    try:
        return json.loads(adb("shell", "run-as", PACKAGE, "cat", "files/library/state.json"))
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return {}


def wait_state(predicate, timeout=90):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        current = state()
        if predicate(current):
            return current
    raise AssertionError(f"Library did not reach expected state: {state()}")


def tap(label):
    for attempt in range(14):
        adb("shell", "uiautomator", "dump", "/data/local/tmp/nhe-enga-window.xml")
        hierarchy = ET.fromstring(adb("exec-out", "cat", "/data/local/tmp/nhe-enga-window.xml"))
        width, height = map(int, re.findall(r"\d+", hierarchy.find("node").get("bounds"))[-2:])
        for node in hierarchy.iter("node"):
            if label.casefold() not in node.get("text", "").casefold() or node.get("clickable") != "true":
                continue
            left, top, right, bottom = map(int, re.findall(r"\d+", node.get("bounds")))
            if bottom - top >= 24 and 24 <= (top + bottom) // 2 < height - 24:
                adb("shell", "input", "tap", str((left + right) // 2), str((top + bottom) // 2))
                return
        start, end = (height * 4 // 5, height // 4) if attempt < 9 else (height // 4, height * 4 // 5)
        adb("shell", "input", "swipe", str(width // 2), str(start), str(width // 2), str(end), "150")
    raise AssertionError(f"Native control not found: {label}")


def launch():
    adb("shell", "am", "start", "-W", "-n", f"{PACKAGE}/{ACTIVITY}")


def check_webview(real_site, offline, tools):
        driver = Path(playwright.__file__).parent / "driver/package"
        script = r"""
const assert = require('node:assert/strict');
const {_android} = require(process.argv[1]);
const real = process.argv[2] === 'true', offline = process.argv[3] === 'true';
const tools = process.argv[5] === 'true';
(async () => {
    const discovered = await _android.devices();
    const devices = discovered.filter(device => device.serial() === process.argv[6]);
    assert.equal(devices.length, 1, 'Selected emulator is not connected');
    const device = devices[0];
    try {
        await device.shell('am start -W -n io.kiansheik.nheenga.debug/io.kiansheik.nheenga.MainActivity');
        const view = await device.webView({pkg: 'io.kiansheik.nheenga.debug'});
        const page = await view.page();
        page.setDefaultTimeout(60000);
        const base = 'https://appassets.androidplatform.net/nhe-enga/';
        const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        if (real) {
            for (const route of ['', 'katu/', 'mbya/']) {
                await page.goto(base + route);
                await page.locator('#searchInput').fill('abacaxi');
                await page.locator('#searchButton').click();
                await page.locator('#results .preview').first().waitFor();
                console.log('PASS real dictionary search (' + (offline ? 'offline' : 'online') + '): /' + route);
            }
            await page.goto(base + 'quiz/');
            await page.waitForFunction(() => typeof filteredDataset !== 'undefined' && filteredDataset.length > 0 && document.querySelector('#question').innerText.trim());
            const answer = await page.evaluate(() => {
                const current = filteredDataset[currentQuestionIndex];
                return {mode: modes.find(mode => mode.slice(0, 2) === current.m), subject: reverseSubjPrefMap[current.s] ?? 'ø', object: reverseObjPrefMap[current.o] ?? 'ø'};
            });
            for (const [name, value] of Object.entries(answer)) await page.locator('#' + name).selectOption(value);
            await page.locator('#enviar').click();
            assert.equal(await page.evaluate(() => score), 3);
            console.log('PASS real quiz answer (' + (offline ? 'offline' : 'online') + ')');
            await page.goto(base + 'docs/primary_sources/cartas_portiguara/Figura1.jpg');
            await page.waitForFunction(() => document.querySelector('img')?.naturalWidth > 0);
            console.log('PASS selected Cartas source image (' + (offline ? 'offline' : 'online') + ')');
            for (const book of ['vlb']) {
                await page.goto(base + 'docs/primary_sources/?book_name=' + book + '&page_number=1');
                await page.waitForFunction(() => document.querySelector('#pageImage')?.naturalWidth > 0);
                await page.locator('#zoomPage').click();
                assert.equal(await page.locator('#zoomPage').getAttribute('aria-pressed'), 'true');
                console.log('PASS real source image + zoom (' + (offline ? 'offline' : 'online') + '): ' + book);
            }
            if (tools) {
                await page.goto(base + 'sentence-builder.html');
                await page.waitForFunction(() => typeof pyodideReady !== 'undefined' && pyodideReady === true, null, {timeout: 120000});
                assert.ok(await page.evaluate(() => window.jsonData.length > 0));
                const noun = await page.evaluate(() => globalPyodide.runPython("str(tupi.Noun('ker', 'normal'))"));
                assert.ok(noun.length > 0);
                console.log('PASS local Pyodide + micropip + Tupi wheel (' + (offline ? 'offline' : 'online') + ')');
            }
        } else {
            await page.goto(base);
            assert.equal(await page.locator('#version').innerText(), 'v1');
            await page.goto(base + 'docs/primary_sources/?book_name=lerhist&page_number=2');
            await page.waitForFunction(() => document.querySelector('#scan').naturalWidth > 0);
            if (offline) {
                const response = await page.goto(base + 'docs/primary_sources/lerhist/1.png');
                assert.equal(response.status(), 404);
                assert.match(await page.locator('body').innerText(), /ainda não foi baixado/);
            }
        }
        assert.deepEqual(errors, []);
        await device.wait({desc: 'Configurações e downloads'});
        await device.screenshot({path: process.argv[4]});
        await device.tap({desc: 'Configurações e downloads'});
        await device.wait({text: "Nhe'enga sem internet"});
        console.log('PASS compact settings gear opens native downloads');
    } finally {
        for (const connection of discovered) await connection.close();
    }
})().catch(error => { console.error(error); process.exitCode = 1; });
"""
        screenshot = ROOT / "dist" / f"android-{'real' if real_site else 'fixture'}-{'offline' if offline else 'online'}.png"
        subprocess.run(["node", "-e", script, str(driver), str(real_site).lower(), str(offline).lower(), str(screenshot), str(tools).lower(), os.environ.get("ANDROID_SERIAL", "emulator-5554")], check=True, timeout=300)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path)
    parser.add_argument("--port", type=int, default=18766)
    parser.add_argument("--tools", action="store_true")
    parser.add_argument("--serial", default=os.environ.get("ANDROID_SERIAL", "emulator-5554"))
    args = parser.parse_args()
    os.environ["ANDROID_SERIAL"] = args.serial
    assert adb("shell", "getprop", "ro.kernel.qemu") == "1", "Refusing to reset a physical device"
    original_airplane = adb("shell", "settings", "get", "global", "airplane_mode_on")
    original_wifi = adb("shell", "settings", "get", "global", "wifi_on")
    requests = []
    online = threading.Event()
    online.set()
    with tempfile.TemporaryDirectory() as temporary:
        site = args.site.resolve() if args.site else Path(temporary) / "nhe-enga"
        if not args.site:
            fixture(site)
        assert (site / "offline/catalog.json").is_file(), "Prepare the offline site first"

        class Handler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_GET(self):
                requests.append(self.path)
                if not online.is_set():
                    self.send_error(503, "Offline acceptance test")
                    return
                if not self.path.startswith("/nhe-enga/"):
                    self.send_error(404)
                    return
                self.path = self.path.removeprefix("/nhe-enga")
                super().do_GET()

            def end_headers(self):
                self.send_header("Cache-Control", "no-store")
                super().end_headers()

        server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), functools.partial(Handler, directory=str(site)))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            environment = dict(os.environ, OFFLINE_CONTENT_BASE=f"http://10.0.2.2:{args.port}/nhe-enga/")
            subprocess.run([str(ROOT / "android/gradlew"), "--no-watch-fs", ":app:assembleDebug"], env=environment, check=True)
            adb("install", "-r", str(ROOT / "android/app/build/outputs/apk/debug/app-debug.apk"))
            adb("shell", "am", "force-stop", PACKAGE)
            adb("shell", "pm", "clear", PACKAGE)
            adb("shell", "pm", "grant", PACKAGE, "android.permission.POST_NOTIFICATIONS", check=False)
            online.clear()
            adb("shell", "cmd", "connectivity", "airplane-mode", "enable")
            adb("shell", "svc", "wifi", "disable")
            launch()
            tap("Abrir dicionários")
            assert not state().get("installed", {}).get("core")
            assert adb("shell", "pidof", PACKAGE), "Fresh offline setup crashed"
            print("PASS fresh install offline: native setup, no library, no crash", flush=True)

            online.set()
            adb("shell", "cmd", "connectivity", "airplane-mode", "disable")
            adb("shell", "svc", "wifi", "enable")
            tap("Consultar opções")
            tap("Salvar / baixar seleção")
            wait_state(lambda current: "core" in current.get("installed", {}))
            assert set(state()["installed"]) == {"core"}
            assert not any(re.search(r"/primary_sources/[^/]+/.*\.(png|jpg|webp)", path) for path in requests)
            print("PASS core-only install: no bulk source images", flush=True)
            if args.site:
                tap("Cartas Potiguaras")
                if args.tools:
                    tap("Gramática e ferramentas")
                tap("Salvar / baixar seleção")
                wanted = {"core", "source-cartas_portiguara"} | ({"tools"} if args.tools else set())
                wait_state(lambda current: wanted <= current.get("installed", {}).keys(), timeout=180)
                assert set(state()["installed"]) == wanted
                print("PASS selected real source/tools packs; no unselected books", flush=True)
            tap("Abrir dicionários")

            check_webview(bool(args.site), False, args.tools)
            if not args.site:
                wait_state(lambda current: "docs/primary_sources/lerhist/2.png" in current.get("saved", {}))
                assert "source-lerhist" not in state()["installed"]
                print("PASS viewed-only source page persists without whole-book download", flush=True)
            online.clear()
            adb("shell", "cmd", "connectivity", "airplane-mode", "enable")
            adb("shell", "svc", "wifi", "disable")
            adb("shell", "am", "force-stop", PACKAGE)
            before = len(requests)
            launch()
            check_webview(bool(args.site), True, args.tools)
            assert len(requests) == before, "Offline library made network requests"
            print("PASS airplane-mode force-stop/relaunch: local content, zero server requests", flush=True)
            print(f"PASS Android smoke ({'real site' if args.site else 'synthetic fixture'})", flush=True)
        finally:
            online.set()
            adb("shell", "cmd", "connectivity", "airplane-mode", "enable" if original_airplane == "1" else "disable", check=False)
            adb("shell", "svc", "wifi", "enable" if original_wifi in ("1", "2") else "disable", check=False)
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    main()