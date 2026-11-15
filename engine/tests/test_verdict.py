import pytest

from happygut_engine import (
    Component as C,
    DiseaseState as S,
    Diagnosis as D,
    DishEvidence,
    Level as L,
    PersonalEvidence,
    Profile,
    RuleCard,
    Verdict as V,
    assess_dish,
    assess_meal,
)

REMISSION_CD = Profile(D.CD, S.REMISSION)
FLARE_CD = Profile(D.CD, S.FLARE)
STRICTURE_CD = Profile(D.CD, S.REMISSION, frozenset({"stricturing"}))

RULES = (
    RuleCard("RC-FAT-FLARE", C.FAT, L.HIGH, severity=2, states=frozenset({S.FLARE})),
    RuleCard("RC-FAT", C.FAT, L.HIGH, severity=1),
    RuleCard("RC-SPICE", C.CAPSAICIN_SPICE, L.MEDIUM, severity=2),
    RuleCard("RC-STRICT-FIBRE", C.INSOLUBLE_FIBRE, L.MEDIUM, severity=3,
             diagnoses=frozenset({D.CD}), phenotypes=frozenset({"stricturing"}), hard=True),
    RuleCard("RC-LACTOSE", C.LACTOSE, L.MEDIUM, severity=2, phenotypes=frozenset({"lactose_intolerant"})),
)


def dish(dish_id="dish.x", alternatives=(), perception=1.0, resolution=1.0, **levels):
    return DishEvidence(
        dish_id=dish_id,
        components={C(k): v for k, v in levels.items()},
        perception_confidence=perception,
        resolution_confidence=resolution,
        alternatives=alternatives,
    )


def test_plain_dish_is_likely_ok():
    v = assess_dish(dish(fat=L.LOW, insoluble_fibre=L.LOW), REMISSION_CD, RULES)
    assert v.verdict == V.LIKELY_OK
    assert v.reason == "no_risk"


def test_never_returns_a_safe_label():
    assert {v.value for v in V} == {"likely_ok", "caution", "likely_trigger", "not_sure"}


def test_rule_only_applies_at_or_above_min_level():
    v = assess_dish(dish(fat=L.MEDIUM), FLARE_CD, RULES)
    assert v.components[0].rule_ids == ()


def test_flare_makes_the_same_dish_riskier():
    biryani = dish(fat=L.HIGH)
    calm = assess_dish(biryani, REMISSION_CD, RULES)
    flare = assess_dish(biryani, FLARE_CD, RULES)
    assert calm.verdict == V.LIKELY_OK  # severity 1 at high level = 0.33
    assert flare.verdict == V.LIKELY_TRIGGER  # severity 2 x 1.3 flare
    assert flare.risk > calm.risk
    assert "RC-FAT-FLARE" in flare.evidence_ids


def test_moderate_rule_at_medium_level_is_caution():
    v = assess_dish(dish(capsaicin_spice=L.MEDIUM), REMISSION_CD, RULES)
    assert v.verdict == V.CAUTION
    assert v.reason == "guideline"


def test_stricturing_hard_rule_forces_trigger():
    salad = dish(insoluble_fibre=L.MEDIUM)
    assert assess_dish(salad, REMISSION_CD, RULES).verdict == V.LIKELY_OK
    v = assess_dish(salad, STRICTURE_CD, RULES)
    assert v.verdict == V.LIKELY_TRIGGER
    assert v.reason == "hard_rule"
    assert v.hard_rule_ids == ("RC-STRICT-FIBRE",)
    assert v.risk == 1.0


def test_hard_rule_is_not_discounted_by_personal_tolerance():
    tolerant = {C.INSOLUBLE_FIBRE: PersonalEvidence(C.INSOLUBLE_FIBRE, p_trigger=0.05, exposures=10)}
    v = assess_dish(dish(insoluble_fibre=L.HIGH), STRICTURE_CD, RULES, tolerant)
    assert v.verdict == V.LIKELY_TRIGGER


