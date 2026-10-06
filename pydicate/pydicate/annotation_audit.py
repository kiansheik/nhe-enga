"""Check annotation transport and expose the evidence behind a breakdown.

An evaluation witness is not a linguistic proof or a unique morpheme producer.
The legacy DEEPEST_NODE alignment is heuristic. This report keeps it separate
from a complete inventory of stored Predicate relations and evaluation events.
"""

from collections import Counter, defaultdict
import re


SCHEMA_VERSION = 1
LIST_RELATIONS = (
    "arguments",
    "pre_adjuncts",
    "post_adjuncts",
    "v_adjuncts",
    "v_adjuncts_pre",
    "compositions",
    "_arguments",
)
NODE_RELATIONS = (
    "principal",
    "_augmentee",
    "_augmentor",
    "incorporated_object",
    "source_verb",
    "_subject",
    "_nominalization_source",
    "verb",
    "noun",
    "arg0",
    "_predicate",
)
_DEEPEST = re.compile(r"DEEPEST_NODE_(\d+)\Z")


def parse_occurrences(text):
    """Preserve ordered spellings/whitespace and reject malformed tag syntax."""
    pieces = []
    cursor = 0
    surface_offset = 0
    while cursor < len(text):
        start = cursor
        while cursor < len(text) and text[cursor] not in "[]":
            cursor += 1
        surface = text[start:cursor]
        if cursor < len(text) and text[cursor] == "]":
            raise ValueError("Unmatched closing annotation bracket")
        tags = []
        groups = []
        while cursor < len(text) and text[cursor] == "[":
            end = text.find("]", cursor + 1)
            if end < 0 or "[" in text[cursor + 1 : end]:
                raise ValueError("Malformed annotation bracket group")
            group = text[cursor + 1 : end]
            if not group or any(not tag for tag in group.split(":")):
                raise ValueError("Empty annotation tag")
            groups.append(group)
            tags.extend(group.split(":"))
            cursor = end + 1
        if tags and not surface.strip():
            raise ValueError("Annotation has no preceding surface occurrence")
        if surface:
            pieces.append(
                {
                    "index": len(pieces),
                    "surface": surface,
                    "tags": sorted(set(tags)),
                    "tag_groups": groups,
                    "surface_start": surface_offset,
                    "surface_end": surface_offset + len(surface),
                }
            )
            surface_offset += len(surface)
    return pieces


def _signature(pieces, exclude_legacy=False):
    return [
        (
            piece["surface"],
            tuple(
                sorted(
                    tag
                    for tag in piece["tags"]
                    if not (exclude_legacy and _DEEPEST.fullmatch(tag))
                )
            ),
        )
        for piece in pieces
    ]


