# Qualification grammar comments, 24 September 2026

Added five comment-only `# @grammar` annotations next to existing Pydicate/Tupi
methods. They explain implementation behavior without changing the program's
outputs. The qualification appendix generator checks their IDs and complete
wording against `kiansheik/latex` `scripts/qualification/grammar_notes.json`,
checks the reviewed method-body hashes, and links the notes by object class to
the generated lexicon and corpus trees.

Verified Python syntax for all four modified modules and regenerated the
qualification appendices from the local corpus/engine pair; all five comments
were found. The corpus still has four pre-existing exact target/render
disagreements (Araújo and Bettendorff records 20 and 28); no target or
realization rule was changed. `make verify-ground-truth` fails on the unchanged
`oldtupicorpus` main checkout because Araújo record 74's source annotations
already differ from generated JSONL; Bettendorff passes. Do not regenerate the
approved file to conceal that discrepancy. This is the first five-method documentation pass,
not a complete Old Tupi grammar or a claim that class membership proves a
method's invocation in every line.
