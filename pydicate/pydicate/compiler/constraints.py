from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class TagConstraint:
    kind: str
    allowed_pos: Tuple[str, ...] = ()
    implies_morph: Tuple[str, ...] = ()


DEFAULT_CONSTRAINTS: Dict[str, TagConstraint] = {
    "VERB": TagConstraint("VERB", allowed_pos=("Verb",)),
    "NOUN": TagConstraint("NOUN", allowed_pos=("Noun",)),
    # "NNOUN": TagConstraint("NNOUN", allowed_pos=("Noun",)),
    "PROPER_NOUN": TagConstraint("PROPER_NOUN", allowed_pos=("ProperNoun",)),
    "PRONOUN": TagConstraint("PRONOUN", allowed_pos=("Pronoun",)),
    "POSSESSIVE_PRONOUN": TagConstraint("POSSESSIVE_PRONOUN", allowed_pos=("Pronoun",)),
    "PATIENT_PREFIX": TagConstraint("PATIENT_PREFIX", allowed_pos=("Pronoun",)),
    "SUBJECT_PREFIX": TagConstraint("SUBJECT_PREFIX", allowed_pos=("Pronoun",)),
    "OBJECT_PREFIX": TagConstraint("OBJECT_PREFIX", allowed_pos=("Pronoun",)),
    "OBJECT_MARKER": TagConstraint("OBJECT_MARKER", allowed_pos=("Pronoun",)),
    "GERUND_SUBJECT_PREFIX": TagConstraint(
        "GERUND_SUBJECT_PREFIX", allowed_pos=("Pronoun",)
    ),
    "SUBJECT": TagConstraint("SUBJECT", allowed_pos=("Pronoun",)),
    "OBJECT": TagConstraint("OBJECT", allowed_pos=("Pronoun",)),
    "POSTPOSITION": TagConstraint("POSTPOSITION", allowed_pos=("Postposition",)),
    "ADVERB": TagConstraint("ADVERB", allowed_pos=("Adverb",)),
    "PARTICLE": TagConstraint("PARTICLE", allowed_pos=("Particle",)),
    "INTERJECTION": TagConstraint("INTERJECTION", allowed_pos=("Interjection",)),
    "CONJUNCTION": TagConstraint("CONJUNCTION", allowed_pos=("Conjunction",)),
    "NUMBER": TagConstraint("NUMBER", allowed_pos=("Number",)),
    "COPULA": TagConstraint("COPULA", allowed_pos=("Copula",)),
    "SUBSTANTIVE_SUFFIX": TagConstraint(
        "SUBSTANTIVE_SUFFIX", allowed_pos=("Noun", "Deverbal", "Deadverbal")
    ),
    "DEVERBAL": TagConstraint("DEVERBAL", allowed_pos=("Deverbal",)),
    "DEADVERBAL": TagConstraint("DEADVERBAL", allowed_pos=("Deadverbal",)),
    "VOCATIVE": TagConstraint(
        "VOCATIVE",
        allowed_pos=("Noun", "ProperNoun", "Pronoun", "Deverbal", "Deadverbal"),
        implies_morph=("VOC",),
    ),
    "IMPERATIVE_PREFIX": TagConstraint("IMPERATIVE_PREFIX", implies_morph=("IMP",)),
    "PERMISSIVE_PREFIX": TagConstraint("PERMISSIVE_PREFIX", implies_morph=("PERM",)),
    "CIRCUMSTANTIAL": TagConstraint("CIRCUMSTANTIAL", implies_morph=("CIRC",)),
    "REDUPLICATION": TagConstraint("REDUPLICATION", implies_morph=("REDUP",)),
    "NEGATION_PARTICLE": TagConstraint("NEGATION_PARTICLE", implies_morph=("NEG",)),
    "NEGATION_SUFFIX": TagConstraint("NEGATION_SUFFIX", implies_morph=("NEG",)),
    "FACILITY_SUFFIX": TagConstraint("FACILITY_SUFFIX", allowed_pos=("Verb",)),
    "ABSOLUTE_AGENT_SUFFIX": TagConstraint(
        "ABSOLUTE_AGENT_SUFFIX", allowed_pos=("Verb",)
    ),
    "ACTIVE_AGENT_SUFFIX": TagConstraint("ACTIVE_AGENT_SUFFIX", allowed_pos=("Verb",)),
    "AGENTLESS_PATIENT_SUFFIX": TagConstraint(
        "AGENTLESS_PATIENT_SUFFIX", allowed_pos=("Verb",)
    ),
}


def resolve_constraints(
    tag_kinds: Iterable[str],
    constraints: Optional[Dict[str, TagConstraint]] = None,
) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    constraints = constraints or DEFAULT_CONSTRAINTS
    allowed_pos: List[str] = []
    morph_ops: List[str] = []
    for kind in tag_kinds:
        constraint = constraints.get(kind)
        if not constraint:
            continue
        allowed_pos.extend(list(constraint.allowed_pos))
        morph_ops.extend(list(constraint.implies_morph))
    return tuple(dict.fromkeys(allowed_pos)), tuple(dict.fromkeys(morph_ops))
