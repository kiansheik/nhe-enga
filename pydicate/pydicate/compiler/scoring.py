from __future__ import annotations

from typing import Iterable, Sequence

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
    ) -> None:
        self.size_weight = size_weight
        self.morph_penalty = morph_penalty
        self.fallback_penalty = fallback_penalty
        self.fallback_pos = set(fallback_pos)

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
        return total
