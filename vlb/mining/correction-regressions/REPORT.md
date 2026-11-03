# VLB correction-ledger development regressions

This report evaluates the latest V3 proposals and the production navigation
policy against the latest ledger revisions explicitly approved for regression.
Ledger overrides are removed before scoring. These records are development
evidence, not a fresh held-out sample or a corpus-wide accuracy estimate. No
independent human verification is claimed for this evaluation. Reviewer
provenance in this snapshot is assistant: 8. Ranking scores are not probabilities.

## Retrieval

- Approved records: 8 (6 accepted, 1 ambiguous, 1 not found, 0 rejected, 0 unresolved).
- Correct first paragraph: 6/6 (100.0%).
- Correct paragraph in the first three candidates: 6/6 (100.0%).
- Correct first exact span: 6/6 (100.0%).
- Correct exact span among offered alternatives: 6/6 (100.0%).
- Individual accepted spans offered: 7/7 (100.0%).

## Production navigation policy

- Automatic targets: 2/8 (25.0% overall); 2/6 (33.3%) on accepted records.
- Correct automatic paragraphs: 2/2 (100.0% precision).
- Correct automatic exact spans: 2/2 (100.0% precision).
- False-positive automatic targets: 0.
- Ambiguous abstentions: 1/1 (100.0%).
- Not-found abstentions: 1/1 (100.0%).

The high-precision gate passes: No automatic target on an approved regression may miss its accepted exact span or assert a target for ambiguous/not-found evidence.
The checked JSON records each citation, proposed result, abstention reason, and
exact-span comparison so a model or policy change produces a reviewable diff.
