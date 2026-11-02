/* VLB source concordance. Text is always inserted as text, never as HTML. */
"use strict";

(() => {
  const $ = id => document.getElementById(id);
  const state = {
    manifest: null, page: null, pageId: null, selectedSource: null,
    selectedCitation: null, entry: null, tab: "text", zoom: 100,
    imageExtension: ".png", sourceIndex: null, citationIndex: null,
    notes: [], loadToken: 0, searchToken: 0, cache: new Map(),
  };
  const NOTE_KEY = "nhe-enga-vlb-review-v1";
  const noteKinds = {transcription: "Transcrição", association: "Associação", pagination: "Paginação", other: "Observação"};
  let toastTimer;

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

  function pageLabel(page = state.page) {
    return page ? `${page.volume}, ${page.page}` : "";
  }

  function pageId(volume, page) {
    return `${volume}-${String(page).padStart(3, "0")}`;
  }

  function allPages() {
    // Plate and blank verso remain navigable even though they have no text file.
    const pages = [...state.manifest.pages];
    for (const slot of state.manifest.scan_slots || []) {
      if (![25, 26].includes(slot.image_index) || pages.some(p => p.image_index === slot.image_index)) continue;
      pages.push({id: pageId("I", slot.image_index), volume: "I", page: slot.image_index,
        pdf_page: slot.image_index, image_index: slot.image_index, kind: slot.kind});
    }
    return pages.sort((a, b) => a.image_index - b.image_index);
  }

  function metadata(id) {
    return allPages().find(p => p.id === id);
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
    if (state.selectedSource) url.searchParams.set("source", state.selectedSource);
    if (state.selectedCitation) url.searchParams.set("citation", state.selectedCitation);
    if (state.entry !== null) url.searchParams.set("entry", state.entry);
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
    return {id: pageId(volume, Number(number)), source: query.get("source"),
      citation: query.get("citation"), entry: entry !== null && /^\d+$/.test(entry) ? Number(entry) : null};
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
    const meta = metadata(id);
    if (!meta) {
      $("load-error").hidden = false;
      $("load-error").textContent = "Esta referência não corresponde a uma página disponível. Abrindo o início do volume I.";
      return loadPage("I-017", {...options, source: null, citation: null, preserveError: true});
    }
    $("page-status").textContent = `Carregando volume ${meta.volume}, página ${meta.page}…`;
    if (!options.preserveError) $("load-error").hidden = true;
    $("transcription-panel").setAttribute("aria-busy", "true");
    try {
      let data = state.cache.get(id);
      if (!data) {
        data = meta.data_file ? await readJSON(`data/${meta.data_file}`) :
          {...meta, fragments: [], citations: [], ocr_lines: [], boundaries: null};
        state.cache.set(id, data);
        if (state.cache.size > 10) state.cache.delete(state.cache.keys().next().value);
      }
      if (token !== state.loadToken) return;
      state.page = {...meta, ...data};
      state.pageId = id;
      state.selectedSource = null;
      state.selectedCitation = null;
      state.entry = options.entry ?? null;
      $("citation-filter").value = "";
      $("citation-detail").hidden = true;
      setPageControls();
      renderPage();
      if (options.citation) selectCitation(options.citation, {update: false, showTab: !options.source});
      else if (state.entry !== null) {
        const cite = state.page.citations.find(c => c.entry_index === state.entry);
        if (cite) selectCitation(cite.id, {update: false, showTab: true});
        else announce("Este verbete não tem uma ocorrência vinculada nesta página do conjunto de dados.");
      }
      if (options.source) selectSource(options.source, {update: false, scroll: true});
      else if (!state.selectedCitation) setTab("text");
      updateNoteTarget();
      updateURL(!!options.push);
      document.title = `VLB ${pageLabel()} · Nhe'enga`;
      $("page-status").textContent = state.page.fragments.length ?
        `Volume ${state.page.volume} · página impressa ${state.page.page} · imagem ${state.page.image_index} do PDF · ${state.page.citations.length} citações` :
        `Volume I · posição ${state.page.page} · ${state.page.image_index === 25 ? "prancha do manuscrito" : "verso em branco"}`;
    } catch (error) {
      if (token !== state.loadToken) return;
      $("load-error").hidden = false;
      $("load-error").textContent = `${error.message} Tente recarregar a página.`;
      $("page-status").textContent = "Não foi possível abrir esta página.";
    } finally {
      if (token === state.loadToken) $("transcription-panel").removeAttribute("aria-busy");
    }
  }

  function renderPage() {
    $("scan-page-label").textContent = `${state.page.volume} · ${state.page.page}`;
    $("text-count").textContent = state.page.fragments.length;
    $("citation-count").textContent = state.page.citations.length;
    const fragments = state.page.fragments;
    $("text-range").textContent = fragments.length ? `§ ${fragments[0].source_line}–${fragments.at(-1).source_line}` : "Sem texto lexical";
    setImage();
    renderFragments();
    renderCitations();
    renderNotes();
    renderBoundaries();
    $("text-viewport").scrollTop = 0;
  }

  function setImage() {
    const path = `../docs/primary_sources/vlb/${state.page.image_index}`;
    const img = $("page-image");
    $("image-message").hidden = false;
    $("image-message").textContent = "Carregando imagem…";
    img.alt = state.page.fragments.length ? `Fac-símile do VLB, volume ${state.page.volume}, página ${state.page.page}` :
      state.page.image_index === 25 ? "Prancha do manuscrito, entre as páginas 24 e 27 do volume I" : "Verso em branco da prancha, volume I";
    img.onload = () => {
      $("image-message").hidden = true;
      drawOverlay();
      const selected = state.page.fragments.find(f => f.id === state.selectedSource);
      if (selected) scrollToHighlight(selected);
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
    state.zoom = 100;
    applyZoom();
    drawOverlay();
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

  function associatedCitations(sourceId) {
    return state.page.citations.filter(c => (c.associations || []).some(a => a.source_id === sourceId));
  }

  function associationLabel(association) {
    return association.status === "reviewed" ? "conferência assistida" : "proposta";
  }

  function renderFragments() {
    const list = $("fragment-list");
    list.replaceChildren();
    if (!state.page.fragments.length) {
      list.append(element("p", "empty-state", state.page.image_index === 25 ?
        "Esta posição contém a reprodução de uma página do manuscrito. A transcrição lexical retoma na página 27." :
        "Verso em branco da prancha. Não há verbetes para alinhar nesta posição."));
      return;
    }
    for (const source of state.page.fragments) {
      const article = element("article", "fragment" + (source.kind === "heading" ? " heading" : ""));
      article.dataset.sourceId = source.id;
      article.id = `source-${source.source_line}`;
      if (source.continues_from_previous) article.append(element("span", "continuation", "↳ Continuação da página anterior"));
      const button = action("", "source-main", () => selectSource(source.id));
      button.setAttribute("aria-label", `Selecionar parágrafo ${source.source_line}: ${compact(source.text, 110)}`);
      button.setAttribute("aria-pressed", "false");
      button.append(element("span", "source-number", `§ ${source.source_line}`), element("span", "source-text", source.text));
      article.append(button);
      if (source.continues_on_next) article.append(element("span", "continuation", "Continua na página seguinte ↗"));
      const meta = element("div", "source-meta");
      if (source.boundary_uncertain) meta.append(element("span", "chip proposed", "página a conferir"));
      for (const cite of associatedCitations(source.id)) {
        const assoc = cite.associations.find(a => a.source_id === source.id);
        meta.append(action(`${cite.headword}${cite.homonym ? " " + cite.homonym : ""} · ${associationLabel(assoc)}${assoc.status === "reviewed" && assoc.source_form ? `: ${assoc.source_form}` : ""}`,
          `chip ${assoc.status === "reviewed" ? "reviewed" : "proposed"}`, () => selectCitation(cite.id, {source: source.id})));
      }
      article.append(meta);
      const actions = element("div", "fragment-actions");
      actions.hidden = true;
      actions.append(action("Anotar diferença", "quiet-button", () => { selectSource(source.id); setTab("notes"); $("note-text").focus(); }));
      const citeCount = associatedCitations(source.id).length;
      if (!citeCount) actions.append(element("span", "muted", "Nenhuma associação proposta neste trecho"));
      article.append(actions);
      const lines = ocrLinesFor(source);
      if (lines.length) {
        const details = element("details", "ocr-reading");
        details.hidden = true;
        details.append(element("summary", "", "Ver leitura do OCR neste trecho"), element("pre", "", lines.map(l => l.text).join("\n")));
        article.append(details);
      }
      list.append(article);
    }
  }

  function ocrLinesFor(source) {
    const ids = new Set(source?.ocr?.line_ids || []);
    return (state.page.ocr_lines || []).filter(line => ids.has(line.id));
  }

  function selectSource(id, options = {}) {
    const source = state.page.fragments.find(f => f.id === id);
    if (!source) {
      announce("Este trecho não foi encontrado nesta página.");
      return;
    }
    state.selectedSource = id;
    for (const article of $("fragment-list").children) {
      const selected = article.dataset.sourceId === id;
      article.classList.toggle("selected", selected);
      article.querySelector(".source-main")?.setAttribute("aria-pressed", String(selected));
      if (article.querySelector(".fragment-actions")) article.querySelector(".fragment-actions").hidden = !selected;
      if (article.querySelector(".ocr-reading")) article.querySelector(".ocr-reading").hidden = !selected;
    }
    setTab("text");
    drawOverlay();
    updateNoteTarget();
    if (options.update !== false) updateURL();
    if (options.scroll !== false) {
      const article = $("fragment-list").querySelector(`[data-source-id="${CSS.escape(id)}"]`);
      if (article) {
        const viewport = $("text-viewport");
        viewport.scrollTo({top: article.getBoundingClientRect().top - viewport.getBoundingClientRect().top + viewport.scrollTop - 12, behavior: scrollBehavior()});
      }
      scrollToHighlight(source);
    }
  }

  function sourceBoxes(source) {
    return source?.ocr?.boxes || ocrLinesFor(source).map(l => l.box);
  }

  function drawOverlay() {
    const overlay = $("ocr-overlay");
    overlay.replaceChildren();
    const source = state.page?.fragments.find(f => f.id === state.selectedSource);
    if (!source) {
      $("highlight-status").textContent = "Selecione um trecho da transcrição para localizar suas linhas no fac-símile.";
      return;
    }
    const boxes = sourceBoxes(source);
    $("highlight-status").textContent = boxes.length ?
      `§ ${source.source_line} · ${boxes.length} ${boxes.length === 1 ? "linha realçada" : "linhas realçadas"} · posição aproximada pelo OCR${source.ocr.status === "partial" ? " (alinhamento parcial)" : ""}.` :
      `§ ${source.source_line} · o OCR não localizou linhas com segurança. Confira o trecho diretamente na imagem.`;
    if (!$("show-ocr").checked) return;
    for (const box of boxes) {
      if (!Array.isArray(box) || box.length !== 4 || box.some(n => !Number.isFinite(n))) continue;
      const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
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
    if (!boxes.length || !$("page-image").complete) return;
    const top = Math.min(...boxes.map(b => b[1])) * $("scan-stage").clientHeight;
    viewport.scrollTo({top: Math.max(0, top - viewport.clientHeight * .27), behavior: scrollBehavior()});
  }

  function scrollBehavior() {
    return matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth";
  }

  function applyZoom() {
    $("scan-stage").style.width = `${state.zoom}%`;
    $("zoom-reset").textContent = `${state.zoom}%`;
    $("zoom-out").disabled = state.zoom <= 100;
    $("zoom-in").disabled = state.zoom >= 250;
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
    for (const assoc of associations) {
      const source = state.page.fragments.find(f => f.id === assoc.source_id);
      const text = `§ ${source?.source_line || assoc.source_line || "?"} · ${associationLabel(assoc)}${assoc.status === "reviewed" && assoc.source_form ? `: ${assoc.source_form}` : ""}`;
      const button = action(text, `chip ${assoc.status === "reviewed" ? "reviewed" : "proposed"}`, () => {
        state.selectedCitation = cite.id;
        showCitationDetail(cite);
        selectSource(assoc.source_id);
        renderCitations();
      });
      button.title = assoc.status === "reviewed" ? "Conferência por assistente, limitada à forma citada; revisão humana ainda disponível." :
        "Candidato automático: conferir a correspondência entre o trecho e a citação.";
      if (source) button.title += ` ${compact(source.text, 180)}`;
      parent.append(button);
    }
    if (!associations.length) parent.append(element("span", "muted", "Página localizada · trecho ainda não associado"));
  }

  function renderCitations() {
    const list = $("citation-list");
    list.replaceChildren();
    const query = fold($("citation-filter").value);
    const citations = state.page.citations.filter(c => !query || fold(`${c.headword} ${c.context} ${c.raw_citation}`).includes(query));
    if (!citations.length) {
      list.append(element("p", "empty-state", state.page.citations.length ? "Nenhuma citação corresponde a este filtro." :
        "Não há referências de Navarro a esta página no conjunto de dados consultado. Isso não demonstra que seus verbetes estejam ausentes do dicionário."));
      return;
    }
    for (const cite of citations) {
      const card = element("article", `citation-card${cite.id === state.selectedCitation ? " selected" : ""}`);
      card.dataset.citationId = cite.id;
      const heading = element("div", "citation-title");
      heading.append(action(citationTitle(cite), "", () => selectCitation(cite.id)), element("small", "citation-reference", cite.raw_citation));
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
    showCitationDetail(cite);
    renderCitations();
    if (options.source) selectSource(options.source, {update: false});
    else if (options.showTab !== false) setTab("citations");
    updateNoteTarget();
    if (options.update !== false) updateURL();
  }

  function showCitationDetail(cite) {
    const detail = $("citation-detail");
    detail.replaceChildren();
    detail.hidden = false;
    const top = element("div", "detail-top");
    const title = element("h3", "");
    title.append(externalLink(citationTitle(cite) + " ↗", dictionaryLink(cite)));
    top.append(title, action("Fechar ×", "quiet-button close-detail", () => {
      state.selectedCitation = null;
      state.entry = null;
      detail.hidden = true;
      renderCitations();
      updateNoteTarget();
      updateURL();
    }));
    detail.append(top, element("p", "citation-reference", `${cite.raw_citation} · ocorrência no dicionário${cite.adapted ? " · citação adaptada" : ""}`),
      element("p", "", cite.context));
    const associations = element("div", "associations");
    addAssociationButtons(associations, cite);
    detail.append(associations);
  }

  function setTab(tab, focus = false) {
    state.tab = tab;
    for (const name of ["text", "citations", "notes"]) {
      const selected = name === tab;
      $(`${name}-tab`).setAttribute("aria-selected", String(selected));
      $(`${name}-tab`).tabIndex = selected ? 0 : -1;
      $(`${name}-content`).hidden = !selected;
    }
    if (focus) $(`${tab}-tab`).focus();
    if (tab === "notes") updateNoteTarget();
  }

  async function ensureSearchIndexes() {
    if (state.sourceIndex && state.citationIndex) return;
    const [sources, citations] = await Promise.all([
      readJSON(`data/${state.manifest.source_index_file || "source-index.json.gz"}`),
      readJSON(`data/${state.manifest.citation_index_file || "citation-index.json.gz"}`),
    ]);
    state.sourceIndex = Array.isArray(sources) ? sources : sources.entries || sources.sources || sources.paragraphs || [];
    state.citationIndex = Array.isArray(citations) ? citations : citations.citations || citations.entries || [];
  }

  async function search(event) {
    event?.preventDefault();
    const query = fold($("search-input").value.trim());
    const token = ++state.searchToken;
    if (!query) { $("search-results").hidden = true; return; }
    $("search-results").hidden = false;
    $("search-heading").textContent = "Buscando…";
    $("search-result-list").replaceChildren();
    try {
      await ensureSearchIndexes();
      if (token !== state.searchToken) return;
      const words = query.split(/\s+/).filter(Boolean);
      const match = text => words.every(w => fold(text).includes(w));
      const citations = state.citationIndex.filter(c => match(`${c.headword} ${c.homonym || ""}`));
      const sources = state.sourceIndex.filter(s => match(s.text));
      const count = citations.length + sources.length;
      $("search-heading").textContent = `${count.toLocaleString("pt-BR")} ${count === 1 ? "resultado" : "resultados"}`;
      const results = [...citations.map(c => ({kind: "citation", data: c})), ...sources.map(s => ({kind: "source", data: s}))].slice(0, 100);
      for (const {kind, data} of results) {
        const ids = data.page_ids || data.pages || [];
        const matchingFragment = kind === "source" ? data.fragments?.find(fragment => match(fragment.text)) : null;
        const first = matchingFragment?.page_id || (typeof ids[0] === "string" ? ids[0] : ids[0]?.id || (ids[0] ? pageId(ids[0].volume, ids[0].page || ids[0].printed_page) : null));
        const button = action("", "search-result", () => {
          if (!first || !metadata(first)) { announce("Referência sem página válida. Veja as referências a corrigir em Sobre esta edição."); return; }
          $("search-results").hidden = true;
          loadPage(first, {push: true, source: kind === "source" ? data.id || data.source_id : null,
            citation: kind === "citation" ? data.id || data.citation_id : null,
            entry: kind === "citation" ? data.entry_index : null});
        });
        button.append(element("span", "result-kind", kind === "citation" ? "Navarro" : `Transcrição · § ${data.source_line}`),
          element("strong", "", kind === "citation" ? citationTitle(data) : compact(data.text, 150)));
        button.append(element("small", "", kind === "citation" ? `${data.raw_citation || ""} · ${ids.join(" / ") || "referência pendente"}` : ids.join(" / ")));
        $("search-result-list").append(button);
      }
      if (!count) $("search-result-list").append(element("p", "empty-state", "Nenhuma ocorrência encontrada. A busca ignora acentos, mas preserva diferenças de grafia histórica."));
      if (count > 100) $("search-result-list").append(element("p", "muted", "Mostrando os primeiros 100 resultados. Use mais palavras para refinar a busca."));
    } catch (error) {
      $("search-heading").textContent = "A busca não pôde ser carregada";
      $("search-result-list").append(element("p", "", error.message));
    }
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
      if (note.source_id) card.append(action("Ver trecho", "quiet-button", () => selectSource(note.source_id)));
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
    $("previous-page").addEventListener("click", () => navigate(-1));
    $("next-page").addEventListener("click", () => navigate(1));
    $("page-select").addEventListener("change", event => loadPage(event.target.value, {push: true}));
    $("volume-select").addEventListener("change", event => loadPage(pageId(event.target.value, event.target.value === "I" ? 17 : 7), {push: true}));
    $("zoom-in").addEventListener("click", () => { state.zoom = Math.min(250, state.zoom + 25); applyZoom(); });
    $("zoom-out").addEventListener("click", () => { state.zoom = Math.max(100, state.zoom - 25); applyZoom(); });
    $("zoom-reset").addEventListener("click", () => { state.zoom = 100; applyZoom(); });
    $("show-ocr").addEventListener("change", drawOverlay);
    $("search-form").addEventListener("submit", search);
    $("close-search").addEventListener("click", () => { state.searchToken++; $("search-results").hidden = true; $("search-input").focus(); });
    $("citation-filter").addEventListener("input", renderCitations);
    for (const tab of ["text", "citations", "notes"]) $(`${tab}-tab`).addEventListener("click", () => setTab(tab));
    document.querySelector(".tabs").addEventListener("keydown", event => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const tabs = ["text", "citations", "notes"];
      const next = event.key === "Home" ? 0 : event.key === "End" ? 2 : (tabs.indexOf(state.tab) + (event.key === "ArrowRight" ? 1 : 2)) % 3;
      setTab(tabs[next], true);
    });
    $("note-form").addEventListener("submit", saveNote);
    $("export-notes").addEventListener("click", exportNotes);
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
    document.addEventListener("keydown", event => {
      if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey || /INPUT|SELECT|TEXTAREA|BUTTON/.test(event.target.tagName) || $("about-dialog").open) return;
      if (event.key === "ArrowLeft") { event.preventDefault(); navigate(-1); }
      if (event.key === "ArrowRight") { event.preventDefault(); navigate(1); }
    });
  }

  async function init() {
    bindEvents();
    readNotes();
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
