"""Flare-risk outlook v0: a transparent, rule-based score for the next few days (spec 003 FR-017).

Every point of the score comes from a named driver, so the app can show why. Version 1
(a gradient-boosted model on the simulated cohort, with SHAP drivers) is evaluated against
this one before it replaces it.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Sequence

from .patterns import (DEFAULT_PATTERN_CONFIG, LIKELY, POSSIBLE, DayRecord, PatternConfig, PatternResult, exposure)

LOW, RAISED, HIGH = "low", "raised", "high"


@dataclass(frozen=True)
class RiskConfig:
    version: str = "flare-risk-v0.1"
    lookback_days: int = 3
    horizon_days: int = 3
    trend_points_per_index_point: int = 8
    trend_max: int = 32
    likely_factor_points: int = 8
    possible_factor_points: int = 4
    per_factor_max: int = 16
    factor_max: int = 40
    upcoming_period_points: int = 10
    missed_dose_points: int = 6
    missed_dose_max: int = 12
    in_flare_points: int = 30
    raised_at: int = 30
    high_at: int = 60


DEFAULT_RISK_CONFIG = RiskConfig()


@dataclass(frozen=True)
class RiskDriver:
    code: str  # index_trend | factor | upcoming_period | missed_doses | in_flare
    points: int
    factor: str | None = None  # for "factor" and "upcoming_period" drivers
    count: int | None = None  # how many times in the lookback
    value: float | None = None  # e.g. index points above the usual level


@dataclass(frozen=True)
class RiskOutlook:
    score: int  # 0-100
    level: str  # low | raised | high
    drivers: tuple[RiskDriver, ...]
    horizon_days: int
    as_of: date
    version: str


def flare_risk(
    days: Sequence[DayRecord],
    patterns: Sequence[PatternResult],
    upcoming_period_types: Sequence[str] = (),
    as_of: date | None = None,
    risk: RiskConfig = DEFAULT_RISK_CONFIG,
    pattern_config: PatternConfig = DEFAULT_PATTERN_CONFIG,
) -> RiskOutlook:
    """``upcoming_period_types``: types of marked stressful periods starting within the horizon."""
    records = sorted(days, key=lambda r: r.day)
    as_of = as_of or (records[-1].day if records else date.today())
    recent = [r for r in records if as_of - timedelta(days=risk.lookback_days - 1) <= r.day <= as_of]
    drivers: list[RiskDriver] = []

    # 1. Index trend: the last days against the person's own usual level.
    earlier = [r.index for r in records if r.index is not None and r.day < as_of - timedelta(days=risk.lookback_days - 1)][-14:]
    latest = [r.index for r in recent if r.index is not None]
    if len(earlier) >= 3 and latest:
        rise = statistics.mean(latest) - statistics.median(earlier)
        if rise >= 1:
            points = min(risk.trend_max, round(rise * risk.trend_points_per_index_point))
            drivers.append(RiskDriver("index_trend", points, value=round(rise, 1)))

    # 2. The person's own contributors that happened in the last few days.
    # Factors that describe the same thing are counted once: one sleep factor, and not both of two
    # factors that mostly happen on the same days (high fat and red meat in the same dish).
    factor_points = 0
    counted: list[PatternResult] = []
    for p in patterns:
        if p.label not in (LIKELY, POSSIBLE) or p.group == "medication":
            continue
        if any(c.group == p.group == "sleep" or c.factor in p.overlaps_with or p.factor in c.overlaps_with for c in counted):
            continue
        count = sum(1 for r in recent if exposure(r, p.factor, pattern_config))
        if not count:
            continue
        per = risk.likely_factor_points if p.label == LIKELY else risk.possible_factor_points
        points = min(per * count, risk.per_factor_max, risk.factor_max - factor_points)
        if points <= 0:
            break
        factor_points += points
        counted.append(p)
        drivers.append(RiskDriver("factor", points, factor=p.factor, count=count))

    # 3. A marked stressful period about to start, if that kind of period is one of their contributors.
    linked = {p.factor for p in patterns if p.label in (LIKELY, POSSIBLE)}
    for kind in dict.fromkeys(upcoming_period_types):
        if f"period:{kind}" in linked:
            drivers.append(RiskDriver("upcoming_period", risk.upcoming_period_points, factor=f"period:{kind}"))

    # 4. Missed doses in the last week (logged only; never advice about medication).
    week = [r for r in records if as_of - timedelta(days=6) <= r.day <= as_of]
    missed = sum(1 for r in week if r.medication == "missed")
    if missed:
        drivers.append(RiskDriver("missed_doses", min(risk.missed_dose_max, missed * risk.missed_dose_points), count=missed))

    # 5. Already in a flare.
    if records and records[-1].period_kind == "flare":
        drivers.append(RiskDriver("in_flare", risk.in_flare_points))

    drivers.sort(key=lambda d: -d.points)
    score = min(100, sum(d.points for d in drivers))
    level = HIGH if score >= risk.high_at else RAISED if score >= risk.raised_at else LOW
    return RiskOutlook(score, level, tuple(drivers), risk.horizon_days, as_of, risk.version)
