# Nhe'enga Agent Rules

This repository implements reusable morphology and the Pydicate DSL. It is not a place to force a single corpus line to render as desired.

## Before an engine edit

- Read the relevant `oldtupicorpus` source record, target, and expression-level candidate first.
- Do not change engine code until the human editor has approved the linguistic analysis and established that the source expression alone cannot represent it.
- Identify the smallest behavior being changed and at least one contrast that must remain unchanged.
- Add or update a focused executable regression before broad refactoring.

## Required verification

1. Run the smallest relevant harness or focused script.
2. Run the corresponding `oldtupicorpus` source/ground-truth verification when a historic rendering is affected.
3. Record the historic attestation and contrast in the change note or test comment.

## Boundaries

- Do not modify `ground_truth` from this repository.
- Do not broaden a special case from one construction to all generic/person/object forms without tests for each affected branch.
- Prefer small reviewable diffs. Do not run parallel agents that edit the same morphology modules.

The authoring MCP server lives in the sibling `../oldtupicorpus` checkout. It is useful for retrieving source context and rendering candidates, but it intentionally cannot write files.
