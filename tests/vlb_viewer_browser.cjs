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
const childProcess = require("node:child_process");
const {chromium} = require(process.env.VLB_PLAYWRIGHT_MODULE || "playwright");
const root = path.resolve(__dirname, "..");
const out = process.env.VLB_QA_DIR || fs.mkdtempSync(path.join(os.tmpdir(), "vlb-browser-"));
fs.mkdirSync(out, {recursive: true});
const mime = {".html":"text/html; charset=utf-8", ".js":"application/javascript; charset=utf-8", ".css":"text/css; charset=utf-8", ".json":"application/json", ".gz":"application/gzip", ".png":"image/png", ".jpg":"image/jpeg", ".ico":"image/x-icon"};
const correctionEventIdPattern = /vlb-correction-[0-9a-f]{20}-r[0-9]{4}/;
const viewerPreferenceKey = "nhe-enga-vlb-viewer-v1";
function assertCorrectionChain(event) {
  const match = event.event_id.match(/^(vlb-correction-[0-9a-f]{20})-r([0-9]{4})$/);
  assert.ok(match,"saved correction has a canonical event ID");
  assert.equal(event.correction_id,match[1]);
  assert.equal(event.revision,Number(match[2]));
  assert.equal(event.supersedes_event_id,event.revision === 1 ? null :
    `${event.correction_id}-r${String(event.revision - 1).padStart(4,"0")}`);
}
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
  let citationIndexRequests = 0;
  page.on("pageerror", error => errors.push(error.message));
  await page.route("**/citation-index.json.gz", route => {
    citationIndexRequests++;
    return route.abort();
  });
  async function clearViewPreferences() {
    await page.evaluate(key => localStorage.removeItem(key), viewerPreferenceKey);
  }
  async function open(query) {
    const params = new URLSearchParams(query);
    params.set("mode", "page");
    await page.goto(base + "?" + params);
    await page.locator("#transcription-panel:not([aria-busy]) .fragment, #fragment-list .empty-state").first().waitFor({state:"attached"});
    await page.waitForFunction(() => {
      const scan = document.getElementById("scan-panel");
      return getComputedStyle(scan).display === "none" || document.getElementById("page-image").naturalWidth > 0;
    });
    assert.equal(await page.locator("#load-error").isVisible(), false);
  }
  async function source(number) {
    const button = page.locator(`#source-${number} .source-main`);
    await button.scrollIntoViewIfNeeded();
    const before = await page.locator("#text-viewport").evaluate(viewport => viewport.scrollTop);
    const tab = await page.locator('[role="tab"][aria-selected="true"]').getAttribute("id");
    await button.click();
    assert.ok(await page.locator(`#source-${number}`).evaluate(node => node.classList.contains("selected")));
    assert.ok(await page.locator("#ocr-overlay rect").count() > 0, "selected source has OCR highlight");
    assert.equal(await page.locator("#citation-detail").isHidden(), true,
      "a transcript line does not open Navarro detail");
    assert.equal(await page.locator('[role="tab"][aria-selected="true"]').getAttribute("id"), tab,
      "a transcript line does not switch tabs");
    assert.ok(Math.abs(await page.locator("#text-viewport").evaluate(viewport => viewport.scrollTop) - before) < 2,
      "a transcript line does not reposition its own viewport");
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
  async function openSelectedNavarroDetail(scope = "") {
    const selected = page.locator(`${scope} .fragment.selected`).first();
    await selected.locator(".fragment-actions button").filter({hasText:"Ver no Navarro"}).click();
    assert.equal(await page.locator("#citations-tab").getAttribute("aria-selected"), "true",
      "the dedicated line action opens contextual Navarro results");
    assert.equal(await page.locator("#citation-detail").isHidden(), true,
      "opening contextual Navarro results does not open an entry detail");
    const card = page.locator("#citation-list .citation-card.selected").first();
    const target = await card.count() ? card : page.locator("#citation-list .citation-card").first();
    await target.locator(".citation-title button").click();
    await page.locator("#citation-detail").waitFor({state:"visible"});
  }
  async function openCurrentNavarroDetail() {
    await page.locator("#citations-tab").click();
    assert.equal(await page.locator("#citation-detail").isHidden(), true,
      "opening the Navarro tab alone does not open an entry detail");
    const card = page.locator("#citation-list .citation-card.selected").first();
    const target = await card.count() ? card : page.locator("#citation-list .citation-card").first();
    await target.locator(".citation-title button").click();
    await page.locator("#citation-detail").waitFor({state:"visible"});
  }
  async function settlePaint() {
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    await page.waitForTimeout(50);
  }
  async function assertMobileUnifiedReader(label, {
    expanded = true, facsimileExpanded = true, searchOpen = false, defaultShare = true,
  } = {}) {
    assert.equal(await page.locator("#scan-panel").isVisible(), true, `${label}: facsimile remains visible`);
    assert.equal(await page.locator("#transcription-panel").isVisible(), true, `${label}: transcription tray remains visible`);
    assert.equal(await page.locator("#toggle-search").isVisible(), true, `${label}: compact search control remains reachable`);
    assert.equal(await page.locator("#toggle-search").getAttribute("aria-controls"), "search-form");
    assert.equal(await page.locator("#toggle-search").getAttribute("aria-expanded"), String(searchOpen));
    assert.equal(await page.locator("#search-form").isVisible(), searchOpen,
      `${label}: search form matches its compact disclosure state`);
    assert.equal(await page.locator("#search-form").evaluate(form => form.inert), !searchOpen,
      `${label}: a collapsed search form is inert`);
    assert.equal(await page.locator("#surface-switch").isVisible(), false, `${label}: obsolete surface switch stays hidden`);
    assert.equal(await page.locator("#toggle-transcription").getAttribute("aria-expanded"), String(expanded));
    assert.equal(await page.locator("#toggle-transcription").getAttribute("aria-controls"), "transcription-body");
    assert.equal(await page.locator("#transcription-body").isVisible(), expanded,
      `${label}: transcription body matches its disclosure state`);
    assert.equal(await page.locator("#transcription-body").evaluate(body => body.inert), !expanded);
    assert.equal(await page.locator("#toggle-facsimile").getAttribute("aria-expanded"), String(facsimileExpanded));
    assert.equal(await page.locator("#toggle-facsimile").getAttribute("aria-controls"), "scan-body");
    assert.equal(await page.locator("#scan-body").isVisible(), facsimileExpanded,
      `${label}: facsimile body matches its disclosure state`);
    assert.equal(await page.locator("#scan-body").evaluate(body => body.inert), !facsimileExpanded);
    const geometry = await page.evaluate(() => {
      const rect = id => document.getElementById(id).getBoundingClientRect();
      const navigation = document.querySelector(".navigation").getBoundingClientRect();
      const search = document.getElementById("search-form").getBoundingClientRect();
      const workspace = document.querySelector(".workspace").getBoundingClientRect();
      const scan = rect("scan-panel");
      const text = rect("transcription-panel");
      const source = document.querySelector("#transcription-body .fragment:not(.heading) .source-text");
      const sourceStyle = source && getComputedStyle(source);
      const fontSize = sourceStyle ? parseFloat(sourceStyle.fontSize) : null;
      const lineHeight = sourceStyle ? parseFloat(sourceStyle.lineHeight) : null;
      return {overflow:document.documentElement.scrollWidth > innerWidth, viewportWidth:innerWidth,
        viewportHeight:innerHeight, navigationTop:navigation.top, navigationBottom:navigation.bottom,
        searchTop:search.top, searchBottom:search.bottom, workspaceTop:workspace.top,
        workspaceBottom:workspace.bottom, workspaceHeight:workspace.height,
        scanLeft:scan.left, scanRight:scan.right, scanTop:scan.top,
        scanBottom:scan.bottom, scanHeight:scan.height, textLeft:text.left, textRight:text.right,
        textTop:text.top, textBottom:text.bottom, textHeight:text.height, fontSize, lineHeight};
    });
    assert.equal(geometry.overflow, false, `${label}: no horizontal overflow`);
    assert.ok(geometry.navigationTop >= -1, `${label}: compact navigation stays within the viewport`);
    assert.ok(geometry.navigationBottom <= geometry.workspaceTop + 1,
      `${label}: compact navigation stays above the reader`);
    if (searchOpen) {
      assert.ok(geometry.searchTop >= geometry.navigationTop - 1, `${label}: open search stays in navigation`);
      assert.ok(geometry.searchBottom <= geometry.workspaceTop + 1, `${label}: open search stays above the reader`);
    }
    assert.ok(geometry.scanLeft >= -1 && geometry.scanRight <= geometry.viewportWidth + 1,
      `${label}: facsimile stays within the viewport`);
    assert.ok(geometry.textLeft >= -1 && geometry.textRight <= geometry.viewportWidth + 1,
      `${label}: transcription stays within the viewport`);
    assert.ok(geometry.scanTop >= geometry.workspaceTop - 1 && geometry.scanBottom <= geometry.textTop + 11,
      `${label}: facsimile is the upper reading surface`);
    assert.ok(geometry.textBottom <= geometry.workspaceBottom + 1 && geometry.workspaceBottom <= geometry.viewportHeight + 1,
      `${label}: transcription tray remains at the bottom of the screen`);
    if (expanded && facsimileExpanded) {
      if (defaultShare) assert.ok(geometry.textHeight >= geometry.workspaceHeight * .27 && geometry.textHeight <= geometry.workspaceHeight * .36,
        `${label}: transcription occupies about the lower third`);
      assert.ok(geometry.scanHeight > geometry.textHeight, `${label}: facsimile remains the primary view`);
      assert.ok(geometry.fontSize >= 14 && geometry.fontSize <= 16,
        `${label}: transcription uses compact readable type`);
      assert.ok(geometry.lineHeight / geometry.fontSize <= 1.55,
        `${label}: transcription line spacing remains compact`);
    } else if (!expanded) {
      assert.ok(geometry.textHeight >= 35 && geometry.textHeight <= 55,
        `${label}: minimized tray leaves a reachable handle`);
    } else {
      assert.ok(geometry.scanHeight >= 35 && geometry.scanHeight <= 55,
        `${label}: minimized facsimile leaves a reachable handle`);
    }
    return geometry;
  }
  async function savedCorrectionFromFeedback() {
    await page.waitForFunction(() =>
      /vlb-correction-[0-9a-f]{20}-r[0-9]{4}/.test(document.getElementById("correction-feedback").textContent));
    const feedback = await page.locator("#correction-feedback").innerText();
    const match = feedback.match(correctionEventIdPattern);
    assert.ok(match,"save feedback identifies the durable event shape");
    const event = await page.evaluate(eventId => {
      const rows = JSON.parse(localStorage.getItem("nhe-enga-vlb-corrections-v1") || "[]");
      return rows.find(row => row.event_id === eventId) || null;
    },match[0]);
    assert.ok(event,"save feedback identifies the event persisted in local storage");
    assertCorrectionChain(event);
    return event;
  }
  try {
    // Keep responsive-view preferences deterministic while still exercising
    // persistence explicitly in the scenarios below.
    await page.goto(base);
    await clearViewPreferences();
    await open("?volume=I&page=17");
    assert.equal(await page.locator("#search-form").isVisible(), true,
      "desktop keeps source-text search available without consuming a toggle row");
    assert.equal(await page.locator("#search-form").evaluate(form => form.inert), false);
    assert.equal(await page.locator("#toggle-search").isVisible(), false,
      "desktop does not need the mobile search disclosure");
    assert.equal(await page.locator("#text-count").innerText(), "29");
    assert.equal(await page.locator("#citation-count").innerText(), "0",
      "Navarro stays empty until a transcript line supplies context");
    await page.locator("#citations-tab").click();
    assert.ok((await page.locator("#citation-list .empty-state").innerText()).includes("Selecione um trecho"));
    assert.equal(await page.locator("#citation-detail").isHidden(), true);
    await page.locator("#text-tab").click();
    assert.equal(await page.locator('a[href="https://abanheenga.blogspot.com/p/como-aprender-tupi.html"]').count(), 2);
    await page.screenshot({path:path.join(out, "vlb-desktop.png"), fullPage:false});
    await source(13);
    assert.ok(page.url().includes("source=vlb-emerson-r568-p00013"));
    assert.ok(Number(await page.locator("#citation-count").innerText()) > 0,
      "selecting a line prepares only its contextual Navarro results");
    assert.equal(await page.locator(".source-meta").count(), 0,
      "Navarro headwords are not injected into the transcript rows");
    assert.equal(await page.locator(".ocr-reading").count(), 0,
      "OCR reading dropdowns are absent from transcript lines");
    assert.equal(await page.getByRole("button", {name:/Citar verbete/i}).count(), 0,
      "a selected line exposes one share action rather than a second citation action");
    const centered = await page.evaluate(() => {
      const viewport = document.getElementById("scan-viewport").getBoundingClientRect();
      const highlight = document.querySelector("#ocr-overlay rect").getBoundingClientRect();
      return {deltaX:Math.abs((highlight.left + highlight.right) / 2 - (viewport.left + viewport.right) / 2),
        deltaY:Math.abs((highlight.top + highlight.bottom) / 2 - (viewport.top + viewport.bottom) / 2),
        width:viewport.width,height:viewport.height};
    });
    assert.ok(centered.deltaY <= centered.height * .12,
      "transcript selection vertically centers the OCR highlight in the facsimile viewer");

    // The facsimile is bidirectional: tapping an aligned line reveals and
    // centers its transcript row, without opening Navarro detail.
    await page.locator("#text-viewport").evaluate(viewport => { viewport.scrollTop = viewport.scrollHeight; });
    const scanLine = await page.locator("#ocr-overlay rect").first().boundingBox();
    assert.ok(scanLine, "selected OCR line has a clickable on-screen box");
    await page.mouse.click(scanLine.x + scanLine.width / 2, scanLine.y + scanLine.height / 2);
    assert.equal(await page.locator("#source-13").evaluate(node => node.classList.contains("selected")), true);
    assert.equal(await page.locator("#citation-detail").isHidden(), true);
    assert.ok(await page.locator("#source-13").evaluate(node => {
      const viewport = document.getElementById("text-viewport").getBoundingClientRect();
      const box = node.getBoundingClientRect();
      return box.top >= viewport.top && box.bottom <= viewport.bottom;
    }), "facsimile line tap centers its transcript row");

    // The single share action hands the complete line, citation, and compact
    // deep link to Web Share, then falls back to copy or manual copy.
    await page.evaluate(() => {
      Object.defineProperty(navigator, "clipboard", {configurable:true, value:{
        writeText: async value => { window.__vlbCopiedCitation = value; }
      }});
      Object.defineProperty(navigator, "share", {configurable:true, value:async value => {
        window.__vlbSharedCitation = value;
      }});
    });
    await page.locator("#source-13 .fragment-actions button").filter({hasText:"Compartilhar"}).click();
    await page.waitForFunction(() => Boolean(window.__vlbSharedCitation));
    const sharedCitation = await page.evaluate(() => window.__vlbSharedCitation);
    const compactSourceURL = new URL(sharedCitation.url);
    const copiedCitation = `${sharedCitation.text}\n${sharedCitation.url}`;
    assert.equal(sharedCitation.text.split("\n")[0], await page.locator("#source-13 .source-text").innerText());
    assert.ok(copiedCitation.includes("\n\nVocabulário na Língua Brasílica (VLB), v. I, p. 17, § 13.\n"));
    assert.equal(compactSourceURL.searchParams.get("page"), "I-017");
    assert.equal(compactSourceURL.searchParams.get("line"), "13");
    assert.equal(compactSourceURL.searchParams.has("source"), false,
      "shared line link uses the compact page-plus-line route");
    assert.equal(sharedCitation.url, compactSourceURL.href);
    assert.ok(sharedCitation.text.includes("VLB), v. I, p. 17, § 13."));
    assert.equal(sharedCitation.title, "VLB I, p. 17, § 13");
    await page.evaluate(() => {
      Object.defineProperty(navigator, "share", {configurable:true, value:undefined});
      window.__vlbCopiedCitation = null;
    });
    await page.locator("#source-13 .fragment-actions button").filter({hasText:"Compartilhar"}).click();
    await page.waitForFunction(() => Boolean(window.__vlbCopiedCitation));
    assert.equal(await page.evaluate(() => window.__vlbCopiedCitation), copiedCitation,
      "share falls back to the complete clipboard block when Web Share is unavailable");
    await page.evaluate(() => {
      Object.defineProperty(navigator, "clipboard", {configurable:true, value:{
        writeText: async () => { throw new DOMException("denied", "NotAllowedError"); }
      }});
      window.__vlbManualCitation = null;
      window.prompt = (label, value) => { window.__vlbManualCitation = {label, value}; return null; };
    });
    await page.locator("#source-13 .fragment-actions button").filter({hasText:"Compartilhar"}).click();
    await page.waitForFunction(() => Boolean(window.__vlbManualCitation));
    const manualCitation = await page.evaluate(() => window.__vlbManualCitation);
    assert.ok(manualCitation.label.includes("Copie a citação"));
    assert.equal(manualCitation.value, copiedCitation,
      "clipboard denial exposes the complete citation block for manual copy");
    await page.goto(compactSourceURL.href);
    await page.locator("#source-13.selected").waitFor();
    await page.waitForFunction(() => {
      const image = document.getElementById("page-image");
      return image.complete && image.naturalWidth > 0;
    });
    assert.equal(await page.locator("#citation-detail").isHidden(), true);
    assert.ok(await page.locator("#ocr-overlay rect").count() > 0,
      "compact citation link restores the selected facsimile line");
    assert.ok(await page.locator("#ocr-overlay rect").first().evaluate(node => {
      const viewport = document.getElementById("scan-viewport").getBoundingClientRect();
      const box = node.getBoundingClientRect();
      return Math.abs((box.top + box.bottom) / 2 - (viewport.top + viewport.bottom) / 2) <= viewport.height * .12;
    }), "compact citation link centers the selected facsimile line");
    assert.ok(await page.locator("#source-13").evaluate(node => {
      const viewport = document.getElementById("text-viewport").getBoundingClientRect();
      const box = node.getBoundingClientRect();
      return box.top >= viewport.top && box.bottom <= viewport.bottom;
    }), "compact citation link centers the selected transcript line");
    await page.locator("#zoom-in").click();
    assert.equal(await page.locator("#zoom-reset").innerText(), "125%");
    assert.equal(await page.evaluate(key => JSON.parse(localStorage.getItem(key)).zoom, viewerPreferenceKey), 125,
      "zoom is saved as a viewing preference");
    await page.locator("#show-ocr").uncheck();
    assert.equal(await page.locator("#ocr-overlay rect").count(), 0);
    await page.locator("#show-ocr").check();
    await open("?volume=I&page=18");
    assert.equal(await page.locator("#zoom-reset").innerText(), "125%",
      "zoom survives page navigation");
    await page.reload();
    await page.locator("#fragment-list .fragment").first().waitFor({state:"attached"});
    await page.waitForFunction(() => document.getElementById("page-image").naturalWidth > 0);
    assert.equal(await page.locator("#zoom-reset").innerText(), "125%",
      "zoom survives a reader reload");
    await page.locator("#zoom-reset").click();

    // An entry deep link identifies its citation, without accepting a proposed
    // source association or opening its detail. The user explicitly opens the
    // contextual Navarro entry and then chooses the source paragraph.
    await open("?volume=I&page=17&entry=7210");
    assert.equal(await page.locator("#text-tab").getAttribute("aria-selected"), "true");
    assert.equal(await page.locator(".fragment.selected").count(), 0);
    assert.equal(await page.locator("#citation-detail").isHidden(), true);
    await openCurrentNavarroDetail();
    assert.ok((await page.locator("#citation-detail h3").innerText()).includes("mokanãî"));
    assert.ok((await page.locator("#citation-detail h3 a").getAttribute("href")).includes("query="));
    await page.locator("#citation-detail .associations button").filter({hasText:"§ 13"}).click();
    assert.equal(await page.locator("#text-tab").getAttribute("aria-selected"), "true");
    assert.equal(await page.locator(".fragment.selected").count(), 1);
    assert.equal(await page.locator("#source-13 mark.match-span").innerText(), "Aimocanãy");
    await page.locator("#citation-detail .detail-actions button").filter({hasText:"Corrigir"}).click();
    await page.locator("#correction-panel").waitFor({state:"visible"});
    assert.equal(await page.evaluate(() => document.activeElement?.id), "correction-heading",
      "opening a correction moves keyboard focus into the editor");
    await page.locator("#source-13 .source-main").click();
    assert.equal(await page.locator("#correction-panel").isVisible(), true,
      "a transcript line click leaves the active correction open");
    assert.equal(await page.locator("#citation-detail").isHidden(), true,
      "a transcript line click cannot reopen Navarro detail over a correction");
    assert.equal(await page.locator("#correction-spans .correction-span").count(), 1,
      "editing a reviewed match preserves its existing exact span");
    await page.locator("#correction-reviewer").fill("VLB browser regression");
    await page.locator("#correction-notes").fill("Rechecked the exact reviewed form and its pinned OCR line in the browser regression.");
    await page.locator("#save-correction").click();
    const reviewedSavedCorrection = await savedCorrectionFromFeedback();
    assert.ok(reviewedSavedCorrection.revision > 1,
      "editing a checked decision appends a chained revision");
    assert.ok((await page.locator("#correction-feedback").innerText()).includes("somente neste navegador"));
    await page.locator("#close-correction").click();
    assert.equal(await page.locator("#citation-detail").isVisible(), true,
      "closing a correction restores its explicitly opened detail");
    await page.locator("#source-14 .source-main").click();
    assert.equal(await page.locator("#citation-detail").isHidden(), true,
      "selecting an unrelated line closes the stale Navarro detail");
    assert.equal(new URL(page.url()).searchParams.has("citation"), false);
    assert.equal(new URL(page.url()).searchParams.has("entry"), false);
    assert.equal((await page.locator("#note-target").innerText()).includes("mokanãî"), false,
      "line navigation cannot attach the old Navarro entry to a new note");

    // Restore the explicit citation context for the note-persistence check.
    await open("?volume=I&page=17&entry=7210");
    await openCurrentNavarroDetail();
    await page.locator("#citation-detail .associations button").filter({hasText:"§ 13"}).click();
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

    // Search is built only from VLB source paragraphs. Literal whole-word
    // matches precede the same exact spelling embedded in larger words, while
    // the orthography model offers clearly labelled probable historical forms.
    await page.locator("#search-input").fill("biã");
    await page.locator('#search-form button[type="submit"]').click();
    await page.locator(".search-result").first().waitFor();
    const biaResults = page.locator(".search-result");
    assert.equal(await biaResults.count(), 4);
    assert.equal(await biaResults.nth(0).getAttribute("data-source-id"), "vlb-emerson-r568-p04770");
    assert.equal(await biaResults.nth(0).getAttribute("data-match-scope"), "whole");
    assert.equal(await biaResults.nth(0).locator(".result-kind").textContent(), "VLB · forma exata");
    assert.ok((await biaResults.nth(0).innerText()).includes("§ 4770"));
    assert.deepEqual(await biaResults.evaluateAll(results => results.slice(1).map(result => result.dataset.matchScope)),
      ["inside", "inside", "inside"], "inside-word matches follow the exact VLB word");
    assert.deepEqual(await biaResults.evaluateAll(results => results.map(result => result.dataset.sourceId)), [
      "vlb-emerson-r568-p04770", "vlb-emerson-r568-p01039",
      "vlb-emerson-r568-p03134", "vlb-emerson-r568-p05140",
    ]);
    assert.equal(await page.locator("#search-result-list .citation-card").count(), 0,
      "search never renders Navarro dictionary result cards");
    assert.equal((await page.locator("#search-result-list").innerText()).includes("Navarro"), false,
      "a literal VLB query contains no dictionary result");
    await biaResults.first().click();
    await page.locator("#source-4770.selected").waitFor();
    assert.equal(new URL(page.url()).searchParams.get("volume"), "II");
    assert.equal(new URL(page.url()).searchParams.get("page"), "32");

    await page.locator("#search-input").fill("Abortiuo");
    await page.locator('#search-form button[type="submit"]').click();
    await page.locator(".search-result").first().waitFor();
    assert.equal(await page.locator(".search-result").first().locator(".result-kind").textContent(),
      "Português · palavra exata", "Portuguese source-side words are searchable without dictionary results");

    await page.locator("#search-input").fill("akyrara");
    await page.locator('#search-form button[type="submit"]').click();
    await page.locator(".search-result").first().waitFor();
    const probableResult = page.locator(".search-result").first();
    assert.equal(await probableResult.getAttribute("data-query-path"), "orthography-model");
    assert.equal(await probableResult.getAttribute("data-source-id"), "vlb-emerson-r568-p00046");
    assert.equal(await probableResult.locator(".result-kind").textContent(), "Navarro → VLB · grafia provável");
    assert.ok((await probableResult.innerText()).includes("Aquîrara"));
    await probableResult.click();
    await page.locator("#source-46.selected").waitFor();
    assert.equal(new URL(page.url()).searchParams.get("volume"), "I");
    assert.equal(new URL(page.url()).searchParams.get("page"), "18");

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
    assert.equal(citationIndexRequests, 0,
      "source-text search succeeds while the legacy Navarro citation index is blocked");

    await clearViewPreferences();
    await open("?volume=I&page=17");
    await page.locator("#about-button").click();
    await page.locator("#unresolved-list p").first().waitFor({state:"attached"});
    assert.equal(await page.locator("#unresolved-list p").count(), 2);
    await page.locator("#close-about").click();
    await page.setViewportSize({width:390,height:844});
    await page.locator('#toggle-search[aria-expanded="false"]').waitFor();
    const expanded390 = await assertMobileUnifiedReader("390px unified reader");
    const compactNavigationHeight = await page.locator(".navigation").evaluate(node => node.getBoundingClientRect().height);
    assert.ok(compactNavigationHeight <= 44, "collapsed mobile navigation uses one low-profile control row");
    assert.equal(await page.locator("#search-form").getAttribute("aria-hidden"), "true");
    await page.locator("#toggle-search").click();
    await page.waitForFunction(() => document.activeElement?.id === "search-input");
    await assertMobileUnifiedReader("390px open search", {searchOpen:true, defaultShare:false});
    assert.equal(await page.locator("#toggle-search").getAttribute("aria-label"), "Fechar busca na transcrição");
    await page.locator("#search-input").press("Escape");
    await assertMobileUnifiedReader("390px closed search");
    assert.equal(await page.evaluate(() => document.activeElement?.id), "toggle-search",
      "Escape closes mobile search and restores focus to its disclosure");

    const splitter = page.locator("#reader-splitter");
    assert.equal(await splitter.getAttribute("role"), "separator");
    assert.equal(await splitter.getAttribute("aria-orientation"), "horizontal");
    assert.equal(await splitter.getAttribute("aria-valuemin"), "18");
    assert.equal(await splitter.getAttribute("aria-valuemax"), "72");
    assert.equal(await splitter.getAttribute("aria-valuenow"), "31");
    const mobileTextHeightBeforeSplit = (await page.locator("#transcription-panel").boundingBox()).height;
    const mobileSplitterBox = await splitter.boundingBox();
    assert.ok(mobileSplitterBox, "mobile reader splitter is visible");
    await page.mouse.move(mobileSplitterBox.x + mobileSplitterBox.width / 2,
      mobileSplitterBox.y + mobileSplitterBox.height / 2);
    await page.mouse.down();
    await page.mouse.move(mobileSplitterBox.x + mobileSplitterBox.width / 2,
      mobileSplitterBox.y - 55, {steps:5});
    await page.mouse.up();
    await settlePaint();
    const mobileTextHeightAfterSplit = (await page.locator("#transcription-panel").boundingBox()).height;
    assert.ok(mobileTextHeightAfterSplit > mobileTextHeightBeforeSplit + 25,
      "dragging the horizontal splitter gives the mobile transcription more height");
    const mobileSplitPreference = await page.evaluate(key => JSON.parse(localStorage.getItem(key)).mobileTextShare,
      viewerPreferenceKey);
    assert.ok(mobileSplitPreference > 31, "mobile split is persisted in local storage");
    assert.equal(Number(await splitter.getAttribute("aria-valuenow")), Math.round(mobileSplitPreference));
    await page.reload();
    await page.locator("#fragment-list .fragment").first().waitFor({state:"attached"});
    await page.waitForFunction(() => document.getElementById("page-image").naturalWidth > 0);
    const mobileTextHeightAfterReload = (await page.locator("#transcription-panel").boundingBox()).height;
    assert.ok(Math.abs(mobileTextHeightAfterReload - mobileTextHeightAfterSplit) < 4,
      "mobile reader proportions survive reload");
    assert.equal(Number(await splitter.getAttribute("aria-valuenow")), Math.round(mobileSplitPreference));
    await clearViewPreferences();
    await page.reload();
    await page.locator("#fragment-list .fragment").first().waitFor({state:"attached"});
    await page.waitForFunction(() => document.getElementById("page-image").naturalWidth > 0);
    assert.equal(await splitter.getAttribute("aria-valuenow"), "31",
      "a fresh preference state restores the mobile one-third transcription default");

    // A real two-touch event sequence changes zoom without selecting a line.
    assert.equal(await page.locator(".fragment.selected").count(), 0);
    const pinchResult = await page.locator("#scan-viewport").evaluate(viewport => {
      const bounds = viewport.getBoundingClientRect();
      const target = viewport;
      const touch = (identifier, x, y) => new Touch({identifier,target,
        clientX:x,clientY:y,pageX:x,pageY:y,screenX:x,screenY:y,radiusX:1,radiusY:1,force:.5});
      const centerX = bounds.left + bounds.width / 2;
      const centerY = bounds.top + bounds.height / 2;
      const start = [touch(1, centerX - 30, centerY), touch(2, centerX + 30, centerY)];
      const moved = [touch(1, centerX - 75, centerY), touch(2, centerX + 75, centerY)];
      target.dispatchEvent(new TouchEvent("touchstart", {touches:start,targetTouches:start,
        changedTouches:start,bubbles:true,cancelable:true}));
      target.dispatchEvent(new TouchEvent("touchmove", {touches:moved,targetTouches:moved,
        changedTouches:moved,bubbles:true,cancelable:true}));
      target.dispatchEvent(new TouchEvent("touchend", {touches:[],targetTouches:[],
        changedTouches:moved,bubbles:true,cancelable:true}));
      return {zoom:document.getElementById("zoom-reset").textContent,
        selected:document.querySelectorAll(".fragment.selected").length};
    });
    assert.equal(pinchResult.zoom, "250%", "two-touch pinch zooms the facsimile around its midpoint");
    assert.equal(pinchResult.selected, 0, "pinch zoom does not accidentally select a source line");
    assert.equal(await page.evaluate(key => JSON.parse(localStorage.getItem(key)).zoom, viewerPreferenceKey), 250,
      "pinch zoom is persisted when the gesture ends");
    await source(13);
    await settlePaint();
    const pinchCentered = await page.evaluate(() => {
      const viewport = document.getElementById("scan-viewport").getBoundingClientRect();
      const highlights = Array.from(document.querySelectorAll("#ocr-overlay rect"),
        node => node.getBoundingClientRect());
      const union = {left:Math.min(...highlights.map(box => box.left)),
        right:Math.max(...highlights.map(box => box.right)),
        top:Math.min(...highlights.map(box => box.top)),
        bottom:Math.max(...highlights.map(box => box.bottom))};
      return {x:Math.abs((union.left + union.right) / 2 - (viewport.left + viewport.right) / 2),
        y:Math.abs((union.top + union.bottom) / 2 - (viewport.top + viewport.bottom) / 2),
        width:viewport.width,height:viewport.height};
    });
    assert.ok(pinchCentered.x <= pinchCentered.width * .14 && pinchCentered.y <= pinchCentered.height * .14,
      `selecting a line recenters it at the pinched zoom level: ${JSON.stringify(pinchCentered)}`);
    await page.locator("#scan-options summary").click();
    await page.locator("#zoom-reset").click();
    await page.locator("#scan-options summary").click();

    const fullReaderGeometry = await assertMobileUnifiedReader("390px before facsimile minimization");
    await page.locator("#toggle-facsimile").click();
    await page.locator("body.facsimile-minimized").waitFor({state:"attached"});
    const facsimileMinimized = await assertMobileUnifiedReader("390px minimized facsimile",
      {facsimileExpanded:false, defaultShare:false});
    assert.equal(await page.evaluate(key => JSON.parse(localStorage.getItem(key)).facsimileMinimized,
      viewerPreferenceKey), true, "explicit facsimile minimization is remembered");
    assert.ok(facsimileMinimized.textHeight > fullReaderGeometry.textHeight,
      "minimizing the facsimile gives the transcription the study area");
    assert.ok(await page.locator("#ocr-overlay rect").count() > 0,
      "facsimile minimization retains the selected OCR highlight");
    await page.locator("#toggle-transcription").click();
    assert.equal(await page.locator("body.facsimile-minimized.transcription-minimized").count(), 0,
      "the reader never leaves both study panes minimized");
    await assertMobileUnifiedReader("transcription minimization restores facsimile", {expanded:false});
    await page.locator("#toggle-transcription").click();
    await assertMobileUnifiedReader("both study panes restored");
    await page.locator("#toggle-facsimile").click();
    await assertMobileUnifiedReader("facsimile hidden before transcript selection",
      {facsimileExpanded:false, defaultShare:false});
    await source(14);
    await assertMobileUnifiedReader("transcript selection restores facsimile");
    assert.equal(await page.evaluate(key => JSON.parse(localStorage.getItem(key)).facsimileMinimized,
      viewerPreferenceKey), true,
      "selection temporarily restores the facsimile without discarding the reader's saved preference");
    assert.equal(await page.locator("#source-14").evaluate(node => node.classList.contains("selected")), true);
    assert.ok(await page.locator("#ocr-overlay rect").first().evaluate(node => {
      const viewport = document.getElementById("scan-viewport").getBoundingClientRect();
      const box = node.getBoundingClientRect();
      return Math.abs((box.top + box.bottom) / 2 - (viewport.top + viewport.bottom) / 2) <= viewport.height * .14;
    }), "selection after restoring the facsimile is centered");
    await source(13);
    await page.screenshot({path:path.join(out, "vlb-mobile-390-unified.png"), fullPage:false});
    await page.locator("#scan-options summary").click();
    await page.locator("#zoom-in").click();
    await page.locator("#zoom-in").click();
    await page.locator("#zoom-in").click();
    await page.locator("#zoom-in").click();
    const scanPosition = await page.locator("#scan-viewport").evaluate(viewport => {
      viewport.scrollTop = Math.min(180, viewport.scrollHeight - viewport.clientHeight);
      return viewport.scrollTop;
    });
    assert.ok(scanPosition > 0, "zoomed facsimile has a meaningful saved reading position");
    await page.screenshot({path:path.join(out, "vlb-mobile-390-unified-zoomed.png"), fullPage:false});
    const textPosition = await page.locator("#text-viewport").evaluate(viewport => {
      viewport.scrollTop = Math.min(210, viewport.scrollHeight - viewport.clientHeight);
      return viewport.scrollTop;
    });
    assert.ok(textPosition > 0, "transcription has a meaningful saved reading position");
    await page.locator("#toggle-transcription").click();
    await page.locator("body.transcription-minimized").waitFor({state:"attached"});
    const minimized390 = await assertMobileUnifiedReader("390px minimized transcription", {expanded:false});
    assert.ok(minimized390.scanHeight > expanded390.scanHeight,
      "minimizing the transcription gives the facsimile more room");
    assert.ok(Math.abs(await page.locator("#scan-viewport").evaluate(viewport => viewport.scrollTop) - scanPosition) < 3,
      "facsimile reading position survives minimizing the transcription");
    await page.screenshot({path:path.join(out, "vlb-mobile-transcription-minimized.png"), fullPage:false});
    await page.locator("#toggle-transcription").click();
    await assertMobileUnifiedReader("390px restored transcription");
    assert.ok(Math.abs(await page.locator("#text-viewport").evaluate(viewport => viewport.scrollTop) - textPosition) < 3,
      "transcription reading position survives minimizing and restoring the tray");
    assert.ok(Math.abs(await page.locator("#scan-viewport").evaluate(viewport => viewport.scrollTop) - scanPosition) < 3,
      "facsimile reading position survives restoring the transcription tray");

    await source(13);
    await page.locator("#toggle-transcription").click();
    await assertMobileUnifiedReader("mobile facsimile reverse navigation", {expanded:false});
    const mobileScanLine = page.locator("#ocr-overlay rect").first();
    await mobileScanLine.scrollIntoViewIfNeeded();
    const mobileScanBox = await mobileScanLine.boundingBox();
    assert.ok(mobileScanBox);
    await page.mouse.click(mobileScanBox.x + mobileScanBox.width / 2,
      mobileScanBox.y + mobileScanBox.height / 2);
    await assertMobileUnifiedReader("facsimile line restores transcription");
    assert.equal(await page.locator("#source-13").evaluate(node => node.classList.contains("selected")), true);
    assert.equal(await page.locator("#citation-detail").isHidden(), true,
      "facsimile line navigation does not open Navarro detail");
    assert.equal(await page.evaluate(key => JSON.parse(localStorage.getItem(key)).transcriptionMinimized,
      viewerPreferenceKey), true,
      "facsimile navigation temporarily restores transcription without discarding its saved preference");

    await clearViewPreferences();
    await page.setViewportSize({width:360,height:800});
    await page.reload();
    await page.locator('#toggle-transcription[aria-expanded="true"]').waitFor();
    await assertMobileUnifiedReader("360px portrait unified reader");
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    await page.screenshot({path:path.join(out, "vlb-mobile-360-unified.png"), fullPage:false});
    await page.setViewportSize({width:844,height:390});
    await assertMobileUnifiedReader("phone landscape unified reader");
    await settlePaint();
    await page.waitForFunction(() => {
      const node = document.querySelector("#ocr-overlay rect");
      if (!node) return false;
      const viewport = document.getElementById("scan-viewport").getBoundingClientRect();
      const box = node.getBoundingClientRect();
      return box.bottom > viewport.top && box.top < viewport.bottom;
    });
    await page.screenshot({path:path.join(out, "vlb-mobile-landscape-unified.png"), fullPage:false});
    await page.setViewportSize({width:768,height:1024});
    await assertMobileUnifiedReader("portrait tablet unified reader");
    await settlePaint();
    await page.screenshot({path:path.join(out, "vlb-tablet-unified.png"), fullPage:false});
    await page.setViewportSize({width:1440,height:1080});
    await clearViewPreferences();
    await page.reload();
    await page.locator("#fragment-list .fragment").first().waitFor({state:"attached"});
    await page.waitForFunction(() => document.getElementById("page-image").naturalWidth > 0);
    assert.equal(await page.locator("#scan-panel").isVisible(), true, "desktop restores the facsimile pane");
    assert.equal(await page.locator("#transcription-panel").isVisible(), true, "desktop restores the transcription pane");
    assert.equal(await page.locator("#surface-switch").isVisible(), false, "desktop does not expose obsolete pane controls");
    assert.equal(await page.locator("#toggle-transcription").isVisible(), false, "desktop keeps both panes fully open");
    assert.equal(await page.locator("#search-form").isVisible(), true, "desktop restores the full search form");
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, "desktop has no horizontal overflow");

    assert.equal(await splitter.getAttribute("aria-orientation"), "vertical");
    assert.equal(await splitter.getAttribute("aria-valuemin"), "28");
    assert.equal(await splitter.getAttribute("aria-valuenow"), "50");
    const desktopTextWidthBeforeSplit = (await page.locator("#transcription-panel").boundingBox()).width;
    await splitter.focus();
    await splitter.press("ArrowLeft");
    await settlePaint();
    const desktopTextWidthAfterKeyboard = (await page.locator("#transcription-panel").boundingBox()).width;
    assert.ok(desktopTextWidthAfterKeyboard > desktopTextWidthBeforeSplit + 15,
      "separator keyboard controls change desktop column widths");
    const desktopSplitterBox = await splitter.boundingBox();
    assert.ok(desktopSplitterBox, "desktop reader splitter is visible");
    await page.mouse.move(desktopSplitterBox.x + desktopSplitterBox.width / 2,
      desktopSplitterBox.y + desktopSplitterBox.height / 2);
    await page.mouse.down();
    await page.mouse.move(desktopSplitterBox.x - 45,
      desktopSplitterBox.y + desktopSplitterBox.height / 2, {steps:5});
    await page.mouse.up();
    await settlePaint();
    const desktopTextWidthAfterDrag = (await page.locator("#transcription-panel").boundingBox()).width;
    assert.ok(desktopTextWidthAfterDrag > desktopTextWidthAfterKeyboard + 20,
      "dragging the vertical splitter gives the desktop transcription more width");
    const desktopSplitPreference = await page.evaluate(key => JSON.parse(localStorage.getItem(key)).desktopTextShare,
      viewerPreferenceKey);
    assert.ok(desktopSplitPreference > 52, "desktop split is persisted in local storage");
    await page.reload();
    await page.locator("#fragment-list .fragment").first().waitFor({state:"attached"});
    await page.waitForFunction(() => document.getElementById("page-image").naturalWidth > 0);
    const desktopTextWidthAfterReload = (await page.locator("#transcription-panel").boundingBox()).width;
    assert.ok(Math.abs(desktopTextWidthAfterReload - desktopTextWidthAfterDrag) < 4,
      "desktop reader proportions survive reload");
    assert.equal(Number(await splitter.getAttribute("aria-valuenow")), Math.round(desktopSplitPreference));
    await clearViewPreferences();
    await page.reload();
    await page.locator("#fragment-list .fragment").first().waitFor({state:"attached"});
    await page.waitForFunction(() => document.getElementById("page-image").naturalWidth > 0);
    assert.equal(await splitter.getAttribute("aria-valuenow"), "50");

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
    assert.equal(await page.locator("#citation-detail").isHidden(), true,
      "dictionary navigation selects and aligns without opening Navarro detail");
    assert.equal(await selectedReviewed.locator("mark.match-span").innerText(), "Aimocanãy",
      "the reviewed exact source span is visibly marked");
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

    // Automatic shared links retain source= for stable paragraph identity and
    // focus=auto so the exact span/OCR target can be recomputed. Both layers
    // must survive a cold reload and page/continuous mode round trips.
    assert.equal(new URL(page.url()).searchParams.get("source"),"vlb-emerson-r568-p00013");
    assert.equal(new URL(page.url()).searchParams.get("focus"),"auto");
    await page.reload();
    await page.locator(`${textSection("I-017")} .fragment.selected mark.match-span`).waitFor();
    assert.equal(await page.locator("#citation-detail").isHidden(), true,
      "reloading a shared alignment link does not open Navarro detail");
    assert.equal(await page.locator(`${textSection("I-017")} .fragment.selected mark.match-span`).innerText(),"Aimocanãy");
    assert.equal(await page.locator(`${scanSection("I-017")} svg rect`).count(),1);
    await page.locator("#mode-select").selectOption("page");
    await page.locator("#source-13 mark.match-span").waitFor();
    assert.equal(await page.locator("#source-13 mark.match-span").innerText(),"Aimocanãy");
    assert.equal(await page.locator("#ocr-overlay rect").count(),1);
    assert.equal(new URL(page.url()).searchParams.get("focus"),"auto");
    await page.locator("#mode-select").selectOption("continuous");
    await page.locator(`${textSection("I-017")} .fragment.selected mark.match-span`).waitFor();
    assert.equal(await page.locator(`${textSection("I-017")} .fragment.selected mark.match-span`).innerText(),"Aimocanãy");
    assert.equal(await page.locator(`${scanSection("I-017")} svg rect`).count(),1);

    // A dictionary deep link opens a single mobile reader: the facsimile is
    // primary and the selected transcription remains available below it.
    await page.setViewportSize({width:390,height:844});
    await page.goto(base + inlineURL.search);
    const mobileReviewed = page.locator(`${textSection("I-017")} .fragment.selected`);
    await mobileReviewed.waitFor();
    await page.locator('#toggle-transcription[aria-expanded="true"]').waitFor();
    await assertMobileUnifiedReader("mobile dictionary deep link");
    assert.equal(await mobileReviewed.getAttribute("data-source-id"), "vlb-emerson-r568-p00013");
    await page.waitForFunction(selector => {
      const image = document.querySelector(selector);
      return image?.complete && image.naturalWidth > 0;
    }, `${scanSection("I-017")} img`);
    assert.equal(await page.locator(`${scanSection("I-017")} svg rect`).count(), 1,
      "unified deep link immediately exposes the form-level OCR target");
    await assertPaintedPage("#scan-viewport","I-017");
    const mobileTextPosition = await page.locator("#text-viewport").evaluate(viewport => viewport.scrollTop);
    assert.equal(await page.locator("#citation-detail").isHidden(), true);
    await settlePaint();
    await page.screenshot({path:path.join(out,"vlb-mobile-selected-actions.png"),fullPage:false});
    await openSelectedNavarroDetail(textSection("I-017"));
    await page.locator("#citation-detail .detail-actions button").filter({hasText:"Corrigir"}).click();
    await page.locator("body.correction-open").waitFor({state:"attached"});
    const correctionGeometry = await page.evaluate(() => {
      const panel = document.getElementById("correction-panel").getBoundingClientRect();
      const pane = document.getElementById("transcription-panel").getBoundingClientRect();
      const scan = document.getElementById("scan-panel").getBoundingClientRect();
      return {panelTop:panel.top,panelBottom:panel.bottom,paneTop:pane.top,paneBottom:pane.bottom,
        panelHeight:panel.height,paneHeight:pane.height,scanHeight:scan.height,overflow:document.documentElement.scrollWidth > innerWidth};
    });
    assert.equal(correctionGeometry.overflow,false,"mobile correction editor does not create horizontal overflow");
    assert.ok(correctionGeometry.panelTop >= correctionGeometry.paneTop && correctionGeometry.panelBottom <= correctionGeometry.paneBottom,
      "mobile correction editor stays inside the transcription tray");
    assert.ok(correctionGeometry.scanHeight >= 135,"mobile correction editor keeps a substantial facsimile visible");
    await page.locator("#save-correction").scrollIntoViewIfNeeded();
    assert.equal(await page.locator("#save-correction").isVisible(),true,"mobile correction actions remain reachable");
    await page.screenshot({path:path.join(out,"vlb-mobile-correction.png"),fullPage:false});
    await page.locator("#close-correction").click();
    await assertMobileUnifiedReader("mobile citation unified reader");
    assert.equal(await page.locator(`${scanSection("I-017")} svg rect`).count(), 1,
      "visible facsimile retains the form-level OCR target");
    await assertPaintedPage("#scan-viewport","I-017");
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    await page.screenshot({path:path.join(out,"vlb-mobile-citation-unified.png"),fullPage:false});
    await page.locator("#toggle-transcription").click();
    await assertMobileUnifiedReader("mobile citation minimized tray", {expanded:false});
    assert.equal(await page.locator(`${scanSection("I-017")} svg rect`).count(), 1,
      "minimizing the transcription retains the OCR target");
    await page.locator("#toggle-transcription").click();
    await assertMobileUnifiedReader("mobile citation restored tray");
    await settlePaint();
    assert.ok(await mobileReviewed.evaluate(node => {
      const viewport = document.getElementById("text-viewport").getBoundingClientRect();
      const box = node.getBoundingClientRect();
      return box.bottom > viewport.top && box.top < viewport.bottom;
    }), "selected transcription remains visible after minimizing and restoring the tray");
    assert.ok(await page.locator("#text-viewport").evaluate(viewport => viewport.scrollTop) >= mobileTextPosition - 3,
      "restoring the tray does not jump above the selected transcription position");
    const legacySurfaceURL = new URL(page.url());
    legacySurfaceURL.searchParams.set("surface", "scan");
    await page.goto(legacySurfaceURL.href);
    await page.locator(`${scanSection("I-017")} .scan-stage img`).waitFor({state:"attached"});
    await page.waitForFunction(selector => {
      const image = document.querySelector(selector);
      return image?.complete && image.naturalWidth > 0;
    }, `${scanSection("I-017")} img`);
    await assertMobileUnifiedReader("legacy mobile surface route");
    assert.equal(await mobileReviewed.getAttribute("data-source-id"), "vlb-emerson-r568-p00013");
    assert.equal(await page.locator(`${scanSection("I-017")} svg rect`).count(),1,
      "legacy surface routes retain the unified source highlight");
    await page.setViewportSize({width:1440,height:1080});
    await page.locator("#scan-panel").waitFor({state:"visible"});

    await page.locator("#next-page").click();
    await page.waitForFunction(() => new URLSearchParams(location.search).get("page") === "18");
    assert.equal(await page.locator(".continuous-text-page .fragment.selected").count(), 0,
      "explicit next-page navigation clears the earlier source selection");
    assert.equal(await page.locator(`${scanSection("I-017")} svg rect`).count(), 0,
      "explicit next-page navigation clears the earlier OCR highlight");
    assert.equal(await page.locator("mark.match-span").count(), 0,
      "continuous page activation removes the earlier exact-span mark");

    // A strong proposal may be useful for navigation, but remains a proposal.
    await openContinuous("?volume=I&page=17&entry=2480&citation_pos=84&focus=auto");
    const selectedProposed = page.locator(`${textSection("I-017")} .fragment.selected`);
    await selectedProposed.waitFor();
    assert.equal(await selectedProposed.getAttribute("data-source-id"), "vlb-emerson-r568-p00025");
    assert.equal(await page.locator("#citation-detail").isHidden(), true);
    await openSelectedNavarroDetail(textSection("I-017"));
    assert.ok((await page.locator("#citation-detail").innerText()).includes("proposta"));
    assert.ok(await page.locator(`${scanSection("I-017")} svg rect`).count() > 0);
    assert.equal(await selectedProposed.locator("mark.match-span").innerText(), "Aguaça pupe aico");

    // A manually chosen lower-ranked exact span is encoded in the shared URL
    // and survives reload instead of silently reverting to the automatic top span.
    await page.locator("#citation-detail details.candidate-evidence summary").click();
    await page.locator("#citation-detail details.candidate-evidence button").filter({hasText:/^“Aguaça”$/}).click();
    assert.equal(new URL(page.url()).searchParams.get("target_start"), "1103");
    assert.equal(new URL(page.url()).searchParams.get("target_end"), "1109");
    assert.equal(new URL(page.url()).searchParams.has("focus"), false);
    assert.equal(await selectedProposed.locator("mark.match-span").innerText(), "Aguaça");
    await page.reload();
    await page.locator(`${textSection("I-017")} .fragment.selected mark.match-span`).waitFor();
    assert.equal(await page.locator(`${textSection("I-017")} .fragment.selected mark.match-span`).innerText(), "Aguaça");
    await page.locator("#mode-select").selectOption("page");
    await page.locator("#source-25 mark.match-span").waitFor();
    assert.equal(await page.locator("#source-25 mark.match-span").innerText(),"Aguaça");
    assert.equal(new URL(page.url()).searchParams.has("focus"),false);
    assert.equal(new URL(page.url()).searchParams.get("target_start"),"1103");
    assert.equal(new URL(page.url()).searchParams.get("target_end"),"1109");
    await page.locator("#mode-select").selectOption("continuous");
    await page.locator(`${textSection("I-017")} .fragment.selected mark.match-span`).waitFor();
    assert.equal(await page.locator(`${textSection("I-017")} .fragment.selected mark.match-span`).innerText(),"Aguaça");
    assert.equal(await page.locator("#citation-detail").isHidden(), true,
      "mode changes preserve alignment without reopening Navarro detail");

    // A new correction can be built from the selected exact text, saved
    // locally, submitted as structured issue data, exported, and strictly
    // validated without exposing a GitHub credential in the reader.
    await openSelectedNavarroDetail(textSection("I-017"));
    await page.locator("#citation-detail .detail-actions button").filter({hasText:"Corrigir"}).click();
    assert.equal(await page.locator("#correction-spans .correction-span").count(), 0);
    await page.locator(`${textSection("I-017")} .fragment.selected mark.match-span`).evaluate(mark => {
      const range = document.createRange();
      range.selectNodeContents(mark);
      const selection = getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
    });
    await page.locator("#add-correction-span").click();
    assert.ok((await page.locator("#correction-spans .correction-span").innerText()).includes("Aguaça"));
    await page.locator("#correction-reviewer").fill("VLB browser regression");
    await page.locator("#correction-notes").fill("Selected the exact historical form and checked its narrowed OCR line in the browser regression.");
    await page.locator("#save-correction").click();
    const aguasaSavedCorrection = await savedCorrectionFromFeedback();
    await page.evaluate(() => {
      window.__vlbIssueURL = null;
      window.open = () => ({opener:null,close(){},location:{replace(value){window.__vlbIssueURL = value;}}});
    });
    await page.locator("#submit-correction").click();
    await page.waitForFunction(() => Boolean(window.__vlbIssueURL));
    const issueURL = new URL(await page.evaluate(() => window.__vlbIssueURL));
    const submitted = JSON.parse(issueURL.searchParams.get("payload"));
    assert.equal(submitted.schema_version,"vlb-correction-submission-1");
    assert.equal(submitted.events.length,1,"save then submit reuses the saved pending revision");
    assert.deepEqual(submitted.events[0],aguasaSavedCorrection);
    assertCorrectionChain(submitted.events[0]);
    assert.equal(submitted.events[0].selected_spans[0].text,"Aguaça");
    assert.ok(submitted.events[0].selected_spans[0].ocr_targets.length > 0,
      "selection of the active model span retains its pinned OCR target");

    const correctionDownloadPromise = page.waitForEvent("download");
    await page.locator("#export-corrections").click();
    const correctionDownload = await correctionDownloadPromise;
    const correctionPath = path.join(out,"corrections-test.json");
    await correctionDownload.saveAs(correctionPath);
    const correctionEnvelope = JSON.parse(fs.readFileSync(correctionPath,"utf8"));
    assert.equal(correctionEnvelope.events.length,2,"export includes both local correction streams");
    childProcess.execFileSync("python3",["vlb/manage_corrections.py","import","--input",correctionPath,"--dry-run"],
      {cwd:root,stdio:"pipe"});
    await page.locator("#close-correction").click();
    await page.evaluate(() => localStorage.removeItem("nhe-enga-vlb-corrections-v1"));
    await page.reload();
    await page.locator(`${textSection("I-017")} .fragment.selected`).waitFor();
    await openSelectedNavarroDetail(textSection("I-017"));
    await page.locator("#citation-detail .detail-actions button").filter({hasText:"Corrigir"}).click();
    await page.locator("#import-corrections").setInputFiles(correctionPath);
    await page.waitForFunction(() => document.getElementById("correction-feedback").textContent.includes("2 correção"));
    assert.equal(await page.evaluate(() => JSON.parse(localStorage.getItem("nhe-enga-vlb-corrections-v1")).length),2);
    await page.locator("#close-correction").click();
    await page.locator("#citation-detail .detail-actions button").filter({hasText:"Corrigir"}).click();
    assert.ok((await page.locator("#correction-spans .correction-span").innerText()).includes("Aguaça"),
      "an imported local revision repopulates its exact spans after reopening");
    await page.locator("#close-correction").click();

    await openContinuous("?volume=I&page=17&entry=3255&citation_pos=612&focus=auto");
    assert.equal(await page.locator(".continuous-text-page .fragment.selected").getAttribute("data-source-id"),
      "vlb-emerson-r568-p00030");
    assert.equal(await page.locator(".continuous-text-page .fragment.selected mark.match-span").innerText(),
      "Ainheengapigpigc iepe","the complete quotation resolves the former weak tie");

    await openContinuous("?volume=I&page=83&entry=2435&focus=auto");
    assert.equal(await page.locator(".continuous-text-page .fragment.selected").count(),0,
      "a reviewed ambiguous correction never invents an automatic destination");
    assert.equal(await page.locator(".continuous-scan-page svg rect").count(),0);
    assert.equal(await page.locator("#citation-detail").isHidden(),true);
    await openCurrentNavarroDetail();
    assert.ok((await page.locator("#citation-detail").innerText()).includes("Correção ambígua"));

    // This definition has two original II64 occurrences but three formatted
    // copies. The linker deliberately omits an occurrence offset rather than
    // guessing which one the reader meant.
    await page.goto(base.replace(/vlb\/$/,"") + "?query=" + encodeURIComponent("aîa"));
    const ambiguousInline = page.locator('#results a[href*="/nhe-enga/vlb/?"][href*="entry=2502"][href*="page=64"]').first();
    await ambiguousInline.waitFor();
    const ambiguousURL = new URL(await ambiguousInline.getAttribute("href"), base);
    assert.equal(ambiguousURL.searchParams.has("citation_pos"), false);
    await openContinuous(ambiguousURL.search);
    assert.equal(await page.locator("#text-tab").getAttribute("aria-selected"), "true",
      "ambiguous navigation does not open the Navarro tray");
    assert.equal(await page.locator("#citation-choice-notice").isVisible(), false,
      "ambiguous choices stay behind the explicit Navarro action");
    await page.locator("#citations-tab").click();
    assert.equal(await page.locator("#citation-choice-notice").isVisible(), true,
      "duplicate citation occurrences require an explicit choice");
    assert.equal(await page.locator(".continuous-text-page .fragment.selected").count(), 0);
    assert.equal(await page.locator(".continuous-scan-page svg rect").count(), 0);
    await page.locator("#text-tab").click();
    const contextualFragment = page.locator(`${textSection("II-064")} .fragment`).filter({
      has:page.locator(".fragment-actions button").filter({hasText:"Ver no Navarro"})
    }).first();
    await contextualFragment.locator(".source-main").click();
    assert.equal(await page.locator("#citation-choice-notice").evaluate(node => node.hidden), true,
      "selecting a source clears a stale ambiguous-entry choice notice");
    assert.equal(new URL(page.url()).searchParams.has("entry"), false,
      "selecting a source clears the stale ambiguous dictionary entry from the URL");
    const contextualAction = contextualFragment.locator(".fragment-actions button").filter({hasText:"Ver no Navarro"});
    const contextualCount = Number((await contextualAction.innerText()).match(/\d+/)[0]);
    assert.equal(Number(await page.locator("#citation-count").innerText()), contextualCount,
      "source selection replaces entry-wide candidates with line-specific Navarro results");
    await contextualAction.click();
    assert.equal(await page.locator("#citation-list .citation-card").count(), contextualCount);

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
    assert.equal(await page.locator("#citation-detail").isHidden(), true,
      "continuous transcript selection does not open Navarro detail");
    assert.equal(await page.locator("#text-tab").getAttribute("aria-selected"), "true");
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
    await assertMobileUnifiedReader("continuous selected-source route");
    await page.waitForFunction(selector => {
      const image = document.querySelector(selector);
      return image?.complete && image.naturalWidth > 0;
    }, `${scanSection("II-078")} img`);
    await assertPaintedPage("#text-viewport","II-078");
    assert.ok(await page.locator(`${scanSection("II-078")} svg rect`).count() > 0,
      "continuous unified reader preserves the selected source highlight");
    assert.ok(await page.locator(`${scanSection("II-078")} svg rect`).first().evaluate(node => {
      const viewport = document.getElementById("scan-viewport").getBoundingClientRect();
      const box = node.getBoundingClientRect();
      return box.bottom > viewport.top && box.top < viewport.bottom;
    }), "continuous mobile reader keeps the selected facsimile line visible");
    await page.screenshot({path:path.join(out,"vlb-continuous-mobile-unified.png"),fullPage:false});
    await page.locator("#toggle-transcription").click();
    await assertMobileUnifiedReader("continuous minimized transcription", {expanded:false});
    assert.ok(await page.locator(`${scanSection("II-078")} svg rect`).count() > 0,
      "continuous minimized tray retains the selected source highlight");
    assert.ok(await page.locator(`${scanSection("II-078")} svg rect`).first().evaluate(node => {
      const viewport = document.getElementById("scan-viewport").getBoundingClientRect();
      const box = node.getBoundingClientRect();
      return box.bottom > viewport.top && box.top < viewport.bottom;
    }), "minimizing continuous transcription keeps the selected facsimile line visible");
    await page.screenshot({path:path.join(out,"vlb-continuous-mobile-minimized.png"),fullPage:false});
    await page.locator("#toggle-transcription").click();
    await assertMobileUnifiedReader("continuous restored transcription");
    assert.equal(await page.locator(`${textSection("II-078")} .fragment.selected`).getAttribute("data-source-id"),
      "vlb-emerson-r568-p05859");
    await assertPaintedPage("#text-viewport","II-078");
    assert.ok(await page.locator(`${scanSection("II-078")} svg rect`).first().evaluate(node => {
      const viewport = document.getElementById("scan-viewport").getBoundingClientRect();
      const box = node.getBoundingClientRect();
      return box.bottom > viewport.top && box.top < viewport.bottom;
    }), "restoring the tray keeps the selected facsimile line visible");
    await page.setViewportSize({width:1440,height:1080});

    // Long correction histories cannot safely fit in every browser/proxy URL.
    // The reader must download the complete envelope and open an unprefilled
    // token-free issue form instead of truncating structured evidence.
    await openContinuous("?volume=I&page=17&entry=7210&citation_pos=86&focus=auto");
    await openSelectedNavarroDetail(textSection("I-017"));
    await page.locator("#citation-detail .detail-actions button").filter({hasText:"Corrigir"}).click();
    await page.locator("#correction-reviewer").fill("VLB browser regression");
    await page.locator("#correction-notes").fill("Long prefill fallback. " + "evidence ".repeat(900));
    await page.evaluate(() => {
      window.__vlbIssueURL = null;
      window.open = () => ({opener:null,close(){},location:{replace(value){window.__vlbIssueURL = value;}}});
    });
    const oversizedDownloadPromise = page.waitForEvent("download");
    await page.locator("#submit-correction").click();
    const oversizedDownload = await oversizedDownloadPromise;
    await oversizedDownload.saveAs(path.join(out,"correction-oversized-prefill.json"));
    await page.waitForFunction(() => Boolean(window.__vlbIssueURL));
    const oversizedIssueURL = new URL(await page.evaluate(() => window.__vlbIssueURL));
    assert.equal(oversizedIssueURL.searchParams.get("template"),"vlb-correction.yml");
    assert.equal(oversizedIssueURL.searchParams.has("payload"),false,
      "oversized structured payload is never truncated into the issue URL");
    assert.ok((await page.locator("#correction-feedback").innerText()).includes("grande demais"));

    // The Pages build changes the scan extension. Exercise the format manifest
    // contract while using the same image bytes as a small local fixture.
    await page.route("**/docs/primary_sources/image-formats.json", route => route.fulfill({contentType:"application/json",body:JSON.stringify({books:{vlb:".jpg"}})}));
    await page.route("**/docs/primary_sources/vlb/17.jpg", route => route.fulfill({contentType:"image/png",path:path.join(root,"docs/primary_sources/vlb/17.png")}));
    await open("?volume=I&page=17");
    assert.ok((await page.locator("#page-image").getAttribute("src")).endsWith("/17.jpg"));
    assert.deepEqual(errors, []);
    const result = {desktop:true,mobile:true,source_selection:true,citation_navigation:true,legacy_entry_link_stays_manual:true,
      ocr_overlay:true,notes_export_and_persistence:true,nontext_inserts:true,volume_offset:true,split_paragraphs:true,
      search:true,source_only_search:true,exact_search_before_inside_word:true,
      portuguese_and_orthography_search:true,no_search_citation_index:true,
      optimized_image_manifest:true,continuous_scroll:true,continuous_prepend_preserves_anchor:true,
      continuous_scroll_sync:true,continuous_mode_toggle:true,inline_citation_occurrence:true,reviewed_form_line_jump:true,
      proposed_jump_stays_proposed:true,ambiguous_jump_fallback:true,ambiguous_occurrence_choice:true,no_homepage_vlb_navigation:true,
      explicit_navigation_clears_selection:true,logical_volume_neighbors:true,source_below_sticky_heading:true,
      mobile_unified_reader:true,mobile_facsimile_primary:true,mobile_transcription_tray:true,mobile_transcription_minimize:true,
      mobile_facsimile_minimize:true,never_both_panes_minimized:true,mobile_collapsible_search:true,
      mobile_low_profile_navigation:true,mobile_compact_transcription_type:true,responsive_viewport_matrix:true,
      reader_splitter_accessible:true,mobile_splitter_drag_persistence:true,desktop_splitter_keyboard_drag_persistence:true,
      pinch_zoom:true,zoom_persistence:true,view_preferences_local_storage:true,no_ocr_reading_dropdown:true,
      contextual_navarro_only:true,citation_detail_requires_explicit_action:true,
      transcript_click_is_navigation_only:true,facsimile_line_reverse_navigation:true,scan_highlight_centered:true,
      contextual_navarro_resets_on_line_selection:true,line_navigation_clears_stale_citation:true,
      selected_line_share_only:true,native_line_share:true,
      share_fallback_to_clipboard:true,clipboard_failure_manual_prompt:true,compact_line_deep_link:true,
      exact_source_span_mark:true,manual_alternative_route_persists:true,correction_local_save:true,
      auto_focus_route_persists:true,manual_alternative_mode_switch_persists:true,
      correction_issue_payload:true,correction_issue_oversize_fallback:true,correction_export_import:true,
      correction_strict_dry_run:true,mobile_correction_geometry:true,
      javascript_errors:errors,screenshots:out};
    fs.writeFileSync(path.join(out,"result.json"), JSON.stringify(result,null,2)+"\n");
    console.log(JSON.stringify(result));
  } catch (error) {
    await page.screenshot({path:path.join(out,"vlb-failure.png"),fullPage:false}).catch(() => {});
    console.error(`VLB browser check failed at ${page.url()}`);
    throw error;
  } finally { await context.close(); await browser.close(); server.close(); }
})().catch(error => { console.error(error); server.close(); process.exitCode = 1; });
