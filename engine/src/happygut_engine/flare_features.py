"""Features for the flare-risk model v1 (pure, no dependencies).

One row per day: what the diary says up to and including that day, plus whether a marked
stressful period starts within the horizon (known from the calendar). Nothing from after the
day is used, so training never sees the future. The same function feeds training (on the
simulated cohort) and the live app, so the model always gets the inputs it was trained on.
"""

from __future__ import annotations

import math
import statistics
from collections.abc import Collection, Sequence
from datetime import date, timedelta

from .patterns import DayRecord
from .vocab import Component, Level

MISSING = math.nan
FOOD_FEATURES = {
    "high_fat_days_3": Component.FAT,
    "very_spicy_days_3": Component.CAPSAICIN_SPICE,
    "high_lactose_days_3": Component.LACTOSE,
    "high_gos_days_3": Component.GOS,
    "high_fibre_days_3": Component.INSOLUBLE_FIBRE,
    "red_meat_days_3": Component.RED_PROCESSED_MEAT,
}
FEATURES: tuple[str, ...] = (
    "index_today", "index_mean_3", "index_max_7", "index_rise", "index_slope_3", "active_days_7", "days_logged_7",
    "food_reaction_days_3", "late_nights_3", "short_sleep_3", "poor_sleep_3", "high_stress_days_3", "stress_mean_3",
    "in_stressful_period", "stressful_period_soon", "missed_doses_7", *FOOD_FEATURES, "flare_days_30", "days_since_flare",
)


def features(records: Sequence[DayRecord], as_of: date, *, active_at: int, stressful_period_soon: bool,
             flare_days: Collection[date]) -> dict[str, float]:
    """The feature row for ``as_of``. Missing values are NaN (the model handles them).

    ``flare_days``: the days counted as flare *as known on* ``as_of``. A flare is only recognised a few
    days in, so training passes what the detector said with the data up to that day, never later.
    """
    past = [r for r in records if r.day <= as_of]
    by_day = {r.day: r for r in past}

    def window(days: int) -> list[DayRecord]:
        return [by_day[d] for d in (as_of - timedelta(days=i) for i in range(days)) if d in by_day]

    def scores(rows: list[DayRecord]) -> list[int]:
        return [r.index for r in rows if r.index is not None]

    last3, last7 = window(3), window(7)
    today = by_day.get(as_of)
    s3, s7 = scores(last3), scores(last7)
    earlier = [r.index for r in past if r.index is not None and r.day < as_of - timedelta(days=2)][-14:]
    three_ago = by_day.get(as_of - timedelta(days=3))
    stress3 = [r.stress for r in last3 if r.stress is not None]
    known = sorted(d for d in flare_days if d <= as_of)

    row: dict[str, float] = {
        "index_today": today.index if today and today.index is not None else MISSING,
        "index_mean_3": statistics.mean(s3) if s3 else MISSING,
        "index_max_7": max(s7) if s7 else MISSING,
        "index_rise": statistics.mean(s3) - statistics.median(earlier) if s3 and len(earlier) >= 3 else MISSING,
        "index_slope_3": (today.index - three_ago.index) if today and three_ago and today.index is not None
        and three_ago.index is not None else MISSING,
        "active_days_7": sum(1 for v in s7 if v >= active_at),
        "days_logged_7": len(last7),
        "food_reaction_days_3": sum(1 for r in last3 if r.food_reaction),
        "late_nights_3": sum(1 for r in last3 if r.late_night),
        "short_sleep_3": sum(1 for r in last3 if r.sleep_hours is not None and r.sleep_hours < 6),
        "poor_sleep_3": sum(1 for r in last3 if r.sleep_quality == "poor"),
        "high_stress_days_3": sum(1 for v in stress3 if v >= 3),
        "stress_mean_3": statistics.mean(stress3) if stress3 else MISSING,
        "in_stressful_period": 1.0 if today and today.period_types else 0.0,
        "stressful_period_soon": 1.0 if stressful_period_soon else 0.0,
        "missed_doses_7": sum(1 for r in last7 if r.medication == "missed"),
        "flare_days_30": sum(1 for d in known if (as_of - d).days < 30),
        "days_since_flare": float(min(180, (as_of - known[-1]).days)) if known else 180.0,
    }
    for name, component in FOOD_FEATURES.items():
        row[name] = sum(1 for r in last3 if (r.components.get(component) or Level.NONE) >= Level.HIGH)
    return {name: float(row[name]) for name in FEATURES}
