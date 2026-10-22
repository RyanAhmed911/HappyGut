"""Food knowledge graph: model, Neo4j statements and an in-memory twin.

Graph model (Neo4j):
    (:Dish)-[:HAS_COMPONENT {level}]->(:Component)
    (:Dish)-[:CONTAINS]->(:Ingredient)
    (:Dish)-[:GENTLER_ALTERNATIVE]->(:Dish)
    (:RuleCard)-[:ABOUT {min_level}]->(:Component)
    (:RuleCard)-[:CITES]->(:Source)
    (:Patient)-[:REACTS_TO {p, n, ci_low, ci_high}]->(:Component)   (written by Trigger Discovery)

Component levels are dish-level estimates from the seeds; ingredient-level composition is added
when Food Composition Table data is loaded. The in-memory graph answers the same questions as the
Neo4j queries, so the MCP server and tests work without a database.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from happygut_engine import Component, DiseaseState, Diagnosis, Level, Profile, RuleCard

from .seeds import DEFAULT_SEEDS, DishSeed, _read, load_dishes


def normalise_name(text: str) -> str:
    text = unicodedata.normalize("NFC", text).lower().strip()
    return re.sub(r"\s+", " ", text)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


# ---------------------------------------------------------------- name matching (pg_trgm-style)

def _trigrams(text: str) -> set[str]:
    grams: set[str] = set()
    for word in normalise_name(text).split(" "):
        if not word:
            continue
        padded = f"  {word} "
        grams.update(padded[i : i + 3] for i in range(len(padded) - 2))
    return grams


def similarity(a: str, b: str) -> float:
    ta, tb = _trigrams(a), _trigrams(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def name_score(name: str, query: str) -> float:
    """Best of whole-string similarity and similarity against any same-length word window."""
    name_n, query_n = normalise_name(name), normalise_name(query)
    if name_n == query_n:
        return 1.0
    best = similarity(name_n, query_n)
    words, width = query_n.split(" "), len(name_n.split(" "))
    for i in range(max(1, len(words) - width + 1)):
        best = max(best, similarity(name_n, " ".join(words[i : i + width])))
    return best


# ---------------------------------------------------------------- results

@dataclass(frozen=True)
class DishMatch:
    dish_id: str
    name_en: str
    name_bn: str
    matched_name: str
    score: float


@dataclass(frozen=True)
class SourceRef:
    key: str
    citation: str
    doi: str
    pmid: str
    licence: str
    quote: str


@dataclass(frozen=True)
class RuleRef:
    id: str
    title_en: str
    title_bn: str
    recommendation_en: str
    recommendation_bn: str
    severity: int
    hard: bool
    evidence_level: str
    status: str
    sources: tuple[SourceRef, ...]


@dataclass(frozen=True)
class VerdictPathStep:
    """One dish → component → rule → sources path that applies to a profile."""

    component: str
    level: str
    rule: RuleRef


@dataclass
class RuleSeedFull:
    rule: RuleCard
    ref: RuleRef


# ---------------------------------------------------------------- in-memory graph

@dataclass
class MemoryGraph:
    dishes: dict[str, DishSeed] = field(default_factory=dict)
    rules: list[RuleSeedFull] = field(default_factory=list)

    @classmethod
    def from_seeds(cls, seeds: Path = DEFAULT_SEEDS, include_drafts: bool = False) -> "MemoryGraph":
        rules = []
        for path in sorted((seeds / "rule_cards").glob("*.yaml")):
            raw = _read(path)
            if not include_drafts and raw.get("status") != "approved":
                continue
            rules.append(_rule_full(raw))
        return cls(dishes=load_dishes(seeds, include_drafts=include_drafts), rules=rules)

    def search_dish(self, query: str, limit: int = 5, threshold: float = 0.3) -> list[DishMatch]:
        matches = []
        for dish in self.dishes.values():
            names = [dish.name_en, dish.name_bn, *dish.aliases]
            score, name = max((name_score(n, query), n) for n in names)
            if score >= threshold:
                matches.append(DishMatch(dish.id, dish.name_en, dish.name_bn, name, round(score, 3)))
        matches.sort(key=lambda m: (-m.score, m.dish_id))
        return matches[:limit]

    def get_components(self, dish_id: str) -> dict:
        dish = self.dishes[dish_id]
        raw = dish.raw
        return {
            "dish_id": dish.id,
            "name_en": dish.name_en,
            "name_bn": dish.name_bn,
            "status": dish.status,
            "level_basis": raw.get("level_basis", ""),
            "components": {c.value: (lvl.name.lower() if lvl is not None else "unknown")
                           for c, lvl in sorted(dish.components.items(), key=lambda kv: kv[0].value)},
            "ingredients": [i.get("name") for i in raw.get("ingredients") or []],
            "gentler_alternatives": list(dish.gentler_alternatives),
            "sources": raw.get("sources") or [],
        }

    def explain_verdict_path(self, dish_id: str, profile: Profile) -> list[VerdictPathStep]:
        """Every dish → component → Rule Card → source path that applies to this profile."""
        dish = self.dishes[dish_id]
        steps = []
        for component, level in sorted(dish.components.items(), key=lambda kv: kv[0].value):
            for r in self.rules:
                if r.rule.applies(profile, component, level):
                    steps.append(VerdictPathStep(component.value, level.name.lower(), r.ref))
        steps.sort(key=lambda s: (not s.rule.hard, -s.rule.severity, s.component, s.rule.id))
        return steps

    def engine_rules(self) -> list[RuleCard]:
        return [r.rule for r in self.rules]


def _rule_full(raw: dict) -> RuleSeedFull:
    from .seeds import _rule

    seed = _rule(raw)
    sources = tuple(
        SourceRef(
            key=s.get("key", ""), citation=s.get("citation", ""), doi=s.get("doi", ""),
            pmid=s.get("pmid", ""), licence=s.get("licence", ""), quote=s.get("quote", ""),
        )
        for s in raw.get("sources") or []
    )
    ref = RuleRef(
        id=raw["id"], title_en=raw["title_en"], title_bn=raw["title_bn"],
        recommendation_en=raw["recommendation_en"], recommendation_bn=raw["recommendation_bn"],
        severity=int(raw["severity"]), hard=bool(raw.get("hard", False)),
        evidence_level=raw.get("evidence_level", ""), status=raw.get("status", "draft"), sources=sources,
    )
    return RuleSeedFull(rule=seed.rule, ref=ref)


# ---------------------------------------------------------------- Neo4j statements

CONSTRAINTS = [
    "CREATE CONSTRAINT dish_id IF NOT EXISTS FOR (d:Dish) REQUIRE d.id IS UNIQUE",
    "CREATE CONSTRAINT ingredient_id IF NOT EXISTS FOR (i:Ingredient) REQUIRE i.id IS UNIQUE",
    "CREATE CONSTRAINT component_id IF NOT EXISTS FOR (c:Component) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT rule_card_id IF NOT EXISTS FOR (r:RuleCard) REQUIRE r.id IS UNIQUE",
    "CREATE CONSTRAINT source_key IF NOT EXISTS FOR (s:Source) REQUIRE s.key IS UNIQUE",
    "CREATE CONSTRAINT patient_id IF NOT EXISTS FOR (p:Patient) REQUIRE p.id IS UNIQUE",
    "CREATE FULLTEXT INDEX dish_names IF NOT EXISTS FOR (d:Dish) ON EACH [d.name_en, d.name_bn, d.aliases_text]",
]

UPSERT_COMPONENTS = "UNWIND $rows AS row MERGE (c:Component {id: row.id})"

UPSERT_DISHES = """
UNWIND $rows AS row
MERGE (d:Dish {id: row.id})
SET d.name_en = row.name_en, d.name_bn = row.name_bn, d.aliases = row.aliases,
    d.aliases_text = row.aliases_text, d.category = row.category, d.status = row.status,
    d.level_basis = row.level_basis