def _tree_inventory(expression):
    from pydicate.predicate import Predicate
    from tupi import Noun as TupiNoun

    nodes = []
    unsupported = []
    legacy = []

    def nested_predicates(value, route=(), ancestors=frozenset()):
        """Find stored relations in containers without inspecting arbitrary objects.

        Container identity is guarded on the active path so a cycle terminates,
        while two distinct routes to a shared Predicate remain visible. Dict
        keys and values use insertion-position routes rather than calling repr
        on user objects merely to construct an evidence label.
        """
        if isinstance(value, Predicate):
            yield route, value
        elif isinstance(value, (dict, list, tuple)):
            if id(value) in ancestors:
                return
            ancestors = ancestors | {id(value)}
            if isinstance(value, dict):
                for index, (key, child) in enumerate(value.items()):
                    yield from nested_predicates(
                        key, route + (("key", index),), ancestors
                    )
                    yield from nested_predicates(
                        child, route + (("value", index),), ancestors
                    )
            else:
                for index, child in enumerate(value):
                    yield from nested_predicates(
                        child, route + (("index", index),), ancestors
                    )

    def walk_legacy(node, path, ancestors):
        if id(node) in ancestors:
            return
        legacy.append({"id": len(legacy) + 1, "path": path})
        for field in ("arguments", "pre_adjuncts", "post_adjuncts"):
            for index, child in enumerate(getattr(node, field, []) or []):
                if isinstance(child, Predicate):
                    walk_legacy(
                        child, f"{path}.{field}[{index}]", ancestors | {id(node)}
                    )

    def walk(node, path, parent, relation, ancestors):
        ancestor_path = ancestors.get(id(node))
        noun = getattr(node, "noun", None)
        lexical_base = noun.verbete(True) if isinstance(noun, TupiNoun) else None
        row = {
            "path": path,
            "parent_path": parent,
            "relation": relation,
            "type": type(node).__name__,
            "category": getattr(node, "category", None),
            "verbete": str(getattr(node, "verbete", "")),
            "nid": getattr(node, "nid", None),
            "tag": str(getattr(node, "tag", "")),
            "pro_drop": bool(getattr(node, "pro_drop", False)),
            "cycle_to": ancestor_path,
            "nominalization_operation": getattr(
                node, "_nominalization_operation", None
            ),
            "nominalization_annotated_argument": getattr(
                node, "_nominalization_annotated_argument", None
            ),
            "has_nominalization_source": isinstance(
                getattr(node, "_nominalization_source", None), Predicate
            ),
            "suppress_lexeme": bool(getattr(node, "_suppress_lexeme", False)),
            "lexical_annotated_base": lexical_base,
        }
        nodes.append(row)
        if ancestor_path:
            return
        ancestors = {**ancestors, id(node): path}
        handled = set()
        for field in LIST_RELATIONS:
            for index, child in enumerate(getattr(node, field, []) or []):
                if isinstance(child, Predicate):
                    handled.add((field, index))
                    walk(child, f"{path}.{field}[{index}]", path, field, ancestors)
        for field in NODE_RELATIONS:
            child = getattr(node, field, None)
            if isinstance(child, Predicate):
                handled.add((field, None))
                walk(child, f"{path}.{field}", path, field, ancestors)
        # A new Predicate-bearing field must not silently disappear from the report.
        for field, value in vars(node).items():
            for route, child in nested_predicates(value):
                if not route and (field, None) in handled:
                    continue
                if (
                    len(route) == 1
                    and route[0][0] == "index"
                    and (field, route[0][1]) in handled
                ):
                    continue
                unsupported.append(
                    {
                        "path": path,
                        "field": field,
                        "kind": "node" if not route else "container",
                        "container_path": "/".join(
                            f"{kind}:{index}" for kind, index in route
                        ),
                    }
                )

    walk(expression, "root", None, "root", {})
    walk_legacy(expression, "root", set())
    return nodes, legacy, unsupported


def _metrics(report):
    statuses = Counter(
        evidence["status"]
        for piece in report["pieces"]
        for evidence in piece["tag_evidence"]
    )
    events_by_nid = defaultdict(set)
    for event in report["evaluation_events"]:
        if event.get("annotated"):
            events_by_nid[event.get("nid")].add(event.get("output"))
    return {
        "piece_count": len(report["pieces"]),
        "tag_count": sum(len(piece["tags"]) for piece in report["pieces"]),
        "tree_path_count": len(report["tree"]),
        "legacy_node_count": len(report["legacy_nodes"]),
        "evaluation_event_count": len(report["evaluation_events"]),
        "cycle_count": sum(bool(node["cycle_to"]) for node in report["tree"]),
        "unsupported_relation_count": len(report["unsupported_relations"]),
        "unique_child_event_witness_tags": statuses["unique_child_event_witness"],
        "ambiguous_child_event_witness_tags": statuses["ambiguous_child_event_witness"],
        "root_output_only_tags": statuses["root_output_only"],
        "unresolved_tags": statuses["unresolved"],
        "shared_nids_with_distinct_outputs": sum(
            len(outputs) > 1 for outputs in events_by_nid.values()
        ),
        "multiword_root_piece_count": sum(
            "ROOT" in p["tags"] and len(p["surface"].split()) > 1
            for p in report["pieces"]
        ),
        "events_without_stored_node_path": sum(
            not event["tree_paths"] for event in report["evaluation_events"]
        ),
        "events_with_ambiguous_stored_node_paths": sum(
            len(event["tree_paths"]) > 1 for event in report["evaluation_events"]
        ),
        "surface_exact_match": int(report["surface"]["matches"]),
        "surface_whitespace_normalized_match": int(
            report["surface"]["matches_after_whitespace_normalization"]
        ),
    }


