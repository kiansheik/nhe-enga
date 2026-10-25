// Run from the repository root: node --test tests/primary_sources.test.cjs
// Execute the actual vanilla-JS functions in a minimal DOM; no npm packages
// or network access are needed. Real scan/edition checks are in source.json.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const zlib = require('node:zlib');

const root = path.resolve(__dirname, '..');
const dictionaryScript = fs.readFileSync(path.join(root, 'js/index.js'), 'utf8');
const linkSourcesStart = dictionaryScript.indexOf('  function linkSources(');
const linkSourcesEnd = dictionaryScript.indexOf('  function splitByBullet(', linkSourcesStart);
assert.ok(linkSourcesStart >= 0 && linkSourcesEnd > linkSourcesStart);
const linkSources = vm.runInNewContext(`${dictionaryScript.slice(linkSourcesStart, linkSourcesEnd)}; linkSources;`);
const viewerHtml = fs.readFileSync(path.join(root, 'docs/primary_sources/index.html'), 'utf8');
const viewerScript = viewerHtml.match(/<script>([\s\S]*?)<\/script>/)[1];
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'docs/primary_sources/evreux1929/source.json'), 'utf8'));
const arcat1686Manifest = JSON.parse(fs.readFileSync(path.join(root, 'docs/primary_sources/arcat1686/source.json'), 'utf8'));
const figueiraManifest = JSON.parse(fs.readFileSync(path.join(root, 'docs/primary_sources/figueira1878/source.json'), 'utf8'));
const anchTeatroManifest = JSON.parse(fs.readFileSync(path.join(root, 'docs/primary_sources/anchteatro1954/source.json'), 'utf8'));
const viewerManifests = {
  anchteatro1954: anchTeatroManifest,
  figueira1878: figueiraManifest,
};

function links(html) {
  return [...html.matchAll(/<a href="([^"]+)"[^>]*>([^<]*)<\/a>/g)].map((match) => ({
    href: match[1],
    text: match[2],
  }));
}

function element(tagName) {
  const listeners = {};
  const classes = new Set();
  const node = {
    tagName, children: [], parentNode: null, hidden: false, disabled: false,
    attributes: {}, style: {},
    classList: {
      toggle(name, enabled) { if (enabled) classes.add(name); else classes.delete(name); },
      contains(name) { return classes.has(name); },
    },
    setAttribute(name, value) { this.attributes[name] = value; },
    addEventListener(name, callback) { (listeners[name] ||= []).push(callback); },
    emit(name) { for (const callback of listeners[name] || []) callback(); },
    appendChild(child) { child.parentNode = this; this.children.push(child); },
    removeChild(child) {
      assert.ok(this.children.includes(child));
      this.children.splice(this.children.indexOf(child), 1);
      child.parentNode = null;
    },
  };
  return node;
}

async function openViewer(query, formats = null) {
  const body = element('body');
  // Only DOM APIs touched by this viewer are implemented. Static elements
  // come from the real HTML, so a removed/renamed control breaks its test.
  for (const match of viewerHtml.matchAll(/<([a-z][a-z0-9]*)\b[^>]*\bid="([^"]+)"([^>]*)>/g)) {
    const node = element(match[1]);
    node.id = match[2];
    node.hidden = /\bhidden\b/.test(match[3]);
    body.appendChild(node);
  }
  function find(node, predicate) {
    if (predicate(node)) return node;
    for (const child of node.children) {
      const result = find(child, predicate);
      if (result) return result;
    }
    return null;
  }
  const document = {
    body,
    createElement: element,
    getElementById(id) { return find(body, (node) => node.id === id); },
    querySelector(selector) {
      return selector.startsWith('#') ? this.getElementById(selector.slice(1)) : find(body, (node) => node.tagName === selector);
    },
  };
  const window = { location: new URL(`https://example.test/nhe-enga/docs/primary_sources/?${query}`) };
  window.history = {
    replaceState(_state, _title, url) { window.location = new URL(url, window.location); },
  };
  vm.runInNewContext(viewerScript, {
    document, window, URLSearchParams,
    fetch: async (url) => {
      if (url.endsWith('/image-formats.json')) {
        return { ok: Boolean(formats), json: async () => formats };
      }
      const match = url.match(/\/primary_sources\/([^/]+)\/source\.json$/);
      const source = match && viewerManifests[match[1]];
      return { ok: Boolean(source), json: async () => source };
    },
  });
  // Allow loadImageFormats().then(updateImage) to complete.
  await new Promise(setImmediate);
  return {
    document, window,
    get: (id) => document.getElementById(id),
    click: (id) => document.getElementById(id).emit('click'),
    image: () => document.querySelector('img'),
  };
}

