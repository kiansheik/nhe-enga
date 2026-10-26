# Diffuse locative -bo and hyphenated postpositions — 2026-10-12

Goal: a dictionary headword such as `-bo` inserted from Pydicate Studio became
`Postposition("-bo")` and rendered `oka -bo` (space, literal hyphen). The user
proposed auto-wrapping hyphen-initial words in `YFix`; they approved the engine
change after seeing that `YFix` cannot express it. No corpus expression,
lexicon entry or ground truth was edited.

Why not `YFix`: it subclasses `Predicate`, so `YFix(Postposition(...)) * noun`
skips `Postposition.__mul__`, leaves `arg0` unset and raises. Its only effect is
`Verb.preval` y-insertion, and only when the wrapped object has `clitic=True`
(currently only adversative particles; `peQ`, `ne`, `mo`, `mã`, `temõ` are
wrapped but render detached). `-pe` itself never used `YFix`; its allomorphy is
`tupi.Noun.pe`.

Attestation (Navarro, -bo2, posp.): kóbo (Anch., Arte, 42), ka'abo and nhũbo
(VLB, II, 81), i potasábo (Ar., Cat., 53), ekomonhangábo (Ar., Cat., 3).
Pronominal dative `-bo` is already modelled as `supé.var(0)` (lexicon `orébo`)
and is not duplicated.

Changed:
- `tupi/tupi/noun.py`: `Noun.bo()` — `-ab` → `-á` + bo; semivowel or vowel
  (oral or nasal) + bo; consonant + epenthetic `y` + bo. Tag
  `[POSTPOSITION:DIFFUSIVE]`.
- `pydicate/.../pos/postposition.py`: `Diffusive` class and `bo` instance
  (replaces `# TODO: implement -bo like -pe`); `BOUND_POSTPOSITIONS`
  (`pe`→`Locative`, `bo`→`Diffusive`) and `Postposition._bound_delegate`, so a
  plain `Postposition("-bo"/"-pe", definition=...)` keeps its definition but
  realizes through the bound class. `Locative.morphology` (qualified
  `@grammar` method) was not touched.
- `pydicate/tests/test_bound_postpositions.py`: attested hosts, -sab deverbal,
  inferred consonant branch, tags, and contrasts (`pe` okype/nhũme, free
  `pupé`, unimplemented `-reme` unchanged, bare `-bo` without argument).

Commands/results: the new test failed before implementation (import of `bo`).
`PYTHONPATH=pydicate:tupi python3 -m unittest discover pydicate/tests`: 92 passed
(82 before). Fresh plain + annotated renders of all 160 historic expressions in
`../oldtupicorpus` before/after: byte-identical. `ground_truth_cli verify`: same
result as baseline (araujo and catecismo_brasilico record 1 stale because of
uncommitted corpus source edits unrelated to this change; bettendorff OK).
`oldtupicorpus/tests/run_tests.py --skip-tokenizer`: 113 passed.

Remaining questions:
- Consonant-final hosts (`okybo`) follow -pe/-y- by analogy; needs an
  attestation or editorial confirmation. Nasal-consonant stems likewise get
  `ybo` with no nasalization.
- Should other hyphenated headwords (`-(r)amo`, `-reme`, `-i` partitive) get
  bound classes, and should hyphenated particles (`-te`, `-ne`, `-mo`) become
  enclitic (setting `clitic` on the `YFix` ones would change existing renders
  such as `sem ne`)?

Suggested next prompt: review the PR for branch `feat/bound-postposition-bo`, confirm or
reject the inferred `okybo` branch, then rebuild Studio's engine dependency and
try inserting `-bo` from the dictionary.