def test_hard_rule_respects_diagnosis():
    uc_stricture = Profile(D.UC, S.REMISSION, frozenset({"stricturing"}))
    v = assess_dish(dish(insoluble_fibre=L.HIGH), uc_stricture, RULES)
    assert v.verdict != V.LIKELY_TRIGGER


def test_phenotype_specific_rule():
    doi = dish(lactose=L.MEDIUM)
    assert assess_dish(doi, REMISSION_CD, RULES).verdict == V.LIKELY_OK
    intolerant = Profile(D.CD, S.REMISSION, frozenset({"lactose_intolerant"}))
    assert assess_dish(doi, intolerant, RULES).verdict == V.CAUTION


def test_learned_personal_trigger_raises_verdict():
    personal = {C.FAT: PersonalEvidence(C.FAT, p_trigger=0.9, exposures=5)}
    v = assess_dish(dish(fat=L.HIGH), REMISSION_CD, RULES, personal)
    assert v.verdict == V.LIKELY_TRIGGER
    assert v.reason == "personal"
    assert "personal:fat" in v.evidence_ids


def test_personal_evidence_with_few_exposures_is_down_weighted():
    personal = {C.FAT: PersonalEvidence(C.FAT, p_trigger=0.9, exposures=2)}
    v = assess_dish(dish(fat=L.HIGH), REMISSION_CD, RULES, personal)
    assert v.personal_contribution == pytest.approx(0.4)  # strength 0.8 x level 1.0 x prior weight 0.5
    assert v.verdict == V.CAUTION


def test_personal_trigger_scales_with_level():
    personal = {C.FAT: PersonalEvidence(C.FAT, p_trigger=0.9, exposures=5)}
    low = assess_dish(dish(fat=L.LOW), REMISSION_CD, RULES, personal)
    high = assess_dish(dish(fat=L.HIGH), REMISSION_CD, RULES, personal)
    assert low.verdict == V.LIKELY_OK
    assert high.verdict == V.LIKELY_TRIGGER


def test_stricture_low_fibre_is_caution_not_ok():
    rules = RULES + (RuleCard("RC-STRICT-LOW", C.INSOLUBLE_FIBRE, L.LOW, severity=3,
                              diagnoses=frozenset({D.CD}), phenotypes=frozenset({"stricturing"})),)
    v = assess_dish(dish(insoluble_fibre=L.LOW), STRICTURE_CD, rules)
    assert v.verdict == V.CAUTION


def test_tolerated_component_discounts_guideline():
    personal = {C.CAPSAICIN_SPICE: PersonalEvidence(C.CAPSAICIN_SPICE, p_trigger=0.1, exposures=6)}
    plain = assess_dish(dish(capsaicin_spice=L.HIGH), REMISSION_CD, RULES)
    tolerated = assess_dish(dish(capsaicin_spice=L.HIGH), REMISSION_CD, RULES, personal)
    assert plain.verdict == V.LIKELY_TRIGGER
    assert tolerated.verdict == V.CAUTION
    assert tolerated.components[0].tolerated


def test_low_perception_confidence_is_not_sure():
    v = assess_dish(dish(perception=0.3, fat=L.HIGH), FLARE_CD, RULES)
    assert v.verdict == V.NOT_SURE
    assert v.reason == "low_confidence"


def test_low_confidence_still_reports_possible_hard_rule():
    v = assess_dish(dish(resolution=0.2, insoluble_fibre=L.HIGH), STRICTURE_CD, RULES)
    assert v.verdict == V.NOT_SURE
    assert v.hard_rule_ids == ("RC-STRICT-FIBRE",)


def test_unknown_levels_reduce_confidence():
    v = assess_dish(dish(fat=None, lactose=None, capsaicin_spice=L.LOW), REMISSION_CD, RULES)
    assert v.confidence == pytest.approx(1 / 3, abs=1e-3)
    assert v.verdict == V.NOT_SURE


def test_dish_with_no_component_data_is_not_sure():
    assert assess_dish(dish(), REMISSION_CD, RULES).verdict == V.NOT_SURE


