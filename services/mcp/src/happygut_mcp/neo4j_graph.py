"""Neo4j backend for the foodgraph server: same answers as MemoryGraph, read from Neo4j.

Rule applicability is still decided by the engine's RuleCard.applies, so the rules logic exists in
one place. Read-only: every query runs in a read transaction.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from happygut_engine import Component, DiseaseState, Diagnosis, Level, Profile, RuleCard
from happygut_pipelines.graph import (
    DishMatch,
    RuleRef,
    SourceRef,
    VerdictPathStep,
    name_score,
    normalise_name,
)

ALL_DISHES = """
MATCH (d:Dish) WHERE $include_drafts OR d.status = 'approved'
RETURN d.id AS id, d.name_en AS name_en, d.name_bn AS name_bn, coalesce(d.aliases, []) AS aliases
"""

DISH_DETAIL = """
MATCH (d:Dish {id: $id}) WHERE $include_drafts OR d.status = 'approved'
OPTIONAL MATCH (d)-[h:HAS_COMPONENT]->(c:Component)
WITH d, collect({id: c.id, level: h.level}) AS comps
OPTIONAL MATCH (d)-[:CONTAINS]->(i:Ingredient)
WITH d, comps, collect(i.name) AS ingredients
OPTIONAL MATCH (d)-[:GENTLER_ALTERNATIVE]->(a:Dish)
RETURN d {.*} AS dish, comps, ingredients, collect(a.id) AS alternatives
"""

DISH_RULE_PATHS = """
MATCH (d:Dish {id: $id})-[h:HAS_COMPONENT]->(c:Component)<-[:ABOUT]-(r:RuleCard)
WHERE ($include_drafts OR (d.status = 'approved' AND r.status = 'approved'))
OPTIONAL MATCH (r)-[:CITES]->(s:Source)
RETURN c.id AS component, h.level AS level, r {.*} AS rule, collect(s {.*}) AS sources
"""


@dataclass
class Neo4jGraph:
    driver: object
    include_drafts: bool = False
    database: str | None = None

    @classmethod
    def from_env(cls, include_drafts: bool = False) -> "Neo4jGraph":
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(
            os.environ["NEO4J_URI"], auth=(os.environ.get("NEO4J_USERNAME", "neo4j"), os.environ["NEO4J_PASSWORD"])
        )
        return cls(driver=driver, include_drafts=include_drafts)

    def _read(self, query: str, **params) -> list[dict]:
        params["include_drafts"] = self.include_drafts
        with self.driver.session(database=self.database, default_access_mode="READ") as session:
            return session.execute_read(lambda tx: [r.data() for r in tx.run(query, **params)])

    def search_dish(self, query: str, limit: int = 5, threshold: float = 0.3) -> list[DishMatch]:
        matches = []
        for d in self._read(ALL_DISHES):
            names = [d["name_en"], d["name_bn"], *d["aliases"]]
            score, _, name = max((name_score(n, query), len(normalise_name(n)), n) for n in names)
            if score >= threshold:
                matches.append(DishMatch(d["id"], d["name_en"], d["name_bn"], name, round(score, 3)))
        # Equal scores: the longer matched name is the more specific dish ("light chicken curry"
        # must not lose to "chicken curry", which is also found inside the query).
        matches.sort(key=lambda m: (-m.score, -len(normalise_name(m.matched_name)), m.dish_id))
        return matches[:limit]

    def get_components(self, dish_id: str) -> dict:
        rows = self._read(DISH_DETAIL, id=dish_id)
        if not rows:
            raise KeyError(dish_id)
        row = rows[0]
        dish = row["dish"]
        levels = {c["id"]: c["level"] for c in row["comps"] if c.get("id")}
        return {
            "dish_id": dish["id"],
            "name_en": dish["name_en"],
            "name_bn": dish["name_bn"],
            "status": dish.get("status", ""),
            "level_basis": dish.get("level_basis", ""),
            "components": {c.value: levels.get(c.value, "none") for c in sorted(Component, key=lambda c: c.value)},
            "ingredients": sorted(row["ingredients"]),
            "gentler_alternatives": sorted(row["alternatives"]),
            "sources": [],
        }

    def explain_verdict_path(self, dish_id: str, profile: Profile) -> list[VerdictPathStep]:
        self.get_components(dish_id)  # raises KeyError for unknown dishes
        steps = []
        for row in self._read(DISH_RULE_PATHS, id=dish_id):
            r = row["rule"]
            rule = RuleCard(
                id=r["id"], component=Component(row["component"]), min_level=Level.parse(r.get("min_level", "low")),
                severity=int(r["severity"]), hard=bool(r.get("hard")),
                diagnoses=frozenset(Diagnosis(x) for x in r.get("diagnoses", [])),
                phenotypes=frozenset(r.get("phenotypes", [])),
                states=frozenset(DiseaseState(x) for x in r.get("states", [])),
            )
            level = Level.parse(row["level"])
            if not rule.applies(profile, rule.component, level):
                continue
            ref = RuleRef(
                id=r["id"], title_en=r.get("title_en", ""), title_bn=r.get("title_bn", ""),
                recommendation_en=r.get("recommendation_en", ""), recommendation_bn=r.get("recommendation_bn", ""),
                severity=int(r["severity"]), hard=bool(r.get("hard")), evidence_level=r.get("evidence_level", ""),
                status=r.get("status", ""),
                sources=tuple(SourceRef(key=s.get("key", ""), citation=s.get("citation", ""), doi=s.get("doi", ""),
                                        pmid=s.get("pmid", ""), licence=s.get("licence", ""), quote=s.get("quote", ""))
                              for s in row["sources"]),
            )
            steps.append(VerdictPathStep(row["component"], row["level"], ref))
        steps.sort(key=lambda s: (not s.rule.hard, -s.rule.severity, s.component, s.rule.id))
        return steps
