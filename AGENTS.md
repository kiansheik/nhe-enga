# Nhe'enga Agent Rules

This repository implements reusable morphology and the Pydicate DSL. It is not a place to force a single corpus line to render as desired.

## Before an engine edit

- Read the relevant `oldtupicorpus` source record, target, and expression-level candidate first.
- Do not change engine code until the human editor has approved the linguistic analysis and established that the source expression alone cannot represent it.
- Check `docs/agent/grammar-navigation.md` for a phenomenon close to what you're fixing before searching blind — it's a living map of where things live in `pydicate`/`tupi`, kept current by past fixes.
- Identify the smallest behavior being changed and at least one contrast that must remain unchanged.
- Add or update a focused executable regression before broad refactoring.
- Never fix a mismatch by editing the `oldtupicorpus` expression to fabricate a new inline lexicon entry (a `Noun(...)`/`Verb(...)`/stem constructed only to bake in the desired surface). That renders correctly while discarding the linguistic claim the expression made, which is worse than leaving the bug unfixed. If the expression itself looks wrong, say so and stop — that judgment belongs to the human editor, not an automated edit here.

## After an engine edit

- Add or correct an entry in `docs/agent/grammar-navigation.md`: the phenomenon, exactly where it's implemented, and one gotcha. Keep it short — put the full root-cause narrative in `AGENT_NOTES.md` or a `docs/agent/session-handoffs/` entry and link to it instead. This is what makes the next agent faster than you were.

## Required verification

1. Run the smallest relevant harness or focused script.
2. Run the corresponding `oldtupicorpus` source/ground-truth verification when a historic rendering is affected.
3. Record the historic attestation and contrast in the change note or test comment.

## Boundaries

- Do not modify `ground_truth` from this repository.
- Do not broaden a special case from one construction to all generic/person/object forms without tests for each affected branch.
- Prefer small reviewable diffs. Do not run parallel agents that edit the same morphology modules.

The authoring MCP server lives in the sibling `../oldtupicorpus` checkout. It is useful for retrieving source context and rendering candidates, but it intentionally cannot write files.
