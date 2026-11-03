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
  assert.equal(result.mechanism, "high_precision_model");
  assert.equal(result.source_span.text, "Aguaça pupe aico");
  assert.ok(result.line_ids.length > 0);
  assert.equal(JSON.stringify(item), before, "navigation must not accept or rewrite an association");
});

test("a complete apypyk quotation resolves the older weak tie, while absent inherited references stay manual", () => {
  const quoted = choose(citation(page17, 3255), page17);
  assert.equal(quoted.status,"proposed");
  assert.equal(quoted.source_id,"vlb-emerson-r568-p00030");
  assert.equal(quoted.source_span.text,"Ainheengapigpigc iepe");
  const page109 = readPage("II-109");
  const result = choose(citation(page109, 7915), page109);
  assert.equal(result.status, "ambiguous");
  assert.equal(result.reason, "model_requires_review");
  assert.equal(result.source_id, undefined);
});

test("a full-paragraph candidate cannot point at a continuation missing its form", () => {
  const page29 = readPage("II-029");
  const item = page29.citations.find(item => item.headword === "îuru'ar");
  const result = choose(item, page29);
  assert.equal(result.status, "ambiguous");
  assert.equal(result.reason, "model_requires_review");
  assert.equal(result.source_id, undefined);
});

test("ledger corrections preserve multi-span, ambiguous, and not-found decisions", () => {
  const page50 = readPage("II-050");
  const putuna = page50.citations.find(item => item.entry_index === 9199 && item.correction);
  const multi = choose(putuna,page50);
  assert.equal(multi.status,"reviewed");
  assert.deepEqual(multi.source_spans.map(span => span.text),["Pigtuã","Pigtuniã"]);
  assert.equal(new Set(multi.line_ids).size,2);

  const page62 = readPage("II-062");
  assert.deepEqual(choose(citation(page62,11055),page62),
    {status:"unavailable",reason:"reviewed_correction_not_found"});
  const page83 = readPage("I-083");
  assert.deepEqual(choose(citation(page83,2435),page83),
    {status:"ambiguous",reason:"reviewed_correction_is_ambiguous"});
});

function fixture(word = "aguasa") {
  const page = {fragments:[{id:"source-a",text:`Nome. — ${word}.`,ocr:{status:"aligned",line_ids:["line-a"],boxes:[[0,.1,1,.2]]}}],
    ocr_lines:[{id:"line-a",text:word,box:[0,.1,1,.2]}]};
  const item = {headword:word,associations:[{source_id:"source-a",status:"proposed",score:35,
    evidence:[{type:"loose_headword_form_key"}]}]};
  return {page,item};
}

function modelFixture({quoted = true, context = 0, status = "suggested", queryKind = "quoted_surface_hypothesis"} = {}) {
  const page = {fragments:[{id:"source-a",text:"Nome. — Aguaça pupe.",source_start0:100,
    source_end0:121,ocr:{status:"aligned",line_ids:["line-a"],boxes:[[0,.1,1,.2]]}}],
    ocr_lines:[{id:"line-a",text:"Aguaça pupe",box:[0,.1,1,.2]}]};
  const item = {headword:"agûasá",associations:[{source_id:"source-a",status:"proposed",rank:1,
    algorithm_version:"vlb-page-ranker-v3",proposal_status:status,score:100,score_is_probability:false,
    span:{text:"Aguaça",start0:108,end0:114,ocr_status:"form_token_match",ocr_line_ids:["line-a"],common_token:false},
    query:{kind:queryKind},
    evidence:{quoted_surface:quoted,portuguese_context_score:context,page_boundary_uncertain:false}}]};
  return {page,item};
}

test("V3 navigation validates the exact source span and requires independent context evidence", () => {
  const supported = modelFixture();
  assert.equal(choose(supported.item,supported.page).mechanism, "high_precision_model");
  const formOnly = modelFixture({quoted:false,context:0});
  assert.deepEqual(choose(formOnly.item,formOnly.page), {status:"unavailable",reason:"model_form_only_evidence"});
  const stale = modelFixture();
  stale.item.associations[0].span.text = "Aguaça!";
  assert.deepEqual(choose(stale.item,stale.page), {status:"unavailable",reason:"stale_model_source_span"});
});

test("V3 needs-review and inferred-prefix candidates stay manual", () => {
  const {page,item} = modelFixture({status:"needs_review"});
  item.associations.push({...item.associations[0],source_id:"source-b",rank:2});
  assert.deepEqual(choose(item,page), {status:"ambiguous",reason:"model_requires_review"});
  const prefix = modelFixture({quoted:false,context:1,queryKind:"surface_prefix_hypothesis"});
  assert.deepEqual(choose(prefix.item,prefix.page), {status:"unavailable",reason:"model_prefix_hypothesis_requires_review"});
});

test("a reviewed exact text span remains navigable when no OCR target is available", () => {
  const page = {fragments:[{id:"source-a",text:"Nome. — Aguaça.",source_start0:100,source_end0:115,
    ocr:{status:"partial",line_ids:[],boxes:[]}}],ocr_lines:[]};
  const item = {headword:"agûasá",correction:{disposition:"accepted"},associations:[{source_id:"source-a",status:"reviewed",
    span:{text:"Aguaça",start0:108,end0:114,ocr_line_ids:[],ocr_boxes:[]}}]};
  const result = choose(item,page);
  assert.equal(result.status,"reviewed");
  assert.equal(result.source_id,"source-a");
  assert.deepEqual(result.line_ids,[]);
  assert.equal(result.source_span.text,"Aguaça");
  item.associations[0].span.text = "stale";
  assert.deepEqual(choose(item,{...page}), {status:"unavailable",reason:"stale_reviewed_source_span"});
});

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
  let navigableAcceptedCorrections = 0;
  for (const file of fs.readdirSync(data).filter(file => file.endsWith(".json.gz"))) {
    const page = readPage(file.replace(/\.json\.gz$/, ""));
    for (const item of page.citations) {
      const reviewed = item.associations.filter(association =>
        association.status === "reviewed" && !association.suppressed_by_correction);
      if (item.correction?.disposition === "accepted" && reviewed.length &&
          new Set(reviewed.map(association => association.source_id)).size === 1) {
        navigableAcceptedCorrections++;
      }
      const result = choose(item,page);
      counts[result.status]++;
      if (!result.source_id) {
        assert.ok(["ambiguous","unavailable"].includes(result.status));
        continue;
      }
      const association = item.associations.find(a => a.source_id === result.source_id);
      const fragment = page.fragments.find(f => f.id === result.source_id);
      assert.equal(association.status, result.status);
      if (!result.line_ids.length) {
        assert.equal(result.status,"reviewed",
          "only an exact reviewed source span may remain navigable without OCR targets");
        assert.deepEqual(association.span?.ocr_line_ids || [],[]);
      }
      for (const id of result.line_ids) {
        assert.ok(fragment.ocr.line_ids.includes(id));
        assert.ok(page.ocr_lines.some(line => line.id === id));
      }
    }
  }
  assert.equal(counts.reviewed, navigableAcceptedCorrections);
  assert.ok(counts.proposed > 2000, "useful evidence-backed navigation exists across both volumes");
  assert.ok(counts.ambiguous > 0 && counts.unavailable > 0, "not every retrieval hit becomes a target");
  console.log("VLB automatic targeting", counts);
});
