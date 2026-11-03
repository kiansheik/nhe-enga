# Navarro → Emerson: an orthographic model for VLB retrieval

The useful unit of comparison is a **modern surface form and an attested
historical span on the cited page**. A directional spelling model makes pairs
such as `potyra` → `Potigra` inexpensive to align while preserving the original
forms, their differences, and competing matches. Page, Portuguese gloss, and
quotation evidence then help identify the appropriate passage.

This analysis describes the frozen implementation in [orthography.py](orthography.py),
the conservative training selector in [seeds.py](seeds.py), and the model recorded
in [output/orthography-model.json](output/orthography-model.json). Counts below
were checked against that output on 2026-11-03. Evaluation results belong in the
separate benchmark report; no benchmark test judgments were used to write this
document or select its examples.

## Historical basis and source credit

Navarro's discussion of his transcription of the Camarão letters provides a
primary explanation of the modern conventions: `y` represents a vowel written
historically as `ig`, `i`, or `j`; the modern apostrophe records a glottal
consonant; semivowel notation varies historically; and `c` can correspond to
modern `k` or `s`. His discussion also identifies inconsistent nasal marking.
These observations motivate alternatives with costs. They concern another
seventeenth-century corpus and do not establish universal VLB substitutions.
See the paleographic criteria, especially items a/c/e/f/i, in
[Navarro (2022)][navarro].