def _evidence_for_pieces(pieces, events):
    index = defaultdict(list)
    roots = set()
    for event in events:
        if not event.get("annotated") or "output" not in event:
            continue
        for event_piece in parse_occurrences(event["output"]):
            for tag in event_piece["tags"]:
                key = (event_piece["surface"].strip(), tag)
                if event.get("parent_event_id") is None:
                    roots.add(key)
                else:
                    index[key].append(
                        {
                            "event_id": event["event_id"],
                            "piece_index": event_piece["index"],
                        }
                    )
    for piece in pieces:
        piece["tag_evidence"] = []
        for tag in piece["tags"]:
            key = (piece["surface"].strip(), tag)
            witnesses = index[key]
            status = (
                "unique_child_event_witness"
                if len(witnesses) == 1
                else (
                    "ambiguous_child_event_witness"
                    if witnesses
                    else "root_output_only" if key in roots else "unresolved"
                )
            )
            piece["tag_evidence"].append(
                {"tag": tag, "status": status, "witnesses": witnesses}
            )


def _event_paths(events, tree):
    for event in events:
        event["tree_paths"] = [
            node["path"]
            for node in tree
            if not node["cycle_to"]
            and node["nid"] == event.get("nid")
            and node["type"] == event.get("type")
        ]
        event["tree_link_status"] = (
            "unique_stored_node_path"
            if len(event["tree_paths"]) == 1
            else (
                "ambiguous_stored_node_paths"
                if event["tree_paths"]
                else "runtime_created_or_not_stored"
            )
        )


def _constructions(tree):
    constructions = []
    for node in tree:
        if node["cycle_to"]:
            continue
        if node["category"] == "conjunction" or node["type"] == "Conjunction":
            children = [child for child in tree if child["parent_path"] == node["path"]]
            constructions.append(
                {
                    "path": node["path"],
                    "kind": "coordination",
                    "tag": node["tag"],
                    "lexeme": node["verbete"],
                    "zero_surface_lexeme": not node["verbete"].strip()
                    or node["suppress_lexeme"],
                    "scope": [
                        child["path"]
                        for child in children
                        if child["relation"] == "arguments"
                    ],
                    "adjunct_paths": [
                        child["path"]
                        for child in children
                        if child["relation"]
                        in (
                            "pre_adjuncts",
                            "post_adjuncts",
                            "v_adjuncts",
                            "v_adjuncts_pre",
                        )
                    ],
                }
            )
        if node["nominalization_operation"]:
            constructions.append(
                {
                    "path": node["path"],
                    "kind": "nominalization",
                    "operation": node["nominalization_operation"],
                    "annotated_argument": node["nominalization_annotated_argument"],
                    "source_path": node["path"] + "._nominalization_source",
                }
            )
    return constructions


def _opaque_lexical_root(surface, source_path, tree):
    """An unchanged stored lexical multiword base is not lost construction detail.

    E.g. Santa Madre Igreja is itself entered as one noun. No guess about its
    morphology or proper-name status is needed: its actual low-level base
    contains the identical annotated root before the surrounding nominalization.
    """
    for node in tree:
        if not node["path"].startswith(source_path + "."):
            continue
        if node["nominalization_operation"] or node["category"] not in (
            "noun",
            "proper_noun",
        ):
            continue
        if any(
            child["parent_path"] == node["path"] and child["relation"] != "principal"
            for child in tree
        ):
            continue
        for piece in parse_occurrences(node["lexical_annotated_base"] or ""):
            if "ROOT" in piece["tags"] and piece["surface"].strip() == surface.strip():
                return True
    return False


