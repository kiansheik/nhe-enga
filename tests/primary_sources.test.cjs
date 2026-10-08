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
    fetch: async () => ({ ok: Boolean(formats), json: async () => formats }),
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
    "Yves D'Evreux, (op. cit., p. 157)", "D'Evreux, Voyage, 293", 'Fig., Arte, 150',
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
