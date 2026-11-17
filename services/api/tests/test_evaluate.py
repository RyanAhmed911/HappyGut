"""The evaluation's deterministic suites double as gates: these must hold on the real seeds."""

from __future__ import annotations

from happygut_api import evaluate
from happygut_api.demo import build_menu
from happygut_api.knowledge import MemoryKnowledge


def test_red_flag_suite_catches_every_phrase_without_false_alarms():
    result = evaluate.red_flags()
    assert result["missed"] == [] and result["wrong_category"] == []
    assert result["false_alarms"] == []
    assert result["phrases"] >= 29 and all(v["phrases"] >= 5 for v in result["by_language"].values())


def test_verdict_rules_hold_on_the_real_dishes():
    knowledge = MemoryKnowledge.from_seeds(evaluate.SEEDS)
    result = evaluate.verdicts(knowledge)
    assert result["caution_or_trigger_without_a_rule"] == 0
    stricture = result["stricture_rule"]
    assert stricture["dishes_with_fibre_skins_seeds_nuts"] > 0 and stricture["not_rated_likely_trigger"] == []
    names = evaluate.dish_names(knowledge)
    assert all(v["names"] == v["resolved_to_own_dish"] for v in names.values())


def test_cohort_scoring_runs_and_is_reproducible():
    knowledge = MemoryKnowledge.from_seeds(evaluate.SEEDS)
    menu = build_menu(knowledge)
    candidates = evaluate.food_candidates(menu)
    first = evaluate.evaluate_patient((3, menu, candidates))
    assert first == evaluate.evaluate_patient((3, menu, candidates))
    assert set(first["horizons"]) == set(evaluate.HORIZONS)
