"""Offline, page-constrained retrieval of attested Navarro/VLB form spans.

This module proposes citation-to-passage links. It does not edit the dictionary,
the transcription, the morphology engine, or the viewer's reviewed links.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import unicodedata

from .orthography import align, compile_model, prior_model, score
from .quotation import parse_quotations


CONFIG = {
    "version": "vlb-page-ranker-v3",
    "paragraph_span_shortlist": 6,
    "surface_shortlist": 2,
    "span_alternatives": 3,
    "top_k": 3,
    "form_weight": 70.0,
    "portuguese_context_weight": 20.0,
    "quotation_context_weight": 18.0,
    "quoted_surface_weight": 8.0,
    "whole_quotation_weight": 15.0,
    "local_quotation_weight": 12.0,
    "suggestion_min_similarity": 0.84,
    "suggestion_min_margin": 5.0,
    "short_form_min_context": 0.34,
    "scores_are_probabilities": False,
}

STOP = set("""a o as os de da do das dos em no na nos nas ao aos um uma uns umas
e ou com sem por para pelo pela que se seu sua seus suas meu minha meus minhas
eu tu ele ela nos vos xe me te lhe ha he eh ser estar ter fazer coisa cousa
qualqr qualquer este esta isto esse essa isso aquele aquela aquelle aquella
aqui ali muito mais menos tal como quando onde qual todo toda todos todas
outro outra outros outras mesmo mesma modo nome verbo forma usado usada pode
tambem nao sim so ut l vel act neut adj adv tr intr s v et etc fig anch ar cat
vlb adapt castilho nomes teatro poemas arte cristã cristao fonte segundo livro
ditto dito dirao diz dizem dizer hum huma humas huns ainda antes depois porq
porque principalmente propriamente somente propriam falando pertence serve
seu sua ouel mais menos actiuo actiuos neutro neutros activo actiuam passiuo
aduerbio adverbio substantiuo relativo relatiuo neutram comunmente porem
qualquer dellas delle delle desta deste desta desses pess pessoa dizerse
""".split())
APOSTROPHES = "'’‘ʼ"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_json(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def digest(value) -> str:
    return hashlib.sha256(stable_json(value)).hexdigest()


def read_json(path: Path):
    raw = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
    return json.loads(raw)


def write_json(path: Path, value, *, pretty=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
           if pretty else stable_json(value)) + b"\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    if path.suffix == ".gz":
        with tmp.open("wb") as stream:
            with gzip.GzipFile(fileobj=stream, mode="wb", filename="", mtime=0) as zipped:
                zipped.write(raw)
    else:
        tmp.write_bytes(raw)
    tmp.replace(path)


def canonical(text: str) -> str:
    return unicodedata.normalize("NFC", text.casefold().translate(
        str.maketrans({char: "'" for char in APOSTROPHES})))


def fold(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", canonical(text))
                   if not unicodedata.combining(c))


def word_spans(text: str):
    """Unicode words, retaining combining marks and original character offsets."""
    i = 0
    while i < len(text):
        if not (text[i].isalpha() or text[i] in APOSTROPHES and
                i + 1 < len(text) and text[i + 1].isalpha()):
            i += 1
            continue
        start = i
        i += 1
        while i < len(text):
            ch = text[i]
            if ch.isalpha() or unicodedata.category(ch).startswith("M"):
                i += 1
            elif ch in APOSTROPHES + "-" and i + 1 < len(text) and text[i + 1].isalpha():
                i += 1
            else:
                break
        yield text[start:i], start, i


def retrieval_key(text: str) -> str:
    """Lossy shortlist key ONLY. The directional final scorer retains diacritics."""
    text = fold(canonical(text).replace("ç", "s"))
    text = text.replace("qu", "k")
    text = re.sub(r"c(?=[ei])", "s", text).replace("c", "k")
    text = text.replace("goa", "gua").replace("ig", "y")
    text = text.replace("j", "i").replace("y", "i")
    return "".join(c for c in text if c.isalpha())


def grams(key):
    return frozenset(key[i:i + 2] for i in range(len(key) - 1)) or frozenset(key)


def cheap_similarity(a, b, ga=None, gb=None):
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    ga, gb = ga or grams(a), gb or grams(b)
    return 2 * len(ga & gb) / max(1, len(ga) + len(gb))


def content_words(text):
    # Portuguese context has its own lossy retrieval conventions. They never
    # enter the Navarro -> Tupi spelling model or rewrite the historical text.
    words = set()
    for word, _, _ in word_spans(text):
        key = fold(word)
        if len(key) < 3 or key in STOP:
            continue
        key = key.replace("ph", "f").replace("y", "i")
        if len(key) > 4 and key.endswith("s"):
            key = key[:-1]
        words.add(key)
    return words


def headword_forms(headword):
    """Expand explicit editorial parentheses, without inventing lexical stems."""
    value = headword.strip(" -?0123456789")
    forms = [value]
    match = re.search(r"\(([\w'’]+)\)", value)
    if match:
        forms = [value[:match.start()] + match[1] + value[match.end():],
                 value[:match.start()] + value[match.end():]]
    return [f for f in dict.fromkeys(forms) if f and not re.search(r"[(),\[\]]", f)]


def quotation_spans(context):
    """Compatibility wrapper; callers needing uncertainty use parse_quotations."""
    return parse_quotations(context)["quotes"]


def make_surfaces(citation, definition, quotation_analysis=None):
    """Spelling and generated surface hypotheses have separate provenance."""
    bases = headword_forms(citation["headword"])
    surfaces = []

    def add(form, kind, penalty=0.0, **evidence):
        form = form.strip()
        if not form or len(form) > 80:
            return
        surfaces.append({"form": form, "kind": kind, "penalty": penalty,
                         **evidence})

    for base in bases:
        add(base, "headword" if base == citation["headword"] else "editorial_optional_form")
    # The dictionary sometimes explicitly supplies a predicate/adjective stem.
    for match in re.finditer(r"\(adj\.\s*:\s*([^()]+)\)", definition):
        for word, left, right in word_spans(match[1]):
            if any(cheap_similarity(retrieval_key(word), retrieval_key(b)) >= .60 for b in bases):
                add(word, "explicit_dictionary_adjective_form", .01,
                    definition_start=match.start(1) + left, definition_end=match.start(1) + right)
                bases.append(word)
    # These are bounded search alternatives, never claimed to be inflected by
    # the engine. A-/aî-/xe- are visible in the VLB citation seed material.
    prefixes = []
    if not citation["headword"].startswith("-") and not citation["headword"].endswith("-"):
        if re.search(r"\bv\.\s*tr\.", definition):
            prefixes.extend(("aî", "a"))
        if re.search(r"\bv\.\s*intr\.", definition):
            prefixes.append("a")
        if re.search(r"\(s\.|\badj\.|\(xe\)", definition):
            prefixes.append("xe")
    for base in list(dict.fromkeys(bases)):
        if len(retrieval_key(base)) < 3:
            continue
        for prefix in dict.fromkeys(prefixes):
            add(prefix + base, "surface_prefix_hypothesis", .025,
                prefix=prefix, stem=base, linguistic_analysis="unreviewed",
                license="grammatical label somewhere in the dictionary entry; sense-specific applicability unreviewed")

    quotes = (quotation_analysis or parse_quotations(citation["context"]))["quotes"]
    base_keys = [retrieval_key(b) for b in bases]
    for quote_index, quote in enumerate(quotes):
        words = list(word_spans(quote["text"]))
        required = [(word, start, end) for word, start, end in words
                    if not any(a <= quote["context_start"] + start < b
                               for a, b in quote.get("optional_intervals", []))]
        for i, (_, start, end) in enumerate(words):
            for width in (1, 2, 3, 4):
                if i + width > len(words):
                    continue
                end = words[i + width - 1][2]
                value = quote["text"][start:end]
                # Do not invent a parenthesis-free or discontinuous surface.
                if any(char in value for char in "()[]"):
                    continue
                if any(a <= quote["context_start"] + start < b
                       for a, b in quote.get("optional_intervals", [])):
                    continue
                key = retrieval_key(value)
                whole = bool(required and start == required[0][1] and end == required[-1][2]
                             and len(required) == width)
                related = any(key == b or len(b) >= 3 and
                              (b in key or cheap_similarity(key, b) >= .64) or
                              bool(b) and len(b) < 3 and "-" in value and b in key
                              for b in base_keys)
                # A literal complete example is independent evidence even when
                # its morphology makes it unlike the dictionary's bare lemma.
                if whole or related:
                    add(value, "quoted_surface_hypothesis", .01,
                        context_start=quote["context_start"] + start,
                        context_end=quote["context_start"] + end,
                        quotation_detection=quote["kind"], quote_index=quote_index,
                        whole_quotation=whole)
                # VLB questions can write a modern multiword interrogative as
                # one historical construction and realize the question particle
                # in the fused form. Keep this as an inspectable hypothesis,
                # licensed only by a complete literal question; it is never a
                # general spelling rewrite or an editorial acceptance.
                if whole and citation["context"][quote["context_end"]:].lstrip().startswith("?"):
                    fused = "".join(word for word, _, _ in required) + "pe"
                    add(fused, "quoted_question_fusion_hypothesis", .035,
                        context_start=quote["context_start"], context_end=quote["context_end"],
                        quotation_detection=quote["kind"], quote_index=quote_index,
                        whole_quotation=True, literal_quote=quote["text"],
                        transformation="join literal words and append interrogative pe")
    # Keep the least speculative provenance when identical literal forms recur.
    unique = {}
    for surface in sorted(surfaces, key=lambda x: x["penalty"]):
        saved = unique.setdefault(canonical(surface["form"]), surface)
        if surface["kind"] in ("quoted_surface_hypothesis", "quoted_question_fusion_hypothesis"):
            saved.setdefault("quotation_occurrences", []).append({
                "text": surface.get("literal_quote", surface["form"]), "context_start": surface["context_start"],
                "context_end": surface["context_end"], "quote_index": surface["quote_index"],
                "whole_quotation": surface["whole_quotation"]})
    # Apply the already licensed, bounded prefix search to an explicitly cited
    # compound as well as the bare headword. The prefixed form is a hypothesis,
    # not a dictionary quotation or a morphological-engine analysis. Preserve
    # the literal compound's separate offsets; do not remove its final vowel.
    for surface in list(unique.values()):
        if "-" not in surface["form"] or len(list(word_spans(surface["form"]))) != 1:
            continue
        if not surface.get("quotation_occurrences"):
            continue
        for prefix in dict.fromkeys(prefixes):
            form = prefix + surface["form"]
            if len(form) <= 80:
                unique.setdefault(canonical(form), {
                    "form": form, "kind": "quoted_compound_prefix_hypothesis", "penalty": .035,
                    "prefix": prefix, "stem": surface["form"],
                    "linguistic_analysis": "unreviewed",
                    "license": "same bounded entry-label prefix hypothesis as bare lemma; compound applicability unreviewed",
                    "quotation_occurrences": surface["quotation_occurrences"],
                })
    return list(unique.values()), quotes


@dataclass
class FragmentFeatures:
    fragment: dict
    portuguese_head: str
    head_words: set
    body_words: list
    spans: list


def fragment_features(fragment, unit):
    full = unit["text"]
    dash = full.find("—")
    body_start = unit["start"] + dash + 1 if dash >= 0 else unit["start"]
    cross_reference = dash >= 0 and bool(re.match(r"\s*(?:uide|vide)\b", fold(full[dash + 1:])))
    text = fragment["text"]
    words = list(word_spans(text))
    candidates = []
    body_words = []
    for i, (word, start, end) in enumerate(words):
        absolute = fragment["source_start0"] + start
        if absolute < body_start:
            continue
        body_words.append(word)
        for width in (1, 2, 3, 4):
            if i + width > len(words):
                continue
            right = words[i + width - 1][2]
            if width > 1 and any(not re.fullmatch(r"[\s-]+", text[words[j][2]:words[j + 1][1]])
                                 for j in range(i, i + width - 1)):
                continue
            actual = text[start:right]
            if len(actual) > 80:
                continue
            key = retrieval_key(actual)
            if not key:
                continue
            candidates.append({"text": actual, "start0": absolute,
                               "end0": fragment["source_start0"] + right,
                               "role": "cross_reference" if cross_reference else "post_separator_text" if dash >= 0 else "unclassified",
                               "word_count": width, "key": key, "grams": grams(key),
                               "common_portuguese_or_grammar_token": all(fold(w[0]) in STOP for w in words[i:i + width])})
    head = full[:dash] if dash >= 0 else ""
    return FragmentFeatures(fragment, head, content_words(head), body_words, candidates)


class Corpus:
    def __init__(self, repository: Path):
        self.root = repository
        base = repository / "vlb"
        self.manifest = read_json(base / "data/manifest.json")
        self.text = (base / "source/emerson_vlb.txt").read_text(encoding="utf-8")
        assert hashlib.sha256(self.text.encode()).hexdigest() == self.manifest["provenance"]["source_text_sha256"]
        self.pages = [read_json(base / "data" / p["data_file"]) for p in self.manifest["pages"]]
        self.page_by_id = {p["id"]: p for p in self.pages}
        self.units = {}
        cursor = 0
        revision = self.manifest["provenance"]["document_revision"]
        for line, text in enumerate(self.text.split("\n"), 1):
            self.units[f"vlb-emerson-r{revision}-p{line:05d}"] = {"text": text, "start": cursor}
            cursor += len(text) + 1
        self.features = {}
        counts = Counter()
        for page in self.pages:
            features = [fragment_features(f, self.units[f["id"]]) for f in page["fragments"] if f["kind"] == "entry"]
            self.features[page["id"]] = features
            for feature in features:
                counts.update(feature.head_words)
        self.idf = {word: 1 + math.log((1 + 7534) / (1 + count)) for word, count in counts.items()}
        dictionary_path = repository / "docs/dict-conjugated.json.gz"
        assert sha(dictionary_path) == self.manifest["provenance"]["dictionary_snapshot_sha256"]
        self.dictionary = [{"f": e["f"], "d": e["d"]} for e in read_json(dictionary_path)]
        self.provenance = {
            "dictionary_sha256": sha(dictionary_path),
            "source_text_sha256": self.manifest["provenance"]["source_text_sha256"],
            "viewer_manifest_sha256": sha(base / "data/manifest.json"),
            "page_alignment_sha256": sha(base / "source/page_alignment.json.gz"),
            "ocr_layout_sha256": sha(base / "source/ocr_layout.json.gz"),
            "citation_links_sha256": sha(base / "source/citation_links.json.gz"),
            "document_revision": revision,
            "offsets": "zero-based Unicode character offsets, half-open; in this snapshot characters are all BMP",
        }


def portuguese_context(corpus, query_words, feature):
    shared = sorted(query_words & feature.head_words)
    value = min(1.0, sum(corpus.idf.get(w, 1.0) for w in shared) / 18.0)
    return value, shared


def quote_support(quotes, feature, primary_keys, model):
    """Independent example words disambiguate repeated lemmas on one page.

    Exclude all recognized primary surface alternatives, so an inflected form
    does not double-count as an independent word of supporting context.
    """
    source_words = [(w, retrieval_key(w)) for w in feature.body_words]
    matched, total = [], 0
    for quote in quotes:
        for word, start, _ in word_spans(quote["text"]):
            if any(a <= quote["context_start"] + start < b
                   for a, b in quote.get("optional_intervals", [])):
                continue
            key = retrieval_key(word)
            if len(key) < 3 or fold(word) in STOP or key in primary_keys:
                continue
            total += 1
            shortlist = sorted(((cheap_similarity(key, other), target) for target, other in source_words), reverse=True)[:2]
            matches = [(1 - score(word, target, model), target) for quick, target in shortlist if quick >= .35]
            best, target = max(matches, default=(0, ""))
            if best >= .82:
                matched.append({"query": word, "historical_token": target,
                                "weighted_similarity": round(best, 3), "role": "companion_word"})
    return len(matched) / max(1, total), matched


def local_quote_support(quotes, surface, feature, span, model):
    """Match ordered companion words near this exact occurrence, not its lemma.

    Optional example arguments may be absent in the source. Required companions
    are matched on the same side of the proposed span, without reusing a token.
    All matches retain literal source offsets and editorial context offsets.
    """
    tokens = [s for s in feature.spans if s["word_count"] == 1]
    best_score, best_matches, best_total = 0.0, [], 0
    for occurrence in surface.get("quotation_occurrences", []):
        quote = quotes[occurrence["quote_index"]]
        companions = []
        for word, left, right in word_spans(quote["text"]):
            a, b = quote["context_start"] + left, quote["context_start"] + right
            if a < occurrence["context_end"] and b > occurrence["context_start"]:
                continue
            if any(x <= a < y for x, y in quote.get("optional_intervals", [])):
                continue
            key = retrieval_key(word)
            if len(key) < 2 or fold(word) in STOP:
                continue
            companions.append((word, key, a, b,
                               "before" if b <= occurrence["context_start"] else "after"))
        matched, used = [], set()
        previous = {"before": -1, "after": -1}
        for word, key, left, right, side in companions:
            choices = [(i, token) for i, token in enumerate(tokens)
                       if i not in used and i > previous[side] and
                       ((side == "before" and token["end0"] <= span["start0"] and
                         span["start0"] - token["end0"] < 90) or
                        (side == "after" and token["start0"] >= span["end0"] and
                         token["start0"] - span["end0"] < 90))]
            # Restrict to the eight nearest tokens on the appropriate side.
            choices = choices[-8:] if side == "before" else choices[:8]
            cheap = sorted(((cheap_similarity(key, token["key"]), i, token)
                            for i, token in choices), key=lambda p: (-p[0], p[1]))[:2]
            found = []
            for quick, i, token in cheap:
                if quick >= .35:
                    similarity = max(0.0, 1 - score(word, token["text"], model))
                    if similarity >= (.84 if len(key) <= 3 else .78):
                        found.append((similarity, -abs(token["start0"] - span["start0"]), i, token))
            if found:
                similarity, _, i, token = max(found, key=lambda x: x[:3])
                used.add(i)
                previous[side] = i
                matched.append({"query": word, "context_start": left, "context_end": right,
                                "historical_token": token["text"], "start0": token["start0"],
                                "end0": token["end0"], "side": side,
                                "weighted_similarity": round(similarity, 5)})
        value = len(matched) / max(1, len(companions))
        if value > best_score or value == best_score and len(matched) > len(best_matches):
            best_score, best_matches, best_total = value, matched, len(companions)
        elif not best_total:
            best_total = len(companions)
    return best_score, best_matches, best_total


def ocr_target(page, fragment, actual):
    """Conservatively narrow an existing paragraph alignment to actual OCR text.

    A unique OCR line set after case/diacritic folding is required for a form target.
    Otherwise retain the paragraph's approximate boxes, explicitly labeled.
    """
    allowed = set(fragment.get("ocr", {}).get("line_ids", []))
    lines = [line for line in page["ocr_lines"] if line["id"] in allowed]
    positions = {line["id"]: i for i, line in enumerate(page["ocr_lines"])}
    tokens = [(fold(word), line["id"], positions[line["id"]], canonical(word))
              for line in lines for word, _, _ in word_spans(line["text"])]
    wanted = [fold(word) for word, _, _ in word_spans(actual)]
    literal_wanted = "".join(canonical(word) for word, _, _ in word_spans(actual))
    hits = []
    if wanted:
        for start in range(len(tokens)):
            # Permit OCR whitespace differences, while matching the actual
            # transcription's letters rather than another modernized alias.
            for width in range(1, min(4, len(tokens) - start + 1)):
                span = tokens[start:start + width]
                if any(span[i + 1][2] - span[i][2] > 1 for i in range(len(span) - 1)):
                    continue
                if "".join(t[0] for t in span) == "".join(wanted):
                    hits.append({"line_ids": list(dict.fromkeys(t[1] for t in span)),
                                 "diacritic_folding_needed": "".join(t[3] for t in span) != literal_wanted})
    exact_hits = [h for h in hits if not h["diacritic_folding_needed"]]
    selected_hits = exact_hits or hits
    unique = {tuple(hit["line_ids"]) for hit in selected_hits}
    if len(unique) == 1:
        ids = list(next(iter(unique)))
        return {"status": "form_token_match", "scope": "ocr_lines_containing_form",
                "line_ids": ids, "boxes": [line["box"] for line in page["ocr_lines"] if line["id"] in ids],
                "method": "unique OCR line set for actual transcription tokens within existing paragraph alignment; exact casefolded hits preferred to diacritic-folded hits",
                "matching_token_runs": len(selected_hits), "folded_token_run_count": len(hits),
                "diacritic_folding_needed": not bool(exact_hits), "match_is_editorial_verification": False,
                "is_exact_glyph_box": False}
    return {"status": "paragraph_only" if allowed else "unavailable",
            "scope": "approximate_paragraph", "line_ids": [line["id"] for line in lines],
            "boxes": [line["box"] for line in lines],
            "method": "existing monotonic transcription-to-PDF-OCR token alignment",
            "matching_token_runs": len(selected_hits), "match_is_editorial_verification": False,
            "is_exact_glyph_box": False}


def rank_citation(corpus, page, citation, model, config=None):
    config = {**CONFIG, **(config or {})}
    definition = corpus.dictionary[citation["entry_index"]]["d"]
    quotation_analysis = parse_quotations(citation["context"])
    surfaces, quotes = make_surfaces(citation, definition, quotation_analysis)
    variants = [(s, retrieval_key(s["form"])) for s in surfaces]
    primary_keys = {key for _, key in variants}
    query_words = content_words(citation["context"])
    primary_key = retrieval_key(citation["headword"])
    candidates = []

    def scored_candidate(feature, span, surface, semantic, shared, quotation, quote_matches):
        cost = score(surface["form"], span["text"], model)
        similarity = max(0.0, 1 - cost - surface["penalty"] - .015 * (span["word_count"] - 1))
        if span["common_portuguese_or_grammar_token"]:
            similarity = max(0.0, similarity - (.30 if len(primary_key) <= 2 else .15))
        quoted = bool(surface.get("quotation_occurrences")) and similarity >= .72
        whole = quoted and any(o.get("whole_quotation") for o in surface["quotation_occurrences"])
        local, matches, total = local_quote_support(quotes, surface, feature, span, model) if quoted else (0.0, [], 0)
        value = (config["form_weight"] * similarity + config["portuguese_context_weight"] * semantic +
                 config["quotation_context_weight"] * quotation + config["quoted_surface_weight"] * quoted +
                 config["whole_quotation_weight"] * whole + config["local_quotation_weight"] * local)
        fragment = feature.fragment
        return {
            "source_id": fragment["id"], "source_line": fragment["source_line"],
            "ranking_score": round(value, 5), "score_is_probability": False,
            "form_similarity": round(similarity, 5), "normalized_edit_cost": round(cost, 6),
            "portuguese_context_score": round(semantic, 5), "portuguese_overlap": shared,
            "quotation_context_score": round(quotation, 5), "quotation_matches": quote_matches,
            "quoted_surface_evidence": quoted, "whole_quotation_evidence": whole,
            "local_quotation_score": round(local, 5), "local_quotation_matches": matches,
            "local_quotation_required_companions": total,
            "attested_span": {k: span[k] for k in
                ("text", "start0", "end0", "role", "word_count", "common_portuguese_or_grammar_token")},
            "query_surface": surface,
            "same_form_occurrences": [{"start0": item["start0"], "end0": item["end0"]}
                                      for item in feature.spans
                                      if canonical(item["text"]) == canonical(span["text"])],
            "page_boundary_uncertain": fragment["boundary_uncertain"],
            "fragment_continues_from_previous": fragment["continues_from_previous"],
            "fragment_continues_on_next": fragment["continues_on_next"],
            "review_status": "unreviewed",
        }

    for feature in corpus.features[page["id"]]:
        semantic, shared = portuguese_context(corpus, query_words, feature)
        quotation, quote_matches = quote_support(quotes, feature, primary_keys, model)
        shortlist = []
        for span in feature.spans:
            pairs = []
            for surface, key in variants:
                quick = cheap_similarity(key, span["key"], gb=span["grams"]) - surface["penalty"]
                whole = any(o.get("whole_quotation") for o in surface.get("quotation_occurrences", []))
                priority = quick + (.12 if whole else .05 if surface.get("quotation_occurrences") else 0)
                pairs.append((priority, quick, surface))
            pairs.sort(key=lambda item: (-item[0], item[2]["form"]))
            if pairs:
                shortlist.append((pairs[0][0], span, pairs[:config["surface_shortlist"]]))
        shortlist.sort(key=lambda item: (-item[0], item[1]["word_count"], item[1]["start0"]))
        # Distinct spelling shapes get a chance before duplicate occurrences
        # consume the shortlist. Then score all occurrences of those shapes so
        # local context can select a later repetition in a long paragraph.
        selected_shapes = []
        for _, span, _ in shortlist:
            shape = canonical(span["text"])
            if shape not in selected_shapes:
                selected_shapes.append(shape)
            if len(selected_shapes) >= config["paragraph_span_shortlist"]:
                break
        shape_set = set(selected_shapes)
        span_options = {}
        for _, span, pairs in shortlist:
            if canonical(span["text"]) not in shape_set:
                continue
            for _, quick, surface in pairs:
                if quick < .20:
                    continue
                candidate = scored_candidate(feature, span, surface, semantic, shared, quotation, quote_matches)
                key = (span["start0"], span["end0"])
                previous = span_options.get(key)
                if previous is None or candidate["ranking_score"] > previous["ranking_score"]:
                    span_options[key] = candidate
        ordered = sorted(span_options.values(), key=lambda item: (
            -item["ranking_score"], -item["local_quotation_score"],
            item["attested_span"]["word_count"], item["attested_span"]["start0"]))
        if not ordered:
            if semantic == 0 and quotation == 0:
                continue
            fragment = feature.fragment
            candidate = {
                "source_id": fragment["id"], "source_line": fragment["source_line"],
                "ranking_score": round(config["portuguese_context_weight"] * semantic +
                                       config["quotation_context_weight"] * quotation, 5),
                "score_is_probability": False, "form_similarity": 0.0, "normalized_edit_cost": None,
                "portuguese_context_score": round(semantic, 5), "portuguese_overlap": shared,
                "quotation_context_score": round(quotation, 5), "quotation_matches": quote_matches,
                "quoted_surface_evidence": False, "whole_quotation_evidence": False,
                "local_quotation_score": 0.0, "local_quotation_matches": [],
                "local_quotation_required_companions": 0,
                "attested_span": None, "query_surface": None, "same_form_occurrences": [],
                "page_boundary_uncertain": fragment["boundary_uncertain"],
                "fragment_continues_from_previous": fragment["continues_from_previous"],
                "fragment_continues_on_next": fragment["continues_on_next"], "review_status": "unreviewed",
                "span_alternatives": [],
            }
        else:
            candidate = ordered[0]
            candidate["span_alternatives"] = ordered[1:1 + config["span_alternatives"]]
        candidates.append(candidate)
    candidates.sort(key=lambda c: (-c["ranking_score"], c["source_line"]))
    candidates = candidates[:max(config["top_k"], 2)]
    margin = candidates[0]["ranking_score"] - candidates[1]["ranking_score"] if len(candidates) > 1 else None
    reasons = []
    status = "no_candidate"
    if candidates:
        top = candidates[0]
        if top["form_similarity"] < config["suggestion_min_similarity"]:
            reasons.append("weak_form_fit")
        if margin is None or margin < config["suggestion_min_margin"]:
            reasons.append("close_competing_passage")
        if len(primary_key) <= 4 and max(top["portuguese_context_score"], top["quotation_context_score"],
                                       top["local_quotation_score"]) < config["short_form_min_context"] and not top["whole_quotation_evidence"]:
            reasons.append("short_form_without_context")
        if top["page_boundary_uncertain"]:
            reasons.append("page_boundary_uncertain")
        if top["attested_span"] and top["attested_span"]["common_portuguese_or_grammar_token"]:
            reasons.append("possible_portuguese_or_grammar_word")
        if top["attested_span"] and top["attested_span"]["role"] != "post_separator_text":
            reasons.append("source_zone_not_a_lexical_body")
        if quotes and not top["quoted_surface_evidence"]:
            reasons.append("explicit_quoted_surface_not_matched")
        if (not top["quoted_surface_evidence"] and top["portuguese_context_score"] == 0 and
                top["quotation_context_score"] == 0):
            reasons.append("form_only_without_independent_context")
        if quotation_analysis["issues"]:
            reasons.append("quotation_parse_requires_review")
        if (top.get("query_surface") or {}).get("kind") == "quoted_compound_prefix_hypothesis":
            reasons.append("compound_prefix_hypothesis_requires_review")
        if (top.get("query_surface") or {}).get("kind") == "quoted_question_fusion_hypothesis":
            reasons.append("question_fusion_hypothesis_requires_review")
        if top["local_quotation_required_companions"] and top["local_quotation_score"] < 1:
            reasons.append("local_quotation_context_incomplete")
        if len(top["same_form_occurrences"]) > 1:
            reasons.append("repeated_form_in_passage")
        if citation.get("adapted"):
            reasons.append("adapted_quotation_requires_review")
        status = "suggested" if not reasons else "needs_review"
        if top["form_similarity"] < .55 and top["portuguese_context_score"] < .20 and top["quotation_context_score"] == 0:
            status = "weak_candidates"
    for candidate in candidates:
        fragment = next(f for f in page["fragments"] if f["id"] == candidate["source_id"])
        for option in [candidate, *candidate.get("span_alternatives", [])]:
            span = option["attested_span"]
            if span:
                assert corpus.text[span["start0"]:span["end0"]] == span["text"]
                assert fragment["source_start0"] <= span["start0"] < span["end0"] <= fragment["source_end0"]
                option["orthographic_alignment"] = align(option["query_surface"]["form"], span["text"], model)
                option["ocr_target"] = ocr_target(page, fragment, span["text"])
            else:
                option["ocr_target"] = {"status": "unavailable", "line_ids": [], "boxes": []}
    return {"citation_id": citation["id"], "page_id": page["id"],
            "entry_index": citation["entry_index"], "headword": citation["headword"],
            "homonym": citation["homonym"], "adapted": citation.get("adapted", False),
            "status": status, "status_is_editorial_verification": False,
            "margin": None if margin is None else round(margin, 5), "review_reasons": reasons,
            "candidates": candidates[:config["top_k"]],
            "quotation_detection": quotes, "quotation_parse": quotation_analysis,
            "existing_reviewed_source_ids": [a["source_id"] for a in citation["associations"] if a["status"] == "reviewed"]}


def existing_ranking(citation):
    reviewed = [a for a in citation["associations"] if a["status"] == "reviewed"]
    proposed = sorted((a for a in citation["associations"] if a["status"] != "reviewed"),
                      key=lambda a: (-a.get("score", 0), a["source_line"]))
    return [a["source_id"] for a in reviewed + proposed if a.get("fragment_available")]


def evaluate(labels, predictions, baseline):
    """Paragraph ranking accuracy, explicitly conditional on reviewable cases."""
    rows = []
    for case in labels["cases"]:
        key = (case["citation_id"], case["page_id"])
        prediction = predictions[key]
        gold = set(case["source_ids"])
        ranked = [c["source_id"] for c in prediction["candidates"]]
        old = baseline.get(key, [])
        best = prediction["candidates"][0] if prediction["candidates"] else None
        span = best.get("attested_span") if best else None
        targets = [t for t in case.get("targets", []) if best and t["source_id"] == best["source_id"]]
        exact_span = bool(span and any(span["start0"] == t["form_start0"] and span["end0"] == t["form_end0"] for t in targets))
        containing_span = bool(span and any(
            span["start0"] <= t["form_start0"] < t["form_end0"] <= span["end0"] or
            t["form_start0"] <= span["start0"] < span["end0"] <= t["form_end0"] for t in targets))
        def exact_option(option):
            actual = option.get("attested_span")
            return bool(actual and any(
                option["source_id"] == t["source_id"] and
                actual["start0"] == t["form_start0"] and actual["end0"] == t["form_end0"]
                for t in case.get("targets", [])))
        offered = [option for candidate in prediction["candidates"][:3]
                   for option in [candidate, *candidate.get("span_alternatives", [])]]
        rows.append({"case_id": case["case_id"], "label_status": case["status"],
                     "headword": case["headword"], "page_id": case["page_id"],
                     "gold_source_ids": sorted(gold), "ranked_source_ids": ranked,
                     "top1_correct": bool(ranked and ranked[0] in gold) if case["status"] == "clear" else None,
                     "top3_contains_gold": bool(set(ranked[:3]) & gold) if case["status"] == "clear" else None,
                     "top1_exact_attested_span": exact_span if case["status"] == "clear" else None,
                     "top3_exact_attested_span": any(exact_option(c) for c in prediction["candidates"][:3]) if case["status"] == "clear" else None,
                     "offered_exact_attested_span": any(exact_option(c) for c in offered) if case["status"] == "clear" else None,
                     "offered_span_count": sum(bool(c.get("attested_span")) for c in offered),
                     "top1_attested_span_contains_or_is_in_gold": containing_span if case["status"] == "clear" else None,
                     "existing_top1_correct": bool(old and old[0] in gold) if case["status"] == "clear" else None,
                     "existing_top3_contains_gold": bool(set(old[:3]) & gold) if case["status"] == "clear" else None,
                     "proposal_status": prediction["status"]})
    clear = [r for r in rows if r["label_status"] == "clear"]
    suggested = [r for r in clear if r["proposal_status"] == "suggested"]
    return {"reviewer": "assistant", "evaluation_unit": "citation/page → source paragraph",
            "not_measured": ["human-verified lexical equivalence", "exact scan glyph-box accuracy", "corpus-wide accuracy"],
            "counts": {"all_cases": len(rows), "clear_cases": len(clear),
                       "ambiguous_cases": sum(r["label_status"] == "ambiguous" for r in rows),
                       "not_found_cases": sum(r["label_status"] == "not_found" for r in rows),
                       "top1_correct": sum(r["top1_correct"] for r in clear),
                       "top3_contains_gold": sum(r["top3_contains_gold"] for r in clear),
                       "top1_exact_attested_span": sum(r["top1_exact_attested_span"] for r in clear),
                       "top3_exact_attested_span": sum(r["top3_exact_attested_span"] for r in clear),
                       "offered_exact_attested_span": sum(r["offered_exact_attested_span"] for r in clear),
                       "top1_attested_span_contains_or_is_in_gold": sum(r["top1_attested_span_contains_or_is_in_gold"] for r in clear),
                       "existing_top1_correct": sum(r["existing_top1_correct"] for r in clear),
                       "existing_top3_contains_gold": sum(r["existing_top3_contains_gold"] for r in clear),
                       "suggested_clear_cases": len(suggested),
                       "suggested_correct": sum(r["top1_correct"] for r in suggested),
                       "suggested_ambiguous_or_not_found": sum(r["proposal_status"] == "suggested" and r["label_status"] != "clear" for r in rows)},
            "offered_metric_scope": "Exact literal span among up to three paragraph candidates, including each paragraph's saved span_alternatives. Legacy top1/top3 measures use only each paragraph's best span.",
            "cases": rows}
