#!/usr/bin/env node
"use strict";

// Development regression evaluation for durable VLB corrections. This calls
// the reader's production target chooser, but removes reviewed associations
// and correction overrides before scoring so the model cannot grade itself
// against the answer already projected into the page data.

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const zlib = require("node:zlib");

const ROOT = path.resolve(__dirname, "..");
const VLB = path.join(ROOT, "vlb");
const LEDGER = path.join(VLB, "corrections", "ledger.jsonl");
const MANIFEST = path.join(VLB, "data", "manifest.json");
const TARGET_POLICY = path.join(VLB, "citation-targets.js");
const OUTPUT = path.join(VLB, "mining", "correction-regressions");
const {choose} = require(TARGET_POLICY);

function sha256(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

function readJSON(file) {
  const bytes = fs.readFileSync(file);
  return JSON.parse(path.extname(file) === ".gz" ? zlib.gunzipSync(bytes) : bytes);
}

function latestApprovedEvents() {
  const latest = new Map();
  for (const raw of fs.readFileSync(LEDGER, "utf8").split(/\r?\n/)) {
    if (!raw.trim()) continue;
    const event = JSON.parse(raw);
    const previous = latest.get(event.correction_id);
    if (!previous || event.revision > previous.revision) latest.set(event.correction_id, event);
  }
  return [...latest.values()]
    .filter(event => event.review.approved_for_regression === true)
    .sort((a, b) => a.citation.citation_id.localeCompare(b.citation.citation_id) ||
      a.page.page_id.localeCompare(b.page.page_id));
}

function exactSpan(sourceId, span, gold) {
  return Boolean(span && gold.some(item => item.source_id === sourceId &&
    item.start0 === span.start0 && item.end0 === span.end0 && item.text === span.text));
}

function ratio(numerator, denominator) {
  return denominator ? Number((numerator / denominator).toFixed(6)) : null;
}

function percent(value) {
  return value === null ? "n/a" : `${(value * 100).toFixed(1)}%`;
}

function evaluate() {
  const manifest = readJSON(MANIFEST);
  const ledgerSha256 = sha256(LEDGER);
  if (manifest.provenance.correction_ledger_sha256 !== ledgerSha256) {
    throw new Error("Reader data is stale relative to vlb/corrections/ledger.jsonl; rebuild vlb/data first");
  }
  const pageFiles = new Map(manifest.pages.map(page => [page.id, page.data_file]));
  const pageCache = new Map();
  const events = latestApprovedEvents();
  const records = [];

  function pageData(pageId) {
    if (!pageCache.has(pageId)) {
      const file = pageFiles.get(pageId);
      if (!file) throw new Error(`Correction regression names unknown page ${pageId}`);
      pageCache.set(pageId, readJSON(path.join(VLB, "data", file)));
    }
    return pageCache.get(pageId);
  }

  for (const event of events) {
    const page = pageData(event.page.page_id);
    const citation = page.citations.find(item => item.id === event.citation.citation_id);
    if (!citation) throw new Error(`Correction regression cannot find ${event.citation.citation_id} on ${page.id}`);

    // Suppression is a consequence of the correction, not a property of the
    // frozen model proposal. Remove it together with reviewed associations.
    const proposals = (citation.associations || [])
      .filter(association => association.status === "proposed" && association.algorithm_version)
      .map(association => {
        const copy = {...association};
        delete copy.suppressed_by_correction;
        return copy;
      })
      .sort((a, b) => (a.rank || 999) - (b.rank || 999) || (b.score || 0) - (a.score || 0));
    const modelCitation = {...citation, correction: null, associations: proposals};
    const target = choose(modelCitation, page);
    const automatic = target.status === "proposed" && Boolean(target.source_id);
    const accepted = event.disposition === "accepted";
    const gold = event.selected_spans || [];
    const goldSources = new Set(gold.map(span => span.source_id));
    const top1 = proposals[0] || null;
    const top3 = proposals.slice(0, 3);
    const offered = top3.flatMap(candidate =>
      [candidate.span, ...(candidate.span_alternatives || [])]
        .filter(Boolean)
        .map(span => ({source_id: candidate.source_id, span}))
    );
    const recoveredGold = new Set();
    for (let index = 0; index < gold.length; index += 1) {
      if (offered.some(item => exactSpan(item.source_id, item.span, [gold[index]]))) recoveredGold.add(index);
    }
    const automaticParagraphCorrect = automatic && accepted && goldSources.has(target.source_id);
    const automaticExactCorrect = automatic && accepted && exactSpan(target.source_id, target.source_span, gold);
    const top1ParagraphCorrect = accepted && Boolean(top1) && goldSources.has(top1.source_id);
    const top3ParagraphCorrect = accepted && top3.some(candidate => goldSources.has(candidate.source_id));
    const top1ExactCorrect = accepted && Boolean(top1) && exactSpan(top1.source_id, top1.span, gold);
    const offeredExactCorrect = accepted && offered.some(item => exactSpan(item.source_id, item.span, gold));

    records.push({
      event_id: event.event_id,
      correction_id: event.correction_id,
      citation_id: event.citation.citation_id,
      entry_index: event.citation.entry_index,
      headword: event.citation.headword,
      page_id: event.page.page_id,
      disposition: event.disposition,
      reviewer_type: event.review.reviewer_type,
      selected_spans: gold.map(span => ({source_id: span.source_id, start0: span.start0,
        end0: span.end0, text: span.text})),
      retrieval: {
        candidates: proposals.length,
        top1_source_id: top1?.source_id || null,
        top1_span: top1?.span ? {start0: top1.span.start0, end0: top1.span.end0, text: top1.span.text} : null,
        top1_paragraph_correct: top1ParagraphCorrect,
        top3_paragraph_correct: top3ParagraphCorrect,
        top1_exact_span_correct: top1ExactCorrect,
        offered_exact_span_correct: offeredExactCorrect,
        accepted_spans_offered: recoveredGold.size,
      },
      production_policy: {
        automatic_target: automatic,
        status: target.status,
        reason: target.reason || null,
        source_id: target.source_id || null,
        source_span: target.source_span ? {start0: target.source_span.start0,
          end0: target.source_span.end0, text: target.source_span.text} : null,
        paragraph_correct: automaticParagraphCorrect,
        exact_span_correct: automaticExactCorrect,
        false_positive: automatic && !automaticExactCorrect,
      },
    });
  }

  const accepted = records.filter(record => record.disposition === "accepted");
  const ambiguous = records.filter(record => record.disposition === "ambiguous");
  const notFound = records.filter(record => record.disposition === "not_found");
  const rejected = records.filter(record => record.disposition === "rejected");
  const unresolved = records.filter(record => record.disposition === "unresolved");
  const uncertain = records.filter(record => record.disposition !== "accepted");
  const automatic = records.filter(record => record.production_policy.automatic_target);
  const acceptedAutomatic = accepted.filter(record => record.production_policy.automatic_target);
  const automaticParagraph = records.filter(record => record.production_policy.paragraph_correct);
  const automaticExact = records.filter(record => record.production_policy.exact_span_correct);
  const falsePositive = records.filter(record => record.production_policy.false_positive);
  const acceptedGoldSpans = accepted.reduce((count, record) => count + record.selected_spans.length, 0);
  const offeredGoldSpans = accepted.reduce((count, record) => count + record.retrieval.accepted_spans_offered, 0);
  const reviewerTypes = Object.fromEntries([...new Set(records.map(record => record.reviewer_type))]
    .sort().map(kind => [kind, records.filter(record => record.reviewer_type === kind).length]));

  const counts = {
    regression_records: records.length,
    accepted_records: accepted.length,
    ambiguous_records: ambiguous.length,
    not_found_records: notFound.length,
    rejected_records: rejected.length,
    unresolved_records: unresolved.length,
    paragraph_top1_correct: accepted.filter(record => record.retrieval.top1_paragraph_correct).length,
    paragraph_top3_correct: accepted.filter(record => record.retrieval.top3_paragraph_correct).length,
    exact_span_top1_correct: accepted.filter(record => record.retrieval.top1_exact_span_correct).length,
    exact_span_offered_correct: accepted.filter(record => record.retrieval.offered_exact_span_correct).length,
    accepted_spans: acceptedGoldSpans,
    accepted_spans_offered: offeredGoldSpans,
    automatic_targets: automatic.length,
    accepted_automatic_targets: acceptedAutomatic.length,
    automatic_correct_paragraph: automaticParagraph.length,
    automatic_exact_span: automaticExact.length,
    false_positive_automatic_targets: falsePositive.length,
    abstentions: records.length - automatic.length,
    uncertain_abstentions: uncertain.filter(record => !record.production_policy.automatic_target).length,
    ambiguous_abstentions: ambiguous.filter(record => !record.production_policy.automatic_target).length,
    not_found_abstentions: notFound.filter(record => !record.production_policy.automatic_target).length,
  };
  const rates = {
    paragraph_top1_recall: ratio(counts.paragraph_top1_correct, accepted.length),
    paragraph_top3_recall: ratio(counts.paragraph_top3_correct, accepted.length),
    exact_span_top1_recall: ratio(counts.exact_span_top1_correct, accepted.length),
    exact_span_offered_recall: ratio(counts.exact_span_offered_correct, accepted.length),
    accepted_span_offered_recall: ratio(counts.accepted_spans_offered, counts.accepted_spans),
    automatic_coverage_all: ratio(counts.automatic_targets, records.length),
    automatic_coverage_accepted: ratio(counts.accepted_automatic_targets, accepted.length),
    automatic_paragraph_precision: ratio(counts.automatic_correct_paragraph, counts.automatic_targets),
    automatic_exact_span_precision: ratio(counts.automatic_exact_span, counts.automatic_targets),
    uncertain_abstention_rate: ratio(counts.uncertain_abstentions, uncertain.length),
    ambiguity_abstention_rate: ratio(counts.ambiguous_abstentions, ambiguous.length),
    not_found_abstention_rate: ratio(counts.not_found_abstentions, notFound.length),
  };

  return {
    schema_version: 1,
    evaluation_role: "Development regression from approved correction-ledger decisions; not held-out evaluation or a corpus-wide accuracy estimate.",
    human_verified: false,
    score_interpretation: "Model ranking scores are not probabilities.",
    inputs: {
      proposal_algorithm_version: manifest.provenance.proposal_algorithm_version,
      navigation_policy_version: manifest.provenance.navigation_policy_version,
      proposal_output_sha256: manifest.provenance.proposal_output_sha256,
      correction_ledger_sha256: ledgerSha256,
      citation_target_policy_sha256: sha256(TARGET_POLICY),
      viewer_manifest_sha256: sha256(MANIFEST),
      selection: "Latest correction revision with review.approved_for_regression=true",
    },
    reviewer_types: reviewerTypes,
    counts,
    rates,
    high_precision_gate: {
      passed: counts.false_positive_automatic_targets === 0,
      requirement: "No automatic target on an approved regression may miss its accepted exact span or assert a target for ambiguous/not-found evidence.",
    },
    records,
  };
}

function renderJSON(evaluation) {
  return JSON.stringify(evaluation, null, 2) + "\n";
}

function renderReport(evaluation) {
  const {counts: c, rates: r} = evaluation;
  const reviewers = Object.entries(evaluation.reviewer_types)
    .map(([kind, count]) => `${kind}: ${count}`).join(", ") || "none";
  return `# VLB correction-ledger development regressions

This report evaluates the latest V3 proposals and the production navigation
policy against the latest ledger revisions explicitly approved for regression.
Ledger overrides are removed before scoring. These records are development
evidence, not a fresh held-out sample or a corpus-wide accuracy estimate. No
independent human verification is claimed for this evaluation. Reviewer
provenance in this snapshot is ${reviewers}. Ranking scores are not probabilities.

## Retrieval

- Approved records: ${c.regression_records} (${c.accepted_records} accepted, ${c.ambiguous_records} ambiguous, ${c.not_found_records} not found, ${c.rejected_records} rejected, ${c.unresolved_records} unresolved).
- Correct first paragraph: ${c.paragraph_top1_correct}/${c.accepted_records} (${percent(r.paragraph_top1_recall)}).
- Correct paragraph in the first three candidates: ${c.paragraph_top3_correct}/${c.accepted_records} (${percent(r.paragraph_top3_recall)}).
- Correct first exact span: ${c.exact_span_top1_correct}/${c.accepted_records} (${percent(r.exact_span_top1_recall)}).
- Correct exact span among offered alternatives: ${c.exact_span_offered_correct}/${c.accepted_records} (${percent(r.exact_span_offered_recall)}).
- Individual accepted spans offered: ${c.accepted_spans_offered}/${c.accepted_spans} (${percent(r.accepted_span_offered_recall)}).

## Production navigation policy

- Automatic targets: ${c.automatic_targets}/${c.regression_records} (${percent(r.automatic_coverage_all)} overall); ${c.accepted_automatic_targets}/${c.accepted_records} (${percent(r.automatic_coverage_accepted)}) on accepted records.
- Correct automatic paragraphs: ${c.automatic_correct_paragraph}/${c.automatic_targets} (${percent(r.automatic_paragraph_precision)} precision).
- Correct automatic exact spans: ${c.automatic_exact_span}/${c.automatic_targets} (${percent(r.automatic_exact_span_precision)} precision).
- False-positive automatic targets: ${c.false_positive_automatic_targets}.
- Ambiguous abstentions: ${c.ambiguous_abstentions}/${c.ambiguous_records} (${percent(r.ambiguity_abstention_rate)}).
- Not-found abstentions: ${c.not_found_abstentions}/${c.not_found_records} (${percent(r.not_found_abstention_rate)}).

The high-precision gate ${evaluation.high_precision_gate.passed ? "passes" : "fails"}: ${evaluation.high_precision_gate.requirement}
The checked JSON records each citation, proposed result, abstention reason, and
exact-span comparison so a model or policy change produces a reviewable diff.
`;
}

function writeOrCheck(mode) {
  const evaluation = evaluate();
  const files = new Map([
    [path.join(OUTPUT, "evaluation.json"), renderJSON(evaluation)],
    [path.join(OUTPUT, "REPORT.md"), renderReport(evaluation)],
  ]);
  if (mode === "--write") {
    fs.mkdirSync(OUTPUT, {recursive: true});
    for (const [file, content] of files) fs.writeFileSync(file, content);
  } else if (mode === "--check") {
    for (const [file, content] of files) {
      if (!fs.existsSync(file) || fs.readFileSync(file, "utf8") !== content) {
        throw new Error(`${path.relative(ROOT, file)} is stale; run node vlb/evaluate_corrections.cjs --write`);
      }
    }
  } else if (mode) {
    throw new Error("Usage: node vlb/evaluate_corrections.cjs [--write|--check]");
  }
  console.log(JSON.stringify({counts: evaluation.counts, rates: evaluation.rates,
    high_precision_gate: evaluation.high_precision_gate, mode: mode || "print"}, null, 2));
  return evaluation;
}

if (require.main === module) {
  try { writeOrCheck(process.argv[2]); }
  catch (error) { console.error(error.message); process.exitCode = 1; }
}

module.exports = {evaluate, renderJSON, renderReport, writeOrCheck};
