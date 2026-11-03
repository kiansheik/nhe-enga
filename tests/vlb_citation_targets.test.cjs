// Run: node --test tests/vlb_citation_targets.test.cjs
// Navigation suggestions must preserve uncertainty and the exact cited occurrence.
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const zlib = require("node:zlib");
const {choose} = require("../vlb/citation-targets.js");
const data = path.join(__dirname, "../vlb/data/pages");
const readPage = id => JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(data, id + ".json.gz"))));
const page17 = readPage("I-017");
const citation = (page, row) => page.citations.find(item => item.entry_index === row);

test("reviewed mokanãî targets only the named Aimocanãy attestation", () => {
  const result = choose(citation(page17, 7210), page17);
  assert.equal(result.status, "reviewed");
  assert.equal(result.source_id, "vlb-emerson-r568-p00013");
  assert.equal(result.source_form, "Aimocanãy");
  assert.equal(result.scope, "form");
  assert.ok(result.line_ids.length > 0);
  const lines = page17.ocr_lines.filter(line => result.line_ids.includes(line.id));
  assert.ok(lines.every(line => line.text.includes("Aimocanãy")));
  assert.equal(citation(page17, 7210).associations[0].covers_entire_source_record, false);
});

test("the separately cited motumung continuation is not inherited as reviewed", () => {
  assert.equal(choose(citation(page17, 7574), page17).status, "reviewed");
  const page110 = readPage("II-110");
  assert.notEqual(choose(citation(page110, 7574), page110).status, "reviewed");
});

test("a unique agûasá OCR form is a proposed jump, even when translations differ", () => {
  const item = citation(page17, 2480);
  const before = JSON.stringify(item);
  const result = choose(item, page17);
  assert.equal(result.status, "proposed");
  assert.equal(result.source_id, "vlb-emerson-r568-p00025");
  assert.equal(result.scope, "form");
  assert.equal(result.mechanism, "form_in_ocr");
  assert.ok(result.line_ids.length > 0);
  assert.equal(JSON.stringify(item), before, "navigation must not accept or rewrite an association");
});

test("weak tied apypyk candidates and absent inherited references do not choose a line", () => {
  assert.deepEqual(choose(citation(page17, 3255), page17), {status:"ambiguous",reason:"tied_candidates"});
  const page109 = readPage("II-109");
  const result = choose(citation(page109, 7915), page109);
  assert.equal(result.status, "unavailable");
  assert.equal(result.reason, "no_association");
  assert.equal(result.source_id, undefined);
});

test("a full-paragraph candidate cannot point at a continuation missing its form", () => {
  const page29 = readPage("II-029");
  const item = page29.citations.find(item => item.headword === "îuru'ar");
  const result = choose(item, page29);
  assert.equal(result.status, "unavailable");
  assert.equal(result.reason, "form_not_in_this_fragment");
});

function fixture(word = "aguasa") {
  const page = {fragments:[{id:"source-a",text:`Nome. — ${word}.`,ocr:{status:"aligned",line_ids:["line-a"],boxes:[[0,.1,1,.2]]}}],
    ocr_lines:[{id:"line-a",text:word,box:[0,.1,1,.2]}]};
  const item = {headword:word,associations:[{source_id:"source-a",status:"proposed",score:35,
    evidence:[{type:"loose_headword_form_key"}]}]};
  return {page,item};
}

test("forms repeated outside the shortlisted candidate remain ambiguous", () => {
  const {page,item} = fixture();
  page.fragments.push({id:"source-b",text:"Outro sentido. — Aguasa.",ocr:{status:"aligned",line_ids:["line-b"]}});
  page.ocr_lines.push({id:"line-b",text:"Aguasa",box:[0,.3,1,.4]});
  assert.deepEqual(choose(item,page), {status:"ambiguous",reason:"form_repeated_in_page"});
});

test("OCR hits outside the selected fragment do not silently become a single-line match", () => {
  const {page,item} = fixture();
  page.ocr_lines.push({id:"line-b",text:"Aguasa",box:[0,.3,1,.4]});
  assert.deepEqual(choose(item,page), {status:"ambiguous",reason:"ocr_form_outside_fragment"});
});

test("short/common aliases and missing aligned OCR need manual review", () => {
  for (const word of ["aba", "como"]) {
    const {page,item} = fixture(word);
    assert.equal(choose(item,page).reason, "short_or_common_ocr_only_alias");
  }
  const {page,item} = fixture();
  page.fragments[0].ocr.status = "partial";
  assert.equal(choose(item,page).reason, "source_without_aligned_ocr");
});

test("every automatic jump retains its status and uses valid OCR lines on the cited page", () => {
  const counts = {reviewed:0,proposed:0,ambiguous:0,unavailable:0};
  for (const file of fs.readdirSync(data).filter(file => file.endsWith(".json.gz"))) {
    const page = readPage(file.replace(/\.json\.gz$/, ""));
    for (const item of page.citations) {
      const result = choose(item,page);
      counts[result.status]++;
      if (!result.source_id) {
        assert.ok(["ambiguous","unavailable"].includes(result.status));
        continue;
      }
      const association = item.associations.find(a => a.source_id === result.source_id);
      const fragment = page.fragments.find(f => f.id === result.source_id);
      assert.equal(association.status, result.status);
      assert.ok(result.line_ids.length > 0);
      for (const id of result.line_ids) {
        assert.ok(fragment.ocr.line_ids.includes(id));
        assert.ok(page.ocr_lines.some(line => line.id === id));
      }
    }
  }
  assert.equal(counts.reviewed, 2);
  assert.ok(counts.proposed > 1000, "useful evidence-backed navigation exists across both volumes");
  assert.ok(counts.ambiguous > 0 && counts.unavailable > 0, "not every retrieval hit becomes a target");
  console.log("VLB automatic targeting", counts);
});
