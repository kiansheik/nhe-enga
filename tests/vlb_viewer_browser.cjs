#!/usr/bin/env node
// Real-browser checks for the VLB comparison workflow. Install Playwright and its
// Chromium, or set VLB_CHROMIUM_PATH to an existing executable. The sparse
// checkout needs scans 17, 18, 19, 25, 26, 161, 231, 232, 292 and 303 for image
// assertions. Other valid neighbors use an image fixture in continuous-mode
// interaction checks; transcription, citation, and pagination data stay real.
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
  const context = await browser.newContext({viewport:{width:1440,height:1080}, reducedMotion:"reduce", serviceWorkers:"block"});
  const page = await context.newPage();
  page.setDefaultTimeout(20000);
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  async function open(query) {
    const params = new URLSearchParams(query);
    params.set("mode", "page");
    await page.goto(base + "?" + params);
    await page.locator("#transcription-panel:not([aria-busy]) .fragment, #fragment-list .empty-state").first().waitFor({state:"attached"});
    await page.waitForFunction(() => document.getElementById("page-image").naturalWidth > 0);
    assert.equal(await page.locator("#load-error").isVisible(), false);
  }
  async function source(number) {
    await page.locator(`#source-${number} .source-main`).click();
    assert.ok(await page.locator(`#source-${number}`).evaluate(node => node.classList.contains("selected")));
    assert.ok(await page.locator("#ocr-overlay rect").count() > 0, "selected source has OCR highlight");
  }
  const textSection = id => `#fragment-list .continuous-text-page[data-page-id="${id}"]`;
  const scanSection = id => `#scan-stack .continuous-scan-page[data-page-id="${id}"]`;
  async function openContinuous(query) {
    const params = new URLSearchParams(query);
    params.set("mode", "continuous");
    const combined = (params.get("page") || "").match(/^(I|II)-(\d+)$/);
    const id = combined ? `${combined[1]}-${combined[2].padStart(3,"0")}` :
      `${params.get("volume") || "I"}-${String(params.get("page") || "17").padStart(3,"0")}`;
    await page.goto(base + "?" + params);
    await page.locator(textSection(id)).waitFor({state:"attached"});
    await page.locator(`${scanSection(id)} img`).waitFor({state:"attached"});
    await page.waitForFunction(selector => {
      const image = document.querySelector(selector);
      return image && image.complete && image.naturalWidth > 0;
    }, `${scanSection(id)} img`);
    assert.equal(await page.locator("#mode-select").inputValue(), "continuous");
    assert.equal(await page.locator("#load-error").isVisible(), false);
    return id;
  }
  async function scrollToPage(viewportId, selector, pageId) {
    await page.locator(`${selector}[data-page-id="${pageId}"]`).waitFor({state:"attached"});
    await page.locator(viewportId).hover();
    await page.mouse.wheel(0, 1); // Explicit user intent interrupts programmatic scroll locks.
    await page.locator(viewportId).evaluate((viewport, {selector,pageId}) => {
      const target = viewport.querySelector(`${selector}[data-page-id="${pageId}"]`);
      viewport.scrollTop += target.getBoundingClientRect().top - viewport.getBoundingClientRect().top + 100;
    }, {selector,pageId});
    const [volume, number] = pageId.split("-");
    await page.waitForFunction(({volume,number}) => {
      const params = new URLSearchParams(location.search);
      return params.get("volume") === volume && Number(params.get("page")) === Number(number);
    }, {volume,number});
  }
  async function assertPaintedPage(viewportId, pageId) {
    await page.waitForFunction(({viewportId,pageId}) => {
      const viewport = document.querySelector(viewportId);
      const box = viewport.getBoundingClientRect();
      const painted = document.elementFromPoint(box.left + viewport.clientWidth / 2,
        box.top + Math.min(100, viewport.clientHeight * .2));
      return painted?.closest(".continuous-scan-page,.continuous-text-page")?.dataset.pageId === pageId;
    }, {viewportId,pageId});
  }
  try {
    await open("?volume=I&page=17");
    assert.equal(await page.locator("#text-count").innerText(), "29");
    assert.equal(await page.locator('a[href="https://abanheenga.blogspot.com/p/como-aprender-tupi.html"]').count(), 2);
    await page.screenshot({path:path.join(out, "vlb-desktop.png"), fullPage:false});
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
    await page.screenshot({path:path.join(out, "vlb-citation.png"), fullPage:false});

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
    await page.screenshot({path:path.join(out, "vlb-continuation.png"), fullPage:false});
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
    await page.screenshot({path:path.join(out, "vlb-mobile.png"), fullPage:false});

    // Only unhydrated neighboring scans are fixture-backed in sparse checkouts.
    // Invalid image positions still fail, and the selected attestation scans
    // (including the neighboring I18/19 and II77 pages) use their actual bytes.
    const manifest = JSON.parse(fs.readFileSync(path.join(root,"vlb/data/manifest.json"),"utf8"));
    const validScans = new Set(manifest.scan_slots.map(slot => slot.image_index));
    await page.route(/\/docs\/primary_sources\/vlb\/\d+\.png$/, route => {
      const number = Number(new URL(route.request().url()).pathname.match(/\/(\d+)\.png$/)[1]);
      const file = path.join(root,`docs/primary_sources/vlb/${number}.png`);
      if (fs.existsSync(file) || !validScans.has(number)) return route.continue();
      return route.fulfill({contentType:"image/png",path:path.join(root,"docs/primary_sources/vlb/17.png")});
    });
    await page.setViewportSize({width:1440,height:1080});

    // Use the production dictionary link, including its occurrence offset. The
    // homepage itself has no navigation link to the VLB reader.
    await page.goto(base.replace(/vlb\/$/,"") + "?query=" + encodeURIComponent("mokanãî"));
    const inline = page.locator('#results a[href*="/nhe-enga/vlb/?"]').first();
    await inline.waitFor();
    assert.equal(await page.locator('a[href="/nhe-enga/vlb/"]').count(), 0, "VLB has no homepage navigation link");
    const inlineURL = new URL(await inline.getAttribute("href"), base);
    assert.equal(inlineURL.searchParams.get("mode"), "continuous");
    assert.equal(inlineURL.searchParams.get("focus"), "auto");
    assert.equal(inlineURL.searchParams.get("entry"), "7210");
    assert.equal(inlineURL.searchParams.get("citation_pos"), "86");
    await openContinuous(inlineURL.search);
    const selectedReviewed = page.locator(`${textSection("I-017")} .fragment.selected`);
    await selectedReviewed.waitFor();
    assert.equal(await selectedReviewed.getAttribute("data-source-id"), "vlb-emerson-r568-p00013");
    assert.ok((await page.locator("#citation-detail").innerText()).includes("Aimocanãy"));
    const reviewedRects = page.locator(`${scanSection("I-017")} svg rect`);
    assert.equal(await reviewedRects.count(), 1, "direct citation focuses its form-bearing OCR run");
    assert.ok(Math.abs(Number(await reviewedRects.first().getAttribute("x")) - 379.01) < .05,
      "highlight belongs to Aimocanãy's OCR run, not the neighboring Portuguese head");
    assert.ok(await selectedReviewed.evaluate(node => {
      const viewport = document.getElementById("text-viewport").getBoundingClientRect();
      const heading = node.closest(".continuous-text-page").querySelector(".continuous-page-heading");
      const box = node.querySelector(".source-main").getBoundingClientRect();
      return box.top >= viewport.top + heading.getBoundingClientRect().height && box.top < viewport.bottom;
    }), "inline citation's source begins below the sticky page heading after cold load");
    assert.ok(await reviewedRects.first().evaluate(node => {
      const viewport = document.getElementById("scan-viewport").getBoundingClientRect();
      const box = node.getBoundingClientRect();
      return box.top >= viewport.top && box.bottom <= viewport.bottom;
    }), "focused OCR line is actually visible in the scan viewport");
    await assertPaintedPage("#scan-viewport","I-017");
    // Chrome's full-page capture resizes dynamic viewport units and can alter
    // scrollports. Capture the actual viewport that was checked instead.
    const captureURL = page.url();
    await page.screenshot({path:path.join(out,"vlb-continuous-citation.png"),fullPage:false});
    assert.equal(page.url(),captureURL);
    await page.locator("#next-page").click();
    await page.waitForFunction(() => new URLSearchParams(location.search).get("page") === "18");
    assert.equal(await page.locator(".continuous-text-page .fragment.selected").count(), 0,
      "explicit next-page navigation clears the earlier source selection");
    assert.equal(await page.locator(`${scanSection("I-017")} svg rect`).count(), 0,
      "explicit next-page navigation clears the earlier OCR highlight");

    // A strong proposal may be useful for navigation, but remains a proposal.
    await openContinuous("?volume=I&page=17&entry=2480&citation_pos=84&focus=auto");
    const selectedProposed = page.locator(`${textSection("I-017")} .fragment.selected`);
    await selectedProposed.waitFor();
    assert.equal(await selectedProposed.getAttribute("data-source-id"), "vlb-emerson-r568-p00025");
    assert.ok((await page.locator("#citation-detail").innerText()).includes("proposta"));
    assert.ok(await page.locator(`${scanSection("I-017")} svg rect`).count() > 0);
    await openContinuous("?volume=I&page=17&entry=3255&citation_pos=612&focus=auto");
    assert.equal(await page.locator(".continuous-text-page .fragment.selected").count(), 0,
      "tied weak associations do not invent an exact destination");
    assert.equal(await page.locator(".continuous-scan-page svg rect").count(), 0);
    assert.ok((await page.locator("#citation-detail").innerText()).includes("§ 28"));
    assert.ok((await page.locator("#citation-detail").innerText()).includes("§ 30"));

    // This definition has two original II64 occurrences but three formatted
    // copies. The linker deliberately omits an occurrence offset rather than
    // guessing which one the reader meant.
    await page.goto(base.replace(/vlb\/$/,"") + "?query=" + encodeURIComponent("aîa"));
    const ambiguousInline = page.locator('#results a[href*="/nhe-enga/vlb/?"][href*="entry=2502"][href*="page=64"]').first();
    await ambiguousInline.waitFor();
    const ambiguousURL = new URL(await ambiguousInline.getAttribute("href"), base);
    assert.equal(ambiguousURL.searchParams.has("citation_pos"), false);
    await openContinuous(ambiguousURL.search);
    assert.equal(await page.locator("#citation-choice-notice").isVisible(), true,
      "duplicate citation occurrences require an explicit choice");
    assert.equal(await page.locator(".continuous-text-page .fragment.selected").count(), 0);
    assert.equal(await page.locator(".continuous-scan-page svg rect").count(), 0);

    // Scrolling, rather than clicking a page button, loads the next page and
    // updates the active URL without adding one history entry per scroll.
    await openContinuous("?volume=I&page=17");
    const initialLast = await page.locator(".continuous-text-page").last().getAttribute("data-page-id");
    const historyBeforeScroll = await page.evaluate(() => history.length);
    await page.locator("#text-viewport").hover();
    await page.mouse.wheel(0, 1);
    await page.locator("#text-viewport").evaluate(viewport => { viewport.scrollTop = viewport.scrollHeight; });
    await page.waitForFunction(last => {
      const sections = document.querySelectorAll(".continuous-text-page");
      return sections.length && sections[sections.length - 1].dataset.pageId !== last;
    }, initialLast);
    await scrollToPage("#scan-viewport", ".continuous-scan-page", "I-018");
    await assertPaintedPage("#scan-viewport","I-018");
    await assertPaintedPage("#text-viewport","I-018");
    assert.equal(await page.evaluate(() => history.length), historyBeforeScroll);
    assert.equal(await page.locator("#page-select").inputValue(), "I-018");
    assert.ok(await page.locator(textSection("I-018")).evaluate(node => {
      const viewport = document.getElementById("text-viewport").getBoundingClientRect();
      const box = node.getBoundingClientRect();
      return box.bottom > viewport.top && box.top < viewport.bottom;
    }), "scan scrolling brings the matching transcription page into view");
    await scrollToPage("#text-viewport", ".continuous-text-page", "I-019");
    await assertPaintedPage("#scan-viewport","I-019");
    await assertPaintedPage("#text-viewport","I-019");
    assert.ok(await page.locator(scanSection("I-019")).evaluate(node => {
      const viewport = document.getElementById("scan-viewport").getBoundingClientRect();
      const box = node.getBoundingClientRect();
      return box.bottom > viewport.top && box.top < viewport.bottom;
    }), "transcription scrolling brings the matching scan page into view");
    await page.screenshot({path:path.join(out,"vlb-continuous-pages.png"),fullPage:false});
    await assertPaintedPage("#scan-viewport","I-019");
    assert.equal(new URL(page.url()).searchParams.get("page"),"19");

    // These are neighboring reading pages despite a seven-image PDF gap for
    // the second volume's front matter. Both near images must stay available.
    await openContinuous("?volume=II&page=7");
    await page.locator(`${scanSection("I-154")} img[src$="/154.png"]`).waitFor({state:"attached"});
    assert.ok((await page.locator(`${scanSection("II-007")} img`).getAttribute("src")).endsWith("/161.png"));
    await scrollToPage("#scan-viewport", ".continuous-scan-page", "I-154");
    await assertPaintedPage("#scan-viewport","I-154");
    assert.ok((await page.locator(`${scanSection("II-007")} img`).getAttribute("src")).endsWith("/161.png"),
      "volume boundary keeps adjacent logical-page images loaded");

    // Prepending an earlier page preserves the old visible page's position.
    // The same source paragraph appears on II77 and II78; page-scoped DOM IDs
    // and selection prevent its first fragment from stealing the continuation.
    await openContinuous("?volume=II&page=78&source=vlb-emerson-r568-p05859");
    await page.locator(textSection("II-077")).waitFor({state:"attached"});
    const initialFirst = await page.locator(".continuous-text-page").first().getAttribute("data-page-id");
    await page.locator("#text-viewport").hover();
    await page.mouse.wheel(0, -1);
    const anchor = await page.locator("#text-viewport").evaluate(viewport => {
      const first = viewport.querySelector(".continuous-text-page");
      viewport.scrollTop += first.getBoundingClientRect().top - viewport.getBoundingClientRect().top + 30;
      return {id:first.dataset.pageId,top:first.getBoundingClientRect().top - viewport.getBoundingClientRect().top};
    });
    await page.waitForFunction(first => document.querySelector(".continuous-text-page")?.dataset.pageId !== first, initialFirst);
    const anchorAfter = await page.locator(textSection(anchor.id)).evaluate(node =>
      node.getBoundingClientRect().top - document.getElementById("text-viewport").getBoundingClientRect().top);
    assert.ok(Math.abs(anchorAfter - anchor.top) < 8, "prepending preserves the visible text anchor");
    const continuation = page.locator(`${textSection("II-078")} [data-source-id="vlb-emerson-r568-p05859"]`);
    await continuation.locator(".source-main").click();
    assert.ok((await continuation.locator(".source-text").innerText()).includes("Mũdês grandes"));
    assert.equal(new URL(page.url()).searchParams.get("page"), "78");
    assert.ok(await page.locator(`${scanSection("II-078")} svg rect`).count() > 0);
    assert.equal(await page.locator(`${scanSection("II-077")} svg rect`).count(), 0);
    assert.deepEqual(await page.evaluate(() => {
      const seen = new Set(), duplicates = [];
      for (const node of document.querySelectorAll("[id]")) {
        if (seen.has(node.id)) duplicates.push(node.id);
        seen.add(node.id);
      }
      return duplicates;
    }), [], "split paragraphs have unique page-scoped DOM IDs");
    await page.locator("#mode-select").selectOption("page");
    await page.locator("#source-5859.selected").waitFor();
    assert.equal(new URL(page.url()).searchParams.get("page"), "78");
    assert.equal(await page.locator("#mode-select").inputValue(), "page");
    await page.locator("#mode-select").selectOption("continuous");
    await page.locator(`${textSection("II-078")} .fragment.selected`).waitFor();
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true,
      "continuous mode has no mobile horizontal overflow");
    await page.locator(".scan-pane").scrollIntoViewIfNeeded();
    await assertPaintedPage("#scan-viewport","II-078");
    await page.screenshot({path:path.join(out,"vlb-continuous-mobile.png"),fullPage:false});
    await page.locator("#transcription-panel").scrollIntoViewIfNeeded();
    await assertPaintedPage("#text-viewport","II-078");
    await page.screenshot({path:path.join(out,"vlb-continuous-mobile-text.png"),fullPage:false});

    // The Pages build changes the scan extension. Exercise the format manifest
    // contract while using the same image bytes as a small local fixture.
    await page.route("**/docs/primary_sources/image-formats.json", route => route.fulfill({contentType:"application/json",body:JSON.stringify({books:{vlb:".jpg"}})}));
    await page.route("**/docs/primary_sources/vlb/17.jpg", route => route.fulfill({contentType:"image/png",path:path.join(root,"docs/primary_sources/vlb/17.png")}));
    await open("?volume=I&page=17");
    assert.ok((await page.locator("#page-image").getAttribute("src")).endsWith("/17.jpg"));
    assert.deepEqual(errors, []);
    const result = {desktop:true,mobile:true,source_selection:true,citation_navigation:true,legacy_entry_link_stays_manual:true,
      ocr_overlay:true,notes_export_and_persistence:true,nontext_inserts:true,volume_offset:true,split_paragraphs:true,
      search:true,optimized_image_manifest:true,continuous_scroll:true,continuous_prepend_preserves_anchor:true,
      continuous_scroll_sync:true,continuous_mode_toggle:true,inline_citation_occurrence:true,reviewed_form_line_jump:true,
      proposed_jump_stays_proposed:true,ambiguous_jump_fallback:true,ambiguous_occurrence_choice:true,no_homepage_vlb_navigation:true,
      explicit_navigation_clears_selection:true,logical_volume_neighbors:true,source_below_sticky_heading:true,
      javascript_errors:errors,screenshots:out};
    fs.writeFileSync(path.join(out,"result.json"), JSON.stringify(result,null,2)+"\n");
    console.log(JSON.stringify(result));
  } catch (error) {
    await page.screenshot({path:path.join(out,"vlb-failure.png"),fullPage:false}).catch(() => {});
    console.error(`VLB browser check failed at ${page.url()}`);
    throw error;
  } finally { await context.close(); await browser.close(); server.close(); }
})().catch(error => { console.error(error); server.close(); process.exitCode = 1; });