WITH d, row
OPTIONAL MATCH (d)-[old:HAS_COMPONENT|CONTAINS|GENTLER_ALTERNATIVE]->()
DELETE old
WITH DISTINCT d, row
FOREACH (comp IN row.components |
  MERGE (c:Component {id: comp.id})
  MERGE (d)-[:HAS_COMPONENT {level: comp.level}]->(c))
FOREACH (ing IN row.ingredients |
  MERGE (i:Ingredient {id: ing.id}) SET i.name = ing.name
  MERGE (d)-[:CONTAINS]->(i))
"""

LINK_ALTERNATIVES = """
UNWIND $rows AS row
MATCH (d:Dish {id: row.id})
UNWIND row.alternatives AS alt_id
MATCH (a:Dish {id: alt_id})
MERGE (d)-[:GENTLER_ALTERNATIVE]->(a)
"""

UPSERT_RULES = """
UNWIND $rows AS row
MERGE (r:RuleCard {id: row.id})
SET r += row.props
WITH r, row
OPTIONAL MATCH (r)-[old:ABOUT|CITES]->()
DELETE old
WITH DISTINCT r, row
MERGE (c:Component {id: row.component})
MERGE (r)-[:ABOUT {min_level: row.min_level}]->(c)
FOREACH (src IN row.sources |
  MERGE (s:Source {key: src.key}) SET s += src
  MERGE (r)-[:CITES]->(s))
