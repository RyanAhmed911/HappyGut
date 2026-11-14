"""Simulated patients with known, injected patterns (spec 003 FR-027).

No public dataset has daily IBD diet, sleep and stress logs, so the Pattern Finder is
validated on simulated diaries where the truth is known: which food components, habits and
periods really raise this simulated person's symptoms. Everything produced here is
simulated data and must be flagged ``is_synthetic`` and labelled "simulated" where shown.

The model: each day has a hidden symptom load. It starts from a calm baseline, rises in
scripted flare windows, and gets a bump (with some probability) after each injected
factor. The load is then turned into diary answers, so the clinical index is computed
by the same code as for a real diary.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Mapping, Sequence

from .indices import DiaryItems
from .vocab import Component, Level

TIMES_OF_DAY = ("morning", "noon", "evening")


@dataclass(frozen=True)
class MenuItem:
    name: str
    components: Mapping[Component, Level]
    meals: frozenset[str] = frozenset(TIMES_OF_DAY)  # when it's normally eaten
    weight: float = 1.0
    rich: bool = False  # party / restaurant food, eaten less often


@dataclass(frozen=True)
class Effect:
    """A bump in symptom load after a factor, on the same day and (weaker) the next."""

    load: float
    probability: float = 0.75
    next_day: float = 0.4  # share of the load carried into the next day


@dataclass(frozen=True)
class StressPeriod:
    type: str
    name: str
    start: int  # day offset
    end: int  # inclusive


@dataclass(frozen=True)
class SimConfig:
    days: int = 120
    seed: int = 11
    baseline_load: float = 1.0
    noise: float = 0.45
    flare_load: float = 5.2
    flare_windows: tuple[tuple[int, int], ...] = ()
    # Injected truth
    food_effects: Mapping[Component, Effect] = field(default_factory=dict)
    late_night_effect: Effect | None = None
    high_stress_effect: Effect | None = None
    period_effects: Mapping[str, Effect] = field(default_factory=dict)
    missed_dose_effect: Effect | None = None
    # Behaviour
    stress_periods: tuple[StressPeriod, ...] = ()
    late_night_rate: float = 0.10
    late_night_rate_in_period: float = 0.50
    rich_meal_rate: float = 0.16
    missed_dose_rate: float = 0.04
    missing_day_rate: float = 0.04
    keep_last_days_logged: int = 10
    reaction_mark_rate: float = 0.55  # how often the person marks the food that bothered them
    # Scripted events (day offset → ...), for a demo persona's recent days
    forced_late_nights: frozenset[int] = frozenset()
    forced_missed_doses: frozenset[int] = frozenset()
    forced_foods: Mapping[int, tuple[str, ...]] = field(default_factory=dict)  # evening meal items by name
    calm_days: frozenset[int] = frozenset()  # no random late nights, rich meals or missed doses


@dataclass(frozen=True)
class SimFood:
    name: str
    time_of_day: str
    reactions: tuple[str, ...] = ()


@dataclass(frozen=True)
class SimDay:
    offset: int
    logged: bool
    foods: tuple[SimFood, ...]
    items: DiaryItems
    bedtime: str  # "HH:MM", the night before this day
    wake_time: str
    sleep_quality: str
    stress: int
    medication: str
    late_night: bool
    in_flare: bool
    load: float


def _clock(minutes: float) -> str:
    m = int(minutes) % (24 * 60)
    return f"{m // 60:02d}:{m % 60:02d}"


def _items(load: float, rng: random.Random) -> DiaryItems:
    """Turn the hidden load into diary answers. The index comes out roughly equal to the load."""
    wellbeing = min(4, int(0.34 * load + 0.5))
    pain = min(3, int(0.28 * load + 0.5))
    liquid = int(max(0.0, 0.5 * load - 1.0) + 0.5)
    if liquid:
        stools = liquid
        bristol = 5 if load < 5 else 6 if load < 8 else 7
    else:
        stools = rng.choice((1, 1, 2))
        bristol = rng.choice((3, 4, 4))
    night = 1 if load >= 6.5 and stools >= 3 else 0
    urgency = "none" if load < 3 else "hurry" if load < 5.5 else "immediately"
    blood = "streaks" if load >= 6 and rng.random() < 0.5 else "none"  # never "a_lot": that is a red flag
    return DiaryItems(stools=stools, night_stools=night, bristol=bristol, blood=blood, urgency=urgency,
                      pain=pain, wellbeing=wellbeing)


def simulate(config: SimConfig, menu: Sequence[MenuItem]) -> list[SimDay]:
    rng = random.Random(config.seed)
    plain = [m for m in menu if not m.rich]
    rich = [m for m in menu if m.rich]
    by_name = {m.name: m for m in menu}

    def pick(pool: Sequence[MenuItem], meal: str) -> MenuItem | None:
        options = [m for m in pool if meal in m.meals]
        return rng.choices(options, weights=[m.weight for m in options])[0] if options else None

    def period_types(d: int) -> set[str]:
        return {p.type for p in config.stress_periods if p.start <= d <= p.end}

    carry = 0.0
    out: list[SimDay] = []
    for d in range(config.days):
        in_period = period_types(d)
        calm = d in config.calm_days
        in_flare = any(a <= d <= b for a, b in config.flare_windows)

        # Behaviour
        late_rate = config.late_night_rate_in_period if in_period else config.late_night_rate
        late = d in config.forced_late_nights or (not calm and rng.random() < late_rate)
        missed = d in config.forced_missed_doses or (not calm and rng.random() < config.missed_dose_rate * (3 if in_period else 1))
        stress = 3 + (rng.random() < 0.5) if in_period else rng.choice((0, 1, 1, 1, 2, 2))
        if not in_period and not calm and rng.random() < 0.06:
            stress = 3

        meals: list[tuple[MenuItem, str]] = []
        for meal in TIMES_OF_DAY:
            item = None
            if meal == "evening" and d in config.forced_foods:
                for name in config.forced_foods[d]:
                    meals.append((by_name[name], meal))
                continue
            if meal != "morning" and not calm and rich and rng.random() < config.rich_meal_rate / 2:
                item = pick(rich, meal)
            item = item or pick(plain, meal)
            if item is not None:
                meals.append((item, meal))
            if meal != "morning" and plain and rng.random() < 0.55:  # a side dish
                side = pick(plain, meal)
                if side is not None and side.name not in {m.name for m, _ in meals}:
                    meals.append((side, meal))

        # Symptom load
        load = config.baseline_load + rng.gauss(0, config.noise) + carry
        carry = 0.0
        if in_flare:
            load += config.flare_load + rng.gauss(0, 0.6)

        def apply(effect: Effect | None) -> bool:
            nonlocal load, carry
            if effect is None or rng.random() >= effect.probability:
                return False
            load += effect.load
            carry += effect.load * effect.next_day
            return True

        bothered: set[str] = set()
        fired: set[Component] = set()
        for item, _meal in meals:
            for comp, effect in config.food_effects.items():
                level = item.components.get(comp)
                if level is not None and level >= Level.MEDIUM and comp not in fired:
                    if apply(effect):
                        fired.add(comp)
                        bothered.add(item.name)
        if late:
            apply(config.late_night_effect)
        if stress >= 3:
            apply(config.high_stress_effect)
        for kind in in_period:
            apply(config.period_effects.get(kind))
        if missed:
            apply(config.missed_dose_effect)
        load = max(0.0, load)

        foods = tuple(
            SimFood(item.name, meal,
                    (rng.choice(("stomach_ache", "bloating", "urgency")),)
                    if item.name in bothered and rng.random() < config.reaction_mark_rate else ())
            for item, meal in meals
        )

        # Sleep the night before this day
        bed = (25 * 60 + 15 + rng.uniform(0, 110)) if late else (23 * 60 + 20 + rng.gauss(0, 22))
        hours = rng.uniform(5.0, 6.4) if late else rng.gauss(7.4, 0.5)
        quality = "poor" if (late and rng.random() < 0.6) or load >= 6 else rng.choice(("good", "good", "ok"))

        logged = d >= config.days - config.keep_last_days_logged or rng.random() >= config.missing_day_rate
        out.append(SimDay(
            offset=d, logged=logged, foods=foods, items=_items(load, rng), bedtime=_clock(bed),
            wake_time=_clock(bed + hours * 60), sleep_quality=quality, stress=int(stress),
            medication="missed" if missed else "taken", late_night=late, in_flare=in_flare, load=round(load, 2),
        ))
    return out