def validate_audit_report(report):
    """Recompute integrity from detailed evidence, including tampered reports.

    Returns errors instead of treating missing detail or invented coverage totals
    as success. It does not judge the correctness of an original grammar rule.
    """
    errors = []
    if report.get("schema_version") != SCHEMA_VERSION:
        return ["unsupported_schema"]
    try:
        raw = parse_occurrences(report["surface"]["annotated"])
        emitted = report["emitted_pieces"]
        hierarchy = parse_occurrences(report["hierarchy_annotated"])
        if _signature(raw) != _signature(emitted):
            errors.append("emit_occurrence_mismatch")
        if _signature(raw) != _signature(hierarchy, exclude_legacy=True):
            errors.append("hierarchy_occurrence_mismatch")
        if _signature(raw) != _signature(report["pieces"]):
            errors.append("reported_piece_mismatch")
        if any(
            (left["surface_start"], left["surface_end"])
            != (right["surface_start"], right["surface_end"])
            for left, right in zip(raw, report["pieces"])
        ):
            errors.append("piece_offset_mismatch")
        reconstructed = "".join(piece["surface"] for piece in raw)
        if reconstructed != report["surface"]["annotated_surface"]:
            errors.append("reconstruction_mismatch")
        if (reconstructed == report["surface"]["ordinary"]) != report["surface"][
            "matches"
        ]:
            errors.append("surface_match_metric_mismatch")
        normalized_match = " ".join(reconstructed.split()) == " ".join(
            report["surface"]["ordinary"].split()
        )
        if (
            normalized_match
            != report["surface"]["matches_after_whitespace_normalization"]
        ):
            errors.append("normalized_surface_match_metric_mismatch")
        paths = {node["path"] for node in report["tree"]}
        if len(paths) != len(report["tree"]) or "root" not in paths:
            errors.append("tree_path_identity")
        for node in report["tree"]:
            if node["parent_path"] is not None and node["parent_path"] not in paths:
                errors.append("tree_parent_missing")
            if node["cycle_to"] is not None:
                if node["cycle_to"] not in paths or not node["path"].startswith(
                    node["cycle_to"] + "."
                ):
                    errors.append("tree_cycle_target_missing")
            if node["nominalization_operation"] and not node["cycle_to"]:
                if (
                    not node["has_nominalization_source"]
                    or node["path"] + "._nominalization_source" not in paths
                ):
                    errors.append("nominalization_source_missing")
            if node["nominalization_operation"] and node["category"] != "proper_noun":
                if any(
                    "ROOT" in p["tags"]
                    and len(p["surface"].split()) > 1
                    and not _opaque_lexical_root(
                        p["surface"],
                        node["path"] + "._nominalization_source",
                        report["tree"],
                    )
                    for p in parse_occurrences(node["verbete"])
                ):
                    errors.append("flattened_nominalization_root")
        if _constructions(report["tree"]) != report["constructions"]:
            errors.append("construction_scope_mismatch")
        legacy = {node["id"] for node in report["legacy_nodes"]}
        if len(legacy) != len(report["legacy_nodes"]) or any(
            node["path"] not in paths for node in report["legacy_nodes"]
        ):
            errors.append("legacy_tree_identity")
        for piece in hierarchy:
            ids = [
                int(match.group(1))
                for tag in piece["tags"]
                if (match := _DEEPEST.fullmatch(tag))
            ]
            if len(ids) != 1 or any(node_id not in legacy for node_id in ids):
                errors.append("legacy_node_reference")
        for piece in raw:
            if "CONJUNCTION" in piece["tags"] and "SUBSTANTIVE_SUFFIX" in piece["tags"]:
                errors.append("conjunction_on_substantive_suffix")
        events = report["evaluation_events"]
        event_ids = {event["event_id"] for event in events}
        if not events:
            errors.append("missing_evaluation_trace")
        elif len(event_ids) != len(events):
            errors.append("duplicate_evaluation_event")
        if not any(
            event.get("parent_event_id") is None
            and event.get("annotated")
            and event.get("output") == report["surface"]["annotated"]
            for event in events
        ):
            errors.append("missing_root_evaluation_witness")
        for event in events:
            parent = event.get("parent_event_id")
            if parent is not None and (
                parent not in event_ids or parent >= event["event_id"]
            ):
                errors.append("evaluation_event_parent")
            if event.get("error") or "output" not in event:
                errors.append("incomplete_evaluation_event")
        recomputed_events = [dict(event) for event in events]
        _event_paths(recomputed_events, report["tree"])
        if [(e["tree_paths"], e["tree_link_status"]) for e in recomputed_events] != [
            (e["tree_paths"], e["tree_link_status"]) for e in events
        ]:
            errors.append("event_tree_path_mismatch")
        recomputed = [
            {"index": p["index"], "surface": p["surface"], "tags": p["tags"]}
            for p in raw
        ]
        _evidence_for_pieces(recomputed, events)
        if [p["tag_evidence"] for p in recomputed] != [
            p["tag_evidence"] for p in report["pieces"]
        ]:
            errors.append("tag_witness_mismatch")
        if report["unsupported_relations"]:
            errors.append("unsupported_predicate_relation")
        if _metrics(report) != report["metrics"]:
            errors.append("metric_mismatch")
    except (KeyError, TypeError, ValueError, IndexError) as error:
        errors.append("malformed_report:" + type(error).__name__ + ":" + str(error))
    return sorted(set(errors))


