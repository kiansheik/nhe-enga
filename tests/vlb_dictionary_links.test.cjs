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

function links(text, row = null) {
  return [...linkSources(text, row).matchAll(/<a href="([^"]+)"[^>]*>([^<]*)<\/a>/g)]
    .filter((match) => match[1].startsWith('/nhe-enga/vlb/?'))
    .map((match) => ({ url: new URL(match[1], 'https://example.test'), text: match[2] }));
}

function locator(link) {
  return [link.url.searchParams.get('volume'), Number(link.url.searchParams.get('page'))];
}

test('VLB citations open the printed page and preserve the dictionary row', () => {
  const found = links('(VLB, II, 69)', 2338);
  assert.equal(found.length, 1);
  assert.equal(found[0].url.pathname, '/nhe-enga/vlb/');
  assert.deepEqual(locator(found[0]), ['II', 69]);
  assert.equal(found[0].url.searchParams.get('entry'), '2338');
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