"""

DELETE_MISSING = """
MATCH (n) WHERE (n:Dish OR n:RuleCard) AND NOT n.id IN $keep_ids
DETACH DELETE n
"""


def graph_statements(graph: MemoryGraph) -> list[tuple[str, dict]]:
    """Idempotent Cypher statements that make Neo4j match the given (approved) knowledge."""
    dishes = list(graph.dishes.values())
    dish_rows = [
        {
            "id": d.id,
            "name_en": d.name_en,
            "name_bn": d.name_bn,
            "aliases": list(d.aliases),
            "aliases_text": " ".join(d.aliases),
            "category": d.raw.get("category", ""),
            "status": d.status,
            "level_basis": d.raw.get("level_basis", ""),
            "components": [
                {"id": c.value, "level": lvl.name.lower() if lvl is not None else "unknown"}
                for c, lvl in sorted(d.components.items(), key=lambda kv: kv[0].value)
                if lvl is None or lvl > Level.NONE
            ],
            "ingredients": [
                {"id": f"ing.{_slug(i['name'])}", "name": i["name"]}
                for i in d.raw.get("ingredients") or [] if i.get("name")
            ],
            "alternatives": list(d.gentler_alternatives),
        }
        for d in dishes
    ]
    rule_rows = [
        {
            "id": r.ref.id,
            "component": r.rule.component.value,
            "min_level": r.rule.min_level.name.lower(),
            "props": {
                "title_en": r.ref.title_en, "title_bn": r.ref.title_bn,
                "recommendation_en": r.ref.recommendation_en, "recommendation_bn": r.ref.recommendation_bn,
                "severity": r.ref.severity, "hard": r.ref.hard, "evidence_level": r.ref.evidence_level,
                "status": r.ref.status,
                "diagnoses": sorted(d.value for d in r.rule.diagnoses),
                "phenotypes": sorted(r.rule.phenotypes),
                "states": sorted(s.value for s in r.rule.states),
            },
            "sources": [
                {"key": s.key, "citation": s.citation, "doi": s.doi, "pmid": s.pmid,
                 "licence": s.licence, "quote": s.quote}
                for s in r.ref.sources
            ],
        }
        for r in graph.rules
    ]
    statements: list[tuple[str, dict]] = [(c, {}) for c in CONSTRAINTS]
    statements.append((UPSERT_COMPONENTS, {"rows": [{"id": c.value} for c in Component]}))
    statements.append((UPSERT_DISHES, {"rows": dish_rows}))
    statements.append((LINK_ALTERNATIVES, {"rows": dish_rows}))
    statements.append((UPSERT_RULES, {"rows": rule_rows}))
    statements.append((DELETE_MISSING, {"keep_ids": [d["id"] for d in dish_rows] + [r["id"] for r in rule_rows]}))
    return statements


def profile_from(diagnosis: str, state: str, phenotypes: Iterable[str] = ()) -> Profile:
    return Profile(Diagnosis(diagnosis), DiseaseState(state), frozenset(phenotypes))
