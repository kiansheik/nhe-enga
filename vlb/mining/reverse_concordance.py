"""Build a source-to-dictionary review inventory for every VLB record.

The citation miner starts with Navarro entries and searches a cited VLB page.
This module reverses that view: every lexicographic record in Emerson's saved
transcription is retained, together with bounded dictionary candidates.  A
candidate is review material, not proof that the whole source record (or even
the proposed span) has been lexicographically accounted for.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from functools import lru_cache
import hashlib
from pathlib import Path

from .orthography import compile_model, score
from .pipeline import (Corpus, cheap_similarity, content_words, grams,
                       make_surfaces, read_json, retrieval_key,
                       sha, stable_json, word_spans, write_json)


CONFIG = {
    "version": "vlb-source-reverse-v1",
    "dictionary_scope": "headword search over rows marked t=1; frozen V2 evidence retained for cited rows in every dictionary section",
    "max_headword_only_candidates_per_source": 8,
    "max_shortlist_per_span": 4,
    "max_gram_candidates": 80,
    "minimum_key_length": 3,
    "minimum_similarity_long": 0.84,
    "minimum_similarity_medium": 0.87,
    "minimum_similarity_short": 0.91,
    "no_semantic_evidence_penalty": 0.03,
    "generated_surface_penalty": 0.02,
    "ambiguity_margin": 0.035,
    "scores_are_probabilities": False,
}

ALLOWED_SURFACE_KINDS = {
    "headword",
    "editorial_optional_form",
    "explicit_dictionary_adjective_form",
    "surface_prefix_hypothesis",
}


def _round(value):
    return round(float(value), 6)


def _source_records(corpus):
    """Return all unique entry records and their page-bounded fragments."""
    records = {}
    page_order = {page["id"]: index for index, page in enumerate(corpus.pages)}
    for page in corpus.pages:
        for feature in corpus.features[page["id"]]:
            source_id = feature.fragment["id"]
            unit = corpus.units[source_id]
            source_line = feature.fragment["source_line"]
            record = records.setdefault(source_id, {
                "source_id": source_id,
                "source_line": source_line,
                "source_start0": unit["start"],
                "source_end0": unit["start"] + len(unit["text"]),
                "text": unit["text"],
                "features": [],
                "page_ids": set(),
            })
            assert record["source_line"] == source_line
            assert record["text"] == unit["text"]
            record["features"].append((page["id"], feature))
            record["page_ids"].add(page["id"])
    expected = corpus.manifest["counts"]["lexicographic_records"]
    assert len(records) == expected, (len(records), expected)
    for record in records.values():
        record["features"].sort(key=lambda pair: (
            page_order[pair[0]], pair[1].fragment["source_start0"]))
        record["page_ids"] = sorted(record["page_ids"], key=page_order.get)
    return records


def _dictionary_forms(dictionary):
    """Index literal headwords plus the same bounded V2 surface hypotheses."""
    forms = []
    entries = {}
    for entry_index, row in enumerate(dictionary):
        if "i" in row:
            assert row["i"] == entry_index
        entry = {
            "entry_index": entry_index,
            "headword": row["f"],
            "homonym": row.get("o", ""),
            "definition_words": content_words(row.get("d", "")),
        }
        entries[entry_index] = entry
        # The main Tupi-to-Portuguese lexicon is explicitly marked t=1.
        # Other sections (notably Nomes) are retained when V2 cites them, but
        # are not swept into unconstrained headword matching.
        if row.get("t") != 1:
            continue
        citation = {"headword": row["f"], "context": ""}
        surfaces, _ = make_surfaces(citation, row.get("d", ""))
        seen = set()
        for surface in surfaces:
            if surface["kind"] not in ALLOWED_SURFACE_KINDS:
                continue
            key = retrieval_key(surface["form"])
            signature = (key, surface["kind"])
            if not key or signature in seen:
                continue
            seen.add(signature)
            forms.append({
                "entry_index": entry_index,
                "form": surface["form"],
                "kind": surface["kind"],
                "penalty": surface.get("penalty", 0.0),
                "key": key,
                "grams": grams(key),
                "word_count": len(list(word_spans(surface["form"]))),
            })
    return entries, forms


def _form_indexes(forms):
    exact = defaultdict(list)
    by_gram = defaultdict(list)
    for form_index, form in enumerate(forms):
        exact[form["key"]].append(form_index)
        for gram in form["grams"]:
            by_gram[gram].append(form_index)
    return exact, by_gram


def _minimum_similarity(key_length, *, has_semantic_evidence, generated):
    if key_length <= 4:
        threshold = CONFIG["minimum_similarity_short"]
    elif key_length <= 6:
        threshold = CONFIG["minimum_similarity_medium"]
    else:
        threshold = CONFIG["minimum_similarity_long"]
    if not has_semantic_evidence:
        threshold += CONFIG["no_semantic_evidence_penalty"]
    if generated:
        threshold += CONFIG["generated_surface_penalty"]
    return min(0.98, threshold)


def _headword_evidence(records, corpus, entries, forms, model):
    """Return best exact source-span evidence per source and dictionary row."""
    exact, by_gram = _form_indexes(forms)

    @lru_cache(maxsize=None)
    def shortlist(key):
        exact_ids = set(exact.get(key, ()))
        ranked = []
        if len(key) >= CONFIG["minimum_key_length"]:
            overlap = Counter()
            for gram in grams(key):
                overlap.update(by_gram.get(gram, ()))
            rough = sorted(overlap, key=lambda i: (
                -overlap[i], abs(len(forms[i]["key"]) - len(key)),
                forms[i]["entry_index"], forms[i]["form"]))
            for form_index in rough[:CONFIG["max_gram_candidates"]]:
                form = forms[form_index]
                ratio = len(form["key"]) / max(1, len(key))
                if not 0.55 <= ratio <= 1.8:
                    continue
                quick = cheap_similarity(key, form["key"], grams(key), form["grams"])
                quick_threshold = 0.65 if len(key) <= 6 else 0.55
                if quick >= quick_threshold:
                    ranked.append((quick, form_index))
        for form_index in exact_ids:
            ranked.append((1.0, form_index))
        ranked.sort(key=lambda item: (
            -item[0], abs(len(forms[item[1]]["key"]) - len(key)),
            forms[item[1]]["entry_index"], forms[item[1]]["form"]))
        result, seen = [], set()
        for _, form_index in ranked:
            signature = (forms[form_index]["entry_index"], forms[form_index]["form"])
            if signature in seen:
                continue
            seen.add(signature)
            result.append(form_index)
            if len(result) >= CONFIG["max_shortlist_per_span"]:
                break
        return tuple(result)

    evidence = defaultdict(dict)
    for source_id, record in records.items():
        for page_id, feature in record["features"]:
            for span in feature.spans:
                if span["role"] == "cross_reference" or span["common_portuguese_or_grammar_token"]:
                    continue
                key = span["key"]
                if len(key) < CONFIG["minimum_key_length"] and key not in exact:
                    continue
                for form_index in shortlist(key):
                    form = forms[form_index]
                    exact_key = key == form["key"]
                    if (span["word_count"] > 1 and form["word_count"] == 1 and
                            not exact_key):
                        continue
                    if abs(span["word_count"] - form["word_count"]) > 1:
                        continue
                    entry = entries[form["entry_index"]]
                    shared = sorted(feature.head_words & entry["definition_words"])
                    semantic = min(1.0, sum(corpus.idf.get(word, 1.0) for word in shared) / 18.0)
                    generated = form["kind"] == "surface_prefix_hypothesis"
                    similarity = 1.0 - score(form["form"], span["text"], model)
                    threshold = _minimum_similarity(
                        max(len(key), len(form["key"])),
                        has_semantic_evidence=bool(shared), generated=generated)
                    if not exact_key and similarity < threshold:
                        continue
                    if exact_key and len(key) < CONFIG["minimum_key_length"] and not shared:
                        continue
                    ranking = (0.78 * similarity + 0.17 * semantic +
                               (0.05 if exact_key else 0.0) - form["penalty"])
                    item = {
                        "method": "dictionary_headword_form",
                        "query_form": form["form"],
                        "query_kind": form["kind"],
                        "source_span": {
                            "start0": span["start0"],
                            "end0": span["end0"],
                            "text": span["text"],
                            "page_id": page_id,
                        },
                        "exact_retrieval_key": exact_key,
                        "form_similarity": _round(similarity),
                        "portuguese_context_score": _round(semantic),
                        "portuguese_overlap": shared,
                        "ranking_score": _round(ranking),
                        "score_is_probability": False,
                        "review_status": "unreviewed",
                    }
                    previous = evidence[source_id].get(form["entry_index"])
                    order = (ranking, exact_key, semantic, similarity,
                             -span["start0"], form["form"])
                    if previous is None or order > previous[0]:
                        evidence[source_id][form["entry_index"]] = (order, item)
    return {source_id: {entry_index: item for entry_index, (_, item) in rows.items()}
            for source_id, rows in evidence.items()}


def _v2_evidence(v2, dictionary, source_text):
    """Invert every saved V2 paragraph proposal without promoting its status."""
    evidence = defaultdict(lambda: defaultdict(list))
    for proposal in v2["records"]:
        entry_index = proposal["entry_index"]
        row = dictionary[entry_index]
        assert row["f"] == proposal["headword"]
        reviewed_ids = set(proposal.get("existing_reviewed_source_ids", ()))
        for rank, candidate in enumerate(proposal["candidates"], 1):
            source_id = candidate["source_id"]
            span = candidate.get("attested_span")
            saved_span = None
            if span:
                assert source_text[span["start0"]:span["end0"]] == span["text"]
                saved_span = {key: span[key] for key in ("start0", "end0", "text")}
                saved_span["page_id"] = proposal["page_id"]
            reviewed = source_id in reviewed_ids
            ranking = (0.64 * candidate.get("form_similarity", 0.0) +
                       0.16 * candidate.get("portuguese_context_score", 0.0) +
                       0.10 * candidate.get("quotation_context_score", 0.0) +
                       0.10 * candidate.get("local_quotation_score", 0.0) -
                       0.03 * (rank - 1))
            if rank == 1 and proposal["status"] == "suggested":
                ranking += 0.06
            if reviewed:
                ranking = 1.0
            item = {
                "method": "v2_citation_candidate",
                "citation_id": proposal["citation_id"],
                "page_id": proposal["page_id"],
                "candidate_rank": rank,
                "proposal_status": proposal["status"],
                "source_span": saved_span,
                "form_similarity": candidate.get("form_similarity"),
                "portuguese_context_score": candidate.get("portuguese_context_score"),
                "quotation_context_score": candidate.get("quotation_context_score"),
                "local_quotation_score": candidate.get("local_quotation_score"),
                "ranking_score": _round(ranking),
                "score_is_probability": False,
                "review_status": "reviewed" if reviewed else "unreviewed",
            }
            evidence[source_id][entry_index].append(item)
    for entries in evidence.values():
        for items in entries.values():
            items.sort(key=lambda item: (
                -item["ranking_score"], item["candidate_rank"],
                item["citation_id"], item["page_id"]))
    return evidence


def _candidate(entry, headword_item, v2_items):
    evidence = ([headword_item] if headword_item else []) + list(v2_items)
    methods = sorted({item["method"] for item in evidence})
    reviewed = any(item["review_status"] == "reviewed" for item in evidence)
    ranking = max(item["ranking_score"] for item in evidence)
    if len(methods) > 1 and not reviewed:
        ranking = min(0.999999, ranking + 0.02)
    strong = reviewed or any(
        item["method"] == "v2_citation_candidate" and
        item["candidate_rank"] == 1 and item["proposal_status"] == "suggested"
        for item in evidence)
    strong = strong or any(
        item["method"] == "dictionary_headword_form" and
        item["exact_retrieval_key"] and len(retrieval_key(item["query_form"])) >= 4
        for item in evidence)
    return {
        "entry_index": entry["entry_index"],
        "headword": entry["headword"],
        "homonym": entry["homonym"],
        "ranking_score": _round(ranking),
        "score_is_probability": False,
        "support": "strong_candidate" if strong else "uncertain_candidate",
        "review_status": "reviewed" if reviewed else "unreviewed",
        "evidence_methods": methods,
        "evidence": evidence,
    }


def build_reverse_concordance(repository: Path):
    repository = repository.resolve()
    corpus = Corpus(repository)
    dictionary_path = repository / "docs/dict-conjugated.json.gz"
    dictionary = read_json(dictionary_path)
    v2_path = repository / "vlb/mining/output-v2/candidates.json.gz"
    model_path = repository / "vlb/mining/output-v2/orthography-model.json"
    v2 = read_json(v2_path)
    model_data = read_json(model_path)
    model = compile_model(model_data)
    records = _source_records(corpus)
    entries, forms = _dictionary_forms(dictionary)
    headword = _headword_evidence(records, corpus, entries, forms, model)
    citation = _v2_evidence(v2, dictionary, corpus.text)

    output_records = []
    evidence_method_records = Counter()
    candidate_review = Counter()
    for source_id, source in sorted(records.items(), key=lambda item: item[1]["source_line"]):
        entry_ids = set(headword.get(source_id, ())) | set(citation.get(source_id, ()))
        candidates = [
            _candidate(entries[entry_index], headword.get(source_id, {}).get(entry_index),
                       citation.get(source_id, {}).get(entry_index, ()))
            for entry_index in entry_ids
        ]
        candidates.sort(key=lambda item: (
            item["review_status"] != "reviewed", -item["ranking_score"],
            item["entry_index"]))
        # Preserve every bounded V2 citation proposal. Only the broad new
        # headword-only sweep is capped for compactness.
        v2_entry_ids = set(citation.get(source_id, ()))
        v2_candidates = [candidate for candidate in candidates
                         if candidate["entry_index"] in v2_entry_ids]
        headword_only = [candidate for candidate in candidates
                         if candidate["entry_index"] not in v2_entry_ids]
        candidates = sorted(
            v2_candidates + headword_only[:CONFIG["max_headword_only_candidates_per_source"]],
            key=lambda item: (item["review_status"] != "reviewed",
                              -item["ranking_score"], item["entry_index"]),
        )
        reviewed = any(candidate["review_status"] == "reviewed" for candidate in candidates)
        strong = [candidate for candidate in candidates if candidate["support"] == "strong_candidate"]
        margin = (candidates[0]["ranking_score"] - candidates[1]["ranking_score"]
                  if len(candidates) > 1 else None)
        if not candidates:
            status = "unmatched"
        elif reviewed:
            status = "candidate_linked"
        elif strong and (margin is None or margin >= CONFIG["ambiguity_margin"]):
            status = "candidate_linked"
        else:
            status = "ambiguous"
        methods = sorted({method for candidate in candidates
                          for method in candidate["evidence_methods"]})
        for method in methods:
            evidence_method_records[method] += 1
        candidate_review.update(candidate["review_status"] for candidate in candidates)
        output_records.append({
            "source_id": source_id,
            "source_line": source["source_line"],
            "source_start0": source["source_start0"],
            "source_end0": source["source_end0"],
            "text": source["text"],
            "page_ids": source["page_ids"],
            "fragment_count": len(source["features"]),
            "status": status,
            "review_status": "partially_reviewed" if reviewed else "unreviewed",
            "coverage": {
                "status": "not_assessed",
                "fully_covered": False,
                "reason": "Candidate spans do not establish that every lexical form or sense in this source record is represented in the dictionary.",
            },
            "candidate_margin": _round(margin) if margin is not None else None,
            "evidence_methods": methods,
            "candidates": candidates,
        })

    status_counts = Counter(record["status"] for record in output_records)
    payload = {
        "schema_version": 1,
        "algorithm": CONFIG,
        "provenance": {
            **corpus.provenance,
            "dictionary_sha256": sha(dictionary_path),
            "v2_candidates_sha256": sha(v2_path),
            "v2_model_sha256": sha(model_path),
            "v2_prediction_model_kind": v2["model_kind"],
            "v2_prediction_model_sha256": v2["model_sha256"],
            "reverse_concordance_code_sha256": sha(
                repository / "vlb/mining/reverse_concordance.py"),
            "shared_pipeline_code_sha256": sha(
                repository / "vlb/mining/pipeline.py"),
            "orthography_code_sha256": sha(
                repository / "vlb/mining/orthography.py"),
        },
        "scope": "Every lexicographic source record in the pinned Emerson transcription; compact review artifact excluded from the default reader payload.",
        "interpretation": "All links are candidates unless their evidence says reviewed. No record is marked fully covered; one matched word is not paragraph coverage.",
        "scores_are_probabilities": False,
        "counts": {
            "source_records": len(output_records),
            "status": dict(sorted(status_counts.items())),
            "records_with_candidates": sum(bool(record["candidates"]) for record in output_records),
            "unresolved_records": status_counts["ambiguous"] + status_counts["unmatched"],
            "candidate_links_retained": sum(len(record["candidates"]) for record in output_records),
            "candidate_review_status": dict(sorted(candidate_review.items())),
            "records_by_evidence_method": dict(sorted(evidence_method_records.items())),
            "partially_reviewed_records": sum(record["review_status"] == "partially_reviewed"
                                               for record in output_records),
            "fully_covered_records": 0,
            "dictionary_rows": len(entries),
            "dictionary_headword_search_rows": sum(row.get("t") == 1 for row in dictionary),
            "dictionary_search_forms": len(forms),
        },
        "records": output_records,
    }
    assert payload["counts"]["source_records"] == 7534
    assert payload["counts"]["fully_covered_records"] == 0
    return payload


def _report(summary):
    counts = summary["counts"]
    statuses = counts["status"]
    return f"""# VLB source-to-dictionary reverse concordance

