# Dictionary entry formatting audit — 2026-10-25

## Goal

Inspect a reproducible sample of fully rendered top-level `.entry` elements,
biased toward long verbetes, and distinguish sound formatting from boundary
failures before changing the production formatter.

This is a rendering audit, not a linguistic review of Navarro's definitions.
`Good` below means that the visible definition/example/translation boundaries
are coherent with the source record.

## Implementation follow-up

After the initial audit, the formatter was repaired across the full set of
identified boundary classes rather than limiting the work to the first
heading-only slice proposed below. The production formatter now protects
generated semantic elements, tracks bracket and parenthesis depth, recognizes
only citation-shaped parentheticals as sources, separates adjacent pairs at
credible citations, handles compact or omitted translation delimiters
conservatively, preserves editorial text outside quote cards, and distinguishes
related-entry prose from examples. Related suffix headwords beginning with a
morphological hyphen are linked without losing that hyphen or becoming quote
cards. Annotated grammatical preambles retain their complete glosses, and
source variants remain separate cards with their original `ou` visible.

The final implementation was exercised in real Chromium over all 8,293 served
Tupi–Portuguese records. It produced zero structural warnings, dialogue
mismatches, leading-separator definitions, editorial-note source lines, or
source citations stranded in Tupi. All remaining heuristic candidates were
reviewed as legitimate punctuation, reported speech, etymology, page ranges,
or cross-reference notation. The final maintained regressions pass 53 browser
tests plus structural and lexical-token-preservation checks over all 8,293
records. A deterministic 31-entry long-record/sentinel sample produced zero
warnings, and every screenshot passed qualitative review. Sticky-footer
geometry was also checked on the initial short page and an expanded long entry.

## Method

The maintained sampler is `scripts/qa/sample_dictionary_entries.py`. It:

1. reads the served `docs/dict-conjugated.json.gz`;
2. keeps the 8,293 lexical Tupi–Portuguese records before `BIBLIOGRAFIA`;
3. forms a pool from the longest 10% (830 records, minimum 423 definition
   characters);
4. ranks that pool reproducibly with SHA-256 and seed
   `format-audit-2026-10-25`;
5. takes 24 records and adds dictionary index 9405 (`ranhẽ²`) as an explicit
   sentinel; and
6. loads the production `index.html`, `styles.css`, and `js/index.js` in
   Chromium at 1440 × 1000, searches through the real UI, and captures each
   rendered `.entry`.

Hidden conjugation controls are omitted from the saved HTML because their
random DOM IDs are unrelated to definition formatting. The browser still
builds them normally. The sample JSON and gallery are byte-for-byte identical
on repeated runs.

Reproduction:

```sh
.venv/bin/python scripts/qa/sample_dictionary_entries.py \
  --seed format-audit-2026-10-25 \
  --sample-size 24 \
  --longest-percent 10 \
  --include-index 9405 \
  --output /tmp/nhe-enga-entry-sample.json \
  --gallery /tmp/nhe-enga-entry-sample.html \
  --screenshots /tmp/nhe-enga-entry-screenshots
```

Result: 25 reviewed entries, 16 coherent and 9 needing correction. The DOM
detector warned on only two; seven additional failures required comparing the
raw record with the visible semantic boundaries.

The reviewed input gzip has SHA-256
`d235a7961961b58fcfbb93362bc3acb9b7f7b7e823196dca5763ef3e7fd16f53`.
The final JSON and gallery hashes are respectively
`68d027fc2f23702a7c94bea32c02046272b03bcc9020155cf5725e9352f7ecfb`
and `1b02252284cd18978bd7b26e3bf1b8f836d9fc1c562eb451f4f39e112c1e0133`.

## Qualitative review

