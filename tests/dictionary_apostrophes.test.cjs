const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const dictionaryScript = fs.readFileSync(path.join(__dirname, '../js/index.js'), 'utf8');
const helperStart = dictionaryScript.indexOf('  function normalizeApostrophes(');
const helperEnd = dictionaryScript.indexOf('  const warnOnce', helperStart);
const searchStart = dictionaryScript.indexOf('  function searchByFirstWord(', helperEnd);
const searchEnd = dictionaryScript.indexOf('  function transformConjList(', searchStart);
assert.ok(helperStart >= 0 && helperEnd > helperStart && searchStart >= 0 && searchEnd > searchStart);

const dictionary = vm.runInNewContext(`
  ${dictionaryScript.slice(helperStart, helperEnd)}
  ${dictionaryScript.slice(searchStart, searchEnd)}
  ({ normalizeApostrophes, buildSearchIndex, searchByFirstWord, searchAllDefinitions })
`);

test('dictionary canonicalizes apostrophe variants in entries and typed searches', () => {
  const entries = [{
    first_word: 'xe ‘ang',
    definition: 'A ’ang word',
    con: 'aʼ',
  }];
  const index = dictionary.buildSearchIndex(entries);

  assert.equal(entries[0].first_word, "xe 'ang");
  assert.equal(entries[0].definition, "A 'ang word");
  assert.equal(entries[0].con, "a'");
  assert.equal(dictionary.searchByFirstWord(index, 'xe ’ang').length, 1);
  assert.equal(dictionary.searchAllDefinitions(index, dictionary.normalizeApostrophes('’ang').toLowerCase()).length, 1);
});