test('D’Evreux preserves citation wording, apostrophe variants, and each page in a range/list', () => {
  for (const author of ["D'Evreux", "D' Evreux", 'D’Evreux', 'D’Évreux']) {
    for (const pages of ['293', 'pp. 142-143', '142–143, 157']) {
      const input = `(${author}, Viagem, ${pages});`;
      const linked = linkSources(input);
      assert.equal(linked.replace(/<\/?a\b[^>]*>/g, ''), input);
      const expected = pages.match(/\d+/g);
      assert.deepEqual(links(linked).map((link) => new URL(link.href, 'https://example.test').searchParams.get('page_number')), expected);
      assert.equal((linked.match(/target="_blank" rel="noopener"/g) || []).length, expected.length);
      assert.ok(links(linked).every((link) => link.href.includes('book_name=evreux1929')));
    }
  }
});

test('shorthand, other editions/books, and unavailable printed pages stay unlinked', () => {
  for (const citation of [
    "Yves D'Evreux, (op. cit., p. 157)", "D'Evreux, Voyage, 293", 'Fig., Missão do Maranhão, 150',
    'Fig., Arte, 1685, 64', 'Fig., Arte, 0', 'Fig., Arte, 168',
    'Anch., Teatro, 177', 'Anch., Teatro, 176, 2006',
    "D'Evreux, Viagem, 1864, 293", "D'Evreux, Viagem, 0", "D'Evreux, Viagem, 3",
    "D'Evreux, Viagem, 443", "D'Evreux, Viagem, 293v",
  ]) assert.equal(linkSources(citation), citation);
});

test('the served dictionary’s 120 explicit citations reach the 42 verified printed pages', () => {
  // Use the served .gz. The similarly named .json is also compressed but
  // contains a different dictionary snapshot and must not substitute for it.
  const entries = JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(root, 'docs/dict-conjugated.json.gz'))));
  let citationCount = 0;
  let pageLinks = 0;
  const pages = new Set();
  for (const entry of entries) {
    const definition = entry.d || '';
    const linked = linkSources(definition);
    assert.equal(linked.replace(/<\/?a\b[^>]*>/g, ''), definition);
    for (const link of links(linked).filter((link) => link.href.includes('book_name=evreux1929'))) {
      if (link.text.includes('Viagem')) citationCount += 1;
      pageLinks += 1;
      pages.add(Number(new URL(link.href, 'https://example.test').searchParams.get('page_number')));
    }
  }
  assert.equal(citationCount, 120);
  assert.equal(pageLinks, 121); // Marabá's pp. 142–143 supplies two links.
  assert.deepEqual([...pages].sort((a, b) => a - b), manifest.verification.all_cited_pages);
});

test('Figueira links every current Arte citation, ranges and inherited pages without changing text', () => {
  const entries = JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(root, 'docs/dict-conjugated.json.gz'))));
  let citationCount = 0;
  const records = new Set();
  const pages = new Set();
  entries.forEach((entry, entryIndex) => {
    const definition = entry.d || '';
    const linked = linkSources(definition);
    assert.equal(linked.replace(/<\/?a\b[^>]*>/g, ''), definition);
    const sourceLinks = links(linked).filter((link) => link.href.includes('book_name=figueira1878'));
    if (sourceLinks.length) records.add(entryIndex);
    for (const link of sourceLinks) {
      if (link.text.includes('Fig.')) citationCount += 1;
      pages.add(Number(new URL(link.href, 'https://example.test').searchParams.get('page_number')));
    }
  });
  assert.equal(citationCount, 622);
  assert.equal(records.size, 455);
  assert.deepEqual([...pages].sort((a, b) => a - b), figueiraManifest.verification.all_cited_pages);

  const inherited = '(Fig., Arte, 147; 163)';
  assert.deepEqual(links(linkSources(inherited)).map((link) => link.text), ['Fig., Arte, 147', '163']);
  const qualified = links(linkSources('(Fig., Arte, 1686, 64)'));
  assert.equal(qualified.length, 1);
  assert.equal(qualified[0].text, 'Fig., Arte, 1686, 64');
  assert.equal(new URL(qualified[0].href, 'https://example.test').searchParams.get('citation_year'), '1686');
});

