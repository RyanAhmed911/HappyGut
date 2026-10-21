from datetime import datetime, timedelta

from happygut_engine import (
    Component as C,
    Level as L,
    MealExposure,
    SymptomEvent,
    discover_triggers,
    exposure_outcomes,
    trigger_posterior,
)

T0 = datetime(2026, 9, 1, 13, 0)


def simulated_history(days=40):
    """SYNTHETIC: high-fat lunches every 3rd day are followed by symptoms ~20 h later."""
    meals, symptoms = [], []
    for d in range(days):
        lunch = T0 + timedelta(days=d)
        fatty = d % 3 == 0
        meals.append(MealExposure(lunch, {C.FAT: L.HIGH if fatty else L.LOW, C.LACTOSE: L.MEDIUM}))
        meals.append(MealExposure(lunch + timedelta(hours=7), {C.FAT: L.LOW}))
        if fatty:
            symptoms.append(SymptomEvent(lunch + timedelta(hours=20)))
    return meals, symptoms


def test_window_counts_symptoms_6_to_48_hours_later():
    meal = MealExposure(T0, {C.FAT: L.HIGH})
    too_soon = [SymptomEvent(T0 + timedelta(hours=2))]
    in_window = [SymptomEvent(T0 + timedelta(hours=30))]
    too_late = [SymptomEvent(T0 + timedelta(hours=60))]
    assert exposure_outcomes([meal], too_soon, C.FAT)[0] == [False]
    assert exposure_outcomes([meal], in_window, C.FAT)[0] == [True]
    assert exposure_outcomes([meal], too_late, C.FAT)[0] == [False]


def test_unknown_level_is_excluded():
    meal = MealExposure(T0, {C.FAT: None})
    assert exposure_outcomes([meal], [], C.FAT) == ([], [])


def test_injected_trigger_is_recovered():
    meals, symptoms = simulated_history()
    result = discover_triggers(meals, symptoms)
    assert result[C.FAT].likely_trigger
    assert result[C.FAT].p_trigger > 0.95


def test_innocent_component_is_not_flagged():
    meals, symptoms = simulated_history()
    result = discover_triggers(meals, symptoms)
    assert not result[C.LACTOSE].likely_trigger


def test_few_exposures_never_flag():
    r = trigger_posterior(C.FAT, exposed=[True, True], unexposed=[False] * 20)
    assert r.p_trigger > 0.8
    assert not r.likely_trigger


def test_results_are_reproducible():
    a = trigger_posterior(C.FAT, [True, False, True, True], [False] * 10)
    b = trigger_posterior(C.FAT, [True, False, True, True], [False] * 10)
    assert a == b


def test_credible_interval_brackets_rate():
    r = trigger_posterior(C.FAT, [True] * 6 + [False] * 2, [False] * 10)
    assert r.ci_low < r.exposed_rate < r.ci_high


def test_converts_to_personal_evidence():
    r = trigger_posterior(C.FAT, [True] * 5, [False] * 10)
    pe = r.to_personal_evidence()
    assert pe.component == C.FAT and pe.exposures == 5 and pe.p_trigger == r.p_trigger
