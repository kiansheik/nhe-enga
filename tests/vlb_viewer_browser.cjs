#!/usr/bin/env node
// Real-browser checks for the VLB comparison workflow. Install Playwright and its
// Chromium, or set VLB_CHROMIUM_PATH to an existing executable. The sparse
// checkout needs scans 17, 25, 26, 161, 232, 292 and 303 for image assertions.
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const http = require("node:http");
const os = require("node:os");
const {chromium} = require(process.env.VLB_PLAYWRIGHT_MODULE || "playwright");
const root = path.resolve(__dirname, "..");
const out = process.env.VLB_QA_DIR || fs.mkdtempSync(path.join(os.tmpdir(), "vlb-browser-"));
fs.mkdirSync(out, {recursive: true});
const mime = {".html":"text/html; charset=utf-8", ".js":"application/javascript; charset=utf-8", ".css":"text/css; charset=utf-8", ".json":"application/json", ".gz":"application/gzip", ".png":"image/png", ".jpg":"image/jpeg", ".ico":"image/x-icon"};
const server = http.createServer((req, res) => {
  const url = new URL(req.url, "http://localhost");
  if (!url.pathname.startsWith("/nhe-enga/")) { res.writeHead(404).end(); return; }
  const file = path.resolve(root, "." + decodeURIComponent(url.pathname.slice("/nhe-enga".length)) + (url.pathname.endsWith("/") ? "index.html" : ""));
  if (!file.startsWith(root + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404).end(); return; }
  res.writeHead(200, {"Content-Type":mime[path.extname(file)] || "application/octet-stream"});
  fs.createReadStream(file).pipe(res);
});