test('Anchieta Teatro links only the nine verified unsuffixed page-176 records', () => {
  const entries = JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(root, 'docs/dict-conjugated.json.gz'))));
  let citationCount = 0;
  const records = new Set();
  entries.forEach((entry, entryIndex) => {
    const definition = entry.d || '';
    const linked = linkSources(definition);
    assert.equal(linked.replace(/<\/?a\b[^>]*>/g, ''), definition);
    const sourceLinks = links(linked).filter((link) => link.href.includes('book_name=anchteatro1954'));
    citationCount += sourceLinks.length;
    if (sourceLinks.length) records.add(entryIndex);
  });
  assert.equal(citationCount, anchTeatroManifest.verification.citation_count);
  assert.equal(records.size, anchTeatroManifest.verification.record_count);
  for (const unverified of [
    'Anch., Teatro, 176, 2006',
    'Anch., Teatro, 176, 2007',
    'Anch., Teatro, 176-178',
    'Anch., Teatro, 176; 180',
  ]) assert.equal(linkSources(unverified), unverified);
});

test('new source assets match their declared scan bounds and explicit targets', () => {
  const imageIndices = (book) => fs.readdirSync(path.join(root, 'docs/primary_sources', book))
    .filter((name) => name.endsWith('.jpg'))
    .map((name) => Number.parseInt(name, 10))
    .sort((a, b) => a - b);
  const figueiraExpected = Array.from(
    { length: figueiraManifest.images.last_index - figueiraManifest.images.first_index + 1 },
    (_value, offset) => figueiraManifest.images.first_index + offset,
  );
  assert.deepEqual(imageIndices('figueira1878'), figueiraExpected);
  assert.deepEqual(
    imageIndices('anchteatro1954'),
    anchTeatroManifest.mapping.targets.map((target) => target.pdf_index).sort((a, b) => a - b),
  );
  for (const target of anchTeatroManifest.mapping.targets) {
    assert.equal(target.image, `${target.pdf_index}.jpg`);
  }
});

test("the ma'enduar examples expose all three requested source links", () => {
  const definition = "...Nde ma'enduá xe ri! - Lembra-te de mim! (Anch., Teatro, 176); Kûesé Pedro nde resé i ma'enduari. - Ontem Pedro se lembrou de ti. (Fig., Arte, 95); N'i ma'enduari xûéne. - Eles não se lembrarão. (Fig., Arte, 40)";
  const sourceLinks = links(linkSources(definition));
  assert.deepEqual(sourceLinks.map((link) => link.text), ['Anch., Teatro, 176', 'Fig., Arte, 95', 'Fig., Arte, 40']);
  assert.deepEqual(sourceLinks.map((link) => new URL(link.href, 'https://example.test').searchParams.get('book_name')), ['anchteatro1954', 'figueira1878', 'figueira1878']);
  assert.deepEqual(sourceLinks.map((link) => new URL(link.href, 'https://example.test').searchParams.get('page_number')), ['176', '95', '40']);
});

test('Araújo 1686 citations select the second edition and preserve ranges', () => {
  for (const [citation, expected] of [
    ['Ar., Cat., 241, 1686', ['241']],
    ['Ar., Cat., 11-12, 1686', ['11', '12']],
    ['Ar., Cat., 11–12, 1686', ['11', '12']],
  ]) {
    const linked = linkSources(citation);
    assert.equal(linked.replace(/<\/?a\b[^>]*>/g, ''), citation);
    assert.deepEqual(links(linked).map((link) => new URL(link.href, 'https://example.test').searchParams.get('page_number')), expected);
    assert.ok(links(linked).every((link) => link.href.includes('book_name=arcat1686')));
  }
  assert.equal(linkSources('Ar., Cat., 1686'), 'Ar., Cat., 1686');
});

