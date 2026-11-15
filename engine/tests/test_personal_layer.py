"""Spec 003: indices, sleep, periods, Flare Pattern Finder, flare risk, and recovery of injected patterns."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from happygut_engine import (Component, DayRecord, DiaryItems, Diagnosis, Level, ManualFlare, detect_periods,
                             find_patterns, flare_risk, hbi, index_for, is_late_night, kind_by_day,
                             personal_evidence, sccai, sleep_hours, worse_days)
from happygut_engine.patterns import LATE_NIGHT, LIKELY, NOT_ENOUGH, NOT_LINKED
from happygut_engine.simulate import Effect, MenuItem, SimConfig, StressPeriod, simulate

D0 = date(2026, 7, 1)


def day(i: int) -> date:
    return D0 + timedelta(days=i)


# ---------------------------------------------------------------- indices

def test_hbi_counts_only_liquid_stools():
    assert hbi(DiaryItems(stools=3, bristol=4, pain=1, wellbeing=1)).score == 2
    assert hbi(DiaryItems(stools=3, bristol=6, pain=1, wellbeing=1)).score == 5
    assert hbi(DiaryItems()).score == 0


@pytest.mark.parametrize("stools,night,urgency,blood,wellbeing,expected", [
    (2, 0, "none", "none", 0, 0),
    (5, 0, "hurry", "none", 1, 3),  # day 4-6 → 1, urgency 1, wellbeing 1
    (9, 2, "immediately", "streaks", 2, 8),  # day 7 → 2, night 1-3 → 1, urgency 2, blood 1, wellbeing 2
    (14, 4, "incontinence", "a_lot", 4, 15),  # day 10 → 3, night 4 → 2, urgency 3, blood 3, wellbeing 4
])
def test_sccai(stools, night, urgency, blood, wellbeing, expected):
    assert sccai(DiaryItems(stools=stools, night_stools=night, urgency=urgency, blood=blood, wellbeing=wellbeing)).score == expected


def test_index_follows_diagnosis_and_validates():
    items = DiaryItems(stools=4, bristol=6, wellbeing=1)
    assert index_for(Diagnosis.CD, items).name == "HBI" and index_for(Diagnosis.UC, items).name == "SCCAI"
    with pytest.raises(ValueError):
        DiaryItems(stools=1, night_stools=2)
    with pytest.raises(ValueError):
        DiaryItems(bristol=8)


# ---------------------------------------------------------------- sleep

def test_sleep_hours_across_midnight():
    assert sleep_hours("23:30", "07:00") == 7.5
    assert sleep_hours("02:30", "08:00") == 5.5
    assert sleep_hours("21:00", "05:00") == 8.0


def test_usual_bedtime_is_the_median_across_midnight():
    from happygut_engine import usual_bedtime

    assert usual_bedtime([]) is None
    assert usual_bedtime(["23:30", "23:50", "00:10", "02:30", "23:40"]) == "23:50"
    assert usual_bedtime(["00:30", "01:00", "01:30"]) == "01:00"


def test_late_night_uses_own_median_after_a_week():
    assert is_late_night("01:30") and not is_late_night("00:30")  # fixed 01:00 at first
    usual = ["23:30"] * 10
    assert is_late_night("01:15", usual) and not is_late_night("00:45", usual)
    night_owl = ["02:00"] * 10  # a shift worker's 02:30 is not "late"
    assert not is_late_night("02:30", night_owl) and is_late_night("04:00", night_owl)


# ---------------------------------------------------------------- periods

def scores(values: list[int | None]) -> dict[date, int]:
    return {day(i): v for i, v in enumerate(values) if v is not None}


def test_no_periods_before_a_week():
    assert detect_periods(scores([1] * 6), "HBI") == []


def test_flare_needs_three_active_of_four():
    assert [p.kind for p in detect_periods(scores([1, 6, 1, 6, 1, 1, 1, 1, 1]), "HBI")] == ["remission"]
    periods = detect_periods(scores([1, 1, 6, 2, 7, 6, 6, 1, 1, 1, 1, 1, 1, 1, 1]), "HBI")
    assert [(p.kind, p.start, p.end) for p in periods] == [
        ("remission", day(0), day(1)), ("flare", day(2), day(6)), ("remission", day(7), day(14))]
    assert periods[-1].ongoing


def test_flare_ends_only_after_seven_calm_days():
    periods = detect_periods(scores([6, 6, 6, 1, 1, 1, 6, 6, 1, 1, 1, 1]), "HBI")
    assert [(p.kind, p.start, p.end) for p in periods] == [("flare", day(0), day(7)), ("settling", day(8), day(11))]


def test_sccai_between_thresholds_is_not_calm():
    # 3-4 is neither active nor remission: it keeps a flare open.
    periods = detect_periods(scores([6, 6, 6, 3, 3, 3, 3, 3, 3, 3, 3]), "SCCAI")
    assert [p.kind for p in periods] == ["flare"] and periods[0].ongoing


def test_user_decisions_win():
    values = [1, 1, 6, 6, 6, 1, 1, 1, 1, 1, 1, 1, 1]
    assert [p.kind for p in detect_periods(scores(values), "HBI", rejected_flares=[day(2)])] == ["remission"]
    manual = detect_periods(scores([1] * 12), "HBI", manual_flares=[ManualFlare(day(4), day(6))])
    assert [(p.kind, p.source) for p in manual] == [("remission", "index"), ("flare", "user"), ("remission", "index")]
    assert kind_by_day(manual)[day(5)] == "flare"


# ---------------------------------------------------------------- patterns

def test_worse_day_is_relative_to_own_median():
    recs = [DayRecord(day(i), index=v) for i, v in enumerate([4, 4, 4, 4, 5, 6, 4])]
    assert worse_days(recs) == {day(5)}
    assert day(0) in worse_days([DayRecord(day(0), index=0, food_reaction=True)])


def test_late_nights_found_and_few_exposures_are_not_enough():
    recs = []
    for i in range(40):
        late = i % 5 == 0
        recs.append(DayRecord(day(i), index=4 if late else 1, late_night=late, stress=1,
                              components={Component.LACTOSE: Level.HIGH} if i in (3, 17) else {}))
    by = {r.factor: r for r in find_patterns(recs)}
    # Day 0 has no history to compare with yet, so 7 of the 8 late nights count as followed by a worse day.
    assert by[LATE_NIGHT].label == LIKELY and by[LATE_NIGHT].exposures == 8 and by[LATE_NIGHT].hits == 7
    assert by["food:lactose"].label == NOT_ENOUGH and by["food:lactose"].exposures == 2
    assert "stress:high" not in by  # never exposed


def test_skipped_answers_are_left_out_not_counted_as_normal():
    recs = [DayRecord(day(i), index=1, late_night=None if i < 20 else (i % 4 == 0)) for i in range(40)]
    r = next(r for r in find_patterns(recs) if r.factor == LATE_NIGHT)
    assert r.exposures + r.baseline_days == 20


def test_overlap_is_reported():
    recs = []
    for i in range(60):
        exam = 20 <= i < 34
        late = exam and i % 2 == 0
        recs.append(DayRecord(day(i), index=5 if exam else 1, late_night=late,
                              period_types=frozenset({"exam"}) if exam else frozenset()))
    by = {r.factor: r for r in find_patterns(recs)}
    assert "period:exam" in by[LATE_NIGHT].overlaps_with
    assert LATE_NIGHT not in by["period:exam"].overlaps_with


def test_scope_uses_only_days_of_that_period_kind():
    recs = [DayRecord(day(i), index=1, late_night=i % 3 == 0, period_kind="flare" if i >= 30 else "remission")
            for i in range(45)]
    all_days = next(r for r in find_patterns(recs) if r.factor == LATE_NIGHT)
    flare = next(r for r in find_patterns(recs, scope="flare") if r.factor == LATE_NIGHT)
    assert flare.exposures == 5 and all_days.exposures == 15


# ---------------------------------------------------------------- simulated persona: recover the injected truth

MENU = [
    MenuItem("rice", {}),
    MenuItem("dal", {Component.GOS: Level.MEDIUM}),  # medium levels are not tracked as exposures
    MenuItem("light curry", {Component.CAPSAICIN_SPICE: Level.LOW}),
    MenuItem("spicy bhorta", {Component.CAPSAICIN_SPICE: Level.HIGH}, weight=0.35),
    MenuItem("lassi", {Component.LACTOSE: Level.HIGH}, weight=0.6),
    MenuItem("biryani", {Component.FAT: Level.HIGH, Component.RED_PROCESSED_MEAT: Level.HIGH}, rich=True),
    MenuItem("fried snack", {Component.FAT: Level.HIGH}, rich=True),
]
TRUTH = SimConfig(
    days=120, seed=11, flare_windows=((44, 57),),
    food_effects={Component.FAT: Effect(2.4, 0.8)},
    late_night_effect=Effect(2.3, 0.9),
    period_effects={"exam": Effect(1.1, 0.7, next_day=0.0)},
    stress_periods=(StressPeriod("exam", "Exams", 38, 52),),
)


def records(sim, start: date = D0) -> list[DayRecord]:
    by_name = {m.name: m for m in MENU}
    out = []
    history: list[str] = []
    all_scores = {start + timedelta(days=s.offset): hbi(s.items).score for s in sim if s.logged}
    kinds = kind_by_day(detect_periods(all_scores, "HBI"))
    for s in sim:
        d = start + timedelta(days=s.offset)
        if not s.logged:
            continue
        comps: dict[Component, Level] = {}
        for f in s.foods:
            for c, lvl in by_name[f.name].components.items():
                comps[c] = max(comps.get(c, Level.NONE), lvl)
        out.append(DayRecord(
            d, index=all_scores[d], food_reaction=any(f.reactions for f in s.foods), components=comps,
            late_night=is_late_night(s.bedtime, history), sleep_hours=sleep_hours(s.bedtime, s.wake_time),
            sleep_quality=s.sleep_quality, stress=s.stress,
            period_types=frozenset(p.type for p in TRUTH.stress_periods if p.start <= s.offset <= p.end),
            medication=s.medication, period_kind=kinds.get(d),
        ))
        history.append(s.bedtime)
    return out


def test_simulation_is_reproducible_and_never_a_red_flag():
    a, b = simulate(TRUTH, MENU), simulate(TRUTH, MENU)
    assert a == b and len(a) == 120
    assert all(s.items.blood != "a_lot" for s in a)


def test_scripted_flare_is_detected_near_its_injected_start():
    sim = simulate(TRUTH, MENU)
    all_scores = {day(s.offset): hbi(s.items).score for s in sim if s.logged}
    flares = [p for p in detect_periods(all_scores, "HBI") if p.kind == "flare"]
    assert len(flares) == 1
    assert abs((flares[0].start - day(44)).days) <= 3 and abs((flares[0].end - day(57)).days) <= 3


def test_injected_patterns_are_recovered():
    by = {r.factor: r for r in find_patterns(records(simulate(TRUTH, MENU)))}
    assert by["food:fat"].label == LIKELY
    assert by[LATE_NIGHT].label == LIKELY
    assert by["period:exam"].label == LIKELY
    assert by["food:capsaicin_spice"].label != LIKELY  # eaten often, no injected effect
    assert by["food:capsaicin_spice"].exposures >= 10
    ev = personal_evidence(list(by.values()))
    assert ev[Component.FAT].p_trigger > 0.8 and ev[Component.FAT].exposures >= 3
    assert ev[Component.CAPSAICIN_SPICE].p_trigger < 0.8


def test_everyday_factor_has_nothing_to_compare_with():
    recs = [DayRecord(day(i), index=1 + (i % 6 == 0) * 3, components={Component.CAPSAICIN_SPICE: Level.HIGH}
                      if i % 20 else {}) for i in range(60)]
    spice = next(r for r in find_patterns(recs) if r.factor == "food:capsaicin_spice")
    assert spice.baseline_days < 7 and spice.label == NOT_ENOUGH


# ---------------------------------------------------------------- flare risk

def test_risk_is_low_on_calm_days_and_names_its_drivers():
    calm = [DayRecord(day(i), index=1, late_night=False, medication="taken") for i in range(30)]
    assert flare_risk(calm, find_patterns(calm)).level == "low"

    recs = records(simulate(TRUTH, MENU))
    patterns = find_patterns(recs)
    last = recs[-1].day
    recent = [DayRecord(last + timedelta(days=i), index=v, late_night=late, medication=med)
              for i, (v, late, med) in enumerate([(3, True, "taken"), (4, True, "missed"), (4, False, "taken")], start=1)]
    out = flare_risk(recs + recent, patterns, upcoming_period_types=["exam"])
    codes = {d.code for d in out.drivers}
    assert out.level in {"raised", "high"} and {"index_trend", "factor", "upcoming_period", "missed_doses"} <= codes
    assert out.score == min(100, sum(d.points for d in out.drivers))
    sleep = [d for d in out.drivers if d.factor and d.factor.startswith("sleep:")]
    assert len(sleep) == 1 and sleep[0].count == 2  # one sleep driver, not three for the same nights
