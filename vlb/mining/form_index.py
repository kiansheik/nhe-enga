"""Compact headword index of the frozen citation/page predictions.

An index entry records ranking proposals, never a verified lexical equivalence.
The same dictionary headword can have several actual historical surface forms.
"""
from collections import defaultdict


def build_form_index(records, provenance):
    entries = {}
    for record in records:
        entry = entries.setdefault(record["entry_index"], {
            "entry_index": record["entry_index"], "headword": record["headword"],
            "homonym": record["homonym"], "citation_page_memberships": 0,
            "forms": defaultdict(list), "without_form": [],
        })
        entry["citation_page_memberships"] += 1
        top = record["candidates"][0] if record["candidates"] else None
        span = top.get("attested_span") if top else None
        reference = {"citation_id": record["citation_id"], "page_id": record["page_id"],
                     "status": record["status"]}
        if span:
            entry["forms"][span["text"]].append({
                **reference, "source_id": top["source_id"],
                "start0": span["start0"], "end0": span["end0"],
                "similarity": top["form_similarity"],
                "ocr_line_ids": top["ocr_target"]["line_ids"],
                "ocr_scope": top["ocr_target"].get("scope"),
            })
        else:
            entry["without_form"].append(reference)
    result = []
    for _, entry in sorted(entries.items()):
        entry["forms"] = [{"historical_form": form, "proposals": refs}
                          for form, refs in sorted(entry["forms"].items(),
                              key=lambda item: (-len(item[1]), item[0]))]
        result.append(entry)
    return {"schema_version": 1, "provenance": provenance,
            "scope": "Top-ranked attested form for each valid citation/page membership, grouped by dictionary snapshot row. Multiple forms and uncertainty are retained.",
            "all_associations_unreviewed": True, "scores_are_probabilities": False,
            "forms_sorted_by": "number of top-ranked proposals, not linguistic frequency or probability",
            "entry_count": len(result), "entries": result}
