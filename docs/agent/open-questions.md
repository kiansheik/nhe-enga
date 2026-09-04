# Open Questions

- Should generated dictionary/data files under `docs/` be removed from the source branch too, with a data build step required before Pages deployment?
- Should primary-source page images move out of the source branch after adding a reliable regeneration or artifact-preservation step?
- Is `sentence-builder.html` still a supported public page? Its wheel path now targets the generated Pages grammar artifact, but its UX and Pyodide behavior were not browser-tested in this cleanup.
- Are `gramatica/package.json` and `gramatica/package-lock.json` still useful, or are they leftovers from before `gramatica/docs/package.json` became the active VuePress package?
