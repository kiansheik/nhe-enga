/* VLB source concordance. Text is always inserted as text, never as HTML. */
"use strict";

(() => {
  const $ = id => document.getElementById(id);
  const narrowMedia = matchMedia("(max-width: 900px)");
  const state = {
    manifest: null, page: null, pageId: null, selectedSource: null,
    selectedCitation: null, entry: null, tab: "text", zoom: 100,
    imageExtension: ".png", sourceIndex: null, orthographyModel: null, searchIndex: null,
    notes: [], corrections: [], correctionDraft: null,
    loadToken: 0, searchToken: 0, cache: new Map(), pending: new Map(),
    mode: "page", autoTarget: null, citationEntryFilter: null, imageFocus: null,
    surface: "scan", surfaceExplicit: false, narrow: narrowMedia.matches,
    transcriptionMinimized: false, facsimileMinimized: false, searchOpen: false,
    surfaceScroll: {scan: 0, text: 0}, surfaceVisited: {scan: false, text: false},
  };
  const flow = {views: new Map(), ids: [], generation: 0, pending: new Map(),
    frames: {}, lockedUntil: {scan: 0, text: 0}, failed: new Set(), position: null, imageAnchorId: null};
  const NOTE_KEY = "nhe-enga-vlb-review-v1";
  const CORRECTION_KEY = "nhe-enga-vlb-corrections-v1";
  const VIEW_KEY = "nhe-enga-vlb-viewer-v1";
  const MIN_ZOOM = 100;
  const MAX_ZOOM = 400;
  const viewPreferences = {
    zoom: 100, desktopTextShare: 50, mobileTextShare: 31,
    transcriptionMinimized: false, facsimileMinimized: false,
    showOcr: true, mode: "continuous",
  };
  // GitHub can reject an oversized prefilled issue URL before its form loads.
  // Leave headroom for browser/proxy limits and fall back to a downloaded
  // payload that the reviewer can paste into the same token-free issue form.
  const MAX_ISSUE_PREFILL_URL_LENGTH = 7000;
  const noteKinds = {transcription: "Transcrição", association: "Associação", pagination: "Paginação", other: "Observação"};
  let toastTimer;
  let suppressScanClickUntil = 0;

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, Number(value)));
  }

  function readViewPreferences() {
    try {
      const saved = JSON.parse(localStorage.getItem(VIEW_KEY) || "null");
      if (!saved || typeof saved !== "object") return;
      if (Number.isFinite(saved.zoom)) viewPreferences.zoom = clamp(saved.zoom, MIN_ZOOM, MAX_ZOOM);
      if (Number.isFinite(saved.desktopTextShare)) viewPreferences.desktopTextShare = clamp(saved.desktopTextShare, 28, 72);
      if (Number.isFinite(saved.mobileTextShare)) viewPreferences.mobileTextShare = clamp(saved.mobileTextShare, 18, 72);
      if (typeof saved.transcriptionMinimized === "boolean") viewPreferences.transcriptionMinimized = saved.transcriptionMinimized;
      if (typeof saved.facsimileMinimized === "boolean") viewPreferences.facsimileMinimized = saved.facsimileMinimized;
      if (typeof saved.showOcr === "boolean") viewPreferences.showOcr = saved.showOcr;
      if (["page", "continuous"].includes(saved.mode)) viewPreferences.mode = saved.mode;
      if (viewPreferences.transcriptionMinimized && viewPreferences.facsimileMinimized) viewPreferences.facsimileMinimized = false;
    } catch { /* A corrupt or blocked preference store must not block the reader. */ }
  }

  function saveViewPreferences() {
    try { localStorage.setItem(VIEW_KEY, JSON.stringify(viewPreferences)); }
    catch { /* Viewing remains fully usable when storage is unavailable. */ }
  }

  function element(tag, className, text) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined && text !== null) el.textContent = String(text);
    return el;
  }

  function action(text, className, onClick) {
    const button = element("button", className, text);
    button.type = "button";
    button.addEventListener("click", onClick);
    return button;
  }

  function externalLink(text, url) {
    const a = element("a", "", text);
    a.href = url;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    return a;
  }

  function fold(text) {
    return String(text || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt-BR");
  }

  function compact(text, max = 220) {
    const value = String(text || "").replace(/\s+/g, " ").trim();
    return value.length > max ? value.slice(0, max - 1) + "…" : value;
  }

  function sourceShareURL(source, page) {
    const url = new URL(location.origin + location.pathname);
    url.searchParams.set("page", page.id);
    url.searchParams.set("line", source.source_line);
    return url.href;
  }

  function sourceCitation(source, page) {
    return `Vocabulário na Língua Brasílica (VLB), v. ${page.volume}, p. ${page.page}, § ${source.source_line}.`;
  }

  function sourceCitationBlock(source, page) {
    return `${source.text}\n\n${sourceCitation(source, page)}\n${sourceShareURL(source, page)}`;
  }

  async function copySourceCitation(source, page) {
    try {
      await navigator.clipboard.writeText(sourceCitationBlock(source, page));
      announce("Verbete, citação e link copiados.");
    } catch {
      window.prompt?.("Copie a citação e o link:", sourceCitationBlock(source, page));
      announce("A citação foi aberta para cópia manual.");
    }
  }

  async function shareSourceCitation(source, page) {
    const data = {title: `VLB ${page.volume}, p. ${page.page}, § ${source.source_line}`,
      text: `${source.text}\n\n${sourceCitation(source, page)}`, url: sourceShareURL(source, page)};
    if (typeof navigator.share === "function") {
      try {
        await navigator.share(data);
        return;
      } catch (error) {
        if (error?.name === "AbortError") return;
      }
    }
    await copySourceCitation(source, page);
  }

  function pageLabel(page = state.page) {
    return page ? `${page.volume}, ${page.page}` : "";
  }

  function pageId(volume, page) {
    return `${volume}-${String(page).padStart(3, "0")}`;
  }

  function allPages() {
    if (state.pages) return state.pages;
    // Plate and blank verso remain navigable even though they have no text file.
    const pages = [...state.manifest.pages];
    for (const slot of state.manifest.scan_slots || []) {
      if (![25, 26].includes(slot.image_index) || pages.some(p => p.image_index === slot.image_index)) continue;
      pages.push({id: pageId("I", slot.image_index), volume: "I", page: slot.image_index,
        pdf_page: slot.image_index, image_index: slot.image_index, kind: slot.kind});
    }
    state.pages = pages.sort((a, b) => a.image_index - b.image_index);
    state.pageOrdinals = new Map(state.pages.map((page, index) => [page.id, index]));
    return state.pages;
  }

  function metadata(id) {
    return allPages().find(p => p.id === id);
  }

  async function pageData(id) {
    if (state.cache.has(id)) return state.cache.get(id);
    if (state.pending.has(id)) return state.pending.get(id);
    const meta = metadata(id);
    const promise = (async () => {
      const data = meta.data_file ? await readJSON(`data/${meta.data_file}`) :
        {...meta, fragments: [], citations: [], ocr_lines: [], boundaries: null};
      const page = {...meta, ...data};
      state.cache.set(id, page);
      if (state.cache.size > 12) state.cache.delete(state.cache.keys().next().value);
      return page;
    })();
    state.pending.set(id, promise);
    try { return await promise; } finally { state.pending.delete(id); }
  }

  function fragmentContainer(id = state.pageId) {
    return state.mode === "continuous" ? flow.views.get(id)?.list : $("fragment-list");
  }

  function activeScan() {
    if (state.mode === "continuous") return flow.views.get(state.pageId);
    return {stage: $("scan-stage"), image: $("page-image"), overlay: $("ocr-overlay")};
  }

  function paneVisible(pane) {
    if (!state.narrow) return true;
    return pane === "text" ? !state.transcriptionMinimized : !state.facsimileMinimized;
  }

  function applySplitPreference() {
    const workspace = document.querySelector(".workspace");
    workspace.style.setProperty("--desktop-text-share", `${viewPreferences.desktopTextShare}%`);
    workspace.style.setProperty("--mobile-text-share", `${viewPreferences.mobileTextShare}%`);
    const splitter = $("reader-splitter");
    const value = Math.round(state.narrow ? viewPreferences.mobileTextShare : viewPreferences.desktopTextShare);
    splitter.setAttribute("aria-orientation", state.narrow ? "horizontal" : "vertical");
    splitter.setAttribute("aria-valuemin", state.narrow ? "18" : "28");
    splitter.setAttribute("aria-valuemax", "72");
    splitter.setAttribute("aria-valuenow", String(value));
    splitter.setAttribute("aria-valuetext", `${value}% para a transcrição`);
  }

  function setSearchOpen(open, {focus = false} = {}) {
    const effective = state.narrow ? Boolean(open) : true;
    state.searchOpen = effective;
    $("toggle-search").setAttribute("aria-expanded", String(effective));
    $("toggle-search").setAttribute("aria-label", effective ? "Fechar busca na transcrição" : "Abrir busca na transcrição");
    $("search-form").inert = !effective;
    if (effective) $("search-form").removeAttribute("aria-hidden");
    else {
      $("search-form").setAttribute("aria-hidden", "true");
      if (state.narrow) {
        state.searchToken++;
        $("search-results").hidden = true;
      }
    }
    document.querySelector(".navigation").classList.toggle("search-open", effective);
    if (effective && focus) requestAnimationFrame(() => $("search-input").focus());
  }

  function applySurfaceVisibility() {
    document.body.classList.toggle("surface-text", state.surface === "text");
    document.body.classList.toggle("surface-scan", state.surface === "scan");
    for (const pane of ["text", "scan"]) {
      const selected = state.surface === pane;
      $(`surface-${pane}`).setAttribute("aria-pressed", String(selected));
      const panel = $(pane === "text" ? "transcription-panel" : "scan-panel");
      panel.inert = false;
      panel.removeAttribute("aria-hidden");
    }
  }

  function setTranscriptionMinimized(minimized, {focus = true, remember = false} = {}) {
    const effective = state.narrow && Boolean(minimized);
    const body = $("transcription-body");
    const button = $("toggle-transcription");
    if (effective && state.facsimileMinimized) setFacsimileMinimized(false, {focus: false, remember});
    if (effective && body.contains(document.activeElement)) button.focus({preventScroll: true});
    state.transcriptionMinimized = effective;
    document.body.classList.toggle("transcription-minimized", effective);
    body.inert = effective;
    if (effective) body.setAttribute("aria-hidden", "true");
    else body.removeAttribute("aria-hidden");
    button.setAttribute("aria-expanded", String(!effective));
    const label = effective ? "Mostrar transcrição" : "Minimizar transcrição";
    button.setAttribute("aria-label", label);
    button.title = label;
    $("transcription-toggle-label").textContent = effective ? "Mostrar" : "Minimizar";
    if (remember) {
      viewPreferences.transcriptionMinimized = effective;
      if (effective) viewPreferences.facsimileMinimized = false;
      saveViewPreferences();
    }
    if (!effective && focus) button.focus({preventScroll: true});
    if (!effective && state.page) {
      requestAnimationFrame(() => {
        const selected = state.page.fragments.find(fragment => fragment.id === state.selectedSource);
        if (selected) scrollTextToSource(selected.id);
        else if (state.mode === "continuous" && flow.position) syncFlowPane("text", flow.position);
        if (state.mode === "continuous") manageFlowImages();
      });
    }
  }

  function setFacsimileMinimized(minimized, {focus = true, remember = false} = {}) {
    const effective = state.narrow && Boolean(minimized);
    const body = $("scan-body");
    const button = $("toggle-facsimile");
    if (effective && state.transcriptionMinimized) setTranscriptionMinimized(false, {focus: false, remember});
    if (effective && body.contains(document.activeElement)) button.focus({preventScroll: true});
    state.facsimileMinimized = effective;
    document.body.classList.toggle("facsimile-minimized", effective);
    body.inert = effective;
    if (effective) {
      body.setAttribute("aria-hidden", "true");
      $("scan-options").open = false;
    } else body.removeAttribute("aria-hidden");
    button.setAttribute("aria-expanded", String(!effective));
    const label = effective ? "Mostrar fac-símile" : "Minimizar fac-símile";
    button.setAttribute("aria-label", label);
    button.title = label;
    $("facsimile-toggle-label").textContent = label;
    if (remember) {
      viewPreferences.facsimileMinimized = effective;
      if (effective) viewPreferences.transcriptionMinimized = false;
      saveViewPreferences();
    }
    if (!effective && focus) button.focus({preventScroll: true});
    if (!effective && state.page) requestAnimationFrame(() => {
      hydrateScan();
      const selected = state.page.fragments.find(fragment => fragment.id === state.selectedSource);
      if (selected) scrollToHighlight(selected);
    });
  }

  function setSurface(surface, options = {}) {
    const next = surface === "text" ? "text" : "scan";
    const previous = state.surface;
    if (state.narrow && state.page && previous && $(previous === "text" ? "text-viewport" : "scan-viewport")) {
      state.surfaceScroll[previous] = flowViewport(previous).scrollTop;
      state.surfaceVisited[previous] = true;
    }
    state.surface = next;
    if (options.explicit) state.surfaceExplicit = true;
    if (state.narrow && next === "text") setTranscriptionMinimized(false, {focus: false});
    applySurfaceVisibility();
    if (state.narrow && state.page && options.restore !== false) {
      const hadVisited = state.surfaceVisited[next];
      requestAnimationFrame(() => {
        const viewport = flowViewport(next);
        if (next === "scan") hydrateScan();
        const selected = state.page.fragments.find(fragment => fragment.id === state.selectedSource);
        if (selected) {
          if (next === "text") scrollTextToSource(selected.id);
          else {
            state.imageFocus = selected.id;
            drawOverlay();
            scrollToHighlight(selected);
          }
        } else if (state.mode === "continuous" && flow.position && !hadVisited) {
          syncFlowPane(next, flow.position);
        } else viewport.scrollTop = state.surfaceScroll[next] || 0;
        state.surfaceScroll[next] = viewport.scrollTop;
        state.surfaceVisited[next] = true;
      });
    } else if (!state.narrow && state.page) hydrateScan();
    if (options.update !== false && state.page) updateURL();
  }

  function syncResponsiveUI(initial = false) {
    const changed = state.narrow !== narrowMedia.matches;
    state.narrow = narrowMedia.matches;
    if (initial || changed) {
      $("reader-options").open = !state.narrow;
      $("scan-options").open = !state.narrow;
    }
    applySplitPreference();
    if (state.narrow) {
      setSearchOpen(false);
      if (initial || changed) {
        setTranscriptionMinimized(viewPreferences.transcriptionMinimized, {focus: false});
        setFacsimileMinimized(viewPreferences.facsimileMinimized, {focus: false});
      }
    } else {
      setSearchOpen(true);
      setTranscriptionMinimized(false, {focus: false});
      setFacsimileMinimized(false, {focus: false});
    }
    applySurfaceVisibility();
    if (!state.page) return;
    hydrateScan();
    if (state.mode === "continuous") manageFlowImages();
    if (changed && state.selectedSource) setSurface(state.surface, {update: false});
  }

  function setMode(mode, {remember = false} = {}) {
    state.mode = mode === "continuous" ? "continuous" : "page";
    document.body.classList.toggle("continuous-mode", state.mode === "continuous");
    $("mode-select").value = state.mode;
    $("scan-stack").hidden = state.mode !== "continuous";
    $("scan-stage").hidden = state.mode === "continuous";
    if (state.mode === "continuous") $("image-message").hidden = true;
    else resetFlow();
    if (remember) {
      viewPreferences.mode = state.mode;
      saveViewPreferences();
    }
  }

  function resetFlow() {
    flow.generation++;
    flow.views.clear();
    flow.ids = [];
    flow.pending.clear();
    flow.failed.clear();
    flow.position = null;
    flow.imageAnchorId = null;
    $("scan-stack").replaceChildren();
    $("fragment-list").replaceChildren();
  }

  function flowViewport(pane) { return $(pane === "scan" ? "scan-viewport" : "text-viewport"); }
  function flowElement(view, pane) { return pane === "scan" ? view.scan : view.text; }

  function lockFlow(pane, milliseconds = 160) {
    flow.lockedUntil[pane] = performance.now() + milliseconds;
  }

  function preserveFlowAnchors(change) {
    // Native scroll anchoring is disabled for the stacks; preserve the same
    // visible page when earlier pages or image dimensions become available.
    const anchors = ["scan", "text"].filter(pane => paneVisible(pane)).map(pane => {
      const position = flowPosition(pane);
      const node = position && flowElement(flow.views.get(position.id), pane);
      return {pane, node, top: node?.getBoundingClientRect().top};
    });
    change();
    for (const {pane, node, top} of anchors) {
      if (!node?.isConnected || (pane === "text" && state.tab !== "text")) continue;
      const delta = node.getBoundingClientRect().top - top;
      if (Math.abs(delta) > .5) {
        lockFlow(pane);
        flowViewport(pane).scrollTop += delta;
      }
    }
  }

  function flowHeading(page) {
    const heading = element("header", "continuous-page-heading");
    heading.append(element("span", "", `VLB ${page.volume} · ${page.fragments.length ? "página" : "posição"} ${page.page}`),
      element("small", "", page.fragments.length ? `${page.fragments.length} trechos · ${page.citations.length} citações` : page.image_index === 25 ? "Prancha" : "Verso em branco"));
    return heading;
  }

  function createFlowView(page) {
    const scan = element("section", "continuous-scan-page");
    const text = element("section", "continuous-text-page");
    scan.dataset.pageId = text.dataset.pageId = page.id;
    scan.setAttribute("aria-label", `Fac-símile VLB ${pageLabel(page)}`);
    text.setAttribute("aria-label", `Transcrição VLB ${pageLabel(page)}`);
    const stage = element("div", "scan-stage");
    const img = element("img");
    img.decoding = "async";
    img.loading = "lazy";
    img.alt = `Fac-símile do VLB, volume ${page.volume}, ${page.fragments.length ? "página" : "posição"} ${page.page}`;
    const overlay = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    overlay.setAttribute("viewBox", "0 0 1000 1000");
    overlay.setAttribute("preserveAspectRatio", "none");
    overlay.setAttribute("aria-hidden", "true");
    stage.append(img, overlay);
    bindScanStage(stage, () => page, true);
    stage.style.width = `${state.zoom}%`;
    stage.style.setProperty("--scan-ratio", "0.7071");
    const message = element("p", "image-message", "A imagem será carregada ao se aproximar desta página.");
    scan.append(flowHeading(page), stage, message);
    const list = element("div", "fragment-list");
    text.append(flowHeading(page), list);
    renderFragments(page, list, true);
    const view = {page, scan, text, stage, image: img, overlay, list, message,
      fallback: false, imageURL: scanURL(page)};
    img.onload = () => {
      if (!scan.isConnected) return;
      preserveFlowAnchors(() => {
        stage.style.setProperty("--scan-ratio", `${img.naturalWidth} / ${img.naturalHeight}`);
        message.hidden = true;
      });
      if (state.mode === "continuous" && state.pageId === page.id) {
        drawOverlay();
        const selected = page.fragments.find(f => f.id === state.selectedSource);
        if (selected && state.imageFocus === selected.id) scrollToHighlight(selected);
      }
    };
    img.onerror = () => {
      if (!img.hasAttribute("src")) return;
      if (!view.fallback && state.imageExtension !== ".png") {
        view.fallback = true;
        view.imageURL = `../docs/primary_sources/vlb/${page.image_index}.png`;
        img.src = view.imageURL;
        if (state.pageId === page.id) $("open-scan").href = view.imageURL;
      } else {
        message.hidden = false;
        message.replaceChildren(element("span", "", "Não foi possível carregar a imagem. "),
          action("Tentar novamente", "quiet-button", () => {
            view.fallback = false; view.imageURL = scanURL(page); img.src = view.imageURL;
          }));
      }
    };
    return view;
  }

  function scanURL(page) { return `../docs/primary_sources/vlb/${page.image_index}${state.imageExtension}`; }

  function manageFlowImages(anchorId = flow.imageAnchorId || state.pageId) {
    allPages();
    const currentIndex = state.pageOrdinals.get(anchorId) ?? state.pageOrdinals.get(state.pageId) ?? 0;
    const canHydrate = paneVisible("scan");
    const radius = state.narrow ? 1 : 3;
    for (const view of flow.views.values()) {
      const near = canHydrate && Math.abs(state.pageOrdinals.get(view.page.id) - currentIndex) <= radius;
      if (near && !view.image.hasAttribute("src")) {
        view.message.hidden = false;
        view.message.textContent = "Carregando imagem…";
        view.image.src = view.imageURL;
      } else if (canHydrate && !near && view.image.hasAttribute("src")) {
        view.image.removeAttribute("src");
        view.message.hidden = true;
      }
    }
  }

  function insertFlowPage(page) {
    if (flow.views.has(page.id)) return flow.views.get(page.id);
    const view = createFlowView(page);
    const nextId = flow.ids.find(id => metadata(id).image_index > page.image_index);
    preserveFlowAnchors(() => {
      $("scan-stack").insertBefore(view.scan, nextId ? flow.views.get(nextId).scan : null);
      $("fragment-list").insertBefore(view.text, nextId ? flow.views.get(nextId).text : null);
    });
    flow.views.set(page.id, view);
    flow.ids.push(page.id);
    flow.ids.sort((a, b) => metadata(a).image_index - metadata(b).image_index);
    manageFlowImages();
    return view;
  }

  async function extendFlow(direction) {
    if (state.mode !== "continuous" || !flow.ids.length) return;
    const pages = allPages();
    const edge = direction < 0 ? flow.ids[0] : flow.ids.at(-1);
    const next = pages[pages.findIndex(p => p.id === edge) + direction];
    if (!next || flow.pending.has(next.id) || flow.failed.has(next.id)) return;
    const generation = flow.generation;
    flow.pending.set(next.id, true);
    try {
      const page = await pageData(next.id);
      if (state.mode !== "continuous" || generation !== flow.generation) return;
      insertFlowPage(page);
    } catch (error) {
      if (generation !== flow.generation) return;
      flow.failed.add(next.id);
      $("load-error").hidden = false;
      $("load-error").replaceChildren(element("span", "", `Não foi possível carregar VLB ${next.volume}, ${next.page}. `),
        action("Tentar novamente", "quiet-button", () => {
          flow.failed.delete(next.id); $("load-error").hidden = true; extendFlow(direction);
        }));
    } finally {
      if (generation === flow.generation) flow.pending.delete(next.id);
    }
  }

  function flowSourceBoxes(page, source) {
    const direct = Array.isArray(source?.ocr?.boxes) ? source.ocr.boxes.filter(box =>
      Array.isArray(box) && box.length === 4 && box.every(Number.isFinite)) : [];
    if (direct.length) return direct;
    const lineIds = new Set(source?.ocr?.line_ids || []);
    return (page?.ocr_lines || []).filter(line => lineIds.has(line.id) &&
      Array.isArray(line.box) && line.box.length === 4 && line.box.every(Number.isFinite)).map(line => line.box);
  }

  function flowLandmarks(view) {
    if (!view?.stage?.clientHeight) return [];
    const scanViewport = flowViewport("scan");
    const textViewport = flowViewport("text");
    const scanViewportBox = scanViewport.getBoundingClientRect();
    const textViewportBox = textViewport.getBoundingClientRect();
    const stageBox = view.stage.getBoundingClientRect();
    const scanBase = stageBox.top - scanViewportBox.top + scanViewport.scrollTop;
    const landmarks = [];
    for (const source of view.page.fragments) {
      const article = view.list.querySelector(`[data-source-id="${CSS.escape(source.id)}"]`);
      const boxes = flowSourceBoxes(view.page, source);
      if (!article || !boxes.length) continue;
      const textBox = (article.querySelector(".source-main") || article).getBoundingClientRect();
      const textStart = textBox.top - textViewportBox.top + textViewport.scrollTop;
      const scanStart = scanBase + Math.min(...boxes.map(box => box[1])) * stageBox.height;
      const scanEnd = scanBase + Math.max(...boxes.map(box => box[3])) * stageBox.height;
      const key = source.id;
      landmarks.push({key: `${key}:start`, scan: scanStart, text: textStart},
        {key: `${key}:end`, scan: scanEnd, text: textStart + textBox.height});
    }
    return landmarks;
  }

  function flowAlignment(view, pane, coordinate) {
    const points = flowLandmarks(view).filter(point => Number.isFinite(point[pane]))
      .sort((left, right) => left[pane] - right[pane]);
    if (!points.length) return null;
    if (coordinate <= points[0][pane]) return {start: points[0].key, end: points[0].key, fraction: 0};
    const last = points.at(-1);
    if (coordinate >= last[pane]) return {start: last.key, end: last.key, fraction: 0};
    for (let index = 1; index < points.length; index++) {
      if (coordinate > points[index][pane]) continue;
      const start = points[index - 1];
      const end = points[index];
      const distance = end[pane] - start[pane];
      return {start: start.key, end: end.key,
        fraction: distance > 0 ? clamp((coordinate - start[pane]) / distance, 0, 1) : 0};
    }
    return null;
  }

  function flowPosition(pane) {
    if (!flow.ids.length || !paneVisible(pane) || (pane === "text" && state.tab !== "text")) return null;
    const viewport = flowViewport(pane);
    const offset = Math.min(100, viewport.clientHeight * .2);
    const line = viewport.getBoundingClientRect().top + offset;
    let view = flow.views.get(flow.ids[0]);
    for (const id of flow.ids) {
      const candidate = flow.views.get(id);
      if (flowElement(candidate, pane).getBoundingClientRect().top <= line) view = candidate;
      else break;
    }
    const bounds = flowElement(view, pane).getBoundingClientRect();
    return {id: view.page.id,
      fraction: Math.max(0, Math.min(1, (line - bounds.top) / Math.max(1, bounds.height))),
      alignment: flowAlignment(view, pane, viewport.scrollTop + offset), offset};
  }

  function syncFlowPane(pane, position) {
    const view = flow.views.get(position.id);
    if (!view || !paneVisible(pane) || (pane === "text" && state.tab !== "text")) return;
    const viewport = flowViewport(pane);
    const offset = Math.min(100, viewport.clientHeight * .2);
    let target = null;
    if (position.alignment) {
      const points = new Map(flowLandmarks(view).map(point => [point.key, point[pane]]));
      const start = points.get(position.alignment.start);
      const end = points.get(position.alignment.end);
      if (Number.isFinite(start) && Number.isFinite(end)) {
        target = start + (end - start) * position.alignment.fraction - offset;
      }
    }
    if (!Number.isFinite(target)) {
      const bounds = flowElement(view, pane).getBoundingClientRect();
      target = bounds.top - viewport.getBoundingClientRect().top + viewport.scrollTop +
        bounds.height * position.fraction - offset;
    }
    if (Math.abs(viewport.scrollTop - target) < 2) return;
    lockFlow(pane);
    viewport.scrollTo({top: Math.max(0, target), behavior: "instant"});
  }

  function activateFlowPage(id, {update = true} = {}) {
    if (state.pageId === id) return;
    const view = flow.views.get(id);
    if (!view) return;
    if (state.correctionDraft) closeCorrection({restoreDetail: false});
    state.page = view.page;
    state.pageId = id;
    flow.imageAnchorId = null;
    state.selectedSource = state.selectedCitation = state.autoTarget = state.imageFocus = null;
    refreshSourceSpanMarks();
    state.entry = state.citationEntryFilter = null;
    $("citation-detail").hidden = true;
    $("citation-choice-notice").hidden = true;
    $("citation-filter").value = "";
    for (const article of $("fragment-list").querySelectorAll(".fragment.selected")) {
      article.classList.remove("selected");
      article.querySelector(".source-main")?.setAttribute("aria-pressed", "false");
      for (const extra of article.querySelectorAll(".fragment-actions")) extra.hidden = true;
    }
    for (const v of flow.views.values()) v.overlay.replaceChildren();
    setPageControls();
    renderPage();
    updateNoteTarget();
    updatePageStatus();
    if (update) updateURL();
  }

  function onFlowScroll(pane) {
    if (state.mode !== "continuous" || !paneVisible(pane) || performance.now() < flow.lockedUntil[pane] || (pane === "text" && state.tab !== "text")) return;
    if (flow.frames[pane]) return;
    flow.frames[pane] = requestAnimationFrame(() => {
      flow.frames[pane] = null;
      if (state.mode !== "continuous" || !paneVisible(pane) || performance.now() < flow.lockedUntil[pane]) return;
      const position = flowPosition(pane);
      if (!position) return;
      const viewport = flowViewport(pane);
      state.surfaceScroll[pane] = viewport.scrollTop;
      state.surfaceVisited[pane] = true;
      if (state.selectedSource) {
        if (pane === "scan") {
          flow.imageAnchorId = position.id;
          manageFlowImages(position.id);
        }
      } else {
        flow.position = position;
        activateFlowPage(position.id);
        const other = pane === "scan" ? "text" : "scan";
        if (paneVisible(other)) syncFlowPane(other, position);
      }
      if (viewport.scrollTop < viewport.clientHeight * 1.5) extendFlow(-1);
      if (viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight < viewport.clientHeight * 2) extendFlow(1);
    });
  }

  function scrollFlowToPage(id) {
    const view = flow.views.get(id);
    if (!view) return;
    for (const pane of ["scan", "text"]) {
      if (!paneVisible(pane) || (pane === "text" && state.tab !== "text")) continue;
      const viewport = flowViewport(pane);
      const node = flowElement(view, pane);
      lockFlow(pane, 450);
      viewport.scrollTo({top: node.getBoundingClientRect().top - viewport.getBoundingClientRect().top + viewport.scrollTop - 12, behavior: "instant"});
    }
  }

  async function readJSON(path) {
    const response = await fetch(path);
    if (!response.ok) throw new Error(`Não foi possível carregar ${path} (${response.status}).`);
    if (path.endsWith(".gz")) {
      if (!window.pako) throw new Error("O leitor de dados comprimidos não foi carregado. Recarregue a página.");
      return JSON.parse(window.pako.ungzip(new Uint8Array(await response.arrayBuffer()), {to: "string"}));
    }
    return response.json();
  }

  function announce(text) {
    $("toast").textContent = text;
    $("toast").hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { $("toast").hidden = true; }, 3500);
  }

  function updateURL(push = false) {
    const url = new URL(location.href);
    url.search = "";
    url.searchParams.set("volume", state.page.volume);
    url.searchParams.set("page", state.page.page);
    if (state.mode === "continuous") url.searchParams.set("mode", "continuous");
    else if (viewPreferences.mode !== "page") url.searchParams.set("mode", "page");
    if (state.selectedSource) url.searchParams.set("source", state.selectedSource);
    if (state.selectedCitation) url.searchParams.set("citation", state.selectedCitation);
    if (state.entry !== null) url.searchParams.set("entry", state.entry);
    if (state.autoTarget && state.selectedCitation && !state.autoTarget.manual) url.searchParams.set("focus", "auto");
    if (state.autoTarget?.manual && state.autoTarget.source_span) {
      url.searchParams.set("target_start", state.autoTarget.source_span.start0);
      url.searchParams.set("target_end", state.autoTarget.source_span.end0);
    }
    if (state.surfaceExplicit) url.searchParams.set("surface", state.surface);
    url.hash = "";
    history[push ? "pushState" : "replaceState"]({}, "", url);
  }

  function routeFromURL() {
    const query = new URLSearchParams(location.search);
    const combined = (query.get("page") || "").match(/^(I|II)-(\d+)$/);
    const oldHash = location.hash.match(/^#page-(I|II)-(\d+)$/);
    const volume = combined?.[1] || oldHash?.[1] || query.get("volume") || "I";
    const number = combined?.[2] || oldHash?.[2] || query.get("page") || (volume === "II" ? "7" : "17");
    const entry = query.get("entry");
    const position = query.get("citation_pos");
    const targetStart = query.get("target_start");
    const targetEnd = query.get("target_end");
    const sourceLine = query.get("line");
    const requestedSurface = query.get("surface");
    const surfaceExplicit = requestedSurface === "scan" || requestedSurface === "text";
    const modeExplicit = query.has("mode");
    const hasTextTarget = query.has("source") || query.has("line") || query.has("citation") || query.has("entry") ||
      query.has("citation_pos") || query.get("focus") === "auto";
    return {id: pageId(volume, Number(number)), source: query.get("source"),
      sourceLine: sourceLine !== null && /^\d+$/.test(sourceLine) ? Number(sourceLine) : null,
      citation: query.get("citation"), entry: entry !== null && /^\d+$/.test(entry) ? Number(entry) : null,
      citationPos: position !== null && /^\d+$/.test(position) ? Number(position) : null,
      targetStart: targetStart !== null && /^\d+$/.test(targetStart) ? Number(targetStart) : null,
      targetEnd: targetEnd !== null && /^\d+$/.test(targetEnd) ? Number(targetEnd) : null,
      mode: modeExplicit ? (query.get("mode") === "continuous" ? "continuous" : "page") : viewPreferences.mode,
      modeExplicit, focus: query.get("focus") === "auto",
      surface: surfaceExplicit ? requestedSurface : hasTextTarget ? "text" : "scan", surfaceExplicit};
  }

  function setPageControls() {
    const pages = allPages();
    $("volume-select").value = state.page.volume;
    $("page-select").replaceChildren();
    for (const p of pages.filter(p => p.volume === state.page.volume)) {
      const label = p.image_index === 25 ? "25 · prancha" : p.image_index === 26 ? "26 · verso em branco" : String(p.page);
      const option = element("option", "", label);
      option.value = p.id;
      $("page-select").append(option);
    }
    $("page-select").value = state.pageId;
    const index = pages.findIndex(p => p.id === state.pageId);
    $("previous-page").disabled = index <= 0;
    $("next-page").disabled = index >= pages.length - 1;
    $("page-position").textContent = `${index + 1} / ${pages.length}`;
  }

  async function loadPage(id, options = {}) {
    const token = ++state.loadToken;
    if (options.surface) {
      state.surfaceExplicit = Boolean(options.surfaceExplicit);
      setSurface(options.surface, {update: false, explicit: state.surfaceExplicit, restore: false});
    }
    if (options.mode && options.mode !== state.mode) setMode(options.mode);
    const meta = metadata(id);
    if (!meta) {
      $("load-error").hidden = false;
      $("load-error").textContent = "Esta referência não corresponde a uma página disponível. Abrindo o início do volume I.";
      return loadPage("I-017", {...options, source: null, citation: null, preserveError: true});
    }
    if (state.correctionDraft) closeCorrection({restoreDetail: false});
    $("page-status").textContent = `Carregando volume ${meta.volume}, página ${meta.page}…`;
    if (!options.preserveError) $("load-error").hidden = true;
    $("transcription-panel").setAttribute("aria-busy", "true");
    try {
      const data = flow.views.get(id)?.page || await pageData(id);
      if (token !== state.loadToken) return;
      state.page = {...meta, ...data};
      state.pageId = id;
      const routedSource = options.source || (Number.isInteger(options.sourceLine) ?
        state.page.fragments.find(fragment => fragment.source_line === options.sourceLine)?.id : null);
      if (state.mode === "page") {
        state.surfaceScroll = {scan: 0, text: 0};
        state.surfaceVisited = {scan: false, text: false};
      }
      state.selectedSource = null;
      state.selectedCitation = null;
      state.autoTarget = state.citationEntryFilter = state.imageFocus = null;
      flow.imageAnchorId = null;
      refreshSourceSpanMarks();
      state.entry = options.entry ?? null;
      $("citation-filter").value = "";
      $("citation-detail").hidden = true;
      $("citation-choice-notice").hidden = true;
      if (state.mode === "continuous") {
        if (!flow.views.has(id)) resetFlow();
        insertFlowPage(state.page);
      }
      setPageControls();
      renderPage();
      const showCitationDetail = options.showCitationDetail === true;
      if (options.citation) selectCitation(options.citation, {update: false,
        showTab: showCitationDetail && !routedSource, showDetail: showCitationDetail, autoFocus: options.focus,
        source: routedSource, targetStart: options.targetStart, targetEnd: options.targetEnd});
      else if (state.entry !== null) {
        const candidates = state.page.citations.filter(c => c.entry_index === state.entry);
        const exact = options.citationPos !== null && options.citationPos !== undefined ?
          candidates.filter(c => c.citation_start <= options.citationPos && options.citationPos < c.citation_end) : candidates;
        if (exact.length === 1) selectCitation(exact[0].id, {update: false,
          showTab: showCitationDetail && !routedSource, showDetail: showCitationDetail, autoFocus: options.focus});
        else if (candidates.length) {
          state.citationEntryFilter = state.entry;
          $("citation-choice-notice").hidden = false;
          $("citation-choice-notice").textContent = "Há mais de uma leitura possível para esta referência. Escolha a ocorrência deste verbete para conferir seu trecho; nenhuma linha foi selecionada automaticamente.";
          renderCitations();
          announce("Há mais de uma leitura possível. Abra Navarro para escolher uma ocorrência.");
        } else announce("Este verbete não tem uma ocorrência vinculada nesta página do conjunto de dados.");
      }
      if (routedSource) selectSource(routedSource, {update: false, scroll: true, revealText: true,
        preserveCitation: Boolean(state.selectedCitation),
        target: state.autoTarget?.source_id === routedSource ? state.autoTarget : null});
      else if (Number.isInteger(options.sourceLine)) announce("Esta linha não foi encontrada na página indicada.");
      else if (!state.selectedCitation && state.citationEntryFilter === null) setTab("text");
      if (state.mode === "continuous") {
        if (!state.selectedSource) scrollFlowToPage(id);
        extendFlow(-1);
        extendFlow(1);
      }
      updateNoteTarget();
      updateURL(!!options.push);
      updatePageStatus();
    } catch (error) {
      if (token !== state.loadToken) return;
      $("load-error").hidden = false;
      $("load-error").textContent = `${error.message} Tente recarregar a página.`;
      $("page-status").textContent = "Não foi possível abrir esta página.";
    } finally {
      if (token === state.loadToken) $("transcription-panel").removeAttribute("aria-busy");
    }
  }

  function updatePageStatus() {
    document.title = `VLB ${pageLabel()} · Nhe'enga`;
    $("page-status").textContent = state.page.fragments.length ?
      `Volume ${state.page.volume} · página impressa ${state.page.page} · imagem ${state.page.image_index} do PDF · ${state.page.citations.length} citações${state.mode === "continuous" ? " · rolagem contínua" : ""}` :
      `Volume I · posição ${state.page.page} · ${state.page.image_index === 25 ? "prancha do manuscrito" : "verso em branco"}`;
  }

  function renderPage() {
    $("scan-page-label").textContent = `${state.page.volume} · ${state.page.page}`;
    $("text-count").textContent = state.page.fragments.length;
    $("citation-count").textContent = state.page.citations.length;
    const fragments = state.page.fragments;
    $("text-range").textContent = fragments.length ? `§ ${fragments[0].source_line}–${fragments.at(-1).source_line}` : "Sem texto lexical";
    if (state.mode === "continuous") {
      for (const view of flow.views.values()) {
        view.scan.classList.toggle("current-page", view.page.id === state.pageId);
        view.text.classList.toggle("current-page", view.page.id === state.pageId);
        view.overlay.replaceChildren();
        for (const article of view.list.querySelectorAll(".fragment.selected")) {
          if (view.page.id === state.pageId && article.dataset.sourceId === state.selectedSource) continue;
          article.classList.remove("selected");
          article.querySelector(".source-main")?.setAttribute("aria-pressed", "false");
          for (const extra of article.querySelectorAll(".fragment-actions")) extra.hidden = true;
        }
      }
      $("open-scan").href = flow.views.get(state.pageId)?.imageURL || scanURL(state.page);
      manageFlowImages();
      drawOverlay();
    } else {
      if (paneVisible("scan")) setImage();
      else prepareImage();
      renderFragments();
      $("text-viewport").scrollTop = 0;
    }
    renderCitations();
    renderNotes();
    renderBoundaries();
    syncSearchResultSelection();
  }

  function prepareImage() {
    const path = `../docs/primary_sources/vlb/${state.page.image_index}${state.imageExtension}`;
    const img = $("page-image");
    img.onload = null;
    img.onerror = null;
    img.removeAttribute("src");
    img.dataset.pageId = state.pageId;
    img.alt = state.page.fragments.length ? `Fac-símile do VLB, volume ${state.page.volume}, página ${state.page.page}` :
      state.page.image_index === 25 ? "Prancha do manuscrito, entre as páginas 24 e 27 do volume I" : "Verso em branco da prancha, volume I";
    $("open-scan").href = path;
    $("image-message").hidden = false;
    $("image-message").textContent = "Abra o fac-símile para carregar a imagem.";
    $("scan-viewport").scrollTo({top: 0, left: 0, behavior: "instant"});
    applyZoom();
    drawOverlay();
  }

  function setImage() {
    const path = `../docs/primary_sources/vlb/${state.page.image_index}`;
    const img = $("page-image");
    img.dataset.pageId = state.pageId;
    $("image-message").hidden = false;
    $("image-message").textContent = "Carregando imagem…";
    img.alt = state.page.fragments.length ? `Fac-símile do VLB, volume ${state.page.volume}, página ${state.page.page}` :
      state.page.image_index === 25 ? "Prancha do manuscrito, entre as páginas 24 e 27 do volume I" : "Verso em branco da prancha, volume I";
    img.onload = () => {
      $("image-message").hidden = true;
      drawOverlay();
      const selected = state.page.fragments.find(f => f.id === state.selectedSource);
      if (selected && state.imageFocus === selected.id) scrollToHighlight(selected);
    };
    let fallback = false;
    img.onerror = () => {
      if (!fallback && state.imageExtension !== ".png") {
        fallback = true;
        img.src = path + ".png";
        $("open-scan").href = img.src;
      } else {
        $("image-message").hidden = false;
        $("image-message").replaceChildren(element("span", "", "A imagem não pôde ser carregada. "),
          externalLink("Consultar os fac-símiles", "https://www.etnolinguistica.org/biblio:drumond-1952-1953-vlb"));
      }
    };
    img.src = path + state.imageExtension;
    $("open-scan").href = img.src;
    $("scan-viewport").scrollTo({top: 0, left: 0, behavior: "instant"});
    applyZoom();
    drawOverlay();
  }

  function hydrateScan() {
    if (!state.page) return;
    if (state.mode === "continuous") {
      manageFlowImages();
      const selected = state.page.fragments.find(fragment => fragment.id === state.selectedSource);
      if (selected) {
        state.imageFocus = selected.id;
        drawOverlay();
        scrollToHighlight(selected);
      }
      return;
    }
    const image = $("page-image");
    if (image.dataset.pageId !== state.pageId || !image.hasAttribute("src")) setImage();
    else {
      drawOverlay();
      const selected = state.page.fragments.find(fragment => fragment.id === state.selectedSource);
      if (selected) {
        state.imageFocus = selected.id;
        scrollToHighlight(selected);
      }
    }
  }

  function renderBoundaries() {
    const notice = $("boundary-notice");
    const bounds = state.page.boundaries || {};
    const start = bounds.start || bounds.start_boundary;
    const end = bounds.end || bounds.end_boundary;
    const uncertain = [start, end].some(b => b &&
      (Number(b.upper_char_offset0) - Number(b.lower_char_offset0) > 1 || /uncertain|bounded/.test(b.status || "")));
    notice.hidden = !uncertain;
    if (uncertain) notice.textContent = "Limite de página aproximado: confira os trechos junto às margens superior e inferior no fac-símile. O texto foi dividido pelo alinhamento do OCR.";
  }

  function associatedCitations(sourceId, page = state.page) {
    return page.citations.filter(c => (c.associations || []).some(a => a.source_id === sourceId));
  }

  function associationLabel(association) {
    if (association.suppressed_by_correction) return "proposta rejeitada";
    if (association.status === "reviewed") return "conferência assistida";
    if (association.status === "ambiguous") return "leitura ambígua";
    return "proposta";
  }

  function associationTarget(association, span = association.span) {
    const lineIds = span?.ocr_line_ids || association.ocr_line_ids || [];
    return {status: association.status, source_id: association.source_id,
      line_ids: lineIds, boxes: span?.ocr_boxes || [], source_span: span || null,
      source_form: association.source_form || span?.text || null,
      scope: span ? "form" : "fragment",
      mechanism: association.correction_id ? "correction_ledger" : association.algorithm_version ? "model_review_choice" : "reviewed_association",
      algorithm_version: association.algorithm_version || null, manual: true};
  }

  function paintSourceText(node) {
    const original = node._vlbSourceText ?? node.textContent;
    node._vlbSourceText = original;
    node.replaceChildren();
    const targets = (state.autoTarget?.source_spans || [state.autoTarget?.source_span]).filter(Boolean)
      .filter(target => target.start0 >= Number(node.dataset.start0) && target.end0 <= Number(node.dataset.end0))
      .sort((a, b) => a.start0 - b.start0);
    const article = node.closest(".fragment");
    const start0 = Number(node.dataset.start0);
    const end0 = Number(node.dataset.end0);
    if (!targets.length || article?.dataset.sourceId !== state.autoTarget.source_id ||
        targets.some(target => original.slice(target.start0 - start0, target.end0 - start0) !== target.text)) {
      node.textContent = original;
      return;
    }
    let cursor = 0;
    for (const target of targets) {
      const left = target.start0 - start0;
      const right = target.end0 - start0;
      if (left < cursor) continue;
      node.append(document.createTextNode(original.slice(cursor, left)));
      const mark = element("mark", "match-span", target.text);
      mark.title = state.autoTarget.status === "reviewed" ? "Expressão registrada na correção revisada." :
        "Expressão proposta nesta ocorrência; confirme-a no fac-símile.";
      node.append(mark);
      cursor = right;
    }
    node.append(document.createTextNode(original.slice(cursor)));
  }

  function refreshSourceSpanMarks() {
    for (const node of document.querySelectorAll(".source-text")) paintSourceText(node);
  }

  function syncSearchResultSelection() {
    for (const result of document.querySelectorAll(".search-result")) {
      const selected = Boolean(state.selectedSource) && result.dataset.sourceId === state.selectedSource &&
        result.dataset.pageId === state.pageId;
      result.classList.toggle("selected", selected);
      if (selected) result.setAttribute("aria-current", "location");
      else result.removeAttribute("aria-current");
    }
  }

  function clearSourceSelection({originPane = null, update = true} = {}) {
    const position = state.mode === "continuous" && originPane ? flowPosition(originPane) : null;
    const view = position && flow.views.get(position.id);
    if (view) {
      state.page = view.page;
      state.pageId = view.page.id;
    }
    const correctionCitation = state.correctionDraft?.page_id === state.pageId ?
      state.page.citations.find(citation => citation.id === state.correctionDraft.citation_id)?.id || null : null;
    state.selectedSource = state.autoTarget = state.imageFocus = null;
    flow.imageAnchorId = null;
    state.selectedCitation = correctionCitation;
    if (!correctionCitation) state.entry = null;
    state.citationEntryFilter = null;
    $("citation-detail").hidden = true;
    $("citation-choice-notice").hidden = true;
    $("citation-filter").value = "";
    refreshSourceSpanMarks();
    for (const article of $("fragment-list").querySelectorAll(".fragment")) {
      article.classList.remove("selected");
      article.querySelector(".source-main")?.setAttribute("aria-pressed", "false");
      for (const extra of article.querySelectorAll(".fragment-actions")) extra.hidden = true;
    }
    for (const flowView of flow.views.values()) flowView.overlay.replaceChildren();
    if (state.mode === "continuous") {
      setPageControls();
      renderPage();
    } else {
      drawOverlay();
      renderCitations();
    }
    updateNoteTarget();
    updatePageStatus();
    syncSearchResultSelection();
    if (position) {
      flow.position = position;
      const other = originPane === "scan" ? "text" : "scan";
      if (paneVisible(other)) syncFlowPane(other, position);
    }
    if (update) updateURL();
  }

  function toggleSourceSelection(page, source, {originPane, revealText = false} = {}) {
    const same = state.pageId === page.id && state.selectedSource === source.id;
    if (same) {
      clearSourceSelection({originPane});
      return;
    }
    if (state.mode === "continuous" && state.pageId !== page.id) {
      lockFlow(originPane, 700);
      activateFlowPage(page.id, {update: false});
    }
    if (revealText && state.narrow) setTranscriptionMinimized(false, {focus: false});
    selectSource(source.id, revealText ? {revealText: true} : {});
  }

  function renderFragments(page = state.page, list = $("fragment-list"), continuous = false) {
    list.replaceChildren();
    if (!page.fragments.length) {
      list.append(element("p", "empty-state", page.image_index === 25 ?
        "Esta posição contém a reprodução de uma página do manuscrito. A transcrição lexical retoma na página 27." :
        "Verso em branco da prancha. Não há verbetes para alinhar nesta posição."));
      return;
    }
    for (const source of page.fragments) {
      const article = element("article", "fragment" + (source.kind === "heading" ? " heading" : ""));
      article.dataset.sourceId = source.id;
      article.dataset.pageId = page.id;
      article.id = continuous ? `source-${page.id}-${source.source_line}` : `source-${source.source_line}`;
      if (source.continues_from_previous) article.append(element("span", "continuation", "↳ Continuação da página anterior"));
      const button = action("", "source-main", () => {
        toggleSourceSelection(page, source, {originPane: "text"});
      });
      button.setAttribute("aria-label", `Selecionar parágrafo ${source.source_line}: ${compact(source.text, 110)}`);
      button.setAttribute("aria-pressed", "false");
      const sourceText = element("span", "source-text", source.text);
      sourceText.dataset.start0 = source.source_start0;
      sourceText.dataset.end0 = source.source_end0;
      sourceText._vlbSourceText = source.text;
      button.append(element("span", "source-number", `§ ${source.source_line}`), sourceText);
      paintSourceText(sourceText);
      article.append(button);
      if (source.continues_on_next) article.append(element("span", "continuation", "Continua na página seguinte ↗"));
      const actions = element("div", "fragment-actions");
      actions.hidden = true;
      const shareButton = action("Compartilhar ↗", "quiet-button", () => shareSourceCitation(source, page));
      shareButton.title = "Compartilhar a linha, a referência do VLB e um link direto";
      actions.append(shareButton);
      const citations = associatedCitations(source.id, page);
      if (citations.length) actions.append(action(`Ver no Navarro (${citations.length})`, "quiet-button", () => {
        if (continuous) {
          lockFlow("text", 700);
          activateFlowPage(page.id, {update: false});
        }
        renderCitations();
        setTab("citations");
      }));
      actions.append(action("Anotar diferença", "quiet-button note-action", () => {
        if (continuous) {
          lockFlow("text", 700);
          activateFlowPage(page.id, {update: false});
        }
        selectSource(source.id); setTab("notes"); $("note-text").focus();
      }));
      if (!citations.length) actions.append(element("span", "muted", "Nenhuma associação proposta neste trecho"));
      article.append(actions);
      list.append(article);
    }
  }

  function scrollTextToSource(id) {
    if (!paneVisible("text")) return;
    const article = fragmentContainer()?.querySelector(`[data-source-id="${CSS.escape(id)}"]`);
    if (!article) return;
    const viewport = $("text-viewport");
    if (state.mode === "continuous") lockFlow("text", 700);
    const view = state.mode === "continuous" ? flow.views.get(state.pageId) : null;
    const headingHeight = view?.text.querySelector(".continuous-page-heading")?.offsetHeight || 0;
    const articleBox = article.getBoundingClientRect();
    const viewportBox = viewport.getBoundingClientRect();
    const availableHeight = Math.max(0, viewport.clientHeight - headingHeight);
    const centeredOffset = Math.max(12, (availableHeight - Math.min(articleBox.height, availableHeight)) / 2);
    viewport.scrollTo({top: articleBox.top - viewportBox.top + viewport.scrollTop - headingHeight - centeredOffset,
      behavior: scrollBehavior()});
    state.surfaceScroll.text = viewport.scrollTop;
  }

  function selectSource(id, options = {}) {
    const source = state.page.fragments.find(f => f.id === id);
    if (!source) {
      announce("Este trecho não foi encontrado nesta página.");
      return;
    }
    const staleCitation = !options.preserveCitation && state.selectedSource !== id &&
      (state.selectedCitation || state.entry !== null || state.citationEntryFilter !== null);
    if (staleCitation) {
      state.selectedCitation = null;
      state.entry = null;
      $("citation-detail").hidden = true;
    }
    state.selectedSource = id;
    if (state.mode === "continuous") flow.imageAnchorId = state.pageId;
    state.autoTarget = options.target || null;
    state.citationEntryFilter = null;
    $("citation-choice-notice").hidden = true;
    refreshSourceSpanMarks();
    state.imageFocus = options.scroll === false ? null : id;
    if (state.mode === "continuous") manageFlowImages(state.pageId);
    for (const article of $("fragment-list").querySelectorAll(".fragment")) {
      const selected = article.dataset.sourceId === id && article.dataset.pageId === state.pageId;
      article.classList.toggle("selected", selected);
      article.querySelector(".source-main")?.setAttribute("aria-pressed", String(selected));
      if (article.querySelector(".fragment-actions")) article.querySelector(".fragment-actions").hidden = !selected;
    }
    if (options.revealText) {
      if (state.narrow) setTranscriptionMinimized(false, {focus: false});
      setTab("text");
    }
    if (options.scroll !== false && state.narrow && state.facsimileMinimized) {
      setFacsimileMinimized(false, {focus: false});
    }
    drawOverlay();
    renderCitations();
    updateNoteTarget();
    syncSearchResultSelection();
    if (options.update !== false) updateURL();
    if (options.scroll !== false) {
      if (options.revealText) scrollTextToSource(id);
      scrollToHighlight(source);
    }
  }

  function sourceBoxes(source) {
    if (state.autoTarget?.source_id === source?.id && state.autoTarget.boxes?.length) return state.autoTarget.boxes;
    if (state.autoTarget?.source_id === source?.id && state.autoTarget.line_ids?.length) {
      const ids = new Set(state.autoTarget.line_ids);
      return state.page.ocr_lines.filter(line => ids.has(line.id)).map(line => line.box);
    }
    if (state.autoTarget?.source_id === source?.id &&
        (state.autoTarget.source_span || state.autoTarget.source_spans?.length)) return [];
    if (Array.isArray(source?.ocr?.boxes)) return source.ocr.boxes;
    const lineIds = new Set(source?.ocr?.line_ids || []);
    return (state.page?.ocr_lines || [])
      .filter(line => lineIds.has(line.id) && Array.isArray(line.box))
      .map(line => line.box);
  }

  function sourceAtScanPoint(page, stage, event) {
    if (!page?.fragments?.length || !stage) return null;
    const bounds = stage.getBoundingClientRect();
    if (!bounds.width || !bounds.height) return null;
    const x = (event.clientX - bounds.left) / bounds.width;
    const y = (event.clientY - bounds.top) / bounds.height;
    const paddingX = Math.min(.025, 10 / bounds.width);
    const paddingY = Math.min(.012, 10 / bounds.height);
    const lines = new Map((page.ocr_lines || []).map(line => [line.id, line]));
    const candidates = [];
    for (const source of page.fragments) {
      for (const lineId of source.ocr?.line_ids || []) {
        const box = lines.get(lineId)?.box;
        if (!Array.isArray(box) || box.length !== 4 || box.some(value => !Number.isFinite(value))) continue;
        if (x < box[0] - paddingX || x > box[2] + paddingX || y < box[1] - paddingY || y > box[3] + paddingY) continue;
        const width = Math.max(.001, box[2] - box[0]);
        const height = Math.max(.001, box[3] - box[1]);
        const score = Math.abs(x - (box[0] + box[2]) / 2) / width +
          Math.abs(y - (box[1] + box[3]) / 2) / height;
        candidates.push({source, score});
      }
    }
    candidates.sort((left, right) => left.score - right.score || left.source.source_line - right.source.source_line);
    return candidates[0]?.source || null;
  }

  function bindScanStage(stage, pageProvider, continuous = false) {
    stage.classList.add("scan-interactive");
    stage.addEventListener("click", event => {
      if (event.button !== 0 || event.defaultPrevented || performance.now() < suppressScanClickUntil) return;
      const page = pageProvider();
      const source = sourceAtScanPoint(page, stage, event);
      if (!source) return;
      toggleSourceSelection(page, source, {originPane: "scan", revealText: true});
    });
  }

  function drawOverlay() {
    const overlay = activeScan()?.overlay;
    if (!overlay) return;
    overlay.replaceChildren();
    const source = state.page?.fragments.find(f => f.id === state.selectedSource);
    if (!source) {
      $("highlight-status").textContent = "Selecione um trecho da transcrição para localizar suas linhas no fac-símile.";
      return;
    }
    const boxes = sourceBoxes(source);
    $("highlight-status").textContent = boxes.length ?
      `§ ${source.source_line} · ${boxes.length} ${boxes.length === 1 ? "linha realçada" : "linhas realçadas"}${state.autoTarget?.status === "proposed" ? " · associação proposta" : ""} · posição aproximada pelo OCR${source.ocr.status === "partial" ? " (alinhamento parcial)" : ""}.` :
      `§ ${source.source_line} · o OCR não localizou linhas com segurança. Confira o trecho diretamente na imagem.`;
    if (!$("show-ocr").checked) return;
    for (const box of boxes) {
      if (!Array.isArray(box) || box.length !== 4 || box.some(n => !Number.isFinite(n))) continue;
      const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      rect.classList.add("source-highlight");
      rect.setAttribute("x", box[0] * 1000);
      rect.setAttribute("y", box[1] * 1000);
      rect.setAttribute("width", (box[2] - box[0]) * 1000);
      rect.setAttribute("height", (box[3] - box[1]) * 1000);
      overlay.append(rect);
    }
  }

  function scrollToHighlight(source) {
    const boxes = sourceBoxes(source);
    const viewport = $("scan-viewport");
    const scan = activeScan();
    if (!paneVisible("scan")) {
      state.imageFocus = source?.id || null;
      return;
    }
    if (!boxes.length || !scan?.image.complete || !scan.image.naturalWidth) return;
    const viewportBox = viewport.getBoundingClientRect();
    const stageBox = scan.stage.getBoundingClientRect();
    const stageTop = stageBox.top - viewportBox.top + viewport.scrollTop;
    const stageLeft = stageBox.left - viewportBox.left + viewport.scrollLeft;
    const top = stageTop + Math.min(...boxes.map(b => b[1])) * scan.stage.clientHeight;
    const bottom = stageTop + Math.max(...boxes.map(b => b[3])) * scan.stage.clientHeight;
    const left = stageLeft + Math.min(...boxes.map(b => b[0])) * scan.stage.clientWidth;
    const right = stageLeft + Math.max(...boxes.map(b => b[2])) * scan.stage.clientWidth;
    if (state.mode === "continuous") lockFlow("scan", 700);
    viewport.scrollTo({top: Math.max(0, (top + bottom) / 2 - viewport.clientHeight / 2),
      left: Math.max(0, (left + right) / 2 - viewport.clientWidth / 2), behavior: scrollBehavior()});
    state.surfaceScroll.scan = viewport.scrollTop;
    state.imageFocus = null;
  }

  function scrollBehavior() {
    return matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth";
  }

  function applyZoom({remember = false} = {}) {
    if (state.mode === "continuous") preserveFlowAnchors(() => {
      for (const view of flow.views.values()) view.stage.style.width = `${state.zoom}%`;
    });
    else $("scan-stage").style.width = `${state.zoom}%`;
    $("zoom-reset").textContent = `${state.zoom}%`;
    $("zoom-out").disabled = state.zoom <= MIN_ZOOM;
    $("zoom-in").disabled = state.zoom >= MAX_ZOOM;
    if (remember) {
      viewPreferences.zoom = state.zoom;
      saveViewPreferences();
    }
  }

  function setZoom(value, {remember = true} = {}) {
    state.zoom = Math.round(clamp(value, MIN_ZOOM, MAX_ZOOM));
    applyZoom({remember});
  }

  function rememberSplit(value) {
    if (state.narrow) viewPreferences.mobileTextShare = clamp(value, 18, 72);
    else viewPreferences.desktopTextShare = clamp(value, 28, 72);
    applySplitPreference();
  }

  function recenterReaderSelection() {
    if (!state.page) return;
    const selected = state.page.fragments.find(fragment => fragment.id === state.selectedSource);
    if (selected) {
      drawOverlay();
      scrollToHighlight(selected);
      if (paneVisible("text")) scrollTextToSource(selected.id);
    } else if (state.mode === "continuous" && flow.position?.id === state.pageId) {
      syncFlowPane("scan", flow.position);
      syncFlowPane("text", flow.position);
    }
  }

  function bindReaderSplitter() {
    const splitter = $("reader-splitter");
    let dragging = false;
    const update = event => {
      const box = document.querySelector(".workspace").getBoundingClientRect();
      const share = state.narrow ? (box.bottom - event.clientY) / box.height * 100 :
        (box.right - event.clientX) / box.width * 100;
      rememberSplit(share);
    };
    splitter.addEventListener("pointerdown", event => {
      if (event.button !== 0 || state.transcriptionMinimized || state.facsimileMinimized) return;
      dragging = true;
      splitter.classList.add("dragging");
      document.body.classList.add("reader-resizing");
      splitter.setPointerCapture(event.pointerId);
      event.preventDefault();
      update(event);
    });
    splitter.addEventListener("pointermove", event => {
      if (!dragging) return;
      event.preventDefault();
      update(event);
    });
    const finish = event => {
      if (!dragging) return;
      dragging = false;
      splitter.classList.remove("dragging");
      document.body.classList.remove("reader-resizing");
      if (splitter.hasPointerCapture?.(event.pointerId)) splitter.releasePointerCapture(event.pointerId);
      saveViewPreferences();
      requestAnimationFrame(recenterReaderSelection);
    };
    splitter.addEventListener("pointerup", finish);
    splitter.addEventListener("pointercancel", finish);
    splitter.addEventListener("dblclick", () => {
      rememberSplit(state.narrow ? 31 : 50);
      saveViewPreferences();
      requestAnimationFrame(recenterReaderSelection);
    });
    splitter.addEventListener("keydown", event => {
      const minimum = state.narrow ? 18 : 28;
      let value = state.narrow ? viewPreferences.mobileTextShare : viewPreferences.desktopTextShare;
      if (event.key === "Home") value = minimum;
      else if (event.key === "End") value = 72;
      else if (state.narrow && event.key === "ArrowUp") value += 2;
      else if (state.narrow && event.key === "ArrowDown") value -= 2;
      else if (!state.narrow && event.key === "ArrowLeft") value += 2;
      else if (!state.narrow && event.key === "ArrowRight") value -= 2;
      else return;
      event.preventDefault();
      rememberSplit(value);
      saveViewPreferences();
      requestAnimationFrame(recenterReaderSelection);
    });
  }

  function bindPinchZoom() {
    const viewport = $("scan-viewport");
    let gesture = null;
    const points = touches => Array.from(touches).slice(0, 2).map(touch => ({x: touch.clientX, y: touch.clientY}));
    const measure = pair => Math.hypot(pair[0].x - pair[1].x, pair[0].y - pair[1].y);
    const midpoint = pair => ({x: (pair[0].x + pair[1].x) / 2, y: (pair[0].y + pair[1].y) / 2});
    viewport.addEventListener("touchstart", event => {
      if (event.touches.length !== 2) return;
      event.preventDefault();
      const pair = points(event.touches);
      const center = midpoint(pair);
      const box = viewport.getBoundingClientRect();
      gesture = {distance: Math.max(1, measure(pair)), zoom: state.zoom,
        scrollLeft: viewport.scrollLeft, scrollTop: viewport.scrollTop,
        centerX: center.x - box.left, centerY: center.y - box.top};
      suppressScanClickUntil = performance.now() + 800;
    }, {passive: false});
    viewport.addEventListener("touchmove", event => {
      if (!gesture || event.touches.length < 2) return;
      event.preventDefault();
      const pair = points(event.touches);
      const center = midpoint(pair);
      const box = viewport.getBoundingClientRect();
      const nextZoom = clamp(gesture.zoom * measure(pair) / gesture.distance, MIN_ZOOM, MAX_ZOOM);
      setZoom(nextZoom, {remember: false});
      const ratio = state.zoom / gesture.zoom;
      viewport.scrollLeft = Math.max(0, (gesture.scrollLeft + gesture.centerX) * ratio - (center.x - box.left));
      viewport.scrollTop = Math.max(0, (gesture.scrollTop + gesture.centerY) * ratio - (center.y - box.top));
      suppressScanClickUntil = performance.now() + 800;
    }, {passive: false});
    const finish = event => {
      if (!gesture || event.touches.length >= 2) return;
      gesture = null;
      viewPreferences.zoom = state.zoom;
      saveViewPreferences();
      suppressScanClickUntil = performance.now() + 500;
    };
    viewport.addEventListener("touchend", finish, {passive: true});
    viewport.addEventListener("touchcancel", finish, {passive: true});
  }

  function dictionaryLink(cite) {
    const url = new URL("../", location.href);
    url.searchParams.set("query", cite.headword);
    return url.href;
  }

  function citationTitle(cite) {
    return `${cite.headword}${cite.homonym ? " " + cite.homonym : ""}`;
  }

  function addAssociationButtons(parent, cite) {
    const associations = cite.associations || [];
    const correctionPrimary = ["accepted", "ambiguous"].includes(cite.correction?.disposition);
    const primaryAssociations = correctionPrimary ?
      associations.filter(association => association.correction_event_id === cite.correction.event_id) : associations;
    const selectAssociation = (assoc, span = assoc.span) => {
      const target = associationTarget(assoc, span);
      state.selectedCitation = cite.id;
      state.entry = cite.entry_index;
      selectSource(assoc.source_id, {update: false, target, revealText: true, preserveCitation: true});
      showCitationDetail(cite, target);
      renderCitations();
      updateURL();
    };
    for (const assoc of primaryAssociations) {
      const source = state.page.fragments.find(f => f.id === assoc.source_id);
      const attested = assoc.span?.text || assoc.source_form;
      const text = `§ ${source?.source_line || assoc.source_line || "?"} · ${associationLabel(assoc)}${attested ? `: ${compact(attested, 45)}` : ""}`;
      const button = action(text, `chip ${assoc.status === "reviewed" ? "reviewed" : "proposed"}`, () => selectAssociation(assoc));
      button.title = assoc.status === "reviewed" ?
        (assoc.reviewer_type === "human" ? "Conferência humana, limitada à forma citada." :
          assoc.reviewer_type === "assistant" ? "Conferência por assistente, limitada à forma citada; revisão humana ainda disponível." :
            "Conferência registrada, limitada à forma citada; consulte a procedência da revisão.") :
        "Candidato automático: conferir a correspondência entre o trecho e a citação.";
      if (source) button.title += ` ${compact(source.text, 180)}`;
      parent.append(button);
    }
    const modelAssociations = associations.filter(assoc => assoc.algorithm_version);
    if (modelAssociations.length) {
      const details = element("details", "candidate-evidence");
      details.append(element("summary", "", "Ver alternativas e evidências"));
      for (const assoc of modelAssociations) {
        const evidence = assoc.evidence || {};
        const block = element("div", "candidate-evidence-item");
        block.append(element("strong", "", `Opção ${assoc.rank} · § ${assoc.source_line}`));
        for (const span of [assoc.span, ...(assoc.span_alternatives || [])].filter(Boolean)) {
          const button = action(`“${compact(span.text, 60)}”`, "quiet-button", () => selectAssociation(assoc, span));
          button.title = span.ocr_status === "form_token_match" ? "Selecionar esta ocorrência e suas linhas de OCR." :
            "Selecionar esta ocorrência; o OCR disponível é aproximado.";
          block.append(button);
        }
        const signals = [];
        if (evidence.quoted_surface) signals.push("expressão citada");
        if (evidence.portuguese_context_score > 0) signals.push("contexto de sentido");
        if (evidence.local_companion_count) signals.push("palavras acompanhantes");
        const notes = [];
        if (signals.length) notes.push(`apoio: ${signals.join(", ")}`);
        if (Number.isFinite(assoc.score)) notes.push(`ordenação ${assoc.score.toFixed(2)} (não é probabilidade)`);
        if (assoc.review_reasons?.length) notes.push(`revisão necessária: ${assoc.review_reasons.join(", ")}`);
        if (notes.length) block.append(element("small", "muted", notes.join(" · ")));
        details.append(block);
      }
      parent.append(details);
    }
    if (!primaryAssociations.length) parent.append(element("span", "muted", "Página localizada · trecho ainda não associado"));
  }

  function renderCitations() {
    const list = $("citation-list");
    list.replaceChildren();
    const query = fold($("citation-filter").value);
    const contextual = state.citationEntryFilter !== null ?
      state.page.citations.filter(c => c.entry_index === state.citationEntryFilter) :
      state.selectedSource ? state.page.citations.filter(c => (c.associations || []).some(a => a.source_id === state.selectedSource)) :
        state.selectedCitation ? state.page.citations.filter(c => c.id === state.selectedCitation) : [];
    $("citation-count").textContent = contextual.length;
    const citations = contextual.filter(c => !query || fold(`${c.headword} ${c.context} ${c.raw_citation}`).includes(query));
    if (!citations.length) {
      const message = query && contextual.length ? "Nenhuma citação corresponde a este filtro." :
        state.selectedSource ? "Este trecho não tem uma referência de Navarro associada." :
          state.citationEntryFilter !== null || state.selectedCitation ? "Esta referência não tem uma ocorrência disponível nesta página." :
            state.page.citations.length ? "Selecione um trecho da transcrição para consultar suas referências de Navarro." :
              "Não há referências de Navarro a esta página no conjunto de dados consultado. Isso não demonstra que seus verbetes estejam ausentes do dicionário.";
      list.append(element("p", "empty-state", message));
      return;
    }
    for (const cite of citations) {
      const card = element("article", `citation-card${cite.id === state.selectedCitation ? " selected" : ""}`);
      card.dataset.citationId = cite.id;
      const heading = element("div", "citation-title");
      heading.append(action(citationTitle(cite), "", () => {
        const preserveTarget = cite.id === state.selectedCitation && state.autoTarget?.source_id === state.selectedSource;
        selectCitation(cite.id, preserveTarget ? {source: state.selectedSource, target: state.autoTarget} : {});
      }), element("small", "citation-reference", cite.raw_citation));
      if (cite.adapted) heading.append(element("span", "chip", "citação adaptada"));
      card.append(heading, element("p", "", compact(cite.context, 350)));
      const associations = element("div", "associations");
      addAssociationButtons(associations, cite);
      card.append(associations);
      list.append(card);
    }
  }

  function selectCitation(id, options = {}) {
    const cite = state.page.citations.find(c => c.id === id);
    if (!cite) { announce("Esta ocorrência de citação não foi encontrada nesta página."); return; }
    state.selectedCitation = id;
    state.entry = cite.entry_index;
    state.autoTarget = null;
    let routedTarget = null;
    if (options.source && Number.isInteger(options.targetStart) && Number.isInteger(options.targetEnd)) {
      for (const association of cite.associations || []) {
        if (association.source_id !== options.source) continue;
        const span = [association.span, ...(association.span_alternatives || [])].filter(Boolean)
          .find(candidate => candidate.start0 === options.targetStart && candidate.end0 === options.targetEnd);
        if (span) { routedTarget = associationTarget(association, span); break; }
      }
    }
    const shouldResolveAuto = options.autoFocus === true ||
      (options.autoFocus !== false && !options.source);
    const resolvedAuto = !options.target && !routedTarget && shouldResolveAuto ?
      window.VLBCitationTargets?.choose(cite, state.page) : null;
    // Shared automatic routes retain both source= and focus=auto. Recompute the
    // current production decision after reload or a mode change, but never pin
    // its exact span/OCR evidence to a different routed paragraph.
    const compatibleAuto = !options.source || resolvedAuto?.source_id === options.source ? resolvedAuto : null;
    const target = options.target || routedTarget || compatibleAuto;
    if (options.source) selectSource(options.source, {update: false, target, revealText: true, preserveCitation: true});
    else if (target?.source_id) selectSource(target.source_id, {update: false, target, revealText: true, preserveCitation: true});
    else {
      state.selectedSource = null;
      state.autoTarget = null;
      refreshSourceSpanMarks();
      for (const article of $("fragment-list").querySelectorAll(".fragment.selected")) {
        article.classList.remove("selected");
        article.querySelector(".source-main")?.setAttribute("aria-pressed", "false");
        for (const extra of article.querySelectorAll(".fragment-actions")) extra.hidden = true;
      }
      drawOverlay();
      if (options.showTab !== false) setTab("citations");
    }
    if (options.showDetail !== false) showCitationDetail(cite, target);
    renderCitations();
    updateNoteTarget();
    syncSearchResultSelection();
    if (options.update !== false) updateURL();
  }

  function showCitationDetail(cite, target = state.autoTarget) {
    const detail = $("citation-detail");
    detail.replaceChildren();
    detail.hidden = false;
    const top = element("div", "detail-top");
    const title = element("h3", "");
    title.append(externalLink(citationTitle(cite) + " ↗", dictionaryLink(cite)));
    const detailActions = element("div", "detail-actions");
    detailActions.append(action("Corrigir correspondência", "quiet-button", () => startCorrection(cite)),
      action("Fechar ×", "quiet-button close-detail", () => {
      state.selectedCitation = null;
      state.entry = null;
      state.autoTarget = null;
      refreshSourceSpanMarks();
      detail.hidden = true;
      drawOverlay();
      renderCitations();
      updateNoteTarget();
      updateURL();
    }));
    top.append(title, detailActions);
    detail.append(top, element("p", "citation-reference", `${cite.raw_citation} · ocorrência no dicionário${cite.adapted ? " · citação adaptada" : ""}`),
      element("p", "", cite.context));
    if (cite.correction) {
      const labels = {accepted:"aceita",rejected:"rejeitada",ambiguous:"ambígua",not_found:"não encontrada",unresolved:"não resolvida"};
      detail.append(element("p", "auto-target-notice reviewed",
        `Correção ${labels[cite.correction.disposition] || cite.correction.disposition}, revisão ${cite.correction.revision}, por ${cite.correction.reviewer}. ${cite.correction.notes}`));
    }
    if (target?.source_id) {
      const reviewed = target.status === "reviewed";
      const ambiguous = target.status === "ambiguous";
      const message = reviewed ? `Trecho localizado por conferência assistida${target.source_form ? `: ${target.source_form}` : ""}. O realce do OCR é aproximado.` :
        ambiguous ? "Leitura preservada como ambígua na correção: este é um dos trechos defensáveis, não uma associação aceita." :
          "Associação proposta: trecho localizado automaticamente pela forma e pelo contexto disponíveis. Confira a leitura e o sentido no fac-símile.";
      detail.append(element("p", `auto-target-notice ${reviewed ? "reviewed" : ambiguous ? "ambiguous" : "proposed"}`, message));
    } else if (target) detail.append(element("p", "muted", target.status === "ambiguous" ?
      "Mais de um trecho é possível. Escolha uma das propostas abaixo para conferir a linha." :
      "Não há evidência suficiente para localizar uma linha automaticamente. Confira as propostas e a página."));
    const associations = element("div", "associations");
    addAssociationButtons(associations, cite);
    detail.append(associations);
  }

  function setTab(tab, focus = false) {
    const previous = state.tab;
    state.tab = tab;
    for (const name of ["text", "citations", "notes"]) {
      const selected = name === tab;
      $(`${name}-tab`).setAttribute("aria-selected", String(selected));
      $(`${name}-tab`).tabIndex = selected ? 0 : -1;
      $(`${name}-content`).hidden = !selected;
    }
    if (focus) $(`${tab}-tab`).focus();
    if (tab === "notes") updateNoteTarget();
    if (state.mode === "continuous" && tab === "text" && previous !== "text" && !state.selectedSource) {
      const position = flowPosition("scan");
      if (position) syncFlowPane("text", position);
    }
  }

  async function ensureSearchIndex() {
    if (state.searchIndex && state.orthographyModel) return;
    if (!window.VLBSearch) throw new Error("O mecanismo de busca não foi carregado. Recarregue a página.");
    const [sources, orthographyModel] = await Promise.all([
      readJSON(`data/${state.manifest.source_index_file || "source-index.json.gz"}`),
      readJSON(`data/${state.manifest.orthography_model_file || "orthography-model.json"}`),
    ]);
    state.sourceIndex = Array.isArray(sources) ? sources : sources.entries || sources.sources || sources.paragraphs || [];
    state.orthographyModel = orthographyModel;
    state.searchIndex = window.VLBSearch.buildIndex(state.sourceIndex);
  }

  async function search(event) {
    event?.preventDefault();
    const query = $("search-input").value.trim();
    const token = ++state.searchToken;
    if (!query) { $("search-results").hidden = true; return; }
    $("search-results").hidden = false;
    $("search-heading").textContent = "Buscando…";
    $("search-result-list").replaceChildren();
    try {
      await ensureSearchIndex();
      if (token !== state.searchToken) return;
      const found = window.VLBSearch.search(state.searchIndex, query, state.orthographyModel, {limit: 100});
      const count = found.total;
      $("search-heading").textContent = `${count.toLocaleString("pt-BR")} ${count === 1 ? "resultado na transcrição" : "resultados na transcrição"}`;
      for (const result of found.results) {
        const data = result.source;
        const first = result.pageId;
        const button = action("", "search-result", () => {
          if (!first || !metadata(first)) { announce("Este trecho não tem uma página válida na transcrição."); return; }
          if (state.narrow) {
            setTranscriptionMinimized(false, {focus: false});
            setFacsimileMinimized(false, {focus: false});
          }
          loadPage(first, {push: true, source: data.id || data.source_id});
        });
        button.dataset.sourceId = result.sourceId;
        button.dataset.pageId = first || "";
        button.dataset.matchScope = result.scope;
        button.dataset.queryPath = result.queryPath;
        button.append(element("span", "result-kind", result.label),
          element("strong", "", compact(data.text, 170)));
        const pages = data.page_ids || [];
        const explanation = result.queryPath === "orthography-model" ?
          `Forma histórica localizada: ${result.matchedForm} · correspondência provável de busca, não identidade lexical` :
          `§ ${data.source_line} · ${result.scope === "whole" ? "palavra ou expressão inteira" : "mesma grafia dentro de palavra"}`;
        button.append(element("small", "", `${explanation} · ${pages.join(" / ")}`));
        $("search-result-list").append(button);
      }
      if (!count) $("search-result-list").append(element("p", "empty-state", "Nenhuma ocorrência encontrada na transcrição. A busca preserva acentos e nasalização; tente a grafia portuguesa, a grafia do VLB ou uma forma de Navarro."));
      if (count > found.results.length) $("search-result-list").append(element("p", "muted", `Mostrando ${found.results.length.toLocaleString("pt-BR")} resultados. Use mais letras ou palavras para refinar a busca.`));
      syncSearchResultSelection();
    } catch (error) {
      $("search-heading").textContent = "A busca não pôde ser carregada";
      $("search-result-list").append(element("p", "", error.message));
    }
  }

  function readCorrections() {
    try {
      const saved = JSON.parse(localStorage.getItem(CORRECTION_KEY) || "[]");
      state.corrections = Array.isArray(saved) ? saved.filter(row => row?.schema_version === 1 && typeof row.event_id === "string") : [];
    } catch { state.corrections = []; }
  }

  function closeCorrection({restoreDetail = true} = {}) {
    state.correctionDraft = null;
    document.body.classList.remove("correction-open");
    $("correction-panel").hidden = true;
    $("correction-feedback").textContent = "";
    window.getSelection()?.removeAllRanges();
    if (restoreDetail && state.selectedCitation) {
      const cite = state.page?.citations.find(row => row.id === state.selectedCitation);
      if (cite) showCitationDetail(cite, state.autoTarget);
    }
  }

  function startCorrection(cite) {
    setTranscriptionMinimized(false, {focus: false});
    const lineMap = new Map(state.page.ocr_lines.map(line => [line.id, line]));
    const local = state.corrections
      .filter(event => event.citation?.citation_id === cite.id && event.page?.page_id === state.pageId)
      .sort((a, b) => b.revision - a.revision)[0];
    const spans = local ? JSON.parse(JSON.stringify(local.selected_spans)) :
      (cite.correction ? cite.associations || [] : [])
        .filter(association => association.correction_event_id === cite.correction?.event_id && association.span)
        .map(association => ({source_id:association.source_id,start0:association.span.start0,end0:association.span.end0,
          text:association.span.text,ocr_targets:(association.span.ocr_line_ids || []).filter(id => lineMap.has(id)).map(id => ({
            line_id:id,box:lineMap.get(id).box,box_source:"pinned_ocr",previous_box:null}))}));
    state.correctionDraft = {citation_id: cite.id, page_id: state.pageId, spans};
    document.body.classList.add("correction-open");
    $("citation-detail").hidden = true;
    $("correction-panel").hidden = false;
    $("correction-target").textContent = `${citationTitle(cite)} · ${cite.raw_citation} · VLB ${pageLabel()}`;
    $("correction-disposition").value = local?.disposition || cite.correction?.disposition || "accepted";
    $("correction-reviewer").value = local?.review?.reviewer || "Leitor do VLB";
    $("correction-notes").value = local?.review?.notes || "";
    $("correction-feedback").textContent = "Selecione a expressão exata na transcrição e use “Adicionar seleção atual”.";
    renderCorrectionSpans();
    setTab("text");
    if (state.narrow) setSurface("text", {explicit: true});
    $("correction-panel").scrollIntoView({block: "nearest"});
    $("correction-heading").tabIndex = -1;
    $("correction-heading").focus({preventScroll: true});
  }

  function renderCorrectionSpans() {
    const list = $("correction-spans");
    list.replaceChildren();
    for (const [index, span] of (state.correctionDraft?.spans || []).entries()) {
      const item = element("div", "correction-span");
      item.append(element("span", "", `§ ${span.source_id.slice(-5).replace(/^0+/, "")} · “${span.text}”`),
        action("Remover", "quiet-button", () => {
          state.correctionDraft.spans.splice(index, 1);
          renderCorrectionSpans();
        }));
      list.append(item);
    }
    if (!list.childElementCount) list.append(element("span", "muted", "Nenhuma passagem adicionada."));
  }

  function selectedCorrectionSpan() {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount !== 1 || selection.isCollapsed) throw new Error("Selecione primeiro as palavras exatas em um único trecho da transcrição.");
    const range = selection.getRangeAt(0);
    const startElement = range.startContainer.nodeType === Node.ELEMENT_NODE ? range.startContainer : range.startContainer.parentElement;
    const endElement = range.endContainer.nodeType === Node.ELEMENT_NODE ? range.endContainer : range.endContainer.parentElement;
    const sourceText = startElement?.closest?.(".source-text");
    if (!sourceText || sourceText !== endElement?.closest?.(".source-text") ||
        !sourceText.contains(range.startContainer) || !sourceText.contains(range.endContainer)) {
      throw new Error("A seleção deve ficar dentro de uma única passagem da transcrição.");
    }
    const article = sourceText.closest(".fragment");
    if (article?.dataset.pageId !== state.pageId) throw new Error("Selecione primeiro o trecho da página atualmente ativa.");
    const prefix = document.createRange();
    prefix.selectNodeContents(sourceText);
    prefix.setEnd(range.startContainer, range.startOffset);
    const raw = range.toString();
    const leading = raw.match(/^\s*/u)[0].length;
    const trailing = raw.match(/\s*$/u)[0].length;
    const text = raw.slice(leading, raw.length - trailing);
    if (!text) throw new Error("A seleção contém apenas espaços.");
    const fragmentStart = Number(sourceText.dataset.start0);
    const start0 = fragmentStart + prefix.toString().length + leading;
    const end0 = start0 + text.length;
    const original = sourceText._vlbSourceText ?? sourceText.textContent;
    if (original.slice(start0 - fragmentStart, end0 - fragmentStart) !== text) throw new Error("A seleção não corresponde mais ao texto preservado; recarregue a página.");
    const matchedTarget = (state.autoTarget?.source_spans || [state.autoTarget?.source_span]).filter(Boolean)
      .find(span => (span.source_id || state.autoTarget?.source_id) === article.dataset.sourceId &&
        span.start0 === start0 && span.end0 === end0 && span.text === text);
    const lineIds = matchedTarget?.ocr_line_ids || [];
    const lineMap = new Map(state.page.ocr_lines.map(line => [line.id, line]));
    const ocrTargets = lineIds.filter(id => lineMap.has(id)).map(id => ({line_id:id,
      box:lineMap.get(id).box,box_source:"pinned_ocr",previous_box:null}));
    return {source_id:article.dataset.sourceId,start0,end0,text,ocr_targets:ocrTargets};
  }

  function addCorrectionSpan() {
    try {
      if (!state.correctionDraft) throw new Error("Abra primeiro a correção de uma citação.");
      const span = selectedCorrectionSpan();
      if (!state.correctionDraft.spans.some(row => row.source_id === span.source_id && row.start0 === span.start0 && row.end0 === span.end0)) {
        state.correctionDraft.spans.push(span);
        state.correctionDraft.spans.sort((a, b) => a.start0 - b.start0);
      }
      renderCorrectionSpans();
      $("correction-feedback").textContent = "Passagem adicionada à correção ainda local.";
      window.getSelection()?.removeAllRanges();
    } catch (error) { $("correction-feedback").textContent = error.message; }
  }

  async function correctionId(citationId, pageIdValue) {
    const bytes = new TextEncoder().encode(`${citationId}\0${pageIdValue}`);
    const digest = await crypto.subtle.digest("SHA-256", bytes);
    return "vlb-correction-" + [...new Uint8Array(digest)].map(byte => byte.toString(16).padStart(2, "0")).join("").slice(0, 20);
  }

  function previousProposal(cite) {
    const association = (cite.associations || []).filter(row => row.algorithm_version)
      .sort((a, b) => (a.rank || 999) - (b.rank || 999))[0];
    if (!association) return null;
    const span = association.span;
    return {algorithm_version:association.algorithm_version,
      output_sha256:state.manifest.provenance.proposal_output_sha256,
      status:association.proposal_status,source_id:span ? association.source_id : null,
      start0:span?.start0 ?? null,end0:span?.end0 ?? null,text:span?.text ?? null};
  }

  async function buildCorrectionEvent() {
    const draft = state.correctionDraft;
    const cite = state.page?.citations.find(row => row.id === draft?.citation_id);
    if (!draft || !cite || draft.page_id !== state.pageId) throw new Error("A citação ou a página da correção mudou; abra a correção novamente.");
    const disposition = $("correction-disposition").value;
    const spans = draft.spans.map(span => JSON.parse(JSON.stringify(span)));
    if (disposition === "accepted" && !spans.length) throw new Error("Uma correção aceita precisa de pelo menos uma passagem exata.");
    if (disposition === "ambiguous" && spans.length < 2) throw new Error("Uma decisão ambígua precisa preservar pelo menos duas passagens.");
    if (["rejected", "not_found"].includes(disposition) && spans.length) throw new Error("Remova as passagens aceitas para registrar esta decisão.");
    const proposal = previousProposal(cite);
    if (disposition === "rejected" && !proposal) throw new Error("Não há proposta anterior identificada para rejeitar.");
    const reviewer = $("correction-reviewer").value.trim();
    const notes = $("correction-notes").value.trim();
    if (!reviewer || !notes) throw new Error("Informe o revisor e uma nota explicando a conferência.");
    const id = await correctionId(cite.id, state.pageId);
    const histories = state.corrections.filter(row => row.correction_id === id);
    const checked = cite.correction ? {revision:cite.correction.revision,event_id:cite.correction.event_id} : null;
    const local = histories.sort((a, b) => b.revision - a.revision)[0];
    const previous = local && (!checked || local.revision >= checked.revision) ? local : checked;
    const revision = (previous?.revision || 0) + 1;
    const provenance = state.manifest.provenance;
    return {schema_version:1,event_id:`${id}-r${String(revision).padStart(4,"0")}`,correction_id:id,
      revision,supersedes_event_id:previous?.event_id || null,recorded_at:new Date().toISOString(),
      citation:{citation_id:cite.id,entry_index:cite.entry_index,legacy_id:cite.legacy_id ?? null,
        headword:cite.headword,homonym:cite.homonym || "",definition_sha256:cite.definition_sha256,
        citation_start0:cite.citation_start,citation_end0:cite.citation_end},
      page:{page_id:state.pageId,volume:state.page.volume,printed_page:state.page.page},
      selected_spans:spans,disposition,previous_proposal:proposal,
      review:{reviewer_type:"human",reviewer,provenance:"Submitted through the static VLB reader; repository review pending.",notes,
        approved_for_regression:false,approved_for_training:false},
      snapshots:{source_text_sha256:provenance.source_text_sha256,dictionary_snapshot_sha256:provenance.dictionary_snapshot_sha256,
        citation_links_sha256:provenance.citation_links_sha256,page_alignment_sha256:provenance.page_alignment_sha256,
        ocr_layout_sha256:provenance.ocr_layout_sha256}};
  }

  function storeCorrection(event) {
    const existing = state.corrections.find(row => row.event_id === event.event_id);
    if (existing && JSON.stringify(existing) !== JSON.stringify(event)) throw new Error("Já existe uma correção local diferente com este identificador.");
    const next = existing ? state.corrections : [...state.corrections, event];
    localStorage.setItem(CORRECTION_KEY, JSON.stringify(next));
    state.corrections = next;
  }

  function correctionContent(event) {
    const {event_id, correction_id, revision, supersedes_event_id, recorded_at, ...content} = event;
    return JSON.stringify(content);
  }

  async function saveCorrection() {
    try {
      const event = await buildCorrectionEvent();
      storeCorrection(event);
      $("correction-feedback").textContent = `Correção ${event.event_id} salva somente neste navegador. Exporte ou envie para torná-la durável no repositório.`;
    } catch (error) { $("correction-feedback").textContent = error.message; }
  }

  function downloadJSON(value, filename) {
    const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2) + "\n"], {type:"application/json;charset=utf-8"}));
    const link = element("a");
    link.href = url; link.download = filename; document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function exportCorrections() {
    if (!state.corrections.length) { $("correction-feedback").textContent = "Não há correções locais para exportar."; return; }
    downloadJSON({schema_version:"vlb-correction-submission-1",events:state.corrections},
      `vlb-correcoes-${new Date().toISOString().slice(0,10)}.json`);
    $("correction-feedback").textContent = "Arquivo exportado. Ele ainda precisa ser importado e revisado no repositório.";
  }

  async function submitCorrection() {
    const issueWindow = window.open("about:blank", "_blank");
    if (issueWindow) issueWindow.opener = null;
    try {
      let event = await buildCorrectionEvent();
      const saved = state.corrections.find(row => row.event_id === event.supersedes_event_id);
      if (saved && correctionContent(saved) === correctionContent(event)) event = saved;
      storeCorrection(event);
      const cite = state.page.citations.find(row => row.id === event.citation.citation_id);
      const checkedRevision = cite?.correction?.revision || 0;
      const pending = state.corrections
        .filter(row => row.correction_id === event.correction_id && row.revision > checkedRevision)
        .sort((a, b) => a.revision - b.revision);
      const envelope = {schema_version:"vlb-correction-submission-1",events:pending};
      const url = new URL("https://github.com/kiansheik/nhe-enga/issues/new");
      url.searchParams.set("template", "vlb-correction.yml");
      url.searchParams.set("title", `[VLB] ${event.citation.headword} · ${event.page.page_id}`);
      url.searchParams.set("payload", JSON.stringify(envelope, null, 2));
      url.searchParams.set("notes", event.review.notes);
      if (!issueWindow) {
        downloadJSON(envelope, `vlb-correcao-${event.correction_id}.json`);
        $("correction-feedback").textContent = "O navegador bloqueou a nova aba. A correção foi baixada para envio manual; ela ainda não chegou ao repositório.";
      } else if (url.toString().length > MAX_ISSUE_PREFILL_URL_LENGTH) {
        downloadJSON(envelope, `vlb-correcao-${event.correction_id}.json`);
        url.searchParams.delete("payload");
        url.searchParams.delete("notes");
        issueWindow.location.replace(url.toString());
        $("correction-feedback").textContent = "A correção é grande demais para preencher a issue pela URL. O arquivo foi baixado: cole seu JSON no formulário aberto. Ela ainda não chegou ao repositório.";
      } else {
        issueWindow.location.replace(url.toString());
        $("correction-feedback").textContent = "A página da issue foi aberta. Conclua o envio no GitHub; abrir a página não confirma submissão nem importação.";
      }
    } catch (error) {
      issueWindow?.close();
      $("correction-feedback").textContent = error.message;
    }
  }

  async function importCorrections(file) {
    try {
      const value = JSON.parse(await file.text());
      if (value?.schema_version !== "vlb-correction-submission-1" || !Array.isArray(value.events)) throw new Error("Arquivo sem o envelope vlb-correction-submission-1.");
      const provenance = state.manifest.provenance;
      for (const event of value.events) {
        if (event?.schema_version !== 1 || event.snapshots?.source_text_sha256 !== provenance.source_text_sha256 ||
            event.snapshots?.dictionary_snapshot_sha256 !== provenance.dictionary_snapshot_sha256) throw new Error("A correção importada pertence a outra versão das fontes.");
        storeCorrection(event);
      }
      $("correction-feedback").textContent = `${value.events.length} correção(ões) importada(s) somente neste navegador; a validação rigorosa ocorre no repositório.`;
    } catch (error) { $("correction-feedback").textContent = error.message; }
  }

  function readNotes() {
    try {
      const saved = JSON.parse(localStorage.getItem(NOTE_KEY) || "[]");
      state.notes = Array.isArray(saved) ? saved.filter(n => n && typeof n.id === "string" && typeof n.text === "string") : [];
    } catch { state.notes = []; }
  }

  function updateNoteTarget() {
    if (!state.page) return;
    const source = state.page.fragments.find(f => f.id === state.selectedSource);
    const cite = state.page.citations.find(c => c.id === state.selectedCitation);
    $("note-target").textContent = `VLB ${pageLabel()}${source ? ` · § ${source.source_line}` : " · página inteira"}${cite ? ` · ${citationTitle(cite)}` : ""}`;
  }

  function renderNotes() {
    const notes = state.notes.filter(n => n.page_id === state.pageId);
    $("notes-count").textContent = notes.length;
    $("export-notes").disabled = !state.notes.length;
    $("note-list").replaceChildren();
    for (const note of notes) {
      const card = element("article", "note-card");
      const heading = element("div", "section-heading");
      const title = element("strong", "", `${noteKinds[note.kind] || "Observação"}${note.source_line ? ` · § ${note.source_line}` : ""}`);
      heading.append(title, action("Excluir", "quiet-button", () => {
        const remaining = state.notes.filter(n => n.id !== note.id);
        try { localStorage.setItem(NOTE_KEY, JSON.stringify(remaining)); }
        catch { announce("Não foi possível alterar o armazenamento deste navegador."); return; }
        state.notes = remaining;
        renderNotes();
      }));
      card.append(heading, element("p", "", note.text));
      if (note.citation_headword) card.append(element("span", "muted", `Citação: ${note.citation_headword}`));
      if (note.source_id) card.append(action("Ver trecho", "quiet-button", () =>
        selectSource(note.source_id, {revealText: true})));
      $("note-list").append(card);
    }
    if (!notes.length) $("note-list").append(element("p", "empty-state", "Nenhuma anotação nesta página."));
  }

  function saveNote(event) {
    event.preventDefault();
    const text = $("note-text").value.trim();
    if (!text || !state.page) return;
    const source = state.page.fragments.find(f => f.id === state.selectedSource);
    const cite = state.page.citations.find(c => c.id === state.selectedCitation);
    const note = {id: crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      created_at: new Date().toISOString(), page_id: state.pageId, volume: state.page.volume,
      printed_page: state.page.page, image_index: state.page.image_index,
      source_id: source?.id || null, source_line: source?.source_line || null,
      source_start0: source?.source_start0 ?? null, source_end0: source?.source_end0 ?? null,
      source_text_sha256: state.manifest.provenance.source_text_sha256,
      dictionary_snapshot_sha256: state.manifest.provenance.dictionary_snapshot_sha256,
      citation_id: cite?.id || null, citation_headword: cite?.headword || null,
      dictionary_entry_index: cite?.entry_index ?? null, kind: $("note-kind").value, text};
    const notes = [...state.notes, note];
    try { localStorage.setItem(NOTE_KEY, JSON.stringify(notes)); }
    catch { $("note-feedback").textContent = "O navegador não permitiu salvar. Copie o texto da anotação para guardá-lo."; return; }
    state.notes = notes;
    $("note-text").value = "";
    $("note-feedback").textContent = "Anotação salva neste navegador. Exporte para compartilhar.";
    renderNotes();
  }

  function exportNotes() {
    const payload = {schema_version: "vlb-review-notes-1", exported_at: new Date().toISOString(),
      source: location.origin + location.pathname, current_viewer_provenance: state.manifest.provenance,
      snapshot_note: "Each note records its own source and dictionary hashes. Older notes without hashes have unspecified snapshot provenance.", notes: state.notes};
    const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2) + "\n"], {type: "application/json;charset=utf-8"}));
    const a = element("a");
    a.href = url;
    a.download = `vlb-anotacoes-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function navigate(delta) {
    if (!state.page) return;
    const pages = allPages();
    const index = pages.findIndex(p => p.id === state.pageId);
    const next = pages[index + delta];
    if (next) loadPage(next.id, {push: true});
  }

  async function showAbout() {
    $("about-dialog").showModal();
    if ($("unresolved-list").childElementCount) return;
    try {
      const data = await readJSON("data/unresolved-citations.json");
      const records = Array.isArray(data) ? data : data.citations || data.records || [];
      for (const record of records) {
        const reason = record.locator_flags?.includes("page_number_outlier_requires_review") ? "número de página fora da edição consultada" : "volume ou página a conferir";
        $("unresolved-list").append(element("p", "", `${record.headword}: ${record.raw_citation} — ${reason}.`));
      }
    } catch { $("unresolved-list").append(element("p", "muted", "Não foi possível carregar a lista de referências pendentes.")); }
  }

  function bindEvents() {
    bindScanStage($("scan-stage"), () => state.page);
    bindReaderSplitter();
    bindPinchZoom();
    $("surface-text").addEventListener("click", () => setSurface("text", {explicit: true}));
    $("surface-scan").addEventListener("click", () => setSurface("scan", {explicit: true}));
    $("toggle-transcription").addEventListener("click", () =>
      setTranscriptionMinimized(!state.transcriptionMinimized, {remember: true}));
    $("toggle-facsimile").addEventListener("click", () =>
      setFacsimileMinimized(!state.facsimileMinimized, {remember: true}));
    $("toggle-search").addEventListener("click", () => setSearchOpen(!state.searchOpen, {focus: !state.searchOpen}));
    $("previous-page").addEventListener("click", () => navigate(-1));
    $("next-page").addEventListener("click", () => navigate(1));
    $("page-select").addEventListener("change", event => loadPage(event.target.value, {push: true}));
    $("volume-select").addEventListener("change", event => loadPage(pageId(event.target.value, event.target.value === "I" ? 17 : 7), {push: true}));
    $("mode-select").addEventListener("change", event => {
      if (!state.page) return;
      viewPreferences.mode = event.target.value === "continuous" ? "continuous" : "page";
      saveViewPreferences();
      const manualSpan = state.autoTarget?.manual ? state.autoTarget.source_span : null;
      loadPage(state.pageId, {push: true, mode: event.target.value, source: state.selectedSource,
        citation: state.selectedCitation, entry: state.entry,
        focus: Boolean(state.autoTarget && !state.autoTarget.manual),
        targetStart: manualSpan?.start0, targetEnd: manualSpan?.end0});
    });
    for (const pane of ["scan", "text"]) {
      const viewport = flowViewport(pane);
      viewport.addEventListener("scroll", () => {
        state.surfaceScroll[pane] = viewport.scrollTop;
        state.surfaceVisited[pane] = true;
        onFlowScroll(pane);
      }, {passive: true});
      for (const event of ["wheel", "touchstart", "pointerdown", "keydown"]) {
        viewport.addEventListener(event, () => { flow.lockedUntil[pane] = 0; state.imageFocus = null; }, {passive: true});
      }
    }
    $("zoom-in").addEventListener("click", () => setZoom(state.zoom + 25));
    $("zoom-out").addEventListener("click", () => setZoom(state.zoom - 25));
    $("zoom-reset").addEventListener("click", () => setZoom(100));
    $("show-ocr").addEventListener("change", () => {
      viewPreferences.showOcr = $("show-ocr").checked;
      saveViewPreferences();
      drawOverlay();
    });
    $("search-form").addEventListener("submit", search);
    $("search-input").addEventListener("keydown", event => {
      if (event.key !== "Escape" || !state.narrow) return;
      event.preventDefault();
      state.searchToken++;
      $("search-results").hidden = true;
      setSearchOpen(false);
      $("toggle-search").focus();
    });
    $("close-search").addEventListener("click", () => {
      state.searchToken++;
      $("search-results").hidden = true;
      if (state.narrow) { setSearchOpen(false); $("toggle-search").focus(); }
      else $("search-input").focus();
    });
    $("citation-filter").addEventListener("input", () => {
      state.citationEntryFilter = null;
      $("citation-choice-notice").hidden = true;
      renderCitations();
    });
    for (const tab of ["text", "citations", "notes"]) $(`${tab}-tab`).addEventListener("click", () => {
      if (state.narrow && state.transcriptionMinimized) setTranscriptionMinimized(false, {focus: false});
      setTab(tab);
    });
    document.querySelector(".tabs").addEventListener("keydown", event => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const tabs = ["text", "citations", "notes"];
      const next = event.key === "Home" ? 0 : event.key === "End" ? 2 : (tabs.indexOf(state.tab) + (event.key === "ArrowRight" ? 1 : 2)) % 3;
      if (state.narrow && state.transcriptionMinimized) setTranscriptionMinimized(false, {focus: false});
      setTab(tabs[next], true);
    });
    $("note-form").addEventListener("submit", saveNote);
    $("export-notes").addEventListener("click", exportNotes);
    $("close-correction").addEventListener("click", () => closeCorrection());
    $("add-correction-span").addEventListener("click", addCorrectionSpan);
    $("save-correction").addEventListener("click", saveCorrection);
    $("submit-correction").addEventListener("click", submitCorrection);
    $("export-corrections").addEventListener("click", exportCorrections);
    $("import-corrections").addEventListener("change", event => {
      const file = event.target.files?.[0];
      if (file) importCorrections(file);
      event.target.value = "";
    });
    $("about-button").addEventListener("click", showAbout);
    $("close-about").addEventListener("click", () => $("about-dialog").close());
    $("about-dialog").addEventListener("click", event => {
      if (event.target === $("about-dialog")) {
        const box = $("about-dialog").getBoundingClientRect();
        if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) $("about-dialog").close();
      }
    });
    $("copy-link").addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(location.href); announce("Link copiado com a página e a seleção atual."); }
      catch { announce("Copie o endereço da barra do navegador; ele contém a seleção atual."); }
    });
    window.addEventListener("popstate", () => { const route = routeFromURL(); loadPage(route.id, route); });
    narrowMedia.addEventListener("change", () => syncResponsiveUI());
    let resizeTimer;
    window.addEventListener("resize", () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        if (!state.page) return;
        if (state.selectedSource) {
          drawOverlay();
          const selected = state.page.fragments.find(fragment => fragment.id === state.selectedSource);
          if (selected) scrollToHighlight(selected);
          return;
        }
        if (state.mode !== "continuous") return;
        if (flow.position?.id === state.pageId) {
          syncFlowPane("scan", flow.position);
          syncFlowPane("text", flow.position);
        } else scrollFlowToPage(state.pageId);
      }, 100);
    });
    document.addEventListener("keydown", event => {
      if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey || /INPUT|SELECT|TEXTAREA|BUTTON/.test(event.target.tagName) || $("about-dialog").open) return;
      if (event.key === "ArrowLeft") { event.preventDefault(); navigate(-1); }
      if (event.key === "ArrowRight") { event.preventDefault(); navigate(1); }
    });
  }

  async function init() {
    readViewPreferences();
    state.zoom = viewPreferences.zoom;
    $("show-ocr").checked = viewPreferences.showOcr;
    setMode(viewPreferences.mode);
    applyZoom();
    bindEvents();
    syncResponsiveUI(true);
    readNotes();
    readCorrections();
    try {
      const [manifest, formats] = await Promise.allSettled([readJSON("data/manifest.json"), readJSON("../docs/primary_sources/image-formats.json")]);
      if (manifest.status === "rejected") throw manifest.reason;
      state.manifest = manifest.value;
      if (formats.status === "fulfilled" && [".jpg", ".jpeg", ".webp", ".png"].includes(formats.value.books?.vlb)) state.imageExtension = formats.value.books.vlb;
      $("snapshot-info").textContent = `${state.manifest.pages.length} páginas de texto, além da prancha e de seu verso. Transcrição do Google Docs, revisão 568; referências extraídas de uma versão identificada do conjunto de dados de Navarro. Os arquivos de dados preservam a procedência e os identificadores das fontes.`;
      const route = routeFromURL();
      await loadPage(route.id, route);
    } catch (error) {
      $("load-error").hidden = false;
      $("load-error").textContent = error.message;
      $("page-status").textContent = "A concordância não pôde ser carregada.";
    }
  }
  init();
})();