def test_meal_takes_the_most_cautious_dish():
    rice = dish("dish.rice", fat=L.NONE)
    kacchi = dish("dish.kacchi", fat=L.HIGH, capsaicin_spice=L.MEDIUM)
    meal = assess_meal([rice, kacchi], FLARE_CD, RULES)
    assert meal.verdict == V.LIKELY_TRIGGER
    assert [d.dish_id for d in meal.dishes] == ["dish.rice", "dish.kacchi"]


def test_not_sure_dish_outranks_ok_but_not_caution():
    unknown = dish("dish.unknown")
    rice = dish("dish.rice", fat=L.NONE)
    spicy = dish("dish.spicy", capsaicin_spice=L.MEDIUM)
    assert assess_meal([rice, unknown], REMISSION_CD, RULES).verdict == V.NOT_SURE
    assert assess_meal([unknown, spicy], REMISSION_CD, RULES).verdict == V.CAUTION


def test_empty_meal_is_not_sure():
    assert assess_meal([], REMISSION_CD, RULES).verdict == V.NOT_SURE


def test_gentler_alternative_is_chosen():
    pool = {
        "dish.chicken_jhol": dish("dish.chicken_jhol", fat=L.LOW, capsaicin_spice=L.LOW),
        "dish.beef_bhuna": dish("dish.beef_bhuna", fat=L.HIGH, capsaicin_spice=L.HIGH),
    }
    kacchi = dish("dish.kacchi", alternatives=("dish.beef_bhuna", "dish.chicken_jhol", "dish.missing"),
                  fat=L.HIGH, capsaicin_spice=L.MEDIUM)
    meal = assess_meal([kacchi], FLARE_CD, RULES, alternatives_pool=pool)
    assert meal.dishes[0].alternative_id == "dish.chicken_jhol"


def test_no_alternative_for_ok_dish():
    pool = {"dish.y": dish("dish.y", fat=L.NONE)}
    meal = assess_meal([dish("dish.x", alternatives=("dish.y",), fat=L.LOW)], REMISSION_CD, RULES,
                       alternatives_pool=pool)
    assert meal.dishes[0].alternative_id is None


def test_result_carries_config_version():
    assert assess_meal([dish(fat=L.LOW)], REMISSION_CD, RULES).config_version == "engine-v0.2"


def test_rule_card_validation():
    with pytest.raises(ValueError):
        RuleCard("bad", C.FAT, L.HIGH, severity=4)
    with pytest.raises(ValueError):
        RuleCard("bad", C.FAT, L.NONE, severity=1)


def test_no_evidence_either_way_adds_no_personal_risk():
    # p_trigger 0.5 means the diary shows no difference; it must not raise the verdict on its own.
    for p in (0.3, 0.5):
        personal = {C.FAT: PersonalEvidence(C.FAT, p_trigger=p, exposures=20)}
        v = assess_dish(dish(fat=L.HIGH), REMISSION_CD, (), personal)
        assert v.personal_contribution == 0 and v.verdict == V.LIKELY_OK
        assert "personal:fat" not in v.evidence_ids
    weak = {C.FAT: PersonalEvidence(C.FAT, p_trigger=0.65, exposures=20)}
    assert assess_dish(dish(fat=L.HIGH), REMISSION_CD, (), weak).verdict == V.LIKELY_OK


def test_evidence_learned_from_high_levels_does_not_spill_onto_low_levels():
    # The Pattern Finder learns from high-fat meals; a low-fat dish must not inherit that.
    personal = {C.FAT: PersonalEvidence(C.FAT, p_trigger=0.95, exposures=14, min_level=L.HIGH)}
    assert assess_dish(dish(fat=L.HIGH), REMISSION_CD, (), personal).verdict == V.LIKELY_TRIGGER
    assert assess_dish(dish(fat=L.MEDIUM), REMISSION_CD, (), personal).verdict == V.CAUTION  # one step below, lower weight
    low = assess_dish(dish(fat=L.LOW), REMISSION_CD, (), personal)
    assert low.verdict == V.LIKELY_OK and low.personal_contribution == 0
