// Run: node --test tests/vlb_dictionary_links.test.cjs
// Exercise the production linker and pinned dictionary, without loading scans.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const zlib = require('node:zlib');

const root = path.resolve(__dirname, '..');
const script = fs.readFileSync(path.join(root, 'js/index.js'), 'utf8');
const start = script.indexOf('  function linkSources(');
const end = script.indexOf('  function splitByBullet(', start);
const linkSources = vm.runInNewContext(`${script.slice(start, end)}; linkSources;`);
const mappingStart = script.indexOf('  function mapCompressedData(');
const mappingEnd = script.indexOf('  function keyForItem(', mappingStart);
const mapCompressedData = vm.runInNewContext(`${script.slice(mappingStart, mappingEnd)}; mapCompressedData;`);
const dictionary = JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(root, 'docs/dict-conjugated.json.gz'))));
const citationRecords = JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(root, 'vlb/source/citation_links.json.gz'))));
const citationsByPage = new Map();
for (const citation of citationRecords) {
  for (const page of citation.page_links) {
    if (page.link_status !== 'page_range_linked') continue;
    const key = `${citation.entry_index}:${page.volume}:${page.printed_page}`;
    if (!citationsByPage.has(key)) citationsByPage.set(key, []);
    citationsByPage.get(key).push(citation);
  }
}

// Use the real formatter to ensure source positions survive its inserted HTML.
const constantsStart = script.indexOf('  const TUPI_START_RE');
const constantsEnd = script.indexOf('  const SUBJ_PREF_MAP', constantsStart);
const formatterStart = script.indexOf('  function splitByBullet(');
const formatterEnd = script.indexOf('  function toggleContent(', formatterStart);
const formatVerbeteDefinition = vm.runInNewContext(`
  ${script.slice(constantsStart, constantsEnd)}
  const warnOnce = () => {};
  ${script.slice(formatterStart, formatterEnd)}
  formatVerbeteDefinition;
`, {window: {location: {pathname: '/nhe-enga/'}}});

function links(text, row = null, originalText = text) {
  return [...linkSources(text, row, originalText).matchAll(/<a href="([^"]+)"[^>]*>([^<]*)<\/a>/g)]
    .filter((match) => match[1].startsWith('/nhe-enga/vlb/?'))
    .map((match) => ({ url: new URL(match[1], 'https://example.test'), text: match[2] }));
}

function locator(link) {
  return [link.url.searchParams.get('volume'), Number(link.url.searchParams.get('page'))];
}

function sourceOccurrences(link) {
  const row = Number(link.url.searchParams.get('entry'));
  const [volume, page] = locator(link);
  const position = Number(link.url.searchParams.get('citation_pos'));
  return (citationsByPage.get(`${row}:${volume}:${page}`) || [])
    .filter(citation => citation.citation_start <= position && position < citation.citation_end_exclusive);
}

test('VLB citations open the printed page and preserve the dictionary row', () => {
  const found = links('(VLB, II, 69)', 2338);
  assert.equal(found.length, 1);
  assert.equal(found[0].url.pathname, '/nhe-enga/vlb/');
  assert.deepEqual(locator(found[0]), ['II', 69]);
  assert.equal(found[0].url.searchParams.get('entry'), '2338');
  assert.equal(found[0].url.searchParams.get('mode'), 'continuous');
  assert.equal(found[0].url.searchParams.get('focus'), 'auto');
  assert.equal(found[0].url.searchParams.get('citation_pos'), '10');
  assert.equal(found[0].text, 'VLB, II, 69');
  assert.equal(found[0].url.searchParams.has('citation'), false);
});

test('page lists, inherited volumes, ranges and VBL spelling retain every token', () => {
  for (const [text, expected] of [
    ['(VLB, I, 46, II, 38; 39)', [['I', 46], ['II', 38], ['II', 39]]],
    ['(VLB, I, 128–129)', [['I', 128], ['I', 129]]],
    ['(VBL, II, 135)', [['II', 135]]],
    ['(VLB, I, 34; II, 109, adapt.)', [['I', 34], ['II', 109]]],
  ]) {
    assert.equal(linkSources(text).replace(/<\/?a\b[^>]*>/g, ''), text);
    assert.deepEqual(links(text).map(locator), expected);
  }
});

test('malformed, missing and nontextual locators are not silently redirected', () => {
  for (const text of ['VLB, I, 1390', 'VLB, I', 'VLB, I, 25', 'VLB, I, 26', 'VLB, II, 150']) {
    assert.equal(linkSources(text), text);
  }
  assert.equal(links('VLB, I, 17', '<script>')[0].url.searchParams.has('entry'), false);
});

test('rows without legacy IDs keep their snapshot index through dictionary mapping', () => {
  const row = 2356; // abaíba: an adjective-bearing record with no legacy i field.
  assert.equal(dictionary[row].i, undefined);
  const mapped = mapCompressedData(dictionary)[row];
  assert.equal(mapped.dictionary_index, row);
  assert.equal(links(mapped.definition, mapped.dictionary_index)[0].url.searchParams.get('entry'), String(row));
});