| Dictionary index | Entry | Verdict | Current rendering and expected boundary |
| ---: | --- | --- | --- |
| 9405 | `ranhẽ²` | Bad | `Advérbio:` contains the first quote, `.quote-tupi` is empty, and the definition plus Tupi example inherit heading weight. Close the heading, keep only the gloss in `.sense-definition`, then render the Tupi and Portuguese as sibling quote lines. |
| 4131 | `erobîar` | Good | Five main examples and five related-entry examples are paired coherently; keep the current boundaries. |
| 9168 | `pupé` | Bad | `itá pupé - com uma pedra (VLB, I, 77)` is left as an unstyled inline fragment between quote cards and sense 3. Treat it as the third bilingual example of sense 2 (or an intentionally compact example component), not loose text. |
| 4609 | `-'ĩ²` | Bad | The `Nd'e'ikatuî... - Não pode... (Ar., Cat., 98)` pair is raw inline text after a dialogue block. It should become a normal quote card before sense 5. |
| 9012 | `poru¹` | Good | Numbered senses, the two examples sharing `(VLB, I, 113)`, and related entries remain visually coherent. |
| 8308 | `opá` | Good | Eleven examples stay under the correct two senses. |
| 6881 | `mendar` | Good | Main and related-entry gloss/example boundaries remain coherent. |
| 10931 | `u'uba¹` | Good | Main examples and the final related-entry example are separated correctly. |
| 10919 | `'useî` | Good | Both numbered senses and all related-entry examples are paired correctly. |
| 7765 | `-ne³` | Bad | The usage note and `T'asóne` / `T'orosóne` pairs are swallowed into the Portuguese line for the preceding example. End that quote at `(Anch., Doutr. Cristã, II, 112)`, leave the usage note outside it, and render the later Tupi/Portuguese pairs separately with their shared citation. |
| 7124 | `moîar¹` | Good | Four senses and both related-entry examples retain sensible boundaries. |
| 5299 | `îoesé` | Bad | `-Oîkuab... -Reconheceu...` appears entirely on the Tupi line because the translation dash has no following space. Recognize this compact source delimiter and create a Portuguese line. |
| 5752 | `kakuab¹` | Bad | The semicolon inside `[o homem ou o animal; fal. de coisas, ...]` prematurely ends bold definition styling. Square-bracket content must remain opaque; the outer semicolon after `]` is the real gloss boundary. |
| 2831 | `ambyasy` | Bad | The generated `Adjetivo:` heading swallows the first adjectival quote, like `ranhẽ²`; `faminto; (xe) ter fome` and the Tupi sentence are placed in the quote card. Close the heading and keep the complete gloss before the example colon. |
| 10802 | `umẽ` | Good | The explanatory parenthesis remains outside the surrounding quote pairs and all five examples are paired. |
| 2834 | `ambyra` | Good | The noun and adjective examples remain distinct and coherent. |
| 8370 | `pabẽ¹` | Good | All five examples are split consistently. |
| 3918 | `(e)mbetara` | Bad | The last Portuguese line absorbs `(Pode também ser pluriforme...)` and the following `tembetara` form. End the quote at the Marcgrave citation and render the usage note/cross-form outside the quote. |
| 4052 | `enopu'am²` | Good | Both long bilingual examples remain correctly paired. |
| 10255 | `temone¹` | Good | All three optative examples remain correctly paired. |
| 7016 | `moanhẽ` | Bad | The second Tupi/Portuguese pair of sense 2 is appended to the first pair's Portuguese line because the source has no semicolon after the first citation. A completed trailing citation should close that pair and permit a new pair. |
| 7015 | `moanhan` | Good | Quoted speech containing hyphens stays inside the correct Tupi and Portuguese lines. |
| 5475 | `îubyk` | Good | Main and related-entry examples remain coherent. |
| 8908 | `por¹` | Good | Quoted clauses containing leading dashes do not disturb the two example pairs. |
| 8997 | `poromonhang` | Good | The two-turn dialogue and the related-entry quote are correctly structured. |

## The reported bold/highlight symptom

The blue `highlighted` span is expected search behavior: the current highlighter
marks matching text in headwords, definitions, and examples, while skipping
citations. It is not what makes the reported example bold.

The unwanted bold text is caused by malformed ancestry. For `ranhẽ²`, the
formatter currently gives the browser the equivalent of:

