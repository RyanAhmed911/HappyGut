"""Remission and flare periods from the daily index (spec 003 FR-021, FR-022).

A flare is proposed when the index is active on at least 3 of 4 consecutive days. It ends
after 7 consecutive logged calm days; the calm run at the end of the data that hasn't
reached 7 days yet is "settling". The user's decisions always win: a rejected flare is
dropped, and manually marked flares are added as given.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Mapping, Sequence

from .indices import THRESHOLDS, IndexThresholds

REMISSION, FLARE, SETTLING = "remission", "flare", "settling"


@dataclass(frozen=True)
class PeriodConfig:
    version: str = "periods-v0.1"
    window_days: int = 4
    active_days_needed: int = 3
    calm_days_to_end: int = 7
    min_days_logged: int = 7


DEFAULT_PERIOD_CONFIG = PeriodConfig()


@dataclass(frozen=True)
class Period:
    kind: str  # remission | flare | settling
    start: date
    end: date  # inclusive
    source: str = "index"  # index | user
    ongoing: bool = False

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1


@dataclass(frozen=True)
class ManualFlare:
    start: date
    end: date | None = None  # None = still going


def _flare_spans(scores: Mapping[date, int], th: IndexThresholds, cfg: PeriodConfig) -> list[tuple[date, date, bool]]:
    """(start, end, ongoing) for each detected flare."""
    if not scores:
        return []
    days = sorted(scores)
    first, last = days[0], days[-1]
    spans: list[tuple[date, date, bool]] = []
    d = first
    while d <= last:
        window = [d + timedelta(days=i) for i in range(cfg.window_days)]
        active = [w for w in window if scores.get(w, -1) >= th.active_at]
        if scores.get(d, -1) >= th.active_at and len(active) >= cfg.active_days_needed:
            start = d
            # The flare runs until 7 consecutive logged calm days; it ends the day before that run.
            calm_run: list[date] = []
            end, ongoing = last, True
            cur = d
            while cur <= last:
                score = scores.get(cur)
                if score is not None:
                    if score < th.remission_below:
                        calm_run.append(cur)
                        if len(calm_run) >= cfg.calm_days_to_end:
                            end, ongoing = calm_run[0] - timedelta(days=1), False
                            break
                    else:
                        calm_run = []
                cur += timedelta(days=1)
            if ongoing and calm_run:
                end = calm_run[0] - timedelta(days=1)  # the unfinished calm run is "settling"
            spans.append((start, end, ongoing))
            d = (calm_run[-1] if not ongoing else last) + timedelta(days=1)
        else:
            d += timedelta(days=1)
    return spans


def detect_periods(
    scores: Mapping[date, int],
    index_name: str,
    rejected_flares: Sequence[date] = (),
    manual_flares: Sequence[ManualFlare] = (),
    config: PeriodConfig = DEFAULT_PERIOD_CONFIG,
) -> list[Period]:
    """Split the logged range into remission / flare / settling periods, oldest first.

    ``rejected_flares``: start dates of proposed flares the user said were not flares.
    Returns an empty list until ``min_days_logged`` days exist.
    """
    if len(scores) < config.min_days_logged:
        return []
    th = THRESHOLDS[index_name]
    first, last = min(scores), max(scores)
    rejected = set(rejected_flares)

    flares: list[tuple[date, date, bool, str]] = [
        (s, e, ongoing, "index") for s, e, ongoing in _flare_spans(scores, th, config) if s not in rejected
    ]
    for m in manual_flares:
        start = max(m.start, first)
        end = min(m.end, last) if m.end is not None else last
        if start > end:
            continue
        # A manual flare replaces any detected flare it overlaps.
        flares = [f for f in flares if f[1] < start or f[0] > end]
        flares.append((start, end, m.end is None, "user"))
    flares.sort()

    periods: list[Period] = []
    cursor = first
    for start, end, ongoing, source in flares:
        if start > cursor:
            periods.append(Period(REMISSION, cursor, start - timedelta(days=1)))
        periods.append(Period(FLARE, start, end, source, ongoing and end == last))
        cursor = end + timedelta(days=1)
    if cursor <= last:
        after_ongoing_flare = bool(flares) and flares[-1][2]
        kind = SETTLING if after_ongoing_flare else REMISSION
        periods.append(Period(kind, cursor, last, ongoing=True))
    elif periods:
        last_p = periods[-1]
        periods[-1] = Period(last_p.kind, last_p.start, last_p.end, last_p.source, True)
    return periods


def kind_by_day(periods: Sequence[Period]) -> dict[date, str]:
    out: dict[date, str] = {}
    for p in periods:
        for i in range(p.days):
            out[p.start + timedelta(days=i)] = p.kind
    return out


def current_kind(periods: Sequence[Period]) -> str | None:
    return periods[-1].kind if periods else None
