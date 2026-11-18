"""Weight trend and unplanned weight loss (pure, no network).

Unplanned weight loss is a warning sign in IBD. HappyGut never diagnoses malnutrition: it shows
the trend and, past the published threshold, suggests telling the doctor.

The threshold is the weight-loss criterion of the GLIM consensus (Table 3):
    ">5% within past 6 months, or >10% beyond 6 months"
with ">10% within the past 6 mo" as the severe grade (Table 4).
Cederholm T, Jensen GL, Correia MITD, et al. GLIM criteria for the diagnosis of malnutrition -
A consensus report from the global clinical nutrition community. J Cachexia Sarcopenia Muscle.
2019;10(1):207-217. doi:10.1002/jcsm.12383. PMID 30920778. CC BY (open access, Europe PMC PMC6438340).

How we apply it (our reading, recorded in docs/01-strategy.md, decision D19): loss is measured
from the highest weigh-in in the window to the latest one, so a dip that has since recovered
doesn't count, and a slow loss that started from a peak does.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta

SOURCE = {
    "key": "GLIM2019",
    "citation": "Cederholm T, et al. GLIM criteria for the diagnosis of malnutrition - A consensus report from the "
                "global clinical nutrition community. J Cachexia Sarcopenia Muscle. 2019.",
    "doi": "10.1002/jcsm.12383",
    "pmid": "30920778",
    "quote": ">5% within past 6 months, or >10% beyond 6 months",
    "licence": "CC BY 4.0 (open access, Europe PMC)",
}


@dataclass(frozen=True)
class WeightConfig:
    version: str = "weight-v0.1"
    recent_window_days: int = 183  # "within past 6 months"
    long_window_days: int = 365  # "beyond 6 months": we look back up to a year
    recent_loss_percent: float = 5.0
    long_loss_percent: float = 10.0
    larger_loss_percent: float = 10.0  # GLIM stage 2 (severe) within 6 months
    due_after_days: int = 7  # a weekly weigh-in
    change_windows: tuple[int, ...] = (30, 90, 180)
    change_tolerance_days: int = 21  # how far from "N days ago" a weigh-in may be to compare with
    min_kg: float = 20.0
    max_kg: float = 300.0


DEFAULT_WEIGHT_CONFIG = WeightConfig()


@dataclass(frozen=True)
class WeightEntry:
    day: date
    kg: float


@dataclass(frozen=True)
class WeightChange:
    days: int  # the window asked for (30, 90, 180)
    since: date  # the weigh-in compared with
    from_kg: float
    kg: float  # latest minus earlier; negative is a loss
    percent: float


@dataclass(frozen=True)
class WeightLoss:
    """Unplanned loss past the GLIM threshold. ``level`` is "notable" or "larger"."""

    level: str
    window: str  # "recent" (within 6 months) or "long" (6 to 12 months)
    peak: WeightEntry
    kg: float  # positive: how much was lost
    percent: float


@dataclass(frozen=True)
class WeightTrend:
    latest: WeightEntry | None
    changes: tuple[WeightChange, ...]
    loss: WeightLoss | None
    due: bool  # no weigh-in in the last week
    entries: int


def _percent(loss: float, of: float) -> float:
    return round(100 * loss / of, 1)


def valid_weight(kg: float, config: WeightConfig = DEFAULT_WEIGHT_CONFIG) -> bool:
    return config.min_kg <= kg <= config.max_kg


def weight_trend(entries: Sequence[WeightEntry], today: date, config: WeightConfig = DEFAULT_WEIGHT_CONFIG) -> WeightTrend:
    """The latest weigh-in, change over each window, and any loss past the threshold."""
    past = sorted((e for e in entries if e.day <= today), key=lambda e: e.day)
    if not past:
        return WeightTrend(None, (), None, True, 0)
    latest = past[-1]
    earlier = past[:-1]

    changes = []
    for days in config.change_windows:
        target = latest.day - timedelta(days=days)
        near = [e for e in earlier if abs((e.day - target).days) <= config.change_tolerance_days]
        if near:
            ref = min(near, key=lambda e: (abs((e.day - target).days), e.day))
            diff = round(latest.kg - ref.kg, 1)
            changes.append(WeightChange(days, ref.day, ref.kg, diff, _percent(diff, ref.kg)))

    loss = None
    recent = [e for e in earlier if (latest.day - e.day).days <= config.recent_window_days]
    long = [e for e in earlier if config.recent_window_days < (latest.day - e.day).days <= config.long_window_days]
    if recent:
        peak = max(recent, key=lambda e: (e.kg, e.day))
        pct = _percent(peak.kg - latest.kg, peak.kg)
        if pct > config.recent_loss_percent:
            level = "larger" if pct > config.larger_loss_percent else "notable"
            loss = WeightLoss(level, "recent", peak, round(peak.kg - latest.kg, 1), pct)
    if loss is None and long:
        peak = max(long, key=lambda e: (e.kg, e.day))
        pct = _percent(peak.kg - latest.kg, peak.kg)
        if pct > config.long_loss_percent:
            loss = WeightLoss("notable", "long", peak, round(peak.kg - latest.kg, 1), pct)

    due = (today - latest.day).days >= config.due_after_days
    return WeightTrend(latest, tuple(changes), loss, due, len(past))
