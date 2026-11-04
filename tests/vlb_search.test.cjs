const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const zlib = require("node:zlib");

const ROOT = path.resolve(__dirname, "..");
const VLBSearch = require(path.join(ROOT, "vlb/search.js"));
const sourceRows = JSON.parse(zlib.gunzipSync(
  fs.readFileSync(path.join(ROOT, "vlb/data/source-index.json.gz"))));
const orthographyModel = JSON.parse(
  fs.readFileSync(path.join(ROOT, "vlb/mining/output-v3/orthography-model.json"), "utf8"));
const index = VLBSearch.buildIndex(sourceRows);

test("literal search retains orthographic marks and ranks whole VLB forms first", () => {
  const result = VLBSearch.search(index, "biã", orthographyModel);
  assert.equal(result.directTotal, 4);
  assert.equal(result.probableTotal, 0);
  assert.deepEqual(result.results.map(item => item.sourceLine), [4770, 1039, 3134, 5140]);
  assert.equal(result.results[0].kind, "vlb-whole");
  assert.equal(result.results[0].scope, "whole");
  assert.equal(result.results[0].queryPath, "literal");
  assert.equal(result.results[0].label, "VLB · forma exata");
  assert.equal(result.results[0].pageId, "II-032");
  assert.equal(result.results[0].matchedForm, "biã");
  assert.ok(result.results.slice(1).every(item => item.kind === "vlb-inside"));
  assert.ok(result.results.slice(1).every(item => item.label === "VLB · dentro de palavra"));
  assert.ok(result.results.every(item => !item.source.text.includes("Aierobiar")));

  const unaccented = VLBSearch.search(index, "bia", orthographyModel);
  assert.ok(unaccented.results.every(item => item.sourceLine !== 4770),
    "an unaccented substring must not be presented as an exact biã match");
});

test("entry heads are stable tie-breakers and result labels identify each source side", () => {
  const era = VLBSearch.search(index, "era", orthographyModel);
  assert.equal(era.results[0].sourceLine, 3134);
  assert.equal(era.results[0].kind, "portuguese-whole");
  assert.equal(era.results[0].label, "Português · palavra exata");
  assert.match(era.results[0].source.text, /^Era,/);

  const zurrar = VLBSearch.search(index, "Zurrar", orthographyModel);
  assert.equal(zurrar.results[0].sourceLine, 7678);
  assert.equal(zurrar.results[0].side, "portuguese");

  const vlb = VLBSearch.search(index, "Biã", orthographyModel);
  assert.equal(vlb.results[0].side, "vlb");
});

test("split source records navigate to the fragment that contains the literal match", () => {
  const result = VLBSearch.search(index, "Cetigmã cangupiara", orthographyModel);
  assert.equal(result.directTotal, 1);
  assert.equal(result.results[0].sourceLine, 5859);
  assert.equal(result.results[0].pageId, "II-078");
  assert.equal(result.results[0].kind, "vlb-whole");
});

test("the frozen directional model supplies bounded probable VLB spellings", () => {
  const compiled = VLBSearch.compileModel(orthographyModel);
  assert.equal(compiled.direction, "Navarro modern surface -> Emerson historical surface");
  assert.equal(compiled.weightsAreProbabilities, false);
  assert.ok(Math.abs(compiled.score("akyrara", "Aquîrara") - .07) < 1e-12);

  const result = VLBSearch.search(index, "akyrara", orthographyModel);
  assert.equal(result.directTotal, 0);
  assert.equal(result.probableTotal, 1);
  assert.equal(result.results[0].sourceLine, 46);
  assert.equal(result.results[0].pageId, "I-018");
  assert.equal(result.results[0].kind, "probable");
  assert.equal(result.results[0].scope, "probable");
  assert.equal(result.results[0].queryPath, "orthography-model");
  assert.equal(result.results[0].matchedForm, "aquîrara");
  assert.equal(result.results[0].label, "Navarro → VLB · grafia provável");
  assert.ok(result.results[0].cost <= .15);
  assert.ok(result.results.every(item => item.sourceId?.startsWith("vlb-emerson-") &&
    item.source.entry_index === undefined), "probable matches are VLB source records, not Navarro entries");
});

test("search caps display without losing source-only totals", () => {
  const result = VLBSearch.search(index, "era", orthographyModel, {limit: 10});
  assert.equal(result.results.length, 10);
  assert.ok(result.total > result.results.length);
  assert.ok(result.results.every(item => item.sourceId?.startsWith("vlb-emerson-")));
});