(async () => {
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  const base = `http://127.0.0.1:${server.address().port}/nhe-enga/vlb/`;
  const browser = await chromium.launch({headless:true, executablePath:process.env.VLB_CHROMIUM_PATH || undefined,
    args:["--no-sandbox", "--disable-dev-shm-usage"]});
  const context = await browser.newContext({viewport:{width:1440,height:1080}, reducedMotion:"reduce"});
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  async function open(query) {
    await page.goto(base + query);
    await page.locator("#transcription-panel:not([aria-busy]) .fragment, #fragment-list .empty-state").first().waitFor({state:"attached"});
    await page.waitForFunction(() => document.getElementById("page-image").naturalWidth > 0);
    assert.equal(await page.locator("#load-error").isVisible(), false);
  }
  async function source(number) {
    await page.locator(`#source-${number} .source-main`).click();
    assert.equal(await page.locator(`#source-${number}`).getAttribute("class"), "fragment selected");
    assert.ok(await page.locator("#ocr-overlay rect").count() > 0, "selected source has OCR highlight");
  }
  try {
    await open("?volume=I&page=17");
    assert.equal(await page.locator("#text-count").innerText(), "29");
    assert.equal(await page.locator('a[href="https://abanheenga.blogspot.com/p/como-aprender-tupi.html"]').count(), 2);
    await page.screenshot({path:path.join(out, "vlb-desktop.png"), fullPage:true});
    await source(13);
    assert.ok(page.url().includes("source=vlb-emerson-r568-p00013"));
    await page.locator("#zoom-in").click();
    assert.equal(await page.locator("#zoom-reset").innerText(), "125%");
    await page.locator("#show-ocr").uncheck();
    assert.equal(await page.locator("#ocr-overlay rect").count(), 0);
    await page.locator("#show-ocr").check();
    await page.locator("#zoom-reset").click();

    // An entry deep link identifies its citation, without accepting a proposed
    // source association. The user explicitly chooses the source paragraph.
    await open("?volume=I&page=17&entry=7210");
    assert.equal(await page.locator("#citations-tab").getAttribute("aria-selected"), "true");
    assert.equal(await page.locator(".fragment.selected").count(), 0);
    assert.ok((await page.locator("#citation-detail h3").innerText()).includes("mokanãî"));
    assert.ok((await page.locator("#citation-detail h3 a").getAttribute("href")).includes("query="));
    await page.locator("#citation-detail .associations button").filter({hasText:"§ 13"}).click();
    assert.equal(await page.locator("#text-tab").getAttribute("aria-selected"), "true");
    assert.equal(await page.locator(".fragment.selected").count(), 1);
    await page.screenshot({path:path.join(out, "vlb-citation.png"), fullPage:true});

    // Review notes keep source and citation IDs and survive a page reload.
    await page.locator("#notes-tab").click();
    await page.locator("#note-text").fill("Conferir Aimocanãy no fac-símile; anotação de teste.");
    await page.locator('#note-form button[type="submit"]').click();
    assert.equal(await page.locator("#note-list .note-card").count(), 1);
    const downloadPromise = page.waitForEvent("download");
    await page.locator("#export-notes").click();
    const download = await downloadPromise;
    const notesPath = path.join(out, "notes-test.json");
    await download.saveAs(notesPath);
    const exported = JSON.parse(fs.readFileSync(notesPath, "utf8"));
    assert.equal(exported.notes[0].source_id, "vlb-emerson-r568-p00013");
    assert.equal(exported.notes[0].dictionary_entry_index, 7210);
    assert.equal(exported.notes[0].source_text_sha256, exported.current_viewer_provenance.source_text_sha256);
    assert.equal(exported.notes[0].dictionary_snapshot_sha256, exported.current_viewer_provenance.dictionary_snapshot_sha256);
    await page.reload();
    await page.locator("#source-13").waitFor();
    await page.locator("#notes-tab").click();
    assert.equal(await page.locator("#note-list .note-card").count(), 1);

    await open("?volume=I&page=25");
    assert.equal(await page.locator("#text-count").innerText(), "0");
    assert.ok((await page.locator("#page-status").innerText()).includes("prancha"));
    await page.locator("#next-page").click();
    await page.waitForFunction(() => document.getElementById("page-status").textContent.includes("verso em branco"));
    assert.equal(new URL(page.url()).searchParams.get("page"), "26");
    await open("?volume=II&page=7");
    assert.ok((await page.locator("#page-image").getAttribute("src")).endsWith("/161.png"));
    await open("?page=II-078&source=vlb-emerson-r568-p05859");
    assert.ok(await page.locator("#source-5859 .continuation").count());
    assert.ok((await page.locator("#source-5859 .source-text").innerText()).includes("Mũdês grandes"));
    assert.ok(await page.evaluate(() => {
      const selected = document.querySelector(".fragment.selected").getBoundingClientRect();
      const viewport = document.getElementById("text-viewport").getBoundingClientRect();
      return selected.top >= viewport.top - 1 && selected.top < viewport.bottom;
    }), "deep linked source is scrolled into its pane");
    await page.screenshot({path:path.join(out, "vlb-continuation.png"), fullPage:true});
    await page.locator("#search-input").fill("Cetigmã cangupiara");
    await page.locator('#search-form button[type="submit"]').click();
    await page.locator(".search-result").first().waitFor();
    await page.locator(".search-result").first().click();
    await page.waitForFunction(() => document.getElementById("page-status").textContent.includes("página impressa 78"));
    assert.equal(new URL(page.url()).searchParams.get("page"), "78", "search opens the continuation containing its words");
    await open("?volume=II&page=138&source=vlb-emerson-r568-p07401");
    assert.ok(await page.locator("#source-7401 .continuation").count());
    await page.locator("#search-input").fill("Zurrar");
    await page.locator('#search-form button[type="submit"]').click();
    await page.locator(".search-result").first().waitFor();
    await page.locator(".search-result").filter({hasText:"Zurrar"}).first().click();
    await page.waitForFunction(() => document.getElementById("page-status").textContent.includes("página impressa 149"));
    assert.equal(await page.locator("#next-page").isDisabled(), true);

    await open("?volume=I&page=17");
    await page.locator("#about-button").click();
    await page.locator("#unresolved-list p").first().waitFor({state:"attached"});
    assert.equal(await page.locator("#unresolved-list p").count(), 2);
    await page.locator("#close-about").click();
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, "mobile has no horizontal overflow");
    await page.screenshot({path:path.join(out, "vlb-mobile.png"), fullPage:true});

    // The Pages build changes the scan extension. Exercise the format manifest
    // contract while using the same image bytes as a small local fixture.
    await page.route("**/docs/primary_sources/image-formats.json", route => route.fulfill({contentType:"application/json",body:JSON.stringify({books:{vlb:".jpg"}})}));
    await page.route("**/docs/primary_sources/vlb/17.jpg", route => route.fulfill({contentType:"image/png",path:path.join(root,"docs/primary_sources/vlb/17.png")}));
    await open("?volume=I&page=17");
    assert.ok((await page.locator("#page-image").getAttribute("src")).endsWith("/17.jpg"));
    assert.deepEqual(errors, []);
    const result = {desktop:true,mobile:true,source_selection:true,citation_navigation:true,entry_link_does_not_assert_match:true,
      ocr_overlay:true,notes_export_and_persistence:true,nontext_inserts:true,volume_offset:true,split_paragraphs:true,
      search:true,optimized_image_manifest:true,javascript_errors:errors,screenshots:out};
    fs.writeFileSync(path.join(out,"result.json"), JSON.stringify(result,null,2)+"\n");
    console.log(JSON.stringify(result));
  } finally { await context.close(); await browser.close(); server.close(); }
})().catch(error => { console.error(error); server.close(); process.exitCode = 1; });
