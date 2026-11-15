"""Knowledge layer seen by the meal check: dish resolution, components, Rule Cards, alternatives.

The in-memory implementation loads approved seeds (the same MemoryGraph the foodgraph MCP
uses offline). A Neo4j adapter can implement the same protocol later (spec 002 T019).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from happygut_engine import DishEvidence, RuleCard
from happygut_pipelines.graph import MemoryGraph, RuleRef

MIN_RESOLUTION_SCORE = 0.45


@dataclass(frozen=True)
class Resolution:
    dish_id: str
    name_en: str
    name_bn: str
    matched_name: str
    score: float


class Knowledge(Protocol):
    reviewed_only: bool

    def resolve(self, *names: str) -> Resolution | None: ...
    def evidence(self, dish_id: str, perception_confidence: float, resolution_confidence: float) -> DishEvidence: ...
    def names(self, dish_id: str) -> tuple[str, str]: ...
    def rules(self) -> list[RuleCard]: ...
    def rule_ref(self, rule_id: str) -> RuleRef: ...
    def alternatives_pool(self) -> dict[str, DishEvidence]: ...
    def counts(self) -> dict[str, int]: ...
    def all_names(self) -> list[str]: ...


class MemoryKnowledge:
    def __init__(self, graph: MemoryGraph, reviewed_only: bool):
        self.graph = graph
        self.reviewed_only = reviewed_only
        self._refs = {r.ref.id: r.ref for r in graph.rules}
        self._pool = {d.id: d.to_evidence() for d in graph.dishes.values()}

    @classmethod
    def from_seeds(cls, seeds_dir: Path, include_drafts: bool = False) -> "MemoryKnowledge":
        graph = MemoryGraph.from_seeds(seeds_dir, include_drafts=include_drafts)
        # "Reviewed only" describes what was actually loaded, not the flag: no draft dish and no draft Rule Card.
        drafts = any(d.status != "approved" for d in graph.dishes.values()) or any(r.ref.status != "approved" for r in graph.rules)
        return cls(graph, reviewed_only=not drafts)

    def resolve(self, *names: str) -> Resolution | None:
        best = None
        for name in names:
            if not name or not name.strip():
                continue
            for m in self.graph.search_dish(name, limit=1):
                if best is None or m.score > best.score:
                    best = m
        if best is None or best.score < MIN_RESOLUTION_SCORE:
            return None
        return Resolution(best.dish_id, best.name_en, best.name_bn, best.matched_name, best.score)

    def evidence(self, dish_id: str, perception_confidence: float, resolution_confidence: float) -> DishEvidence:
        return self.graph.dishes[dish_id].to_evidence(perception_confidence, resolution_confidence)

    def names(self, dish_id: str) -> tuple[str, str]:
        d = self.graph.dishes[dish_id]
        return d.name_en, d.name_bn

    def rules(self) -> list[RuleCard]:
        return self.graph.engine_rules()

    def rule_ref(self, rule_id: str) -> RuleRef:
        return self._refs[rule_id]

    def alternatives_pool(self) -> dict[str, DishEvidence]:
        return self._pool

    def counts(self) -> dict[str, int]:
        return {"dishes": len(self.graph.dishes), "rule_cards": len(self.graph.rules)}

    def all_names(self) -> list[str]:
        """Every dish name and alias (used to stop the PII models from scrubbing dish names)."""
        return [n for d in self.graph.dishes.values() for n in (d.name_en, d.name_bn, *d.aliases)]
