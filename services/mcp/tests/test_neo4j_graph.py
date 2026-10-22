"""Neo4jGraph against a fake driver that answers like Neo4j would for the seed graph."""

from happygut_mcp.neo4j_graph import ALL_DISHES, DISH_DETAIL, DISH_RULE_PATHS, Neo4jGraph
from happygut_pipelines.graph import MemoryGraph, profile_from

MEM = MemoryGraph.from_seeds(include_drafts=True)


class FakeRecord(dict):
    def data(self):
        return dict(self)


class FakeTx:
    def run(self, query, **p):
        if query == ALL_DISHES:
            return [FakeRecord(id=d.id, name_en=d.name_en, name_bn=d.name_bn, aliases=list(d.aliases))
                    for d in MEM.dishes.values()]
        if query == DISH_DETAIL:
            d = MEM.dishes.get(p["id"])
            if d is None:
                return []
            c = MEM.get_components(d.id)
            comps = [{"id": k, "level": v} for k, v in c["components"].items() if v != "none"]
            return [FakeRecord(dish={"id": d.id, "name_en": d.name_en, "name_bn": d.name_bn, "status": d.status,
                                     "level_basis": c["level_basis"]},
                               comps=comps, ingredients=c["ingredients"], alternatives=c["gentler_alternatives"])]
        if query == DISH_RULE_PATHS:
            d = MEM.dishes[p["id"]]
            rows = []
            for comp, lvl in d.components.items():
                if lvl is None or lvl.value == 0:
                    continue
                for r in MEM.rules:
                    if r.rule.component == comp:
                        rows.append(FakeRecord(
                            component=comp.value, level=lvl.name.lower(),
                            rule={"id": r.ref.id, "min_level": r.rule.min_level.name.lower(), "severity": r.ref.severity,
                                  "hard": r.ref.hard, "diagnoses": [x.value for x in r.rule.diagnoses],
                                  "phenotypes": list(r.rule.phenotypes), "states": [x.value for x in r.rule.states],
                                  "title_en": r.ref.title_en, "status": r.ref.status},
                            sources=[s.__dict__ for s in r.ref.sources]))
            return rows
        raise AssertionError(query)


class FakeSession:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute_read(self, fn):
        return fn(FakeTx())


class FakeDriver:
    def session(self, **kw):
        assert kw.get("default_access_mode") == "READ"
        return FakeSession()


G = Neo4jGraph(driver=FakeDriver(), include_drafts=True)


def test_search_matches_memory_graph():
    for q in ["kachchi", "ফুচকা", "ajke dupure kacchi khabo", "musur dal"]:
        assert [m.dish_id for m in G.search_dish(q)] == [m.dish_id for m in MEM.search_dish(q)]


def test_components_match_memory_graph():
    assert G.get_components("dish.kacchi_biryani")["components"] == MEM.get_components("dish.kacchi_biryani")["components"]


def test_verdict_paths_match_memory_graph():
    for profile in [profile_from("CD", "remission", ["stricturing"]), profile_from("UC", "flare"),
                    profile_from("CD", "remission", ["ibs_like_symptoms"])]:
        for dish in ["dish.shak_bhaji", "dish.kacchi_biryani", "dish.chotpoti"]:
            a = [(s.component, s.rule.id) for s in G.explain_verdict_path(dish, profile)]
            b = [(s.component, s.rule.id) for s in MEM.explain_verdict_path(dish, profile)]
            assert a == b, (dish, profile)
