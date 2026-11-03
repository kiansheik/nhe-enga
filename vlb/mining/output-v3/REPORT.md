# VLB alignment V3 evaluation

V3 predictions and code were frozen before the independent review packet was annotated. The 24-case review is assistant-produced and not human-verified, so these are bounded sample results rather than corpus-wide accuracy estimates.

## Frozen ranker on the fresh blind sample

- Clear cases: 21 of 24; ambiguous: 3; not found: 0.
- Correct first paragraph: 20/21 (95.2%).
- Correct paragraph in the first three: 21/21 (100.0%).
- Exact first span: 15/21 (71.4%).
- Exact span among offered alternatives: 19/21 (90.5%).
- Previous reader ranking, for comparison only: top paragraph 15/21; top three 18/21.

## Automatic navigation policy

The policy present when labels were released targeted 10 cases. It chose a correct clear-case paragraph in 9, but also targeted 1 ambiguous case. That false-positive signal is retained here.

After release, that failure became a development regression. The browser policy now abstains from automatically asserting inferred prefix hypotheses; candidates remain available for manual review. Reuse of this sample for the gate is not a new held-out result:

- Automatic targets: 9.
- Clear-case coverage: 9/21 (42.9%).
- Paragraph precision across all automatic targets: 9/9 (100.0%).
- Exact-span precision across all automatic targets: 8/9 (88.9%).
- Ambiguous/not-found abstention: 3/3 (100.0%).
- Narrowed OCR line available: 9/9.

OCR line availability is not exact scan-glyph accuracy. The boxes cover OCR line regions and are not human-verified glyph boxes.

## Integrity

- Prediction SHA-256: `98cde030318d3e2131b0c6df38f3aa77fd1b80444445d4bedc833843461e4928`
- Blind packet SHA-256: `a64adf5225b2477773089c4b9543c1c92b070475d44c341831e3e2cfc0ba1d31`
- Labels SHA-256: `ab73a469e445b722a4f55479daf513731a13b1d7cb5a30ec7988439eff422685`
- Pre-V3 reader ranking SHA-256: `2a962643459153a91fd2a0c9d06139844a177becfae80a9c82bcc7d42133456f` (commit `b5df369af6a7d2db72f933746ca6b5c13a44310d`).

Reproduce with `python3 vlb/mining/benchmark-v3/validate_annotations.py` and `python3 vlb/mining/evaluate_v3.py`.
