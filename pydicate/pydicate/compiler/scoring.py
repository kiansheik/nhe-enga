from __future__ import annotations

import math
from typing import Dict, Iterable, Optional, Sequence, Tuple

from .ir import IRKind, IRNode


class Scorer:
    def cost(self, node: IRNode) -> float:
        raise NotImplementedError


class DefaultScorer(Scorer):
    def __init__(
        self,
        size_weight: float = 1.0,
        morph_penalty: float = 0.5,
        fallback_penalty: float = 4.0,
        fallback_pos: Sequence[str] = ("Predicate", "Tok", "Unknown"),
        attachment_priors: Optional[Dict[str, Dict[str, float]]] = None,
        attachment_weight: float = 1.0,
    ) -> None:
        self.size_weight = size_weight
        self.morph_penalty = morph_penalty
        self.fallback_penalty = fallback_penalty
        self.fallback_pos = set(fallback_pos)
        self.attachment_priors = attachment_priors or {}
        self.attachment_weight = attachment_weight

    def _node_tag_kinds(self, node: IRNode) -> Tuple[str, ...]:
        token = None
        if node.kind == IRKind.ATOM:
            token = node.attrs.get("token")
        if not token:
            return ()
        return token.tag_kinds

    def _node_tag_values(self, node: IRNode, kind: str) -> Tuple[str, ...]:
        token = None
        if node.kind == IRKind.ATOM:
            token = node.attrs.get("token")
        if not token:
            return ()
        return token.tag_features.get(kind, ())

    def _contains_verbish(self, node: IRNode) -> bool:
        for n in node.walk():
            if n.kind == IRKind.ATOM:
                if n.name == "Verb":
                    return True
                token = n.attrs.get("token")
                if token and "VERB" in token.tag_kinds:
                    return True
        return False

    def _is_subject_marker(self, node: IRNode) -> bool:
        kinds = self._node_tag_kinds(node)
        return any(
            k in kinds for k in ("SUBJECT", "SUBJECT_PREFIX", "GERUND_SUBJECT_PREFIX")
        )

    def _is_object_marker(self, node: IRNode) -> bool:
        kinds = self._node_tag_kinds(node)
        return any(
            k in kinds
            for k in ("OBJECT", "OBJECT_PREFIX", "OBJECT_MARKER", "PATIENT_PREFIX")
        )

    def _is_postposition(self, node: IRNode) -> bool:
        if node.kind == IRKind.ATOM and node.name == "Postposition":
            return True
        return "POSTPOSITION" in self._node_tag_kinds(node)

    def _prior_penalty(self, key: str, direction: str) -> float:
        dist = self.attachment_priors.get(key, {})
        prob = dist.get(direction)
        if prob is None:
            return 0.0
        prob = max(prob, 1e-9)
        return -math.log(prob) * self.attachment_weight

    def _node_cost(self, node: IRNode) -> float:
        cost = self.size_weight
        if node.kind == IRKind.MORPH:
            cost += self.morph_penalty
        if node.kind == IRKind.ATOM and node.name in self.fallback_pos:
            cost += self.fallback_penalty
        return cost

    def cost(self, node: IRNode) -> float:
        total = 0.0
        for n in node.walk():
            total += self._node_cost(n)
            if (
                self.attachment_priors
                and n.kind == IRKind.OP
                and n.name == "MUL"
                and len(n.children) == 2
            ):
                left, right = n.children
                if self._is_subject_marker(left) and self._contains_verbish(right):
                    total += self._prior_penalty("subject", "left")
                    for val in self._node_tag_values(left, "SUBJECT"):
                        total += self._prior_penalty(f"subject:{val}", "left")
                elif self._is_subject_marker(right) and self._contains_verbish(left):
                    total += self._prior_penalty("subject", "right")
                    for val in self._node_tag_values(right, "SUBJECT"):
                        total += self._prior_penalty(f"subject:{val}", "right")
                if self._is_object_marker(left) and self._contains_verbish(right):
                    total += self._prior_penalty("object", "left")
                    for val in self._node_tag_values(left, "OBJECT"):
                        total += self._prior_penalty(f"object:{val}", "left")
                elif self._is_object_marker(right) and self._contains_verbish(left):
                    total += self._prior_penalty("object", "right")
                    for val in self._node_tag_values(right, "OBJECT"):
                        total += self._prior_penalty(f"object:{val}", "right")
                if self._is_postposition(left):
                    total += self._prior_penalty("postposition", "left")
                elif self._is_postposition(right):
                    total += self._prior_penalty("postposition", "right")
        return total