test('the served dictionary’s 1686 citations reach exactly the selected source pages', () => {
  const entries = JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(root, 'docs/dict-conjugated.json.gz'))));
  let citationCount = 0;
  let pageLinks = 0;
  const pages = new Set();
  for (const entry of entries) {
    const definition = entry.d || '';
    citationCount += [...definition.matchAll(/Ar\.,\s*Cat\.,\s*\d+(?:\s*[-–—]\s*\d+)?\s*,\s*1686\b/gi)].length;
    const linked = linkSources(definition);
    assert.equal(linked.replace(/<\/?a\b[^>]*>/g, ''), definition);
    for (const link of links(linked).filter((item) => item.href.includes('book_name=arcat1686'))) {
      pageLinks += 1;
      pages.add(Number(new URL(link.href, 'https://example.test').searchParams.get('page_number')));
    }
  }
  assert.equal(citationCount, arcat1686Manifest.verification.citation_count);
  assert.equal(pageLinks, 91); // The 11–12 citation supplies two links.
  assert.deepEqual([...pages].sort((a, b) => a - b), arcat1686Manifest.verification.all_cited_pages);
});

test('Araújo 1686 publishes only cited pages and the two-page context buffer', () => {
  const { first_printed_page: first, last_printed_page: last, printed_page_to_image_offset: offset } = arcat1686Manifest.pagination;
  const context = arcat1686Manifest.selection.context_pages_each_side;
  const expected = new Set();
  for (const cited of arcat1686Manifest.verification.all_cited_pages) {
    for (let page = Math.max(first, cited - context); page <= Math.min(last, cited + context); page += 1) {
      expected.add(page + offset);
    }
  }
  const actual = fs.readdirSync(path.join(root, 'docs/primary_sources/arcat1686'))
    .filter((name) => name.endsWith('.jpg'))
    .map((name) => Number.parseInt(name, 10));
  assert.equal(actual.length, arcat1686Manifest.selection.rendered_image_count);
  assert.deepEqual(actual.sort((a, b) => a - b), [...expected].sort((a, b) => a - b));
});

