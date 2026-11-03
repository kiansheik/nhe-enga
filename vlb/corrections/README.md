# VLB correction ledger

`ledger.jsonl` is the durable editorial layer for Navarro-to-VLB matching. It
does not rewrite Navarro's dictionary snapshot, Emerson's transcription, the
OCR snapshot, or a frozen mining experiment.

Each canonical JSON line is an immutable event for one exact
`(citation_id, page_id)` correction stream. A later decision appends the next
revision and names the event it supersedes. Earlier lines remain history.
`selected_spans` is always an array, including when one citation legitimately
accepts several historical forms. This prevents a later save from collapsing
the two accepted `putuna` alternatives into a single span.

## What validation establishes

`python3 vlb/manage_corrections.py validate` checks all of the following
against the pinned repository inputs:

- exact citation occurrence, dictionary row, definition hash, and original
  definition offsets;
- original and generated page membership, printed volume, and page;
- exact source IDs, unchanged source text, global half-open character offsets,
  and page-fragment boundaries;
- OCR line membership and boxes; a reviewer-corrected box must name the old
  pinned box as well as its replacement;
- source, dictionary, citation, page-alignment, and OCR hashes;
- the frozen algorithm version and candidate-output hash of a saved proposal;
- deterministic correction/event IDs, monotonic revisions, explicit
  supersession, and conflicting or stale updates;
- reviewer provenance and the rule that automated suggestions cannot become
  reviewed regression or training evidence.

The checked-in first revision contains eight assistant-reviewed decisions. It
records six accepted matches, the unresolved `aembé` ambiguity, and the
botanical `'ybapekanga` sense as not found on its cited page. These are
assistant reviews, not human verification. All eight are development
regressions; none is approved for training.

## Import contract

An import file or fenced GitHub issue payload has this envelope:

```json
{
  "schema_version": "vlb-correction-submission-1",
  "events": [
    {"schema_version": 1, "event_id": "...", "correction_id": "..."}
  ]
}
```

The event itself must satisfy `schema.json` and the stricter live-data checks
in `ledger.py`. Import is idempotent: an identical existing event is skipped;
the same event ID with different content is rejected. The entire combined
history is validated before any new canonical lines are appended.

```sh
python3 vlb/manage_corrections.py import --input correction.json --dry-run
python3 vlb/manage_corrections.py import --input correction.json
python3 vlb/manage_corrections.py import --input issue-body.md --issue-body
```

The static reader needs no GitHub credential. It can download the same JSON
envelope and, when the user chooses to submit, open the repository's VLB issue
form for copy/paste. A maintainer then runs the manually dispatched
`VLB correction import` workflow with the issue number. The workflow treats
the issue body as untrusted data, runs this validator, appends only the ledger,
and opens a reviewable pull request. It does not execute issue content.

## Feedback exports

Only the latest revision in each stream is exported. Inclusion is explicit in
the review fields rather than inferred from a model suggestion.

```sh
python3 vlb/manage_corrections.py export --kind regression --output /tmp/vlb-regressions.json
python3 vlb/manage_corrections.py export --kind training --output /tmp/vlb-training.json
```

The regression export currently includes all eight decisions. The training
export is deliberately empty until a reviewer explicitly approves a later
revision for that use.