The VLB has its own editorial history. Drumond's preface explains that the second
edition corrects earlier transcription and printing errors, incorporates entries
from the Lisbon manuscript, and preserves the original spelling of those added
entries. A single uniform historical spelling system would therefore be an
unsafe assumption. The preface is reproduced on
[Emerson's VLB project site][emerson].

The digitized text is the work of **Emerson José Silveira da Costa**. His project
credits the transcription and invites corrections against the printed source.
The pinned copy used here is document revision 568; its provenance is recorded
in [the source README](../source/README.md). Please retain links to Emerson's
[original project][emerson], [Google document][document], and
[Como aprender tupi resource page on Abanhe'enga][blog]. The page images come from
the edition available through the [Biblioteca Digital Curt Nimuendajú][facsimile].

## Concrete correspondences in the VLB

The examples below are development evidence from the pinned dictionary and
Emerson text. They are attested forms and proposed spelling analyses, not new
editorial verification of every associated citation. `§22`, for example, means
source record `vlb-emerson-r568-p00022`; it is a transcription paragraph number,
not a printed line number. Full text is in
[emerson_vlb.txt](../source/emerson_vlb.txt), with page associations in the
[source index](../data/source-index.json.gz).

| Modern form or explicitly identified surface | Emerson form | Printed page; record | Useful correspondence and limitation |
| --- | --- | --- | --- |
| `potyra` (Navarro row 9082, homonym 1, shirt ruffle) | `Potigra` | I, 17; §22 | `y → ig`. The historical `ig` is handled as one alternative spelling unit. |
| `ybyraypy` (row 11206) | `Ybiraigpig` | I, 18; §33 | The same word contains retained `y`, `y → i`, and two `y → ig` correspondences. |
| `akyrara` (row 2778) | `Aquîrara` | I, 18; §46 | `k → qu` before historical `î`, together with `y → î`. Several relevant entries occur on this page. |
| `eirusu` (row 3816) | `Eiruçu` | I, 18; §33 | A clear `s → ç` spelling comparison. |
| Explicit dictionary example `Asesemõ` under `esemõ` (row 4241) | `Acecemõ` | I, 17; §27 | Both `s` positions correspond to `c` before historical `e`. The initial `s` is already present in the supplied modern surface. |
| Explicit example `Aîmokanãî` under `mokanãî` (row 7210) | `Aimocanãy` | I, 17; §13 | `î → i/y`, `k → c`; the nasal vowel remains. This exact occurrence/form pair is one of the existing narrowly reviewed associations. |
| Search surface `aî + moîepotar` (row 7154) | `Aimojepotar` | I, 19; §93 | The separately labeled prefix hypothesis supplies `aî-`; the stem exhibits `î → j`. The shared sense concerns kindling with an ember. |
| `Agûasá` in an explicit example under `agûasá` (row 2480) | `Aguaça` | I, 17; §25 | `û → u`, `s → ç`, and different accent marking. The paragraph also contains `Xeaguaça`. |
| Explicit example `Xe pokarugûar` under `pokarugûara` (row 8858) | `Xepocarugoar` | I, 18; §36 | Joining the supplied words, `k → c`, and the specific `gûa → goa` correspondence. |
| `eirapu'a` (row 3811) | `Eirapua` | I, 18; §33 | Omission of the modern glottal apostrophe is an alternative with a nonzero cost. |

These observations favor **competing directional alternatives**. Replacing every
modern `y` with `i` would discard the evidence in `Ybiraigpig`; deleting every
historical `g` would also damage genuine consonants. Likewise, the model permits
`s → c` before historical `e/i`, while the inexpensive `k → c` rule excludes
that environment. The `k → qu` condition examines the following historical
vowel: it therefore works in `akyrara` → `Aquîrara`, even though the modern
letter following `k` is `y`.

The observed pair `Aîku'aman` → `Aicuamã` (I, 17; §23, row 6164) also raises a
question about final `an` versus `ã`. The first model does not turn that one
observation into a general final-`n` deletion or a universal nasal rewrite.
It remains an example for further philological review.

## Choosing the surface is a separate step

A dictionary lemma often differs from the VLB's cited surface for morphological
reasons. The spelling learner receives the surface after that choice has been
recorded. It never learns arbitrary empty-to-prefix or suffix-to-empty rules.

For `pokarugûara`, the dictionary explicitly supplies the adjective form
`pokarugûar` and the example `Xe pokarugûar` — “Eu sou hábil.” Comparing that
surface with `Xepocarugoar` isolates useful spelling and spacing differences.
Aligning only the bare lemma would mix those differences with the final `-a`
alternation and the preceding `xe`.

Similarly, the explicit examples under `esemõ` include `Asesemõ` and
`Xe resemõ`, which correspond to `Acecemõ` (§27) and `Xerecemõ` (§26).
Those examples justify examining `s/c` and word joining. They do not justify a
spelling rule such as `e → rece`. Another explicit contrast is `andara`, whose
dictionary entry supplies adjective `andar` and example `Xe andar`, alongside
historical `Xeandar` (I, 18; §48, row 2922).

The candidate pipeline records three useful kinds of input: literal headwords,
explicit dictionary/example forms, and bounded prefix hypotheses. The last
category uses `a-`, `aî-`, or `xe-` as retrieval alternatives with a penalty and
visible provenance. A label elsewhere in a dictionary entry does not establish
that a prefix applies to every sense. These hypotheses do not invoke or alter
the morphology engine.

## What the weighted alignment computes

The comparison normalizes Unicode composition, case, and typographic variants
of apostrophes. It retains the letters, nasal marks, stress marks, and glottal
apostrophes themselves. A dynamic program finds the lowest-cost sequence of
single-grapheme edits and permitted multigraph alternatives. Every chosen
operation is available in the alignment trace.

| Operation | Cost in the initial model |
| --- | ---: |
| Identical grapheme | 0 |
| `î → i`, `û → u` | 0.14 |
| Contextually permitted `k → c/qu`, or `s → ç` | 0.16 |
| `y → ig`, or `î → j` | 0.18 |
| Same base letter with different nonnasal marks, when no cheaper rule applies | 0.26 |
| Modern glottal apostrophe absent historically | 0.40 |
| Same base letter with changed presence of nasal tilde | 0.75 |
| Otherwise unmatched insertion, deletion, or substitution | 1.00 |

The complete alternative set and its descriptions are in the model JSON.
These weights express retrieval preferences; they are not probabilities or
estimates of how frequently a historical spelling occurs. In particular, the
generic mark comparison is a computational fallback, not a statement that every
diacritic has the same linguistic function.

The raw cost is divided by the longer surface's grapheme count and capped at 1.
For `potyra` → `Potigra`, the single `y → ig` operation costs 0.18, giving a
normalized cost of approximately `0.025714` and a similarity of `0.974286`.
That value measures this alignment under the chosen costs. It does not mean
there is a 97.4% chance that a citation points to this entry.

The page ranker combines spelling fit with other evidence, including Portuguese
entry-head overlap and words accompanying a quoted form. A spelling fit by
itself cannot distinguish repeated forms on one page or establish the extent
of a dictionary entry's coverage.

## How the silver training pairs are selected

The seed extractor deliberately starts with narrow observations available in
the existing citation/page data:

1. The headword has at least four letters under the old retrieval key, and a
   previously shortlisted source paragraph has Portuguese entry-head overlap
   with the citation context.
2. A token after an observed entry separator matches the old headword key or
   one of the separately recorded prefix alternatives. Only one distinct
   surface and one eligible paragraph survive for that citation.
3. The same old form key does not occur in another paragraph on the cited page.
   Repeated instances within the chosen paragraph retain their offsets.
4. The exact historical span is preserved. An exact modern token in a clearly
   delimited example can replace a generated search surface, with its context
   offsets recorded.
5. Preregistered headwords, pages, and source paragraphs are excluded before
   learning. Paragraph exclusions also cover continuations onto neighboring
   pages. Exclusion keys normalize case, Unicode/apostrophe typography, and
   terminal editorial punctuation such as `marã?` versus `marã`.

The post-separator region can still contain Portuguese commentary. These
observations therefore remain **silver, proposed pairs**; they are not human
gold labels. The extractor's old key folds accents and apostrophes and admits
`c/k`, `ç/s`, and `j/i` aliases. This creates selection bias: many examples of
an admitted alias cannot independently prove the alias. Conversely, a spelling
absent from that key may have no silver support even when it is well attested.
`y → ig` is an important example: its support in this model is the primary
discussion and the VLB development examples, not an independent discovery from
these seeds.

The frozen output contains the following inventory:

| Training stage | Count |
| --- | ---: |
| Selected silver seed records | 613 |
| Repeated headword/modern-surface/historical-surface pairs removed | 46 |
| Remaining pair above the maximum allowed seed cost, skipped | 1 |
| Accepted unique surface pairs | **566** |

Each accepted pair is aligned once using the frozen prior model. The learner
counts nonempty correspondences, with distinct headword and page support and
bounded example lists. A new rule needs at least three headwords and two pages.
Repeated citations of the same surface pair count once. There is no recursive
self-training from the ranker's own predictions, and evaluation judgments are
not input to either selection or training. The complete seed records are in
[output/seeds.json.gz](output/seeds.json.gz).

## Supported observations versus effective rules

Support and computational effect answer different questions:

| Category in the frozen learned model | Count | Meaning |
| --- | ---: | --- |
| Supported learned observations | **24** | Meet the independent-headword/page thresholds. |
| Effective-cost learned rules | **10** | Meet those thresholds and can improve the available edit cost. |
| Supported but inert observations | **14** | Their proposed cost cannot beat the existing single-grapheme fallback; retained for inspection, omitted from executable rules. |

For example, an observed stress-mark change can have abundant support while
its proposed learned cost is higher than the existing 0.26 fallback. Adding
that rule would change neither the winning alignment nor its score. Filtering
these inert rules was checked to leave all current seed-pair distances unchanged.

The ten effective additions comprise `i → j` and nine nasal-mark alternatives.
The nasal alternatives retain a cost of at least 0.65, close to the original
0.75 fallback and much higher than a documented `y → ig` spelling operation.
Their counts arise from accent-folded silver selection; they should be read as
observations worth reviewing, not proof that nasal distinctions can be ignored.
The stronger value of the first model may therefore come from its documented
priors and page/context constraints. The frozen prior-only, learned, and
uniform-edit comparisons are needed to measure that contribution.

## What can be concluded from a proposed match

A successful proposal identifies an unchanged text span, its source record,
the cited page, a supplied modern surface, and an inspectable alignment.
Its scan target may be an OCR line containing the form or an approximate
paragraph region; that does not establish an exact glyph box. Repeated forms,
OCR errors, clipped page continuations, adapted quotations, and short words
remain reasons to inspect the source.

Coverage must be recorded at the relevant level. In §13, the existing reviewed
`mokanãî` association names `Aimocanãy`; the same source paragraph also contains
`Aimõgue` and `Aimocanacanãy`. Reviewing the named form does not cover all those
forms or the whole paragraph. Likewise, a failed retrieval can reflect an
unmodeled surface, a locator problem, or transcription noise. It becomes
evidence for a new verbete only after the source and the existing dictionary
have been checked for that particular sense and form.

[navarro]: https://www.scielo.br/j/bgoeldi/a/vy7RnrNvd5B4rrCCX6vVx4d/?lang=pt
[emerson]: https://sites.google.com/site/vocabularionalinguabrasilica/
[document]: https://docs.google.com/document/d/1oNYyk0gHjtP4Rm_Auemt-63DYMXLY9GgFtQ2OE2H6Ek/edit
[blog]: https://abanheenga.blogspot.com/p/como-aprender-tupi.html
[facsimile]: https://www.etnolinguistica.org/biblio:drumond-1952-1953-vlb

### Primary reference

Navarro, Eduardo de Almeida. 2022. “Transcrição e tradução integral anotada das
cartas dos índios Camarões, escritas em 1645 em tupi antigo.” *Boletim do Museu
Paraense Emílio Goeldi. Ciências Humanas* 17(3).
[DOI: 10.1590/2178-2547-BGOELDI-2021-0034](https://doi.org/10.1590/2178-2547-BGOELDI-2021-0034).
