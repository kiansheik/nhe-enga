# Claude Code instructions

Read `AGENTS.md` first. This repository is the reusable Old Tupi morphology and Pydicate engine.

Before changing morphology code for a corpus line:

1. Use the sibling `oldtupi-authoring` MCP tools to inspect the relevant source record and precedents.
2. Confirm that the human editor has approved the linguistic analysis.
3. Show why the problem cannot be represented at the source-expression level.
4. Add a focused regression and identify a contrast that must remain unchanged.
5. Run focused checks and then the affected corpus verification in `../oldtupicorpus`.

Never change the engine merely to force one source target to pass. Do not modify corpus ground truth from this repository.
