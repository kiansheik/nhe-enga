"""Conservative, reproducible silver seed extraction from existing page evidence.

These anchors are intentionally selected with the old spelling aliases and thus
cannot validate those aliases.  They are training observations, never reviewed
citations or proof that a whole VLB record is covered by a dictionary entry.
"""

from collections import defaultdict
import hashlib
import re
import unicodedata

from .orthography import normalize_form, normalize_headword


_APOSTROPHES = "'’‘ʼʻ"


def _words(text):
    """Yield original Unicode word surfaces and exact codepoint offsets."""
    start = None
    for index, char in enumerate(text):
        letter = unicodedata.category(char)[0] in {"L", "M"}
        joiner = char in _APOSTROPHES + "-" and start is not None and index + 1 < len(text) and unicodedata.category(text[index + 1])[0] == "L"
        leading_apostrophe = char in _APOSTROPHES and start is None and index + 1 < len(text) and unicodedata.category(text[index + 1])[0] == "L"
        if letter or joiner or leading_apostrophe:
            if start is None:
                start = index
        elif start is not None:
            yield text[start:index], start, index
            start = None
    if start is not None:
        yield text[start:], start, len(text)


def _legacy_key(text):
    text = text.casefold().replace("ç", "s")
    text = "".join(char for char in unicodedata.normalize("NFD", text) if not unicodedata.combining(char))
    return re.sub("[^a-z]", "", text.replace("c", "k").replace("j", "i"))


def _body_start(text):
    """Only trust an observed entry separator; no guessed Portuguese sentence cut."""
    for separator in ("—", " – "):
        position = text.find(separator)
        if position >= 0:
            return position + len(separator)
    return None


def _explicit_quote_tokens(context):
    """Tokens only from colon-introduced examples followed by a translation dash.

    This misses examples introduced in other ways by design.  Returning a token
    certifies its position in an example-shaped span, not a linguistic parse.
    """
    tokens = defaultdict(list)
    for colon in re.finditer(":", context):
        remainder = context[colon.end():colon.end() + 240]
        delimiter = re.search(r"(?:\s+[–—-]\s+|\.\s*[-–—]\s*)", remainder)
        if not delimiter:
            continue
        span = remainder[:delimiter.start()]
        if ";" in span or "(" in span or ")" in span:
            continue
        for word, start, end in _words(span):
            tokens[_legacy_key(word)].append((word, colon.end() + start, colon.end() + end))
    return tokens


def extract_seeds(pages, excluded_headwords=(), excluded_pages=(), excluded_source_ids=()):
    """Return selected silver pairs with original source offsets and exclusions.

    A pair must have a distinctive (>=4-letter) headword, one old shortlisted
    candidate supported by Portuguese entry-head overlap, one matching surface
    after an observed entry separator, and no competing occurrence in another
    paragraph on the cited page.  Prefix alternatives are explicit hypotheses,
    never spelling operations.  Unsegmented paragraphs are excluded.
    """
    excluded_heads = {normalize_headword(head) for head in excluded_headwords}
    excluded_page_ids = set(excluded_pages)
    excluded_sources = set(excluded_source_ids)
    seeds, seen = [], set()
    for page in sorted(pages, key=lambda item: item["id"]):
        if page["id"] in excluded_page_ids:
            continue
        fragments = {fragment["id"]: fragment for fragment in page["fragments"]}
        word_records, page_occurrences = {}, defaultdict(set)
        for fragment in page["fragments"]:
            records = list(_words(fragment["text"]))
            word_records[fragment["id"]] = records
            for word, _, _ in records:
                page_occurrences[_legacy_key(word)].add(fragment["id"])
        for citation in sorted(page.get("citations", []), key=lambda item: item["id"]):
            headword = citation["headword"]
            key = _legacy_key(headword)
            if len(key) < 4 or normalize_headword(headword) in excluded_heads:
                continue
            variants = {
                key: (headword, ""),
                "a" + key: ("a" + headword, "a"),
                "ai" + key: ("aî" + headword, "aî"),
                "xe" + key: ("xe" + headword, "xe"),
            }
            candidates = {}
            for association in citation.get("associations", []):
                if association["source_id"] in excluded_sources:
                    continue
                head_support = [evidence for evidence in association.get("evidence", []) if evidence["type"] == "context_to_Portuguese_head_token_overlap"]
                if not head_support:
                    continue
                fragment = fragments.get(association["source_id"])
                if not fragment:
                    continue
                body_start = _body_start(fragment["text"])
                if body_start is None:
                    continue
                matches = [(word, start, end) for word, start, end in word_records[fragment["id"]]
                           if start >= body_start and _legacy_key(word) in variants]
                # Repeated identical surface text is one type, with all offsets
                # retained. Distinct spellings or prefix choices are ambiguous.
                forms = {normalize_form(word) for word, _, _ in matches}
                if len(forms) != 1:
                    continue
                word, start, end = matches[0]
                if len(page_occurrences[_legacy_key(word)]) != 1:
                    continue
                candidates[fragment["id"]] = (fragment, matches, head_support)
            if len(candidates) != 1:
                continue
            fragment, matches, head_support = next(iter(candidates.values()))
            word, start, end = matches[0]
            modern, prefix = variants[_legacy_key(word)]
            morphology = {"kind": "literal_headword" if not prefix else "hypothesized_prefix",
                          "prefix": prefix, "linguistic_analysis_verified": False}
            context = citation.get("context", "")
            quoted = _explicit_quote_tokens(context).get(_legacy_key(word), [])
            quote_span = None
            # Require the exact generated modern spelling, including diacritics,
            # so a vague alias match cannot masquerade as a quoted modern form.
            exact_quotes = [item for item in quoted if normalize_form(item[0]) == normalize_form(modern)]
            if exact_quotes:
                modern, quote_start, quote_end = exact_quotes[0]
                morphology = {"kind": "explicit_context_surface", "prefix": prefix,
                              "linguistic_analysis_verified": False}
                quote_span = {"start_in_context": quote_start, "end_in_context": quote_end}
            signature = (normalize_headword(headword), normalize_form(modern), normalize_form(word), page["id"])
            if signature in seen:
                continue
            seen.add(signature)
            identity = "|".join((citation["id"], page["id"], fragment["id"], str(start), modern, word))
            fragment_start = fragment.get("source_start0")
            seed = {
                "seed_id": "silver-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16],
                "citation_id": citation["id"], "page_id": page["id"],
                "source_id": fragment["id"], "source_line": fragment.get("source_line"),
                "headword": headword, "modern_form": modern, "vlb_form": word,
                "evidence_kind": "same_page_unique_legacy_form_plus_Portuguese_head_overlap",
                "status": "silver_proposed", "morphology": morphology,
                "source_zone": "after_observed_entry_separator_may_include_Portuguese_commentary",
                "source_form_start_in_fragment": start, "source_form_end_in_fragment": end,
                "source_start0": fragment_start + start if fragment_start is not None else None,
                "source_end0": fragment_start + end if fragment_start is not None else None,
                "source_occurrences_in_fragment": [{"start": a, "end": b} for _, a, b in matches],
                "Portuguese_head_evidence": head_support,
                "selection_aliases": "case/accent/apostrophe folding; c~k, ç~s, j~i; explicit a/aî/xe prefix hypotheses",
                "selection_bias_warning": "This pair cannot independently validate the aliases used to select it.",
            }
            if quote_span:
                seed["modern_context_span"] = quote_span
            seeds.append(seed)
    return sorted(seeds, key=lambda item: item["seed_id"])
