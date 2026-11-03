"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const childProcess = require("node:child_process");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const {evaluate, renderJSON, renderReport} = require("../vlb/evaluate_corrections.cjs");

test("approved ledger decisions dynamically score the frozen model and production policy", () => {
  const evaluation = evaluate();
  const {counts, records} = evaluation;
  assert.equal(evaluation.evaluation_role.includes("Development regression"), true);
  assert.equal(evaluation.human_verified, false);
  const reviewerTypes = records.reduce((totals, record) => {
    totals[record.reviewer_type] = (totals[record.reviewer_type] || 0) + 1;
    return totals;
  }, {});
  assert.deepEqual(evaluation.reviewer_types,
    Object.fromEntries(Object.entries(reviewerTypes).sort(([left], [right]) => left.localeCompare(right))));
  assert.equal(Object.values(evaluation.reviewer_types).reduce((total, count) => total + count, 0),records.length);
  assert.equal(counts.regression_records,records.length);
  for (const [disposition, field] of [
    ["accepted","accepted_records"],
    ["ambiguous","ambiguous_records"],
    ["not_found","not_found_records"],
    ["rejected","rejected_records"],
    ["unresolved","unresolved_records"],
  ]) {
    assert.equal(counts[field],records.filter(record => record.disposition === disposition).length);
  }
  assert.equal(counts.accepted_records + counts.ambiguous_records + counts.not_found_records +
    counts.rejected_records + counts.unresolved_records,records.length);
  assert.equal(records.every(record => record.production_policy.status !== "reviewed"), true,
    "ledger overrides must be removed before evaluating the model");
  const accepted = records.filter(record => record.disposition === "accepted");
  const uncertain = records.filter(record => record.disposition !== "accepted");
  const automatic = records.filter(record => record.production_policy.automatic_target);
  const falsePositive = records.filter(record => record.production_policy.false_positive);
  assert.equal(counts.accepted_spans,
    accepted.reduce((total, record) => total + record.selected_spans.length,0));
  assert.equal(counts.accepted_spans_offered,
    accepted.reduce((total, record) => total + record.retrieval.accepted_spans_offered,0));
  assert.ok(counts.accepted_spans_offered <= counts.accepted_spans);
  assert.equal(counts.automatic_targets,automatic.length);
  assert.equal(counts.accepted_automatic_targets,
    accepted.filter(record => record.production_policy.automatic_target).length);
  assert.equal(counts.automatic_correct_paragraph,
    records.filter(record => record.production_policy.paragraph_correct).length);
  assert.equal(counts.automatic_exact_span,
    records.filter(record => record.production_policy.exact_span_correct).length);
  assert.equal(counts.false_positive_automatic_targets,falsePositive.length);
  assert.equal(counts.abstentions,records.length - automatic.length);
  assert.equal(counts.uncertain_abstentions,uncertain.length,
    "ambiguous, not-found, rejected, and unresolved evidence must never become automatic targets");
  assert.equal(counts.ambiguous_abstentions,counts.ambiguous_records);
  assert.equal(counts.not_found_abstentions,counts.not_found_records);
  assert.equal(evaluation.high_precision_gate.passed,
    counts.false_positive_automatic_targets === 0);
  assert.equal(evaluation.high_precision_gate.passed, true);
  assert.equal(counts.false_positive_automatic_targets,0);
});

test("checked regression outputs are deterministic and current", () => {
  const evaluation = evaluate();
  assert.ok(renderJSON(evaluation).endsWith("\n"));
  assert.match(renderReport(evaluation), /No\s+independent human verification/);
  childProcess.execFileSync(process.execPath, ["vlb/evaluate_corrections.cjs", "--check"],
    {cwd: root, stdio: "pipe"});
});
