"""Sleep duration and the "late night" flag (spec 003 FR-009).

"Late" is judged against the person's own usual bedtime, so shift workers aren't flagged
by a fixed clock time: more than 90 minutes after their median bedtime over the last 14
nights. Until 7 nights are logged, a fixed 01:00 applies.
"""

from __future__ import annotations

import statistics
from typing import Sequence

LATE_AFTER_MINUTES = 90
MIN_NIGHTS = 7
HISTORY_NIGHTS = 14
DEFAULT_LATE_AT = 25 * 60  # 01:00, counted from the previous noon-anchored day


def _evening_minutes(clock: str) -> int:
    """Minutes on a scale where an after-midnight bedtime follows the evening: 23:30 → 1410, 01:30 → 1530."""
    hours, minutes = (int(x) for x in clock.split(":"))
    if not (0 <= hours <= 23 and 0 <= minutes <= 59):
        raise ValueError(f"bad time: {clock}")
    total = hours * 60 + minutes
    return total + 24 * 60 if total < 12 * 60 else total  # before noon = after midnight


def sleep_hours(bedtime: str, wake_time: str) -> float:
    """Duration across midnight, in hours."""
    bed = _evening_minutes(bedtime)
    hours, minutes = (int(x) for x in wake_time.split(":"))
    wake = hours * 60 + minutes + 24 * 60
    if wake <= bed:
        wake += 24 * 60
    return round((wake - bed) / 60, 2)


def is_late_night(bedtime: str, previous_bedtimes: Sequence[str] = ()) -> bool:
    """``previous_bedtimes``: earlier nights, oldest first."""
    bed = _evening_minutes(bedtime)
    history = [_evening_minutes(b) for b in previous_bedtimes][-HISTORY_NIGHTS:]
    if len(history) < MIN_NIGHTS:
        return bed >= DEFAULT_LATE_AT
    return bed > statistics.median(history) + LATE_AFTER_MINUTES