This inventory starts from all **{counts['source_records']:,}** lexicographic
records in the pinned Emerson transcription and retains bounded Navarro
dictionary candidates for future review. It is not loaded by the browser and
does not alter the frozen V1/V2 experiments.

## Recomputed inventory

| Status | Records |
| --- | ---: |
| Candidate linked (still not paragraph coverage) | {statuses.get('candidate_linked', 0):,} |
| Ambiguous candidates | {statuses.get('ambiguous', 0):,} |
| Unmatched | {statuses.get('unmatched', 0):,} |
| Records with at least one retained candidate | {counts['records_with_candidates']:,} |
| Fully covered records | {counts['fully_covered_records']:,} |

The earlier reported 7,094/440 split was not assumed. These counts were
recomputed from the checked-in dictionary, transcription, frozen V2 proposals,
and V2 directional spelling model. `candidate_linked` means only that the
ranking has a separated strong candidate. `ambiguous` and `unmatched` remain
unresolved. All unreviewed candidates require lexical and semantic review.

## Evidence and reproduction

The artifact combines inverted V2 citation candidates with literal dictionary
headwords, explicit editorial variants, and the same bounded prefix hypotheses
used by V2. Every saved source span is validated against the unchanged source
text and a page membership. Scores are deterministic ranking weights, not
probabilities.