test("emo'emyîara opens printed page 241 of Araújo 1686 with bounded context", async () => {
  const href = links(linkSources('Ar., Cat., 241, 1686'))[0].href;
  const viewer = await openViewer(href.split('?')[1]);
  assert.equal(viewer.image().src, '/nhe-enga/docs/primary_sources/arcat1686/276.jpg');
  assert.match(viewer.get('currentPage').textContent, /^Página 241 de 371/);
  assert.match(viewer.document.title, /Catecismo Brasílico \(1686\)/);
  assert.equal(viewer.get('sourceDetails').hidden, false);
  assert.equal(viewer.get('sourceInfo').href, arcat1686Manifest.catalog_url);
  assert.match(viewer.get('sourcePdf').href, /#page=277$/);
  viewer.click('nextPage');
  viewer.click('nextPage');
  assert.equal(viewer.window.location.searchParams.get('page_number'), '243');
  assert.equal(viewer.get('nextPage').disabled, true);
  viewer.click('nextPage');
  assert.equal(viewer.window.location.searchParams.get('page_number'), '243');
});

test('so’o-Îurupari citation opens the 1929 page 293 scan and PDF ordinal 294', async () => {
  // Attestation: source.json records “Soo-Jeropary” at printed p. 293.
  const href = links(linkSources("(D'Evreux, Viagem, 293)"))[0].href;
  const viewer = await openViewer(href.split('?')[1]);
  assert.equal(viewer.image().src, '/nhe-enga/docs/primary_sources/evreux1929/293.jpg');
  assert.equal(viewer.get('currentPage').textContent, 'Página 293 de 442');
  assert.match(viewer.document.title, /Viagem ao Norte do Brasil \(1929\)/);
  assert.equal(viewer.get('sourceDetails').hidden, false);
  assert.equal(viewer.get('sourceInfo').href, manifest.catalog_url);
  assert.equal(viewer.get('sourcePdf').href, `${manifest.pdf.url}#page=294`);
  assert.equal(viewer.get('openImage').href, viewer.image().src);
  viewer.click('nextPage');
  assert.equal(viewer.window.location.searchParams.get('page_number'), '294');
  const reloaded = await openViewer(viewer.window.location.search.slice(1));
  assert.equal(reloaded.image().src, '/nhe-enga/docs/primary_sources/evreux1929/294.jpg');
  reloaded.click('prevPage');
  assert.equal(reloaded.window.location.searchParams.get('page_number'), '293');
});

test('Figueira resolves the requested printed pages through the verified complete-scan map', async () => {
  for (const [citation, printedPage, imageIndex, pdfOrdinal] of [
    ['Fig., Arte, 95', 95, 118, 119],
    ['Fig., Arte, 40', 40, 63, 64],
  ]) {
    const href = links(linkSources(citation))[0].href;
    const viewer = await openViewer(href.split('?')[1]);
    assert.equal(viewer.image().src, `/nhe-enga/docs/primary_sources/figueira1878/${imageIndex}.jpg`);
    assert.match(viewer.get('currentPage').textContent, new RegExp(`Página impressa ${printedPage}`));
    assert.equal(viewer.get('sourcePdf').href, `${figueiraManifest.pdf.url}#page=${pdfOrdinal}`);
    assert.equal(viewer.get('sourceNotice').hidden, true);
  }

  const qualifiedHref = links(linkSources('(Fig., Arte, 1686, 64)'))[0].href;
  const qualified = await openViewer(qualifiedHref.split('?')[1]);
  assert.equal(qualified.get('sourceNotice').hidden, false);
  assert.match(qualified.get('sourceNotice').textContent, /conserva “1686”.*1687.*página 64/);
  qualified.click('nextPage');
  assert.equal(qualified.window.location.searchParams.has('citation_year'), false);
  assert.equal(qualified.get('sourceNotice').hidden, true);

  const first = await openViewer('book_name=figueira1878&page_number=1');
  assert.match(first.image().src, /\/24\.jpg$/);
  first.click('prevPage');
  assert.match(first.image().src, /\/23\.jpg$/);
  assert.match(first.get('currentPage').textContent, /Preliminar sem numeração/);
  assert.equal(first.window.location.searchParams.get('scan'), '23');
  assert.equal(first.window.location.searchParams.has('page_number'), false);
  first.click('nextPage');
  assert.equal(first.window.location.searchParams.get('page_number'), '1');

  const unavailable = await openViewer('book_name=figueira1878&page_number=168');
  assert.equal(unavailable.image(), null);
  assert.equal(unavailable.get('imageError').hidden, false);
  assert.match(unavailable.get('imageError').textContent, /mapa desta fonte/);
  assert.equal(unavailable.window.location.searchParams.get('page_number'), '168');
});

test('Anchieta page 176 opens the explicit Martins witness and labels the edition boundary', async () => {
  const href = links(linkSources('(Anch., Teatro, 176)'))[0].href;
  const viewer = await openViewer(href.split('?')[1]);
  const target = anchTeatroManifest.mapping.targets[0];
  assert.equal(viewer.image().src, `/nhe-enga/docs/primary_sources/anchteatro1954/${target.image}`);
  assert.equal(viewer.get('currentPage').textContent, target.label);
  assert.equal(viewer.get('sourceDetails').hidden, false);
  assert.equal(viewer.get('sourceInfo').href, anchTeatroManifest.catalog_url);
  assert.equal(viewer.get('sourcePdf').href, target.source_page_url);
  assert.equal(viewer.get('sourcePdf').textContent, anchTeatroManifest.viewer.source_page_link_label);
  assert.equal(viewer.get('sourceNotice').hidden, false);
  assert.match(viewer.get('sourceNotice').textContent, /paginação de Navarro.*Martins.*não existe uma equivalência geral/);
  assert.equal(viewer.get('prevPage').disabled, true);
  assert.equal(viewer.get('nextPage').disabled, true);
});

test('cover, unnumbered preliminaries, and final blank have bounded navigation and honest labels', async () => {
  const start = await openViewer('book_name=evreux1929&page_number=0');
  assert.equal(start.get('prevPage').disabled, true);
  assert.match(start.get('currentPage').textContent, /Capa.*sem numeração/);
  start.click('prevPage');
  assert.match(start.image().src, /\/0\.jpg$/);
  start.click('nextPage');
  assert.match(start.get('currentPage').textContent, /Preliminares 1 de 13.*sem numeração/);
  assert.equal(start.get('prevPage').disabled, false);
  const firstNumbered = await openViewer('book_name=evreux1929&page_number=14');
  assert.equal(firstNumbered.get('currentPage').textContent, 'Página 14 de 442');
  const end = await openViewer('book_name=evreux1929&page_number=442');
  end.click('nextPage');
  assert.match(end.get('currentPage').textContent, /final em branco.*sem numeração/);
  assert.equal(end.get('nextPage').disabled, true);
  end.click('nextPage');
  assert.match(end.image().src, /\/443\.jpg$/);
  assert.equal(end.window.location.searchParams.get('page_number'), '443');
  end.click('prevPage');
  assert.equal(end.get('nextPage').disabled, false);
});

test('invalid D’Evreux page parameters become valid, shareable URLs', async () => {
  for (const [requested, expected] of [['-10', 0], ['900', 443], ['abc', 1], ['', 1], ['293v', 1], ['0293', 293]]) {
    const viewer = await openViewer(`book_name=evreux1929&page_number=${requested}`);
    assert.match(viewer.image().src, new RegExp(`/${expected}\\.jpg$`));
    assert.equal(viewer.window.location.searchParams.get('page_number'), String(expected));
  }
});

test('zoom controls, open-image URL, and load-error notice remain usable across navigation', async () => {
  const viewer = await openViewer('book_name=evreux1929&page_number=293');
  viewer.click('zoomPage');
  assert.equal(viewer.document.body.classList.contains('zoomed'), true);
  assert.equal(viewer.get('zoomPage').attributes['aria-pressed'], 'true');
  viewer.click('nextPage');
  assert.equal(viewer.document.body.classList.contains('zoomed'), true);
  assert.match(viewer.get('openImage').href, /\/294\.jpg$/);
  viewer.image().emit('click');
  assert.equal(viewer.get('zoomPage').attributes['aria-pressed'], 'false');
  viewer.image().emit('error');
  assert.equal(viewer.get('imageError').hidden, false);
  viewer.click('nextPage');
  assert.equal(viewer.get('imageError').hidden, true);
});

test('existing source URLs, folios, image formats, and source selection are preserved', async () => {
  for (const [citation, expectedImage] of [
    ['VLB, I, 12', 'vlb/12.png'], ['VLB, II, 69', 'vlb/223.png'],
    ['Anch., Arte, 44', 'ancharte/43.png'], ['Anch., Arte, 12v', 'ancharte/12.png'],
    ['Ar., Cat., 12v', 'arcat1618/59.png'], ['Bettendorff, Compêndio, 93', 'betcomp/102.jpg'],
    ['Léry, Histoire, 287', 'lerhist/341.jpg'],
  ]) {
    const href = links(linkSources(citation))[0].href;
    const viewer = await openViewer(href.split('?')[1]);
    assert.equal(viewer.image().src, `/nhe-enga/docs/primary_sources/${expectedImage}`);
    assert.equal(viewer.get('sourceDetails').hidden, true);
    assert.match(viewer.get('currentPage').textContent, /^Imagem /);
  }
  const converted = await openViewer('book_name=vlb&page_number=223', { books: { vlb: '.webp' } });
  assert.match(converted.image().src, /vlb\/223\.webp$/);
  const arcat = await openViewer('book_name=arcat1618&page_number=12v');
  arcat.click('nextPage');
  assert.equal(arcat.window.location.searchParams.get('page_number'), '13');
  const reloaded = await openViewer(arcat.window.location.search.slice(1));
  assert.match(reloaded.image().src, /arcat1618\/60\.png$/);
});
