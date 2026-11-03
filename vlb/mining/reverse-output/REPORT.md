# VLB source-to-dictionary reverse concordance

This inventory starts from all **7,534** lexicographic
records in the pinned Emerson transcription and retains bounded Navarro
dictionary candidates for future review. It is not loaded by the browser and
does not alter the frozen V1/V2 experiments.

## Recomputed inventory

| Status | Records |
| --- | ---: |
| Candidate linked (still not paragraph coverage) | 3,771 |
| Ambiguous candidates | 2,949 |
| Unmatched | 814 |
| Records with at least one retained candidate | 6,720 |
| Fully covered records | 0 |

The earlier reported 7,094/440 split was not assumed. These counts were
recomputed from the checked-in dictionary, transcription, frozen V2 proposals,
and V2 directional spelling model. `candidate_linked` means only that the
ranking has a separated strong candidate. `ambiguous` and `unmatched` remain
unresolved. All unreviewed candidates require lexical and semantic review.

## Evidence and reproduction

The artifact combines inverted V2 citation candidates with literal dictionary
headwords, explicit editorial variants, and the same bounded prefix hypotheses
used by V2. Every saved source span is validated against the unchanged source
text and a page membership. Scores are deterministic ranking weights, not
probabilities.

```sh
python3 vlb/build_reverse_concordance.py
python3 -m unittest tests.test_vlb_reverse_concordance
```

Artifact SHA-256: `62ef0dccae2c70e61bc65b4af8b7ca9adc304e9058d35385106cd6edd9baed51`.
