import pytest

from happygut_pipelines.graph import (
    CONSTRAINTS,
    MemoryGraph,
    graph_statements,
    name_score,
    profile_from,
    similarity,
)


@pytest.fixture(scope="module")
def g():
    return MemoryGraph.from_seeds(include_drafts=True)


def test_trigram_similarity_matches_pg_trgm_behaviour():
    assert similarity("kacchi", "kacchi") == 1.0
    assert 0.3 < similarity("kacchi", "kachchi") < 1.0
    assert similarity("kacchi", "pizza") < 0.1


def test_name_found_inside_a_sentence():
    assert name_score("kacchi", "ajke dupure kacchi khabo") == 1.0


def test_approved_only_by_default():
    assert MemoryGraph.from_seeds().dishes == {} or all(
        d.status == "approved" for d in MemoryGraph.from_seeds().dishes.values())


@pytest.mark.parametrize("query,expected", [
    ("kacchi biryani", "dish.kacchi_biryani"),
    ("kachchi biriyani", "dish.kacchi_biryani"),
    ("কাচ্চি বিরিয়ানি", "dish.kacchi_biryani"),
    ("ajke dupure kacchi khabo", "dish.kacchi_biryani"),
    ("shorshe ilish", "dish.shorshe_ilish"),
    ("musur dal", "dish.masoor_dal"),
    ("ফুচকা", "dish.fuchka"),
    # A name that contains another dish's shorter name must still find the more specific dish.
    ("Light chicken curry", "dish.murgir_patla_jhol"),
    ("mutton rezala", "dish.mutton_rezala"),
    ("patla khichuri", "dish.patla_khichuri"),
    ("lal cha", "dish.rong_cha"),
    # Fast food, snacks, drinks and fruit (2026-11-19 expansion).
    ("burger", "dish.beef_burger"),
    ("chicken burger", "dish.chicken_burger"),
    ("pepperoni pizza", "dish.pizza"),
    ("chicken biryani", "dish.chicken_biryani"),
    ("kacchi biryani", "dish.kacchi_biryani"),
    ("maggi noodles", "dish.instant_noodles"),
    ("noodles", "dish.chowmein"),
    ("coke", "dish.soft_drink"),
    ("dim bhaji", "dish.omelette"),
])
def test_search_dish(g, query, expected):
    assert g.search_dish(query)[0].dish_id == expected


def test_unknown_dish_returns_nothing(g):
    assert g.search_dish("sushi platter") == []


def test_get_components(g):
    c = g.get_components("dish.kacchi_biryani")
    assert c["components"]["fat"] == "high"
    assert "dish.plain_rice" in c["gentler_alternatives"]
    assert c["level_basis"] == "typical_recipe_estimate"


def test_explain_path_for_stricture_puts_hard_rules_first(g):
    steps = g.explain_verdict_path("dish.shak_bhaji", profile_from("CD", "remission", ["stricturing"]))
    assert steps[0].rule.hard
    assert steps[0].rule.id == "RC-STRICT-001"
    assert steps[0].component == "insoluble_fibre"
    assert steps[0].rule.sources[0].citation


def test_explain_path_is_empty_when_nothing_applies(g):
    assert g.explain_verdict_path("dish.plain_rice", profile_from("CD", "flare")) == []


def test_explain_path_respects_state(g):
    flare = {s.rule.id for s in g.explain_verdict_path("dish.kacchi_biryani", profile_from("CD", "flare"))}
    calm = {s.rule.id for s in g.explain_verdict_path("dish.kacchi_biryani", profile_from("CD", "remission"))}
    assert "RC-FLARE-FAT-H" in flare and "RC-FLARE-FAT-H" not in calm


def test_neo4j_statements_cover_everything(g):
    stmts = graph_statements(g)
    assert [s for s, _ in stmts[: len(CONSTRAINTS)]] == CONSTRAINTS
    by_text = {s.split()[1] if s.startswith("UNWIND") else s.split()[0]: p for s, p in stmts}
    dish_rows = next(p["rows"] for s, p in stmts if "MERGE (d:Dish" in s)
    rule_rows = next(p["rows"] for s, p in stmts if "MERGE (r:RuleCard" in s)
    assert len(dish_rows) == len(g.dishes) and len(rule_rows) == len(g.rules)
    kacchi = next(r for r in dish_rows if r["id"] == "dish.kacchi_biryani")
    assert {"id": "fat", "level": "high"} in kacchi["components"]
    assert all(c["level"] != "none" for c in kacchi["components"]), "none-level components are not linked"
    assert any(i["id"] == "ing.basmati_rice" for i in kacchi["ingredients"])
    keep = next(p["keep_ids"] for s, p in stmts if "DETACH DELETE" in s)
    assert "dish.kacchi_biryani" in keep and "RC-STRICT-001" in keep
    assert by_text  # statements are well-formed tuples


def test_statements_are_parameterised(g):
    for statement, _ in graph_statements(g):
        assert "kacchi" not in statement.lower(), "data must go in parameters, never in Cypher text"


def test_every_stored_name_leads_to_its_own_dish(g):
    wrong = [(n, d.id) for d in g.dishes.values() for n in (d.name_en, d.name_bn, *d.aliases)
             if n and g.search_dish(n)[0].dish_id != d.id]
    assert wrong == []