```sh
python3 vlb/build_reverse_concordance.py
python3 -m unittest tests.test_vlb_reverse_concordance
```

Artifact SHA-256: `{summary['artifact_sha256']}`.
"""


def write_reverse_concordance(repository: Path, output: Path):
    repository = repository.resolve()
    output = output.resolve()
    frozen = {
        (repository / "vlb/mining/output").resolve(),
        (repository / "vlb/mining/output-v2").resolve(),
    }
    if output in frozen:
        raise ValueError("reverse concordance output must not overwrite frozen V1/V2 artifacts")
    payload = build_reverse_concordance(repository)
    output.mkdir(parents=True, exist_ok=True)
    artifact = output / "source-dictionary-concordance.json.gz"
    write_json(artifact, payload)
    summary = {
        "schema_version": 1,
        "algorithm": CONFIG,
        "provenance": payload["provenance"],
        "counts": payload["counts"],
        "artifact": artifact.name,
        "artifact_sha256": sha(artifact),
        "uncompressed_payload_sha256": hashlib.sha256(stable_json(payload)).hexdigest(),
        "default_browser_payload": False,
        "frozen_v1_v2_modified": False,
    }
    write_json(output / "summary.json", summary, pretty=True)
    (output / "REPORT.md").write_text(_report(summary), encoding="utf-8")
    return summary