def audit_annotation(expression):
    """Produce a JSON-serializable accountability report from actual evaluation."""
    from pydicate.predicate import EvalCtx

    report = {
        "schema_version": SCHEMA_VERSION,
        "passed": False,
        "scope": "Annotation transport and stored structure; not linguistic adjudication or proven morpheme authorship.",
        "legacy_scope": "DEEPEST_NODE is a heuristic partial-tree alignment, not tag provenance.",
        "witness_scope": "Exact surface/tag occurrences observed in child evaluations; repeated candidates remain ambiguous. Root-only evidence is not independent origin coverage.",
        "hard_failures": [],
    }
    try:
        tree, legacy, unsupported = _tree_inventory(expression)
        ctx = EvalCtx()
        annotated = expression.eval(annotated=True, ctx=ctx)
        ordinary = expression.eval(annotated=False)
        pieces = parse_occurrences(annotated)
        reconstructed = "".join(piece["surface"] for piece in pieces)
        hierarchy_annotated = expression.hierarchical_representation_v4()
        emitted = [
            {"index": index, "surface": surface, "tags": sorted(set(tags))}
            for index, (surface, tags) in enumerate(expression.emit())
        ]
        events = [dict(event) for event in ctx.events]
        _event_paths(events, tree)
        _evidence_for_pieces(pieces, events)
        constructions = _constructions(tree)
        report.update(
            {
                "surface": {
                    "ordinary": ordinary,
                    "annotated": annotated,
                    "annotated_surface": reconstructed,
                    "matches": ordinary == reconstructed,
                    "matches_after_whitespace_normalization": " ".join(ordinary.split())
                    == " ".join(reconstructed.split()),
                },
                "pieces": pieces,
                "emitted_pieces": emitted,
                "hierarchy_annotated": hierarchy_annotated,
                "tree": tree,
                "legacy_nodes": legacy,
                "unsupported_relations": unsupported,
                "evaluation_events": events,
                "constructions": constructions,
            }
        )
        report["metrics"] = _metrics(report)
        report["hard_failures"] = validate_audit_report(report)
    except Exception as error:
        report["hard_failures"] = [
            "audit_error:" + type(error).__name__ + ":" + str(error)
        ]
    report["passed"] = not report["hard_failures"]
    return report
