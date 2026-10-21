"""Seed consistency + end-to-end sanity of the engine on the real seed files."""

import pytest

from happygut_engine import DiseaseState as S, Diagnosis as D, Profile, Verdict as V, assess_meal
from happygut_pipelines.seeds import load_dishes, load_rules, review_status, validate


def test_seeds_are_consistent():
    assert validate() == []


def test_minimum_seed_counts():
    status = review_status()
    assert sum(status["dishes"].values()) >= 50
    assert sum(status["rule_cards"].values()) >= 25


def test_drafts_are_not_loaded_by_default():
    approved = load_dishes()
    assert all(d.status == "approved" for d in approved.values())


@pytest.fixture(scope="module")
def kb():
    return load_dishes(include_drafts=True), load_rules(include_drafts=True)


def verdict(kb, dish_id, profile, **kwargs):
    dishes, rules = kb
    pool = {k: v.to_evidence() for k, v in dishes.items()}
    return assess_meal([dishes[dish_id].to_evidence()], profile, rules, alternatives_pool=pool, **kwargs)


REMISSION = Profile(D.CD, S.REMISSION)
FLARE = Profile(D.CD, S.FLARE)
STRICTURE = Profile(D.CD, S.REMISSION, frozenset({"stricturing"}))
IBS_LIKE = Profile(D.UC, S.REMISSION, frozenset({"ibs_like_symptoms"}))


def test_plain_rice_is_ok_for_everyone(kb):
    for p in (REMISSION, FLARE, STRICTURE, IBS_LIKE):
        assert verdict(kb, "dish.plain_rice", p).verdict == V.LIKELY_OK


def test_kacchi_during_flare_is_trigger_with_gentler_alternative(kb):
    m = verdict(kb, "dish.kacchi_biryani", FLARE)
    assert m.verdict == V.LIKELY_TRIGGER
    assert m.dishes[0].alternative_id in {"dish.murgir_patla_jhol", "dish.chicken_stew", "dish.plain_rice"}


def test_leafy_greens_with_stricture_hit_the_hard_rule(kb):
    m = verdict(kb, "dish.shak_bhaji", STRICTURE)
    assert m.verdict == V.LIKELY_TRIGGER
    assert "RC-STRICT-001" in m.dishes[0].hard_rule_ids


def test_jhalmuri_peanuts_with_stricture_hit_the_hard_rule(kb):
    assert "RC-STRICT-002" in verdict(kb, "dish.jhalmuri", STRICTURE).dishes[0].hard_rule_ids


def test_chotpoti_with_ibs_like_symptoms_is_flagged(kb):
    assert verdict(kb, "dish.chotpoti", IBS_LIKE).verdict in {V.CAUTION, V.LIKELY_TRIGGER}


def test_every_gentle_alternative_is_ok_in_remission(kb):
    dishes, _ = kb
    alternatives = {a for d in dishes.values() for a in d.gentler_alternatives}
    for alt in alternatives:
        assert verdict(kb, alt, REMISSION).verdict == V.LIKELY_OK, alt