test('the inherited adapted citation in nhe’ẽporangaíba remains navigable', () => {
  const row = 7915;
  assert.equal(dictionary[row].f, "nhe'ẽporangaíba");
  assert.deepEqual(links(dictionary[row].d, row).map(locator), [['I', 34], ['II', 109]]);
  const inherited = sourceOccurrences(links(dictionary[row].d, row)[1]);
  assert.equal(inherited.length, 1);
  assert.equal(inherited[0].citation_id, 'navarro-d235a7961961b58f-r07915-s00260-e00276');
});

test('two citations to the same page retain distinct original occurrences', () => {
  const row = 5056; // îepé: two different examples both cite VLB I17.
  const found = links(formatVerbeteDefinition(dictionary[row].d), row, dictionary[row].d);
  assert.deepEqual(found.map(locator), [['I', 17], ['I', 17]]);
  assert.deepEqual(found.map(link => sourceOccurrences(link)[0]?.citation_id), [
    'navarro-d235a7961961b58f-r05056-s00115-e00125',
    'navarro-d235a7961961b58f-r05056-s00198-e00208',
  ]);
});

test('page-token positions use original code points, not inserted markup or UTF-16 units', () => {
  const original = '🐾 palavra (VLB, I, 17)';
  const formatted = '<b>🐾 palavra</b> <span>(VLB, I, 17)</span>';
  const found = links(formatted, 1, original)[0];
  assert.equal(Number(found.url.searchParams.get('citation_pos')), Array.from(original).indexOf('1'));
  assert.notEqual(Number(found.url.searchParams.get('citation_pos')), original.indexOf('17'));
  const changed = links('(VLB, I, 18)', 1, original)[0];
  assert.equal(changed.url.searchParams.has('citation_pos'), false, 'mismatched rendering falls back to the page without inventing an occurrence');
});

test('rendered citations retain original positions and expose genuinely ambiguous copies', () => {
  let count = 0;
  let ambiguousCopies = 0;
  dictionary.forEach((record, row) => {
    if (!record.d || !/\b(?:VLB|VBL)\b/.test(record.d)) return;
    const formatted = record.t === 1 || record.t === true ? formatVerbeteDefinition(record.d) : record.d;
    const rawLinks = links(record.d, row);
    const rendered = links(formatted, row, record.d);
    const copiesByPage = new Map();
    rendered.forEach((link) => {
      const key = locator(link).join(':');
      if (!copiesByPage.has(key)) copiesByPage.set(key, []);
      copiesByPage.get(key).push(link);
    });
    for (const original of rawLinks) {
      assert.ok(copiesByPage.has(locator(original).join(':')), `lost cited page, row ${row}`);
      assert.equal(sourceOccurrences(original).length, 1, `raw citation identity, row ${row}`);
    }
    rendered.forEach((link) => {
      const key = locator(link).join(':');
      const originals = rawLinks.filter(original => locator(original).join(':') === key);
      if (!link.url.searchParams.has('citation_pos')) {
        assert.ok(originals.length > 1 && originals.length !== copiesByPage.get(key).length,
          `unnecessary missing source position, row ${row}`);
        ambiguousCopies += 1;
        return;
      }
      const matches = sourceOccurrences(link);
      assert.equal(matches.length, 1, `ambiguous original occurrence, row ${row}, ${link.url}`);
      const original = originals.length === 1 ? originals[0] : originals[copiesByPage.get(key).indexOf(link)];
      assert.equal(matches[0].citation_id, sourceOccurrences(original)[0].citation_id, `wrong original occurrence, row ${row}`);
      count += 1;
    });
  });
  assert.equal(count, 6225);
  assert.equal(ambiguousCopies, 98);
});

test('ambiguous duplicate examples fall back to a page without selecting the first occurrence', () => {
  const row = 2502; // aîa has two original II64 citations, displayed three times.
  const rendered = links(formatVerbeteDefinition(dictionary[row].d), row, dictionary[row].d)
    .filter(link => locator(link).join(':') === 'II:64');
  assert.equal(rendered.length, 3);
  assert.ok(rendered.every(link => !link.url.searchParams.has('citation_pos')));
});

test('the homepage exposes VLB without linking the unfinished grammar page', () => {
  const home = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  assert.match(home, /<a\b[^>]*href=["']\/nhe-enga\/vlb\/["'][^>]*>VLB<\/a>/i);
  assert.doesNotMatch(home, /<a\b[^>]*href=["']\/nhe-enga\/gramatica\/?["']/i);
});

test('all served dictionary text survives linking and valid VLB locators reach the reader', () => {
  let count = 0;
  const citedPages = new Set();
  dictionary.forEach((record, row) => {
    const html = linkSources(record.d, row);
    assert.equal(html.replace(/<\/?a\b[^>]*>/g, ''), record.d, `row ${row}`);
    for (const link of links(record.d, row)) {
      count += 1;
      const [volume, page] = locator(link);
      citedPages.add(`${volume}:${page}`);
      assert.equal(link.url.searchParams.get('entry'), String(row));
      assert.ok(volume === 'I' ? page >= 17 && page <= 154 : page >= 7 && page <= 149);
    }
  });
  assert.equal(count, 6164);
  assert.equal(citedPages.size, 277);
});