```html
<div class="sense-section-title">Advérbio:
  <div class="sense-quote">
    <div class="quote-tupi"></div>
    <span class="sense-definition">primeiro, antes, primeiramente (na afirm.)</span>:
    ...Ereîkuá ranhẽ meémo emonã nde rekorama...
  </div>
  <div class="quote-pt">Deverias ter sabido antes...</div>
</div>
```

The intended structure is:

```html
<div class="sense-section-title">Advérbio:</div>
<span class="sense-definition">primeiro, antes, primeiramente (na afirm.)</span>:
<div class="sense-quote">
  <div class="quote-tupi">...Ereîkuá ranhẽ meémo emonã nde rekorama...</div>
  <div class="quote-pt">Deverias ter sabido antes...</div>
</div>
```

`sense-section-title` has `font-weight: 600`, so the invalid nesting—not the
blue highlight—makes the first example and translation bold.

## Confirmed scope of the heading bug

A full formatter pass over all 8,293 Tupi–Portuguese records found:

- 489 generated `Adjetivo:` or `Advérbio:` headings;
- 274 malformed heading-to-quote occurrences in 270 entries;
- 178 malformed `Advérbio` occurrences and 96 malformed `Adjetivo`
  occurrences; and
- exactly 274 empty `.quote-tupi` elements, all belonging to those same
  malformed occurrences and none elsewhere.

This is an exact scope for this one signature, not a claim that the other
8,023 entries are correct. The long-entry sample exposed four additional
failure classes.

## Root causes and PR-sized changes

The principal problem is that `formatVerbeteSection()` first injects semantic
HTML and then reparses that generated HTML with punctuation heuristics.
`findColonOutside()` ignores characters inside a tag (`<...>`) but not text
inside an element, so it selects the colon in generated `Advérbio:` or
`Adjetivo:` before the actual definition/example colon. Browser tree repair
then turns the malformed string into the nesting above.

A focused formatter PR should be split into reviewable changes:

1. **Protect structural boundaries.** Parse definition/example delimiters
   before inserting HTML, or make the later scan explicitly skip generated
   section-title and sense elements. Sense markers, POS headings, and related
   headwords must be hard barriers for quote merging.
2. **Track square brackets.** The colon and semicolon scans currently track
   parentheses only. Track `[...]` depth too, so grammatical notes such as the
   one in `kakuab¹` cannot create a false boundary.
3. **Close pairs at credible citations.** A completed source citation should
   be able to end one bilingual pair even when the source omits a semicolon;
   this addresses `moanhẽ` without merging the next pair into `.quote-pt`.
4. **Handle compact translation dashes narrowly.** Permit a source/translation
   delimiter like ` -Reconheceu` in a quote-shaped, cited segment, while
   preserving suffixes and dialogue markers such as `-pyr`.
5. **Separate notes from citations.** A trailing parenthesis is not
   automatically a bibliographic citation. Require citation-shaped content
   before assigning `.quote-citation`, and keep editorial/usage notes outside
   quote lines.
6. **Fail closed.** If a segment is ambiguous, leave it readable and unstyled
   rather than emitting empty quote lines or nested semantic blocks.

The first PR can safely fix items 1–2 plus the exact `ranhẽ²` regression. The
multi-pair and compact-dash changes should follow with their own fixtures
because their heuristics affect a broader range of source punctuation.

## Regression coverage to add with the formatter PR

- exact `ranhẽ²` assertions for section title, definition, Tupi line, and
  Portuguese line;
- corpus invariants forbidding `.sense-section-title .sense-quote`, empty
  `.quote-tupi`, semantic sense elements inside quote lines, and quote lines
  whose parent is not `.sense-quote`;
- a square-bracket contrast based on `kakuab¹`;
- a compact-dash contrast based on `îoesé`;
- a post-dialogue quote based on `-'ĩ²`;
- an annotation followed by shared-citation examples based on `-ne³`;
- adjacent pairs without a semicolon based on `moanhẽ`; and
- coherent controls from `poru¹`, `moanhan`, and `poromonhang`.

The formatter implementation and tests were deliberately not changed during
the initial audit phase documented above. They were implemented in the
follow-up described at the top of this report.
