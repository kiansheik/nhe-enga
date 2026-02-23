from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple, Union

from .tokens import Token


@dataclass(frozen=True)
class TagConstraint:
    kind: str
    allowed_pos: Tuple[str, ...] = ()
    implies_morph: Tuple[str, ...] = ()
    required_values: Tuple[str, ...] = ()
    disallowed_values: Tuple[str, ...] = ()


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
    "CAUSATIVE_PREFIX": TagConstraint("CAUSATIVE_PREFIX", allowed_pos=("Verb",)),
    "FACILITY_SUFFIX": TagConstraint("FACILITY_SUFFIX", allowed_pos=("Verb",)),
    "ABSOLUTE_AGENT_SUFFIX": TagConstraint(
        "ABSOLUTE_AGENT_SUFFIX", allowed_pos=("Deverbal",)
    ),
    "ACTIVE_AGENT_SUFFIX": TagConstraint(
        "ACTIVE_AGENT_SUFFIX", allowed_pos=("Deverbal",)
    ),
    "AGENTLESS_PATIENT_SUFFIX": TagConstraint(
        "AGENTLESS_PATIENT_SUFFIX", allowed_pos=("Deverbal",)
    ),
}


ConstraintMap = Dict[str, Union[TagConstraint, Iterable[TagConstraint]]]


def _iter_constraints(
    constraint: Union[TagConstraint, Iterable[TagConstraint]],
) -> Iterable[TagConstraint]:
    if isinstance(constraint, TagConstraint):
        yield constraint
    else:
        for item in constraint:
            if isinstance(item, TagConstraint):
                yield item


def _constraint_matches(constraint: TagConstraint, *, values: Tuple[str, ...]) -> bool:
    if constraint.required_values:
        for value in constraint.required_values:
            if value not in values:
                return False
    if constraint.disallowed_values:
        for value in constraint.disallowed_values:
            if value in values:
                return False
    return True


def resolve_constraints(
    tag_kinds: Iterable[str],
    constraints: Optional[ConstraintMap] = None,
    *,
    token: Optional[Token] = None,
) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    constraints = constraints or DEFAULT_CONSTRAINTS
    allowed_pos: List[str] = []
    morph_ops: List[str] = []

    tag_features = token.tag_features if token else {}
    full_tags = token.tags if token else ()

    for kind in tag_kinds:
        constraint = constraints.get(kind)
        if not constraint:
            continue
        values = tag_features.get(kind, ())
        for rule in _iter_constraints(constraint):
            if not _constraint_matches(rule, values=values):
                continue
            allowed_pos.extend(list(rule.allowed_pos))
            morph_ops.extend(list(rule.implies_morph))

    for tag in full_tags:
        constraint = constraints.get(tag)
        if not constraint:
            continue
        for rule in _iter_constraints(constraint):
            allowed_pos.extend(list(rule.allowed_pos))
            morph_ops.extend(list(rule.implies_morph))

    # Suffix-only tags should dominate POS selection.
    suffix_only_kinds = {
        "ABSOLUTE_AGENT_SUFFIX",
        "ACTIVE_AGENT_SUFFIX",
        "AGENTLESS_PATIENT_SUFFIX",
    }
    if any(kind in tag_kinds for kind in suffix_only_kinds):
        if "Deverbal" in allowed_pos:
            allowed_pos = ["Deverbal"]

    return tuple(dict.fromkeys(allowed_pos)), tuple(dict.fromkeys(morph_ops))
